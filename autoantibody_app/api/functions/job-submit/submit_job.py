# Built-in/Generic Imports
from datetime import datetime
import shlex

# Third-party Imports
import boto3
from botocore.exceptions import ClientError
import json
import os
# from misc import mnemonic_hash
import logging
import time
from urllib.parse import urlparse
from pathlib import Path
from shortuuid import ShortUUID
from wonderwords import RandomWord, Defaults
import csv
import io
from .tracking import PipelineRuns

logger = logging.getLogger(__name__)

s3_client = boto3.client("s3")

def mnemonic_hash(
    word_min_length=3,
    word_max_length=8,
    uuid_length = 7,
    uuid_alphabet = "23456789BCDFGHJKLMNPQRSTVWXYZbcdfghjkmnpqrstvwxyz"
):

    # Create a UUID in Base49
    uuid = ShortUUID(alphabet=uuid_alphabet).random(length=uuid_length)

    # Use an extended list of words
    # TODO: if this becomes a package, use importlib.resources
    # Custom adjectives
    adjectives_file = "assets/word-lists/adjectives.tsv"
    with open(Path(__file__).parent.joinpath(adjectives_file), "r") as f:
        adjectives = f.readlines()
    adjectives = [word.strip() for word in adjectives]
    # Custom nouns
    nouns_file = "assets/word-lists/nouns.tsv"
    with open(Path(__file__).parent.joinpath(nouns_file), "r") as f:
        nouns = f.readlines()
    nouns = [word.strip() for word in nouns]

    # When creating the generator, if one of the categories will be custom, we 
    # have to define the others we would like to keep with the Defaults lists.
    # E.g. custom adjectives, default nouns
    #   generator = RandomWord(adjective=adjectives, noun=Defaults.NOUNS)
    generator = RandomWord(adjective=adjectives, noun=nouns)

    # Pick a random word from each categorical list. Words should only contain 
    # letters (no hyphens or spaces), and be between 3-16 characters long.
    categories = ["adjective", "noun"]
    words = []
    for category in categories:
        words.append(
            generator.word(
                include_categories=[category], 
                word_min_length=word_min_length, 
                word_max_length=word_max_length, 
                regex="[A-Za-z]+"
            )
        )

    return "_".join(words + [uuid])

def get_job_name(pipeline_name, hash_id, environment, registry_id
                  ):
        """
        The job name has the following structure:
            wf-{environment}-{pipeline_name}-{hash_id}
        - the "wf-" prefix is used to filter the logs when monitoring the queue,
        - the "environment" is used to choose the right trackingdb,
        - the "pipeline_name" and "hash_id" are used to query the trackingDB,
        - the "registry_id" is for user visual aid.
        """
        # if isinstance(registry_id, list) and len(registry_id) > 1:
        #     registry_id = "multi"
        # elif isinstance(registry_id, list) and len(registry_id) == 1:
        #     registry_id = registry_id[0]
        # return f"wf-{environment}-{pipeline_name}-{hash_id}-{registry_id}"
        return f"wf-{environment}-{pipeline_name}-{hash_id}-{registry_id}"

def get_command_string(revision, output_path, input_file, with_gpu, stage, uuid, ):
        # use https to github repo

        options = []
        options.append("https://github.com/alchemab/wf-nf-autoantibodyclassifier.git")

        options.append(f"-profile awsbatch")

        # revision is tag or commit of repo
        options.append(f"-revision {revision}")
        options.append(f"--outdir {output_path}/autoantibodyclassifier/{uuid}")
        options.append(f"--input {input_file}")
        options.append(f"--with_gpu {str(with_gpu).lower()}")
        options.append(f"--stage {stage}")
        if with_gpu:
            options.append(f"--awsgpuqueue {os.environ['GPU_QUEUE']}")

        return " ".join(options)


def write_dict_to_s3(sample_sheet_dict, bucket_name, s3_key):
    # Create a string buffer to hold the CSV data
    csv_buffer = io.StringIO()
    
    # Write CSV to the buffer
    writer = csv.DictWriter(csv_buffer, fieldnames=sample_sheet_dict.keys())
    writer.writeheader()
    writer.writerow(sample_sheet_dict)
    
    # Get the string value and encode it
    csv_content = csv_buffer.getvalue()
    
    # Initialize S3 client
    s3_client = boto3.client('s3')
    
    try:
        # Upload the CSV content to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,  
            Body=csv_content,
            ContentType='text/csv'
        )
        return True
    except ClientError as e:
        print(f"Error uploading to S3: {str(e)}")
        raise e
    finally:
        # Clean up the buffer
        csv_buffer.close()

