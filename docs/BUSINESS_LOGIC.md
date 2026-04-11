# Namaskah — How It Works

---

## The Simple Version

Namaskah buys phone numbers from TextVerified and resells them to users at a markup.

```
User pays $2.50
Namaskah pays TextVerified ~$0.80
Namaskah keeps ~$1.70 profit
```

That's the entire business model.

---

## What Happens When a User Buys a Verification

```
1. User picks a service (e.g. WhatsApp)
2. Namaskah checks user has enough balance
3. Namaskah asks TextVerified: "give me a US number for WhatsApp"
4. TextVerified returns a phone number e.g. +1 (213) 555-1234
5. Namaskah charges the user $2.50
6. User sees the phone number on screen
7. User enters that number into WhatsApp
8. WhatsApp sends an SMS code to that number
9. Namaskah polls TextVerified every 5 seconds: "any SMS yet?"
10. TextVerified returns the SMS
11. Namaskah extracts the code e.g. 806185
12. User sees the code on screen
13. User enters the code into WhatsApp — done
```

---

## TextVerified API Calls

| What | When |
|------|------|
| Buy a number | When user clicks "Get Number" |
| Check for SMS | Every 5 seconds after number is assigned |
| Cancel number | When user cancels or 10 min timeout |
| Get balance | Admin dashboard only |
| List services | App startup (cached 24h) |

---

## Pricing

| Tier | Monthly | Per SMS | Filters |
|------|---------|---------|---------|
| Freemium | Free | $2.22 | None |
| Pay-As-You-Go | Free | $2.50 + surcharges | Area code / Carrier |
| Pro | $25 | $0.30 overage after $15 quota | Included |
| Custom | $35 | $0.20 overage after $25 quota | Included |

---

## Admin vs Regular Users

- **Regular users** — balance stored in database, topped up via Paystack
- **Admin** — balance is the live TextVerified account balance, no Paystack needed

---

## Bugs Fixed (April 6, 2026)

### Bug 1 — Stale SMS codes delivered
TextVerified recycles phone numbers. Old SMS from previous users were being delivered as if they were new. Users got charged and received dead codes.

**Fix**: Only accept SMS that arrived after the verification was created.

### Bug 2 — Wrong code extracted
The code `806-185` was being missed because the regex only looked for plain numbers. TextVerified's own parsed code was being ignored.

**Fix**: Use TextVerified's parsed code directly. Regex is now a last resort only.

### Bug 3 — WebSocket crashing every 12 seconds
The server was trying to accept the same WebSocket connection twice. This crashed the connection, the browser retried, and the cycle repeated forever — filling the entire server log with errors.

**Fix**: Accept the connection once. Register it without accepting again.

---

## Known Risks

1. **Historical stale codes** — users charged before April 6 fix may need manual refunds
2. **Timeout refunds** — if polling hits 10 minutes with no SMS, a refund is triggered but not guaranteed to succeed
3. **10-minute window** — users have 10 minutes to use the number before it expires
