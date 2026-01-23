# Dependency Fix Plan - Checklist Format

**Priority:** P0/P1/P2 fixes identified in `REPO_DEPENDENCY_AUDIT.md`  
**Estimated Time:** ~4-6 hours total  
**Risk Level:** Low (P0), Medium (P1), Low-Medium (P2)

---

## PR1: "No Behavior Change" Dependency Hygiene (P0)

**Goal:** Fix critical issues without changing dependency versions  
**Estimated Time:** 90 minutes  
**Risk:** Low

### Python Version Standardization

- [ ] **Update Dockerfile**
  - [ ] File: `nerava-backend-v9/Dockerfile`
  - [ ] Change: `FROM python:3.9-slim` → `FROM python:3.10-slim`
  - [ ] Verify: Docker build succeeds
  - [ ] Command: `docker build -t nerava-backend-test -f nerava-backend-v9/Dockerfile nerava-backend-v9/`

- [ ] **Update Dockerfile.localdev**
  - [ ] File: `nerava-backend-v9/Dockerfile.localdev`
  - [ ] Change: `FROM python:3.9-slim` → `FROM python:3.10-slim`
  - [ ] Verify: Docker build succeeds

- [ ] **Update nixpacks.toml**
  - [ ] File: `nerava-backend-v9/nixpacks.toml`
  - [ ] Change: `PYTHON_VERSION = "3.9"` → `PYTHON_VERSION = "3.10"`
  - [ ] Verify: No syntax errors

- [ ] **Update CI workflow**
  - [ ] File: `.github/workflows/ci.yml`
  - [ ] Change: `python-version: '3.11'` → `python-version: '3.10'`
  - [ ] Verify: CI passes

- [ ] **Verify Python 3.10 compatibility**
  - [ ] Create Python 3.10 virtual environment
  - [ ] Install dependencies: `pip install -r nerava-backend-v9/requirements.txt`
  - [ ] Run tests: `pytest nerava-backend-v9/tests/`
  - [ ] Verify no Python 3.10-specific issues

### Add Missing sentry-sdk

- [ ] **Recompile requirements.txt**
  - [ ] File: `nerava-backend-v9/requirements.in` (verify sentry-sdk is present)
  - [ ] Command: `cd nerava-backend-v9 && pip-compile requirements.in`
  - [ ] Verify: `grep sentry-sdk nerava-backend-v9/requirements.txt` shows the package
  - [ ] Commit: Both `requirements.in` and `requirements.txt`

- [ ] **Test Sentry initialization**
  - [ ] Install dependencies: `pip install -r nerava-backend-v9/requirements.txt`
  - [ ] Verify: `python -c "import sentry_sdk; print('OK')"` succeeds
  - [ ] Check: No warnings about missing sentry-sdk in app startup logs

### Node.js Version Pinning

- [ ] **charger-portal/package.json**
  - [ ] Add: `"engines": { "node": ">=20.0.0 <21.0.0" }`
  - [ ] Verify: `npm install` works with Node 20
  - [ ] Verify: `npm install` fails with Node <20 (if possible)

- [ ] **landing-page/package.json**
  - [ ] Add: `"engines": { "node": ">=20.0.0 <21.0.0" }`
  - [ ] Verify: `npm install` works with Node 20

- [ ] **ui-admin/package.json**
  - [ ] Add: `"engines": { "node": ">=20.0.0 <21.0.0" }`
  - [ ] Verify: `npm install` works with Node 20

- [ ] **ui-mobile/package.json**
  - [ ] Add: `"engines": { "node": ">=20.0.0 <21.0.0" }`
  - [ ] Verify: `npm install` works with Node 20

### CI Workflow Improvements

- [ ] **Remove continue-on-error**
  - [ ] File: `.github/workflows/ci.yml`
  - [ ] Remove: `continue-on-error: true` from both jobs
  - [ ] Verify: CI fails appropriately if tests fail

- [ ] **Add requirements.txt check**
  - [ ] File: `.github/workflows/ci.yml` or create new workflow
  - [ ] Add step to verify requirements.txt is up-to-date:
    ```yaml
    - name: Check requirements.txt is up-to-date
      working-directory: nerava-backend-v9
      run: |
        pip install pip-tools
        pip-compile --dry-run requirements.in
    ```

### Testing Checklist

- [ ] **Backend Tests**
  - [ ] Run: `pytest nerava-backend-v9/tests/`
  - [ ] Verify: All tests pass
  - [ ] Verify: No Python version warnings

