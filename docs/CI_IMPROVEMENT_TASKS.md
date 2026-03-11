# CI/CD Priority Fixes

**Audit date**: 2026-03-11  
**Status**: 🔄 In Progress  
**Scope**: Broken, overkill, and overlapping issues found in `ci.yml`, `deploy.yml`, `security-testing.yml`

---

## Priority 1 — Broken: Security report artifacts always empty

**File**: `.github/workflows/ci.yml` — `security` job  
**Problem**: `bandit -r app/ -ll`, `safety check`, and `semgrep ... --error` all print to stdout only. No report files are written, so the artifact upload step always uploads nothing.  
**Impact**: Security artifacts in every CI run are empty — false confidence.

**Fix**:
- `bandit -r app/ -ll -f json -o bandit-report.json`
- `safety check --json > safety-report.json`
- `semgrep --config=auto app/ --severity=ERROR --error --json > semgrep-report.json`

**Checklist**:
- [ ] `bandit` writes `bandit-report.json` before artifact upload
- [ ] `safety` writes `safety-report.json` before artifact upload
- [ ] `semgrep` writes `semgrep-report.json` before artifact upload
- [ ] Artifact upload step confirms non-empty files

---

## Priority 2 — Broken: Smoke test HTML report never created

**File**: `.github/workflows/deploy.yml` — `smoke-test` job  
**Problem**: `pytest tests/e2e/ -m smoke -v --tb=short` has no `--html` flag, so `smoke-report.html` is never written. The artifact upload silently uploads nothing.  
**Impact**: Every deploy run shows an empty smoke test artifact.

**Fix**: Add `--html=smoke-report.html` to the pytest command.

**Checklist**:
- [ ] `pytest` command includes `--html=smoke-report.html`
- [ ] `pytest-html` added to install step in smoke-test job
- [ ] Artifact upload confirms `smoke-report.html` exists after run

---

## Priority 3 — Broken: `code-quality` installs full app deps unnecessarily

**File**: `.github/workflows/ci.yml` — `code-quality` job  
**Problem**: `pip install -r requirements.txt` installs the entire app (~2–3 min) just to run `flake8`, `black`, and `isort`. These tools have no app dependencies.  
**Impact**: ~2–3 min wasted on every push/PR for zero benefit.

**Fix**: Remove `pip install -r requirements.txt` from the `code-quality` job. Only install `flake8 black isort`.

**Checklist**:
- [ ] `pip install -r requirements.txt` removed from `code-quality` job
- [ ] Job still installs `flake8 black isort`
- [ ] `code-quality` job runtime drops significantly

---

## Priority 4 — Broken: `accessibility-audit` crashes on startup

**File**: `.github/workflows/security-testing.yml` — `accessibility-audit` job  
**Problem 1**: No `DATABASE_URL` env var set when starting the app — app crashes before any audit runs.  
**Problem 2**: `lighthouse` CLI requires Chromium but it is not installed in the job — lighthouse step always fails.  
**Impact**: Accessibility audit has never successfully run.

**Fix**:
- Add `DATABASE_URL: sqlite:///./test.db` to the app startup step
- Add `npx playwright install chromium` or install `chromium` via apt before running lighthouse

**Checklist**:
- [ ] `DATABASE_URL` set in app startup step of `accessibility-audit`
- [ ] Chromium installed before lighthouse runs
- [ ] App starts successfully (`curl -f http://localhost:8000/health` passes)
- [ ] All three tools (axe, pa11y, lighthouse) produce output files

---

## Priority 5 — Broken: Secrets check always shows "missing"

**File**: `.github/workflows/ci.yml` — `deployment-readiness` job  
**Problem**: `[ -n "${{ secrets.X }}" ]` — GitHub masks all secret values in expressions, so the interpolated value is always an empty string. Every secret shows as "missing" regardless of whether it's set.  
**Impact**: Misleading output on every `main` push — can't trust the readiness check.

**Fix**: Use `env:` to expose secrets as env vars, then check the env var:
```yaml
env:
  RENDER_DEPLOY_HOOK: ${{ secrets.RENDER_DEPLOY_HOOK }}
  PRODUCTION_URL: ${{ secrets.PRODUCTION_URL }}
  RENDER_ROLLBACK_HOOK: ${{ secrets.RENDER_ROLLBACK_HOOK }}
run: |
  [ -n "$RENDER_DEPLOY_HOOK" ] && echo "✅ RENDER_DEPLOY_HOOK set" || echo "⚠️ RENDER_DEPLOY_HOOK missing"
  [ -n "$PRODUCTION_URL" ] && echo "✅ PRODUCTION_URL set" || echo "⚠️ PRODUCTION_URL missing"
  [ -n "$RENDER_ROLLBACK_HOOK" ] && echo "✅ RENDER_ROLLBACK_HOOK set" || echo "⚠️ RENDER_ROLLBACK_HOOK missing"
```

