# Nerava Cleanup Completion - Remaining Tasks

**Date:** 2026-01-23
**Prerequisite:** `2026-01-23_repo-cleanup-implementation.md` (P0-P3 commits completed)
**Status:** Git tracking clean, but physical directories and root files remain

---

## Problem Summary

The initial cleanup successfully:
- Removed secrets from git tracking
- Updated .gitignore
- Created .env.example files
- Removed build artifacts from tracking
- Created docs/security/secrets.md

But left incomplete:
- **Duplicate directories still exist on disk** (removed from git, not deleted)
- **78 markdown files remain at root** (target: 1 README.md)
- **docs/ has files in root** instead of organized subdirectories

---

## Task 1: Delete Archived Directories

These directories were already backed up to `backups/archived-dirs/` and removed from git tracking. Now delete them from disk:

```bash
cd /Users/jameskirk/Desktop/Nerava

# Verify backups exist first
ls -la backups/archived-dirs/

# Delete duplicate directories
rm -rf "nerava-backend-v9"
rm -rf "nerava-backend-v9 2"
rm -rf "landing-page"
rm -rf "landing-page 2"
rm -rf "nerava-app-driver"
rm -rf "ui-admin"

# Delete empty/abandoned directories (if they still exist)
rm -rf "src-figma"
rm -rf "src_admin"
rm -rf "src_landing_figma_new"
rm -rf "WYC-search"
rm -rf "nerava_pwa_demo"
```

**Verification:**
```bash
ls -d */ | grep -E "nerava-backend-v9|landing-page|nerava-app-driver|ui-admin"
# Expected: empty output (no matches)
```

---

## Task 2: Move ALL Root Markdown Files to docs/

Move every .md file from root to docs/archive/ EXCEPT README.md:

```bash
cd /Users/jameskirk/Desktop/Nerava

# List what will be moved (review first)
ls -1 *.md | grep -v "^README.md$"

# Move all except README.md
for f in *.md; do
  if [ "$f" != "README.md" ]; then
    mv "$f" docs/archive/
  fi
done
```

**Verification:**
```bash
ls *.md
# Expected: only README.md
```

---

## Task 3: Organize docs/ Directory

Move files from docs/ root into appropriate subdirectories:

```bash
cd /Users/jameskirk/Desktop/Nerava/docs

# Move runbooks to deployment/
mv *_RUNBOOK*.md deployment/ 2>/dev/null || true
mv OPS_*.md deployment/ 2>/dev/null || true
mv LAUNCH_*.md deployment/ 2>/dev/null || true
mv OBSERVABILITY.md deployment/ 2>/dev/null || true

# Move audits and analysis to architecture/
mv *_AUDIT*.md architecture/ 2>/dev/null || true
mv *_ANALYSIS*.md architecture/ 2>/dev/null || true
mv REPO_DEPENDENCY*.md architecture/ 2>/dev/null || true

# Move validation/test reports to archive/
mv *_VALIDATION*.md archive/ 2>/dev/null || true
mv *_REPORT*.md archive/ 2>/dev/null || true
mv *_SUMMARY*.md archive/ 2>/dev/null || true
mv BASELINE_*.md archive/ 2>/dev/null || true
mv COVERAGE_*.md archive/ 2>/dev/null || true
mv DELETED_*.md archive/ 2>/dev/null || true
mv FRONTEND_*.md archive/ 2>/dev/null || true
mv IMPLEMENTATION_*.md archive/ 2>/dev/null || true
mv LEGACY_*.md archive/ 2>/dev/null || true
mv MCP_*.md archive/ 2>/dev/null || true
mv TEST_*.md archive/ 2>/dev/null || true

# Move ChatGPT/Cursor analysis files to archive/
mv CHATGPT_*.md archive/ 2>/dev/null || true
mv CURSOR_*.md archive/ 2>/dev/null || true

# Move remaining misc files to archive/
mv analytics.md archive/ 2>/dev/null || true
mv dr.md archive/ 2>/dev/null || true
mv multi-dc.md archive/ 2>/dev/null || true
mv operations.md archive/ 2>/dev/null || true
```

**Verification:**
```bash
ls -1 docs/*.md
# Expected: only README.md in docs/ root
```

---

## Task 4: Update docs/README.md

Ensure docs/README.md accurately reflects the final structure:

