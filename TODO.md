# TODO

## Current State (March 2026)

✅ **v4.4.1 Complete** — All features implemented and tested  
✅ **Security hardened** — Emergency endpoint removed, JWT revocation, CSP nonce applied to all templates, WebSocket auth fixed  
✅ **Deployed** — Running on Render at https://namaskah.onrender.com  
✅ **TextVerified configured** — `TEXTVERIFIED_API_KEY` + `TEXTVERIFIED_EMAIL` set in Render env  
✅ **Database migrated** — Monetary columns converted to `Numeric(10,4)`  
✅ **Codebase cleaned** — 54 dead files removed, stub services deleted  

---

## Immediate Actions

### Required
- [ ] Configure email service (SMTP credentials) — set `SMTP_USERNAME` + `SMTP_PASSWORD` in Render env
- [ ] Monitor first production deployment — check TextVerified initialises cleanly in Render logs

### Optional Enhancements
- [ ] Enable Numverify API for carrier name lookup (AT&T, Verizon, etc.) — set `NUMVERIFY_API_KEY` in Render env. VOIP rejection and mobile/landline detection already work offline via `phonenumbers` library.
- [ ] Setup Prometheus + Grafana monitoring stack
- [ ] Confirm Sentry DSN is active and receiving errors

---

## Roadmap (Q2–Q4 2026)

### Q2 2026
- [ ] Enhanced analytics dashboard (carrier success rates, user preferences)
- [ ] SDK libraries (Python, JavaScript, Go)
- [ ] API rate limiting improvements
- [ ] Update `NGN_USD_RATE` in Render env if exchange rate drifts significantly from 1600

### Q3 2026
- [ ] Premium tier with Carrier Guarantee feature
- [ ] Multi-region deployment
- [ ] Advanced carrier analytics dashboard

### Q4 2026
- [ ] Commercial APIs (if volume justifies)
- [ ] Enterprise tier features
- [ ] Advanced reporting
