# CI/CD Improvement Tasks

**Goal**: Consolidate pipelines, enforce quality gates, automate rollback, and reach coverage targets  
**Status**: ✅ Complete  
**Secrets confirmed**: `GITLAB_TOKEN`, `PRODUCTION_URL`, `RENDER_DEPLOY_HOOK`, `RENDER_ROLLBACK_HOOK` ✅

---

## Phase 1 — Pipeline Consolidation
> Fix the redundant CI problem. Every push currently triggers 3 overlapping pipelines.

---

### Task 1.1 — Disable redundant CI workflows

**What**: Disable `ci-simple.yml` and `ci-strict.yml`. Keep `ci.yml` as the single active pipeline.

**How**:
- Add `if: false` at the top-level of `ci-simple.yml` and `ci-strict.yml`, or rename them to `.disabled`
- Alternatively delete them if they have no unique value

**Checks**:
- [x] Push to `develop` triggers exactly 1 CI pipeline run (not 3)
- [x] `ci.yml` is the only workflow running on push/PR

**Acceptance Criteria**:
- GitHub Actions tab shows a single CI workflow per push
- No duplicate job names in the run list
- `ci-simple.yml` and `ci-strict.yml` are either disabled or removed

---

### Task 1.2 — Promote blocking checks in `ci.yml`

**What**: `black`, `isort`, `bandit`, and `safety` are currently informational (`continue-on-error: true`). Promote them to blocking.

**How**: In `ci.yml`, remove `continue-on-error: true` from the `code-quality` and `security` jobs

**Checks**:
- [x] A PR with unformatted code fails the `code-quality` job
- [x] A PR with a known vulnerable dependency fails the `security` job
- [x] `bandit` high/medium findings block the pipeline

**Acceptance Criteria**:
- `ci.yml` `code-quality` job fails on `black`/`isort` violations
- `ci.yml` `security` job fails on `bandit -ll` findings and `safety` CVEs
- Existing codebase passes all newly blocking checks (fix any pre-existing violations first)

---

## Phase 2 — Deployment Hardening
> Wire up rollback, make health check blocking, and tighten the deploy gate.

---

### Task 2.1 — Wire `RENDER_ROLLBACK_HOOK` into `deploy.yml`

**What**: `RENDER_ROLLBACK_HOOK` secret exists but is unused. Add automatic rollback on deploy failure.

**How**: In `deploy.yml`, add a rollback step after the health check:
```yaml
- name: Rollback on failure
  if: failure()
  env:
    RENDER_ROLLBACK_HOOK: ${{ secrets.RENDER_ROLLBACK_HOOK }}
  run: |
    echo "⏪ Health check failed — triggering rollback..."
    curl -s -o /dev/null -w "%{http_code}" -X POST "$RENDER_ROLLBACK_HOOK"
```

**Checks**:
- [x] `RENDER_ROLLBACK_HOOK` is referenced in `deploy.yml`
- [x] Rollback step only runs `if: failure()`
- [ ] Manual test: simulate a failed health check and confirm rollback hook fires

**Acceptance Criteria**:
- A failed post-deploy health check automatically triggers the rollback hook
- Successful deploys do not trigger rollback
- Rollback step is visible in the GitHub Actions run log

---

### Task 2.2 — Make post-deploy health check blocking

**What**: The `/health` check in `deploy.yml` currently uses `exit 0` on failure — it never actually blocks. Make it fail the pipeline if health check fails after retries.

**How**: Replace the health check step with a retry loop that exits non-zero after N attempts:
```bash
for i in {1..5}; do
  curl -f -s "${PROD_URL}/health" && echo "✅ Healthy" && exit 0
  echo "Attempt $i failed, retrying in 15s..."
  sleep 15
done
echo "❌ Health check failed after 5 attempts"
exit 1
```

**Checks**:
- [x] Health check retries 5 times with 15s intervals
- [x] Pipeline fails if all retries exhausted
- [x] `PRODUCTION_URL` not set → step is skipped with a warning (not failed)

