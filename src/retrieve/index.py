import os
import boto3
# from aws_xray_sdk_core import xray_recorder, patch_all
#
# logger = logging.getLogger()
# logger.setLeel(Logging.INFO)
# patch_all()

table_name = os.getenv("TABLE_NAME")

ddb = boto3.client('dynamodb', region_name='us-east-1')


def handler(event, context):
    short_id = event.get('short_id')

    try:
        item = ddb.get_item(TableName=table_name,Key={'short_id': {'S': str(short_id)}})
        long_url = item.get('Item').get('long_url')


    except:
        return {
            'statusCode': 301,
            'location': 'https://blog.thomasnet.com/hs-fs/hubfs/shutterstock_774749455.jpg?width=1200&name=shutterstock_774749455.jpg'
        }

    return {
        "statusCode": 301,
        "location": long_url
    }
