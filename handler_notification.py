import json
import os
import boto3
from services.notification import Notifications


NOTIFICATION_TABLE = os.environ['NOTIFICATION_TABLE']
IS_OFFLINE = os.environ.get('IS_OFFLINE')

if IS_OFFLINE:
  client = boto3.resource(
    'dynamodb',
    region_name='localhost',
    endpoint_url='http://localhost:8000'
  )
else:
  client = boto3.resource('dynamodb')

def createNotification(event, context):

  if not event.get("body"):
    return {"statusCode": 400, "body": json.dumps({"detail": "No body was found"})}

  body = json.loads(event["body"])

  notifications = Notifications(client)
  notifications_exists = notifications.exists(NOTIFICATION_TABLE)
  if not notifications_exists:
    return {
      "statusCode": 500,
      "body": json.dumps({
        "detail": "Table does not exists"
      })
    }

  status_code, message, result = notifications.add_notification(body)

  return {
    "statusCode": status_code,
    "body": json.dumps({
      "detail": message,
      "result": result
    })
  }

def getNotification(event, context):

  pathParameters = event.get("pathParameters")
  if not pathParameters:
    return {"statusCode": 400, "body": json.dumps({"detail": "No pathParameters was found"})}

  notifications = Notifications(client)
  notifications_exists = notifications.exists(NOTIFICATION_TABLE)
  if not notifications_exists:
    return {
      "statusCode": 500,
      "body": json.dumps({
        "detail": "Table does not exists",
        "result": {}
      })
    }

  status_code, message, result = notifications.get_notification_by_id(pathParameters["id"])
  return {
    "statusCode": status_code,
    "body": json.dumps({
      "detail": message,
      "result": result
    })
  }

def listNotification(event, context):

  notifications = Notifications(client)
  notifications_exists = notifications.exists(NOTIFICATION_TABLE)
  if not notifications_exists:
    return {
      "statusCode": 500,
      "body": json.dumps({
        "detail": "Table does not exists",
        "result": {}
      })
    }

  status_code, message, results = notifications.scan_notifications()

  return {
    "statusCode": status_code,
    "body": json.dumps({
      "detail": message,
      "result": results
    })
  }

def deleteNotification(event, context):

  pathParameters = event.get("pathParameters")
  if not pathParameters:
    return {"statusCode": 400, "body": json.dumps({"detail": "No pathParameters was found"})}


  notifications = Notifications(client)
  notifications_exists = notifications.exists(NOTIFICATION_TABLE)
  if not notifications_exists:
    return {
      "statusCode": 500,
      "body": json.dumps({
        "detail": "Table does not exists",
      })
    }

  status_code, message, notification = notifications.delete_notification(pathParameters["id"])

  return {
    "statusCode": status_code,
    "body": json.dumps({
      "detail": message,
      "result": notification
    })
  }

def updateNotification(event, context):
  pathParameters = event.get("pathParameters")
  body = event.get("body")

  if not body:
    return {"statusCode": 400, "body": json.dumps({"detail": "No body was found"})}

  if not pathParameters:
    return {"statusCode": 400, "body": json.dumps({"detail": "No pathParameters was found"})}

  body = json.loads(body)

  notifications = Notifications(client)
  notifications_exists = notifications.exists(NOTIFICATION_TABLE)
  if not notifications_exists:
    return {
      "statusCode": 500,
      "body": json.dumps({
        "detail": "Table does not exists",
        "result": {}
      })
    }

  status_code, message, notification = notifications.update_notification(pathParameters["id"], body)
  body["notification_id"] = pathParameters["id"]

  return {
    "statusCode": status_code,
    "body": json.dumps({
      "detail": message,
      "result": notification
    })
  }
