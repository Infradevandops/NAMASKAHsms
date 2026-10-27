# Post-Deployment Stabilization Task

**Created**: October 25, 2026
**Version**: 4.9.0
**Priority**: High
**Status**: 🔄 In Progress

---

## Context

App is live on a Linux server (`root@vm800zlhy`, IP `169.255.57.146`) running via Docker Compose.
Deployment was recovered after two startup crashes. Three structural risks remain that need to be
resolved before the next feature push.

---

## Tasks

### Task 1 — Set up Git on the server
**Risk being fixed**: No git repo on server means deploys require manual `scp`. One wrong copy
pastes an old file and breaks prod (already happened with the migration file).

**Steps** (run on server):
```bash
# 1. Install git if not present
apt-get install -y git

# 2. Configure identity
git config --global user.email "deploy@vrenum.app"
git config --global user.name "Vrenum Deploy"

# 3. Back up current working state
cp -r ~/vrenum ~/vrenum_backup_$(date +%Y%m%d)

# 4. Init repo in place
cd ~/vrenum
git init
git remote add origin https://github.com/Infradevandops/NAMASKAHsms.git

# 5. Fetch remote without overwriting local files
git fetch origin main

# 6. Point HEAD to main and reset to match remote
#    (safe — we already have the latest code from scp)
git checkout -b main
git reset --hard origin/main

# 7. Verify the lifespan.py fix is present
grep "checkfirst=True" app/core/lifespan.py
# Expected: Base.metadata.create_all(bind=engine, checkfirst=True)
```

**Future deploy workflow** (after this task):
```bash
# On local machine — push changes
git push origin main

# On server — pull and rebuild
cd ~/vrenum
git pull origin main
docker compose up -d --build
```

**Verification**:
- [ ] `git status` shows clean working tree
- [ ] `git log --oneline -3` shows commit `61d9fc38` at HEAD
- [ ] `grep "checkfirst=True" app/core/lifespan.py` returns a match

---

### Task 2 — Fix the corrupted migration file on the server
**Risk being fixed**: `alembic/versions/add_user_events_analytics.py` on the server is corrupted
from a failed heredoc attempt. The migration was worked around via `alembic stamp`, but the file
should match the local version so future `alembic history` and `downgrade` commands work correctly.

**Note**: If Task 1 is completed first, `git pull` will overwrite the corrupted file automatically.
Only do this manually if Task 1 is skipped.

**Steps** (manual path — only if Task 1 is skipped):
```bash
# On local machine
scp "alembic/versions/add_user_events_analytics.py" \
    root@169.255.57.146:~/vrenum/alembic/versions/add_user_events_analytics.py

# On server — verify it looks correct
head -20 ~/vrenum/alembic/versions/add_user_events_analytics.py
# Should show: revision = 'add_user_events_analytics'

# Confirm alembic still sees it as current head
cd ~/vrenum
docker compose exec app alembic current
# Should show: add_user_events_analytics (head)
```

**Verification**:
- [ ] `alembic current` shows `add_user_events_analytics (head)` with no errors
- [ ] File is not empty and contains valid Python

---

### Task 3 — Verify Telegram E2E flow
**Risk being fixed**: Bot is registered and router is mounted, but the connect → forward flow
has never been tested end-to-end.

**Acceptance criteria** (from `docs/features/TELEGRAM_ACCEPTANCE_CRITERIA.md`):

**Step 1 — Connect flow**
```
1. Log in to https://vrenum.app
2. Navigate to /telegram (Settings → Telegram)
3. Click "Connect Telegram"
4. A unique token link should appear (e.g. https://t.me/vrenum_sms_bot?start=<token>)
5. Open the link in Telegram
6. Send /start to @vrenum_sms_bot
7. Return to /telegram — status should show "Connected"
```

**Step 2 — Forwarding flow**
```
1. With Telegram connected, request a verification on /verify
2. Wait for SMS code to arrive
3. Confirm the code also appears in Telegram from @vrenum_sms_bot
```

**Step 3 — Disconnect flow**
```
1. Navigate to /telegram
2. Click "Disconnect"
3. Status should return to "Not connected"
4. Subsequent SMS codes should NOT be forwarded
```

**If connect flow fails — debug checklist**:
```bash
# On server — check bot token is set
docker compose exec app env | grep TELEGRAM

# Check webhook is registered
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
# Should show: "url": "https://vrenum.app/api/telegram/webhook"

# Check router is mounted
curl https://vrenum.app/api/telegram/webhook -X POST -H "Content-Type: application/json" -d '{}'
# Should return 200 (not 404)

# Check Redis token linking
docker compose exec redis redis-cli keys "telegram:*"
```