- [ ] **Docker Build**
  - [ ] Build: `docker build -t nerava-backend-test -f nerava-backend-v9/Dockerfile nerava-backend-v9/`
  - [ ] Verify: Build succeeds
  - [ ] Verify: Container starts: `docker run -p 8000:8000 nerava-backend-test`

- [ ] **Frontend Builds**
  - [ ] charger-portal: `cd charger-portal && npm ci && npm run build`
  - [ ] landing-page: `cd landing-page && npm ci && npm run build`
  - [ ] ui-admin: `cd ui-admin && npm ci && npm run build`
  - [ ] ui-mobile: `cd ui-mobile && npm ci` (no build script)

- [ ] **CI Verification**
  - [ ] Push PR and verify CI passes
  - [ ] Verify no continue-on-error masking failures

---

## PR2: Safe Python Upgrades (P1)

**Goal:** Upgrade Pydantic and other safe packages  
**Estimated Time:** 2 hours  
**Risk:** Low-Medium

### Upgrade Pydantic

- [ ] **Update requirements.in**
  - [ ] File: `nerava-backend-v9/requirements.in`
  - [ ] Change: `pydantic==2.5.0` → `pydantic>=2.12.0,<3.0.0`
  - [ ] Recompile: `pip-compile requirements.in`

- [ ] **Verify Pydantic upgrade**
  - [ ] Install: `pip install -r nerava-backend-v9/requirements.txt`
  - [ ] Verify version: `python -c "import pydantic; print(pydantic.__version__)"` shows 2.12.x
  - [ ] Run tests: `pytest nerava-backend-v9/tests/`
  - [ ] Check: No Pydantic validation errors

- [ ] **Test Pydantic models**
  - [ ] Search for all Pydantic models: `grep -r "BaseModel" nerava-backend-v9/app/`
  - [ ] Verify: All models instantiate correctly
  - [ ] Test: Create test instances of each model

### Upgrade SQLAlchemy (Patch Version)

- [ ] **Update requirements.in**
  - [ ] File: `nerava-backend-v9/requirements.in`
  - [ ] Change: `sqlalchemy==2.0.23` → `sqlalchemy>=2.0.23,<2.1.0`
  - [ ] Recompile: `pip-compile requirements.in`
  - [ ] Verify: Latest 2.0.x patch version is installed

- [ ] **Test database operations**
  - [ ] Run migrations: `alembic upgrade head`
  - [ ] Verify: No migration errors
  - [ ] Test: Create/read/update/delete operations
  - [ ] Run tests: `pytest nerava-backend-v9/tests/`

### Other Safe Upgrades

- [ ] **Review other patch/minor upgrades**
  - [ ] Check: `pip list --outdated` in virtual environment
  - [ ] Update patch versions in requirements.in
  - [ ] Recompile: `pip-compile requirements.in`
  - [ ] Test: Full test suite

### Testing Checklist

- [ ] **Full Test Suite**
  - [ ] Run: `pytest nerava-backend-v9/tests/`
  - [ ] Verify: All tests pass
  - [ ] Check: No deprecation warnings

- [ ] **API Testing**
  - [ ] Start server: `python -m uvicorn app.main_simple:app`
  - [ ] Test: All API endpoints
  - [ ] Verify: OpenAPI docs load: `http://localhost:8000/docs`
  - [ ] Test: Request/response validation

- [ ] **Database Testing**
  - [ ] Run migrations: `alembic upgrade head`
  - [ ] Test: CRUD operations
  - [ ] Verify: No SQLAlchemy warnings

---

## PR3: FastAPI & Starlette Upgrade (P1, Post-PR2)

**Goal:** Upgrade FastAPI and related packages  
**Estimated Time:** 3-4 hours  
**Risk:** Medium-High

### Pre-Upgrade Research

- [ ] **Review FastAPI changelog**
  - [ ] Check: FastAPI 0.103.2 → 0.115.x changelog
  - [ ] Identify: Breaking changes
  - [ ] Document: Migration steps needed

- [ ] **Review Starlette changelog**
  - [ ] Check: Starlette 0.27.0 → 0.41.x changelog
  - [ ] Identify: Breaking changes
  - [ ] Document: Middleware/routing changes

- [ ] **Review uvicorn changelog**
  - [ ] Check: uvicorn 0.23.2 → 0.32.x changelog
  - [ ] Identify: Configuration changes

