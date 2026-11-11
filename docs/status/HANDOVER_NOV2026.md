# HANDOVER — VRENUM SMS
# Session: November 2026 — Sprint G/H Planning + Partial Execution

**HEAD**: `5f3eb79a` on origin/main
**Written**: November 2026
**For**: Next engineer / next session

---

## WHAT WAS DONE THIS SESSION

### Sprints A–F: All 66 tasks executed and pushed

Full execution across 6 sprints. Key commits:

| Commit | What |
|--------|------|
| `a7d45469` | OTP passwordless login (Redis-backed, 10-min TTL, 3/15min rate limit) |
| `331db1d5` | AUTH-001/002, removed fake `validating` SSE step, version 4.9.9 |
| `7c79789f` | Area code fix, voice transcribing, reuse endpoint+UI+WS, stock watches, back-order monitor, bulk bonus, SubscriptionAddon/StockWatch/RentalBackOrder models, migration |
| `bafb5db1` | Annual plans, PAYG API addon, admin portal, lifespan wiring |
| `776ebed1` | MASTER_TASKS corrected 25→45/71 |
| `506e9b6d` | All 21 remaining A–F tasks: C-006/007/015/018/019, D-006/007/010/013/014/015/017/018/019/020, E-003/005/006 |
| `8b022c7d` | B-008/F-001: smsAndVoiceCombo — schema, pricing +$0.50, TV capability, SSE, UI badge |
| `48e33990` | SDK_OPTIMIZATION_OPPORTUNITIES.md — all 14 items marked done |
| `6c270046` | Sprint G task doc: provider resilience, timeout standards, Vrenum SDK/API contract |
| `a8d2a189` | Sprint H task doc: purchase flow UX overhaul (initial) |
| `d8f29f53` | Sprint H rewrite with exact TV spec from screenshots (arc spinner, 11 message pairs, carrier icon, MM:SS, full SMS, reuse btn, webhook monitor) |
| `5f3eb79a` | ACTIVE_SPRINT consolidated (all open work in one file), MASTER_TASKS updated 66/83 |

### Sprint G: Partial execution (interrupted)

The following G tasks were **written to files but the session was cancelled before commit**:

- `G-004` — `base_provider.py` updated: `PURCHASE_TIMEOUT_S=12`, `CANCEL_TIMEOUT_S=5`, `STATUS_TIMEOUT_S=8`, `MAX_PURCHASE_ATTEMPTS=1`, `list_recent_purchases()` default method added
- `G-004` — All 4 adapters (`textverified_adapter.py`, `fivesim_adapter.py`, `telnyx_adapter.py`, `pvapins_adapter.py`) wrapped with `asyncio.wait_for(PURCHASE_TIMEOUT_S)`
- `G-001 + G-002` — `purchase_endpoints.py` SSE stream updated: `asyncio.wait_for(12s)` on purchase call, `purchasing_delayed` SSE event on timeout, Redis `purchase_pending:*` key written, keepalive ping every 5s
- `G-003` — `app/workers/orphan_reconciliation.py` created (new file)
- `G-006` — `app/services/providers/circuit_breaker.py` created (new file)
- `H-006` — `app/workers/webhook_health_monitor.py` creation was **cancelled mid-write**

**These changes are in the working tree but NOT committed or pushed.**

Run `git status` to confirm, then `git diff` to review before committing.

---

## CURRENT STATE

### Repository
- HEAD: `5f3eb79a` — all docs pushed, code changes uncommitted
- Branch: `main`
- Server last deployed: `e06e91ce` (everything from there to `5f3eb79a` is pending deploy)
- Migration pending on server: `alembic upgrade head` (covers `expiry_warned_at`, `billing_period`, `annual_renewal_at`, `stock_watches`, `rental_back_orders`, `subscription_addons`)

### Open code tasks (13 total)

**Partially done in working tree (need commit):**
- G-001: SSE 12s timeout + `purchasing_delayed` + Redis pending key ✅ written
- G-002: SSE keepalive ping ✅ written (nginx config is manual — see G-002b)
- G-003: `orphan_reconciliation.py` ✅ written — needs wiring into `lifespan.py`
- G-004: base_provider + all 4 adapters ✅ written
- G-006: `circuit_breaker.py` ✅ written — needs wiring into `provider_router.py`
- H-006: `webhook_health_monitor.py` ❌ cancelled mid-write — needs to be created fresh

**Not started:**
- H-001: Purchase loading modal (dark card, arc spinner, TV 11-message sequence)
- H-002: Step 3 overhaul (carrier icon, MM:SS countdown, full SMS, reuse button)
- H-003: Step 3 activity feed log
- H-004: `purchasing_delayed` frontend state (blocked on G-001 deploy)
- H-005: Combo method picker card (P2)
- G-005: Vrenum API contract doc (P2)
- E-004: CI triage (manual)

---

## NEXT STEPS — EXACT ORDER

### 1. Check working tree and commit G-001/002/003/004/006

```bash
git status
git diff app/services/providers/base_provider.py
git diff app/api/verification/purchase_endpoints.py
```

If the diffs look correct:

```bash
git add app/services/providers/base_provider.py \
        app/services/providers/textverified_adapter.py \
        app/services/providers/fivesim_adapter.py \
        app/services/providers/telnyx_adapter.py \
        app/services/providers/pvapins_adapter.py \
        app/api/verification/purchase_endpoints.py \
        app/workers/orphan_reconciliation.py \
        app/services/providers/circuit_breaker.py
git commit -m "G-001/002/003/004/006: 12s purchase timeout, purchasing_delayed SSE, keepalive, orphan recon worker, provider timeout contract, circuit breaker"
git push
```

### 2. Wire G-003 and G-006 into lifespan + router

