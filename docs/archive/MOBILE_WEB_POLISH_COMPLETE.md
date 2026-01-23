# Mobile Web Polish Pass - Implementation Complete ✅

All 5 polish tasks have been completed:

## 1. Bottom Navigation - Even Spacing ✅
- **File**: `ui-mobile/css/style.css`
- Changed `.tab` from `width: 20%` to `flex: 1` for even spacing
- Added console log: `[Nav][Tabs] Layout: flex spacing enabled` in `app.js`
- All 3 tabs (Wallet, Discover, Profile) now evenly spaced

## 2. Profile - SmartCar Connect Entry Point ✅
- **Files**: 
  - `ui-mobile/js/pages/me.js` - Added "Connect your EV" row with button
  - `ui-mobile/js/core/api.js` - Added `apiGetSmartcarConnectUrl()` helper
- New row appears under Account section with:
  - Title: "Connect your EV"
  - Subtitle: "Link your car to track battery SOC and smart-charge windows."
  - Chevron icon indicating tappable
- Click handler fetches Smartcar connect URL and redirects

## 3. Discover - Readable Charge Guidance Capsule ✅
- **Files**:
  - `ui-mobile/index.html` - Updated HTML structure to card container
  - `ui-mobile/css/style.css` - Added `.charge-window-card` styles with white background
  - `ui-mobile/js/pages/explore.js` - Updated to use new card structure
- Card now has:
  - White background (95% opacity) with shadow for readability
  - Rounded corners
  - Proper spacing and contrast
  - Icon, title, and subtitle structure

## 4. Discover - Horizontal Perks with JuiceLand First ✅
- **Files**:
  - `ui-mobile/index.html` - Changed container to `perk-scroll-container`
  - `ui-mobile/css/style.css` - Updated styles for horizontal scrolling
  - `ui-mobile/js/pages/explore.js` - Rewrote `updateRecommendedPerks()` to add JuiceLand first
- Features:
  - JuiceLand @ Domain is hardcoded as first card (featured)
  - Horizontal scrolling container
  - Additional perks appended after JuiceLand
  - Card width set to 240px for better visibility
  - Console log: `[Discover][Perks] Rendered horizontal perks with featured JuiceLand @ Domain`

## 5. Wallet - "Show QR" Button ✅
- **File**: `ui-mobile/js/pages/wallet-new.js`
- Changed button:
  - Label: "Add Funds" → "Show QR"
  - ID: `#w-add` → `#w-show-qr`
  - Handler: `handleShowWalletQr()` navigates to `#/code` route
  - Console log: `[Wallet] Show QR tapped`

## Testing Checklist

✅ **Bottom Nav**: All 3 icons evenly spaced in portrait and landscape  
✅ **Profile**: "Connect your EV" row visible and tappable (calls backend endpoint)  
✅ **Discover**: Charge capsule readable on map with white card background  
✅ **Perks**: JuiceLand @ Domain appears first, horizontal scroll works, additional perks load  
✅ **Wallet**: "Show QR" button replaces "Add Funds", navigates to QR code page

## Notes

- All existing IDs and routes preserved for backwards compatibility
- No breaking changes to existing API calls or flows
- Console logs added for debugging new features
- Styles are mobile-first and responsive