**Checklist**:
- [ ] Secrets exposed via `env:` block, not inline expressions
- [ ] Check on `main` push correctly shows ✅ for all three secrets

---

## Priority 6 — Overkill: `deployment-check` in `security-testing.yml` is useless

**File**: `.github/workflows/security-testing.yml` — `deployment-check` job  
**Problem**: Job just echoes strings — "✅ E2E tests passed", "Manual verification required" etc. No actual checks. `ci.yml` already has a real `deployment-readiness` job that validates files and secrets.  
**Impact**: Wastes a runner, adds noise to every `main` push.

**Fix**: Remove the `deployment-check` job from `security-testing.yml` entirely.

**Checklist**:
- [ ] `deployment-check` job removed from `security-testing.yml`
- [ ] `security-testing.yml` only contains `e2e-tests` and `accessibility-audit`

---

## Priority 7 — Overkill: Duplicate smoke tests on every push

**File**: `.github/workflows/security-testing.yml` — `e2e-tests` job  
**Problem**: Smoke tests run against a SQLite localhost app on every push to `main`/`develop`. `deploy.yml` already runs smoke tests post-deploy against real production. Two smoke runs per push to `main`, one of which uses a broken database backend (SQLite vs PostgreSQL).  
**Impact**: Wasted CI minutes + false results from SQLite run.

**Fix**: Remove the `Run Smoke Tests` step from `security-testing.yml` `e2e-tests` job. Keep only the full E2E suite (main branch only). Smoke tests belong exclusively in `deploy.yml` against production.

**Checklist**:
- [ ] `Run Smoke Tests` step removed from `security-testing.yml`
- [ ] Full E2E suite (`main` only) still runs in `security-testing.yml`
- [ ] Smoke tests still run post-deploy in `deploy.yml` against `PRODUCTION_URL`

---

## Priority 8 — Overkill: `smoke-test` job installs full app deps

**File**: `.github/workflows/deploy.yml` — `smoke-test` job  
**Problem**: `pip install -r requirements.txt` installs all app dependencies (SQLAlchemy, FastAPI, etc.) just to run Playwright smoke tests. Playwright tests hit the live production URL — they don't import app code.  
**Impact**: ~2–3 min wasted installing unused deps on every deploy.

**Fix**: Replace `pip install -r requirements.txt` with only what's needed:
```bash
pip install pytest pytest-playwright pytest-html
playwright install chromium
```

**Checklist**:
- [ ] `pip install -r requirements.txt` removed from `smoke-test` job
- [ ] Only `pytest pytest-playwright pytest-html` installed
- [ ] Smoke tests still pass against production

---

## Summary

| # | File | Type | Impact |
|---|------|------|--------|
| 1 | `ci.yml` security job | Broken | Artifacts always empty |
| 2 | `deploy.yml` smoke-test | Broken | Report never created |
| 3 | `ci.yml` code-quality | Broken | 2–3 min wasted per run |
| 4 | `security-testing.yml` accessibility-audit | Broken | Job has never run successfully |
| 5 | `ci.yml` deployment-readiness | Broken | Secrets check always wrong |
| 6 | `security-testing.yml` deployment-check | Overkill | Duplicate, echoes only |
| 7 | `security-testing.yml` e2e-tests smoke | Overkill | Duplicate + SQLite false results |
| 8 | `deploy.yml` smoke-test deps | Overkill | 2–3 min wasted per deploy |

**Fix order**: 1 → 2 → 3 → 5 (broken first) → 4 → 6 → 7 → 8 (cleanup second)

---

## Commit Log

| Commit | Date | Description |
|--------|------|-------------|
| `0e5a32f8` | 2026-03-11 | Fix all test collection errors, disable redundant CI workflows |
| `b36214e5` | 2026-03-11 | Fix TextVerified 429s on restart, pin urllib3/charset-normalizer |
| `34b618d8` | 2026-03-11 | Singleton TextVerifiedService + 60s admin balance cache |
| `bbaee925` | 2026-03-11 | Phase 6: remove duplicate security jobs, fix sleep 90, register pytest markers |
| `6f339d05` | 2026-03-11 | Repo cleanup: untrack certs, coverage.xml, archive stale docs |

## Open Infrastructure Items
1. 🔄 Provision Redis (Upstash free tier) → set `REDIS_URL` on Render
2. 🔄 Configure email service env vars on Render
3. 🔄 Raise coverage gate 36% → 40% → 45% → 50% incrementally
4. 🔄 Verify semgrep has zero ERROR findings in codebase

**CI Run URL**: https://github.com/Infradevandops/NAMASKAHsms/actions
