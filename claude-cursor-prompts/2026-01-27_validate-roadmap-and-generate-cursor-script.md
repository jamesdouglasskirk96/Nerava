CLAUDE PROMPT — Validate Roadmap + Generate Cursor Script (10/10 UX)

You are Claude Code. Validate the roadmap below and then generate a Cursor-ready implementation script to execute it. Treat the roadmap as a proposal; confirm what’s correct, flag gaps, and output a final, concrete implementation plan with exact files and steps.

Roadmap (to validate and implement):
1) Replace all alert() calls with inline error states
   - Files: apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx (6 alerts)
            apps/driver/src/components/DriverHome/DriverHome.tsx (8 alerts)
            apps/driver/src/components/WalletSuccess/WalletSuccessModal.tsx (1 alert)
   - Create ErrorModal component
   - Use ErrorModal/ErrorBanner with clear recovery actions

2) Add refresh CTAs to empty states
   - Files: apps/driver/src/components/PreCharging/PreChargingScreen.tsx
            apps/driver/src/components/WhileYouCharge/WhileYouChargeScreen.tsx
   - Add Refresh button wired to refetchIntent()/refetchMerchants()

3) Fix expiration modal routing
   - File: apps/driver/src/components/ExclusiveActiveView/ExclusiveActiveView.tsx
   - Change “Secure a New Spot” to navigate to merchant detail (navigate(`/m/${merchant.place_id}`))

Polish:
4) OTP inline loading feedback
   - File: apps/driver/src/components/ActivateExclusiveModal/ActivateExclusiveModal.tsx
   - Add spinner/progress feedback near OTP input

5) Touch target audit (44x44)
   - Verify and pad icon buttons

6) Network error recovery states
   - Offline banner + retry, cache last successful state, pull-to-refresh

7) Improve empty state messaging

Your output MUST include:
A) Validation: what’s correct, what’s missing, and any file path corrections needed
B) Cursor script: step-by-step implementation with exact file edits, and any new components
C) QA checklist: focused tests per change
D) Guardrails: no refactors, keep scope tight, no new deps

Keep it concise and actionable.
