import imp
import json
import logging
import os
import boto3
from services.mail import Sendgrid
from services.whatsapp import Botmaker
from services.notification import Notifications
from services.log import Log
from utils import validate_notification_sqs
from datetime import datetime

logger = logging.getLogger(__name__)


QUEUE_URL = os.getenv('QUEUE_URL')
SQS = boto3.client('sqs')
NOTIFICATION_TABLE = os.environ['NOTIFICATION_TABLE']
LOG_TABLE = os.environ['LOG_TABLE']
IS_OFFLINE = os.environ.get('IS_OFFLINE')

if IS_OFFLINE:
    logger.setLevel(logging.DEBUG)
    client = boto3.resource(
        'dynamodb',
        region_name='localhost',
        endpoint_url='http://localhost:8000'
    )
else:
    client = boto3.resource('dynamodb')


def producer(event, context):
    now = datetime.now()
    status_code = 200
    message = ''
    body = event.get('body')
    pathParameters = event.get('pathParameters')
    if not body:
        log.add_log("LUMA", now, 400, "No body was found", "api_call", "", "", "")
        return {'statusCode': 400, 'body': json.dumps({'message': 'No body was found'})}

    if not pathParameters:
        log.add_log("LUMA", now, 400, "No notification Id was provided", "api_call", "", "", "")
        return {'statusCode': 400, 'body': json.dumps({'message': 'No notification Id was provided'})}

    log = Log(client)
    log_exists = log.exists(LOG_TABLE)
    if not log_exists:
        logger.info(f'500 table log does not exists')
        return

    is_valid, message = validate_notification_sqs(pathParameters['id'], json.loads(body))
    if not is_valid:
        log.add_log("LUMA", now, 400, message, "api_call", "", "", "")
        return {'statusCode': 400, 'body': json.dumps({'detail': message})}

    try:
        message_attrs = {
            'notification_id': {'StringValue': pathParameters['id'], 'DataType': 'String'}
        }
        SQS.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=event['body'],
            MessageAttributes=message_attrs,
        )
        message = f'Message {pathParameters["id"]} accepted!'
    except Exception as e:
        logger.exception('Sending message to SQS queue failed!')

        message = str(e)
        status_code = 500

    log.add_log("LUMA", now, status_code, message, "api_call", "", "", "")
    return {'statusCode': status_code, 'body': json.dumps({'detail': message})}


def consumer(event, context):
    for record in event['Records']:
        now = datetime.now()
        body = json.loads(record["body"])
        notification_id = record["messageAttributes"]["notification_id"]["stringValue"]

        notifications = Notifications(client)
        notifications_exists = notifications.exists(NOTIFICATION_TABLE)
        if not notifications_exists:
            logger.info(f'500 table notification does not exists')
            return

        log = Log(client)
        log_exists = log.exists(LOG_TABLE)
        if not log_exists:
            logger.info(f'500 table log does not exists')
            return

        status_code, message, notification = notifications.get_notification_by_id(notification_id)
        send_email = notification["send_email"]
        send_whatsapp = notification["send_whatsapp"]

        if status_code == 200:
            if send_email:
                to_emails = [(body["email"], "full_name"),]

                sendgrid = Sendgrid()
                status_code, message = sendgrid.send_template_email(notification["email_id"], to_emails, body["email_fields"])

                log.add_log("LUMA", now, status_code, message,"email", notification["email_id"], notification.notification_id, notification.title)

            if send_whatsapp:
                cellphone = body["cellphone"]

                payload = {
                    "chatPlatform": "whatsapp",
                    "chatChannelNumber": "5527996989507",
                    "platformContactId": cellphone,
                    "ruleNameOrId": notification["template_name"],
                    "params": body["whatsapp_fields"]
                }

                whatsapp = Botmaker()
                status_code, message = whatsapp.send_message(payload)

                log.add_log("LUMA", now, status_code, message, "whatsapp", cellphone, notification.notification_id, notification.title)
        else:
            logger.error(f"Couldn't find the notification {notification_id} to send. Here is the error message: {message}")
