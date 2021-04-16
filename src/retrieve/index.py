import os
import boto3

table_name = os.getenv("TABLE_NAME")

ddb = boto3.resource('dynamodb', region_name='us-east-1').Table(table_name)


def handler(event):
    short_id = event.get('short_id')

    try:
        item = ddb.get_item(Key={'short_id': short_id})
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
