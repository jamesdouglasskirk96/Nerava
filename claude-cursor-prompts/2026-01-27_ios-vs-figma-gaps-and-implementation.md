CLAUDE PROMPT — iOS vs Figma Gaps + Cursor Implementation Prompt

You are Claude Code. Identify all gaps between the iOS driver app and the Nerava‑Figma‑With‑Amenities implementation, then produce a Cursor‑ready implementation prompt to close those gaps (or explicitly defer if not in scope). Use the comparison summary below as a starting point but verify against the codebase and Figma files.

Comparison Summary (initial):
- Missing in iOS:
  1) Amenity voting feature (AmenityVotes component)
  2) Primary filters (Bathroom, Food, WiFi, Pets, Music, Patio)
- iOS already has better loading/empty states and a11y than Figma

Figma references:
- Nerava-Figma-With-Amenities/app/components/AmenityVotes.tsx
- Nerava-Figma-With-Amenities/app/components/PrimaryFilters.tsx
- Nerava-Figma-With-Amenities/app/App.tsx (layered nav model)

Your output MUST include:
A) Verified gap list (what’s missing in iOS vs Figma)
B) Decision: implement now vs defer (with rationale)
C) Cursor implementation prompt with exact files, steps, and snippets
D) QA checklist (UI/UX verification)
E) Guardrails: no refactors, no new deps, keep scope tight

Constraints:
- Keep UX consistent with Figma.
- If React Router architecture differs, adapt components to current iOS web app structure, not vice‑versa.
- Focus on implementing amenity voting + primary filters first if they’re the only gaps.

Keep it concise and actionable.
