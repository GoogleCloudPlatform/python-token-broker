"""
MODULE FOR TESTING TOKEN BROKER SERVICE
"""
# pylint: disable=broad-except
import sys
import os
import logging
from time import time
from token_initializer import TokenHttpInitializerWrapper

def upload_stream_resumable(name, byte_stream, bucket_name):
    """
    This python application uploads a file by
    passing an access token returned by Token Broker.
    When the upload request is sent, GCP checks to see whether the account
    associated with the supplied access token has storage write permissions
    on the designated bucket.
    If the account has such permissions, the upload executes; otherwise,
    the command fails and returns a 403 HTTP status code.
    You must write your code to anticipate the possibility that a granted token
    might no longer work. For example, a token might stop working if the user
    account has exceeded a certain number of token requests.
    """
    try:
        token_broker_obj = TokenHttpInitializerWrapper(URL_STRING, CLIENT_CERTIFICATE)
        storage_client = token_broker_obj.initialize_storage(project_id='accesstokenbroker')
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(name)
        blob.upload_from_string(byte_stream)
        logging.info(name)
        logging.info(byte_stream)
        logging.info(bucket)
    except Exception as err:
        logging.exception(err)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

TOKEN_BROKER_HOSTNAME = os.environ['TOKEN_BROKER_DNS']
CLIENT_CERTIFICATE = os.environ['CLIENT_CERTIFICATE']
KEY_STORE = os.environ['KEY_STORE']

logging.info("Using client certificate at %s", CLIENT_CERTIFICATE)
logging.info("Using key store at %s", KEY_STORE)

URL_STRING = TOKEN_BROKER_HOSTNAME
logging.info("Connectiong to %s", URL_STRING)

upload_stream_resumable(
    "{}.csv".format(str(int(time()))),
    "test".encode(),
    sys.argv[1]
)
