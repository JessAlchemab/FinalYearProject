import boto3
import os
import sys
from urllib.parse import urlparse
from botocore.exceptions import ClientError
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from psycopg2 import OperationalError
from secrets_manager import get_secret

rds_secrets = get_secret("FRANKLIN_RDS")
rds_database_name = rds_secrets["DB_NAME"]
rds_database_user = rds_secrets["DB_USER"]
rds_database_host = rds_secrets["DB_HOST"]
rds_database_port = rds_secrets["DB_PORT"]
rds_database_password = rds_secrets["DB_PASSWORD"]

def create_connection(db_name, db_user, db_password, db_host, db_port):
    connection = None
    try:
        connection = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection

def execute_query(conn, query):
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            return column_names, result
    except psycopg2.Error as e:
        print(f"Error executing query: {e}")
        return None, None
    finally:
        conn.close()

def upload_metrics_to_rds(metrics, hash_id, table_name):
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
    connection = create_connection(
        "franklin_metrics", 
        rds_database_user, 
        rds_database_password, 
        rds_database_host, 
        rds_database_port
    )
    cur = connection.cursor()
    print('table name:', table_name)
    # # Create the table if it doesn't exist
    # cur.execute(f"""
    #     CREATE TABLE IF NOT EXISTS {table_name} (
    #         hash_id VARCHAR(30) PRIMARY KEY,
    #         {', '.join([f"{col} FLOAT" for col in df.columns])}
    #     )
    # """)
    
    # Insert the data into the table
    values = [tuple(row) for row in df.to_records(index=False)]
    cols = ', '.join(df.columns)
    
    execute_values(cur, f"INSERT INTO {table_name} ({cols}) VALUES %s", values)
    connection.commit()
    
    # Close the connection
    cur.close()
    connection.close()
    
    print(f"Metrics uploaded to RDS table: {table_name}")