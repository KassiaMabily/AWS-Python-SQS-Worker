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

def validate_notification_sqs(notification_id, body):
  notifications = Notifications(client)
  notifications_exists = notifications.exists(NOTIFICATION_TABLE)
  if not notifications_exists:
    return False, f"Table not exists"

  status_code, message, notification = notifications.get_notification_by_id(notification_id)

  if status_code == 200:
    send_email = notification["send_email"]
    send_whatsapp = notification["send_whatsapp"]

    if send_email:
      if "email" not in body:
        return False, f"Email was not found in body"

      for field in notification["email_fields"]:
        if field not in body["email_fields"].keys():
          return False, f"Email field {field} was not found"

    if send_whatsapp:
      if "cellphone" not in body:
        return False, f"Cellphone was not found in body"

      for field in notification["whatsapp_fields"]:
        if field not in body["whatsapp_fields"].keys():
          return False, f"Whatsapp field {field} was not found"

    return True, f"Notification body is valid"

  return False, message
