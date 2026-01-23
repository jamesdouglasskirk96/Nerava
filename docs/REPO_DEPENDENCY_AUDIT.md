# Repo-Wide Package + Dependency Audit Report

**Generated:** 2025-01-XX  
**Scope:** Full repository (backend + frontend + scripts + infra)  
**Methodology:** Context7-powered validation + manual analysis

---

## 1. Executive Summary

### Dependency Health Score: **6.5/10**

**Rationale:**
- ✅ Consistent package manager usage (npm across all JS projects)
- ✅ Lockfiles present for all JS projects
- ⚠️ Python version mismatch across environments (3.9 vs 3.10 vs 3.11)
- ⚠️ Missing dependency in compiled requirements.txt (sentry-sdk)
- ⚠️ Outdated major framework versions (FastAPI 0.103.2, Pydantic 2.5.0)
- ⚠️ No explicit Node.js version pinning
- ⚠️ CI workflows use different Python versions than production

### Top 10 Risks (Ranked)

| Priority | Risk | Impact | File(s) | Status |
|----------|------|--------|---------|--------|
| **P0** | Python version mismatch (3.9/3.10/3.11) | High | `Dockerfile`, `.github/workflows/*.yml`, `nixpacks.toml`, `pyproject.toml` | **CRITICAL** |
| **P0** | Missing `sentry-sdk` in compiled requirements.txt | High | `nerava-backend-v9/requirements.txt` | **CRITICAL** |
| **P1** | FastAPI 0.103.2 (released 2023) - 20+ minor versions behind | Medium | `nerava-backend-v9/requirements.in` | **OUTDATED** |
| **P1** | Pydantic 2.5.0 (released 2024) - 7+ minor versions behind | Medium | `nerava-backend-v9/requirements.in` | **OUTDATED** |
| **P1** | httpx 0.26.0 constraint violation potential | Medium | `nerava-backend-v9/requirements.in` | **REVIEW** |
| **P1** | No Node.js version pinning in package.json files | Medium | All `package.json` files | **MISSING** |
| **P2** | React version mismatch (18.2.0 vs 18.3.1) | Low | `ui-admin/package.json` vs others | **MINOR** |
| **P2** | recharts version mismatch (2.12.7 vs 3.3.0) | Low | `charger-portal/package.json` vs `ui-mobile/package.json` | **MINOR** |
| **P2** | CI workflows use `continue-on-error: true` | Low | `.github/workflows/ci.yml` | **RISK** |
| **P2** | Missing pytest-cov/coverage in requirements-dev.txt | Low | `nerava-backend-v9/requirements-dev.txt` | **MISSING** |

### Launch-Safe Recommended Changes

**P0 (Must Fix Before Launch):**
1. Standardize Python version to 3.10 across all environments
2. Add `sentry-sdk` to requirements.txt (recompile from requirements.in)
3. Pin Node.js version in all package.json files (recommend Node 20 LTS)

**P1 (Should Fix Soon):**
1. Upgrade FastAPI to latest 0.115.x (test thoroughly)
2. Upgrade Pydantic to latest 2.12.x (test thoroughly)
3. Review httpx version constraints

**P2 (Nice to Have):**
1. Standardize React versions across projects
2. Standardize recharts versions
3. Remove `continue-on-error` from CI workflows
4. Add missing dev dependencies

---

## 2. Dependency Inventory

### 2.1 JavaScript/TypeScript Projects

| Project | Package Manager | Manifest | Lockfile | Node Version | Install Command |
|---------|----------------|----------|----------|--------------|----------------|
| **charger-portal** | npm | `package.json` | `package-lock.json` | Not pinned | `npm ci` |
| **landing-page** | npm | `package.json` | `package-lock.json` | Not pinned | `npm ci` |
| **ui-admin** | npm | `package.json` | `package-lock.json` | Not pinned | `npm ci` |
| **ui-mobile** | npm | `package.json` | `package-lock.json` | Not pinned | `npm ci` |

