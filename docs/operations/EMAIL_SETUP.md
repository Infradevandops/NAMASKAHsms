# Email Setup Guide

> **Last Updated**: November 2026
> Covers: how email sending works, what to configure, and what to change as you grow.

---

## Current Status — Already Configured ✅

Resend is live in production:
- `RESEND_API_KEY` — set in `.env.production`
- `FROM_EMAIL_ADDRESS` — `support@vrenum.app`
- `SUPPORT_EMAIL` — `support@vrenum.app`
- `ADMIN_NOTIFY_EMAIL` — `admin@vrenum.app`

Emails are sending. The app logs `Email service initialised — Resend` on startup.

To verify on the server:
```bash
ssh root@<your-vps-ip> "cd ~/vrenum && docker compose logs app | grep -i 'email service'"
```

### Email Hardening (November 2026)

The email system was hardened in `978b6b87`. Key changes that affect operations:

- **Outbox worker**: A supervised background worker now processes the `email_outbox` table. Run `alembic upgrade head` on the server to create the `email_outbox` and `contact_submissions` tables before deploying.
- **Preference policy**: `GET /api/notifications/email` now returns real `email_notifications_enabled` derived from the user's actual preferences (was hardcoded `True`).
- **Contact form durability**: Contact submissions are persisted to DB before the API responds. Forwarding failure no longer loses the submission — it sets `forwarding_status=failed` and the outbox worker retries.
- **Template autoescape**: Jinja HTML templates now use `autoescape=True`. URL variables are validated against trusted HTTPS hosts.
- **Security email footers**: Password reset and verification emails no longer include an unsubscribe footer (security mail must not imply it can be opted out of).

---

## How Email Sending Works

The app tries Resend first. If `RESEND_API_KEY` is not set, it falls back to SMTP. If neither is configured, emails are silently skipped and a warning is logged.

```
RESEND_API_KEY set?
  ├── Yes → send via Resend API (recommended)
  └── No  → SMTP_HOST + SMTP_USERNAME + SMTP_PASSWORD set?
              ├── Yes → send via SMTP
              └── No  → log warning, skip send
```

The sending address that appears in users' inboxes is controlled by `FROM_EMAIL_ADDRESS` in `.env.production`.

---

## The Three Email Addresses to Configure

| Variable | Purpose | Example |
|----------|---------|---------|
| `FROM_EMAIL_ADDRESS` | The `From:` header users see in every email | `hello@vrenum.app` |
| `SUPPORT_EMAIL` | Shown in email footers and error pages | `support@vrenum.app` |
| `ADMIN_NOTIFY_EMAIL` | Where system alerts go (revenue-zero, DB issues) | `alerts@vrenum.app` or your personal email |

`ADMIN_NOTIFY_EMAIL` falls back to `ADMIN_EMAIL` if not set, so you don't need to add it immediately.

---

## Setup: Resend (Recommended — Do This Now)

Resend is the right choice at your current scale. Free tier covers 3,000 emails/month and 100/day. No SMTP config, no port issues, reliable delivery.

### Steps

