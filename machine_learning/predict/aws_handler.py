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
import datetime

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
    print(metrics)
    # df = pd.DataFrame(list(metrics.items()), columns=['metric', 'values'])
    df = pd.DataFrame([metrics])
    
    
    df['hash_id'] = hash_id
    print(df)
    
    # Establish connection to RDS
    connection = create_connection(
        "franklin_metrics", 
        rds_database_user, 
        rds_database_password, 
        rds_database_host, 
        rds_database_port
    )
    cursor = connection.cursor()

    # Insert data into PostgreSQL table
    insert_query = """
        INSERT INTO autoantibody_dev (
            hash_id,
            date,
            total_rows,
            human_rows,
            IGHV4_34_percentage,
            IGHV3_30_percentage,
            IGHG_percentage,
            IGHG1_percentage,
            IGHG2_percentage,
            IGHG3_percentage,
            IGHG4_percentage,
            average_cdr3_length,
            average_mu_count,
            human_prediction_percentage,
            probability_histogram
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    # Assuming 'hash_id' is provided separately

    # Insert each row in the DataFrame
    date = datetime.datetime.now()

    for _, row in df.iterrows():
        cursor.execute(insert_query, (
            hash_id,
            date,
            row['total_rows'],
            row['human_rows'],
            row['IGHV4_34_percentage'],
            row['IGHV3_30_percentage'],
            row['IGHG_percentage'],
            row['IGHG1_percentage'],
            row['IGHG2_percentage'],
            row['IGHG3_percentage'],
            row['IGHG4_percentage'],
            row['average_cdr3_length'],
            row['average_mu_count'],
            row['human_prediction_percentage'],
            row['probability_histogram']
        ))

    # Commit the transaction
    connection.commit()

    # Close the cursor and connection
    cursor.close()
    connection.close()
    
    print(f"Metrics uploaded to RDS table: {table_name}")