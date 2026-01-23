# Nerava Monorepo Cleanup - Cursor Implementation Prompt

**Date:** 2026-01-23
**Source:** CLEANUP_REPORT.md
**Repo Root:** `/Users/jameskirk/Desktop/Nerava`

---

## 1. Goal

Make the Nerava monorepo **demo/launch-ready** by:
1. Removing all tracked secrets, private keys, and sensitive files from git
2. Consolidating duplicate directories to single canonical versions
3. Removing committed build artifacts and recovering ~3GB disk space
4. Organizing documentation into a clean, navigable structure
5. Ensuring CI/CD and local dev continue to work after cleanup

---

## 2. Non-Goals

- **No architecture changes** - This is cleanup only, not a redesign
- **No runtime behavior changes** - Only changes required to remove hardcoded secrets
- **No new features or refactoring** beyond what's explicitly listed
- **No deletion of production-critical code** - Only duplicates and artifacts

---

## 3. Assumptions

- The `backend/` directory is the canonical backend (not `nerava-backend-v9/` or `nerava-backend-v9 2/`)
- The `apps/` directory contains the canonical frontend apps (admin, driver, landing, merchant)
- GitHub Actions workflows in `.github/workflows/` are the source of truth for CI/CD
- Any committed secrets are **already compromised** and must be rotated
- User has ability to update App Runner environment variables and GitHub Secrets

---

## 4. Phase Plan

Execute phases **in order**. Do not skip phases. Commit after each phase.

---

### Phase P0: Critical Security Remediation (MUST BE FIRST)

**Objective:** Remove all secrets from git tracking and prevent re-commit.

#### P0.1 - Create Backup Directory

```bash
cd /Users/jameskirk/Desktop/Nerava
mkdir -p backups/.secrets-backup-$(date +%Y%m%d)
```

#### P0.2 - Backup and Remove Private Keys

```bash
# Backup keys before removal (DO NOT COMMIT backups/)
cp nerava.key backups/.secrets-backup-$(date +%Y%m%d)/ 2>/dev/null || true
cp nerava-pass.key backups/.secrets-backup-$(date +%Y%m%d)/ 2>/dev/null || true
cp cookies.txt backups/.secrets-backup-$(date +%Y%m%d)/ 2>/dev/null || true
cp nerava.csr backups/.secrets-backup-$(date +%Y%m%d)/ 2>/dev/null || true
cp nerava-pass.csr backups/.secrets-backup-$(date +%Y%m%d)/ 2>/dev/null || true
cp pass.cer backups/.secrets-backup-$(date +%Y%m%d)/ 2>/dev/null || true

# Remove from git tracking (keeps local copy until explicit delete)
git rm --cached nerava.key 2>/dev/null || true
git rm --cached nerava-pass.key 2>/dev/null || true
git rm --cached cookies.txt 2>/dev/null || true
git rm --cached nerava.csr 2>/dev/null || true
git rm --cached nerava-pass.csr 2>/dev/null || true
git rm --cached pass.cer 2>/dev/null || true

# Delete local copies (already backed up)
rm -f nerava.key nerava-pass.key cookies.txt nerava.csr nerava-pass.csr pass.cer
```

#### P0.3 - Backup and Remove .env Files

```bash
# Backend .env files
cp backend/.env backups/.secrets-backup-$(date +%Y%m%d)/backend-.env 2>/dev/null || true
cp backend/.env.backup backups/.secrets-backup-$(date +%Y%m%d)/backend-.env.backup 2>/dev/null || true
cp backend/.env.bak backups/.secrets-backup-$(date +%Y%m%d)/backend-.env.bak 2>/dev/null || true

git rm --cached backend/.env 2>/dev/null || true
git rm --cached backend/.env.backup 2>/dev/null || true
git rm --cached backend/.env.bak 2>/dev/null || true
rm -f backend/.env backend/.env.backup backend/.env.bak

# nerava-backend-v9 2 .env files (will be deleted entirely in P1)
cp "nerava-backend-v9 2/.env" "backups/.secrets-backup-$(date +%Y%m%d)/nerava-backend-v9-2-.env" 2>/dev/null || true
cp "nerava-backend-v9 2/.env.backup" "backups/.secrets-backup-$(date +%Y%m%d)/nerava-backend-v9-2-.env.backup" 2>/dev/null || true
cp "nerava-backend-v9 2/.env.bak" "backups/.secrets-backup-$(date +%Y%m%d)/nerava-backend-v9-2-.env.bak" 2>/dev/null || true

# nerava-app-driver .env files (will be deleted entirely in P1)
cp nerava-app-driver/.env "backups/.secrets-backup-$(date +%Y%m%d)/nerava-app-driver-.env" 2>/dev/null || true
cp nerava-app-driver/.env.local "backups/.secrets-backup-$(date +%Y%m%d)/nerava-app-driver-.env.local" 2>/dev/null || true
cp nerava-app-driver/.env.production "backups/.secrets-backup-$(date +%Y%m%d)/nerava-app-driver-.env.production" 2>/dev/null || true
```

