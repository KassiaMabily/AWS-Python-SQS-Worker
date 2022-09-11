import uuid
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class Notifications:
  _all_fields = [ 'title', 'send_email', 'send_whatsapp', 'email_id', 'email_fields', 'template_name', 'whatsapp_fields' ]

  def __init__(self, dyn_resource):
    """
    :param dyn_resource: A Boto3 DynamoDB resource.
    """
    self.dyn_resource = dyn_resource
    self.table = None

  def exists(self, table_name):
    """
    Determines whether a table exists. As a side effect, stores the table in
    a member variable.
    :param table_name: The name of the table to check.
    :return: True when the table exists; otherwise, False.
    """
    try:
      table = self.dyn_resource.Table(table_name)
      table.load()
      exists = True
    except ClientError as err:
      if err.response['Error']['Code'] == 'ResourceNotFoundException':
        exists = False
      else:
        logger.error(
          "Couldn't check for existence of %s. Here's why: %s: %s",
          table_name,
          err.response['Error']['Code'], err.response['Error']['Message']
        )
        raise
    else:
      self.table = table
    return exists

  def add_notification(self, data):
    """
    Adds a notification to the table.
    :param data: The dict that contains all fields.
    """
    try:
      notification_id = str(uuid.uuid4())
      data['notification_id'] =  notification_id

      is_valid, message = self.is_valid(data)
      if not is_valid:
        return 400, message, {}

      self.table.put_item(Item=data)

    except ClientError as err:
      status_code = err.response['ResponseMetadata']['HTTPStatusCode']
      message = f"Couldn't add notification {data['title']} to table {self.table.name}. Here's why: {err.response['Error']['Code']}: {err.response['Error']['Message']}"
      logger.error(f'{status_code}: {message}')
      return status_code, message, {}

    else:
      return 200, f'Notification {data["title"]} created successfully', data

  def get_notification_by_id(self, notification_id):
    """
    Gets notification data from the table for a specific notification identifier.
    :param notification_id: The notification hash identifier.
    :return: The data about the requested notification.
    """
    try:
      response = self.table.get_item(Key={'notification_id': notification_id})
    except ClientError as err:
      status_code = err.response['ResponseMetadata']['HTTPStatusCode']
      message = f"Couldn't get notification {notification_id} to table {self.table.name}. Here's why: {err.response['Error']['Code']}: {err.response['Error']['Message']}"
      logger.error(f'{status_code}: {message}')
      return status_code, message, {}
    else:
      item = response.get("Item")
      if item is not None:
        return 200, f'Notification was successfully retrieved', item
      else:
        return 404, f'Notification not found', {}

  def scan_notifications(self):
    """
    Scans for all notifications.
    :return: The list of notifications.
    """
    notifications = []
    try:
      response = self.table.scan()
      notifications = response.get('Items', [])
    except ClientError as err:
      status_code = err.response['ResponseMetadata']['HTTPStatusCode']
      message = f"Couldn't retrieves notification of table {self.table.name}. Here's why: {err.response['Error']['Code']}: {err.response['Error']['Message']}"
      logger.error(f'{status_code}: {message}')
      return status_code, message, []

    return 200, "Notifications retrieved successfully", notifications

  def delete_notification(self, notification_id):
    """
    Deletes a notification from the table.
    :param notification_id: The identity of the notification to delete.
    """
    try:
      status_code, message, notification = self.get_notification_by_id(notification_id)
      self.table.delete_item(
        Key={
          'notification_id': notification_id
        }
      )
    except ClientError as err:
      status_code = err.response['ResponseMetadata']['HTTPStatusCode']
      message = f"Couldn't delete notification {notification_id} of table {self.table.name}. Here's why: {err.response['Error']['Code']}: {err.response['Error']['Message']}"
      return status_code, message, notification
    else:
      return 200, f"Notification {notification_id} deleted successfully", notification

  def update_notification(self, notification_id, payload):
    """
    Updates a notification in the table.
    :param notification_id: The identity of the notification to update.
    :param payload: The payload to update the notification with.
    """

    notification = self.get_notification_by_id(notification_id)
    is_valid, message = self.is_valid(payload)
    if not is_valid:
      return 400, message, notification

    try:
      response = self.table.update_item(
        Key={'notification_id': notification_id},
        UpdateExpression="set title=:t, send_email=:se, send_whatsapp=:sw, email_id=:e, email_fields=:ef, template_name=:tn, whatsapp_fields=:wf",
        ExpressionAttributeValues={
          ':t': str(payload["title"]),
          ':se': payload["send_email"],
          ':sw': payload["send_whatsapp"],
          ':e': str(payload["email_id"]),
          ':ef': payload["email_fields"],
          ':tn': str(payload["template_name"]),
          ':wf': payload["whatsapp_fields"],
        },
        ReturnValues="UPDATED_NEW"
      )
    except ClientError as err:
      status_code = err.response['ResponseMetadata']['HTTPStatusCode']
      message = f"Couldn't update notification {notification_id} of table {self.table.name}. Here's why: {err.response['Error']['Code']}: {err.response['Error']['Message']}"
      return status_code, message, notification
    else:
      return 200, f'Notification {payload["title"]} updated successfully', payload

  def is_valid(self, body):
    if not "title" in body:
      return False, "No title was provided"

    if not "send_email" in body or not "send_whatsapp" in body:
      return False, "Please, toggle the send_email or whatsapp"

    # Validacao de email
    if body["send_email"] and (not "email_id" in body or len(body["email_id"]) <= 0):
      return False, "No email template id was provided"

    if body["send_email"] and (("email_fields" in body and len(body["email_fields"]) <= 0) or (not "email_fields" in body)):
      return False, "No email fields were provided"

    # Validacao de whatsapp
    if body["send_whatsapp"] and (not "template_name" in body or len(body["template_name"]) <= 0):
      return False, "No template name was provided"

    if body["send_whatsapp"] and (("whatsapp_fields" in body and len(body["whatsapp_fields"]) <= 0) or (not "whatsapp_fields" in body)):
      return False, "No whatsapp fields were provided"

    return True, "OK"

  def format_notification(item):
    return {
      'title': item.get('title').get('S'),
      'notification_id': item.get('notification_id').get('S'),
      'email_id': item.get('email_id').get('S'),
      'template_name': item.get('template_name').get('S'),
      'email_fields': [ i["S"] for i in item.get('email_fields').get('L') ],
      'whatsapp_fields': [ i["S"] for i in item.get('whatsapp_fields').get('L') ],
      'send_email': item.get('send_email').get('BOOL'),
      'send_whatsapp': item.get('send_whatsapp').get('BOOL'),
    }
