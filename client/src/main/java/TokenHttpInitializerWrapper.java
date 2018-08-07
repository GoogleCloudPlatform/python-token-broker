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

    private String fetchToken() throws IOException {
        javax.net.ssl.HttpsURLConnection.setDefaultHostnameVerifier((hostname, sslSession) -> hostname.equals(tokenHost));
        String urlString = "https://" + tokenHost + ":4443/token";
        URL url = new URL(null, urlString);
        HttpsURLConnection con = (HttpsURLConnection) url.openConnection();
        return new java.util.Scanner(con.getInputStream()).useDelimiter("\\A").next();
    }

    TokenHttpInitializerWrapper(String tokenHost) {
        this.tokenHost = tokenHost;
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