**`app/core/lifespan.py`** — add after `run_back_order_monitor()`:
```python
from app.workers.orphan_reconciliation import run_orphan_reconciliation
asyncio.create_task(run_orphan_reconciliation())
startup_logger.info("✅ Orphan reconciliation worker started (60s loop)")
```

**`app/services/providers/provider_router.py`** — in `get_provider()`, before returning primary:
```python
from app.services.providers.circuit_breaker import circuit_breaker
if circuit_breaker.is_open(primary.name):
    logger.warning(f"Circuit breaker OPEN for {primary.name}, routing to failover")
    # fall through to failover logic
```

And in `purchase_with_failover()`, wrap the `primary.purchase_number()` call:
```python
try:
    result = await primary.purchase_number(**provider_kwargs)
    circuit_breaker.record_success(primary.name)
    ...
except ProviderError as e:
    circuit_breaker.record_failure(primary.name)
    ...
```

### 3. Create H-006 webhook health monitor (was cancelled)

New file `app/workers/webhook_health_monitor.py`:
```python
"""TV webhook auto-re-enable monitor. Runs every 30 min.
TV auto-disables webhook after repeated delivery failures (e.g. during deploys).
"""
import asyncio, os, requests
from app.core.logging import get_logger
logger = get_logger(__name__)

async def run_webhook_health_monitor():
    while True:
        try:
            await _check_and_heal()
        except Exception as e:
            logger.error(f"Webhook health monitor error: {e}")
        await asyncio.sleep(1800)

async def _check_and_heal():
    api_key = os.getenv("TEXTVERIFIED_API_KEY")
    base_url = os.getenv("APP_BASE_URL", "https://vrenum.app")
    endpoint = f"{base_url}/api/verification/webhook/tv"
    if not api_key:
        return
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        resp = await asyncio.to_thread(
            requests.get, "https://app.textverified.com/api/pub/v2/webhooks",
            headers=headers, timeout=10
        )
        if resp.status_code != 200:
            return
        hooks = resp.json().get("data", [])
        our_hook = next((w for w in hooks if endpoint in str(w.get("url", ""))), None)
        if our_hook and not our_hook.get("enabled", True):
            hook_id = our_hook["id"]
            await asyncio.to_thread(
                requests.patch,
                f"https://app.textverified.com/api/pub/v2/webhooks/{hook_id}",
                headers=headers, json={"enabled": True}, timeout=10
            )
            logger.info(f"Webhook health: re-enabled TV webhook {hook_id}")
    except Exception as e:
        logger.warning(f"Webhook health check failed (non-critical): {e}")
```

Wire into `lifespan.py`:
```python
from app.workers.webhook_health_monitor import run_webhook_health_monitor
asyncio.create_task(run_webhook_health_monitor())
startup_logger.info("✅ TV webhook health monitor started (30-min loop)")
```

### 4. Execute Sprint H frontend tasks

All spec is in `docs/engineering/development/PURCHASE_FLOW_UX_OVERHAUL.md`.
The exact TV message sequence, HTML structure, CSS, and JS are fully specced.
H-001 and H-002 are the highest value — do those first.

### 5. Deploy

```bash
ssh user@server
cd ~/vrenum
git pull
alembic upgrade head
./restart.sh
# Then set nginx:
# proxy_read_timeout 30s;
# proxy_send_timeout 30s;
```

---

## KEY FACTS FOR NEXT SESSION

**The money leak**: TV's SDK has invisible 3× retry (7s overhead). SSE had no timeout on the purchase call. G-001 fixes this with `asyncio.wait_for(12s)`. The thread keeps running after timeout — G-003 (orphan worker) finds the result and heals the DB. This is the most important thing to ship.

**The UX gap**: Vrenum shows "Confirming availability..." + spinner for 15s. TV shows 11 rotating message pairs across 4 phases with an arc-orbiting-icon animation. Full spec with exact TV copy in `PURCHASE_FLOW_UX_OVERHAUL.md`. H-001 is 2.5h and closes the gap entirely.

**TV webhook auto-disable**: TV disables our webhook after repeated failures during deploys. H-006 is a 30-min background loop that re-enables it. Screenshot evidence in `docs/artifacts/Screenshot 2026-10-31 at 04.40.53.png`.

**Provider architecture**: Vrenum has 4 providers (TV, 5sim, Telnyx, PVApins) behind `ProviderRouter`. G-004 adds `PURCHASE_TIMEOUT_S=12` to the base class — all adapters now enforce it. G-006 adds a circuit breaker so a degraded TV doesn't cascade into 50 concurrent 12s timeouts.

**Vrenum SDK/API contract**: Defined in `PROVIDER_RESILIENCE_AND_PLATFORM_STANDARDS.md`. Nothing TV-specific leaks through the public API. `activation_id`, `ReservationCapability`, `RentalDuration` are all hidden. Public surface is `verification_id`, `capability` (sms/voice/combo), `duration` (1d/3d/7d/30d).

**Deploy gap**: Server is on `e06e91ce`. Everything from there to `5f3eb79a` is pending. The migration must run before the new code is live (`alembic upgrade head`).

---

## FILE INDEX

| File | Role |
|------|------|
| `docs/status/ACTIVE_SPRINT.md` | **Single actionable task list — start here** |
| `docs/status/MASTER_TASKS.md` | Historical record of all completed work |
| `docs/engineering/PROVIDER_RESILIENCE_AND_PLATFORM_STANDARDS.md` | Sprint G full spec |
| `docs/engineering/development/PURCHASE_FLOW_UX_OVERHAUL.md` | Sprint H full spec (exact TV copy) |
| `docs/engineering/SDK_OPTIMIZATION_OPPORTUNITIES.md` | All done — closed |
| `docs/artifacts/` | 31 TV screenshots (Oct–Nov 2026) |
