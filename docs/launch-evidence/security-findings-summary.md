# Security Scan Findings Summary

**Generated**: 2025-01-27  
**Purpose**: Summarize Critical/High security findings with remediation plans

## Scan Execution Status

| Tool | Status | Report File |
|------|--------|-------------|
| gitleaks | ❌ Not Installed | N/A - Tool not available |
| bandit | ✅ Completed | `nerava-backend-v9/bandit-report.json` |
| semgrep | ❌ Failed | Execution error (pysemgrep not found) |
| npm audit (ui-mobile) | ✅ Completed | `npm-audit-ui-mobile.json` |
| npm audit (charger-portal) | ✅ Completed | `npm-audit-charger-portal.json` |
| npm audit (landing-page) | ✅ Completed | `npm-audit-landing-page.json` |
| npm audit (ui-admin) | ✅ Completed | `npm-audit-ui-admin.json` |

## Critical/High Findings

### Bandit - Python Security Scanner

**Total Issues**: 6 HIGH severity issues

#### Finding 1: Weak MD5 Hash in Cache Layers
- **Tool**: bandit
- **Severity**: HIGH
- **File**: `app/cache/layers.py:254`
- **Issue**: Use of weak MD5 hash for security
- **Remediation**: Add `usedforsecurity=False` parameter to MD5 usage, or migrate to SHA-256
- **PR Plan**: 
  ```python
  # Current:
  hashlib.md5(key.encode()).hexdigest()
  # Fix:
  hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()
  # OR better:
  hashlib.sha256(key.encode()).hexdigest()
  ```

#### Finding 2: Weak MD5 Hash in Cache Layers (Second Instance)
- **Tool**: bandit
- **Severity**: HIGH
- **File**: `app/cache/layers.py:265`
- **Issue**: Use of weak MD5 hash for security
- **Remediation**: Same as Finding 1

#### Finding 3: Weak SHA1 Hash in Apple Wallet Pass
- **Tool**: bandit
- **Severity**: HIGH
- **File**: `app/services/apple_wallet_pass.py:274`
- **Issue**: Use of weak SHA1 hash for security
- **Remediation**: Add `usedforsecurity=False` or migrate to SHA-256
- **PR Plan**:
  ```python
  # Current:
  hashlib.sha1(data).hexdigest()
  # Fix:
  hashlib.sha1(data, usedforsecurity=False).hexdigest()
  # OR better:
  hashlib.sha256(data).hexdigest()
  ```

#### Finding 4: Weak MD5 Hash in Hubs Dynamic
- **Tool**: bandit
- **Severity**: HIGH
- **File**: `app/services/hubs_dynamic.py:10`
- **Issue**: Use of weak MD5 hash for security
- **Remediation**: Same as Finding 1

#### Finding 5: Weak MD5 Hash in Idempotency
- **Tool**: bandit
- **Severity**: HIGH
- **File**: `app/services/idempotency.py:16`
- **Issue**: Use of weak MD5 hash for security
- **Remediation**: Same as Finding 1

#### Finding 6: Weak MD5 Hash in Purchases
- **Tool**: bandit
- **Severity**: HIGH
- **File**: `app/services/purchases.py:137`
- **Issue**: Use of weak MD5 hash for security
- **Remediation**: Same as Finding 1

### npm audit - JavaScript Dependencies

#### ui-mobile
- **Status**: ✅ No vulnerabilities found
- **Total dependencies**: 71 (40 prod, 32 dev)
- **Vulnerabilities**: 0

#### charger-portal
- **Status**: ⚠️ HIGH vulnerabilities found
- **Package**: `glob` (via `@next/eslint-plugin-next` → `eslint-config-next`)
- **Severity**: HIGH
- **Fix Available**: Update `eslint-config-next` to version `16.1.1` (semver major)
- **PR Plan**: 
  ```bash
  cd charger-portal
  npm install eslint-config-next@16.1.1
  ```
- **Note**: This is a semver major update, may require code changes

#### landing-page
- **Status**: ⚠️ HIGH vulnerabilities found
- **Package**: `glob` (via `@next/eslint-plugin-next` → `eslint-config-next`)
- **Severity**: HIGH
- **Fix Available**: Update `eslint-config-next` to version `16.1.1` (semver major)
- **PR Plan**: 
  ```bash
  cd landing-page
  npm install eslint-config-next@16.1.1
  ```

#### ui-admin
- **Status**: ⚠️ MODERATE vulnerabilities found
- **Package**: `esbuild` (via `vite`)
- **Severity**: MODERATE
- **Issue**: esbuild enables any website to send requests to dev server (CWE-346)
- **Fix Available**: Update `vite` to version `7.3.0` (semver major)
- **PR Plan**:
  ```bash
  cd ui-admin
  npm install vite@7.3.0
  ```
- **Note**: Development server vulnerability, lower priority for production builds

### gitleaks - Secret Scanning
- **Status**: ❌ Tool not installed
- **Action Required**: Install gitleaks: `brew install gitleaks`
- **Manual Command**: `gitleaks detect --source . --verbose`
- **Risk**: Cannot verify no secrets committed to repository

### semgrep - OWASP Top Ten
- **Status**: ❌ Execution failed
- **Error**: `pysemgrep` not found in PATH
- **Action Required**: Fix semgrep installation or run manually
- **Manual Command**: `semgrep --config=p/owasp-top-ten nerava-backend-v9/ --json`

## Summary Table

| Tool | Critical | High | Medium | Low | Total |
|------|----------|------|--------|-----|-------|
| bandit | 0 | 6 | 0 | 540 | 546 |
| npm audit (ui-mobile) | 0 | 0 | 0 | 0 | 0 |
| npm audit (charger-portal) | 0 | 1 | 0 | 0 | 1 |
| npm audit (landing-page) | 0 | 1 | 0 | 0 | 1 |
| npm audit (ui-admin) | 0 | 0 | 1 | 0 | 1 |
| gitleaks | ❌ Not run | - | - | - | - |
| semgrep | ❌ Failed | - | - | - | - |

## Remediation Priority

### Priority 1 (Critical - Must Fix Before Launch)
1. **Bandit Finding 1-6**: Replace weak MD5/SHA1 hashes with SHA-256 or add `usedforsecurity=False`
   - Files: `app/cache/layers.py`, `app/services/apple_wallet_pass.py`, `app/services/hubs_dynamic.py`, `app/services/idempotency.py`, `app/services/purchases.py`
   - Estimated time: 2-4 hours
   - Risk: Security vulnerability if hashes used for security purposes

### Priority 2 (High - Should Fix Before Launch)
2. **npm audit (charger-portal, landing-page)**: Update `eslint-config-next` to 16.1.1
   - Estimated time: 1-2 hours (may require code changes due to semver major)
   - Risk: HIGH severity vulnerability in dependency

### Priority 3 (Medium - Can Fix Post-Launch)
3. **npm audit (ui-admin)**: Update `vite` to 7.3.0
   - Estimated time: 1 hour
   - Risk: Development server vulnerability, lower priority for production

### Priority 4 (Missing Tools - Should Complete)
4. **gitleaks**: Install and run secret scan
   - Estimated time: 30 minutes
   - Risk: Cannot verify no secrets in codebase

5. **semgrep**: Fix installation and run OWASP scan
   - Estimated time: 30 minutes
   - Risk: Missing OWASP Top Ten vulnerability detection