#### P0.4 - Update Root .gitignore

Add/verify these entries in `/.gitignore`:

```gitignore
# === Security: Never commit these ===
*.key
*.p12
*.pem
*.cer
*.csr
cookies.txt
.env
.env.*
!.env.example
*.backup
*.bak

# === Backup directory (local only) ===
backups/

# === Build artifacts ===
node_modules/
dist/
build/
.next/
out/
.vite/
.cache/
.pytest_cache/
__pycache__/
*.pyc
.venv/
venv/
.coverage
htmlcov/
coverage/
playwright-report/
test-results/

# === IDE/OS ===
.DS_Store
*.swp
*.swo
.idea/
*.iml

# === Archives (don't commit zips) ===
*.zip
*.tar.gz
*.tgz

# === Database files ===
*.db
*.sqlite
*.sqlite3
```

#### P0.5 - Create/Verify .env.example Files

**For `/backend/.env.example`** (create if missing or update):

```env
# Nerava Backend Environment Variables
# Copy to .env and fill in real values

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/nerava

# Authentication
JWT_SECRET_KEY=your-jwt-secret-here-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
S3_BUCKET_NAME=nerava-assets

# Twilio
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890

# SendGrid
SENDGRID_API_KEY=your-sendgrid-key
SENDGRID_FROM_EMAIL=noreply@nerava.com

# Square
SQUARE_ACCESS_TOKEN=your-square-token
SQUARE_ENVIRONMENT=sandbox
SQUARE_APPLICATION_ID=your-square-app-id
SQUARE_LOCATION_ID=your-square-location

# Google
GOOGLE_PLACES_API_KEY=your-google-places-key

# App Config
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**For `/apps/driver/.env.example`** (create if missing):

```env
# Driver App Environment Variables
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_PLACES_API_KEY=your-google-places-key
VITE_ENVIRONMENT=development
```

**For `/apps/admin/.env.example`** (create if missing):

```env
# Admin Portal Environment Variables
VITE_API_BASE_URL=http://localhost:8000
VITE_ENVIRONMENT=development
```

**For `/apps/merchant/.env.example`** (create if missing):

```env
# Merchant Portal Environment Variables
VITE_API_BASE_URL=http://localhost:8000
VITE_SQUARE_APPLICATION_ID=your-square-app-id
VITE_ENVIRONMENT=development
```

**For `/apps/landing/.env.example`** (create if missing):

```env
# Landing Page Environment Variables
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development
```

#### P0.6 - Create Security Documentation

Create `/docs/security/secrets.md`:

```markdown
# Nerava Secrets Management

## Where Secrets Live

### Production
- **App Runner:** Environment variables configured in AWS App Runner console
- **GitHub Actions:** Repository secrets in Settings > Secrets and variables > Actions

### Development
- **Local:** `.env` files (never committed, copy from `.env.example`)

## Required Secrets by Service

### Backend (App Runner)
| Secret | Description |
|--------|-------------|
| DATABASE_URL | PostgreSQL connection string |
| JWT_SECRET_KEY | JWT signing key (min 32 chars) |
| TWILIO_ACCOUNT_SID | Twilio account identifier |
| TWILIO_AUTH_TOKEN | Twilio API token |
| SENDGRID_API_KEY | SendGrid email API key |
| SQUARE_ACCESS_TOKEN | Square payment API token |
| GOOGLE_PLACES_API_KEY | Google Places API key |

### Frontend Apps (Build-time)
| Secret | Description |
|--------|-------------|
| VITE_API_BASE_URL | Backend API URL |
| VITE_GOOGLE_PLACES_API_KEY | Google Places (public, restricted by domain) |

### GitHub Actions
| Secret | Description |
|--------|-------------|
| AWS_ACCESS_KEY_ID | AWS deployment credentials |
| AWS_SECRET_ACCESS_KEY | AWS deployment credentials |
| PROD_DATABASE_URL | Production database URL |

