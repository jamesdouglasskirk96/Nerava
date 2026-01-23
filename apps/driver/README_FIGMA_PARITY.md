# Figma UI Parity - Mock Mode Documentation

This document explains how to use the Figma mock mode for offline development and testing without backend dependencies.

## Overview

The `nerava-ui` app now supports a complete mock data layer that enables:
- Offline development without backend server
- Deterministic fixtures for consistent testing
- Visual parity with Figma designs
- Fast iteration without network dependencies

## Running Mock Mode

### Method 1: Environment Variable

Create a `.env.local` file (gitignored) in `nerava-ui/`:

```env
VITE_UI_MODE=figma_mock
```

Then run:
```bash
npm run dev
```

### Method 2: URL Query Parameter

Add `?mock=1` to any URL:
```
http://localhost:5173/wyc?mock=1
http://localhost:5173/pre-charging?mock=1
http://localhost:5173/m/mock_starbucks_001?mock=1&session_id=mock_session_12345
```

### Method 3: LocalStorage

Open browser console and run:
```javascript
localStorage.setItem('UI_MODE', 'figma_mock')
location.reload()
```

## Demo Mode Toggle

Use `?demo=1` query parameter to enable demo mode, which adds a toggle button in the header to switch between Charging and Pre-Charging states:

```
http://localhost:5173/wyc?demo=1&mock=1
```

The toggle button appears in the header and allows quick switching between states for demos.

## Mock Data Structure

### Fixtures Location

Mock data is defined in `src/mock/fixtures.ts`:

- **Merchants**: 6 merchants with categories (Coffee, Food, Fitness, Retail, Pets, Grocery)
- **Chargers**: 3 chargers with nearby experiences
- **Merchant Details**: Full details for each merchant
- **Session IDs**: Deterministic session IDs for testing

### Updating Fixtures

Edit `src/mock/fixtures.ts` to modify mock data:

```typescript
export const MOCK_MERCHANTS: MerchantSummary[] = [
  {
    place_id: 'mock_starbucks_001',
    name: 'Starbucks Reserve',
    // ... other fields
  },
  // Add more merchants...
]
```

After updating fixtures, the app will automatically use the new data in mock mode.

## Mock API Functions

Mock API functions are in `src/mock/mockApi.ts`:

- `captureIntentMock()` - Returns merchants or chargers based on state
- `getMerchantDetailsMock()` - Returns merchant details
- `activateExclusiveMock()` - Returns wallet activation response
- `getChargerDetailsMock()` - Returns charger with nearby experiences

All functions simulate network delays (50-150ms) for realistic feel.

## Design Tokens

Design tokens are centralized in `src/ui/tokens.ts`:

- Colors (Facebook blue, grays, semantic colors)
- Spacing (4px scale)
- Border radius (card, modal, pill, button)
- Shadows (card, card-lg, modal)
- Typography (font sizes, weights, line heights)
- Breakpoints (mobile-first)

Components use these tokens via Tailwind classes that match the token values.

## Category Logos

Category logos are defined in `src/ui/categoryLogos.tsx`:

- Automatically maps merchant categories to icons
- Provides fallback when `photo_url` or `logo_url` is missing
- Categories: Coffee, Food, Fitness, Retail, Pets, Grocery, Entertainment, Pharmacy, Other

The `PhotoPlaceholder` component renders category logos when photos are missing.

## Screens

### 1. Charging State (`/wyc`)

- Shows merchants in carousel (1 primary + 2 secondary)
- Carousel rotates with arrows and dots
- Category logo fallbacks for missing photos
- Click merchant card → Merchant Details

### 2. Pre-Charging State (`/pre-charging`)

- Shows charger cards with nearby experiences
- Same carousel component as charging state
- "Navigate to Charger" CTA (stub for now)

### 3. Merchant Details (`/m/:merchantId`)

- Hero image with category logo fallback
- "Activate Exclusive" button (was "Add to Wallet")
- Distance card and hours card
- Perk description

### 4. Exclusive Activated Modal

- Title: "Exclusive Activated"
- Subtitle: "Active for the next 60 minutes"
- CTA: "View Wallet" (shows stub for now)

