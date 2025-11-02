# Local Development Setup

Quick setup guide for running Namaskah SMS locally.

## 🚀 Quick Start

1. **Run the setup script:**
   ```bash
   python3 dev_setup.py
   ```

2. **Start the server:**
   ```bash
   python3 -m uvicorn main:app --reload --port 8000
   ```

3. **Open browser:**
   ```
   http://localhost:8000
   ```

4. **Login with demo credentials:**
   - Email: `admin@namaskah.app`
   - Password: `Namaskah@Admin2024`

## 🔧 Manual Setup (if needed)

If the quick setup doesn't work:

1. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

2. **Create demo user:**
   ```bash
   python3 setup_demo_user.py
   ```

3. **Test API endpoints:**
   ```bash
   python3 test_api.py
   ```

## 🐛 Troubleshooting

### "Loading services..." / "Loading countries..." Issue

This is a common localhost issue. Try:

1. **Hard refresh the browser** (Cmd+Shift+R / Ctrl+Shift+F5)
2. **Clear browser cache** for localhost:8000
3. **Check browser console** for JavaScript errors
4. **Verify API endpoints** with the test script

### Login Failed Issue

1. **Run the demo user setup:**
   ```bash
   python3 setup_demo_user.py
   ```

2. **Check database connection** in `.env` file
3. **Verify migrations** ran successfully

### Database Issues

1. **Check `.env` file** has correct DATABASE_URL
2. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

## 📝 Notes

- The app uses a production Supabase database even in development
- TextVerified API key is configured for real SMS services
- Dropdowns loading issue is typically a localhost caching problem
- Production deployment works fine - this is a dev environment issue

## 🔗 Production

The production version is working correctly. Local development issues don't affect production deployment.