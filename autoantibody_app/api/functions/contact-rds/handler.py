from .secrets_manager import get_secret
from .connection_handlers import create_connection, execute_query
import json

secrets = get_secret("FRANKLIN_RDS")
database_name = secrets["DB_NAME"]
database_user = secrets["DB_USER"]
database_host = secrets["DB_HOST"]
database_port = secrets["DB_PORT"]
database_password = secrets["DB_PASSWORD"]

def parse_sql_hash(headers, rows):
    row = rows[0]
    # This makes the SQL query results into a nice format for the frontend
    container_dict = {}
    for header in headers:
        container_dict[header] = row[headers.index(header)]
    return container_dict

def parse_sql_runs(headers, rows):
    # This makes the SQL query results into a nice format for the frontend
    container_list = []
    for row in rows:
        hash_id_loc = headers.index('hash_id')
        date_loc = headers.index('date')
        container_list.append({"hash_id": row[hash_id_loc], "date": row[date_loc]})
    return container_list

def retrieve_runs(event, context):
    body = json.loads(event.get('body', '{}'))

    search_string = body.get('search_string')
    connection = create_connection(
        "franklin_metrics", database_user, database_password, database_host, database_port
    )
    cursor = connection.cursor()

    query = f"""
        SELECT hash_id, date FROM autoantibody_dev
        {f'where hash_id like %{search_string}%' if len(search_string) > 0 else ''}
        ORDER BY date
        LIMIT 20
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    cursor.close()
    return {
        "statusCode": 200,
        "body": json.dumps({
           "data": parse_sql_runs(column_names, rows)
        }),
        "headers": {"Access-Control-Allow-Origin": "*"}
    }

def get_run_data(event, context):
    body = json.loads(event.get('body', '{}'))
    run = body.get('name', {})

    connection = create_connection(
    "franklin_metrics", database_user, database_password, database_host, database_port
)
    cursor = connection.cursor()
    query = f"""
        SELECT * FROM autoantibody_dev
        WHERE hash_id = '{run}'
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    cursor.close()
    return {
        "statusCode": 200,
        "body": json.dumps({
           "data": parse_sql_hash(column_names, rows)
        }),
        "headers": {"Access-Control-Allow-Origin": "*"}
    }