```bash
cat > docs/README.md << 'EOF'
# Nerava Documentation

## Directory Structure

```
docs/
├── deployment/      # Deployment guides, runbooks, operations
├── architecture/    # System design, audits, dependencies
├── api/            # API endpoint documentation
├── security/       # Secrets management, security guidelines
├── archive/        # Historical docs, completed work, old analyses
└── launch-evidence/ # Launch validation evidence
```

## Quick Links

### Operations
- [OPS Alarms Runbook](./deployment/OPS_ALARMS_RUNBOOK.md)
- [Prod Validation Runbook](./deployment/PROD_VALIDATION_RUNBOOK.md)
- [Launch Go/No-Go](./deployment/LAUNCH_GO_NO_GO.md)

### Architecture
- [Repo Dependency Audit](./architecture/REPO_DEPENDENCY_AUDIT.md)

### Security
- [Secrets Management](./security/secrets.md)

## Archive

Old documentation (completed fixes, analyses, deprecated content) is in `./archive/`.
EOF
```

---

## Task 5: Clean Up Prompt Archives

Move any remaining cursor prompt files at root:

```bash
cd /Users/jameskirk/Desktop/Nerava

# Check for any remaining prompt files at root
ls cursor-prompt-*.txt 2>/dev/null

# Move if any exist
mv cursor-prompt-*.txt claude-cursor-prompts/archive/ 2>/dev/null || true
```

---

## Task 6: Final Verification

```bash
cd /Users/jameskirk/Desktop/Nerava

echo "=== Root Directory Contents ==="
ls -1

echo ""
echo "=== Root Markdown Files ==="
ls *.md 2>/dev/null || echo "None (expected: README.md only)"

echo ""
echo "=== Directory Count ==="
ls -d */ | wc -l
echo "directories (target: ~15-20)"

echo ""
echo "=== Docs Structure ==="
ls docs/

echo ""
echo "=== Files in docs/ root ==="
ls docs/*.md 2>/dev/null || echo "Only README.md (good)"

echo ""
echo "=== Duplicate Directories Check ==="
ls -d */ | grep -E "nerava-backend-v9|landing-page|nerava-app-driver|ui-admin" || echo "None found (good)"

echo ""
echo "=== Disk Usage ==="
du -sh .
```

---

## Expected Final State

### Root Directory (~15-20 items)
```
/Users/jameskirk/Desktop/Nerava/
├── .github/
├── .claude/
├── .cursor/
├── apps/
├── backend/
├── backups/           (gitignored)
├── charger-portal/
├── charts/
├── claude-cursor-prompts/
├── docs/
├── e2e/
├── infra/
├── mcp/
├── mobile/
├── packages/
├── postman/
├── reports/
├── scripts/
├── static/
├── tests/
├── tools/
├── wallet-pass/
├── README.md
├── docker-compose.yml
├── pyproject.toml
└── [other config files]
```

### docs/ Directory
```
docs/
├── README.md          (index)
├── deployment/        (15-20 files)
├── architecture/      (5-10 files)
├── api/              (endpoint docs)
├── security/         (secrets.md)
├── archive/          (100+ historical files)
└── launch-evidence/  (validation evidence)
```

### Root Markdown Files
- `README.md` only

---

## Success Criteria Checklist

- [ ] No duplicate directories on disk (nerava-backend-v9*, landing-page*, nerava-app-driver, ui-admin)
- [ ] Only README.md at repository root
- [ ] docs/ root contains only README.md and subdirectories
- [ ] All historical docs moved to docs/archive/
- [ ] Runbooks and deployment docs in docs/deployment/
- [ ] Audits and architecture docs in docs/architecture/
- [ ] Directory count at root is ~15-20 (down from 150+)
- [ ] `du -sh .` shows ~1.5GB or less

---

## Commit

After all tasks complete:

```bash
git add -A
git status

# Should show minimal changes (mostly file moves within docs/)
# If git tracks the moves, commit:

git commit -m "Complete cleanup: delete archived dirs, organize all documentation

- Removed duplicate directories from disk (already in backups/)
- Moved 77 root markdown files to docs/archive/
- Organized docs/ into deployment/, architecture/, archive/ subdirs
- Root now has only README.md

Final state: ~20 root directories, clean documentation hierarchy"
```

---

**End of Cleanup Completion Prompt**