**Summary:**
- ✅ All projects use npm (consistent)
- ✅ All projects have lockfiles
- ⚠️ No Node.js version pinning in package.json files
- ⚠️ CI uses Node 20 (`.github/workflows/ci.yml`), but not enforced in projects

### 2.2 Python Backend

| Component | Package Manager | Manifest | Lockfile | Python Version | Install Command |
|-----------|----------------|----------|----------|----------------|----------------|
| **nerava-backend-v9** | pip-tools | `requirements.in` | `requirements.txt` (compiled) | **MISMATCH** | `pip install -r requirements.txt` |
| **nerava-backend-v9 (dev)** | pip-tools | `requirements-dev.in` | `requirements-dev.txt` (compiled) | **MISMATCH** | `pip-sync requirements-dev.txt` |
| **Root config** | N/A | `pyproject.toml` | N/A | Targets 3.10 | N/A |

**Python Version Mismatch Details:**
- **Dockerfile**: Python 3.9 (`FROM python:3.9-slim`)
- **Dockerfile.localdev**: Python 3.9 (`FROM python:3.9-slim`)
- **nixpacks.toml**: Python 3.9 (`PYTHON_VERSION = "3.9"`)
- **.github/workflows/backend-tests.yml**: Python 3.10 (`python-version: "3.10"`)
- **.github/workflows/ci.yml**: Python 3.11 (`python-version: '3.11'`)
- **pyproject.toml**: Targets Python 3.10 (`target-version = ["py310"]`)

**⚠️ CRITICAL:** This mismatch can cause "works on my machine" issues and production failures.

### 2.3 Infrastructure & Tooling

| Component | Type | File | Notes |
|-----------|------|------|-------|
| **CI/CD** | GitHub Actions | `.github/workflows/backend-tests.yml` | Python 3.10 |
| **CI/CD** | GitHub Actions | `.github/workflows/ci.yml` | Python 3.11, Node 20 |
| **Container** | Docker | `nerava-backend-v9/Dockerfile` | Python 3.9 |
| **Container** | Docker | `nerava-backend-v9/Dockerfile.localdev` | Python 3.9 |
| **Deployment** | Nixpacks | `nerava-backend-v9/nixpacks.toml` | Python 3.9 |

---

## 3. Risk & Compatibility Findings

### 3.1 Python Ecosystem

#### Security Risks

| Package | Current Version | Latest Version | Risk Level | Notes |
|---------|----------------|----------------|------------|-------|
| **fastapi** | 0.103.2 | 0.115.x+ | ⚠️ Medium | 20+ minor versions behind, security patches likely |
| **pydantic** | 2.5.0 | 2.12.x+ | ⚠️ Medium | 7+ minor versions behind, bug fixes available |
| **httpx** | 0.26.0 | 0.27.x+ | ⚠️ Low | Constraint in requirements.in: `>=0.24.0,<0.27.0` |
| **starlette** | 0.27.0 | 0.41.x+ | ⚠️ Medium | Transitive dependency, very outdated |
| **uvicorn** | 0.23.2 | 0.32.x+ | ⚠️ Medium | 9+ minor versions behind |
| **sqlalchemy** | 2.0.23 | 2.0.36+ | ⚠️ Low | Patch versions behind, should update |
| **cryptography** | 46.0.3 | Latest | ✅ Good | Recent version |
| **redis** | 7.0.1 | Latest | ✅ Good | Recent version |

#### Stability Risks

1. **Missing Dependency: `sentry-sdk`**
   - **Location:** `nerava-backend-v9/requirements.in` line 43
   - **Issue:** Listed in `.in` file but NOT in compiled `requirements.txt`
   - **Impact:** Sentry initialization will fail silently (code handles this gracefully, but monitoring is disabled)
   - **Evidence:** `nerava-backend-v9/app/main_simple.py:94` has fallback handling
   - **Fix:** Recompile requirements.txt: `pip-compile requirements.in`

