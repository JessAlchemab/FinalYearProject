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
from predict import (predict_cpu)

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


def lambda_handler(event, context):
    print('event')
    print(event)
    try:
        body = json.loads(event['body'])
        sequence = body.get('sequence')
        
        
        if not sequence:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No sequence provided'})
            }

        temp_dir = tempfile.mkdtemp()

        try:
            input_file = create_input_file(sequence, temp_dir)
            
            file_id = str(uuid.uuid4())
            output_file = f"autoantibody_annotated.{file_id}.tsv"
            output_path = os.path.join(temp_dir, output_file)
            predict_cpu(
                input_file,
                output_path,
                os.environ['TOKENIZER_PATH'],
                os.environ['MODEL_PATH']
            )

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
