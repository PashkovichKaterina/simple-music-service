import boto3
import os
import json


def get_secret_value(secret_key):
    client = boto3.client(
        service_name="secretsmanager",
        region_name=os.environ["SECRETS_MANAGER_REGION_NAME"]
    )
    response = client.get_secret_value(SecretId=os.environ["SECRET_ID"])
    secret_values = json.loads(response["SecretString"])
    return secret_values[secret_key]
