# CI/CD Priority Fixes

**Audit date**: 2026-03-11  
**Status**: ✅ Complete  
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

**Acceptance criteria**:
- [x] `bandit-report.json` exists and is non-empty after the security job runs
- [x] `safety-report.json` exists and is non-empty after the security job runs
- [x] `semgrep-report.json` exists and is non-empty after the security job runs
- [x] Artifact `security-reports-<run_id>` in GitHub Actions UI contains all three files
- [x] CI still fails (exit 1) when bandit/safety/semgrep find blocking issues

---

## Priority 2 — Broken: Smoke test HTML report never created

**File**: `.github/workflows/deploy.yml` — `smoke-test` job  
**Problem**: `pytest tests/e2e/ -m smoke -v --tb=short` has no `--html` flag, so `smoke-report.html` is never written. The artifact upload silently uploads nothing.  
**Impact**: Every deploy run shows an empty smoke test artifact.

**Fix**: Add `--html=smoke-report.html` to the pytest command and install `pytest-html`.

**Acceptance criteria**:
- [x] `pytest-html` present in the `smoke-test` install step
- [x] `pytest` command includes `--html=smoke-report.html`
- [x] Artifact `smoke-test-report-<run_id>` in GitHub Actions UI contains a non-empty `smoke-report.html`
- [x] Report renders correctly in browser (title, pass/fail counts visible)

---

## Priority 3 — Broken: `code-quality` installs full app deps unnecessarily

**File**: `.github/workflows/ci.yml` — `code-quality` job  
**Problem**: `pip install -r requirements.txt` installs the entire app (~2–3 min) just to run `flake8`, `black`, and `isort`. These tools have no app dependencies.  
**Impact**: ~2–3 min wasted on every push/PR for zero benefit.

**Fix**: Remove `pip install -r requirements.txt` from the `code-quality` job. Only install `flake8 black isort`.

**Acceptance criteria**:
- [x] `pip install -r requirements.txt` absent from `code-quality` job
- [x] `flake8`, `black`, `isort` still installed and all three checks still run
- [x] `code-quality` job completes in under 60 seconds (vs ~3 min before)

---

## Priority 4 — Broken: `accessibility-audit` crashes on startup

**File**: `.github/workflows/security-testing.yml` — `accessibility-audit` job  
**Problem 1**: No `DATABASE_URL` env var set when starting the app — app crashes before any audit runs.  
**Problem 2**: `lighthouse` CLI requires Chromium but it is not installed in the job — lighthouse step always fails.  
**Problem 3**: `sleep 10` startup wait has no health check — app may not be ready when audit tools run.  
**Impact**: Accessibility audit has never successfully run.

**Fix**:
- Add `DATABASE_URL: sqlite:///./test.db` + required secrets to the app startup step
- Add `npx playwright install chromium` before running lighthouse
- Replace `sleep 10` with a retry health check loop (same pattern as `e2e-tests` job)

**Acceptance criteria**:
- [x] `DATABASE_URL` set in the app startup step of `accessibility-audit`
- [x] App startup step includes a health check retry loop (not bare `sleep 10`)
- [x] `curl -f http://localhost:8000/health` passes before any audit tool runs
- [x] Chromium installed before lighthouse runs
- [x] All three tools (axe, pa11y, lighthouse) produce non-empty output files
- [x] Artifact `accessibility-reports-<run_id>` contains `axe-report.json`, `pa11y-report.json`, `lighthouse-a11y.json`

---

## Priority 5 — Broken: Secrets check always shows "missing"

**File**: `.github/workflows/ci.yml` — `deployment-readiness` job  
**Problem**: `[ -n "${{ secrets.X }}" ]` — GitHub masks all secret values in expressions, so the interpolated value is always an empty string. Every secret shows as "missing" regardless of whether it's set.  
**Impact**: Misleading output on every `main` push — can't trust the readiness check.

**Fix**: Expose secrets via `env:` block, then check the env var in the shell:
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

**Acceptance criteria**:
- [x] Secrets exposed via `env:` block, not inline `${{ secrets.X }}` expressions in the shell command
- [x] On `main` push with all three secrets set, all three lines show ✅
- [x] On `main` push with a secret missing, that line correctly shows ⚠️

---

## Priority 6 — Overkill: `deployment-check` in `security-testing.yml` is useless

**File**: `.github/workflows/security-testing.yml` — `deployment-check` job  
**Problem**: Job just echoes strings — "✅ E2E tests passed", "Manual verification required" etc. No actual checks. `ci.yml` already has a real `deployment-readiness` job that validates files and secrets.  
**Impact**: Wastes a runner, adds noise to every `main` push.

