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

import com.google.api.client.auth.oauth2.Credential;
import com.google.api.client.googleapis.auth.oauth2.GoogleCredential;
import com.google.api.client.http.HttpRequest;
import com.google.api.client.http.HttpRequestInitializer;
import com.google.api.client.http.HttpStatusCodes;

import javax.net.ssl.HttpsURLConnection;
import java.io.IOException;
import java.net.URL;

public class TokenHttpInitializerWrapper implements HttpRequestInitializer {

    private final String tokenHost;

    public TokenHttpInitializerWrapper(String tokenHost) {
        this.tokenHost = tokenHost;
    }

    private String fetchToken() throws IOException {
        String urlString = "https://" + tokenHost + ":4443/token";
        URL url = new URL(null, urlString);
        HttpsURLConnection con = (HttpsURLConnection) url.openConnection();
        return new java.util.Scanner(con.getInputStream()).useDelimiter("\\A").next();
    }

    private Credential createCredential() throws IOException {
        String accessToken = fetchToken();
        // Do not print in production environment
        System.out.println("Test token: " + accessToken);
        return new GoogleCredential().setAccessToken(accessToken);
    }

    @Override
    public final void initialize(final HttpRequest request) throws IOException {
        System.out.println("Initializing " + TokenHttpInitializerWrapper.class.getSimpleName());
        // Refreshes the token on every request
        request.setInterceptor(createCredential());
        request.setUnsuccessfulResponseHandler(
                (failedRequest, response, supportsRetry) -> {
                    if (response.getStatusCode() == HttpStatusCodes.STATUS_CODE_UNAUTHORIZED) {
                        // Try to refresh token if the request failed
                        request.setInterceptor(createCredential());
                        System.out.println("Retrying with the new token");
                        return true;
                    }
                    return false;
                });
    }
}
