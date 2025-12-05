# aws_utils.py
import boto3
from botocore.config import Config
import os

REGION = os.getenv("AWS_REGION", "us-east-1")
BOTO_CONFIG = Config(retries={'max_attempts': 5, 'mode': 'standard'})

def client(service):
    return boto3.client(service, region_name=REGION, config=BOTO_CONFIG)

def resource(service):
    return boto3.resource(service, region_name=REGION, config=BOTO_CONFIG)
