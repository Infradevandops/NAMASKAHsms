# Monitoring Setup Guide

Simple monitoring for your SMS platform without expensive tools.


## Why Keep It Simple?

Datadog costs $15-30/month and is too complex for your current needs. Use free tools instead.


## What You Need

**Error Tracking**
- Sentry (free tier)
- Catches crashes and bugs
- Sends email alerts

**Uptime Monitoring** 
- UptimeRobot (free)
- Checks if your site is down
- Sends SMS alerts

**Logs**
- Render built-in logs (free)
- See what happened when


## Setup Steps

### 1. Add Error Tracking

Go to sentry.io and create free account
Copy your project key
Add to Render environment variables:
```
SENTRY_DSN=your-key-here
```

### 2. Add Uptime Monitoring

Go to uptimerobot.com and create free account
Add these 3 monitors:
- https://namaskah.onrender.com (main site)
- https://namaskah.onrender.com/health (API health)
- https://namaskah.onrender.com/api/auth/me (login check)

Set alert method to email or SMS.

### 3. Check Logs

In Render dashboard, click your service then "Logs"
Set up email alerts for errors


## What This Gives You

**When something breaks:**
- Sentry emails you the error details
- UptimeRobot texts you if site goes down
- Render logs show what happened

**Cost:** $0 per month
**Setup time:** 15 minutes


## When to Upgrade

Only upgrade when you have:
- 1000+ daily users
- Multiple team members
- Complex infrastructure

Then consider Sentry Pro ($26/month) or other paid tools.


## Quick Checklist

- [ ] Create Sentry account
- [ ] Add SENTRY_DSN to Render
- [ ] Create UptimeRobot account  
- [ ] Add 3 monitors to UptimeRobot
- [ ] Set up Render log alerts
- [ ] Test by triggering an error

Done! Your monitoring is set up.