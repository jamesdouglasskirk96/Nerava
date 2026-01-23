# Frontend Testing Plan

**Date:** 2025-01-XX  
**Status:** Testing infrastructure exists, plan for expansion

## Current State

### Test Infrastructure

**ui-mobile/** (Primary PWA Frontend):
- ✅ **Jest** configured (`jest.config.js`)
- ✅ **Playwright** configured (`playwright.config.ts`)
- ✅ **Test files exist:**
  - `tests/e2e.spec.ts` - Playwright E2E tests
  - `tests/wallet.test.js` - Wallet component tests
  - `tests/wallet-polling.test.js` - Polling logic tests
  - `tests/merchant-detail.test.js` - Merchant detail tests
  - `tests/demo/autorun.spec.ts` - Demo autorun tests

**charger-portal/** (Next.js Portal):
- Has `package.json` - needs test setup verification

**landing-page/**:
- Has `package.json` - needs test setup verification

## What We Will Test Next

### Priority 1: Critical User Flows (PWA)

1. **Authentication Flow**
   - Magic link email submission
   - Token verification and session creation
   - Logout and session cleanup

2. **Wallet Operations**
   - Balance display and updates
   - Transaction history
   - Redemption flow

3. **Merchant Discovery**
   - Nearby merchants list
   - Merchant detail view
   - QR code scanning

4. **Charging Session**
   - Session start/stop
   - Real-time balance updates
   - Session verification

### Priority 2: Component Tests

1. **Core Components**
   - Modal component (open/close, content)
   - Toast notifications
   - Deal chips (countdown, display)

2. **API Integration**
   - API error handling
   - Network failure recovery
   - Loading states

### Priority 3: E2E Flows

1. **Complete User Journey**
   - Register → Charge → Earn → Redeem
   - Merchant onboarding flow
   - Payment processing flow

## How to Run Tests

### Jest Unit Tests
```bash
cd ui-mobile
npm test
```

### Playwright E2E Tests
```bash
cd ui-mobile
npx playwright test
```

### Run All Frontend Tests
```bash
cd ui-mobile
npm run test:all  # If configured, otherwise run individually
```

## What's Deferred and Why

### Deferred Items

1. **Full Component Test Coverage**
   - **Why:** Current tests cover critical paths. Full coverage can be added incrementally.
   - **When:** Post-launch, as part of regular development cycle

2. **Visual Regression Testing**
   - **Why:** Not critical for MVP launch. Can be added later for UI consistency.
   - **When:** When design system stabilizes

3. **Performance Testing**
   - **Why:** Performance is acceptable for MVP. Optimization can come later.
   - **When:** When scaling becomes a concern

4. **Accessibility Testing**
   - **Why:** Basic accessibility is in place. Full audit can be done post-launch.
   - **When:** As part of accessibility audit initiative

## Test Coverage Goals

- **Current:** ~20% (estimated based on existing test files)
- **Target:** 40% for critical paths (auth, wallet, payments)
- **Timeline:** Incremental improvement over next 3 months

## Next Steps

1. ✅ Document existing test infrastructure (this doc)
2. ⏳ Add tests for auth flow (magic link)
3. ⏳ Add tests for critical API error paths
4. ⏳ Expand E2E test coverage for core user flows
5. ⏳ Set up CI/CD to run frontend tests automatically

## Notes

- Frontend tests are separate from backend coverage goals
- Backend coverage target (55%) does not include frontend code
- Frontend testing is complementary to backend API tests