## Rotating Compromised Secrets

If secrets were ever committed to git, assume they are compromised and rotate:

### Immediate Actions
1. **JWT_SECRET_KEY:** Generate new 32+ char random string, update App Runner
2. **TWILIO:** Rotate in Twilio Console > API Keys
3. **SENDGRID:** Rotate in SendGrid > Settings > API Keys
4. **SQUARE:** Rotate in Square Developer Dashboard > Credentials
5. **GOOGLE_PLACES_API_KEY:** Rotate in Google Cloud Console > APIs & Services > Credentials
6. **DATABASE_URL:** Change password in AWS RDS, update App Runner

### Git History Cleanup (Optional but Recommended)
If secrets were in git history, consider using `git filter-repo` to remove them:
```bash
# Install git-filter-repo
brew install git-filter-repo

# Remove specific files from all history
git filter-repo --invert-paths --path nerava.key --path nerava-pass.key --path cookies.txt

# Force push (CAUTION: rewrites history)
git push --force --all
```
```

#### P0.7 - Verification

```bash
# Check no secrets are tracked
git ls-files | grep -E "\.(env|key|pem|cer|csr)$" | grep -v example
# Expected: empty output

# Check .gitignore is correct
cat .gitignore | grep -E "^\.env$|^\*\.key$"
# Expected: .env and *.key lines present

# Verify .env.example files exist
ls -la backend/.env.example apps/*/.env.example
```

#### P0.8 - Commit P0

```bash
git add -A
git commit -m "P0: Remove secrets from tracking, add .gitignore protections

- Remove private keys (nerava.key, nerava-pass.key, cookies.txt)
- Remove .env files from tracking (backed up locally)
- Update .gitignore with comprehensive security rules
- Add .env.example templates for all apps
- Add /docs/security/secrets.md with rotation guide

SECURITY: Assume all committed secrets are compromised - rotate immediately"
```

---

### Phase P1: Consolidate Duplicate Directories

**Objective:** Remove duplicate/legacy directories, keep canonical versions.

#### P1.1 - Archive Duplicate Backends

```bash
# Archive before deletion
mkdir -p backups/archived-dirs

# nerava-backend-v9 (original, smaller) - archive
cp -r nerava-backend-v9 backups/archived-dirs/ 2>/dev/null || true
git rm -rf nerava-backend-v9

# nerava-backend-v9 2 (duplicate with space in name) - archive
cp -r "nerava-backend-v9 2" "backups/archived-dirs/nerava-backend-v9-2" 2>/dev/null || true
git rm -rf "nerava-backend-v9 2"
```

#### P1.2 - Archive Duplicate Landing Pages

```bash
# landing-page (legacy) - archive
cp -r landing-page backups/archived-dirs/ 2>/dev/null || true
git rm -rf landing-page

# landing-page 2 (duplicate with space) - archive
cp -r "landing-page 2" "backups/archived-dirs/landing-page-2" 2>/dev/null || true
git rm -rf "landing-page 2"

# Canonical: apps/landing
```

#### P1.3 - Remove Corrupted Driver App Directory

The `nerava-app-driver` directory contains filesystem corruption from failed shell commands.

```bash
# Archive first
cp -r nerava-app-driver backups/archived-dirs/ 2>/dev/null || true

# Remove entirely (apps/driver is canonical)
git rm -rf nerava-app-driver
```

#### P1.4 - Archive Legacy UI Directories

```bash
# ui-admin (simpler version, apps/admin is canonical)
cp -r ui-admin backups/archived-dirs/ 2>/dev/null || true
git rm -rf ui-admin

# ui-mobile (apps/driver covers mobile PWA)
cp -r ui-mobile backups/archived-dirs/ 2>/dev/null || true
# Keep for now if Flutter app references it, otherwise:
# git rm -rf ui-mobile
```

#### P1.5 - Remove Empty/Abandoned Directories

```bash
# Figma export directories (empty or stale)
git rm -rf src-figma 2>/dev/null || true
git rm -rf src_admin 2>/dev/null || true
git rm -rf src_landing_figma_new 2>/dev/null || true

# Unknown/abandoned
git rm -rf WYC-search 2>/dev/null || true
git rm -rf nerava_pwa_demo 2>/dev/null || true
```

#### P1.6 - Update References

Search for and update any references to removed directories:

```bash
# Find references to removed directories
rg -l "nerava-backend-v9|landing-page|nerava-app-driver|ui-admin" --type yaml --type json --type md

# Update .github/workflows/*.yml if they reference old paths
# Update package.json files if they reference old paths
# Update docker-compose.yml if it references old paths
```

**Manual review required:** Check each file found and update paths to canonical locations:
- `nerava-backend-v9` -> `backend`
- `nerava-backend-v9 2` -> `backend`
- `landing-page` -> `apps/landing`
- `landing-page 2` -> `apps/landing`
- `nerava-app-driver` -> `apps/driver`
- `ui-admin` -> `apps/admin`

#### P1.7 - Verification

```bash
# Verify no duplicate directories remain
ls -d */ | grep -E "nerava-backend-v9|landing-page|nerava-app-driver"
# Expected: empty output (or "No such file or directory")

