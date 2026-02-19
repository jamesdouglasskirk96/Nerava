CLAUDE PROMPT — Validate Merchant Portal Bug Fixes + Regrade

You are Claude Code. Validate the two bug fixes just applied and regrade merchant portal readiness. Confirm the fixes in code with file/line evidence, and report any remaining issues.

Bugs that were fixed:
1) `fetchAPI` not exported
   - File: apps/merchant/app/services/api.ts
   - Expected: `export async function fetchAPI<T>(...)`

2) React hooks violation in CustomerExclusiveView
   - File: apps/merchant/app/components/CustomerExclusiveView.tsx
   - Expected: `timeRemaining` useState at top-level; countdown useEffect initializes from session

Your output MUST include:
- Pass/Fail for each fix with evidence (file + line)
- Updated readiness score (0–10) and ship verdict
- Any remaining blockers or regressions
- Minimal next steps (if any)

Keep it concise and rigorous.
