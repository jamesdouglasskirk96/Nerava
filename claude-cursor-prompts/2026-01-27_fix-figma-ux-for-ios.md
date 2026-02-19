CLAUDE PROMPT — Fix UX Gaps for iOS App (Cross‑check with Figma)

You are Claude Code. Fix the UX issues below in the iOS app (driver web app inside WKWebView). You MUST cross‑check against the Nerava‑Figma‑With‑Amenities design and only implement changes consistent with that design. If a proposed fix would deviate from Figma, call it out and propose the closest Figma‑aligned alternative.

UX Findings (from Nerava‑Figma‑With‑Amenities review):
- Missing loading states (skeletons unused)
- Missing empty states with actionable CTAs
- Error handling uses browser alert() calls
- Accessibility gaps (icon buttons missing aria labels; no reduced motion)

Where alert() calls were found in the Figma project:
- ActiveExclusive.tsx: “Call merchant”, “Code copied”
- AccountPage.tsx: “Settings coming soon”, “Referral link copied”
- App.tsx: “Logged out”, “Favorites coming soon”

Your job:
1) Validate these issues against the current iOS web app code and the Figma design.
2) Implement Figma‑aligned fixes in the iOS web app (apps/driver) only.
3) Produce a Cursor‑ready implementation plan with exact file edits and snippets.

Requirements:
- Replace alert() with inline error UI (ErrorModal/ErrorBanner/Toast) that matches Figma.
- Add skeleton loading states and shimmer animation consistent with Figma.
- Add empty states with CTAs (Refresh / Clear filters / Browse chargers) matching Figma.
- Add a11y improvements (aria labels, reduced motion).
- Do NOT introduce new deps or redesign layouts.

Output format:
A) Figma cross‑check summary (what matches, what deviates, decisions)
B) Implementation plan (files + concrete changes)
C) QA checklist (screens + behaviors)
D) Guardrails (no refactors, no new deps)

Keep it tight and actionable.