# Verify canonical directories exist
ls -d backend apps/admin apps/driver apps/landing apps/merchant
# Expected: all directories listed

# Verify no broken references
rg "nerava-backend-v9 2" .
# Expected: empty output
```

#### P1.8 - Commit P1

```bash
git add -A
git commit -m "P1: Consolidate duplicate directories

Removed (archived to backups/):
- nerava-backend-v9/ (canonical: backend/)
- nerava-backend-v9 2/ (canonical: backend/)
- landing-page/ (canonical: apps/landing/)
- landing-page 2/ (canonical: apps/landing/)
- nerava-app-driver/ (canonical: apps/driver/) - had filesystem corruption
- ui-admin/ (canonical: apps/admin/)
- src-figma/, src_admin/, src_landing_figma_new/ (empty Figma exports)
- WYC-search/, nerava_pwa_demo/ (abandoned)

Updated references to point to canonical directories"
```

---

### Phase P2: Remove Build Artifacts

**Objective:** Remove committed build artifacts and recover disk space.

#### P2.1 - Remove node_modules Directories

```bash
# Remove all node_modules from git tracking
git rm -rf --cached apps/admin/node_modules 2>/dev/null || true
git rm -rf --cached apps/driver/node_modules 2>/dev/null || true
git rm -rf --cached apps/landing/node_modules 2>/dev/null || true
git rm -rf --cached apps/merchant/node_modules 2>/dev/null || true
git rm -rf --cached charger-portal/node_modules 2>/dev/null || true
git rm -rf --cached e2e/node_modules 2>/dev/null || true
git rm -rf --cached mcp/node_modules 2>/dev/null || true

# Delete locally
rm -rf apps/admin/node_modules
rm -rf apps/driver/node_modules
rm -rf apps/landing/node_modules
rm -rf apps/merchant/node_modules
rm -rf charger-portal/node_modules
rm -rf e2e/node_modules
rm -rf mcp/node_modules
```

#### P2.2 - Remove Build Output Directories

```bash
# Remove dist directories
git rm -rf --cached apps/admin/dist 2>/dev/null || true
git rm -rf --cached apps/driver/dist 2>/dev/null || true
git rm -rf --cached apps/merchant/dist 2>/dev/null || true
git rm -rf --cached wallet-pass/dist 2>/dev/null || true
git rm -rf --cached wallet-pass/build 2>/dev/null || true

rm -rf apps/admin/dist apps/driver/dist apps/merchant/dist
rm -rf wallet-pass/dist wallet-pass/build

# Remove .next directories
git rm -rf --cached apps/landing/.next 2>/dev/null || true
git rm -rf --cached charger-portal/.next 2>/dev/null || true

rm -rf apps/landing/.next charger-portal/.next

# Remove out directories (Next.js static export)
git rm -rf --cached apps/landing/out 2>/dev/null || true
rm -rf apps/landing/out
```

#### P2.3 - Remove Python Artifacts

```bash
# Remove virtual environments
git rm -rf --cached backend/.venv 2>/dev/null || true
rm -rf backend/.venv

# Remove cache directories
git rm -rf --cached backend/.cache 2>/dev/null || true
git rm -rf --cached backend/.pytest_cache 2>/dev/null || true
git rm -rf --cached .pytest_cache 2>/dev/null || true

rm -rf backend/.cache backend/.pytest_cache .pytest_cache

# Remove __pycache__ directories
find . -type d -name "__pycache__" -exec git rm -rf --cached {} \; 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} \; 2>/dev/null || true

