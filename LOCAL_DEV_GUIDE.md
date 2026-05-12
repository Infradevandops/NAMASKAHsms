# Local Development Quick Start

## 🚀 Start Local Server

```bash
./start_local.sh
```

This will:
- ✅ Use SQLite database (`./data/namaskah_local.db`)
- ✅ Skip PostgreSQL migrations
- ✅ Start on `http://localhost:8000`
- ✅ Enable hot reload

---

## 🔧 Environment Files

| File | Purpose |
|------|---------|
| `.env` | **Production** (Render.com) - PostgreSQL |
| `.env.development` | **Local** - SQLite |
| `.env.example` | Template |

---

## 📊 Database Info

**Local Development**:
- Type: SQLite
- Location: `./data/namaskah_local.db`
- Size: 856 KB
- No migrations needed

**Production**:
- Type: PostgreSQL
- Host: Render.com
- Requires VPN/tunnel for local access

---

## 🧪 Test OneSignal

1. **Start local server**:
   ```bash
   ./start_local.sh
   ```

2. **Visit**: `http://localhost:8000/push-settings`

3. **Enable notifications**: Click button, accept permission

4. **Send test**: Click "Send Test Notification"

---

## ⚠️ Common Issues

### Issue: "could not translate host name"
**Cause**: Using production DATABASE_URL locally
**Fix**: Use `./start_local.sh` instead of `./start.sh`

### Issue: Migration errors
**Cause**: Migrations are for PostgreSQL
**Fix**: SQLite doesn't need migrations (schema auto-created)

### Issue: Port already in use
**Fix**:
```bash
lsof -ti:8000 | xargs kill -9
./start_local.sh
```

---

## 📝 Scripts

| Script | Purpose |
|--------|---------|
| `./start_local.sh` | Local development (SQLite) |
| `./start.sh` | Production mode (PostgreSQL) |
| `./restart.sh` | Restart production |

---

## 🎯 Next Steps

1. ✅ OneSignal fix applied
2. ✅ Local startup script created
3. 🔄 Run `./start_local.sh`
4. 🧪 Test push notifications
5. 🚀 Deploy to production when ready

---

**Quick Start**: `./start_local.sh` → Visit `http://localhost:8000`