**Acceptance Criteria**:
- A broken production deployment fails the `deploy` job
- Rollback (Task 2.1) fires automatically as a result
- Healthy deployments pass within the retry window

---

### Task 2.3 — Gate `deploy.yml` on CI passing

**What**: `deploy.yml` currently fires independently on push to `main` with no dependency on CI passing. A broken push can deploy.

**How**: Change `deploy.yml` trigger to use `workflow_run` waiting on `ci.yml` to succeed:
```yaml
on:
  workflow_run:
    workflows: ["CI - Balanced Pipeline"]
    types: [completed]
    branches: [main]
```
Add condition: `if: github.event.workflow_run.conclusion == 'success'`

**Checks**:
- [x] A push to `main` that fails CI does not trigger deployment
- [x] A push to `main` that passes CI triggers deployment automatically
- [x] Manual `workflow_dispatch` still works as override

**Acceptance Criteria**:
- `deploy.yml` only runs after `ci.yml` completes successfully on `main`
- Failed CI runs show no corresponding deploy run in Actions tab
- Manual deploy override still available via `workflow_dispatch`

---

## Phase 3 — Coverage Ramp-Up
> Current coverage ~81% reported, but CI gates are set at 18–20%. Align gates with roadmap targets.

---

### Task 3.1 — Raise coverage threshold to 50%

**What**: CI coverage gate is 18% (`ci.yml`) — far below the Q1 2026 roadmap target of 50%. Raise it incrementally.

**How**: In `ci.yml`, update `--cov-fail-under=18` to `--cov-fail-under=50`

**Checks**:
- [x] `pytest` run locally passes with `--cov-fail-under=50`
- [x] CI pipeline passes with new threshold
- [ ] Coverage report shows ≥ 50% before merging this change

**Acceptance Criteria**:
- `ci.yml` fails any PR that drops coverage below 50%
- Codecov badge reflects the new baseline
- No existing tests removed to hit the number

---

### Task 3.2 — Enable integration tests in CI

**What**: `security-testing.yml` runs integration tests but `ci.yml` only runs `tests/` broadly. Confirm integration tests are included and not being skipped.

**How**:
- Check `pytest.ini` for any markers that skip integration tests by default
- Ensure `tests/integration/` runs in `ci.yml` (not just `security-testing.yml`)
- Add `DATABASE_URL` and `REDIS_URL` env vars are correctly set for integration suite

**Checks**:
- [x] `pytest tests/integration/` passes locally against test DB
- [x] Integration tests appear in CI run output (not skipped)
- [ ] No `@pytest.mark.skip` on integration tests without justification

**Acceptance Criteria**:
- CI run log shows integration test results (pass/fail counts)
- Integration tests contribute to the coverage report
- Any skipped integration tests have a documented reason

---

### Task 3.3 — Add coverage trend tracking

**What**: Coverage is reported to Codecov but there's no PR gate that prevents regressions.

**How**: In `ci.yml` codecov upload step, add:
```yaml
- uses: codecov/codecov-action@v4
  with:
    file: ./coverage.xml
    fail_ci_if_error: true
    threshold: 1  # fail if coverage drops by more than 1%
```

**Checks**:
- [x] A PR that drops coverage by >1% fails the CI
- [x] Codecov PR comment shows diff coverage
- [x] `fail_ci_if_error: true` is set

**Acceptance Criteria**:
- Coverage cannot regress without a deliberate override
- Codecov posts a coverage diff comment on every PR
- CI fails on Codecov upload errors

---

## Phase 4 — Security Hardening
> Promote security scanning from informational to enforced, and add secrets detection.

---

### Task 4.1 — Add Gitleaks secrets scanning

**What**: `tools/gitleaks.toml` exists but Gitleaks is not in any workflow. Add it to `ci.yml`.

