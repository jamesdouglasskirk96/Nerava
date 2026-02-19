CURSOR PROMPT — Fix Remaining Merchant Portal Bugs (P0)

You are Claude Code. Fix the two P0 bugs called out in the regrade report. Keep scope tight: apps/merchant only.

Bugs to fix:
1) `fetchAPI` not exported
   - File: apps/merchant/app/services/api.ts
   - Fix: add `export` to the `fetchAPI` function declaration so CustomerExclusiveView can import it.

2) React hooks violation in CustomerExclusiveView
   - File: apps/merchant/app/components/CustomerExclusiveView.tsx
   - Fix: move `useState` for timeRemaining to top-level with other hooks, and set initial value in a useEffect when session loads.

Output MUST include:
- Exact file edits/snippets
- Confirmation of build/TypeScript impact
- QA checklist (CustomerExclusiveView load + countdown)

Guardrails:
- No refactors
- No new deps
- apps/merchant only
