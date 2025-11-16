# 📱 Namaskah SMS Verification Platform

**5SIM Integration for SMS Verification**

---

## 🚀 Quick Start

```bash
# Start server
./start.sh

# Or manually
uvicorn main:app --host 127.0.0.1 --port 8000
```

**Open:** `http://localhost:8000/verify`

---

## 📊 Verification Flow

**Correct 5SIM Flow:**
1. Select Country
2. Select Service (loaded for that country)
3. Purchase
4. Receive SMS Code

---

## 🔧 Configuration

**Required:** `.env` file with:
```
FIVESIM_API_KEY=your_api_key_here
```

---

## 📖 Documentation

See `VERIFICATION_GUIDE.md` for implementation details.

---

## 🎯 Main Endpoints

- `/verify` - Verification dashboard
- `/api/verify/create` - Purchase verification
- `/api/verify/status/{id}` - Check SMS status
- `/api/countries/` - Get all countries
- `/api/countries/{country}/services` - Get services

---

**Built with FastAPI + 5SIM API**
