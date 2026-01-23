# Environment Runtime Checklist

**Generated**: 2025-01-27  
**Purpose**: Detect missing runtimes and provide exact macOS install commands

## Runtime Detection Results

| Runtime | Status | Path | Install Command | Verification Command |
|---------|--------|------|-----------------|---------------------|
| python3 | ✅ Found | `/usr/bin/python3` | Already installed | `python3 --version` |
| pip3 | ✅ Found | `/usr/bin/pip3` | Already installed | `pip3 --version` |
| node | ✅ Found | `/opt/homebrew/bin/node` | Already installed | `node --version` |
| npm | ✅ Found | `/opt/homebrew/bin/npm` | Already installed | `npm --version` |
| psql | ❌ Missing | N/A | `brew install postgresql` | `psql --version` |
| gitleaks | ❌ Missing | N/A | `brew install gitleaks` | `gitleaks version` |
| bandit | ❌ Missing | N/A | `pip3 install bandit` | `bandit --version` |
| semgrep | ❌ Missing | N/A | `brew install semgrep` or `pip3 install semgrep` | `semgrep --version` |

## Install Commands for Missing Runtimes

Run these commands to install missing tools:

```bash
# PostgreSQL client (for psql)
brew install postgresql

# Secret scanning tool
brew install gitleaks

# Python security scanner
pip3 install bandit

# Static analysis tool (OWASP scanning)
brew install semgrep
# OR alternative:
# pip3 install semgrep
```

## Verification Commands

After installation, verify each tool:

```bash
psql --version
gitleaks version
bandit --version
semgrep --version
```






