# Nerava Directory Cleanup Report

**Generated:** January 23, 2026
**Total Issues Found:** 45+
**Estimated Recoverable Space:** ~2GB

---

## CRITICAL SECURITY ISSUES (Fix Immediately)

### Private Keys in Repository
```
DELETE IMMEDIATELY:
/Users/jameskirk/Desktop/Nerava/nerava.key
/Users/jameskirk/Desktop/Nerava/nerava-pass.key
/Users/jameskirk/Desktop/Nerava/cookies.txt
```
**Action:** Move to AWS Secrets Manager or 1Password. Never commit keys.

### Environment Files with Secrets
```
REVIEW AND SECURE:
/Users/jameskirk/Desktop/Nerava/backend/.env
/Users/jameskirk/Desktop/Nerava/backend/.env.backup
/Users/jameskirk/Desktop/Nerava/backend/.env.bak
/Users/jameskirk/Desktop/Nerava/nerava-backend-v9 2/.env*
/Users/jameskirk/Desktop/Nerava/nerava-app-driver/.env*
```
**Action:** Keep only `.env.example` with placeholder values. Real secrets in secrets manager.

---

## CORRUPTED DIRECTORIES (Delete All)

The `nerava-app-driver` directory contains filesystem corruption from a failed curl command:

```bash
# These are NOT real directories - they're shell command artifacts
rm -rf "/Users/jameskirk/Desktop/Nerava/nerava-app-driver/-H"
rm -rf "/Users/jameskirk/Desktop/Nerava/nerava-app-driver/-X"
rm -rf "/Users/jameskirk/Desktop/Nerava/nerava-app-driver/-s"
rm -rf "/Users/jameskirk/Desktop/Nerava/nerava-app-driver/curl"
rm -rf "/Users/jameskirk/Desktop/Nerava/nerava-app-driver/POST"
rm -rf "/Users/jameskirk/Desktop/Nerava/nerava-app-driver/echo"
rm -rf "/Users/jameskirk/Desktop/Nerava/nerava-app-driver/Content-Type: application"
rm -rf "/Users/jameskirk/Desktop/Nerava/nerava-app-driver/X-Nerava-Key:"
rm -rf "/Users/jameskirk/Desktop/Nerava/nerava-app-driver/=================="*
rm -rf "/Users/jameskirk/Desktop/Nerava/nerava-app-driver/🎬"*
rm -rf "/Users/jameskirk/Desktop/Nerava/nerava-app-driver/📋"*
```

---

## DUPLICATE DIRECTORIES (Consolidate)

### Backend (3 versions!)

| Directory | Status | Action |
|-----------|--------|--------|
| `/backend` | **KEEP** - Primary | Consolidate here |
| `/nerava-backend-v9` | Archive | Delete or move to `/archive/` |
| `/nerava-backend-v9 2` | Duplicate with space in name! | **DELETE** |

**Why this happened:** Copy-paste during development created duplicates. The space in the name breaks scripts.

### Landing Page (3 versions!)

| Directory | Status | Action |
|-----------|--------|--------|
| `/apps/landing` | **KEEP** - Monorepo style | Use this |
| `/landing-page` | Legacy | Delete or archive |
| `/landing-page 2` | Duplicate with space | **DELETE** |

### Driver App (2 versions + corruption)

| Directory | Status | Action |
|-----------|--------|--------|
| `/apps/driver` | **KEEP** - Monorepo style | Use this |
| `/nerava-app-driver` | Corrupted + legacy | **DELETE ENTIRELY** |

### Admin Portal (2 versions)

| Directory | Status | Action |
|-----------|--------|--------|
| `/apps/admin` | **KEEP** - Feature-rich | Use this |
| `/ui-admin` | Simpler but API-connected | Merge useful code, then delete |

---

## BUILD ARTIFACTS (Delete - Auto-Rebuild)

```bash
# Remove all node_modules (~1.5GB total)
find /Users/jameskirk/Desktop/Nerava -name "node_modules" -type d -prune -exec rm -rf {} +

# Remove all .next build directories
find /Users/jameskirk/Desktop/Nerava -name ".next" -type d -prune -exec rm -rf {} +

# Remove Python virtual environments
find /Users/jameskirk/Desktop/Nerava -name ".venv" -type d -prune -exec rm -rf {} +
find /Users/jameskirk/Desktop/Nerava -name "venv" -type d -prune -exec rm -rf {} +

# Remove pytest cache
find /Users/jameskirk/Desktop/Nerava -name ".pytest_cache" -type d -prune -exec rm -rf {} +
find /Users/jameskirk/Desktop/Nerava -name "__pycache__" -type d -prune -exec rm -rf {} +

# Remove coverage files
find /Users/jameskirk/Desktop/Nerava -name ".coverage" -delete
find /Users/jameskirk/Desktop/Nerava -name "htmlcov" -type d -prune -exec rm -rf {} +
```

