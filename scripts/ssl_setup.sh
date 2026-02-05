#!/bin/bash

set -e

echo "🔐 Setting up SSL/TLS certificates..."

CERT_DIR="certs"
mkdir -p "$CERT_DIR"

# Generate self-signed certificate for development
if [ ! -f "$CERT_DIR/server.crt" ]; then
    echo "Generating self-signed certificate..."
    openssl req -x509 -newkey rsa:4096 -nodes -out "$CERT_DIR/server.crt" -keyout "$CERT_DIR/server.key" -days 365 \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    echo "✅ Certificate generated: $CERT_DIR/server.crt"
    echo "✅ Private key generated: $CERT_DIR/server.key"
else
    echo "✅ Certificates already exist"
fi

# Set proper permissions
chmod 600 "$CERT_DIR/server.key"
chmod 644 "$CERT_DIR/server.crt"

echo ""
echo "📋 Certificate Details:"
openssl x509 -in "$CERT_DIR/server.crt" -text -noout | grep -E "Subject:|Issuer:|Not Before|Not After"

echo ""
echo "✅ SSL/TLS setup complete!"
echo "Use with: uvicorn main:app --ssl-keyfile=$CERT_DIR/server.key --ssl-certfile=$CERT_DIR/server.crt"
