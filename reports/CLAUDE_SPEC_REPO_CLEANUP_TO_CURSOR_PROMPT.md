# Claude Spec: Generate Cursor Prompt for Repo Cleanup (Nerava)

**Purpose:** You (Claude Code) will produce a **single Cursor-ready implementation prompt** that cleans up the Nerava monorepo based on `CLEANUP_REPORT.md`, without breaking builds or deployments.

**Hard rule:** The Cursor prompt must be **safe**: no secret values, no irreversible deletes without backups, and no “big bang” refactors. Prefer `git mv`, staged commits, and verification steps after each stage.

---

## Inputs You Must Use

1. **Cleanup report (source of truth):** `CLEANUP_REPORT.md` (provided by user).
2. **Repo root:** `/Users/jameskirk/Desktop/Nerava`
3. **Goal:** Make the repo demo/launch-ready by removing dangerous files, consolidating duplicate directories, and standardizing env + docs.

---

## Target Outcome

By end of cleanup:

1. **No private keys or secrets are tracked** in git (and the working tree is clean).
2. **One canonical backend directory** (no duplicate `nerava-backend-v9 2`, no shadow copies).
3. **One canonical driver app directory** (no duplicate stale exports).
4. **All env secrets moved out of repo**; only `.env.example` remains.
5. **Docs are consolidated** into `/docs` and `/specs`, and stray “prompt” files are organized.
6. **CI can run** (lint/build/tests) and local dev starts for:
   - backend
   - driver
   - merchant portal
   - admin portal

---

## What You Must Produce (Deliverables)

### Deliverable A — Cursor Implementation Prompt (Primary)
A single prompt Cursor can execute end-to-end, containing:

- **Scope**
- **Ordered phases** (P0 security → P1 consolidation → P2 clean artifacts → P3 docs)
- **Exact file operations** (`git mv`, deletions, renames)
- **Verification commands** after each phase
- **Rollback instructions** (how to revert if anything breaks)
- **Success criteria checklist**

### Deliverable B — Repo Cleanup Manifest (Secondary, inside the same Cursor prompt)
Inside the Cursor prompt, include a “manifest” section listing:

- Files to delete
- Files to move
- Files to keep
- Files to ignore going forward (gitignore additions)

---

## Constraints / Guardrails

### Security
- **Do not paste actual secrets** from any `.env` or key file into outputs.
- If the report names a private key file:
  - Cursor prompt should **remove it from git history tracking** (if committed) using `git rm --cached` (and optionally recommend git filter-repo), and then delete locally after backing up.
- Add/verify `.gitignore` entries for:
  - `*.key`, `*.p12`, `*.pem`, `cookies.txt`, `.env`, `.env.*`, `*.backup`, `*.bak`
  - `node_modules`, `dist`, `.vite`, `coverage`, `playwright-report`, `.DS_Store`

### Repo integrity
- Prefer **`git mv`** so history is preserved.
- No new architecture. This is cleanup, not redesign.
- Don’t change runtime behavior unless it’s required to remove secrets/hardcoding.

### Operational safety
- Before deleting, **create a `/backups/`** folder (gitignored) and copy suspicious files there first.
- Any “corrupted directory” listed in the report must be handled by:
  - verifying it’s redundant (diff directory trees)
  - keeping the newest canonical version
  - archiving the rest to `/backups/` and then removing from repo

---

## Required Phases to Include in the Cursor Prompt

### Phase P0 — Critical Security Remediation (Must be first)
Use the report’s “CRITICAL SECURITY ISSUES” section as the checklist.

Cursor prompt must:
1. Locate and remove from git tracking:
   - `nerava.key`, `nerava-pass.key`, `cookies.txt`
   - any `.env`, `.env.backup`, `.env.bak`, `.env*` files
2. Add `.gitignore` protections so these can’t be re-added.
3. Create `.env.example` files where missing, with placeholders only.
4. Add a short `/docs/security/secrets.md` explaining:
   - where secrets live (App Runner env vars, GitHub Secrets)
   - how to rotate compromised secrets immediately

**Verification:** `git status`, `git ls-files | rg -n "(\.env$|\.key$|cookies\.txt)"`

---

### Phase P1 — Consolidate Duplicate / Shadow Directories
From `CLEANUP_REPORT.md`, identify duplicated or legacy directories (examples the report mentions):
- `nerava-backend-v9 2/` vs `backend/`
- duplicated driver directories (`nerava-app-driver/`, exports, copies)
- any other “corrupted directories” or duplicate builds

Cursor prompt must:
1. Determine which directory is canonical by:
   - most recent commits
   - referenced in deployment scripts
   - referenced in package.json / docker / App Runner build context
2. Migrate changes into canonical dirs using `git mv` where appropriate.
3. Archive the losers into `/backups/` (gitignored) and remove from repo.

**Verification:** `rg -n "nerava-backend-v9 2|backend/" -S` and ensure no references point to removed dirs.

---

### Phase P2 — Remove Generated / Heavy Artifacts (Recover space)
Use report’s “recoverable space” targets. Remove:
- `dist/`, build artifacts, caches
- downloaded exports, old zips, `node_modules` if present in repo
- duplicate images and temporary files listed by report

**Verification:** `git status`, `du -sh` on key folders, ensure `.gitignore` covers artifacts.

---

### Phase P3 — Docs + Specs Canonicalization
Create/organize:
- `/docs/` (how-to, runbooks, ops)
- `/specs/` (product/engineering specs)
- `/prompts/` (Cursor/Claude prompts, versioned)

Move scattered “prompt” files into `/prompts/` with consistent naming:
- `YYYY-MM-DD_<area>_<topic>.md`

Add:
- `/docs/README.md` index linking to key runbooks
- `/specs/README.md` index linking to current v1 specs
- Root `README.md` pointing to docs and how to run each app

**Verification:** links resolve; no stale paths.

---

## Cleanups You Must Explicitly Address (from report + current state)

1. **Hardcoded Google Places API key** (report highlights it’s hardcoded):
   - Remove hardcoded key
   - Use `GOOGLE_PLACES_API_KEY` env var everywhere
   - Add to `.env.example` and App Runner env var checklist

2. **Multiple portal apps using mock data**:
   - Keep feature behavior the same, but ensure mocks are clearly isolated (e.g., `mock/` folder) and not mixed into prod code paths.
   - If the cleanup requires it, ensure `VITE_API_BASE_URL` is the only base URL source.

3. **Deploy scripts and workflows paths**:
   - Update GitHub Actions / scripts if they reference removed directories.
   - Ensure CI still runs after cleanup.

---

## Cursor Prompt Output Format Requirements

In the final Cursor prompt you generate, use this exact structure:

1. **Goal**
2. **Non-goals**
3. **Assumptions**
4. **Phase Plan (P0–P3)** with checklists and exact commands
5. **Manifest**
6. **Verification**
7. **Rollback**

Keep it **diff-friendly** and **command-driven**.

---

## Quality Bar

Before you finish, you must run (or instruct Cursor to run) these checks:

### Backend
- `python -m py_compile` for touched python files
- `pytest` if present (or skip with justification)

### Frontends (driver/admin/merchant)
- `npm ci` (or `pnpm i` if repo uses pnpm)
- `npm run lint`
- `npm run build`

### Repo hygiene
- `git status` clean
- `rg` check that secrets are not present
- ensure `.env.example` exists for each app

---

## Final Note

This cleanup is not optional. If keys were ever committed, assume they’re compromised and **rotate them** (Twilio, SendGrid, JWT, encryption keys, etc.). In the Cursor prompt, include a “Rotation checklist” section with provider-specific steps (without linking or pasting secrets).

