#!/bin/bash
# VRENUM SMS - Log Audit & Debug Script
# Usage: ./logs_audit.sh [option]
# Options: live, errors, today, search, full

set -e

SERVER="root@169.255.57.57"
SERVICE="vrenum"

echo "🔍 VRENUM SMS - Log Audit Tool"
echo "================================"

case "${1:-live}" in
  live)
    echo "📡 Streaming live logs (Ctrl+C to stop)..."
    ssh $SERVER "journalctl -u $SERVICE -f --no-pager"
    ;;

  errors)
    echo "❌ Last 100 error logs..."
    ssh $SERVER "journalctl -u $SERVICE -p err -n 100 --no-pager"
    ;;

  today)
    echo "📅 Today's logs..."
    ssh $SERVER "journalctl -u $SERVICE --since today --no-pager"
    ;;

  search)
    if [ -z "$2" ]; then
      echo "Usage: ./logs_audit.sh search <keyword>"
      exit 1
    fi
    echo "🔎 Searching for: $2"
    ssh $SERVER "journalctl -u $SERVICE --no-pager | grep -i '$2'"
    ;;

  full)
    echo "📜 Full service logs (last 1000 lines)..."
    ssh $SERVER "journalctl -u $SERVICE -n 1000 --no-pager"
    ;;

  status)
    echo "📊 Service Status..."
    ssh $SERVER "systemctl status $SERVICE --no-pager"
    ;;

  app)
    echo "📝 Application log file (if exists)..."
    ssh $SERVER "tail -n 100 /root/NAMASKAHsms/app.log 2>/dev/null || echo 'No app.log file found'"
    ;;

  nginx)
    echo "🌐 Nginx access logs (last 50)..."
    ssh $SERVER "tail -n 50 /var/log/nginx/access.log 2>/dev/null || echo 'Nginx not configured yet'"
    echo ""
    echo "🌐 Nginx error logs (last 50)..."
    ssh $SERVER "tail -n 50 /var/log/nginx/error.log 2>/dev/null || echo 'Nginx not configured yet'"
    ;;

  disk)
    echo "💾 Disk usage and log sizes..."
    ssh $SERVER "df -h / && echo '' && du -sh /var/log/* 2>/dev/null | sort -h"
    ;;

  *)
    echo "Usage: ./logs_audit.sh [option]"
    echo ""
    echo "Options:"
    echo "  live      - Stream live logs (default)"
    echo "  errors    - Show last 100 errors"
    echo "  today     - Show today's logs"
    echo "  search    - Search logs: ./logs_audit.sh search <keyword>"
    echo "  full      - Show last 1000 log lines"
    echo "  status    - Show service status"
    echo "  app       - Show application log file"
    echo "  nginx     - Show Nginx logs"
    echo "  disk      - Show disk usage and log sizes"
    echo ""
    echo "Examples:"
    echo "  ./logs_audit.sh live"
    echo "  ./logs_audit.sh errors"
    echo "  ./logs_audit.sh search 'payment'"
    echo "  ./logs_audit.sh search '500'"
    ;;
esac
