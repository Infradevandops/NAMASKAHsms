# 🚀 SERVER MANAGEMENT GUIDE

## Quick Commands

```bash
# Start server
./server.sh start

# Stop server
./server.sh stop

# Restart server
./server.sh restart

# Check status
./server.sh status

# View logs (live)
./server.sh logs

# Force kill all (emergency)
./server.sh kill
```

---

## 📋 Common Tasks

### **Start Development Server**
```bash
cd /Users/machine/Desktop/Namaskah.\ app
./server.sh start

# Visit: http://localhost:8000
```

### **Stop Server Gracefully**
```bash
./server.sh stop
```

### **Restart After Code Changes**
```bash
./server.sh restart
```

### **Check if Server is Running**
```bash
./server.sh status
```

### **View Live Logs**
```bash
./server.sh logs
# Press Ctrl+C to exit
```

### **Emergency Kill (if server won't stop)**
```bash
./server.sh kill
```

---

## 🔧 Manual Commands (if script fails)

### **Find Running Processes**
```bash
ps aux | grep uvicorn
```

### **Kill by PID**
```bash
kill <PID>
# or force kill
kill -9 <PID>
```

### **Kill All Uvicorn**
```bash
pkill -f uvicorn
# or force
pkill -9 -f uvicorn
```

### **Check Port 8000**
```bash
lsof -i :8000
```

### **Kill Process on Port 8000**
```bash
lsof -ti:8000 | xargs kill -9
```

---

## 📊 Server Status Indicators

**✅ Running**:
```
✅ Server is running (PID: 12345)
   Visit: http://localhost:8000
   Logs: tail -f logs/server.log
```

**❌ Stopped**:
```
❌ Server not running
```

**⚠️ Already Running**:
```
⚠️  Server already running (PID: 12345)
   Visit: http://localhost:8000
```

---

## 🐛 Troubleshooting

### **Problem: "Address already in use"**
```bash
# Kill process on port 8000
./server.sh kill

# Or manually
lsof -ti:8000 | xargs kill -9

# Then start again
./server.sh start
```

### **Problem: Server won't stop**
```bash
# Force kill all
./server.sh kill
```

### **Problem: Can't find server.sh**
```bash
# Make sure you're in the right directory
cd /Users/machine/Desktop/Namaskah.\ app

# Make script executable
chmod +x server.sh
```

### **Problem: Permission denied**
```bash
chmod +x server.sh
```

---

## 📁 Files Created

- `server.sh` - Server management script
- `.server.pid` - Process ID file (auto-created)
- `logs/server.log` - Server logs (auto-created)

---

## 🎯 Best Practices

1. **Always use `./server.sh stop` before closing terminal**
2. **Check status before starting**: `./server.sh status`
3. **View logs if errors occur**: `./server.sh logs`
4. **Use `kill` only as last resort**

---

## 🚀 Quick Start Workflow

```bash
# 1. Navigate to project
cd /Users/machine/Desktop/Namaskah.\ app

# 2. Start server
./server.sh start

# 3. Open browser
open http://localhost:8000

# 4. Make changes to code
# (server auto-reloads with --reload flag)

# 5. Stop when done
./server.sh stop
```

---

## 📝 Notes

- Server runs on `http://127.0.0.1:8000`
- Auto-reload enabled (watches for file changes)
- Logs saved to `logs/server.log`
- PID saved to `.server.pid`

---

**Need help? Run**: `./server.sh` (shows usage)
