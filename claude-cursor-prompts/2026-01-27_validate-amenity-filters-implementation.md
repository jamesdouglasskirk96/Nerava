CLAUDE PROMPT — Validate AmenityVotes + PrimaryFilters Implementation

You are Claude Code. Validate the implementation below against the Nerava‑Figma‑With‑Amenities design and the iOS driver web app. Confirm correctness, highlight any gaps or regressions, and provide a focused QA checklist.

Implementation Summary (to validate):
- New components:
  - apps/driver/src/components/shared/AmenityVotes.tsx
  - apps/driver/src/components/shared/PrimaryFilters.tsx
- Integrations:
  - apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx
    - AmenityVotes inserted after SocialProofBadge
    - Voting modal with thumbs up/down
    - localStorage persistence, default amenities when API missing
  - apps/driver/src/components/DriverHome/DriverHome.tsx
    - PrimaryFilters shown for PRE_CHARGING + CHARGING_ACTIVE
    - Filters apply to merchant list before grouping
- Types:
  - apps/driver/src/types/index.ts adds optional amenities on MerchantInfo
- Filtering logic:
  - filterMerchantsByAmenities uses AND logic across selected filters
  - Supports bathroom/food/wifi/pets now; music/patio placeholders

Your output MUST include:
1) Figma alignment check (what matches, what deviates)
2) Functional validation (does logic align with UX intent)
3) Potential bugs or edge cases
4) QA checklist (what to test)
5) Final verdict: “ship” / “needs fixes”

Constraints:
- Focus on UX parity with Figma.
- Note any missing assets, spacing, or state behavior that diverges from Figma.
- Keep it concise and actionable.