2. **Version Constraint Mismatch**
   - **Location:** `nerava-backend-v9/requirements.in` line 27
   - **Constraint:** `httpx>=0.24.0,<0.27.0`
   - **Actual:** `httpx==0.26.0` in requirements.txt
   - **Status:** ✅ Valid (0.26.0 < 0.27.0), but constraint prevents upgrading to 0.27.x+

3. **Python Version Mismatch**
   - **Impact:** Different behavior between local dev, CI, and production
   - **Risk:** Type checking, runtime behavior differences
   - **Example:** `pyproject.toml` targets Python 3.10, but Docker uses 3.9

#### Operational Risks

1. **Missing Lockfile Verification**
   - **Issue:** No automated check that `requirements.txt` matches `requirements.in`
   - **Risk:** Developers may forget to recompile after editing `.in` files

2. **Floating Versions in requirements.in**
   - **Examples:**
     - `psycopg2-binary>=2.9.0` (line 13)
     - `PyJWT>=2.8.0` (line 17)
     - `cryptography>=41.0.0` (line 19)
   - **Risk:** Non-reproducible builds, potential breaking changes

3. **Missing Dev Dependencies**
   - **Issue:** `requirements-dev.in` lists `pytest-cov>=4.0.0` and `coverage>=7.0.0` but they're not in `requirements-dev.txt`
   - **Impact:** Coverage reporting may not work

### 3.2 JavaScript/TypeScript Ecosystem

#### Security Risks

| Package | Project(s) | Current Version | Latest Version | Risk Level |
|---------|-----------|----------------|----------------|------------|
| **next** | charger-portal, landing-page | 14.2.5 | 15.1.8+ | ⚠️ Low | 14.x still supported |
| **react** | charger-portal, landing-page | 18.3.1 | 19.2.0+ | ⚠️ Low | 18.x still supported |
| **react** | ui-admin | 18.2.0 | 19.2.0+ | ⚠️ Low | Slightly older |
| **react-dom** | charger-portal, landing-page | 18.3.1 | 19.2.0+ | ⚠️ Low | 18.x still supported |
| **react-dom** | ui-admin | 18.2.0 | 19.2.0+ | ⚠️ Low | Slightly older |
| **typescript** | charger-portal, landing-page | 5.5.3 | Latest | ✅ Good |
| **typescript** | ui-admin | 5.2.2 | Latest | ⚠️ Low | Patch versions behind |
| **eslint** | charger-portal, landing-page | 8.57.0 | 9.x+ | ⚠️ Low | 8.x still supported |
| **eslint** | ui-admin | 8.55.0 | 9.x+ | ⚠️ Low | Slightly older |
| **recharts** | charger-portal | 2.12.7 | 3.3.0+ | ⚠️ Medium | Major version behind |
| **recharts** | ui-mobile | 3.3.0 | Latest | ✅ Good |
| **@playwright/test** | ui-mobile | 1.56.1 | Latest | ✅ Good |

#### Stability Risks

1. **React Version Mismatch**
   - **ui-admin:** React 18.2.0
   - **Other projects:** React 18.3.1
   - **Impact:** Low, but inconsistent

2. **recharts Major Version Mismatch**
   - **charger-portal:** recharts 2.12.7
   - **ui-mobile:** recharts 3.3.0
   - **Impact:** Different APIs, potential breaking changes if code is shared

3. **No Node.js Version Pinning**
   - **Issue:** No `engines` field in package.json files
   - **Risk:** Different developers/CI may use different Node versions
   - **CI uses:** Node 20 (`.github/workflows/ci.yml`)

#### Operational Risks

1. **CI Workflow Issues**
   - **File:** `.github/workflows/ci.yml`
   - **Issue:** `continue-on-error: true` on both jobs
   - **Risk:** Tests may fail silently
   - **Impact:** False sense of security