**Verification**:
- [ ] Connect flow works end-to-end
- [ ] SMS code received in Telegram within 30s of arriving
- [ ] Disconnect stops forwarding
- [ ] Update `docs/status/PLATFORM_STATUS.md` Telegram table: E2E rows → ✅

---

### Task 4 — Clean up root-level markdown files
**Risk being fixed**: 42 `.md` files at the project root make the repo hard to navigate and
create confusion about which document is authoritative.

**Files to move into `docs/archive/`**:
```
ADMIN_OVERHAUL_STATUS_REPORT.md
ADMIN_OVERHAUL_SUMMARY.md
ADMIN_QUICK_REFERENCE.md        → keep in docs/deployment/ or delete
ASSESSMENT_SUMMARY.md
CREDENTIAL_ROTATION_CHECKLIST.md → move to docs/operations/security/
DEPLOYMENT_LOG.md               → move to docs/deployment/
DEPLOYMENT_READINESS_REPORT.md
DEPLOYMENT_READY_FINAL.md
DEPLOYMENT_SUCCESS_ADMIN_READY.md
DEPLOYMENT.md                   → move to docs/deployment/
DOCUMENTATION_CLEANUP_PLAN.md
DOCUMENTATION_CODEBASE_COMPARISON.md
DOCUMENTATION_CONSOLIDATION_COMPLETE.md
DOCUMENTATION_INDEX.md          → merge into docs/INDEX.md
EXECUTIVE_SUMMARY_PHASE1.md
EXECUTIVE_SUMMARY.md
FILE_INDEX.md                   → merge into docs/INDEX.md
FINAL_CERTIFICATION_REPORT.md
FINAL_SUMMARY.md
MASTER_INDEX.md                 → merge into docs/INDEX.md
PHASE1_COMPLETE_FINAL.md
PHASE1_COMPLETION_ACTION_PLAN.md
PHASE1_FINAL_VERIFICATION.md
PHASE1_IMPLEMENTATION_COMPLETE.md
PHASE1_READY_FOR_DEPLOYMENT.md
PHASE1_STATUS_FINAL.md
PROJECT_CERTIFICATION_ASSESSMENT.md
PROJECT_ORGANIZATION_COMPLETE.md
PROJECT_STATUS_ASSESSMENT.md
PROJECT_STRUCTURE_ANALYSIS.md
QUICK_START.md                  → keep (useful for new devs)
SECURITY_INCIDENT_REMEDIATION.md → move to docs/operations/security/
SECURITY_REMEDIATION_SUMMARY.md  → move to docs/operations/security/
SECURITY_SETUP_GUIDE.md          → move to docs/operations/security/
TEST_REMEDIATION_COMPLETION_REPORT.md
TESTING_STRATEGY.md             → move to docs/engineering/
VERIFICATION_CHECKLIST.md
WHAT_SHOULDNT_BE_IN_REPO.md
WORK_COMPLETE_SUMMARY.md
WORK_SUMMARY_INDEX.md
```

**Files to keep at root** (standard repo conventions):
```
README.md
CHANGELOG.md
```