def setup_files(temp_filename, uuid):

        # Set the input and output paths. The input path will be used to stage 
        # files dynamic files required for the pipeline, like barcode lists.
        input_path = "/".join([os.environ['NF_INPUTSDIR'], "autoantibodyclassifier", uuid])


        # upload sample sheet file and input file - create and upload to input path
        # The file is initially uploaded to the zeus bucket. From here we copy it into
        # the input path
        temp_filepath = "s3://" + os.environ['AUTOANTIBODY_S3_BUCKET'] + uuid

        # copy to nf_inputsdir
        # s3 cp zeus-parameters-input-files/{uuid} to 
        input_parsed = urlparse(input_path)
        temp_parsed = urlparse(temp_filepath)
        source_bucket = temp_parsed.netloc
        source_key = temp_parsed.path.lstrip('/')  # Removes leading '/'
        destination_bucket = input_parsed.netloc
        destination_key = input_parsed.path.lstrip('/')  # Removes leading '/'

        # Copy the file
        print({ 'Bucket': os.environ['AUTOANTIBODY_S3_BUCKET'],
                'Key': temp_filename,})
        print(destination_bucket)
        print(destination_key)
        # Rename the file so that it has consistent name
        new_filename = f"input_file.{temp_filename.split('.')[-1]}"
        s3_client.copy(
            {
                'Bucket': os.environ['AUTOANTIBODY_S3_BUCKET'],
                'Key': temp_filename,
            },
            destination_bucket,
            f"{destination_key}/{new_filename}"
        )

        print(f"File copied from {temp_filepath} to {input_path}")


#         input_file,hash_id
#         s3://path/to/input_file.tsv,example_hash
        sample_sheet_dict = {"input_file": f"{os.environ['NF_INPUTSDIR']}/autoantibodyclassifier/{uuid}/input_file.{temp_filename.split('.')[-1]}", "hash_id": uuid}
        write_dict_to_s3(sample_sheet_dict, destination_bucket, f"{destination_key}/samplesheet.csv")
        print(f"Sample sheet generated at {destination_key}/samplesheet.csv")
        return {"input": f"s3://{destination_bucket}/{destination_key}/{new_filename}", "samplesheet": f"s3://{destination_bucket}/{destination_key}/samplesheet.csv"}



def start_job(commands, batch_client, temp_filename, uuid, version):

        jobs = {}

        input_path = "/".join([os.environ['NF_INPUTSDIR'], "autoantibodyclassifier", uuid, f"input_file.{temp_filename.split('.')[-1]}"])
        output_path = "/".join([os.environ['NF_OUTPUTSDIR'], "autoantibodyclassifier", uuid])

        # for tracking_entry, definition in job_definitions:

        start_time = time.time()



        # TODO: create and copy across the sample sheet

        # command = get_command_string(revision, output_path, input_path, with_gpu)

        # pipeline_name = tracking_entry["pipeline_name"]
        pipeline_name = "autoantibodyclassifier"
        # registry_id = tracking_entry["registry_id"]
        hash_id = uuid
        if os.environ['STAGE'] == 'prod':
             stage = "production"
        else:
             stage = "development"
        # Get a formatted job name
        registry_id = temp_filename.split('/')[-1].split(".")[-2].replace("-", "")
        print("REGISTRY ID")
        print(registry_id)
        job_name = get_job_name(
            pipeline_name, 
            hash_id, 
            stage,
            registry_id)
        print(commands)
        
        # Register job on batch
        # TODO: review the retryStrategy option
        try:
            response = batch_client.submit_job(
                jobName=job_name,
                jobQueue=os.environ['MASTER_QUEUE'],
                jobDefinition=os.environ['JOB_DEFINITION'],
                containerOverrides={
                    "command": shlex.split(commands),
                    "environment": [
                        {
                            "name": "NF_JOB_REGION",
                            "value": os.environ['REGION']
                        }
                    ],
                },
                retryStrategy={"attempts": 1},
            )

        except ClientError as err:
            logger.error(
                "Error when submitting job %s. Here's why: %s: %s", job_name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            time.sleep(2)

        trackingdb = PipelineRuns(stage)
        tracking_entry = {}

        tracking_entry['pipeline_name'] = 'autoantibodyclassifier'
        tracking_entry['registry_id'] = registry_id
        tracking_entry['hash_id'] = uuid
        tracking_entry["scheduler_job_id"] = response["jobId"]
        tracking_entry["start_date"] = \
            datetime.utcfromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S")
        tracking_entry["job_status"] = "SUBMITTED"
        tracking_entry['pipeline_version'] = version
        tracking_entry['registry_type'] = 'hash_id'
        tracking_entry['command'] = commands
        tracking_entry['default'] = True
        tracking_entry['tag'] = ''
        tracking_entry['output_path'] = output_path
        tracking_entry['pipeline_tools_submit_parameters'] = None
        tracking_entry['cloning_parameters'] = None
        trackingdb.add_entry(**tracking_entry)
        
        jobs[hash_id] = {
            "job_id": response["jobId"],
        }


        return jobs


# def submit_pipeline(revision, input_file):
def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    print(body)
    revision = body.get('revision')
    input_file = body.get('input_file')
    # Get a mnemonic UUID for the input/output path
    uuid = mnemonic_hash()
    batch_client = boto3.client("batch", region_name=os.environ['REGION'])
    files_setup = setup_files(input_file, uuid)
    commands = get_command_string(revision, os.environ['NF_OUTPUTSDIR'], files_setup['samplesheet'], True, os.environ['STAGE'], uuid)
    start_job(commands, batch_client, files_setup['samplesheet'], uuid, revision)
    return {"status": "success"}