---

## ZIP ARCHIVES (Move to Archive or Delete)

```
/Users/jameskirk/Desktop/Nerava/nerava-backend-v9.zip  (28MB)
/Users/jameskirk/Desktop/Nerava/ui-mobile.zip          (19MB)
/Users/jameskirk/Desktop/Nerava/nerava-ui-latest.zip   (2.6KB - likely corrupted)
/Users/jameskirk/Desktop/Nerava/apps/landing.zip       (138MB)
```

**Action:** If needed for recovery, move to `/archive/`. Otherwise delete.

---

## DEBUG/TEST DATA FILES (Delete)

```bash
# JSON data dumps
rm "/Users/jameskirk/Desktop/Nerava/chargers_with_merchants.json"
rm "/Users/jameskirk/Desktop/Nerava/texas_charger_rankings.json"
rm "/Users/jameskirk/Desktop/Nerava/merchant_data_validation.json"

# NPM audit reports
rm /Users/jameskirk/Desktop/Nerava/npm-audit-*.json

# Test HTML
rm "/Users/jameskirk/Desktop/Nerava/view-heights-pizzeria.html"

# SQLite database (if test data)
rm "/Users/jameskirk/Desktop/Nerava/nerava.db"
```

---

## EMPTY/ABANDONED DIRECTORIES (Delete)

```bash
# Empty Figma export directories
rm -rf "/Users/jameskirk/Desktop/Nerava/src-figma"
rm -rf "/Users/jameskirk/Desktop/Nerava/src_admin"
rm -rf "/Users/jameskirk/Desktop/Nerava/src_landing_figma_new"

# Unknown/abandoned
rm -rf "/Users/jameskirk/Desktop/Nerava/WYC-search"
rm -rf "/Users/jameskirk/Desktop/Nerava/nerava_pwa_demo"
```

---

## DOCUMENTATION CHAOS (~130 Markdown Files at Root)

### Problem
The root directory has ~130 markdown files making it impossible to navigate:
- Multiple versions of same docs (e.g., `MAGIC_LINK_500_ERROR_FIX.md` AND `MAGIC_LINK_500_ERROR_FIXED.md`)
- Old prompts mixed with current ones
- Deployment guides for deprecated platforms
- Status reports from months ago

### Proposed Structure

```
/Users/jameskirk/Desktop/Nerava/
├── docs/
│   ├── deployment/
│   │   ├── aws-apprunner.md
│   │   ├── cloudfront-setup.md
│   │   └── runbook.md
│   ├── architecture/
│   │   ├── backend-overview.md
│   │   ├── frontend-apps.md
│   │   └── data-models.md
│   ├── api/
│   │   ├── admin-endpoints.md
│   │   ├── merchant-endpoints.md
│   │   └── driver-endpoints.md
│   └── archive/
│       └── (old docs moved here)
├── claude-cursor-prompts/
│   ├── active/
│   │   ├── v1-launch-portals.md
│   │   └── deploy-v26.md
│   └── archive/
│       └── (old prompts)
└── README.md (single source of truth)
```

### Files to Archive (Move to `/docs/archive/`)

```
CODEBASE_ANALYSIS_2025.md
CODEBASE_COMPREHENSIVE_ANALYSIS.md
CODE_REVIEW_GRADE.md
CURSOR_CHARGER_DISCOVERY_PROMPT.md
CURSOR_CHARGER_DISCOVERY_FINAL.md
PRODUCTION_FIXES_COMPLETE.md
PRODUCTION_FIXES_VALIDATION.md
PRODUCTION_QUALITY_GATE_ANALYSIS.md
PROD_QUALITY_GATE.md
PROD_QUALITY_GATE_TODO.md
RAILWAY_DEPLOYMENT.md (deprecated platform)
... (100+ more)
```

### Cursor Prompts to Consolidate

Move all `cursor-prompt-*.txt` files to `/claude-cursor-prompts/archive/`:
```
cursor-prompt-asadas-photo-fix.txt
cursor-prompt-charger-merchant-routing.txt
cursor-prompt-deploy-and-fix-auth.txt
cursor-prompt-deploy-production.txt
cursor-prompt-fix-docker-build.txt
cursor-prompt-fix-iam-role-deploy.txt
cursor-prompt-official-logo.txt
cursor-prompt-user-avatar.txt
```

---

## RECOMMENDED FINAL STRUCTURE

