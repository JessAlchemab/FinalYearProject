import boto3
import os
import sys
from urllib.parse import urlparse
from botocore.exceptions import ClientError
import pandas as pd
import sqlalchemy

def download_s3_object(s3_path, download_dir="/app/files"):
    # Parse the S3 path
    parsed_url = urlparse(s3_path)
    
    if parsed_url.scheme != 's3':
        raise ValueError("Provided path is not a valid S3 path.")
    
    bucket_name = parsed_url.netloc
    object_key = parsed_url.path.lstrip('/')
    
    os.makedirs(download_dir, exist_ok=True)
    
    # Define the local download path
    filename = os.path.basename(object_key)
    download_path = os.path.join(download_dir, filename)
    
    # Initialize the S3 client
    s3 = boto3.client('s3')
    
    # Download the file
    s3.download_file(bucket_name, object_key, download_path)
    return {"status": "success", "message": f"Downloaded {s3_path} to {download_path}"}

def upload_file_to_s3(local_file_path, s3_path):
    # Parse the S3 path
    parsed_url = urlparse(s3_path)
    
    if parsed_url.scheme != 's3':
        raise ValueError("Provided path is not a valid S3 path.")
    
    bucket_name = parsed_url.netloc
    object_key = parsed_url.path.lstrip('/')
    
    # Check if the file exists locally
    if not os.path.isfile(local_file_path):
        raise FileNotFoundError(f"The file {local_file_path} does not exist.")
    
    # Initialize the S3 client
    s3 = boto3.client('s3')
    
    # Upload the file
    s3.upload_file(local_file_path, bucket_name, object_key)
    print(f"Uploaded {local_file_path} to {s3_path}")
    return {"status": "success", "message": f"Uploaded {local_file_path} to {s3_path}"}

def upload_metrics_to_rds(metrics, hash_id, table_name, rds_connection_string):
    # Convert metrics dictionary to a DataFrame
    df = pd.DataFrame.from_dict(metrics, orient='index').T
    df.index.name = 'hash_id'
    df['hash_id'] = hash_id
    
    # Create connection to RDS
    engine = sqlalchemy.create_engine(rds_connection_string)
    
    # Upload DataFrame to RDS table
    df.to_sql(table_name, engine, if_exists='append', index=False)
    
    print(f"Metrics uploaded to RDS table: {table_name}")