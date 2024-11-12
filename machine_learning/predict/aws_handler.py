import boto3
import os
import sys
from urllib.parse import urlparse
from botocore.exceptions import ClientError
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

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
    """
    Upload the metrics dictionary to an RDS table using the provided hash_id as the primary key.
    
    Args:
        metrics (dict): Dictionary of metrics to be uploaded.
        hash_id (str): Unique identifier to use as the primary key.
        table_name (str): Name of the RDS table to upload to.
        rds_connection_string (str): Connection string for the RDS database.
    """
    # Convert metrics dictionary to a DataFrame with hash_id as the index
    df = pd.DataFrame.from_dict(metrics, orient='index')
    df.index.name = 'hash_id'
    df['hash_id'] = hash_id
    
    # Establish connection to RDS
    conn = psycopg2.connect(rds_connection_string)
    cur = conn.cursor()
    
    # Create the table if it doesn't exist
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            hash_id VARCHAR(30) PRIMARY KEY,
            {', '.join([f"{col} FLOAT" for col in df.columns])}
        )
    """)
    
    # Insert the data into the table
    values = [tuple(row) for row in df.to_records(index=False)]
    cols = ', '.join(df.columns)
    
    execute_values(cur, f"INSERT INTO {table_name} ({cols}) VALUES %s", values)
    conn.commit()
    
    # Close the connection
    cur.close()
    conn.close()
    
    print(f"Metrics uploaded to RDS table: {table_name}")