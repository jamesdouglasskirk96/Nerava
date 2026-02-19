CLAUDE PROMPT — Generate Cursor Plan to Reach 10/10 (Merchant Portal + Onboarding)

You are Claude Code. Use the UX review below and produce a Cursor‑ready implementation prompt to get the merchant portal + onboarding from 6.5/10 to 10/10. Keep scope tight and aligned to current architecture.

Review (source of truth):
- claude-cursor-prompts/2026-01-27_merchant-portal-onboarding-review.md

Your output MUST include:
1) Scope & Priorities (P0 must‑fix vs P1/P2)
2) Step‑by‑step implementation with exact file paths and concrete edits/snippets
3) Backend needs (new endpoints or schema changes) with file locations
4) QA / Verification checklist
5) Guardrails (no refactors, no new deps, no design overhauls)

Focus areas to fix:
- Remove hardcoded mock data in Overview
- Add real session management (token expiry handling + logout)
- Gate DemoNav behind env flag
- Fix non‑functional pages (Settings/Billing/PrimaryExperience/SelectLocation)
- Replace alert() with inline error UI
- Wire CustomerExclusiveView to real API
- Fix Exclusives progress bar or remove it until data exists
- Send all fields in CreateExclusive payload

Constraints:
- Keep the portal honest (no fake data)
- If backend endpoints are missing, propose minimal additions
- Provide code‑level detail sufficient to implement

Keep it concise and executable.
