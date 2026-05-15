#!/bin/bash
# setup.sh — Run ONCE on a fresh Ubuntu 22.04 droplet as root
# Usage: bash setup.sh
set -e

echo "=== Namaskah Droplet Setup ==="

# 1. Update system
apt update && apt upgrade -y

# 2. Create app user
adduser --disabled-password --gecos "" namaskah
usermod -aG sudo namaskah
rsync --archive --chown=namaskah:namaskah ~/.ssh /home/namaskah

# 3. Firewall
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw --force enable

# 4. Install Python 3.11
apt install -y software-properties-common
add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install -y python3.11 python3.11-venv python3.11-dev

# 5. Install system packages
apt install -y nginx git curl build-essential libpq-dev supervisor

# 6. Install pip
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# 7. Create log directory
mkdir -p /var/log/namaskah
chown namaskah:namaskah /var/log/namaskah

# 8. Clone repo
su - namaskah -c "git clone https://github.com/Infradevandops/NAMASKAHsms.git /home/namaskah/app"

# 9. Setup venv
su - namaskah -c "python3.11 -m venv /home/namaskah/app/.venv && /home/namaskah/app/.venv/bin/pip install --upgrade pip && /home/namaskah/app/.venv/bin/pip install -r /home/namaskah/app/requirements.txt"

# 10. Copy configs
cp /home/namaskah/app/deploy/digitalocean/supervisor.conf /etc/supervisor/conf.d/namaskah.conf
cp /home/namaskah/app/deploy/digitalocean/nginx.conf /etc/nginx/sites-available/namaskah
ln -sf /etc/nginx/sites-available/namaskah /etc/nginx/sites-enabled/namaskah
rm -f /etc/nginx/sites-enabled/default

# 11. Copy deploy script
cp /home/namaskah/app/deploy/digitalocean/deploy.sh /home/namaskah/deploy.sh
chmod +x /home/namaskah/deploy.sh
chown namaskah:namaskah /home/namaskah/deploy.sh

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "1. Create /home/namaskah/app/.env with your production env vars"
echo "2. Run: su - namaskah -c 'cd /home/namaskah/app && source .venv/bin/activate && alembic upgrade head'"
echo "3. Run: supervisorctl reread && supervisorctl update && supervisorctl start namaskah"
echo "4. Run: nginx -t && systemctl reload nginx"
echo "5. Verify: curl http://127.0.0.1:8000/health"