```
/Users/jameskirk/Desktop/Nerava/
├── apps/                          # All frontend applications
│   ├── admin/                     # Admin portal (React)
│   ├── driver/                    # Driver PWA (React)
│   ├── landing/                   # Landing page (Next.js)
│   ├── merchant/                  # Merchant portal (React)
│   └── charger-portal/            # Charger portal (Next.js)
│
├── backend/                       # Single backend directory
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
│
├── infrastructure/                # IaC and deployment
│   ├── cloudformation/
│   ├── terraform/
│   └── scripts/
│
├── docs/                          # All documentation
│   ├── deployment/
│   ├── architecture/
│   ├── api/
│   └── archive/
│
├── claude-cursor-prompts/         # AI prompts (active + archive)
│   ├── active/
│   └── archive/
│
├── reports/                       # Generated reports
│
├── e2e/                           # End-to-end tests
│
├── mcp/                           # MCP server configs
│
└── README.md                      # Single entry point
```

---

## CLEANUP SCRIPT

```bash
#!/bin/bash
# Nerava Cleanup Script
# WARNING: Review each section before running!

NERAVA_DIR="/Users/jameskirk/Desktop/Nerava"
cd "$NERAVA_DIR"

echo "=== Phase 1: Remove Security Risks ==="
# Move keys to secure location first!
# rm nerava.key nerava-pass.key cookies.txt

echo "=== Phase 2: Remove Corrupted Directories ==="
rm -rf "nerava-app-driver/-H"
rm -rf "nerava-app-driver/-X"
rm -rf "nerava-app-driver/-s"
rm -rf "nerava-app-driver/curl"
rm -rf "nerava-app-driver/POST"
rm -rf "nerava-app-driver/echo"
rm -rf "nerava-app-driver/Content-Type:"*
rm -rf "nerava-app-driver/X-Nerava-Key:"*
rm -rf "nerava-app-driver/==="*
rm -rf "nerava-app-driver/🎬"*
rm -rf "nerava-app-driver/📋"*

echo "=== Phase 3: Remove Duplicates ==="
rm -rf "nerava-backend-v9 2"
rm -rf "nerava-backend-v9"
rm -rf "landing-page 2"
rm -rf "nerava-app-driver"  # After saving any needed code

echo "=== Phase 4: Remove Build Artifacts ==="
find . -name "node_modules" -type d -prune -exec rm -rf {} + 2>/dev/null
find . -name ".next" -type d -prune -exec rm -rf {} + 2>/dev/null
find . -name ".venv" -type d -prune -exec rm -rf {} + 2>/dev/null
find . -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null
find . -name ".pytest_cache" -type d -prune -exec rm -rf {} + 2>/dev/null
find . -name ".coverage" -delete 2>/dev/null

echo "=== Phase 5: Remove Debug Data ==="
rm -f chargers_with_merchants.json
rm -f texas_charger_rankings.json
rm -f merchant_data_validation.json
rm -f npm-audit-*.json
rm -f view-heights-pizzeria.html

echo "=== Phase 6: Remove Empty Directories ==="
rm -rf src-figma
rm -rf src_admin
rm -rf src_landing_figma_new
rm -rf WYC-search
rm -rf nerava_pwa_demo

echo "=== Phase 7: Archive Zips ==="
mkdir -p archive
mv *.zip archive/ 2>/dev/null

echo "=== Phase 8: Organize Documentation ==="
mkdir -p docs/archive
mkdir -p claude-cursor-prompts/archive
# Move old docs manually after review

echo "=== Cleanup Complete ==="
du -sh .
```

---

## WHY CURSOR MADE MISTAKES

The confusing directory structure caused Cursor to:

1. **Reference wrong driver app** - Used `/apps/driver` instead of `/nerava-app-driver` because both existed
2. **Use outdated code** - Multiple backend versions meant inconsistent implementations
3. **Miss files** - Too much noise (130+ markdown files) made finding relevant code harder
4. **Create duplicates** - Unclear which directory was "canonical" led to duplicate implementations

**Fix:** A clean, consistent structure with one source of truth per app prevents these mistakes.

---

## ESTIMATED IMPACT

| Metric | Before | After |
|--------|--------|-------|
| Total Size | ~4GB | ~1.5GB |
| Top-level items | 150+ | ~15 |
| Markdown files at root | 130+ | 1 (README.md) |
| Backend directories | 3 | 1 |
| Driver app directories | 2 | 1 |
| Landing page directories | 3 | 1 |

---

## NEXT STEPS

1. **Backup first**: `tar -czf nerava-backup-$(date +%Y%m%d).tar.gz /Users/jameskirk/Desktop/Nerava`
2. **Review this report** with team
3. **Run cleanup script** in phases (not all at once)
4. **Update .gitignore** to prevent future issues
5. **Document the new structure** in README.md
6. **Update CI/CD** if paths changed