**Fix**: Remove the `deployment-check` job from `security-testing.yml` entirely.

**Acceptance criteria**:
- [x] `deployment-check` job absent from `security-testing.yml`
- [x] `security-testing.yml` only contains `e2e-tests` and `accessibility-audit` jobs
- [x] No regression in `ci.yml` deployment-readiness coverage

---

## Priority 7 — Overkill: Duplicate smoke tests on every push

**File**: `.github/workflows/security-testing.yml` — `e2e-tests` job  
**Problem**: Smoke tests run against a SQLite localhost app on every push to `main`/`develop`. `deploy.yml` already runs smoke tests post-deploy against real production. Two smoke runs per push to `main`, one of which uses a broken database backend (SQLite vs PostgreSQL).  
**Impact**: Wasted CI minutes + false results from SQLite run.

**Fix**: Remove the `Run Smoke Tests` step from `security-testing.yml`. Keep only the full E2E suite (main branch only). Smoke tests belong exclusively in `deploy.yml` against production.

**Note**: Removing this step also removes the only place `smoke-report.html` was correctly generated — Priority 2 (`deploy.yml`) must be fixed in the same pass so smoke reports are not lost.

**Acceptance criteria**:
- [x] `Run Smoke Tests` step absent from `security-testing.yml` `e2e-tests` job
- [x] Full E2E suite (`main` only) still runs in `security-testing.yml` with `--html=e2e-report.html`
- [x] Smoke tests still run post-deploy in `deploy.yml` against `PRODUCTION_URL` with `--html=smoke-report.html` (P2 fix applied)
- [x] No duplicate smoke runs visible in GitHub Actions on a `main` push

---

## Priority 8 — Overkill: `smoke-test` job installs full app deps

**File**: `.github/workflows/deploy.yml` — `smoke-test` job  
**Problem**: `pip install -r requirements.txt` installs all app dependencies (SQLAlchemy, FastAPI, etc.) just to run Playwright smoke tests. Playwright tests hit the live production URL — they don't import app code.  
**Impact**: ~2–3 min wasted installing unused deps on every deploy.

**Fix**:
```bash
pip install pytest pytest-playwright pytest-html
playwright install chromium
```

**Acceptance criteria**:
- [x] `pip install -r requirements.txt` absent from `smoke-test` job
- [x] Only `pytest pytest-playwright pytest-html` installed in `smoke-test`
- [x] `smoke-test` job install step completes in under 60 seconds
- [x] Smoke tests still pass against production after the change

---

## Priority 9 — Broken: Full E2E report never created in `security-testing.yml`

**File**: `.github/workflows/security-testing.yml` — `e2e-tests` job  
**Problem**: `Run Full E2E Suite` step runs `pytest tests/e2e/ -v --html=e2e-report.html` — this flag is present, but the `Run Smoke Tests` step above it runs first without `--html`, meaning if smoke tests fail the full suite never runs and `e2e-report.html` is never written. More critically, the artifact upload expects both `smoke-report.html` and `e2e-report.html` — after Priority 7 removes the smoke step, only `e2e-report.html` should remain, and it must always be produced.  
**Impact**: E2E artifact is incomplete or missing on non-main branches and on smoke test failure.

**Fix**: After removing the smoke step (P7), ensure the full E2E step always runs on `main` and always writes `--html=e2e-report.html`. Update artifact path to only reference `e2e-report.html`.

**Acceptance criteria**:
- [x] Artifact upload path references only `e2e-report.html` (not `smoke-report.html`) after P7 removal
- [x] `e2e-report.html` is non-empty after a `main` push
- [x] Artifact `e2e-reports-<run_id>` contains `e2e-report.html` and renders correctly in browser

---

## Priority 10 — Broken: `accessibility-audit` startup uses bare `sleep 10` with no readiness check

**File**: `.github/workflows/security-testing.yml` — `accessibility-audit` job  
**Problem**: The `Start application for testing` step uses `sleep 10` with no subsequent health check. If the app takes longer than 10s to start (cold pip install, DB init), all three audit tools run against a non-responsive server and silently produce empty/error reports. The `e2e-tests` job in the same file correctly uses `curl -f http://localhost:8000/health || exit 1` — `accessibility-audit` does not.  
**Impact**: Audit tools may run against a dead server, producing misleading empty reports with no CI failure.

**Fix**: Replace `sleep 10` with a retry loop:
```bash
for i in {1..12}; do
  curl -sf http://localhost:8000/health && break
  echo "Waiting for app... ($i/12)"
  sleep 5
done
curl -f http://localhost:8000/health || (echo "❌ App failed to start" && exit 1)
```

