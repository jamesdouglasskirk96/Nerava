CURSOR PROMPT — Fix Backend Gaps for iOS “Real” Functionality

You are Claude Code. Implement the backend gaps identified in the backend gaps analysis so the iOS app is fully real/production‑functional. Use the analysis as ground truth; focus on P0 blockers first.

Source analysis doc:
- claude-cursor-prompts/2026-01-27_backend-gaps-for-ios-reality.md

Priorities:
P0 (must fix)
1) Amenity Votes Backend API
   - Add DB model + migration
   - Add API endpoints to submit and fetch amenity votes
   - Aggregate counts for bathroom/wifi (and future fields)

2) MerchantInfo.amenities field
   - Add to backend schema/response
   - Populate from amenity votes aggregation

P1 (if time)
3) Primary Filters backend support (filter params)
4) Favorites sync on load

P2 (optional)
5) Push notification integration
6) Filter persistence

Your output MUST include:
A) Concrete implementation plan (files + steps)
B) Exact endpoints + schemas
C) DB migration steps
D) QA checklist (API + app behavior)
E) Guardrails (no refactors, keep scope tight)

Keep it concise and executable.
