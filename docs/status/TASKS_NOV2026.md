# Tasks — November 2026

## CRITICAL: verification-flow.js not loading (chooseMethod undefined)

**Symptom**: Clicking SMS / Voice / SMS+Voice buttons does nothing. Console shows:
- `Uncaught SyntaxError: unexpected token: keyword 'this' verification-flow.js:143:7`
- `ReferenceError: chooseMethod is not defined`
- `typeof chooseMethod` → `"undefined"`

**Root cause**: Cloudflare is caching the old broken `verification-flow.js` (before the `/*` comment fix).
The VM file is correct. The Docker volume mount (`/root/vrenum/static:/app/static`) means static files
are served directly from the VM — Docker rebuilds do NOT affect static files.

**Fix**: Purge Cloudflare cache so the fixed file is served.
1. Cloudflare Dashboard → vrenum.app → Caching → Configuration → **Purge Everything**
2. Hard refresh browser (`Cmd+Shift+R`)
3. Confirm `typeof chooseMethod` returns `"function"` in console

**Status**: ⏳ Pending Cloudflare cache purge

---

## RESOLVED: Container down / Cloudflare 522

**Cause**: No reverse proxy on port 80 — Cloudflare couldn't reach origin.
**Fix**: Installed Nginx on VM, proxying port 80 → 127.0.0.1:8000.
**Status**: ✅ Fixed (Nov 22, 2026)

---

## RESOLVED: DNS pointing to wrong IP

**Cause**: Cloudflare A record was pointing to old proxy IP, not VPS.
**Fix**: Updated A record to VPS IP, kept Proxied (orange cloud).
**Status**: ✅ Fixed (Nov 22, 2026)

---

## KNOWN: WebSocket failing (wss://vrenum.app/ws/notifications)

**Cause**: Nginx `/ws/` location block with upgrade headers added but Cloudflare
WebSocket proxying may need to be enabled.
**Fix**:
1. Cloudflare Dashboard → Network → **WebSockets** → Enable
2. Nginx config already has correct upgrade headers at `/ws/`
**Status**: ⏳ Pending Cloudflare WebSocket toggle (non-critical, app works without it)

---

## KNOWN: Background worker errors (non-critical)

- `orphan_reconciliation`: Upstash Redis 500k free tier limit hit — errors every ~30s
- `back_order_monitor`: `cannot import name 'AsyncSessionLocal' from 'app.core.database'`
- `annual_renewal_reminder`: `User` has no `annual_renewal_at` attribute
- `margin_reconciliation`: `timedelta` not imported

**Impact**: None — app serves normally, these are background jobs only.
**Status**: ⏳ Deferred (fix before Render migration)

---

## TODO: Render migration (before Dec 1 VPS expiry)

**Steps**:
1. `cat /root/vrenum/.env.production` on VM → copy all env vars
2. Create Render web service pointing to GitHub repo
3. Add PostgreSQL + Redis add-ons on Render
4. Set all env vars in Render dashboard
5. Update Cloudflare A record to Render's IP/CNAME
6. Verify alembic migrations run on deploy
**Deadline**: Dec 1, 2026 (VPS expires)
**Status**: ⏳ Not started
