import logging
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import uuid
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)

class Log:
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

  def add_log(self, username, dt, status_code, message, type_message, to_user, notification_id, notification_title):
    try:

      self.table.put_item(
        Item={
          'log_id': str(uuid.uuid4()),
          'user': username,
          'created_at': dt.strftime("%FT%T"),
          'status': str(status_code),
          'notification_id': notification_id,
          'notification_title': notification_title,
          'message': message,
          'type': type_message,
          'to_user': to_user
        }
      )

    except ClientError as err:
      status_code = err.response['ResponseMetadata']['HTTPStatusCode']
      message = f"Couldn't add log {type_message} to {to_user} to table {self.table.name}. Here's why: {err.response['Error']['Code']}: {err.response['Error']['Message']}"
      logger.error(f'{status_code}: {message}')
      return status_code, message

    else:
      return 200, f'Log {type_message} {self.table.name} created successfully to {to_user}'

  def scan_log(self):
    logs = []
    now = datetime.now()
    seven_days_ago = now - timedelta(days=7)

    filterDate = Key('created_at').between(seven_days_ago.strftime("%FT%T"), now.strftime("%FT%T"))

    try:
      response = self.table.scan()
      logs = response.get('Items', [])
    except ClientError as err:
      status_code = err.response['ResponseMetadata']['HTTPStatusCode']
      message = f"Couldn't retrieves logs of table {self.table.name}. Here's why: {err.response['Error']['Code']}: {err.response['Error']['Message']}"
      logger.error(f'{status_code}: {message}')
      return status_code, message, []

    return 200, "Logs retrieved successfully", logs
