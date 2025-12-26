#!/bin/bash
# Server Management Script for Namaskah

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to start server
start_server() {
    echo -e "${GREEN}🚀 Starting Namaskah server...${NC}"
    
    # Check if already running
    if [ -f .server.pid ]; then
        PID=$(cat .server.pid)
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Server already running (PID: $PID)${NC}"
            echo -e "${YELLOW}   Visit: http://localhost:8000${NC}"
            return 1
        else
            rm .server.pid
        fi
    fi
    
    # Start server in background
    nohup uvicorn main:app --host 127.0.0.1 --port 8000 --reload > logs/server.log 2>&1 &
    SERVER_PID=$!
    
    # Save PID
    echo $SERVER_PID > .server.pid
    
    echo -e "${GREEN}✅ Server started (PID: $SERVER_PID)${NC}"
    echo -e "${GREEN}   Visit: http://localhost:8000${NC}"
    echo -e "${GREEN}   Logs: tail -f logs/server.log${NC}"
}

# Function to stop server
stop_server() {
    echo -e "${YELLOW}🛑 Stopping Namaskah server...${NC}"
    
    if [ ! -f .server.pid ]; then
        echo -e "${RED}❌ No server PID file found${NC}"
        
        # Try to find and kill uvicorn processes
        PIDS=$(pgrep -f "uvicorn main:app")
        if [ -n "$PIDS" ]; then
            echo -e "${YELLOW}   Found running uvicorn processes: $PIDS${NC}"
            echo -e "${YELLOW}   Killing them...${NC}"
            kill $PIDS 2>/dev/null
            sleep 2
            kill -9 $PIDS 2>/dev/null
            echo -e "${GREEN}✅ Killed uvicorn processes${NC}"
        else
            echo -e "${YELLOW}   No running server found${NC}"
        fi
        return 0
    fi
    
    PID=$(cat .server.pid)
    
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        sleep 2
        
        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            kill -9 $PID
        fi
        
        rm .server.pid
        echo -e "${GREEN}✅ Server stopped (PID: $PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  Server not running (stale PID file)${NC}"
        rm .server.pid
    fi
}

# Function to restart server
restart_server() {
    echo -e "${YELLOW}🔄 Restarting Namaskah server...${NC}"
    stop_server
    sleep 1
    start_server
}

# Function to check server status
status_server() {
    if [ -f .server.pid ]; then
        PID=$(cat .server.pid)
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server is running (PID: $PID)${NC}"
            echo -e "${GREEN}   Visit: http://localhost:8000${NC}"
            echo -e "${GREEN}   Logs: tail -f logs/server.log${NC}"
            return 0
        else
            echo -e "${RED}❌ Server not running (stale PID file)${NC}"
            rm .server.pid
            return 1
        fi
    else
        echo -e "${RED}❌ Server not running${NC}"
        return 1
    fi
}

# Function to view logs
logs_server() {
    if [ -f logs/server.log ]; then
        tail -f logs/server.log
    else
        echo -e "${RED}❌ No log file found${NC}"
    fi
}

# Function to kill all uvicorn processes
kill_all() {
    echo -e "${RED}💀 Killing ALL uvicorn processes...${NC}"
    
    PIDS=$(pgrep -f "uvicorn")
    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}   Found processes: $PIDS${NC}"
        kill $PIDS 2>/dev/null
        sleep 2
        kill -9 $PIDS 2>/dev/null
        echo -e "${GREEN}✅ All uvicorn processes killed${NC}"
    else
        echo -e "${YELLOW}   No uvicorn processes found${NC}"
    fi
    
    # Clean up PID file
    [ -f .server.pid ] && rm .server.pid
}

# Main script
case "$1" in
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
        status_server
        ;;
    logs)
        logs_server
        ;;
    kill)
        kill_all
        ;;
    *)
        echo "Namaskah Server Management"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|kill}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the server"
        echo "  stop     - Stop the server gracefully"
        echo "  restart  - Restart the server"
        echo "  status   - Check server status"
        echo "  logs     - View server logs (live)"
        echo "  kill     - Force kill all uvicorn processes"
        echo ""
        exit 1
        ;;
esac

exit 0
