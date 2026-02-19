CLAUDE PROMPT — iOS ↔ Backend E2E Validation + Production Gap Report

You are Claude Code. Validate end‑to‑end flows between the iOS app (native shell + driver web app) and the backend. Produce a production gap analysis report and concrete next steps with code‑level detail sufficient to write a Cursor implementation prompt to reach 10/10.

Scope:
- iOS native shell (SwiftUI + WKWebView) + driver web app
- Backend API + DB
- Focus on real production flows, not UI polish

Your output MUST include:
1) End‑to‑end flow map (OTP auth → discovery → merchant details → activation → in‑transit → at‑merchant → verify/complete)
2) For each step: exact frontend/native file(s) and backend endpoint(s) used
3) Gaps/blockers (P0/P1) with exact file paths and missing backend fields/endpoints
4) Data contract mismatches (schema fields missing or named differently)
5) Security/auth gaps (token scope, auth required but missing, rate limits, etc.)
6) Observability/testing gaps (missing tests, missing logs)
7) Concrete next steps: a Cursor‑ready implementation checklist with file‑level detail and suggested snippets

Constraints:
- Keep scope tight; no refactors.
- If something is uncertain, mark it and suggest the exact file or command to confirm.

Use repo paths when referencing code.
