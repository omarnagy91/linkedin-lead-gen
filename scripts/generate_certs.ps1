# PowerShell script to generate self-signed certificates for development/testing

# Create certs directory if it doesn't exist
$certsPath = "..\nginx\certs"
if (-not (Test-Path $certsPath)) {
    New-Item -ItemType Directory -Force -Path $certsPath
}

# Check if OpenSSL is available
try {
    openssl version
    Write-Host "OpenSSL is installed."
} catch {
    Write-Host "OpenSSL is not installed or not in your PATH. Please install OpenSSL and try again."
    exit 1
}

# Generate a private key
openssl genrsa -out "$certsPath\server.key" 2048

# Generate a certificate signing request
openssl req -new -key "$certsPath\server.key" -out "$certsPath\server.csr" -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Generate a self-signed certificate (valid for 365 days)
openssl x509 -req -days 365 -in "$certsPath\server.csr" -signkey "$certsPath\server.key" -out "$certsPath\server.crt"

# Verify the certificate
openssl x509 -in "$certsPath\server.crt" -text -noout

Write-Host "Self-signed certificates generated successfully."
Write-Host "Certificate location: $certsPath\server.crt"
Write-Host "Private key location: $certsPath\server.key"