### Upgrade FastAPI

- [ ] **Update requirements.in**
  - [ ] File: `nerava-backend-v9/requirements.in`
  - [ ] Change: `fastapi==0.103.2` → `fastapi>=0.115.0,<0.116.0`
  - [ ] Recompile: `pip-compile requirements.in`

- [ ] **Verify FastAPI upgrade**
  - [ ] Install: `pip install -r nerava-backend-v9/requirements.txt`
  - [ ] Verify version: `python -c "import fastapi; print(fastapi.__version__)"` shows 0.115.x
  - [ ] Check: Starlette version (should upgrade automatically)

### Upgrade Starlette (if needed)

- [ ] **Check Starlette version**
  - [ ] Command: `pip show starlette`
  - [ ] If < 0.41.x, add explicit pin: `starlette>=0.41.0,<0.42.0`
  - [ ] Recompile: `pip-compile requirements.in`

### Upgrade uvicorn

- [ ] **Update requirements.in**
  - [ ] File: `nerava-backend-v9/requirements.in`
  - [ ] Change: `uvicorn[standard]==0.23.2` → `uvicorn[standard]>=0.32.0,<0.33.0`
  - [ ] Recompile: `pip-compile requirements.in`

### Code Changes (if needed)

- [ ] **Check dependency injection**
  - [ ] Search: `grep -r "yield" nerava-backend-v9/app/`
  - [ ] Review: Dependencies with `yield` and `except`
  - [ ] Fix: Ensure exceptions are re-raised (FastAPI 0.70.0+ requirement)

- [ ] **Check middleware**
  - [ ] Review: All middleware usage
  - [ ] Verify: Compatibility with Starlette 0.41.x
  - [ ] Fix: Any breaking changes

- [ ] **Check routing**
  - [ ] Review: All route definitions
  - [ ] Verify: No deprecated patterns
  - [ ] Fix: Any breaking changes

### Testing Checklist

- [ ] **Full Test Suite**
  - [ ] Run: `pytest nerava-backend-v9/tests/`
  - [ ] Verify: All tests pass
  - [ ] Check: No deprecation warnings

- [ ] **API Testing**
  - [ ] Start server: `python -m uvicorn app.main_simple:app`
  - [ ] Test: All API endpoints
  - [ ] Verify: OpenAPI docs load: `http://localhost:8000/docs`
  - [ ] Test: Request/response validation
  - [ ] Test: Error handling

- [ ] **Dependency Injection Testing**
  - [ ] Test: All dependencies with `yield`
  - [ ] Verify: Exception handling works correctly
  - [ ] Test: Dependency cleanup

- [ ] **Middleware Testing**
  - [ ] Test: All middleware
  - [ ] Verify: Request/response processing
  - [ ] Test: Error handling in middleware

- [ ] **Performance Testing**
  - [ ] Compare: Response times before/after upgrade
  - [ ] Verify: No performance regressions

---

## PR4: JavaScript Upgrades (P2, Post-Launch)

**Goal:** Standardize and upgrade JavaScript packages  
**Estimated Time:** 2-3 hours  
**Risk:** Medium

### Standardize React Versions

- [ ] **Update ui-admin/package.json**
  - [ ] File: `ui-admin/package.json`
  - [ ] Change: `"react": "^18.2.0"` → `"react": "^18.3.1"`
  - [ ] Change: `"react-dom": "^18.2.0"` → `"react-dom": "^18.3.1"`
  - [ ] Install: `npm install`
  - [ ] Build: `npm run build`
  - [ ] Test: `npm run lint`

### Upgrade recharts in charger-portal

- [ ] **Research recharts 3.x migration**
  - [ ] Review: recharts 3.x migration guide
  - [ ] Identify: Breaking API changes
  - [ ] Document: Changes needed

- [ ] **Update charger-portal/package.json**
  - [ ] File: `charger-portal/package.json`
  - [ ] Change: `"recharts": "^2.12.7"` → `"recharts": "^3.3.0"`
  - [ ] Install: `npm install`

- [ ] **Update code (if needed)**
  - [ ] Search: `grep -r "recharts" charger-portal/app/`
  - [ ] Review: All recharts usage
  - [ ] Fix: Any breaking API changes
  - [ ] Test: All charts render correctly

- [ ] **Verify charts**
  - [ ] Build: `npm run build`
  - [ ] Start: `npm start`
  - [ ] Manual test: All charts in UI
  - [ ] Verify: No console errors

