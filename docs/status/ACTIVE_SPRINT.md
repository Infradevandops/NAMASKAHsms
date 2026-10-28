# ACTIVE SPRINT — v4.9.x Operational Priorities

**Updated**: October 26, 2026
**Version**: 4.9.1
**Focus**: Revenue integrity, mobile conversion, cost visibility

Skipped: Telegram E2E, SDK libraries, Phase 2 Analytics, JWT migration — none are operational blockers right now.

---

## P1 — TextVerified Cost Reconciliation

**Why**: You're charging users $2.63/SMS. TV charges ~$2.00–$2.40. The margin is unverified and silent. A bad TV pricing change or billing error could erode margin for weeks without anyone noticing.

**What exists**: `app/services/provider_settlement_service.py` — built but never scheduled.

**What to build**: Wire a weekly cron into `app/core/lifespan.py` that:
1. Pulls total `verifications.cost` for the past 7 days from DB
2. Compares against TextVerified balance delta (balance at start of week minus current)
3. If margin < 15% or negative → email `ADMIN_NOTIFY_EMAIL`

**Files to touch**:
- `app/core/lifespan.py` — add weekly scheduler
- `app/services/provider_settlement_service.py` — implement the comparison logic
- `app/services/alerting_service.py` — add `send_margin_alert()`

**Done when**: Weekly cron fires, margin report visible in admin, alert fires if margin drops below threshold.

---

## P2 — Mobile Responsiveness (Public Pages First)

**Why**: Public pages are the conversion funnel. Landing, pricing, and about are broken on 320–425px. This directly affects signups.

**What exists**: `static/css/responsive.css` has 768px and 375px breakpoints only. No 320px or 425px. No CSS variable overrides for mobile typography/spacing.

**Scope — public pages only (phase 1)**:

| Page | Key issues |
|------|-----------|
| `templates/landing.html` | Hero headings oversized, sections 40px padding |
| `templates/pricing.html` | Tier cards don't stack, price 48px, padding 40px |
| `templates/about.html` | H1 48px, feature/stats/team grids don't stack |
| `templates/affiliate_program.html` | Commission table 4 cols, card grid doesn't collapse |
| `templates/contact.html` | 2-col grid never stacks, form inputs too small for touch |

**What to build**:
1. Add breakpoints to `static/css/responsive.css`: 320px, 360px, 425px with typography + spacing overrides
2. Add mobile CSS variable overrides to `static/css/design-system.css`
3. Fix each of the 5 pages above with media queries (no inline style changes needed on most)

**Done when**: All 5 pages render cleanly at 320px, 375px, 425px, 768px with no horizontal scroll and readable text.

---

## P3 — Month-End Revenue Target Alert

**Why**: `monthly_target` model and `target_tracking_service.py` both exist. No one gets notified if the month closes below target. Silent miss.

**What to build**: Add to `app/core/lifespan.py` — on the last day of each month at 20:00 UTC:
1. Query `monthly_target` for current month
2. Query actual revenue from `revenue_recognition` for current month
3. If actual < target → email `ADMIN_NOTIFY_EMAIL` with shortfall amount

**Files to touch**:
- `app/core/lifespan.py` — add month-end scheduler
- `app/services/target_tracking_service.py` — implement `check_month_end_target()`
- `app/services/alerting_service.py` — add `send_target_miss_alert()`

**Done when**: Scheduler fires on last day of month, email sent if target missed.

---

## P4 — Test Coverage 81% → 90%

**Why**: CI badge shows 81.48%. 90% is the stated target. Gap is ~8.5 percentage points. Closing this reduces regression risk as the platform grows.

**What to focus on** (highest ROI areas based on current gaps):
- `app/services/stock_monitor.py` — new file, 0 tests
- `app/services/provider_settlement_service.py` — new logic, 0 tests
- `app/services/target_tracking_service.py` — new logic, 0 tests
- Integration gaps in tier upgrade flow and refund edge cases

**Done when**: `pytest --cov=app` reports ≥ 90%.

---

## Backlog (not this sprint)

| Item | Reason deferred |
|------|----------------|
| Telegram E2E | Non-operational, cosmetic feature |
| JWT → httpOnly cookie | Architectural, low urgency at current user count |
| Phase 2 Analytics | No users yet to analyse |
| SDK libraries | No API consumers yet |
| Dashboard mobile | Public pages first, then dashboard |
| Multi-provider stock monitor | TextVerified is the only active provider |

---

## Sprint Completion Criteria

- [ ] P1: Weekly TV reconciliation cron live, margin alert tested
- [ ] P2: 5 public pages pass mobile audit at 320px–768px
- [ ] P3: Month-end target alert wired and tested
- [ ] P4: Coverage ≥ 90% on `pytest --cov=app`
