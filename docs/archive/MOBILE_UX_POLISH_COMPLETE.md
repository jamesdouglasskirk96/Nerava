# Mobile Web UX Polish - Complete ✅

All 5 UX polish tasks have been implemented:

## 1. Bottom Nav - Even Icon Spacing ✅
- **File**: `ui-mobile/css/style.css`
- Updated `.tabbar` with `padding: 8px 0` for consistent spacing
- Tabs use `flex: 1` for even distribution
- All 3 icons (Wallet, Discover, Profile) evenly spaced and visually centered

## 2. Profile / Account Page Cleanup ✅
- **File**: `ui-mobile/js/pages/me.js`
- Removed Privacy Policy and Terms of Service links
- Account section now shows only:
  - Connect your EV
  - Notifications (placeholder)
  - Sign out button
- Clean, minimal layout

## 3. Discover - Resy-Style Merchant Cards ✅
- **Files**:
  - `ui-mobile/js/pages/explore.js` - New `renderMerchantCard()` function
  - `ui-mobile/css/style.css` - Resy-style card CSS
- Features:
  - Dark card background (#111827)
  - Left side: Name, rating (★ 4.6), category, price tier, distance
  - Two action buttons: "+20 Nova for survey" and "+40 Nova for visit"
  - Right side: Merchant image thumbnail (72x72px)
  - Horizontal scrolling container
  - JuiceLand @ Domain hardcoded as first card
  - Cards are 320-360px wide with scroll snap

## 4. Discover - Small Charge Chip ✅
- **Files**:
  - `ui-mobile/index.html` - Replaced card with chip markup
  - `ui-mobile/js/pages/explore.js` - New `initChargeChip()` and `updateChargeChip()`
  - `ui-mobile/css/style.css` - Chip styles
- Features:
  - Small pill-shaped chip (positioned at top: 118px, left: 16px)
  - Dark background with shadow for readability
  - Text: "Charge now, off-peak ends in 1h" (dynamic based on state)
  - Updates every minute
  - Replaces the large card we created earlier

## 5. Discover - Center Map Button ✅
- **Files**:
  - `ui-mobile/index.html` - Added button in map container
  - `ui-mobile/js/pages/explore.js` - `initMapCenterButton()` and `centerMapOnUser()`
  - `ui-mobile/css/style.css` - Button styles
- Features:
  - Floating button (⦿) positioned bottom-right
  - Dark background matching Resy style
  - Centers map on user location (or charger/fallback)
  - Smooth hover/active transitions

## CSS Additions

### Charge Chip
```css
.charge-chip {
  position: absolute;
  top: 118px;
  left: 16px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(17, 24, 39, 0.9);
  color: #f9fafb;
  /* ... */
}
```

### Resy-Style Cards
```css
.perk-card--resy {
  background: #111827;
  color: #f9fafb;
  /* Dark card with left/right layout */
}
```

### Center Map Button
```css
.map-center-btn {
  position: absolute;
  right: 16px;
  bottom: 140px;
  background: #111827;
  /* ... */
}
```

### Button Pills
```css
.btn-pill.btn-primary { /* Blue primary button */ }
.btn-pill.btn-light { /* Light outline button */ }
```

## Testing Checklist

✅ **Bottom Nav**: Icons evenly spaced, Discover visually centered  
✅ **Profile**: Only Connect EV, Notifications, Sign out visible  
✅ **Discover Charge Chip**: Small chip visible, readable, updates correctly  
✅ **Merchant Cards**: Resy-style dark cards, horizontal scroll, JuiceLand first  
✅ **Center Map**: Button visible, recenters map on click  

## Notes

- All existing functionality preserved
- No breaking changes to APIs or routes
- JuiceLand @ Domain is hardcoded as first merchant card
- Charge chip updates every minute with current state
- Center map button uses user location or falls back to charger/default

