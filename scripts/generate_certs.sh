#!/bin/bash
# Generate self-signed certificates for development/testing

# Create certs directory if it doesn't exist
mkdir -p ../nginx/certs

# Generate a private key
openssl genrsa -out ../nginx/certs/server.key 2048

# Generate a certificate signing request
openssl req -new -key ../nginx/certs/server.key -out ../nginx/certs/server.csr -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Generate a self-signed certificate (valid for 365 days)
openssl x509 -req -days 365 -in ../nginx/certs/server.csr -signkey ../nginx/certs/server.key -out ../nginx/certs/server.crt

# Verify the certificate
openssl x509 -in ../nginx/certs/server.crt -text -noout

echo "Self-signed certificates generated successfully."
echo "Certificate location: ../nginx/certs/server.crt"
echo "Private key location: ../nginx/certs/server.key"