# Remove coverage files
git rm --cached backend/.coverage 2>/dev/null || true
git rm -rf --cached backend/htmlcov 2>/dev/null || true
rm -f backend/.coverage
rm -rf backend/htmlcov
```

#### P2.4 - Remove Archive Files

```bash
# Remove zip files from git
git rm --cached nerava-backend-v9.zip 2>/dev/null || true
git rm --cached nerava-ui-latest.zip 2>/dev/null || true
git rm --cached ui-mobile.zip 2>/dev/null || true
git rm --cached apps/landing.zip 2>/dev/null || true

# Move to backups instead of deleting (user may need them)
mv nerava-backend-v9.zip backups/ 2>/dev/null || true
mv nerava-ui-latest.zip backups/ 2>/dev/null || true
mv ui-mobile.zip backups/ 2>/dev/null || true
mv apps/landing.zip backups/ 2>/dev/null || true
```

#### P2.5 - Remove Debug/Test Data Files

```bash
# JSON data dumps
git rm --cached chargers_with_merchants.json 2>/dev/null || true
git rm --cached texas_charger_rankings.json 2>/dev/null || true
git rm --cached merchant_data_validation.json 2>/dev/null || true
git rm --cached npm-audit-*.json 2>/dev/null || true

rm -f chargers_with_merchants.json texas_charger_rankings.json merchant_data_validation.json
rm -f npm-audit-*.json

# Test HTML files
git rm --cached view-heights-pizzeria.html 2>/dev/null || true
rm -f view-heights-pizzeria.html

# SQLite database
git rm --cached nerava.db 2>/dev/null || true
mv nerava.db backups/ 2>/dev/null || true
```

#### P2.6 - Verification

```bash
# Check disk space recovered
du -sh .

# Verify no node_modules tracked
git ls-files | grep node_modules
# Expected: empty output

# Verify no dist/build tracked
git ls-files | grep -E "^(apps|charger-portal|wallet-pass)/.*(dist|\.next|build)/"
# Expected: empty output

# Verify .gitignore covers artifacts
cat .gitignore | grep -E "node_modules|dist|\.next"
```

#### P2.7 - Commit P2

```bash
git add -A
git commit -m "P2: Remove build artifacts from tracking

Removed:
- node_modules/ directories (10 instances, ~2.5GB)
- dist/, .next/, build/, out/ directories
- Python .venv/, .cache/, .pytest_cache/, __pycache__/
- .coverage files
- Archive zips (moved to backups/)
- Debug data files (JSON dumps, test HTML)
- SQLite database

.gitignore updated to prevent re-commit"
```

---

### Phase P3: Documentation Canonicalization

**Objective:** Organize documentation into clean structure.

#### P3.1 - Create Documentation Structure

```bash
# Create doc directories
mkdir -p docs/deployment
mkdir -p docs/architecture
mkdir -p docs/api
mkdir -p docs/archive
mkdir -p docs/security  # Created in P0

# Create prompts archive
mkdir -p claude-cursor-prompts/archive
```

#### P3.2 - Move Root Cursor Prompts

```bash
# Move cursor-prompt-*.txt files to archive
git mv cursor-prompt-asadas-photo-fix.txt claude-cursor-prompts/archive/ 2>/dev/null || true
git mv cursor-prompt-charger-merchant-routing.txt claude-cursor-prompts/archive/ 2>/dev/null || true
git mv cursor-prompt-deploy-and-fix-auth.txt claude-cursor-prompts/archive/ 2>/dev/null || true
git mv cursor-prompt-deploy-production.txt claude-cursor-prompts/archive/ 2>/dev/null || true
git mv cursor-prompt-fix-docker-build.txt claude-cursor-prompts/archive/ 2>/dev/null || true
git mv cursor-prompt-fix-iam-role-deploy.txt claude-cursor-prompts/archive/ 2>/dev/null || true
git mv cursor-prompt-official-logo.txt claude-cursor-prompts/archive/ 2>/dev/null || true
git mv cursor-prompt-user-avatar.txt claude-cursor-prompts/archive/ 2>/dev/null || true
```

#### P3.3 - Categorize and Move Root Markdown Files

This requires manual review. Suggested categorization:

**Move to `docs/deployment/`:**
```bash
git mv AWS_*.md docs/deployment/ 2>/dev/null || true
git mv DEPLOY_*.md docs/deployment/ 2>/dev/null || true
git mv CLOUDFRONT_*.md docs/deployment/ 2>/dev/null || true
git mv APPRUNNER_*.md docs/deployment/ 2>/dev/null || true
git mv PRODUCTION_*.md docs/deployment/ 2>/dev/null || true
```

**Move to `docs/architecture/`:**
```bash
git mv CODEBASE_*.md docs/architecture/ 2>/dev/null || true
git mv ARCHITECTURE_*.md docs/architecture/ 2>/dev/null || true
git mv BACKEND_*.md docs/architecture/ 2>/dev/null || true
```

**Move to `docs/api/`:**
```bash
git mv API_*.md docs/api/ 2>/dev/null || true
git mv ENDPOINT_*.md docs/api/ 2>/dev/null || true
```

**Move to `docs/archive/` (old/completed items):**
```bash
git mv *_FIX.md docs/archive/ 2>/dev/null || true
git mv *_FIXED.md docs/archive/ 2>/dev/null || true
git mv *_COMPLETE.md docs/archive/ 2>/dev/null || true
git mv *_VALIDATION.md docs/archive/ 2>/dev/null || true
git mv RAILWAY_*.md docs/archive/ 2>/dev/null || true  # Deprecated platform
```

**Keep at root (important current docs):**
- `README.md`
- `CONTRIBUTING.md` (if exists)
- `CHANGELOG.md` (if exists)

#### P3.4 - Create docs/README.md Index

Create `/docs/README.md`:

```markdown
# Nerava Documentation

