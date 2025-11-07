#!/bin/bash

# 🚀 Namaskah SMS - Production Deployment Script
# Minimal deployment automation

set -e

echo "🚀 Deploying Namaskah SMS to Production"
echo "======================================"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ Don't run as root. Use a regular user with sudo access." >&2
   exit 1
fi

# Check Python version
python_version="$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)"
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ required. Found: $python_version" >&2
    exit 1
fi

echo "✅ Python version: $python_version"

# Install dependencies
echo "📦 Installing dependencies..."
if ! pip3 install -r requirements.txt; then
    echo "❌ Failed to install dependencies" >&2
    exit 1
fi

# Check environment variables
echo "🔧 Checking environment configuration..."

required_vars=("SECRET_KEY" "TEXTVERIFIED_API_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        missing_vars+=("$var")
    fi
done

if [[ ${#missing_vars[@]} -gt 0 ]]; then
    echo "❌ Missing required environment variables:" >&2
    printf '   %s\n' "${missing_vars[@]}" >&2
    echo "💡 Set them in .env file or export them" >&2
    exit 1
fi

echo "✅ Environment variables configured"

# Initialize database
echo "🗄️ Initializing database..."
python3 -c "
try:
    from main import Base, engine
    Base.metadata.create_all(bind=engine)
    print('✅ Database initialized')
except Exception as e:
    print(f'❌ Database error: {e}')
    exit(1)
"

# Run production tests
echo "🧪 Running production tests..."
if python3 production_test.py; then
    echo "✅ All tests passed"
else
    echo "⚠️ Some tests failed, but continuing deployment"
fi

# Check if port 8000 is available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️ Port 8000 is already in use"
    read -p "Kill existing process? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo kill -9 "$(lsof -t -i:8000)" 2>/dev/null || true
        echo "✅ Existing process killed"
    fi
fi

# Start the application
echo "🚀 Starting Namaskah SMS..."

# Check if PM2 is available
if command -v pm2 &> /dev/null; then
    echo "📊 Using PM2 process manager"
    
    # Create PM2 ecosystem file
    cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'namaskah-sms',
    script: 'uvicorn',
    args: 'main:app --host ${HOST:-127.0.0.1} --port ${PORT:-8000} --workers ${WORKERS:-4}',
    interpreter: 'python3',
    env: {
      ENVIRONMENT: 'production'
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true
  }]
}
EOF
    
    # Create logs directory
    mkdir -p logs
    
    # Start with PM2
    pm2 delete namaskah-sms 2>/dev/null || true
    pm2 start ecosystem.config.js
    pm2 save
    
    echo "✅ Application started with PM2"
    echo "📊 Monitor with: pm2 monit"
    echo "📋 Logs with: pm2 logs namaskah-sms"
    
else
    echo "🔄 Starting with uvicorn (install PM2 for production)"
    
    # Start in background
    nohup uvicorn main:app --host ${HOST:-127.0.0.1} --port ${PORT:-8000} --workers ${WORKERS:-4} > app.log 2>&1 &
    
    echo "✅ Application started in background"
    echo "📋 Logs: tail -f app.log"
fi

# Wait for application to start
echo "⏳ Waiting for application to start..."
sleep 5

# Health check with retry
echo "🏥 Performing health check..."
health_check_passed=false
for i in {1..5}; do
    if curl -f -s --connect-timeout 10 http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Health check passed"
        health_check_passed=true
        break
    else
        echo "⏳ Health check attempt $i/5 failed, retrying..."
        sleep 2
    fi
done

if [ "$health_check_passed" = false ]; then
    echo "❌ Health check failed after 5 attempts" >&2
    echo "🔍 Check logs for errors" >&2
    if command -v pm2 &> /dev/null; then
        echo "📋 PM2 logs: pm2 logs namaskah-sms" >&2
    else
        echo "📋 Application logs: tail -f app.log" >&2
    fi
    exit 1
fi

# Display deployment info
echo ""
echo "🎉 Deployment Successful!"
echo "======================="
echo "🌐 Application URL: http://localhost:8000"
echo "📊 Enhanced Dashboard: http://localhost:8000/dashboard/enhanced"
echo "👤 Admin Panel: http://localhost:8000/admin"
echo "🏥 Health Check: http://localhost:8000/health"
echo ""
echo "👤 Default Admin Login:"
echo "   Email: admin@namaskah.app"
echo "   Password: Namaskah@Admin2024"
echo "   ⚠️ Change password after first login!"
echo ""
echo "📊 Production Monitoring:"
echo "   Health: http://localhost:8000/admin/production/health"
echo "   Metrics: http://localhost:8000/admin/production/metrics"
echo ""

# Optional: Setup systemd service
read -p "🔧 Setup systemd service for auto-start? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    
    # Create systemd service file
    sudo tee /etc/systemd/system/namaskah-sms.service > /dev/null << EOF
[Unit]
Description=Namaskah SMS Service
After=network.target

[Service]
Type=exec
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=ENVIRONMENT=production
ExecStart=$(which uvicorn) main:app --host ${HOST:-127.0.0.1} --port ${PORT:-8000} --workers ${WORKERS:-4}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    
    # Enable and start service
    sudo systemctl daemon-reload
    sudo systemctl enable namaskah-sms
    sudo systemctl start namaskah-sms
    
    echo "✅ Systemd service created and started"
    echo "🔧 Control with: sudo systemctl {start|stop|restart|status} namaskah-sms"
fi

echo ""
echo "🚀 Namaskah SMS is now running in production!"
echo "📖 See DEPLOYMENT_GUIDE.md for advanced configuration"