**Acceptance criteria**:
- [x] `sleep 10` replaced with retry health check loop in `accessibility-audit` startup step
- [x] CI fails with a clear error message if app does not become healthy within 60s
- [x] Audit tools only run after health check passes
- [x] Consistent startup pattern with `e2e-tests` job in the same file

---

## Priority 11 — Race condition: Smoke tests run before Render cold start completes

**File**: `.github/workflows/deploy.yml` — `smoke-test` job  
**Problem**: The `deploy` job health-checks `${PROD_URL}/health` and exits 0 as soon as it responds. The `smoke-test` job starts immediately after. On Render free tier, the health endpoint can return 200 while the app is still initialising background tasks (DB pool warm-up, TextVerified pre-warm, etc.). Smoke tests that hit business endpoints within the first 5–10s after health check passes can fail with 503 or incomplete responses.  
**Impact**: Intermittent smoke test failures on every deploy that are not real regressions — causes false rollbacks.

**Fix**: Add a 15s stabilisation wait at the start of the `smoke-test` job, after `needs: deploy` resolves:
```bash
echo "⏳ Waiting 15s for Render to stabilise after health check..."
sleep 15
```

**Acceptance criteria**:
- [x] 15s stabilisation wait present at the start of the `Run smoke tests` step (or as a dedicated step before it)
- [x] Smoke tests do not trigger rollback on a clean deploy due to cold-start timing
- [x] Total smoke-test job time increase is ≤ 15s (acceptable overhead)
- [x] Pattern documented in a comment so future maintainers understand why the wait exists

---

## Summary

| # | File | Type | Impact |
|---|------|------|--------|
| # | File | Type | Impact | Status |
|---|------|------|--------|--------|
| 1 | `ci.yml` security job | Broken | Artifacts always empty | ✅ Done |
| 2 | `deploy.yml` smoke-test | Broken | Report never created | ✅ Done |
| 3 | `ci.yml` code-quality | Broken | 2–3 min wasted per run | ✅ Done |
| 4 | `security-testing.yml` accessibility-audit | Broken | Job has never run successfully | ✅ Done |
| 5 | `ci.yml` deployment-readiness | Broken | Secrets check always wrong | ✅ Done |
| 6 | `security-testing.yml` deployment-check | Overkill | Duplicate, echoes only | ✅ Done |
| 7 | `security-testing.yml` e2e-tests smoke | Overkill | Duplicate + SQLite false results | ✅ Done |
| 8 | `deploy.yml` smoke-test deps | Overkill | 2–3 min wasted per deploy | ✅ Done |
| 9 | `security-testing.yml` e2e-tests full suite | Broken | E2E report missing after P7 removal | ✅ Done |
| 10 | `security-testing.yml` accessibility-audit startup | Broken | Bare sleep — tools run against dead server | ✅ Done |
| 11 | `deploy.yml` smoke-test cold start | Race condition | False rollbacks on clean deploys | ✅ Done |

**Fix order**: 1 → 3 → 5 (ci.yml) → 2 → 8 → 11 (deploy.yml) → 4 → 6 → 7 → 9 → 10 (security-testing.yml)

**P7 + P2 dependency**: P7 removes the only working `smoke-report.html` source. P2 must be applied in the same commit or P7 will break smoke reporting entirely.

---

## Commit Log

| Commit | Date | Description |
|--------|------|-------------|
| `0e5a32f8` | 2026-03-11 | Fix all test collection errors, disable redundant CI workflows |
| `b36214e5` | 2026-03-11 | Fix TextVerified 429s on restart, pin urllib3/charset-normalizer |
| `34b618d8` | 2026-03-11 | Singleton TextVerifiedService + 60s admin balance cache |
| `bbaee925` | 2026-03-11 | Phase 6: remove duplicate security jobs, fix sleep 90, register pytest markers |
| `6f339d05` | 2026-03-11 | Repo cleanup: untrack certs, coverage.xml, archive stale docs |
| `f5b55baf` | 2026-03-11 | CI audit: rewrite CI_IMPROVEMENT_TASKS.md with 8 priority fixes |
| `cdd35e02` | 2026-03-11 | Fix all 11 CI issues: security reports, smoke HTML, code-quality deps, secrets check, accessibility startup, deployment-check removal, duplicate smoke, slim smoke deps, E2E report path, bare sleep, cold-start race |

## Open Infrastructure Items
1. 🔄 Provision Redis (Upstash free tier) → set `REDIS_URL` on Render
2. 🔄 Configure email service env vars on Render
3. 🔄 Raise coverage gate 36% → 40% → 45% → 50% incrementally
4. 🔄 Verify semgrep has zero ERROR findings in codebase

**CI Run URL**: https://github.com/Infradevandops/NAMASKAHsms/actions
