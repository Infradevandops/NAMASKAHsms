# CI/CD Workflows Reference

**Location**: `.github/workflows/`  
**Total Workflows**: 6  
**Last Updated**: 2026

---

## Workflows Overview

| File | Name | Trigger | Purpose |
|------|------|---------|---------|
| `ci.yml` | Balanced Pipeline | push/PR → `main`, `develop` | Primary CI — balanced blocking/informational checks |
| `ci-simple.yml` | Simplified Pipeline | push/PR → `main`, `develop` | Lenient CI — all checks non-blocking |
| `ci-strict.yml` | Enhanced Pipeline | push/PR → `main`, `develop` | Strict CI — all checks blocking |
| `deploy.yml` | Production Deployment | push → `main`, manual | Triggers Render deploy + health check |
| `security-testing.yml` | Security & Testing | push → `main`/`develop`, PR → `main` | Full security, E2E, and accessibility suite |
| `sync-to-gitlab.yml` | GitLab Mirror | push → `main`/`develop`, manual | Mirrors repo to GitLab backup |

> ⚠️ **Known Issue**: `ci.yml`, `ci-simple.yml`, and `ci-strict.yml` share identical triggers. Every push runs all three in parallel with overlapping checks. Only one should be active at a time.

---

## 1. `ci.yml` — Balanced Pipeline

**Triggers**: push/PR to `main`, `develop`

| Job | Tool / Check | Blocking |
|-----|-------------|----------|
| `code-quality` | `flake8` — critical syntax errors (E9, F63, F7, F82) | ✅ Yes |
| `code-quality` | `black` formatting, `isort` import order | ❌ No |
| `security` | `bandit` SAST scan | ❌ No |
| `security` | `safety` dependency CVE check | ❌ No |
| `tests` | `pytest` with PostgreSQL 15 + Redis 7 | ✅ Yes |
| `tests` | Coverage upload to Codecov; fails if **< 18%** | ✅ Yes |
| `deployment-readiness` | `render.yaml`, `main.py`, `requirements.txt` exist | ✅ Yes |
| `deployment-readiness` | `RENDER_DEPLOY_HOOK`, `PRODUCTION_URL` secrets present | ❌ No |

`deployment-readiness` runs on `main` only, needs `code-quality` + `tests`.

---

## 2. `ci-simple.yml` — Simplified Pipeline

**Triggers**: push/PR to `main`, `develop`

| Job | Tool / Check | Blocking |
|-----|-------------|----------|
| `basic-checks` | `flake8` syntax | ❌ No |
| `basic-checks` | `pytest` with PostgreSQL + Redis | ❌ No |
| `basic-checks` | `bandit` SAST scan | ❌ No |
| `deployment-readiness` | `render.yaml`, `main.py`, `requirements.txt` exist | ❌ No |
| `deployment-readiness` | `RENDER_DEPLOY_HOOK` secret present | ❌ No |

All steps use `continue-on-error: true`. `deployment-readiness` runs on `main` only.

---

## 3. `ci-strict.yml` — Enhanced Pipeline

**Triggers**: push/PR to `main`, `develop`

| Job | Tool / Check | Blocking |
|-----|-------------|----------|
| `lint-and-format` | `flake8` critical syntax | ✅ Yes |
| `lint-and-format` | `black` formatting | ✅ Yes |
| `lint-and-format` | `isort` import order | ✅ Yes |
| `lint-and-format` | `mypy` type checking | ✅ Yes |
| `lint-and-format` | `pylint` score **≥ 7.0** | ✅ Yes |
| `security-scan` | `bandit` SAST (JSON artifact) | ✅ Yes |
| `security-scan` | `safety` CVE check (JSON artifact) | ✅ Yes |
| `security-scan` | `semgrep` SAST (JSON artifact) | ✅ Yes |
| `test` | `pytest` with PostgreSQL + Redis | ✅ Yes |
| `test` | Codecov upload (`fail_ci_if_error: true`); fails if **< 20%** | ✅ Yes |
| `deployment-readiness` | File existence + secrets validation | ✅ Yes |

`deployment-readiness` runs on `main` only, needs all 3 prior jobs.

---

## 4. `deploy.yml` — Production Deployment

**Triggers**: push to `main`, manual `workflow_dispatch` (with optional `force_deploy` input)

