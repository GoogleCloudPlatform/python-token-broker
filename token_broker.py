#!/usr/bin/env python3

# Copyright 2018 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import socket
from http.server import BaseHTTPRequestHandler,HTTPServer
import ssl
import sys
import logging
import os
import traceback
from google.auth.transport.requests import AuthorizedSession
from google import auth
import json

# See README.md file for instructions
# HTTPS server address
SERVER = sys.argv[1]
# HTTPS server port
SERVER_PORT = int(sys.argv[2])
# Server certificate location (must include the private key)
SERVER_CERTIFICATE = sys.argv[3]
# Service account for which a token is generated
SERVICE_ACCOUNT = sys.argv[4]
# Certificate bundle
CA_BUNDLE = sys.argv[5]
os.environ['REQUESTS_CA_BUNDLE'] = CA_BUNDLE

# Generates an access token based on the service account attached to the GCE instance
def get_access_token():
    credentials, project = auth.default()
    authed_session = AuthorizedSession(credentials)
    # You can limit scope and lifetime of the token
    logging.info("Generating token")
    response = authed_session.post('https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/' + SERVICE_ACCOUNT + ':generateAccessToken', data={"lifetime": "600s" ,"scope" : ["https://www.googleapis.com/auth/cloud-platform"]})
    return json.loads(response.content.decode("utf-8"))["accessToken"]

class LoggingSSLSocket(ssl.SSLSocket):

    def accept(self, *args, **kwargs):
        logging.info('Accepting connection')
        try:
            result = super(LoggingSSLSocket, self).accept(*args, **kwargs)
        except:
            logging.info("Connection error: " + traceback.format_exc())
            raise
        logging.info('Done accepting connection.')
        return result

    def do_handshake(self, *args, **kwargs):
        logging.info('Starting handshake')
        try:
            result = super(LoggingSSLSocket, self).do_handshake(*args, **kwargs)
        except:
            logging.info("Handshake error: " + traceback.format_exc())
            raise
        logging.info('Done with handshake.')
        return result

class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        logging.info(format%args)

    def log_error(self, format, *args):
        logging.error(format%args)

    def do_GET(self):
        cert = self.connection.getpeercert()
        logging.info("Client certificate: " + str(cert))

        # Verify request origin
        ip = self.connection.getpeername()[0]
        host = socket.gethostbyaddr(ip)
        ssl.match_hostname(cert, host[0])
        
        logging.info("Client host: " + str(host))
        
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        if self.path == '/token':
            token = get_access_token()
            self.wfile.write(token.encode("utf-8"))
        return

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Create HTTPS server on port 443
httpd = HTTPServer((SERVER, SERVER_PORT), Handler)
# Create a socket and check client certificate for TLS handshake. ca_certs parameter points to the file with CA certificates.
httpd.socket = LoggingSSLSocket(httpd.socket, certfile = SERVER_CERTIFICATE, server_side = True, cert_reqs = ssl.CERT_REQUIRED, ca_certs = CA_BUNDLE)
logging.info("Starting server on " + SERVER + ":" + str(SERVER_PORT))

# Start the server
httpd.serve_forever()
