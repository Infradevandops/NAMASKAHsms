# TextVerified Fix - Manual Steps

## Problem
TextVerified library is installed but the service can't initialize because environment variables aren't being loaded properly.

## Root Cause
The app loads `.env` file but TextVerifiedService reads directly from `os.getenv()` which might not have the variables loaded yet.

## Solution: Add TEXTVERIFIED_USERNAME

The code looks for `TEXTVERIFIED_USERNAME` OR `TEXTVERIFIED_EMAIL`. You have `TEXTVERIFIED_EMAIL` but add both to be safe.

---

## Manual Fix Steps

### Step 1: SSH into VPS
```bash
ssh root@<your-vps-ip>
```

### Step 2: Edit .env file
```bash
cd /root/NAMASKAHsms
nano .env
```

### Step 3: Add this line (if not already there)
```env
TEXTVERIFIED_USERNAME=<your-textverified-email>
```

Your .env should have BOTH:
```env
TEXTVERIFIED_API_KEY=<your-textverified-api-key>
TEXTVERIFIED_EMAIL=<your-textverified-email>
TEXTVERIFIED_USERNAME=<your-textverified-email>
```

### Step 4: Save and exit
- Press `Ctrl+O` to save
- Press `Enter` to confirm
- Press `Ctrl+X` to exit

### Step 5: Restart service
```bash
systemctl restart vrenum
```

### Step 6: Check logs
```bash
journalctl -u vrenum -n 30 -f
```

You should see:
```
TextVerified client initialized successfully
```

---

## Alternative: One-Line Fix

```bash
ssh root@<your-vps-ip> "cd /root/NAMASKAHsms && echo 'TEXTVERIFIED_USERNAME=<your-textverified-email>' >> .env && systemctl restart vrenum && sleep 3 && journalctl -u vrenum -n 20"
```

---

## Verify It Works

After restart, test the API:
```bash
curl https://vrenum.app/api/countries
```

Should return list of countries without errors.

---

## Why This Happens

The TextVerifiedService code:
```python
self.api_username = os.getenv("TEXTVERIFIED_USERNAME") or os.getenv("TEXTVERIFIED_EMAIL")
```

It checks `TEXTVERIFIED_USERNAME` first, then falls back to `TEXTVERIFIED_EMAIL`.
Adding `TEXTVERIFIED_USERNAME` ensures it's always found.
