import json
import time
import boto3
import pandas as pd

def submit_query(event, context):
    # Create Athena client
    client = boto3.client('athena')
    
    # SQL query to fetch the required calculations
    query = """
    WITH filtered_data AS (
        SELECT *
        FROM "datacube-testing"."datacube_latest"
        WHERE locus = 'IGH' AND elite_controller_status = 'Control'
    )
    SELECT 
        AVG(mu_count_total) AS average_mu_count,
        
        100.0 * SUM(CASE WHEN v_call LIKE 'IGHV4-34%' THEN 1 ELSE 0 END) / COUNT(*) AS ighv4_34_percentage,
        
        100.0 * SUM(CASE WHEN v_call LIKE 'IGHV3-30%' THEN 1 ELSE 0 END) / COUNT(*) AS ighv3_30_percentage,
        
        100.0 * SUM(CASE WHEN c_call LIKE 'IGHG%' THEN 1 ELSE 0 END) / COUNT(*) AS ighg_percentage,
        
        100.0 * SUM(CASE WHEN c_call = 'IGHG1' THEN 1 ELSE 0 END) / COUNT(*) AS ighg1_percentage,
        100.0 * SUM(CASE WHEN c_call = 'IGHG2' THEN 1 ELSE 0 END) / COUNT(*) AS ighg2_percentage,
        100.0 * SUM(CASE WHEN c_call = 'IGHG3' THEN 1 ELSE 0 END) / COUNT(*) AS ighg3_percentage,
        100.0 * SUM(CASE WHEN c_call = 'IGHG4' THEN 1 ELSE 0 END) / COUNT(*) AS ighg4_percentage,
        
        AVG(LENGTH(cdr3_aa)) AS average_cdr3_length,
        
        COUNT(*) AS total_rows
            FROM filtered_data
    """
    
    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': 'datacube-testing',
            'Catalog': 'AwsDataCatalog'
        },
        ResultConfiguration={'OutputLocation': "s3://alchemab-bfd-glue-tmp/api"}
    )
    query_execution_id = response['QueryExecutionId']
    return {
        "statusCode": 200,
        "body": json.dumps({
           "queryId": query_execution_id
        }),
        "headers": {"Access-Control-Allow-Origin": "*"}
    }

    

def get_status(event, context):
    body = json.loads(event.get('body', '{}'))
    query_id = body.get('queryId', {})
    print('QUERY ID')
    print(query_id)
    client = boto3.client('athena')
    response_get_query_details = client.get_query_execution(
        QueryExecutionId=query_id)
    status = response_get_query_details['QueryExecution']['Status']['State']
    return {
        "statusCode": 200,
        "body": status,
        "headers": {"Access-Control-Allow-Origin": "*"}
    }

# def get_data(query_id, page_number, page_size=1000):
def get_data(event, context):
    body = json.loads(event.get('body', '{}'))
    query_id = body.get('queryId', {})
    # page_size = 10
    page_number = body.get('pageNumber', {})
    client = boto3.client('athena')

    # Get the first page
    response = client.get_query_results(
        QueryExecutionId=query_id,
        MaxResults=10
    )
    col_indices = {item['VarCharValue']: index for index, item in enumerate(
        response["ResultSet"]["Rows"][0]["Data"])}
    results = response["ResultSet"]["Rows"][1]["Data"]
    results_dict = {}
    

    for key, value in col_indices.items():
        col_name = key
        location = value
        results_dict[col_name] = results[location]['VarCharValue']

    print(results_dict)
    return {
        "statusCode": 200,
        "body": json.dumps({
           "results": results_dict
        }),
        "headers": {"Access-Control-Allow-Origin": "*"}
    }
    # If we need a page other than the first, continue fetching
    # current_page = 1
    # while current_page < page_number and "NextToken" in response:
    #     response = client.get_query_results(
    #         QueryExecutionId=query_id,
    #         NextToken=response["NextToken"],
    #         MaxResults=page_size
    #     )
    #     results = response["ResultSet"]["Rows"]
    #     current_page += 1

    # has_more = "NextToken" in response
    # return results, col_indices, has_more

