from .secrets_manager import get_secret
from .connection_handlers import create_connection, execute_query
import json

secrets = get_secret("FRANKLIN_RDS")
database_name = secrets["DB_NAME"]
database_user = secrets["DB_USER"]
database_host = secrets["DB_HOST"]
database_port = secrets["DB_PORT"]
database_password = secrets["DB_PASSWORD"]

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
    print(rows)
    print(column_names)

def get_run_data(run):
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
    print(rows)
    print(column_names)