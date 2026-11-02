# AUDIT IMPLEMENTATION PLAN

**Source**: `docs/Audit`
**Created**: November 1, 2026
**Version**: 4.9.7
**Repo health score**: 5.5 / 10

---

## Repo Health Score Breakdown

| Area | Score | Reason |
|------|-------|--------|
| CI pipeline | 6/10 | Runs and blocks on failures, but deploy is not gated on CI |
| Deploy pipeline | 3/10 | Fires on every push to main regardless of CI result |
| Health endpoint | 1/10 | Always returns 200 — checks nothing |
| Critical-path tests | 4/10 | Unit tests exist but payment/SMS/auth lifecycle not covered |
| Branch protection | 0/10 | No branch protection rules configured on GitHub |
| Rollback procedure | 3/10 | "git revert" documented but no DB rollback, no container restore |
| Observability | 6/10 | Sentry + BetterStack active, but no metric thresholds |
| Secret governance | 4/10 | .env.example exists, no rotation process documented |
| Architecture visibility | 7/10 | Modular structure intact, docs exist |
| Technical debt register | 0/10 | Does not exist |

**Overall**: 5.5 / 10 — functional product, not production-grade operations

---

## The 5 Most Important Improvements (Priority Order)

1. **Gate deploy on green CI** — deploy fires on every push regardless of test results
2. **Fix /health endpoint** — always returns 200, deploy health check is meaningless
3. **Add post-deploy feature smoke** — nothing verifies SMS/auth/payments work after deploy
4. **Branch protection on main** — direct pushes to main bypass all CI
5. **Real rollback procedure** — no DB migration rollback, no container restore path

---

## Task Inventory

### TASK-1 — Gate deploy on green CI ✅ EXECUTABLE NOW
**Audit item**: #2 (branch protection) + implicit in #4
**Current state**: `deploy.yml` triggers on `push: branches: [main]` independently of `ci.yml`. A push that fails all tests still deploys.
**Fix**: Change `deploy.yml` trigger from `push` to `workflow_run` on `ci.yml` completion, with `if: conclusion == 'success'` guard.
**Files**: `.github/workflows/deploy.yml`
**Effort**: 5 lines

---

### TASK-2 — Fix /health endpoint ✅ EXECUTABLE NOW
**Audit item**: #4
**Current state**:
```python
async def health_check():
    return {"status": "healthy", "service": "vrenum-sms"}
```
Always 200. Checks nothing. Deploy waits 10 min for this — it passes even if DB is down.
**Fix**: Check DB connectivity, Redis ping, TV API key present. Return 503 if any fail.
**Files**: `app/api/main_routes.py`
**Effort**: ~20 lines

---

### TASK-3 — Post-deploy feature smoke workflow ✅ EXECUTABLE NOW
**Audit item**: #1 (production-critical flows)
**Current state**: Nothing runs after deploy to verify the live app works.
**Fix**: New `feature-smoke.yml` workflow triggered after `deploy.yml` succeeds. Hits live prod endpoints:
- `GET /health` — DB + Redis + TV config
- `POST /api/auth/login` — JWT returned
- `GET /api/services/stock` — at least 1 service available
- `GET /api/notifications/categories` — 200
- `GET /api/billing/balance` — 200
Reports pass/fail per feature. Failure triggers Sentry alert.
**Files**: `.github/workflows/feature-smoke.yml`
**Effort**: New file ~80 lines

---

### TASK-4 — Branch protection on main + develop branch 📋 MANUAL (GitHub UI)
**Audit item**: #2
**Current state**: No branch protection. All work pushed directly to main. 6 stale branches deleted. `develop` branch created.

**Branch design**:
```
develop  ←── all work pushed here freely
   │
   │  PR: develop → main (when ready to ship)
   │  CI must be green on develop before PR can merge
   │  main is protected — no direct pushes allowed
   │
   ▼
main  ←── only receives green-CI-verified merges
   │
   ▼
deploy.yml fires → prod
```

**Branches kept**:
- `main` — protected, prod-only
- `develop` — working branch, CI runs on every push
- `pre-rebrand/v4.7.1-snapshot` — frozen rollback reference, keep

**Branches deleted**: `Oghenesuvwe-dev-patch-1`, `dependabot/pip/pip-f38aae6ccf`, `feature/rebrand-vrenum`, 3x `snyk-fix-*`

**Manual steps in GitHub UI** (Settings → Branches → Add rule for `main`):
1. Branch name pattern: `main`
2. ☑ Require status checks to pass before merging
   - Add: `secrets-scan`, `code-quality`, `frontend-unit-tests`, `unit-tests`
3. ☑ Require branches to be up to date before merging
4. ☑ Do not allow bypassing the above settings
5. Leave "Require a pull request before merging" OFF (solo dev)
6. Save

**After this is set**: direct pushes to main will be rejected by GitHub. All work goes to `develop`, PR to `main` when CI is green.

---

### TASK-5 — Real rollback procedure 📋 DOC TASK
**Audit item**: #3
**Current state**: PLATFORM_STATUS says "Rollback: git revert to previous commit" — no DB steps, no container steps.
**Fix**: Write `docs/deployment/ROLLBACK_PROCEDURE.md` with:
- Step 1: SSH to server, `git log --oneline -5` to find target commit
- Step 2: `git reset --hard <commit>` + `docker compose up -d --build --force-recreate`
- Step 3: DB migration rollback — `alembic downgrade -1` (or specific revision)
- Step 4: Verify `/health` returns all green
- Step 5: If DB rollback needed, restore from last pg_dump backup
**Files**: `docs/deployment/ROLLBACK_PROCEDURE.md`
**Effort**: Doc only

