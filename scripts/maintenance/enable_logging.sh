#!/bin/bash
# Enable Application Logging for VRENUM SMS

set -e

SERVER="root@169.255.57.57"
APP_DIR="/root/NAMASKAHsms"

echo "🔧 Enabling Application Logging..."
echo "=================================="

# Step 1: Update systemd service to capture stdout/stderr
echo "📝 Step 1: Updating systemd service..."
ssh $SERVER << 'EOF'
cat > /etc/systemd/system/vrenum.service << 'SERVICE'
[Unit]
Description=Vrenum SMS Verification API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/NAMASKAHsms
Environment="PATH=/root/NAMASKAHsms/.venv/bin:/usr/local/bin:/usr/bin:/bin"
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

systemctl daemon-reload
echo "✅ Systemd service updated"
EOF

# Step 2: Create logging configuration
echo ""
echo "📝 Step 2: Creating logging config..."
ssh $SERVER << 'EOF'
cd /root/NAMASKAHsms

# Create logs directory
mkdir -p logs

# Create logging config file
cat > app/core/logging_config.py << 'PYEOF'
import logging
import sys
from pathlib import Path

def setup_logging():
    """Configure application logging"""

    # Create logs directory
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Console handler (goes to journald)
            logging.StreamHandler(sys.stdout),
            # File handler (backup)
            logging.FileHandler(log_dir / "app.log")
        ]
    )

    # Set specific log levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return logging.getLogger(__name__)
PYEOF

echo "✅ Logging config created"
EOF

# Step 3: Restart service
echo ""
echo "🔄 Step 3: Restarting service..."
ssh $SERVER "systemctl restart vrenum"
sleep 3

# Step 4: Verify
echo ""
echo "✅ Step 4: Verifying logs..."
ssh $SERVER "journalctl -u vrenum -n 20 --no-pager"

echo ""
echo "=================================="
echo "✅ Logging enabled successfully!"
echo ""
echo "Test with:"
echo "  ./logs_audit.sh live"
echo ""
echo "Or make a request:"
echo "  curl https://vrenum.app/health"
echo "  ./logs_audit.sh live"