2. **Missing TypeScript Strict Mode**
   - **Issue:** No explicit `strict: true` in tsconfig.json files (needs verification)
   - **Risk:** Type safety issues may go undetected

---

## 4. Upgrade / Refactor Recommendations

### 4.1 Python Backend Upgrades

#### P0: Fix Python Version Mismatch

**What to Change:**
- `nerava-backend-v9/Dockerfile`: Change `FROM python:3.9-slim` → `FROM python:3.10-slim`
- `nerava-backend-v9/Dockerfile.localdev`: Change `FROM python:3.9-slim` → `FROM python:3.10-slim`
- `nerava-backend-v9/nixpacks.toml`: Change `PYTHON_VERSION = "3.9"` → `PYTHON_VERSION = "3.10"`
- `.github/workflows/backend-tests.yml`: Already uses 3.10 ✅
- `.github/workflows/ci.yml`: Change `python-version: '3.11'` → `python-version: '3.10'`

**Why:**
- Python 3.9 reaches end-of-life in October 2025
- Python 3.10 is the current LTS version
- Consistency prevents "works on my machine" issues
- `pyproject.toml` already targets Python 3.10

**Blast Radius:** Medium
- Requires testing all Python code
- May need to update type hints if using Python 3.10+ features

**Verification Steps:**
```bash
cd nerava-backend-v9
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

#### P0: Add Missing sentry-sdk to requirements.txt

**What to Change:**
- `nerava-backend-v9/requirements.in`: Already has `sentry-sdk>=1.38.0` ✅
- `nerava-backend-v9/requirements.txt`: Missing (needs recompilation)

**Why:**
- Sentry is configured in code but dependency is missing
- Monitoring is silently disabled

**Blast Radius:** Low
- No code changes needed
- Just recompile requirements

**Verification Steps:**
```bash
cd nerava-backend-v9
pip-compile requirements.in
# Verify sentry-sdk appears in requirements.txt
grep sentry-sdk requirements.txt
```

#### P1: Upgrade FastAPI 0.103.2 → 0.115.x

**What to Change:**
- `nerava-backend-v9/requirements.in`: Change `fastapi==0.103.2` → `fastapi>=0.115.0,<0.116.0`

**Why (Context7 Validation):**
- FastAPI follows semantic versioning for 0.x releases
- Minor versions (0.103 → 0.115) may include breaking changes
- FastAPI 0.100.0+ supports Pydantic v2 (already using v2.5.0)
- Latest versions include security patches and performance improvements
- **Breaking Change Note:** FastAPI 0.70.0+ upgraded Starlette (already using 0.27.0, but should upgrade together)

**Blast Radius:** Medium-High
- Requires thorough testing of all API endpoints
- May need to update dependency injection patterns (yield/except handling)
- Starlette upgrade may introduce breaking changes

**Verification Steps:**
```bash
cd nerava-backend-v9
pip-compile requirements.in
pip install -r requirements.txt
pytest
# Manual API testing
curl http://localhost:8000/docs  # Verify OpenAPI docs load
```

#### P1: Upgrade Pydantic 2.5.0 → 2.12.x

**What to Change:**
- `nerava-backend-v9/requirements.in`: Change `pydantic==2.5.0` → `pydantic>=2.12.0,<3.0.0`

**Why (Context7 Validation):**
- Pydantic V2 policy: No breaking changes in minor releases (2.5 → 2.12)
- Bug fixes and performance improvements in newer versions
- Python 3.14 support in 2.12.x
- **Note:** Pydantic V2 dropped support for `email-validator<2.0.0` (already using 2.3.0 ✅)

**Blast Radius:** Low-Medium
- Pydantic V2 policy states no breaking changes in minor releases
- Should still test all model validation

**Verification Steps:**
```bash
cd nerava-backend-v9
pip-compile requirements.in
pip install -r requirements.txt
pytest
# Verify all Pydantic models validate correctly
```

#### P1: Review httpx Version Constraint

**What to Change:**
- `nerava-backend-v9/requirements.in`: Change `httpx>=0.24.0,<0.27.0` → `httpx>=0.26.0,<0.28.0`

**Why:**
- Current constraint prevents upgrading to 0.27.x+
- httpx 0.27.x may include security patches
- **Note:** Check FastAPI/Starlette compatibility with httpx 0.27.x before upgrading

**Blast Radius:** Low
- Only affects HTTP client usage
- Test external API calls

**Verification Steps:**
```bash
# Check FastAPI/Starlette compatibility with httpx 0.27.x
# Test all external HTTP calls (Stripe, Twilio, Google Auth, etc.)
```

#### P2: Upgrade Starlette 0.27.0 → 0.41.x

**What to Change:**
- `nerava-backend-v9/requirements.in`: Add `starlette>=0.41.0,<0.42.0` (if not transitive)

**Why:**
- Starlette is transitive via FastAPI, but explicit pinning ensures consistency
- Very outdated version (0.27.0 → 0.41.x is 14 minor versions)

**Blast Radius:** Medium
- Upgrade together with FastAPI
- Test middleware and routing

**Verification Steps:**
```bash
# Upgrade FastAPI first, then verify Starlette version
pip show starlette
```

#### P2: Upgrade uvicorn 0.23.2 → 0.32.x

**What to Change:**
- `nerava-backend-v9/requirements.in`: Change `uvicorn[standard]==0.23.2` → `uvicorn[standard]>=0.32.0,<0.33.0`

**Why:**
- 9+ minor versions behind
- Performance and security improvements

**Blast Radius:** Low
- ASGI server, mostly transparent to application code

**Verification Steps:**
```bash
# Test server startup and request handling
python -m uvicorn app.main_simple:app --reload
```

### 4.2 JavaScript/TypeScript Upgrades

#### P1: Pin Node.js Version

**What to Change:**
- All `package.json` files: Add `"engines": { "node": ">=20.0.0 <21.0.0" }`

**Why:**
- CI uses Node 20
- Ensures consistent behavior across environments
- Prevents "works on my machine" issues

**Blast Radius:** Low
- No code changes needed
- Just adds version constraint

**Verification Steps:**
```bash
# Test with Node 20
node --version  # Should be 20.x.x
npm ci
npm run build
```

#### P2: Standardize React Versions

**What to Change:**
- `ui-admin/package.json`: Change `"react": "^18.2.0"` → `"react": "^18.3.1"`
- `ui-admin/package.json`: Change `"react-dom": "^18.2.0"` → `"react-dom": "^18.3.1"`

**Why:**
- Consistency across projects
- React 18.3.1 includes bug fixes

**Blast Radius:** Low
- Patch version upgrade, should be safe

**Verification Steps:**
```bash
cd ui-admin
npm install
npm run build
npm run lint
```

#### P2: Upgrade recharts in charger-portal

**What to Change:**
- `charger-portal/package.json`: Change `"recharts": "^2.12.7"` → `"recharts": "^3.3.0"`

**Why:**
- Major version upgrade (2.x → 3.x)
- May include breaking API changes
- **Note:** Review recharts 3.x migration guide first

**Blast Radius:** Medium
- Major version upgrade
- Review all recharts usage in charger-portal

**Verification Steps:**
```bash
cd charger-portal
npm install recharts@^3.3.0
npm run build
# Manual testing of all charts
```

#### P2: Upgrade Next.js 14.2.5 → 14.3.x (or 15.x post-launch)

**What to Change:**
- `charger-portal/package.json`: Change `"next": "^14.2.5"` → `"next": "^14.3.0"`
- `landing-page/package.json`: Change `"next": "^14.2.5"` → `"next": "^14.3.0"`

**Why (Context7 Validation):**
- Next.js 14.x is still supported
- Next.js 15.x introduces breaking changes (async Request APIs)
- **Recommendation:** Stay on 14.x for launch, upgrade to 15.x post-launch

**Blast Radius:** Low (14.2 → 14.3) or Medium-High (14.x → 15.x)
- 14.2 → 14.3: Patch/minor upgrade, should be safe
- 14.x → 15.x: Breaking changes (async APIs)

**Verification Steps:**
```bash
cd charger-portal
npm install next@^14.3.0
npm run build
npm run start
# Test all pages and API routes
```

---

## 5. Standardization Plan

### 5.1 JavaScript Package Manager

**Recommendation: npm (current choice)**

**Rationale:**
- ✅ Already used consistently across all projects
- ✅ Lockfiles (`package-lock.json`) present in all projects
- ✅ No need to introduce yarn/pnpm complexity
- ✅ npm is the default Node.js package manager

**Action Items:**
- ✅ No changes needed (already standardized)

### 5.2 Python Dependency Management

**Recommendation: Continue using pip-tools (current choice)**

**Rationale:**
- ✅ Already in use (`requirements.in` → `requirements.txt`)
- ✅ Provides reproducible builds
- ✅ Separates direct vs transitive dependencies
- ✅ Works well with Docker and CI/CD

**Action Items:**
1. Add pre-commit hook or CI check to ensure `requirements.txt` is up-to-date:
   ```yaml
   # .github/workflows/check-requirements.yml
   - name: Check requirements.txt is up-to-date
     run: |
       pip-compile --dry-run requirements.in
   ```

2. Document the workflow in `nerava-backend-v9/README.md`:
   ```markdown
   ## Updating Dependencies
   
   To update dependencies:
   1. Edit `requirements.in` or `requirements-dev.in`
   2. Run `pip-compile requirements.in` or `pip-compile requirements-dev.in`
   3. Commit both `.in` and `.txt` files
   ```

### 5.3 Version Pinning Policy

**Production Dependencies:**
- ✅ Pin exact versions in `requirements.txt` (already done via pip-compile)
- ✅ Use `>=X.Y.0,<X.Y+1.0` in `requirements.in` for minor version flexibility
- ⚠️ Review floating versions (`>=`) and consider pinning critical dependencies

**Development Dependencies:**
- ✅ Same policy as production
- ✅ Can be more flexible with dev tools (e.g., `pytest>=8.4.0`)

**JavaScript Dependencies:**
- ✅ Use `^` for minor/patch updates (current practice)
- ✅ Pin exact versions in `package-lock.json` (automatic)
- ⚠️ Consider using `~` for patch-only updates in critical packages

### 5.4 Dependency Update Automation

**Recommendation: Use Renovate (preferred) or Dependabot**

**Renovate Configuration** (`.github/renovate.json`):
```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:base"],
  "packageRules": [
    {
      "matchUpdateTypes": ["major"],
      "enabled": false
    },
    {
      "matchManagers": ["pip-compile"],
      "matchFiles": ["requirements*.in"],
      "enabled": true
    },
    {
      "matchManagers": ["npm"],
      "matchUpdateTypes": ["minor", "patch"],
      "enabled": true,
      "automerge": true,
      "automergeType": "pr"
    }
  ]
}
```

**Dependabot Configuration** (`.github/dependabot.yml`):
```yaml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/charger-portal"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
  - package-ecosystem: "npm"
    directory: "/landing-page"
    schedule:
      interval: "weekly"
  - package-ecosystem: "npm"
    directory: "/ui-admin"
    schedule:
      interval: "weekly"
  - package-ecosystem: "npm"
    directory: "/ui-mobile"
    schedule:
      interval: "weekly"
  - package-ecosystem: "pip"
    directory: "/nerava-backend-v9"
    schedule:
      interval: "weekly"
    versioning-strategy: "lockfile-only"
