import json
import boto3
from botocore.exceptions import ParamValidationError
import os
from functools import wraps

# Initialize the Cognito client
cognito_client = boto3.client('cognito-idp', region_name='eu-west-2')

def cognito_authentication_required(groups):
    def decorator(func):
        @wraps(func)
        def wrapper(event, context, *args, **kwargs):
            try:
                access_token = event['headers'].get('x-access-token')
                # Get user attributes
                response = cognito_client.get_user(AccessToken=access_token)
                user_attributes = response['UserAttributes']
                username = response['Username']

                # Retrieve the user's groups
                user_pool_id = os.environ.get('USER_POOL_ID', 'eu-west-2_umWVAeebs')
                response = cognito_client.admin_list_groups_for_user(
                    UserPoolId=user_pool_id,
                    Username=username
                )
                user_groups = [group['GroupName'] for group in response['Groups']]

                if not any(group in user_groups for group in groups):
                    return {
                        'statusCode': 403,
                        'body': json.dumps({'error': f'Access denied. User is not in the required groups: {groups}'})
                    }
                
                # Call the original function if authentication and authorization pass
                return func(event, context, *args, **kwargs)

            except (IndexError, ParamValidationError, cognito_client.exceptions.NotAuthorizedException):
                return {
                    'statusCode': 401,
                    'body': json.dumps({'error': 'Alchelign Error: Unauthorized or Invalid access token.'})
                }

        return wrapper
    return decorator

# Example usage
# @cognito_authentication_required(['eu-west-2_umWVAeebs_Okta', 'another_group'])
# def handler(event, context):
#     # Your actual function logic here
#     return {
#         'statusCode': 200,
#         'body': json.dumps({'message': 'Success!'})
#     }
