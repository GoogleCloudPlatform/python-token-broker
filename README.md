
# Creating Token Broker Test Instance

1. Enable Google Cloud Platform IAM token API: https://console.developers.google.com/apis/api/iamcredentials.googleapis.com/overview
1. Create a service account with IAM roles that must be granted to your client-side application. This service account will be impersonated by the client application, i.e. the client application will have access to all resources that this service account has. In this example, the client service account has write access to GCS.
1. Create a GCE instance in a secured subnet and assign it a service account with a role called *Service Account Token Creator*. This role is required to generate IAM tokens. We will use *token-broker* as the name of the instance going forward. These instructions were written for Debian but the python script that runs Token Broker can be run on any operating system supported by Google Cloud SDK.

   1. Ssh to the created token broker GCE instance and run the following command:
   1. Pull a repository with Token Broker code from the github repository to the new GCE instance.
   1. Cd to the token-broker directory and run the following command:

          openssl req -new -x509 -keyout ./token_broker.pem -out ./token_broker.pem -days 365 -nodes
   1. Check that a private/public key pair was created in `token_broker.pem` file. This key will be used for a TLS certificate used by the Token Broker server.

 1. Create a client-side GCE instance that will request tokens from the token broker server. We will use *tb-client* as the name of the client instance going forward.
    1. Ssh to the new instance and install jdk with maven:

           sudo apt-get install openjdk-9-jdk maven
    1. Create a client key store:

           keytool -genkey -dname "cn=CLIENT" -alias truststorekey -keyalg RSA -keystore ./client-truststore.jks -keypass 123456 -storepass 123456 # Use a stronger password for production usage
    1. Copy the server certificate to the client node. Only a public portion of the key is required in production.

           gcloud compute scp token-broker:~/token_broker.pem .
    1. Convert the key from PEM to DER format:

           openssl x509 -outform der -in token_broker.pem -out token_broker.der
    1. Add the server key to the client key store:

           keytool -import -alias token_broker -keystore client-truststore.jks -file token_broker.der
    1. Add standard java keys to the client key store (when prompted enter the password "changeit"):

           sudo keytool -importkeystore -srckeystore /usr/lib/jvm/java-9-openjdk-amd64/lib/security/cacerts -destkeystore client-truststore.jks -srcstoretype JKS -deststorepass 123456o
    1. Find the clinet FQDN:

           curl http://metadata.google.internal/computeMetadata/v1/instance/hostname  -H "Metadata-Flavor: Google"
    1. Generate a client key used for authentication against the Token Broker server:

           openssl req -new -x509 -keyout client.pem -out client.pem -days 365 -nodes
    1. Convert the client certificate to PFX format:

           openssl pkcs12 -export -in client.pem -inkey client.pem -out client.p12
    1. Copy the client certificate to the TB instance:

           gcloud compute scp client.pem token-broker:~

1. Ssh back to the token broker instance and import the client certificate to the server key store:

       cat /etc/ssl/certs/ca-certificates.crt client.pem > ~/ca-bundle.crt
1. Install google-auth python library:

       pip3 install google-auth

1. Run the token broker server:

       ./token_broker.py $(curl -s http://metadata.google.internal/computeMetadata/v1/instance/hostname -H "Metadata-Flavor: Google") 4443 token_broker.pem <Service account email from Step #2> ca-bundle.crt

   Verify successful server start.

1. On the client machine download the repository and change directory to `client`. This directory has client code that uploads data to GCS using the token broker.

1. Set environment variables and build the client application:

       export PATH_TO_REPO=<Path to github repo>
       cd $PATH_TO_REPO/client/Authtest
       export TB_INSTANCE_NAME=token-broker
       mvn package && cp target/broker-client-1.0-SNAPSHOT-jar-with-dependencies.jar ../../
       cd -

1. Run the sample java client:

        export TOKEN_BROKER_DNS=<Token Broker FQDN>
        java -Djavax.net.ssl.keyStoreType=pkcs12 -Djavax.net.ssl.keyStore=client.p12 -Djavax.net.ssl.keyStorePassword=123456 -Djavax.net.ssl.trustStoreType=jks -Djavax.net.ssl.trustStore=client-truststore.jks -Djavax.net.ssl.trustStorePassword=123456 -Dtoken-broker.host=$TOKEN_BROKER_DNS $PATH_TO_REPO/client/Authtest/target/broker-client-1.0-SNAPSHOT-jar-with-dependencies.jar <bucket-name>

    You should see the output similar to this:

        Using client certificate at .../client.p12
        Using key store at .../client-truststore.jks
        Connecting to https://<Token Broker host>:443/token
        Loading data to GCS