**How**: Add a `secrets-scan` job to `ci.yml`:
```yaml
secrets-scan:
  name: Secrets Detection
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    - uses: gitleaks/gitleaks-action@v2
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Checks**:
- [x] Gitleaks runs on every push/PR
- [x] `tools/gitleaks.toml` config is picked up (add `--config tools/gitleaks.toml`)
- [ ] A test branch with a fake secret pattern triggers a failure
- [ ] `.env` and `.env.local` are in `.gitignore` (confirm not committed)

**Acceptance Criteria**:
- Gitleaks job appears in every CI run
- Any committed secret pattern blocks the PR
- `gitleaks.toml` rules are applied (not just defaults)

---

### Task 4.2 — Make `semgrep` blocking in `ci.yml`

**What**: `semgrep` only runs in `security-testing.yml` (non-blocking) and `ci-strict.yml` (disabled after Phase 1). Add it to `ci.yml` as blocking for high-severity findings.

**How**: Add to the `security` job in `ci.yml`:
```bash
pip install semgrep
semgrep --config=auto app/ --severity=ERROR --error
```

**Checks**:
- [x] `semgrep` runs in `ci.yml` security job
- [x] Only `ERROR` severity findings block (warnings are informational)
- [ ] Existing codebase has zero `ERROR`-level semgrep findings before enabling

**Acceptance Criteria**:
- `semgrep` ERROR findings block PRs
- WARNING findings are logged but don't fail the build
- Security report artifact is uploaded on every run

---

## Phase 5 — E2E & Accessibility
> Smoke tests and accessibility audits are only in `security-testing.yml`. Integrate smoke tests into the main deploy gate.

---

### Task 5.1 — Add smoke tests to `deploy.yml` post-deploy

**What**: After a successful deploy, run a minimal smoke test suite against production to confirm critical paths work.

**How**: Add a `smoke-test` job to `deploy.yml` after the health check:
```yaml
smoke-test:
  needs: deploy
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - run: pip install pytest playwright && playwright install chromium
    - name: Run smoke tests against production
      env:
        BASE_URL: ${{ secrets.PRODUCTION_URL }}
      run: pytest tests/e2e/ -m smoke -v
```

**Checks**:
- [x] Smoke tests run against `PRODUCTION_URL` (not localhost)
- [x] Smoke tests are tagged with `@pytest.mark.smoke`
- [x] Failure triggers rollback (via Task 2.1)
- [ ] Smoke suite completes in < 5 minutes

**Acceptance Criteria**:
- Every production deploy is followed by an automated smoke test run
- A failing smoke test triggers the rollback hook
- Smoke test results are visible in the deploy workflow run

---

### Task 5.2 — Schedule weekly accessibility audit

**What**: Accessibility audit in `security-testing.yml` only runs on push. Add a scheduled weekly run against production.

**How**: Add `schedule` trigger to `security-testing.yml`:
```yaml
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday 9am UTC
  push:
    branches: [main, develop]
```

**Checks**:
- [x] Workflow runs automatically on Monday mornings
- [x] Audit runs against `PRODUCTION_URL` when triggered by schedule
- [x] Reports are uploaded as artifacts with date-stamped names

**Acceptance Criteria**:
- Accessibility audit runs weekly without manual trigger
- Lighthouse, axe, and pa11y reports are retained as artifacts
- Any new accessibility regressions are visible in the weekly report

---

## Summary

| Phase | Tasks | Focus | Target |
|-------|-------|-------|--------|
| 1 | 1.1, 1.2 | Pipeline consolidation | Single CI, all checks blocking |
| 2 | 2.1, 2.2, 2.3 | Deploy hardening | Rollback, health gate, CI dependency |
| 3 | 3.1, 3.2, 3.3 | Coverage | 50% gate, integration tests, regression guard |
| 4 | 4.1, 4.2 | Security | Gitleaks, semgrep blocking |
| 5 | 5.1, 5.2 | E2E & Accessibility | Post-deploy smoke, weekly a11y audit |

**Recommended order**: Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