## Quick Links

### Operations
- [Deployment Runbook](./deployment/runbook.md)
- [AWS App Runner Setup](./deployment/aws-apprunner.md)
- [CloudFront Setup](./deployment/cloudfront-setup.md)

### Architecture
- [Backend Overview](./architecture/backend-overview.md)
- [Frontend Apps](./architecture/frontend-apps.md)

### API
- [Admin Endpoints](./api/admin-endpoints.md)
- [Merchant Endpoints](./api/merchant-endpoints.md)
- [Driver Endpoints](./api/driver-endpoints.md)

### Security
- [Secrets Management](./security/secrets.md)

## Directory Structure

```
docs/
├── deployment/     # How to deploy and operate
├── architecture/   # System design and structure
├── api/           # API documentation
├── security/      # Security guidelines
├── archive/       # Historical docs (completed work)
└── launch-evidence/ # Launch validation evidence
```

## Archive

Old documentation (completed fixes, deprecated platforms) is in `./archive/`.
```

#### P3.5 - Create claude-cursor-prompts/README.md

Create `/claude-cursor-prompts/README.md`:

```markdown
# Claude/Cursor Prompts

AI assistant prompts for development tasks.

## Active Prompts

| File | Purpose |
|------|---------|
| `v1-launch-portals.md` | V1 launch implementation guide |
| `v1-portals-test-deploy.md` | Portal testing and deployment |
| `deploy-v26-with-env.txt` | V26 deployment with env setup |
| `deployment-monitor.txt` | Deployment monitoring |
| `working-prompt.txt` | Current working prompt |

## Naming Convention

New prompts: `YYYY-MM-DD_<area>_<topic>.md`

Examples:
- `2026-01-23_backend_api-auth.md`
- `2026-01-24_driver_offline-mode.md`

## Archive

Old/completed prompts are in `./archive/`.
```

#### P3.6 - Update Root README.md

Ensure root `README.md` has:

```markdown
# Nerava

EV charging and local commerce platform.

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 15+

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in values
uvicorn app.main:app --reload
```

### Frontend Apps
```bash
# Admin Portal
cd apps/admin && npm install && npm run dev

# Driver App
cd apps/driver && npm install && npm run dev

# Merchant Portal
cd apps/merchant && npm install && npm run dev

# Landing Page
cd apps/landing && npm install && npm run dev
```

## Project Structure

```
nerava/
├── apps/           # Frontend applications
│   ├── admin/      # Admin portal (React + Vite)
│   ├── driver/     # Driver PWA (React + Vite)
│   ├── landing/    # Landing page (Next.js)
│   └── merchant/   # Merchant portal (React + Vite)
├── backend/        # FastAPI backend
├── docs/           # Documentation
├── e2e/            # End-to-end tests
├── infra/          # Infrastructure (Terraform)
└── .github/        # CI/CD workflows
```

## Documentation

See [docs/README.md](./docs/README.md) for full documentation.

## Contributing

1. Create feature branch from `main`
2. Make changes
3. Run tests: `npm run test` / `pytest`
4. Submit PR
```

#### P3.7 - Verification

```bash
# Check docs structure
ls -la docs/
ls -la docs/deployment/ docs/architecture/ docs/api/ docs/archive/

# Check prompts structure
ls -la claude-cursor-prompts/
ls -la claude-cursor-prompts/archive/

# Count remaining root markdown files (should be minimal)
ls -la *.md | wc -l
# Target: < 5 files (README, CONTRIBUTING, CHANGELOG, etc.)
```

