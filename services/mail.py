import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Subject
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
IS_OFFLINE = os.environ.get('IS_OFFLINE')
FROM_EMAIL = 'no-reply@lumaensino.com.br'

class Sendgrid(object):

    def __init__(self):
        super(Sendgrid, self).__init__()
        api_key = os.environ.get('SENDGRID_API_KEY', None)
        self._token = api_key

        if IS_OFFLINE:
            logger.setLevel(logging.DEBUG)


    def send_template_email(self, email_id, to_emails, dynamic_template_data):
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_emails
        )

        message.dynamic_template_data = dynamic_template_data
        message.template_id = email_id

        if self._token:
            try:
                sg = SendGridAPIClient(self._token)
                response = sg.send(message)
            except Exception as e:
                status_code = type(e).__name__
                message = f'{str(e)}'

                logger.error(f'SendGrid API error: {status_code}. Here is the error message: {message}')

                return status_code, message
            else:
                status_code = response.status_code
                formatted_emails = ",".join("(%s,%s)" % tup for tup in to_emails)
                message = f'Message {email_id} sent to {formatted_emails}'
                logger.info(message)
                return response.status_code, message

        logger.error(f'SendGrid API error: {403}. Here is the error message: No API Key was provided')
        return 403, str("No API Key was provided")
