#!/bin/bash
# VRENUM SMS - SSL Setup Script (Let's Encrypt)
# Usage: ./scripts/setup-ssl.sh yourdomain.com

set -e

DOMAIN=${1:-vrenum.app}
EMAIL=${2:-admin@$DOMAIN}

echo "🔐 Setting up SSL for $DOMAIN..."

# Check if running from project root
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Run this script from the project root directory"
    exit 1
fi

# Create temporary nginx config for initial cert
cat > deploy/nginx/nginx-initial.conf << 'EOF'
events { worker_connections 1024; }
http {
    server {
        listen 80;
        server_name _;
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        location / {
            return 200 'SSL setup in progress';
            add_header Content-Type text/plain;
        }
    }
}
EOF

# Start nginx with initial config
echo "📦 Starting nginx for certificate challenge..."
docker compose down nginx 2>/dev/null || true
docker run -d --name nginx-certbot \
    -p 80:80 \
    -v $(pwd)/deploy/nginx/nginx-initial.conf:/etc/nginx/nginx.conf:ro \
    -v $(pwd)/certs:/etc/letsencrypt \
    -v certbot_webroot:/var/www/certbot \
    nginx:alpine

sleep 3

# Get certificate
echo "📜 Requesting certificate from Let's Encrypt..."
docker run --rm \
    -v $(pwd)/certs:/etc/letsencrypt \
    -v certbot_webroot:/var/www/certbot \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

# Stop temporary nginx
docker stop nginx-certbot && docker rm nginx-certbot

# Clean up
rm deploy/nginx/nginx-initial.conf

echo "✅ SSL certificate obtained!"
echo ""
echo "Now start the full stack:"
echo "  docker compose up -d"
echo ""
echo "Certificate will auto-renew via certbot container."
