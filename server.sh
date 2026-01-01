#!/bin/bash

# Namaskah Server Management Script
# Usage: ./server.sh [start|stop|restart|status|logs|kill]

set -e

# Configuration
HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8000}
PID_FILE=".server.pid"
LOG_FILE="logs/server.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

# Function to check if server is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            # PID file exists but process is dead, clean up
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to get server PID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    fi
}

# Function to start the server
start_server() {
    if is_running; then
        local pid=$(get_pid)
        print_warning "Server already running (PID: $pid)"
        print_info "Visit: http://$HOST:$PORT"
        return 0
    fi

    print_info "Starting Namaskah server..."

    # Check if .env exists
    if [ ! -f .env ]; then
        print_error "No .env file found. Creating from example..."
        cp .env.example .env
        print_error "Please edit .env with your credentials"
        exit 1
    fi

    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv .venv
    fi

    # Activate virtual environment
    source .venv/bin/activate

    # Install dependencies
    print_info "Installing dependencies..."
    if ! pip install -q -r requirements.txt; then
        print_error "Failed to install dependencies"
        exit 1
    fi

    # Run database migrations
    print_info "Running database migrations..."
    alembic upgrade head 2>/dev/null || print_warning "Migrations skipped (may already be applied)"

    # Find available port
    while lsof -i:$PORT >/dev/null 2>&1; do
        PORT=$((PORT + 1))
        if [ $PORT -gt 8010 ]; then
            print_error "No available ports found between 8000-8010"
            exit 1
        fi
    done

    # Start server in background
    print_info "Starting server on http://$HOST:$PORT"
    nohup uvicorn main:app --host "$HOST" --port "$PORT" --reload > "$LOG_FILE" 2>&1 &
    local pid=$!
    
    # Save PID
    echo $pid > "$PID_FILE"
    
    # Wait a moment to check if server started successfully
    sleep 2
    if is_running; then
        print_status "Server started successfully (PID: $pid)"
        print_info "📱 Landing: http://$HOST:$PORT"
        print_info "📋 Dashboard: http://$HOST:$PORT/dashboard"
        print_info "✉️ Verify: http://$HOST:$PORT/verify"
        print_info "📊 Logs: tail -f $LOG_FILE"
    else
        print_error "Failed to start server"
        print_info "Check logs: cat $LOG_FILE"
        exit 1
    fi
}

# Function to stop the server
stop_server() {
    if ! is_running; then
        print_error "Server not running"
        return 0
    fi

    local pid=$(get_pid)
    print_info "Stopping server (PID: $pid)..."
    
    # Try graceful shutdown first
    if kill "$pid" 2>/dev/null; then
        # Wait up to 10 seconds for graceful shutdown
        local count=0
        while [ $count -lt 10 ] && is_running; do
            sleep 1
            count=$((count + 1))
        done
        
        if is_running; then
            print_warning "Graceful shutdown failed, forcing kill..."
            kill -9 "$pid" 2>/dev/null || true
        fi
    fi
    
    # Clean up PID file
    rm -f "$PID_FILE"
    
    # Double check and clean up any remaining processes
    pkill -f "uvicorn main:app" 2>/dev/null || true
    
    print_status "Server stopped"
}

# Function to restart the server
restart_server() {
    print_info "Restarting server..."
    stop_server
    sleep 1
    start_server
}

# Function to show server status
show_status() {
    if is_running; then
        local pid=$(get_pid)
        print_status "Server is running (PID: $pid)"
        print_info "Visit: http://$HOST:$PORT"
        print_info "Logs: tail -f $LOG_FILE"
    else
        print_error "Server not running"
    fi
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        print_info "Showing live logs (Press Ctrl+C to exit)..."
        tail -f "$LOG_FILE"
    else
        print_error "No log file found at $LOG_FILE"
    fi
}

# Function to kill all server processes (emergency)
kill_all() {
    print_warning "Emergency kill - stopping all uvicorn processes..."
    
    # Kill by PID file first
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        kill -9 "$pid" 2>/dev/null || true
        rm -f "$PID_FILE"
    fi
    
    # Kill all uvicorn processes
    pkill -9 -f "uvicorn main:app" 2>/dev/null || true
    
    # Kill processes on port 8000-8010
    for port in {8000..8010}; do
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    done
    
    print_status "All server processes killed"
}

# Function to show usage
show_usage() {
    echo "Namaskah Server Management"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start    - Start the server"
    echo "  stop     - Stop the server gracefully"
    echo "  restart  - Restart the server"
    echo "  status   - Show server status"
    echo "  logs     - Show live server logs"
    echo "  kill     - Force kill all server processes (emergency)"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 logs"
}

# Main script logic
case "${1:-}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    kill)
        kill_all
        ;;
    *)
        show_usage
        exit 1
        ;;
esac