### Upgrade Next.js (Optional - Post-Launch)

- [ ] **Research Next.js 15.x**
  - [ ] Review: Next.js 15.x migration guide
  - [ ] Identify: Breaking changes (async Request APIs)
  - [ ] Decide: Stay on 14.x or upgrade to 15.x

- [ ] **If upgrading to 14.3.x (safe)**
  - [ ] File: `charger-portal/package.json`
  - [ ] Change: `"next": "^14.2.5"` → `"next": "^14.3.0"`
  - [ ] File: `landing-page/package.json`
  - [ ] Change: `"next": "^14.2.5"` → `"next": "^14.3.0"`
  - [ ] Install: `npm install` in both projects
  - [ ] Build: `npm run build` in both projects
  - [ ] Test: All pages and API routes

- [ ] **If upgrading to 15.x (requires code changes)**
  - [ ] Review: Async Request APIs migration
  - [ ] Update: All `cookies()`, `headers()`, `params()` usage to async
  - [ ] Update: All `searchParams` usage to async
  - [ ] Test: All pages and API routes

### Testing Checklist

- [ ] **Build All Projects**
  - [ ] charger-portal: `npm run build`
  - [ ] landing-page: `npm run build`
  - [ ] ui-admin: `npm run build`
  - [ ] ui-mobile: `npm ci` (no build script)

- [ ] **Lint All Projects**
  - [ ] charger-portal: `npm run lint`
  - [ ] landing-page: `npm run lint`
  - [ ] ui-admin: `npm run lint`

- [ ] **Manual UI Testing**
  - [ ] charger-portal: Test all pages and charts
  - [ ] landing-page: Test all pages
  - [ ] ui-admin: Test all pages
  - [ ] ui-mobile: Test all functionality

- [ ] **Type Checking**
  - [ ] charger-portal: `npm run type-check`
  - [ ] landing-page: `npm run type-check`
  - [ ] ui-admin: `npm run build` (includes type checking)

---

## General Checklist (All PRs)

### Pre-PR

- [ ] **Create feature branch**
  - [ ] Branch: `fix/dependency-audit-pr1` (or pr2, pr3, pr4)
  - [ ] Base: `main` or `master`

- [ ] **Review audit report**
  - [ ] Read: `docs/REPO_DEPENDENCY_AUDIT.md`
  - [ ] Understand: All changes being made
  - [ ] Identify: Potential risks

### During Development

- [ ] **Make changes incrementally**
  - [ ] One change at a time
  - [ ] Test after each change
  - [ ] Commit frequently

- [ ] **Document changes**
  - [ ] Update: CHANGELOG.md (if exists)
  - [ ] Add: Comments for non-obvious changes
  - [ ] Document: Any workarounds needed

### Pre-Commit

- [ ] **Run tests**
  - [ ] Backend: `pytest nerava-backend-v9/tests/`
  - [ ] Frontend: Build and lint all projects
  - [ ] Verify: All tests pass

- [ ] **Check for warnings**
  - [ ] Python: No deprecation warnings
  - [ ] JavaScript: No console warnings
  - [ ] TypeScript: No type errors

- [ ] **Verify dependencies**
  - [ ] Python: `pip check` (no conflicts)
  - [ ] JavaScript: `npm audit` (no critical vulnerabilities)

### PR Submission

- [ ] **Write PR description**
  - [ ] Title: Clear and descriptive
  - [ ] Description: Link to audit report
  - [ ] Checklist: Copy relevant section from this file
  - [ ] Testing: Document test results

- [ ] **Request review**
  - [ ] Assign: Relevant reviewers
  - [ ] Label: `dependencies`, `p0`/`p1`/`p2`
  - [ ] Mention: Any breaking changes

### Post-Merge

- [ ] **Monitor CI/CD**
  - [ ] Verify: CI passes
  - [ ] Verify: Deployment succeeds
  - [ ] Monitor: Production logs for errors

- [ ] **Update documentation**
  - [ ] Update: README.md if needed
  - [ ] Update: Deployment docs if needed
  - [ ] Update: Developer setup docs if needed

---

## Notes

- **Testing Strategy:** Test thoroughly after each PR before moving to the next
- **Rollback Plan:** Each PR should be independently revertible
- **Communication:** Notify team before making breaking changes
- **Timeline:** P0 fixes should be done before launch, P1/P2 can be done post-launch

---

**Last Updated:** 2025-01-XX  
**Status:** Ready for implementation