### 5. Preferences Modal

- Triggered after first activation in session
- "Want better matches next time?"
- Category checkboxes
- Saves to localStorage (no backend call)
- Only shows once per session

## Running Playwright Tests

### Prerequisites

Install Playwright (if not already installed):
```bash
cd nerava-ui
npm install -D @playwright/test playwright
npx playwright install
```

### Run Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI
npm run test:e2e:ui

# Run specific test file
npx playwright test e2e/tests/charging-state.spec.ts
```

### Test Files

- `e2e/tests/charging-state.spec.ts` - Charging state screen
- `e2e/tests/pre-charging-state.spec.ts` - Pre-charging state screen
- `e2e/tests/merchant-details.spec.ts` - Merchant details screen
- `e2e/tests/exclusive-modal.spec.ts` - Exclusive activated modal
- `e2e/tests/preferences-modal.spec.ts` - Preferences modal
- `e2e/tests/carousel.spec.ts` - Carousel rotation

### Screenshot Comparisons

Screenshots are saved to `e2e/test-results/` on failure. To update baselines:

```bash
npx playwright test --update-snapshots
```

## What's NOT Wired to Backend

The following features are **local-only** and don't make backend calls:

1. **Mock Mode**: All API calls use fixtures when `VITE_UI_MODE=figma_mock`
2. **Preferences**: Saved to localStorage, not sent to backend
3. **Wallet Pass Preview**: "View Wallet" shows alert stub
4. **Charger Navigation**: "Navigate to Charger" shows alert stub
5. **Category Logos**: Local SVG icons, no image CDN
6. **Demo Mode Toggle**: Pure frontend routing, no backend state

## Visual Parity Checklist

When comparing to Figma, verify:

- [ ] Safe area spacing (top/bottom padding)
- [ ] Header alignment (NERAVA left, state pill right)
- [ ] Title/subtitle typography (font size, weight, line height, color)
- [ ] Card shadows and radius (16px for cards, 20px for modals)
- [ ] Pills: distance pill, Sponsored pill, Exclusive pill (colors, padding, radius)
- [ ] Icon sizes (24px, 32px, etc.)
- [ ] Button padding and radius (8px radius)
- [ ] Modals: backdrop opacity (60% black), spacing, typography
- [ ] Carousel: arrow button size, dot indicator size/spacing

## Troubleshooting

### Mock mode not working

1. Check `.env.local` has `VITE_UI_MODE=figma_mock`
2. Check URL has `?mock=1`
3. Check browser console for `[API]` logs - should say "Using mock API"
4. Clear browser cache and reload

### Carousel not rotating

1. Ensure multiple merchants in fixtures
2. Check browser console for errors
3. Verify carousel controls are visible

### Category logos not showing

1. Check merchant has `types` array
2. Verify `normalizeCategory()` function in `categoryLogos.tsx`
3. Check SVG icons render correctly

### Preferences modal not showing

1. Clear sessionStorage: `sessionStorage.clear()`
2. Ensure you've activated exclusive at least once
3. Check modal is not blocked by other modals

## Development Workflow

1. **Start dev server**: `npm run dev`
2. **Enable mock mode**: Add `VITE_UI_MODE=figma_mock` to `.env.local`
3. **Update fixtures**: Edit `src/mock/fixtures.ts`
4. **Test changes**: Refresh browser
5. **Run tests**: `npm run test:e2e`
6. **Compare to Figma**: Use visual parity checklist

## Next Steps

To wire to real backend:

1. Remove `VITE_UI_MODE=figma_mock` from `.env.local`
2. Ensure backend is running on `http://localhost:8001`
3. Update `src/services/api.ts` to remove mock mode checks (optional)
4. Test with real API endpoints

## Files Reference

- Mock data: `src/mock/fixtures.ts`, `src/mock/mockApi.ts`, `src/mock/types.ts`
- Design tokens: `src/ui/tokens.ts`, `src/ui/theme.ts`
- Category logos: `src/ui/categoryLogos.tsx`
- API integration: `src/services/api.ts`
- Components: `src/components/`
- Tests: `e2e/tests/`

