# Fix Database Schema Issue

## Problem

Supabase has two `users` tables:

- `auth.users` (Supabase Auth system)
- `public.users` (Your app's table)

SQLAlchemy is querying the wrong one.

## Solution

**In Render Environment Variables, update DATABASE_URL:**

Add this to the end of your DATABASE_URL:

```
?options=-c%20search_path%3Dpublic
```

Example:

```
postgresql://user:pass@host:port/db?options=-c%20search_path%3Dpublic
```

This tells PostgreSQL to use the `public` schema by default.

## After Update

1. Redeploy in Render
2. Login should work with:
   - Email: admin@namaskah.app
   - Password: NamaskahAdmin2024!
