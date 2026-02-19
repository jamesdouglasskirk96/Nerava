CLAUDE PROMPT — Admin Portal Gaps Review (apps/admin)

You are Claude Code. Review the admin portal and identify gaps in UX, functionality, and backend integration. Provide a concise gap report and a Cursor‑ready implementation prompt to close the top gaps.

Scope:
- apps/admin (frontend)
- Relevant backend endpoints used by admin portal

Your output MUST include:
1) UX score (0–10)
2) Top 3 wins
3) Top 5 gaps (file + line evidence)
4) Production readiness verdict
5) Cursor‑ready implementation plan (exact files + steps)

Constraints:
- Keep scope tight; no refactors, no new deps
- If backend endpoints are missing, call them out with exact path suggestions

If unsure, list files you need to inspect.