#### P3.8 - Commit P3

```bash
git add -A
git commit -m "P3: Organize documentation structure

- Created docs/ hierarchy (deployment, architecture, api, security, archive)
- Moved root markdown files to appropriate directories
- Created docs/README.md index
- Moved cursor prompts to claude-cursor-prompts/archive/
- Created claude-cursor-prompts/README.md
- Updated root README.md with quick start guide

Root directory now clean with only essential files"
```

---

## 5. Manifest

### Files to DELETE (after backup)

```
# Private keys
nerava.key
nerava-pass.key
cookies.txt
nerava.csr
nerava-pass.csr
pass.cer

# Environment files (keep .env.example only)
backend/.env
backend/.env.backup
backend/.env.bak
nerava-backend-v9 2/.env*
nerava-app-driver/.env*

# Directories (P1)
nerava-backend-v9/
nerava-backend-v9 2/
landing-page/
landing-page 2/
nerava-app-driver/
ui-admin/
src-figma/
src_admin/
src_landing_figma_new/
WYC-search/
nerava_pwa_demo/

# Build artifacts (P2)
*/node_modules/
*/dist/
*/.next/
*/build/
*/out/
backend/.venv/
backend/.cache/
*/.pytest_cache/
*/__pycache__/
*.coverage

# Archives
*.zip (at root and apps/)

# Debug data
chargers_with_merchants.json
texas_charger_rankings.json
merchant_data_validation.json
npm-audit-*.json
view-heights-pizzeria.html
nerava.db
```

### Files to MOVE

```
# To claude-cursor-prompts/archive/
cursor-prompt-*.txt

# To docs/deployment/
AWS_*.md, DEPLOY_*.md, CLOUDFRONT_*.md, APPRUNNER_*.md, PRODUCTION_*.md

# To docs/architecture/
CODEBASE_*.md, ARCHITECTURE_*.md, BACKEND_*.md

# To docs/api/
API_*.md, ENDPOINT_*.md

# To docs/archive/
*_FIX.md, *_FIXED.md, *_COMPLETE.md, *_VALIDATION.md, RAILWAY_*.md
```

### Files to KEEP (Canonical)

```
# Backend
backend/

# Frontend Apps
apps/admin/
apps/driver/
apps/landing/
apps/merchant/

# Infrastructure
.github/workflows/
infra/
charts/

# Documentation
docs/
claude-cursor-prompts/
README.md

# Configuration
.gitignore
docker-compose.yml
pyproject.toml
pytest.ini

# Tests
e2e/
tests/
```

### .gitignore Additions

```gitignore
# Security
*.key
*.p12
*.pem
*.cer
*.csr
cookies.txt
.env
.env.*
!.env.example
*.backup
*.bak
backups/

# Build
node_modules/
dist/
build/
.next/
out/
.vite/
.cache/
.pytest_cache/
__pycache__/
*.pyc
.venv/
venv/
.coverage
htmlcov/
coverage/
playwright-report/
test-results/

# IDE/OS
.DS_Store
*.swp
*.swo
.idea/
*.iml

# Archives
*.zip
*.tar.gz
*.tgz

# Database
*.db
*.sqlite
*.sqlite3
```

---

## 6. Verification Commands

Run after ALL phases complete:

```bash
cd /Users/jameskirk/Desktop/Nerava

echo "=== Security Check ==="
# No secrets tracked
git ls-files | grep -E "\.(env|key|pem|cer|csr)$" | grep -v example
# Expected: empty

echo "=== Structure Check ==="
# No duplicate directories
ls -d */ | grep -E "nerava-backend-v9|landing-page|nerava-app-driver"
# Expected: empty or "No such file"

# Canonical directories exist
ls -d backend apps/admin apps/driver apps/landing apps/merchant
# Expected: all listed

echo "=== Artifact Check ==="
# No node_modules tracked
git ls-files | grep node_modules | head -5
# Expected: empty

# No dist/build tracked
git ls-files | grep -E "/dist/|/\.next/|/build/" | head -5
# Expected: empty

echo "=== Disk Space ==="
du -sh .
# Expected: ~1.5GB (down from ~4GB)

echo "=== Build Verification ==="
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m py_compile app/main.py
# pytest (if tests exist)
cd ..

# Frontend - Admin
cd apps/admin
npm ci
npm run lint
npm run build
cd ../..

# Frontend - Driver
cd apps/driver
npm ci
npm run lint
npm run build
cd ../..

# Frontend - Merchant
cd apps/merchant
npm ci
npm run lint
npm run build
cd ../..

# Frontend - Landing
cd apps/landing
npm ci
npm run lint
npm run build
cd ../..

echo "=== Git Status ==="
git status
# Expected: clean working tree
```

