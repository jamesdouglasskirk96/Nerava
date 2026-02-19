CLAUDE PROMPT — Generate Cursor Plan to Reach 10/10 (Merchant Portal)

You are Claude Code. Use the latest validation below to produce a Cursor‑ready implementation plan to reach 10/10. All P0s are closed; focus on the remaining non‑blockers and any missing backend endpoint required for full functionality.

Latest validation summary:
- P0 bugs fixed (fetchAPI export + hooks order)
- Ship verdict: Ship (8.0/10)
- Non‑blockers to fast‑follow:
  1) Overview “Reserve Primary Experience” button is a no‑op in production (Overview.tsx:202)
  2) merchant_id fallback to 'current_merchant' string literal in several components (causes 404 if localStorage empty)
  3) Backend endpoint GET /v1/exclusive/{session_id} does not exist yet (CustomerExclusiveView shows error)

Your output MUST include:
1) Scope & priorities (P1/P2)
2) Step‑by‑step implementation (exact files + snippets)
3) Backend additions required (if any) with file paths
4) QA checklist
5) Guardrails (no refactors, no new deps)

Keep it concise and executable.