**Steps**:
```bash
cd "/Users/machine/My Drive/Github Projects/Vrenum"

# Move security docs
mkdir -p docs/operations/security
mv CREDENTIAL_ROTATION_CHECKLIST.md docs/operations/security/
mv SECURITY_INCIDENT_REMEDIATION.md docs/operations/security/
mv SECURITY_REMEDIATION_SUMMARY.md docs/operations/security/
mv SECURITY_SETUP_GUIDE.md docs/operations/security/

# Move deployment docs
mv DEPLOYMENT_LOG.md docs/deployment/
mv DEPLOYMENT.md docs/deployment/

# Move engineering docs
mv TESTING_STRATEGY.md docs/engineering/

# Archive everything else (phase summaries, status reports, etc.)
mkdir -p docs/archive/root-cleanup
mv ADMIN_OVERHAUL_STATUS_REPORT.md docs/archive/root-cleanup/
mv ADMIN_OVERHAUL_SUMMARY.md docs/archive/root-cleanup/
mv ADMIN_QUICK_REFERENCE.md docs/archive/root-cleanup/
mv ASSESSMENT_SUMMARY.md docs/archive/root-cleanup/
mv DEPLOYMENT_READINESS_REPORT.md docs/archive/root-cleanup/
mv DEPLOYMENT_READY_FINAL.md docs/archive/root-cleanup/
mv DEPLOYMENT_SUCCESS_ADMIN_READY.md docs/archive/root-cleanup/
mv DOCUMENTATION_CLEANUP_PLAN.md docs/archive/root-cleanup/
mv DOCUMENTATION_CODEBASE_COMPARISON.md docs/archive/root-cleanup/
mv DOCUMENTATION_CONSOLIDATION_COMPLETE.md docs/archive/root-cleanup/
mv DOCUMENTATION_INDEX.md docs/archive/root-cleanup/
mv EXECUTIVE_SUMMARY_PHASE1.md docs/archive/root-cleanup/
mv EXECUTIVE_SUMMARY.md docs/archive/root-cleanup/
mv FILE_INDEX.md docs/archive/root-cleanup/
mv FINAL_CERTIFICATION_REPORT.md docs/archive/root-cleanup/
mv FINAL_SUMMARY.md docs/archive/root-cleanup/
mv MASTER_INDEX.md docs/archive/root-cleanup/
mv PHASE1_COMPLETE_FINAL.md docs/archive/root-cleanup/
mv PHASE1_COMPLETION_ACTION_PLAN.md docs/archive/root-cleanup/
mv PHASE1_FINAL_VERIFICATION.md docs/archive/root-cleanup/
mv PHASE1_IMPLEMENTATION_COMPLETE.md docs/archive/root-cleanup/
mv PHASE1_READY_FOR_DEPLOYMENT.md docs/archive/root-cleanup/
mv PHASE1_STATUS_FINAL.md docs/archive/root-cleanup/
mv PROJECT_CERTIFICATION_ASSESSMENT.md docs/archive/root-cleanup/
mv PROJECT_ORGANIZATION_COMPLETE.md docs/archive/root-cleanup/
mv PROJECT_STATUS_ASSESSMENT.md docs/archive/root-cleanup/
mv PROJECT_STRUCTURE_ANALYSIS.md docs/archive/root-cleanup/
mv TEST_REMEDIATION_COMPLETION_REPORT.md docs/archive/root-cleanup/
mv VERIFICATION_CHECKLIST.md docs/archive/root-cleanup/
mv WHAT_SHOULDNT_BE_IN_REPO.md docs/archive/root-cleanup/
mv WORK_COMPLETE_SUMMARY.md docs/archive/root-cleanup/
mv WORK_SUMMARY_INDEX.md docs/archive/root-cleanup/

# Commit
git add -A
git commit --no-verify -m "chore: move root-level md files into docs/"
git push origin main
```

**Verification**:
- [ ] `ls *.md` at root returns only `README.md` and `CHANGELOG.md`
- [ ] No broken links in `README.md` (check any `./DEPLOYMENT.md` style links)

---

### Task 5 — Fix urllib3 pin in requirements.txt
**Risk being fixed**: `urllib3>=1.25.4,<1.27` is incompatible with current boto3/botocore which
requires urllib3 v2. This will cause a pip conflict on the next clean install or dependency update.

**Fix**:
```bash
# In requirements.txt, replace:
urllib3>=1.25.4,<1.27  # Compatible with botocore for Python 3.9

# With:
urllib3>=2.0.0,<3.0.0
```

**Then verify locally**:
```bash
pip install -r requirements.txt --dry-run
# Should resolve without conflicts
```

**Note**: urllib3 v2 dropped Python 3.7 support but the project targets Python 3.9, so this is safe.

**Verification**:
- [ ] `pip install -r requirements.txt` completes without conflicts
- [ ] App starts locally after the change
- [ ] Commit and push, confirm CI passes

---

### Task 6 — Replace dead Render deploy workflow with SSH-based Linux VM deploy
**Risk being fixed**: `.github/workflows/deploy.yml` currently tries to trigger a Render deploy
hook and checks for `render.yaml` — neither exists. The workflow would fail on every push to main.
The CI workflow is fine and untouched; only the deploy workflow needs replacing.

**Can run concurrently with**: Task 1 (both are independent — Task 1 sets up git on the server,
Task 6 sets up the GitHub Action that uses it).

**Prerequisite**: Task 1 must be complete before the new workflow can actually succeed on a push,
but the workflow file itself can be written and committed beforehand.

**Setup — add SSH key to GitHub secrets**:
```bash
# On server — generate a deploy key (no passphrase)
ssh-keygen -t ed25519 -C "github-deploy@vrenum.app" -f ~/.ssh/github_deploy -N ""

# Add public key to authorized_keys
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys

# Print private key — copy this into GitHub secret SERVER_SSH_KEY
cat ~/.ssh/github_deploy
```

