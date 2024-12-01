# Built-in/Generic Imports
import logging
import operator
from datetime import datetime
from functools import reduce

# Third-party Imports
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)


class PipelineRuns:
    """Encapsulates an Amazon DynamoDB table of pipeline runs data."""

    table_name = "pipeline-runs"

    def __init__(self, environment, region_name = "eu-west-2"):
        self.dyn_client = boto3.client('dynamodb', region_name=region_name)
        self.dyn_resource = boto3.resource('dynamodb', region_name=region_name)
        self.table_name = "-".join([self.table_name, environment])
        self.table = self._load_or_create_table(self.table_name)

    def _load_or_create_table(self, table_name):
        """
        Returns the requested table. If it doesn't exist, it is created first.

        :param table_name: The name of the table to check.
        :return: The requested table.
        """
        try:
            table = self.dyn_resource.Table(table_name)
            table.load()
        except ClientError as err:
            if err.response['Error']['Code'] == 'ResourceNotFoundException':
                table = self.create_table(self, table_name)
            else:
                logger.error(
                    "Couldn't check for existence of %s. Here's why: %s: %s",
                    table_name,
                    err.response['Error']['Code'], err.response['Error']['Message'])
                raise
        return table

    def create_table(self, table_name):
        """
        Creates an Amazon DynamoDB table that can be used to store pipeline runs data.
        The table uses the pipeline_name as the partition key and the hash_id as sort 
        key.

        :param table_name: The name of the table to create.
        :return: The newly created table.
        """
        try:
            self.table = self.dyn_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'pipeline_name', 'KeyType': 'HASH'}, # Partition key
                    {'AttributeName': 'hash_id', 'KeyType': 'RANGE'}     # Sort key
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'pipeline_name', 'AttributeType': 'S'},
                    {'AttributeName': 'hash_id', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={'ReadCapacityUnits': 10, 'WriteCapacityUnits': 10})
            self.table.wait_until_exists()
        except ClientError as err:
            logger.error(
                "Couldn't create table %s. Here's why: %s: %s", table_name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return self.table

    def update_batch_default_field(self, entries):
        """
        In a transaction, sets the new item as default and turn the previous items'
        default value to false.

        :param entries: The data to update in the table. Each item must contain the
                        keys required by the schema that was specified when the
                        table was created and the new "default" value.
        """
        try:
            transact_items = []
            for entry in entries:
                transact_items.append(
                    {
                        "Update": {
                            "TableName": self.table_name,
                            "Key": {
                                "pipeline_name": {"S": entry["pipeline_name"]},
                                "hash_id": {"S": entry["hash_id"]},
                            },
                            "ConditionExpression": "attribute_exists(pipeline_name) AND attribute_exists(hash_id)",
                            "UpdateExpression": "SET #defaultField = :value",
                            "ExpressionAttributeNames": {"#defaultField": "default"},
                            "ExpressionAttributeValues": {
                                ":value": {"BOOL": entry["default"]}
                            },
                        }
                    }
                )
            self.dyn_client.transact_write_items(TransactItems=transact_items)

        except ClientError as err:
            logger.error(
                "Couldn't update data into table %s. Here's why: %s: %s", self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise

    def write_batch(self, entries):
        """
        Fills an Amazon DynamoDB table with the specified data, using the Boto3
        Table.batch_writer() function to put the items in the table.
        Inside the context manager, Table.batch_writer builds a list of
        requests. On exiting the context manager, Table.batch_writer starts sending
        batches of write requests to Amazon DynamoDB and automatically
        handles chunking, buffering, and retrying.

        :param entries: The data to put in the table. Each item must contain at least
                        the keys required by the schema that was specified when the
                        table was created.
        """
        try:
            with self.table.batch_writer() as writer:
                for entry in entries:
                    writer.put_item(Item=entry)
        except ClientError as err:
            logger.error(
                "Couldn't load data into table %s. Here's why: %s: %s", self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise

    def add_entry(self, 
        pipeline_name,
        hash_id,
        pipeline_version,
        registry_type,
        registry_id,
        command,
        job_status,
        default,
        tag,
        output_path,
        pipeline_tools_submit_parameters,
        cloning_parameters,
        scheduler_job_id,
        start_date,
        end_date = None,
        user_id = None,
        user_email = None
    ):
        """
        Adds an entry to the table.

        :param pipeline_name: which pipeline was executed.
        :param hash_id: unique ID given to the specific pipeline execution.
        :param pipeline_version: which version of the pipeline was used.
        :param registry_type: one of experiment_id, library_id, or gem_id, to specify the type of registry_id being recorded.
        :param registry_id: Benchling's Registry ID (SE, BB, TXL, etc.; or in the future any other object ID) the pipeline has been executed on.
        :param start_date: when was the pipeline submitted.
        :param end_date: when did the pipeline finished.
        :param command: command used to start the pipeline.
        :param job_status: final status of the current pipeline execution (FAILED, SUCCEDED, RUNNING, etc.).
        :param default: true/false, if we request the results for a specific registry_id, which pipeline execution should be returned by default.
        :param tag: a name tag that can be used to request for a specific pipeline execution for registry_id.
        :param output_path: path to where the results of the current pipeline execution are located.
        :param pipeline_tools_submit_parameters: list with the parameters used to invoke the script.
        :param cloning_parameters: dictionary with the parameters needed to clone the job on the frontend.
        :param scheduler_job_id: scheduler job ID to track the job submission.
        :param user_id: id of the user submitting the pipeline.
        :param user_email: email address of the user submitting the pipeline.
        """
        try:
            self.table.put_item(
                Item={
                    'pipeline_name': pipeline_name,
                    'hash_id': hash_id,
                    'pipeline_version': pipeline_version,
                    'registry_type': registry_type,
                    'registry_id':  registry_id,
                    'date_start': start_date,
                    'date_end': end_date,
                    'command': command,
                    'job_status': job_status,
                    'default': default,
                    'tag': tag,
                    'output_path': output_path,
                    'user_id': user_id,
                    'user_email': user_email,
                    'pipeline_tools_submit_parameters': pipeline_tools_submit_parameters,
                    'cloning_parameters': cloning_parameters,
                    'scheduler_job_id': scheduler_job_id,
                    'removed': False,
                    'removed_date': None,
                    'error_data': None,
                    'log_stream': None
                }
            )
        except ClientError as err:
            logger.error(
                "Couldn't add entry %s to table %s. Here's why: %s: %s",
                hash_id, self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise

    def get_entry(self, pipeline_name, hash_id):
        """
        Gets entry data from the table for a specific entry.

        :param pipeline_name: partition key.
        :param hash_id: sort key.
        :return: The data about the requested pipeline run.
        """
        try:
            response = self.table.get_item(
                Key={'pipeline_name': pipeline_name, 'hash_id': hash_id})
        except ClientError as err:
            logger.error(
                "Couldn't get entry %s from table %s. Here's why: %s: %s",
                hash_id, self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Item'] if "Item" in response else {}

    def update_entry(
        self, 
        pipeline_name, 
        hash_id, 
        pipeline_version=None, 
        registry_type=None, 
        registry_id=None, 
        start_date=None, 
        end_date=None, 
        command=None, 
        job_status=None, 
        default=None, 
        tag=None, 
        output_path=None,
        user_id=None,
        user_email=None,
        pipeline_tools_submit_parameters=None,
        cloning_parameters=None,
        scheduler_job_id=None,
        error_data=None,
        log_stream=None,
        removed=None,
        removed_date=None
    ):
        """
        Updates data for an entry in the table.

        :param pipeline_name: partition key (required for update).
        :param hash_id: sort key (required for update).
        :param pipeline_version: which version of the pipeline was used.
        :param registry_type: one of experiment_id, library_id, or gem_id, to specify the type of registry_id being recorded.
        :param registry_id: Benchling's Registry ID (SE, BB, TXL, etc.; or in the future any other object ID) the pipeline has been executed on.
        :param start_date: when was the pipeline submitted.
        :param end_date: when did the pipeline finished.
        :param command: command used to start the pipeline.
        :param job_status: final status of the current pipeline execution (FAILED, SUCCEDED, RUNNING, etc.).
        :param default: true/false, if we request the results for a specific registry_id, which pipeline execution should be returned by default.
        :param tag: a name tag that can be used to request for a specific pipeline execution for registry_id.
        :param output_path: path to where the results of the current pipeline execution are located.
        :param user_id: id of the user submitting or owning the pipeline.
        :param user_email: email address of the user submitting or owning the pipeline.
        :param pipeline_tools_submit_parameters: list with the parameters used to invoke the script.
        :param cloning_parameters: dictionary with the parameters needed to clone the job on the frontend.
        :param scheduler_job_id: scheduler job ID to track the job submission.
        :param error_data: a dictionary with an error message to be stored.
        :param log_stream: name of the log stream to access the job logs.
        :param removed: boolean, if the entry has been removed.
        :param removed_date: datetime for when the entry was removed.
        :return: The fields that were updated, with their new values.
        """
        def add_expression(update_expression, expression_values, expression_names, field_name, placeholder, value):
            if value is not None:
                update_expression.append(f"#{field_name}={placeholder}")
                expression_values[placeholder] = value
                expression_names[f"#{field_name}"] = field_name

        update_expression = []
        expression_values = {}
        expression_names = {}
        try:
            add_expression(update_expression, expression_values, expression_names, "user_id", ":a", user_id)
            add_expression(update_expression, expression_values, expression_names, "user_email", ":b", user_email)
            add_expression(update_expression, expression_values, expression_names, "pipeline_version", ":c", pipeline_version)
            add_expression(update_expression, expression_values, expression_names, "registry_type", ":d", registry_type)
            add_expression(update_expression, expression_values, expression_names, "registry_id", ":e", registry_id)
            add_expression(update_expression, expression_values, expression_names, "date_start", ":f", start_date)
            add_expression(update_expression, expression_values, expression_names, "date_end", ":g", end_date)
            add_expression(update_expression, expression_values, expression_names, "command", ":h", command)
            add_expression(update_expression, expression_values, expression_names, "job_status", ":i", job_status)
            add_expression(update_expression, expression_values, expression_names, "default", ":j", default)
            add_expression(update_expression, expression_values, expression_names, "tag", ":k", tag)
            add_expression(update_expression, expression_values, expression_names, "output_path", ":l", output_path)
            add_expression(update_expression, expression_values, expression_names, "pipeline_tools_submit_parameters", ":m", pipeline_tools_submit_parameters)
            add_expression(update_expression, expression_values, expression_names, "scheduler_job_id", ":n", scheduler_job_id)
            add_expression(update_expression, expression_values, expression_names, "error_data", ":o", error_data)
            add_expression(update_expression, expression_values, expression_names, "log_stream", ":p", log_stream)
            add_expression(update_expression, expression_values, expression_names, "cloning_parameters", ":q", cloning_parameters)
            add_expression(update_expression, expression_values, expression_names, "removed", ":r", removed)
            add_expression(update_expression, expression_values, expression_names, "removed_date", ":s", removed_date)

            expression_string = "set " + ", ".join(update_expression)

            response = self.table.update_item(
                Key={'pipeline_name': pipeline_name, 'hash_id': hash_id},
                ConditionExpression="attribute_exists(pipeline_name) AND attribute_exists(hash_id)",
                UpdateExpression=expression_string,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names,
                ReturnValues="UPDATED_NEW")
        except ClientError as err:
            logger.error(
                "Couldn't update entry %s in table %s. Here's why: %s: %s",
                hash_id, self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Attributes']

    def query_entries(self, pipeline_name):
        """
        Queries for pipeline runs on a specific pipeline_name.

        :param pipeline_name: The pipeline_name to query.
        :return: The list of pipeline runs that were executed for the specified pipeline_name.
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key('pipeline_name').eq(pipeline_name))
        except ClientError as err:
            logger.error(
                "Couldn't query for pipeline runs in %s. Here's why: %s: %s", pipeline_name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Items']

    def scan_entries(
        self, 
        pipeline_name=None, 
        hash_ids=[], 
        pipeline_version=None, 
        registry_type=None, 
        registry_ids=[], 
        start_date=None, 
        start_date_from=None, 
        start_date_to=None, 
        end_date=None, 
        end_date_from=None, 
        end_date_to=None, 
        job_status=None, 
        default=None, 
        tag=None, 
        user_id=None,
        user_email=None,
        removed=None
    ):
        """
        Scans for movies that were released in a range of years.
        Uses a projection expression to return a subset of data for each movie.

        :param pipeline_name: which pipeline was executed.
        :param hash_ids: list of unique hash_ids from pipeline execution.
        :param pipeline_version: which version of the pipeline was used.
        :param registry_type: which type of registry entries are we interested in (one of experiment_id, library_id, or gem_id).
        :param registry_ids: list of Benchling Registry IDs (SE, BB, TXL, etc.).
        :param start_date: when did the pipeline started (exact date).
        :param start_date_from: when did the pipeline started (start range).
        :param start_date_to: when did the pipeline started (end range).
        :param end_date: when did the pipeline ended (exact date).
        :param end_date_from: when did the pipeline ended (end range).
        :param end_date_to: when did the pipeline ended (end range).
        :param job_status: final status of the current pipeline execution (FAILED, SUCCEDED, RUNNING, etc.).
        :param default: true/false, if we request the results for a specific registry_id, which pipeline execution should be returned by default.
        :param tag: a name tag that can be used to request for a specific pipeline execution for registry_id.
        :param user_id: id of the user submitting or owning the pipeline.
        :param user_email: email address of the user submitting or owning the pipeline.
        :param removed: boolean, if the entry has been removed.
        :return: The list of pipeline runs matching the specified filters.
        """
        filter_expressions = []
        if pipeline_name is not None:
            filter_expressions.append(Key('pipeline_name').eq(pipeline_name))
        if hash_ids and len(hash_ids) > 0:
            hash_ids_query = []
            for hash_id in hash_ids:
                hash_ids_query.append(Key('hash_id').eq(hash_id))
            filter_expressions.append(reduce(operator.or_, hash_ids_query))
        if user_id is not None:
            filter_expressions.append(Attr('user_id').eq(user_id))
        if user_email is not None:
            filter_expressions.append(Attr('user_email').eq(user_email))
        if pipeline_version is not None:
            filter_expressions.append(Attr('pipeline_version').eq(pipeline_version))
        if registry_type is not None:
            filter_expressions.append(Attr('registry_type').eq(registry_type))
        if registry_ids and len(registry_ids) > 0:
            registry_ids_query = []
            if registry_type == "multi":
                registry_ids_query.append(Attr('registry_id').eq(sorted(registry_ids)))
            else:
                for registry_id in registry_ids:
                    registry_ids_query.append(Attr('registry_id').eq(registry_id))
            filter_expressions.append(reduce(operator.or_, registry_ids_query))
        if start_date is not None:
            filter_expressions.append(Attr('date_start').eq(start_date))
        elif start_date_from is not None and start_date_to is not None:
            filter_expressions.append(Attr('date_start').between(start_date_from, start_date_to))
        elif start_date_from is not None:
            filter_expressions.append(Attr('date_start').gte(start_date_from))
        elif start_date_to is not None:
            filter_expressions.append(Attr('date_start').lte(start_date_to))
        if end_date is not None:
            filter_expressions.append(Attr('date_end').eq(end_date))
        elif end_date_from is not None and end_date_to is not None:
            filter_expressions.append(Attr('date_end').between(end_date_from, end_date_to))
        elif end_date_from is not None:
            filter_expressions.append(Attr('date_end').gte(end_date_from))
        elif end_date_to is not None:
            filter_expressions.append(Attr('date_end').lte(end_date_to))
        if job_status is not None:
            filter_expressions.append(Attr('job_status').eq(job_status))
        if default is not None:
            filter_expressions.append(Attr('default').eq(default))
        if tag is not None:
            filter_expressions.append(Attr('tag').eq(tag))
        if removed is not None:
            filter_expressions.append(Attr('removed').eq(removed))

        scan_kwargs = {}
        if filter_expressions:
            scan_kwargs['FilterExpression'] =  reduce(operator.and_, filter_expressions)

        pipeline_runs = []
        try:
            done = False
            start_key = None
            while not done:
                if start_key:
                    scan_kwargs['ExclusiveStartKey'] = start_key
                response = self.table.scan(**scan_kwargs)
                pipeline_runs.extend(response.get('Items', []))
                start_key = response.get('LastEvaluatedKey', None)
                done = start_key is None
        except ClientError as err:
            logger.error(
                "Couldn't scan for pipeline runs. Here's why: %s: %s",
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise

        return pipeline_runs

    def restore_entry(self, pipeline_name, hash_id):
        """
        Restores an entry from the table by setting the removed mark to false 
        and emptying the removed_date.

        :param pipeline_name: The pipeline_name of the pipeline run to restore.
        :param hash_id: The hash_id of the pipeline run to restore.
        """
        try:
            expression_string = "set removed=:a, removed_date=:b"
            expression_values = { ':a': False, ':b': '' }
            response = self.table.update_item(
                Key={'pipeline_name': pipeline_name, 'hash_id': hash_id},
                ConditionExpression="attribute_exists(pipeline_name) AND attribute_exists(hash_id)",
                UpdateExpression=expression_string,
                ExpressionAttributeValues=expression_values,
                ReturnValues="UPDATED_NEW")
        except ClientError as err:
            logger.error(
                "Couldn't update entry %s in table %s. Here's why: %s: %s",
                hash_id, self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Attributes']

    def remove_entry(self, pipeline_name, hash_id):
        """
        Marks an entry from the table as removed and sets the date for the action.
        This is an implementation of "soft deletion".

        :param pipeline_name: The pipeline_name of the pipeline run to remove.
        :param hash_id: The hash_id of the pipeline run to remove.
        """
        try:
            expression_string = "set removed=:a, removed_date=:b"
            expression_values = { ':a': True, ':b': datetime.now().strftime("%Y-%m-%d %H:%M:%S") }
            response = self.table.update_item(
                Key={'pipeline_name': pipeline_name, 'hash_id': hash_id},
                ConditionExpression="attribute_exists(pipeline_name) AND attribute_exists(hash_id)",
                UpdateExpression=expression_string,
                ExpressionAttributeValues=expression_values,
                ReturnValues="UPDATED_NEW")
        except ClientError as err:
            logger.error(
                "Couldn't update entry %s in table %s. Here's why: %s: %s",
                hash_id, self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Attributes']

    # def delete_entry(self, pipeline_name, hash_id):
    #     """
    #     Deletes an entry from the table.

    #     :param pipeline_name: The pipeline_name of the pipeline run to delete.
    #     :param hash_id: The hash_id of the pipeline run to delete.
    #     """
    #     try:
    #         self.table.delete_item(Key={'pipeline_name': pipeline_name, 'hash_id': hash_id})
    #     except ClientError as err:
    #         logger.error(
    #             "Couldn't delete pipeline run %s. Here's why: %s: %s", hash_id,
    #             err.response['Error']['Code'], err.response['Error']['Message'])
    #         raise

    # def delete_table(self):
    #     """
    #     Deletes the table.
    #     """
    #     try:
    #         self.table.delete()
    #         self.table = None
    #     except ClientError as err:
    #         logger.error(
    #             "Couldn't delete table. Here's why: %s: %s",
    #             err.response['Error']['Code'], err.response['Error']['Message'])
    #         raise
