import json
import uuid
import boto3
from botocore.exceptions import ClientError
import os  # To extract the file extension

BUCKET_NAME = os.environ['AUTOANTIBODY_S3_BUCKET']
s3_client = boto3.client("s3")

def get_upload_url(event, context):
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

        # Extract the folder path from the provided file_path
        # folder_path = os.path.dirname(file_path)

        # Use the folder path and append the random hash with the file extension
        hashed_file_path = f"{random_hash}_autoantibody{file_extension}"

        # Generate the presigned URL
        params = {"Bucket": BUCKET_NAME, "Key": hashed_file_path}
        presigned_url = s3_client.generate_presigned_url(
            "put_object", Params=params, ExpiresIn=60
        )

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization,x-access-token",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
            },
            "body": json.dumps({"url": presigned_url, "hashed_name": hashed_file_path, "status": 200}),
        }

    except ClientError as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