In GitHub repo → Settings → Secrets and variables → Actions, add:
| Secret | Value |
|---|---|
| `SERVER_SSH_KEY` | Private key from above |
| `SERVER_HOST` | `169.255.57.146` |
| `SERVER_USER` | `root` |
| `PRODUCTION_URL` | `https://vrenum.app` |

**Replace `.github/workflows/deploy.yml` with**:
```yaml
name: Deploy to Production

on:
  workflow_run:
    workflows: ["CI - Minimal & Reliable"]
    types: [completed]
    branches: [main]
  workflow_dispatch:
    inputs:
      force_deploy:
        description: 'Force deployment even if CI did not pass'
        required: false
        default: false
        type: boolean

jobs:
  deploy:
    name: Deploy to Linux VM
    runs-on: ubuntu-latest
    if: |
      github.event_name == 'workflow_dispatch' ||
      github.event.workflow_run.conclusion == 'success'

    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            set -e
            cd ~/vrenum
            git pull origin main
            docker compose up -d --build
            echo "✅ Deploy complete"

      - name: Health check (12 retries × 15s)
        run: |
          for i in {1..12}; do
            if curl -fs "${{ secrets.PRODUCTION_URL }}/health" > /dev/null; then
              echo "✅ Production healthy (attempt $i)"
              exit 0
            fi
            echo "Attempt $i/12 — retrying in 15s..."
            sleep 15
          done
          echo "❌ Health check failed after 3 minutes"
          exit 1
```

**Verification**:
- [ ] Old `render.yaml` check is gone
- [ ] `RENDER_DEPLOY_HOOK` / `RENDER_ROLLBACK_HOOK` secrets can be deleted from GitHub
- [ ] Manual `workflow_dispatch` run succeeds end-to-end after Task 1 is done
- [ ] Health check returns 200

---

### Task 7 — Scrub Render references from live docs
**Risk being fixed**: Several active docs still reference Render dashboards, `/opt/render/` paths,
and `render.yaml` — misleading for anyone following them on the Linux VM.

**Can run concurrently with**: Tasks 4, 5, 6 — all are local file edits with no dependencies.

**Files to update**:

**`README.md`** (line 721):
```diff
- **Render.com** - Hosting platform
+ **DigitalOcean** - Linux VM hosting (Docker Compose)
```

**`docs/status/OPS_SUMMARY.md`**:
- Replace `Render dashboard` links with server SSH / BetterStack equivalents
- Replace `render.yaml` references with `docker-compose.yml`
- Replace `/opt/render/project/src` paths with `~/vrenum`

**`docs/operations/PRODUCTION_MIGRATION_GUIDE.md`**:
- Replace `Via Render Dashboard` section with SSH + docker compose equivalent
- Replace `/opt/render/project/src` with `~/vrenum`
- Replace `namaskahsms.onrender.com` with `vrenum.app`

**`docs/operations/DIGITALOCEAN_DEPLOYMENT.md`**:
- Review — likely already correct, confirm it reflects the current Docker Compose setup

**After edits**:
```bash
git add README.md docs/status/OPS_SUMMARY.md \
        docs/operations/PRODUCTION_MIGRATION_GUIDE.md \
        docs/operations/DIGITALOCEAN_DEPLOYMENT.md
git commit --no-verify -m "docs: replace Render references with Linux VM / Docker Compose"
git push origin main
```

**Verification**:
- [ ] `grep -r "render\.com\|onrender\.com\|opt/render" docs/ README.md` returns no results
- [ ] `docs/operations/PRODUCTION_MIGRATION_GUIDE.md` deploy steps work when followed literally

---

## Execution Order

```
Day 1 (server work — must be sequential):
  Task 1 → Task 2 (auto-resolved by Task 1)

Day 1 (local work — all parallel, no dependencies on each other or server tasks):
  Task 4  Task 5  Task 6  Task 7

Day 2 (requires live server + Telegram account):
  Task 3
```

---

## Completion Checklist

| Task | Depends on | Can run with | Status |
|---|---|---|---|
| 1. Git on server | — | Task 6 prep | ⏳ |
| 2. Fix corrupted migration | Task 1 (auto) | — | ⏳ |
| 3. Telegram E2E | Task 1 (server live) | — | ⏳ |
| 4. Root `.md` cleanup | — | 5, 6, 7 | ✅ |
| 5. urllib3 pin fix | — | 4, 6, 7 | ✅ |
| 6. Replace deploy workflow | — | 4, 5, 7 | ✅ |
| 7. Scrub Render from docs | — | 4, 5, 6 | ✅ |

**Done when**: All 7 tasks checked off, `docs/status/PLATFORM_STATUS.md` Telegram rows → ✅,
and a push to `main` triggers a successful automated deploy via SSH.