```

---

## 6. Quick Wins (Under 2 Hours)

### ✅ Immediate Actions (No Code Changes)

1. **Add Node.js engines to all package.json** (15 min)
   - Add `"engines": { "node": ">=20.0.0 <21.0.0" }` to all 4 package.json files

2. **Recompile requirements.txt** (5 min)
   - Run `pip-compile requirements.in` to include sentry-sdk

3. **Standardize React versions** (10 min)
   - Update ui-admin to React 18.3.1

4. **Fix CI Python version** (5 min)
   - Change `.github/workflows/ci.yml` Python 3.11 → 3.10

5. **Add requirements.txt check to CI** (20 min)
   - Add step to verify requirements.txt is up-to-date

6. **Remove continue-on-error from CI** (5 min)
   - Remove `continue-on-error: true` from `.github/workflows/ci.yml`

7. **Document dependency update process** (30 min)
   - Add section to README about updating dependencies

**Total Time: ~90 minutes**

---

## 7. Proposed PR Plan

### PR1: "No Behavior Change" Dependency Hygiene (P0)

**Scope:**
- Fix Python version mismatch (standardize to 3.10)
- Add missing sentry-sdk to requirements.txt
- Pin Node.js version in all package.json files
- Fix CI Python version inconsistency
- Remove `continue-on-error` from CI workflows

**Files Changed:**
- `nerava-backend-v9/Dockerfile`
- `nerava-backend-v9/Dockerfile.localdev`
- `nerava-backend-v9/nixpacks.toml`
- `nerava-backend-v9/requirements.txt` (recompiled)
- All `package.json` files (add engines)
- `.github/workflows/ci.yml`

**Testing:**
- Run all tests in Python 3.10 environment
- Verify Docker builds successfully
- Verify CI passes without continue-on-error
- Verify Node.js version constraint works

**Risk:** Low (no dependency upgrades, just standardization)

---

### PR2: Safe Python Upgrades (P1)

**Scope:**
- Upgrade Pydantic 2.5.0 → 2.12.x
- Upgrade SQLAlchemy to latest 2.0.x patch
- Upgrade other patch/minor versions

**Files Changed:**
- `nerava-backend-v9/requirements.in`
- `nerava-backend-v9/requirements.txt` (recompiled)

**Testing:**
- Full test suite
- Manual API testing
- Verify all Pydantic models validate correctly

**Risk:** Low-Medium (Pydantic V2 policy says no breaking changes in minor releases)

---

### PR3: FastAPI & Starlette Upgrade (P1, Post-PR2)

**Scope:**
- Upgrade FastAPI 0.103.2 → 0.115.x
- Upgrade Starlette 0.27.0 → 0.41.x (transitive or explicit)
- Upgrade uvicorn 0.23.2 → 0.32.x

**Files Changed:**
- `nerava-backend-v9/requirements.in`
- `nerava-backend-v9/requirements.txt` (recompiled)
- Potentially code changes for breaking changes

**Testing:**
- Full test suite
- Manual API testing (all endpoints)
- Verify OpenAPI docs
- Test dependency injection patterns
- Test middleware

**Risk:** Medium-High (major version jumps, potential breaking changes)

---

### PR4: JavaScript Upgrades (P2, Post-Launch)

**Scope:**
- Standardize React versions
- Upgrade recharts in charger-portal (2.x → 3.x)
- Upgrade Next.js 14.2.5 → 14.3.x (or 15.x if ready)

**Files Changed:**
- `ui-admin/package.json`
- `charger-portal/package.json`
- `landing-page/package.json`
- Potentially code changes for recharts 3.x

**Testing:**
- Build all projects
- Manual UI testing
- Verify all charts render correctly

**Risk:** Medium (recharts major version upgrade)

---

## 8. Appendix

### 8.1 Top 50 Packages by Risk

**Python (High Risk - Outdated):**
1. starlette==0.27.0 (14+ minor versions behind)
2. fastapi==0.103.2 (20+ minor versions behind)
3. uvicorn==0.23.2 (9+ minor versions behind)
4. pydantic==2.5.0 (7+ minor versions behind)
5. sqlalchemy==2.0.23 (13+ patch versions behind)

**Python (Medium Risk - Review):**
6. httpx==0.26.0 (version constraint prevents upgrade)
7. python-jose==3.3.0 (check for updates)
8. passlib==1.7.4 (check for updates)
9. alembic==1.12.1 (check for updates)

**JavaScript (Low Risk - Current):**
- All packages are relatively current
- recharts version mismatch between projects

### 8.2 Packages That Gate Launch

**P0 (Must Fix):**
1. ✅ Python version standardization (prevents production issues)
2. ✅ sentry-sdk missing (monitoring disabled)
3. ✅ Node.js version pinning (prevents environment issues)

**P1 (Should Fix):**
1. ⚠️ FastAPI 0.103.2 (security patches available)
2. ⚠️ Starlette 0.27.0 (very outdated)
3. ⚠️ Pydantic 2.5.0 (bug fixes available)

### 8.3 Packages That Should Be Removed

**None identified** - All packages appear to be in use.

**Potential Cleanup:**
- Review if `python-dotenv==1.0.0` is still needed (pydantic-settings may handle this)
- Review if `python-multipart==0.0.20` is still needed (FastAPI may handle this)

---

## 9. Context7 Validation Summary

### FastAPI Validation
- ✅ Current version (0.103.2) is functional but outdated
- ⚠️ FastAPI 0.100.0+ supports Pydantic v2 (already using v2.5.0)
- ⚠️ FastAPI 0.70.0+ upgraded Starlette (breaking changes possible)
- ✅ FastAPI follows semantic versioning (minor versions may have breaking changes)

### Next.js Validation
- ✅ Next.js 14.2.5 is stable and supported
- ⚠️ Next.js 15.x introduces breaking changes (async Request APIs)
- ✅ Next.js 14.x requires Node.js 18.17+ (using Node 20 ✅)
- ✅ Next.js 14.x requires React 18.2.0+ (using 18.3.1 ✅)

### React Validation
- ✅ React 18.3.1 is stable
- ⚠️ React 19.x is available but Next.js 14.x uses React 18.x
- ✅ React 18.x is compatible with Next.js 14.x

### Pydantic Validation
- ✅ Pydantic V2 policy: No breaking changes in minor releases
- ✅ Pydantic 2.5.0 → 2.12.x should be safe
- ⚠️ Pydantic V1 not compatible with Python 3.14+ (using V2 ✅)
- ✅ email-validator>=2.0.0 required for Pydantic V2 (using 2.3.0 ✅)

### httpx Validation
- ✅ httpx 0.26.0 is functional
- ⚠️ Version constraint `<0.27.0` prevents security patches
- ✅ httpx follows semantic versioning
- ⚠️ Check FastAPI/Starlette compatibility before upgrading to 0.27.x+

---

## 10. Conclusion

**Overall Assessment:**
The repository has a solid foundation with consistent package manager usage and lockfiles. However, there are critical issues around Python version mismatches and missing dependencies that should be addressed before launch.

**Immediate Actions (P0):**
1. Standardize Python version to 3.10
2. Add sentry-sdk to requirements.txt
3. Pin Node.js version in all projects

**Short-term Actions (P1):**
1. Upgrade FastAPI and Pydantic (test thoroughly)
2. Review httpx version constraints

**Long-term Actions (P2):**
1. Standardize JavaScript package versions
2. Set up dependency update automation (Renovate/Dependabot)
3. Upgrade Next.js to 15.x post-launch

**Risk Level:** Medium (manageable with proper testing)

**Launch Readiness:** ✅ Ready after P0 fixes are applied

---

**Report Generated:** 2025-01-XX  
**Next Review:** After PR1 is merged









