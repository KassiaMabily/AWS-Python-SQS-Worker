import json
import os
import boto3
from services.log import Log


LOG_TABLE = os.environ['LOG_TABLE']
IS_OFFLINE = os.environ.get('IS_OFFLINE')

if IS_OFFLINE:
  client = boto3.resource(
    'dynamodb',
    region_name='localhost',
    endpoint_url='http://localhost:8000'
  )
else:
  client = boto3.resource('dynamodb')


def listLog(event, context):

  logs = Log(client)
  logs_exists = logs.exists(LOG_TABLE)
  if not logs_exists:
    return {
      "statusCode": 500,
      "body": json.dumps({
        "detail": "Table log does not exists",
        "result": {}
      })
    }

  status_code, message, results = logs.scan_log()

  return {
    "statusCode": status_code,
    "body": json.dumps({
      "detail": message,
      "result": results
    })
  }
