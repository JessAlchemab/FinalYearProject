import json
import uuid
import boto3
from botocore.exceptions import ClientError
import os

BUCKET_NAME = os.environ['AUTOANTIBODY_S3_BUCKET']
s3_client = boto3.client("s3")

def get_multipart_upload_url(event, context):
    query_params = event.get("queryStringParameters")
    if query_params and isinstance(query_params, dict):
        file_path = query_params.get("file_path")
    else:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"error": "No queryStringParameters provided or invalid format."}
            ),
        }

    if not file_path:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"error": "No file_path querystring parameter provided."}
            ),
        }

    try:
        # Generate a random UUID for the file name
        random_hash = str(uuid.uuid4())
        
        # Extract the file extension from the original file path
        _, file_extension = os.path.splitext(file_path)
        if not file_extension:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"error": "File path does not contain a valid file extension."}
                ),
            }

        # Use the random hash and file extension
        hashed_file_path = f"{random_hash}_autoantibody{file_extension}"

        # Initiate multipart upload
        multipart_upload = s3_client.create_multipart_upload(
            Bucket=BUCKET_NAME,
            Key=hashed_file_path
        )

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization,x-access-token",
                "Access-Control-Allow-Methods": "GET,OPTIONS,POST,PUT,DELETE",
            },
            "body": json.dumps({
                "uploadId": multipart_upload['UploadId'],
                "hashed_name": hashed_file_path,
                "status": 200
            }),
        }

    except ClientError as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

def get_multipart_upload_part_url(event, context):
    query_params = event.get("queryStringParameters")
    if not query_params:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "No query parameters provided"}),
        }

    try:
        file_path = query_params.get("file_path")
        upload_id = query_params.get("uploadId")
        part_number = query_params.get("partNumber")

        if not all([file_path, upload_id, part_number]):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required parameters"}),
            }

        # Generate presigned URL for this specific part
        presigned_url = s3_client.generate_presigned_url(
            'upload_part',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': file_path,
                'UploadId': upload_id,
                'PartNumber': int(part_number)
            },
            ExpiresIn=3600  # URL valid for 1 hour
        )

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization,x-access-token",
                "Access-Control-Allow-Methods": "GET,OPTIONS,PUT",
            },
            "body": json.dumps({
                "url": presigned_url,
                "status": 200
            }),
        }

    except ClientError as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

def complete_multipart_upload(event, context):
    try:
        # Parse request body and query parameters
        body = json.loads(event.get('body', '{}'))
        query_params = event.get("queryStringParameters", {})

        file_path = query_params.get("file_path")
        upload_id = query_params.get("uploadId")
        parts = body.get("parts", [])

        if not all([file_path, upload_id, parts]):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required parameters"}),
            }

        # Complete the multipart upload
        result = s3_client.complete_multipart_upload(
            Bucket=BUCKET_NAME,
            Key=file_path,
            UploadId=upload_id,
            MultipartUpload={
                'Parts': [
                    {'ETag': part['ETag'], 'PartNumber': part['PartNumber']} 
                    for part in parts
                ]
            }
        )

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization,x-access-token",
                "Access-Control-Allow-Methods": "POST,OPTIONS",
            },
            "body": json.dumps({
                "location": result['Location'],
                "hashed_name": file_path,
                "status": 200
            }),
        }

    except ClientError as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

def abort_multipart_upload(event, context):
    query_params = event.get("queryStringParameters")
    if not query_params:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "No query parameters provided"}),
        }

    try:
        file_path = query_params.get("file_path")
        upload_id = query_params.get("uploadId")

        if not all([file_path, upload_id]):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required parameters"}),
            }

        # Abort the multipart upload
        s3_client.abort_multipart_upload(
            Bucket=BUCKET_NAME,
            Key=file_path,
            UploadId=upload_id
        )

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization,x-access-token",
                "Access-Control-Allow-Methods": "DELETE,OPTIONS",
            },
            "body": json.dumps({"status": "Multipart upload aborted"}),
        }

    except ClientError as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    


def download_file(event, context):
    s3_client = boto3.client('s3')
    
    try:
        # Parse folder from request body
        body = json.loads(event['body'])
        folder = body['hashId']
        if os.environ['STAGE'] == "dev":
            bucket = "alchemab-pipeline-results-development"
        else:
            bucket = "alchemab-pipeline-results-production"
        # List objects in the specific folder
        list_response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=f'outputs/autoantibodyclassifier/{folder}/autoantibody_annotated.input_file'
        )
        
        # Verify exactly one file exists
        if 'Contents' not in list_response or len(list_response['Contents']) != 1:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'File not found (or too many file found)'})
            }
        
        file_key = list_response['Contents'][0]['Key']
        
        # Generate presigned URL
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket,
                'Key': file_key
            },
            ExpiresIn=3600  
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'presignedUrl': presigned_url}),
            'headers': {
                'Access-Control-Allow-Origin': '*'
            }
        }
    
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error generating presigned URL'})
        }