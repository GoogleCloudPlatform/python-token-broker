/*
 * Copyright (C) 2018 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */

package com.google.cloud.tokenbroker;

import com.google.api.client.googleapis.javanet.GoogleNetHttpTransport;
import com.google.api.client.googleapis.json.GoogleJsonResponseException;
import com.google.api.client.googleapis.media.MediaHttpUploader;
import com.google.api.client.http.*;
import com.google.api.client.json.JsonFactory;
import com.google.api.client.json.jackson2.JacksonFactory;
import javax.net.ssl.HttpsURLConnection;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.util.Date;

/**
 * This java application uploads a file by creating Java SDK client and passing an access token returned by Token Broker. When the upload request is sent, GCP checks to see whether the account associated with the supplied access token has storage write permissions on the designated bucket. If the account has such permissions, the upload executes; otherwise, the command fails and returns a 403 HTTP status code. You must write your code to anticipate the possibility that a granted token might no longer work. For example, a token might stop working if the user account has exceeded a certain number of token requests.
*/
public class AuthTest {

    private static String TOKEN_BROKER_HOSTNAME = System.getProperty("token-broker.host");

    public static void main(String[] args) throws Exception {
        System.out.println("Using client certificate at " + System.getProperty("javax.net.ssl.keyStore"));
        System.out.println("Using key store at " + System.getProperty("javax.net.ssl.trustStore"));
        HttpsURLConnection.setDefaultHostnameVerifier((hostname, sslSession) -> hostname.equals(TOKEN_BROKER_HOSTNAME));
        String urlString = "https://" + TOKEN_BROKER_HOSTNAME + ":4443/token";
        System.out.println("Connecting to " + urlString);

        System.out.println("Loading data to GCS");
        String loadName = new Date().toString() + ".csv";

        uploadStreamResumable(loadName,
                new ByteArrayInputStream("test".getBytes(StandardCharsets.UTF_8.name())),
                args[0]);
        System.out.println("Load complete");
    }

    private static final JsonFactory JSON_FACTORY = JacksonFactory.getDefaultInstance();

    /**
     * Uploads data to an object in a bucket.
     *
     * @param name the name of the destination object.
     * @param stream the data - for instance, you can use a FileInputStream to upload a file.
     */
    private static void uploadStreamResumable(String name,
                                             InputStream stream,
                                             String bucket) throws IOException, GeneralSecurityException {
        InputStreamContent mediaContent =
                new InputStreamContent("text/plain", stream);
        mediaContent.setLength(mediaContent.getLength());

        HttpTransport httpTransport = GoogleNetHttpTransport.newTrustedTransport();
        HttpRequestInitializer httpRequestInitializer = new TokenHttpInitializerWrapper(TOKEN_BROKER_HOSTNAME);
        GenericUrl requestUrl = new GenericUrl("https://www.googleapis.com/upload/storage/v1/b/"+bucket+"/o?uploadType=resumable&name="+name);
        MediaHttpUploader uploader = new MediaHttpUploader(mediaContent, httpTransport, httpRequestInitializer);
        HttpResponse response = uploader.upload(requestUrl);
        if (!response.isSuccessStatusCode()) {
            throw  GoogleJsonResponseException.from(JSON_FACTORY, response);
        }
    }

}
