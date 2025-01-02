import json
import os
import subprocess
import tempfile
import csv
import uuid
from typing import Dict, Any

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
    try:
        body = json.loads(event.get('body', '{}'))
        sequence = body.get('sequence')
        
        if not sequence:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No sequence provided'})
            }

        # Create temporary directory for everything to run in
        temp_dir = tempfile.mkdtemp()
        # temp_dir = os.path.join(os.getcwd(), 'temp') if os.environ.get('IS_LOCAL') == 'true' else tempfile.mkdtemp()
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # make input file
            input_file = create_input_file(sequence, temp_dir)
            
            # make a unique hash ID, since that's what the script expects to receive
            file_id = str(uuid.uuid4())
            output_file = f"autoantibody_annotated.{file_id}.tsv"
            output_path = os.path.join(temp_dir, output_file)

            base_cmd = ['torchrun']

            # Construct the full command for docker running
            cmd = base_cmd + [
                '--nproc_per_node=1',
                '/app/predict.py',
                '--run_mode', 'cpu',
                '--input_path', input_file,
                '--output_file', output_path,
                # '--input_path', input_file if not os.environ.get('IS_LOCAL') else f'/temp/{os.path.basename(input_file)}',
                # '--output_file', output_path if not os.environ.get('IS_LOCAL') else f'/temp/{output_file}',
                '--tokenizer_path', os.environ['TOKENIZER_PATH'],
                '--model_path', os.environ['MODEL_PATH']
            ]
            print(cmd)
            # Actually run the command
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            print(process)
            if process.returncode != 0:
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': 'Prediction failed',
                        'details': process.stderr
                    })
                }

            # Read and return results
            results = read_output_file(output_path)
            
            return {
                'statusCode': 200,
                'body': json.dumps(results)
            }

        finally:
            # Clean up temp directory if on lambda
            # if os.environ.get('IS_LOCAL') != 'true' and os.path.exists(temp_dir):
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }