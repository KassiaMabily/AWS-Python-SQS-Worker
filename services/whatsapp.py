import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
IS_OFFLINE = os.environ.get('IS_OFFLINE')

class Botmaker(object):
  def __init__(self):
    super(Botmaker, self).__init__()
    api_key = os.environ.get('BOTMAKER_API_KEY', None)
    self._token = api_key

    if IS_OFFLINE:
      logger.setLevel(logging.DEBUG)

  def send_message(self, body):
    headers = {
      'Accept': 'application/json',
      'access-token': f'{self._token}'
    }

    if self._token:
      response = requests.post('https://go.botmaker.com/api/v1.0/intent/v2', headers=headers, json=body)

      try:
        response.raise_for_status()
      except requests.exceptions.Timeout:
        logger.error(f'Botmaker API error: {response.status_code}. Here is the error message: Timeout Error ocurred, program waits and retries again')
        return response.status_code, "Timeout Error ocurred, program waits and retries again"
      except requests.exceptions.TooManyRedirects:
        logger.error(f'Botmaker API error: {response.status_code}. Here is the error message: Too many redirects')
        return response.status_code, "Too many redirects"
      except requests.exceptions.HTTPError as e:
        logger.error(f'Botmaker API error: {response.status_code}. Here is the error message: {str(response.reason)}')
        return response.status_code, str(response.reason)
      except requests.exceptions.RequestException as e:
        logger.error(f'Botmaker API error: {response.status_code}. Here is the error message: {str(response.reason)}')
        return response.status_code, str(response.reason)

      logger.info(f'Message {body["ruleNameOrId"]} sent to {body["platformContactId"]}')
      return response.status_code, f'Message {body["ruleNameOrId"]} sent to {body["platformContactId"]}'

    logger.error(f'Botmaker API error: {403}. Here is the error message: No API Key was provided')
    return 403, str("No API Key was provided")