---

### TASK-6 — Staging/pre-prod validation path 📋 FUTURE
**Audit item**: #6
**Current state**: No staging environment.
**Fix**: Not executable now — requires a second server or Docker environment. Deferred to when first paying users are onboarded and risk of prod surprises increases.
**Status**: Deferred

---

### TASK-7 — Targeted integration tests 🔄 IN PROGRESS
**Audit item**: #7
**Current state**: Integration tests exist but are non-blocking in CI (`continue-on-error: true`). Critical paths (payment webhook, SMS lifecycle, auth) not covered.
**Fix**: Part of the coverage push sprint (v4.9.7 P1). Promote integration tests to blocking once stable.
**Status**: In progress — coverage sprint

---

### TASK-8 — Dependency safety tracking 📋 DOC TASK
**Audit item**: #8
**Fix**: Add `docs/engineering/DEPENDENCY_REGISTER.md` listing runtime deps, last reviewed date, known advisories. Enable GitHub Dependabot alerts on the repo.
**Status**: Planned

---

### TASK-9 — Observability thresholds 📋 FUTURE
**Audit item**: #9
**Current state**: Sentry + BetterStack active. No metric baselines or alert thresholds set.
**Fix**: Define baselines in BetterStack for:
- SMS delivery rate < 80% → alert
- Payment webhook success rate < 95% → alert
- /health response time > 2s → alert
**Status**: Planned — after first 100 users establish baselines

---

### TASK-10 — Review "production-ready" claims 📋 DOC TASK
**Audit item**: #10
**Current state**: PLATFORM_STATUS says "✅ Production Ready" but health check is fake, deploy is not CI-gated, no branch protection.
**Fix**: Update PLATFORM_STATUS after TASK-1, TASK-2, TASK-3 are complete. Only claim production-ready once the 5 critical items are done.
**Status**: Blocked on TASK-1/2/3

---

### TASK-11 — Technical debt register 📋 DOC TASK
**Audit item**: #11
**Fix**: Create `docs/engineering/TECHNICAL_DEBT.md` listing:
- `validating` SSE step is a fake UX label (no real work)
- `_mock_services()` dead code still in textverified_service.py
- Integration tests non-blocking in CI
- `/health` was always-200 (fixed in TASK-2)
- `tv:services_list` 24h cache can serve stale prices
**Status**: Planned

---

### TASK-12 — Domain ownership docs 📋 FUTURE
**Audit item**: #12
**Status**: Deferred — low priority for solo dev

---

### TASK-13 — Architecture visibility 📋 ONGOING
**Audit item**: #13
**Current state**: Modular structure intact. Boundaries visible.
**Status**: No action needed now

---

### TASK-14 — Release checklist 📋 DOC TASK
**Audit item**: #14
**Fix**: Create `docs/deployment/RELEASE_CHECKLIST.md`:
- [ ] All CI jobs green on main
- [ ] No pending DB migrations without corresponding alembic version
- [ ] TEXTVERIFIED_API_KEY and PAYSTACK_SECRET_KEY verified in .env.production
- [ ] /health returns all green post-deploy
- [ ] Feature smoke workflow passes
- [ ] CHANGELOG updated
- [ ] PLATFORM_STATUS version bumped
**Status**: Planned

---

### TASK-15 — Migration health tracking 📋 DOC TASK
**Audit item**: #15
**Current state**: Migrations run in CI (`alembic upgrade head`) but no separate validation step in deploy.
**Fix**: Add `alembic check` step to deploy workflow before `docker compose up` to confirm no pending migrations are being skipped.
**Files**: `.github/workflows/deploy.yml`
**Status**: Planned — add alongside TASK-1

---

## Execution Plan

### This session — execute TASK-1, TASK-2, TASK-3

These are the three automatable fixes. Everything else is either manual (GitHub UI), doc-only, or deferred.

**TASK-1**: Fix `deploy.yml` — gate on CI green
**TASK-2**: Fix `/health` — real DB + Redis + TV checks
**TASK-3**: Write `feature-smoke.yml` — post-deploy live feature verification

### Next session
- TASK-4: Branch protection (manual, GitHub UI, 5 min)
- TASK-5: Rollback procedure doc
- TASK-14: Release checklist doc
- TASK-11: Technical debt register

---

## Status Tracker

| Task | Description | Status |
|------|-------------|--------|
| TASK-1 | Gate deploy on green CI | ✅ Done — `deploy.yml` now `workflow_run` gated |
| TASK-2 | Fix /health endpoint | ✅ Done — DB + Redis + TV config checks, 503 on failure |
| TASK-3 | Post-deploy feature smoke | ✅ Done — `feature-smoke.yml` 6 live checks |
| TASK-4 | Branch protection (manual) | 📋 Manual |
| TASK-5 | Rollback procedure doc | 📋 Planned |
| TASK-6 | Staging environment | ⏸ Deferred |
| TASK-7 | Integration tests blocking | 🔄 In progress |
| TASK-8 | Dependency register | 📋 Planned |
| TASK-9 | Observability thresholds | ⏸ After 100 users |
| TASK-10 | Review prod-ready claims | ⏸ Blocked on 1/2/3 |
| TASK-11 | Technical debt register | 📋 Planned |
| TASK-12 | Domain ownership docs | ⏸ Deferred |
| TASK-13 | Architecture visibility | ✅ No action needed |
| TASK-14 | Release checklist | 📋 Planned |
| TASK-15 | Migration health in deploy | 📋 Planned |
