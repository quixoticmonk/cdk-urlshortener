import os
import json
import boto3
from string import ascii_uppercase, ascii_lowercase, digits
from time import strftime, time
from aws_xray_sdk_core import xray_recorder, patch_all

logger = logging.getLogger()
logger.setLeel(Logging.INFO)
patch_all()

domain_url = os.getenv('DOMAIN_URL')
expiry_time = os.getenv("EXPIRY_TIME")
table_name = os.getenv("TABLE_NAME")

ddb = boto3.resource('dynamodb', region_name='us-east-1')


def generate_id():
    _chars = digits + ascii_lowercase + ascii_uppercase
    _base = len(_chars)
    _return_value = []
    _id = int(time())

    while _id > 0:
        _val = _id % _base
        _return_value.append(_chars[_val])
        _id = _id // _base

    return "".join(_return_value[::-1])


def handler(event, context):
    print(event)
    _long_url = event.get('body').get('long_url')
    _short_id = generate_id()
    _short_url = domain_url + _short_id
    _timestamp = strftime("%Y-%m-%dT%H:%M:%S")
    _ttl_value = int(time()) + int(86400)

    ddb.Table(table_name).put_item(
        Item={
            'short_id': _short_id,
            'created_at': _timestamp,
            'ttl': int(_ttl_value),
            'short_url': _short_url,
            'long_url': _long_url
        }
    )
    _gateway_response = '{"short_id":"' + \
        _short_url + '","long_url":"' + _long_url + '"}'
    return {"statusCode": 200, "body": _gateway_response}