---

## 7. Rollback Instructions

### Before Starting
```bash
# Create full backup
cd /Users/jameskirk/Desktop
tar -czf nerava-backup-$(date +%Y%m%d-%H%M%S).tar.gz Nerava/
```

### Rollback Specific Phase

```bash
# See commit history
git log --oneline -10

# Rollback to before a specific phase
git reset --hard HEAD~1  # Undo last commit
git reset --hard HEAD~2  # Undo last 2 commits
# etc.
```

### Rollback Everything

```bash
# From backup
cd /Users/jameskirk/Desktop
rm -rf Nerava
tar -xzf nerava-backup-YYYYMMDD-HHMMSS.tar.gz
```

### Recover Specific Files

```bash
# Files are in backups/ directory
ls backups/.secrets-backup-*/
ls backups/archived-dirs/
ls backups/*.zip

# Copy back as needed
cp backups/.secrets-backup-*/backend-.env backend/.env
```

---

## 8. Secret Rotation Checklist

**CRITICAL:** If any of these were ever committed, rotate immediately:

### JWT Secret
1. Generate new secret: `openssl rand -hex 32`
2. Update App Runner environment variable: `JWT_SECRET_KEY`
3. Existing sessions will be invalidated (acceptable)

### Twilio
1. Go to: Twilio Console > Account > API Keys
2. Create new API Key
3. Update App Runner: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`
4. Revoke old key

### SendGrid
1. Go to: SendGrid > Settings > API Keys
2. Create new key with same permissions
3. Update App Runner: `SENDGRID_API_KEY`
4. Delete old key

### Square
1. Go to: Square Developer Dashboard > Application > Credentials
2. Create new Access Token
3. Update App Runner: `SQUARE_ACCESS_TOKEN`
4. Revoke old token

### Google Places API
1. Go to: Google Cloud Console > APIs & Services > Credentials
2. Create new API key
3. Restrict to your domains
4. Update App Runner and frontend builds: `GOOGLE_PLACES_API_KEY`
5. Delete old key

### AWS Access Keys (if compromised)
1. Go to: AWS IAM > Users > Security credentials
2. Create new access key
3. Update GitHub Secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
4. Deactivate/delete old key

### Database Password
1. AWS RDS Console > Modify > New master password
2. Update App Runner: `DATABASE_URL`
3. Restart App Runner service

---

## 9. Post-Cleanup CI/CD Verification

After cleanup, verify CI/CD still works:

```bash
# Push to a test branch
git checkout -b cleanup-verification
git push -u origin cleanup-verification

# Verify GitHub Actions run
# - backend-tests.yml should pass
# - ci.yml should pass

# If workflows fail, check:
# 1. Path references in .github/workflows/*.yml
# 2. Required environment variables in GitHub Secrets
# 3. Build contexts in deploy-*.yml
```

---

## 10. Success Criteria Checklist

- [ ] No `.key`, `.env`, `.pem`, `.cer` files tracked in git (except `.env.example`)
- [ ] `.gitignore` updated with all security and artifact patterns
- [ ] `.env.example` exists for: backend, apps/admin, apps/driver, apps/merchant, apps/landing
- [ ] `/docs/security/secrets.md` created with rotation guide
- [ ] Only one backend directory: `backend/`
- [ ] Only one set of frontend apps: `apps/admin`, `apps/driver`, `apps/landing`, `apps/merchant`
- [ ] No `node_modules/`, `dist/`, `.next/`, `.venv/` tracked in git
- [ ] No `.zip` archives at root
- [ ] Root directory has < 20 items (down from 150+)
- [ ] Root has < 5 markdown files (README.md and essentials only)
- [ ] `docs/` organized with README.md index
- [ ] `claude-cursor-prompts/` has archive/ subdirectory
- [ ] Backend builds: `python -m py_compile app/main.py`
- [ ] All frontend apps build: `npm run build` passes
- [ ] `git status` shows clean working tree
- [ ] Secret rotation completed for all compromised credentials
- [ ] GitHub Actions workflows pass on test branch

---

**End of Cursor Implementation Prompt**
