#!/bin/bash
# Fix systemd service to load .env file

echo "🔧 Updating systemd service to load .env file..."
echo ""

ssh root@169.255.57.57 << 'EOF'
# Update systemd service to include EnvironmentFile
cat > /etc/systemd/system/vrenum.service << 'SERVICE'
[Unit]
Description=Vrenum SMS Verification API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/NAMASKAHsms
Environment="PATH=/root/NAMASKAHsms/.venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/root/NAMASKAHsms/.env
ExecStart=/root/NAMASKAHsms/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info
Restart=always
RestartSec=10

# Capture logs to journald
StandardOutput=journal
StandardError=journal
SyslogIdentifier=vrenum

[Install]
WantedBy=multi-user.target
SERVICE

echo "✅ Systemd service updated with EnvironmentFile"

# Reload systemd
systemctl daemon-reload
echo "✅ Systemd daemon reloaded"

# Restart service
systemctl restart vrenum
echo "✅ Service restarted"

sleep 3

echo ""
echo "📊 Checking logs for TextVerified initialization..."
journalctl -u vrenum -n 30 --no-pager | grep -i textverified | tail -5
EOF

echo ""
echo "====================================="
echo "✅ Fix complete!"
echo ""
echo "Check logs with: ./logs_audit.sh live"
