#!/bin/bash
# setup.sh — Run ONCE on a fresh Ubuntu 22.04 droplet as root
# Usage: bash setup.sh
set -e

echo "=== Vrenum Droplet Setup ==="

# 1. Update system
apt update && apt upgrade -y

# 2. Create app user
adduser --disabled-password --gecos "" vrenum
usermod -aG sudo vrenum
rsync --archive --chown=vrenum:vrenum ~/.ssh /home/vrenum

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
mkdir -p /var/log/vrenum
chown vrenum:vrenum /var/log/vrenum

# 8. Clone repo
su - vrenum -c "git clone https://github.com/Infradevandops/NAMASKAHsms.git /home/vrenum/app"

# 9. Setup venv
su - vrenum -c "python3.11 -m venv /home/vrenum/app/.venv && /home/vrenum/app/.venv/bin/pip install --upgrade pip && /home/vrenum/app/.venv/bin/pip install -r /home/vrenum/app/requirements.txt"

# 10. Copy configs
cp /home/vrenum/app/deploy/digitalocean/supervisor.conf /etc/supervisor/conf.d/vrenum.conf
cp /home/vrenum/app/deploy/digitalocean/nginx.conf /etc/nginx/sites-available/vrenum
ln -sf /etc/nginx/sites-available/vrenum /etc/nginx/sites-enabled/vrenum
rm -f /etc/nginx/sites-enabled/default

# 11. Copy deploy script
cp /home/vrenum/app/deploy/digitalocean/deploy.sh /home/vrenum/deploy.sh
chmod +x /home/vrenum/deploy.sh
chown vrenum:vrenum /home/vrenum/deploy.sh

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "1. Create /home/vrenum/app/.env with your production env vars"
echo "2. Run: su - vrenum -c 'cd /home/vrenum/app && source .venv/bin/activate && alembic upgrade head'"
echo "3. Run: supervisorctl reread && supervisorctl update && supervisorctl start vrenum"
echo "4. Run: nginx -t && systemctl reload nginx"
echo "5. Verify: curl http://127.0.0.1:8000/health"