| Job | Step | Blocking |
|-----|------|----------|
| `deploy` | Validate `render.yaml`, `main.py`, `requirements.txt` | ✅ Yes |
| `deploy` | Trigger Render deploy hook via `curl` POST | ✅ Yes |
| `deploy` | Wait 60s for deployment to start | — |
| `deploy` | `GET /health` health check on `PRODUCTION_URL` | ❌ No |
| `deploy` | Report final deployment status | — |

Requires secret: `RENDER_DEPLOY_HOOK`. Optional: `PRODUCTION_URL`.

---

## 5. `security-testing.yml` — Security & Testing Pipeline

**Triggers**: push to `main`/`develop`; PR to `main`

| Job | Tool / Check | Blocking |
|-----|-------------|----------|
| `security-scan` | `bandit` SAST (JSON artifact) | ❌ No |
| `security-scan` | `safety` CVE check (JSON artifact) | ❌ No |
| `security-scan` | `semgrep` SAST (JSON artifact) | ❌ No |
| `test-suite` | `pytest tests/unit/` with PostgreSQL + Redis | ✅ Yes |
| `test-suite` | `pytest tests/integration/` | ✅ Yes |
| `test-suite` | Codecov upload | — |
| `e2e-tests` | Playwright Chromium install | — |
| `e2e-tests` | Smoke tests (`-m smoke`) — always | ✅ Yes |
| `e2e-tests` | Full E2E suite — `main` branch only | ✅ Yes |
| `e2e-tests` | HTML reports uploaded as artifacts | — |
| `accessibility-audit` | `axe-core` scan | ❌ No |
| `accessibility-audit` | `pa11y` accessibility test | ❌ No |
| `accessibility-audit` | Lighthouse accessibility audit | ❌ No |
| `accessibility-audit` | JSON reports uploaded as artifacts | — |
| `deployment-check` | Readiness gate (needs `security-scan`, `test-suite`, `e2e-tests`) | — |

`deployment-check` runs on `main` only.

---

## 6. `sync-to-gitlab.yml` — GitLab Mirror

**Triggers**: push to `main`/`develop`, manual `workflow_dispatch`

| Job | Step | Blocking |
|-----|------|----------|
| `sync` | Full history checkout (`fetch-depth: 0`) | — |
| `sync` | Push branch to GitLab via `GITLAB_TOKEN` | ✅ Yes |
| `sync` | Gracefully skip if `GITLAB_TOKEN` not set | — |

Requires secret: `GITLAB_TOKEN`. Target: `gitlab.com/oghenesuvwe-group/NAMASKAHsms.git`

---

## All Unique Checks — Master Reference

| Category | Tools | Workflows |
|----------|-------|-----------|
| Syntax | `flake8` (E9, F63, F7, F82) | ci, ci-simple, ci-strict |
| Formatting | `black`, `isort` | ci, ci-strict |
| Type checking | `mypy` | ci-strict |
| Linting | `pylint` (≥ 7.0) | ci-strict |
| SAST | `bandit`, `semgrep` | ci, ci-strict, security-testing |
| Dependency CVEs | `safety` | ci, ci-strict, security-testing |
| Unit tests | `pytest tests/unit/` | security-testing |
| All tests | `pytest tests/` (coverage ≥ 18–20%) | ci, ci-simple, ci-strict |
| Integration tests | `pytest tests/integration/` | security-testing |
| E2E tests | `pytest` + Playwright Chromium | security-testing |
| Accessibility | `axe-core`, `pa11y`, Lighthouse | security-testing |
| Deployment readiness | File existence + secrets check | ci, ci-simple, ci-strict, deploy |
| Health check | `curl /health` post-deploy | deploy |
| Repo mirroring | Git push to GitLab | sync-to-gitlab |

---

## Required Secrets

| Secret | Used By | Purpose |
|--------|---------|---------|
| `RENDER_DEPLOY_HOOK` | `deploy.yml`, `ci.yml`, `ci-simple.yml`, `ci-strict.yml` | Trigger Render deployment |
| `PRODUCTION_URL` | `deploy.yml`, `ci.yml`, `ci-strict.yml` | Post-deploy health check |
| `GITLAB_TOKEN` | `sync-to-gitlab.yml` | GitLab mirror authentication |
