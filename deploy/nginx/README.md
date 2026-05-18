# Configuration Files

This directory contains server configuration files.

## Nginx Configurations

- `nginx.conf` - Base nginx configuration
- `nginx-production.conf` - Production environment
- `nginx-ssl.conf` - SSL/TLS configuration
- `nginx-lb.conf` - Load balancer configuration
- `nginx-multi-region.conf` - Multi-region setup

## Usage

```bash
# Copy to nginx sites-available
sudo cp config/nginx-production.conf /etc/nginx/sites-available/namaskah

# Enable site
sudo ln -s /etc/nginx/sites-available/namaskah /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```