**1. Create account**
Go to [resend.com](https://resend.com) → sign up with your email.

**2. Add your domain**
Resend → Domains → Add Domain → enter `vrenum.app`

You'll get three DNS records to add. In your DNS provider (Cloudflare):
- Add the three TXT/MX records Resend gives you
- Wait for Resend to show "Verified" (usually under 5 minutes with Cloudflare)

**3. Create an API key**
Resend → API Keys → Create API Key → name it `vrenum-production` → copy it

**4. Update `.env.production` on the server**
```bash
ssh root@<your-vps-ip>
nano ~/vrenum/.env.production
```

Add or update:
```env
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
FROM_EMAIL_ADDRESS=hello@vrenum.app
SUPPORT_EMAIL=support@vrenum.app
ADMIN_NOTIFY_EMAIL=your-personal@email.com
```

**5. Restart the app to pick up the new env**
```bash
cd ~/vrenum && docker compose up -d --force-recreate
```

**6. Verify it's working**
```bash
# Check email service initialised correctly
docker compose logs app | grep "Email service"
# Should show: Email service initialised — Resend (lazy-loaded)
```

Then trigger a test: register a new account on vrenum.app and confirm the welcome email arrives.

---

## DNS Records to Add in Cloudflare

When you add `vrenum.app` to Resend, it will give you records like these (exact values come from Resend):

| Type | Name | Value |
|------|------|-------|
| TXT | `resend._domainkey.vrenum.app` | `p=MIGfMA0GCSq...` (DKIM key) |
| TXT | `vrenum.app` | `v=spf1 include:amazonses.com ~all` (SPF) |
| TXT | `_dmarc.vrenum.app` | `v=DMARC1; p=none; rua=mailto:dmarc@vrenum.app` |

> In Cloudflare, set all three to **DNS only** (grey cloud, not proxied). Proxying DNS records breaks email authentication.

---

## What Each Email Address Should Be

**`hello@vrenum.app`** — the From address
This is what users see in their inbox. Use something friendly. `hello@` or `noreply@` both work. `noreply@` signals users not to reply; `hello@` is warmer. Your call.

**`support@vrenum.app`** — shown in footers
This should be a real inbox you check. Users who reply to emails or look at the footer will use this. Forward it to your personal email or use Zoho Mail free tier to create a real mailbox.

**`alerts@vrenum.app`** (or your personal email) — system alerts
This gets revenue-zero alerts, DB warnings, etc. Use your personal email here until you have a team.

---

## Creating Real Mailboxes for support@ and alerts@

You don't need a paid Google Workspace account. Two free options:

**Option A — Zoho Mail (free, up to 5 users)**
1. Go to [zoho.com/mail](https://www.zoho.com/mail/) → Free plan
2. Add `vrenum.app` as your domain
3. Create `support@vrenum.app` and `alerts@vrenum.app`
4. Add Zoho's MX records in Cloudflare

**Option B — Cloudflare Email Routing (free, forwards to any inbox)**
1. Cloudflare dashboard → your domain → Email → Email Routing
2. Create a rule: `support@vrenum.app` → forwards to `your-personal@gmail.com`
3. No mailbox to manage — replies come from your personal email

Option B is simpler to set up. Option A gives you a proper inbox with a vrenum.app address when you reply.

---

## Scaling Plan — What to Change as You Grow

### Now → 100 users (current)
- Resend free tier (3,000/month) is more than enough
- One `FROM_EMAIL_ADDRESS` for everything
- `SUPPORT_EMAIL` forwarded to your personal inbox
- No changes needed

### 100 → 1,000 users
- Stay on Resend — paid plan starts at $20/month for 50,000 emails
- Consider splitting From addresses by email type:
  - Transactional (receipts, verifications): `hello@vrenum.app`
  - Marketing (digests, announcements): `updates@vrenum.app`
- Splitting matters because if a marketing email gets marked as spam, it won't affect delivery of receipts
- Set up a real `support@vrenum.app` mailbox (Zoho or Google Workspace)

### 1,000 → 10,000 users
- Add email unsubscribe tracking (store unsubscribe tokens in DB, honour them)
- Add bounce handling — Resend webhooks can notify you of hard bounces; mark those users as `email_bounced=True` and stop sending
- Consider a dedicated IP address (Resend Pro) for better deliverability
- Set up DMARC reporting to catch spoofing attempts

### 10,000+ users
- Evaluate SendGrid or AWS SES for cost (SES is $0.10/1,000 emails vs Resend's higher per-email cost at scale)
- Implement email preference centre (daily digest vs weekly vs none)
- A/B test subject lines on welcome and low-balance emails
- Dedicated sending domain per email type (e.g. `mail.vrenum.app` for transactional)

---

## Current Email Behaviour: Admin Accounts

Admin accounts (`is_admin=True`) are **excluded from low balance alerts**. This is intentional — admin balance reflects the TextVerified account balance (synced live), not a wallet that needs topping up. Sending a low balance alert to an admin would be misleading.

All other email types (welcome, receipt, etc.) still send to admin accounts normally.

---

## Checking Email Logs

If an email fails to send, it logs a warning but never crashes the request. To see email activity:

```bash
# On server — filter for email-related log lines
ssh root@<your-vps-ip> "cd ~/vrenum && docker compose logs app | grep -i email"
```

What you'll see:
- `Email service initialised — Resend` → configured correctly
- `Email sent via Resend to user@example.com` → successful send
- `Email service not configured, skipping send` → env vars missing
- `Failed to send email to user@example.com: ...` → Resend API error (check API key, domain verification)

---

## Environment Variables Reference

```env
# .env.production

# Resend (primary — use this)
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# SMTP (fallback — only if Resend not configured)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@gmail.com
SMTP_PASSWORD=your-app-password   # Gmail: use App Password, not account password

# Addresses
FROM_EMAIL_ADDRESS=hello@vrenum.app      # From: header in all emails
SUPPORT_EMAIL=support@vrenum.app         # Shown in footers
ADMIN_NOTIFY_EMAIL=you@youremail.com     # System alerts destination
```

---

> **Resend is already live.** `support@vrenum.app` is the sending address. The next email task is wiring the low balance alert, tier upgrade email, and passing `user_name` to payment/refund callers — see TASK-009 through TASK-011 in `TASKS.md`.
