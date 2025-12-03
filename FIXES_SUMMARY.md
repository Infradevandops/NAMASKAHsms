source "/Users/machine/Desktop/Namaskah. app/venv/bin/activate"

The default interactive shell is now zsh.
To update your account to use zsh, please run `chsh -s /bin/zsh`.
For more details, please visit https://support.apple.com/kb/HT208050.
Machines-MacBook-Pro:Namaskah. app machine$ source "/Users/machine/Desktop/Namaskah. app/venv/bin/activate"
(venv) Machines-MacBook-Pro:Namaskah. app machine$ python3 scripts/validate_production.py  # Verify
./start_production.sh                    # Start
curl https://namaskah.onrender.com/api/system/health  # Test

==================================================
PRODUCTION VALIDATION
==================================================

🔍 Checking environment configuration...
❌ Missing environment variables: SECRET_KEY, JWT_SECRET_KEY, DATABASE_URL, TEXTVERIFIED_API_KEY, PAYSTACK_SECRET_KEY, BASE_URL

🔍 Checking static files...
✅ Static files present

🔍 Checking templates...
✅ Templates present

🔍 Checking imports...
❌ Import error: No module named 'app'

🔍 Checking database...
❌ Database error: No module named 'app'

==================================================
RESULTS: 2/5 checks passed
==================================================

❌ Some checks failed. Please fix issues before deploying.
(venv) Machines-MacBook-Pro:Namaskah. app machine$ ./start_production.sh                    # Start
🚀 Starting Namaskah SMS Production Server
==========================================
✅ Environment variables loaded

Running production validation...

==================================================
PRODUCTION VALIDATION
==================================================

🔍 Checking environment configuration...
✅ Environment variables configured

🔍 Checking static files...
✅ Static files present

🔍 Checking templates...
✅ Templates present

🔍 Checking imports...
❌ Import error: No module named 'app'

🔍 Checking database...
❌ Database error: No module named 'app'

==================================================
RESULTS: 3/5 checks passed
==================================================

❌ Some checks failed. Please fix issues before deploying.
(venv) Machines-MacBook-Pro:Namaskah. app machine$ curl https://namaskah.onrender.com/api/system/health  # Test
{"status":"healthy","timestamp":"2025-12-03T21:42:03.285106","version":"2.5.0","database":"connected","authentication":"active"}(venv) Machines-MacBook-Pro:Namaskah. app machine$ 