#!/usr/bin/env python3

# Copyright 2019 Google Inc.
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
import ssl
import sys
import logging
import os
import traceback
import json
from http.server import BaseHTTPRequestHandler,HTTPServer
from google.auth.transport.requests import AuthorizedSession
from google import auth

class LoggingSSLSocket(ssl.SSLSocket):
    def accept(self, *args, **kwargs):
        logging.info("Accepting connection")

        try:
            result = super(LoggingSSLSocket, self).accept(*args, **kwargs)
            logging.info("Accepted connection.")
        except:
            logging.info("Connection error: " + traceback.format_exc())
            raise

        return result

    def do_handshake(self, *args, **kwargs):
        logging.info("Starting handshake")
        
        try:
            result = super(LoggingSSLSocket, self).do_handshake(*args, **kwargs)
            logging.info("Handshake complered")
        except:
            logging.info("Handshake error: " + traceback.format_exc())
            raise
            
        return result

class Handler(BaseHTTPRequestHandler):
    # Token lifetime in seconds, maximum one hour.
    TOKEN_LIFETIME = 600
    
    # Scopes to use for token.
    TOKEN_SCOPE = "https://www.googleapis.com/auth/cloud-platform"

    def create_access_token(self):
        credentials, project = auth.default()
        
        response = AuthorizedSession(credentials).post(
            "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/" + Handler.role_account + ":generateAccessToken", 
            data={
                "lifetime": "%ds" % Handler.TOKEN_LIFETIME,
                "scope" : [Handler.TOKEN_SCOPE]})
                
        return json.loads(response.content.decode("utf-8"))["accessToken"]

    def log_message(self, format, *args):
        logging.info(format % args)

    def log_error(self, format, *args):
        logging.error(format % args)

    def do_GET(self):
        try:
            cert = self.connection.getpeercert()
            logging.info("Client certificate: " + str(cert))

            # Authenticate client.
            ip = self.connection.getpeername()[0]
            host = socket.gethostbyaddr(ip)
            ssl.match_hostname(cert, host[0])
            
            logging.info("Client %s authenticated" % str(host))
            
            if self.path == "/token":
                token = self.create_access_token()
            
                self.send_response(200)
                self.wfile.write(token.encode("utf-8"))
                
            else:
                self.send_error(404)
                
        except ssl.CertificateError as e:
            logging.exception("Certificate validation failed")
            self.send_error(403)
        
        except Exception as e:
            logging.exception("Failed to handle request")
            self.send_error(500)

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    if len(sys.argv) < 6:
        print("Usage: %s listen-ip listen-port server-certitficate role-account ca-certificate")
        sys.exit(1)
        
    listen_ip = sys.argv[1]
    listen_port = int(sys.argv[2])
    server_cert = sys.argv[3]
    role_account = sys.argv[4]
    ca_cert = sys.argv[5]

    # Create HTTPS server on port 443
    Handler.role_account = role_account
    httpd = HTTPServer((listen_ip, listen_port), Handler)
    
    # Create a socket and check client certificate for TLS handshake. 
    httpd.socket = LoggingSSLSocket(
        httpd.socket, 
        certfile = server_cert, 
        server_side = True, 
        cert_reqs = ssl.CERT_REQUIRED, 
        ca_certs = ca_cert)
        
    logging.info("Starting server on %s:%s" % (listen_port, listen_port))

    httpd.serve_forever()
