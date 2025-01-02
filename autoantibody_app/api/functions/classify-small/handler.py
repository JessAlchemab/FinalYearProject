import json
import os
import shutil
import subprocess
import tempfile
import csv
import uuid
from typing import Dict, Any
import sys
import time
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_input_file(sequence: str, temp_dir: str) -> str:
    input_file = os.path.join(temp_dir, 'input.csv')
    with open(input_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['sequence_vh'])  
        writer.writerow([sequence])
    return input_file

def read_output_file(output_file: str) -> Dict[str, Any]:
    try:
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            return next(reader)  
    except Exception as e:
        return {"error": f"Failed to read output file: {str(e)}"}

# def get_docker_command():
#     if os.environ.get('IS_LOCAL') == 'true':
#         return [
#             'docker', 'run',
#             '--rm',  
#             '-v', f'{os.getcwd()}/temp:/temp', 
#             '189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier:latest',  
#             'torchrun'
#         ]
#     else:
#         return ['torchrun']

def lambda_handler(event, context):
    logger.info("Lambda handler started")
    logger.info(f"Received event: {event}")

    try:
        body = event.get('body', '{}')
        logger.info(f"Received body: {body}")
        
        if isinstance(body, str):
            body = json.loads(body)
        sequence = body.get('sequence')
        
        logger.info(f"Parsed sequence: {sequence}")
        
        if not sequence:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No sequence provided'})
            }

        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temp dir: {temp_dir}")

        try:
            input_file = create_input_file(sequence, temp_dir)
            logger.info(f"Created input file: {input_file}")
            
            file_id = str(uuid.uuid4())
            output_file = f"autoantibody_annotated.{file_id}.tsv"
            output_path = os.path.join(temp_dir, output_file)
            logger.info(f"Output path: {output_path}")

            cmd = ['torchrun', '--nproc_per_node=1', '/app/predict.py',
                  '--run_mode', 'cpu',
                  '--input_path', input_file,
                  '--output_file', output_path,
                  '--tokenizer_path', os.environ['TOKENIZER_PATH'],
                  '--model_path', os.environ['MODEL_PATH']]
            
            logger.info(f"Running command: {' '.join(cmd)}")
            process = subprocess.run(cmd, capture_output=True, text=True)
            logger.info(f"Process returncode: {process.returncode}")
            logger.info(f"Process stdout: {process.stdout}")
            logger.info(f"Process stderr: {process.stderr}")
            
            if process.returncode != 0:
                raise Exception(f"Command failed: {process.stderr}")

            results = read_output_file(output_path)
            logger.info(f"Results: {results}")
            
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps(results)
            }

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info("Cleaned up temp dir")

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e)})
        }

if __name__ == "__main__":
    print('aaa')
    # Simulate an event and context
    try:
        # Parse the event from the first argument if provided, otherwise default to a sample
        event = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {"body": '{"sequence": "ACTG"}'}
        context = {}  # Simulate an empty context object

        # Call the lambda_handler function
        print("event")
        print(event)

        result = lambda_handler(event, context)

        # Print the result in JSON format
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)