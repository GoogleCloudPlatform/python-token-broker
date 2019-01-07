"""
PYTHON LIBRARY FOR ACCESS TOKEN BROKER
"""
import logging
import sys
import requests
import google.oauth2.credentials
from google.cloud import storage, bigquery
from google.auth.transport.urllib3 import AuthorizedHttp
from googleapiclient.discovery import build

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class TokenHttpInitializerWrapper:
    """
    CLASS TO INSTANTIATE API CALL TO ACCESS TOKEN SERVER
    """
    __token_host = None
    __client_certificate = None

    def __init__(self, token_host, client_certificate):
        """
        CONSTRUCTOR FUNCTION
        """
        self.__token_host = token_host
        self.__client_certificate = client_certificate

    def __fetch_token(self):
        """
        PRIVATE FUNCTION TO FETCH TOKEN FROM THE ACCESS TOKEN BROKER SERVER
        """
        url_string = "https://{}:4443/token".format(self.__token_host)
        token_resposne = requests.get(
            url_string,
            verify=False,
            cert=self.__client_certificate
        )
        logging.info(url_string)
        return token_resposne.content
    
    def __create_credential(self):
        """
        PRIVATE FUNCTION TO CREATE CREDENTIALS
        """
        access_token = self.__fetch_token()
        print(access_token)
        credentials = google.oauth2.credentials.Credentials(access_token)
        return credentials
    
    def initialize(self, api, version):
        """
        DEFAULT INITIALIZATION METHOD
        SUPPORTED APIS : https://developers.google.com/api-client-library/python/apis/
        """
        logging.info("Initializing %s", self.__class__.__name__)
        credentials = self.__create_credential()
        authed_http = AuthorizedHttp(credentials)
        service = build(api, version, http=authed_http)
        return service
    
    def initialize_storage(self, project_id=None):
        """
        INITIALIZING STORAGE CLIENT
        """
        storage_client = storage.Client(
            credentials=self.__create_credential(),
            project=project_id
        )
        return storage_client
    
    def initialize_bigquery(self, project_id=None):
        """
        INITIALIZING BIGQUERY CLIENT
        """
        bigquery_client = bigquery.Client(
            credentials=self.__create_credential(),
            project=project_id
        )
        return bigquery_client
