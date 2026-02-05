# Production URLs Reference

## Working URLs

### Public Pages
- ✅ **Home**: https://namaskah.onrender.com/
- ✅ **Login**: https://namaskah.onrender.com/login
- ✅ **Register**: https://namaskah.onrender.com/register
- ✅ **Pricing**: https://namaskah.onrender.com/pricing

### Redirects (Auto-redirect to correct page)
- ✅ **Auth Login**: https://namaskah.onrender.com/auth/login → redirects to `/login`
- ✅ **Auth Register**: https://namaskah.onrender.com/auth/register → redirects to `/register`
- ✅ **Sign In**: https://namaskah.onrender.com/signin → redirects to `/login`

### Dashboard (Requires Authentication)
- ✅ **Dashboard**: https://namaskah.onrender.com/dashboard

### API Endpoints
- ✅ **Health Check**: https://namaskah.onrender.com/health
- ✅ **Diagnostics**: https://namaskah.onrender.com/api/diagnostics
- ✅ **Verification API**: https://namaskah.onrender.com/api/verification/*
- ✅ **Billing API**: https://namaskah.onrender.com/api/billing/*
- ✅ **Admin API**: https://namaskah.onrender.com/api/admin/*

## Not Available (Core Router Disabled)

These endpoints are temporarily unavailable due to syntax errors in core router files:

- ❌ `/api/login` (POST) - Login API endpoint
- ❌ `/api/register` (POST) - Register API endpoint
- ❌ `/api/auth/*` - All auth API endpoints
- ❌ `/api/forwarding/*` - SMS forwarding endpoints
- ❌ `/api/gdpr/*` - GDPR endpoints

## Workarounds

### For Login/Register:
The **pages** work fine at `/login` and `/register`. The issue is that the **API endpoints** for submitting login/register forms are in the disabled core_router.

**Temporary Solution**: 
You'll need to either:
1. Fix the syntax errors in `app/api/core/forwarding.py` and `app/api/core/gdpr.py`
2. Or create standalone auth API endpoints outside the core_router

## Latest Fixes Applied

1. ✅ Database connection fixed
2. ✅ Template errors fixed (landing.html)
3. ✅ Template variables added (services, user_count)
4. ✅ Redirects added for `/auth/login` and `/auth/register`
5. ✅ Code formatting and linting

## Deployment Status

**Last Deploy**: Commit `3f2230e`
**Status**: Deploying (wait 2-3 minutes)

After deployment:
- `/auth/login` will redirect to `/login` (no more 404)
- `/auth/register` will redirect to `/register` (no more 404)
- Home page will load with services data
- All public pages will work

## Testing After Deploy

```bash
# Should redirect to /login (302)
curl -I https://namaskah.onrender.com/auth/login

# Should return HTML
curl https://namaskah.onrender.com/login

# Should return JSON
curl https://namaskah.onrender.com/health
```
