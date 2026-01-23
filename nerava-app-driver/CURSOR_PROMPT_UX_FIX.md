# Cursor Prompt: Nerava Driver App UX Fix

**Goal:** Fix mobile layout + missing context so the Driver app is demo-safe and self-explanatory during the charge party.

---

## Overview of Changes Required

| Issue | Fix |
|-------|-----|
| State labels wrong | "Pre-Charging" → "Find a charger", "Charging Active" → "Charging Now" |
| Merchant Details doesn't fit mobile viewport | Refactor to mobile-first layout with sticky header |
| Location error is disruptive | Replace red error with calm "Location off" component |
| Pre-Charging hides merchant context | Make "Nearby experiences" larger and tappable |

---

## 1. Rename State Labels (UI Text Only)

### Files to modify:
- `src/components/WhileYouCharge/WhileYouChargeScreen.tsx`
- `src/components/PreCharging/PreChargingScreen.tsx`
- `src/components/WhileYouCharge/ChargingActivePill.tsx` (if still exists)

### Changes:

**In WhileYouChargeScreen.tsx** - Find and replace all instances:
- `"Charging Active"` → `"Charging Now"`

**In PreChargingScreen.tsx** - Find and replace all instances:
- `"Pre-Charging"` → `"Find a charger"`

**Header pill button in both screens should use consistent styling:**
```tsx
<button
  onClick={handleToggle}
  className="px-3 py-1.5 bg-[#1877F2] rounded-full hover:bg-[#166FE5] active:scale-95 transition-all"
>
  <span className="text-xs text-white font-medium">
    {/* "Charging Now" or "Find a charger" */}
  </span>
</button>
```

### Acceptance Criteria:
- [ ] No user-facing "Pre-Charging" text remains
- [ ] No user-facing "Charging Active" text remains
- [ ] Both state pills look identical (blue pill with white text)

---

## 2. Merchant Details: Mobile-First Layout

### File: `src/components/MerchantDetails/MerchantDetailsScreen.tsx`

### Current Problems (from screenshot):
1. Hero area uses placeholder icon instead of actual photo
2. Layout has awkward spacing and doesn't fit viewport
3. Red "Location permission denied" error is disruptive
4. Content competes for vertical space

### Required Layout Structure:

```tsx
<div className="h-[100dvh] flex flex-col bg-white overflow-hidden">
  {/* Sticky Header Bar - ALWAYS visible */}
  <div className="sticky top-0 z-20 flex items-center justify-between px-4 py-3 bg-white/95 backdrop-blur-sm border-b border-gray-100">
    <button onClick={onClose} className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
      <X className="w-5 h-5" />
    </button>
    <div className="flex gap-2">
      <button onClick={onFavorite} className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
        <Heart className={`w-5 h-5 ${isFavorite ? 'fill-red-500 text-red-500' : ''}`} />
      </button>
      <button onClick={onShare} className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
        <Share2 className="w-5 h-5" />
      </button>
    </div>
  </div>

  {/* Single Scrollable Content Area */}
  <div className="flex-1 overflow-y-auto">
    {/* Hero Image - max 35-40% of viewport */}
    <div className="relative w-full h-[35vh] max-h-[280px] bg-gray-200">
      {imageUrl ? (
        <img src={imageUrl} alt={merchantName} className="w-full h-full object-cover" />
      ) : (
        <PhotoPlaceholder ... />
      )}

      {/* Badges overlay at bottom */}
      <div className="absolute bottom-4 left-4 right-4 flex justify-between items-end">
        <Badge variant="walk-time">{walkTime}</Badge>
        {isExclusive && <Badge variant="exclusive">Exclusive</Badge>}
      </div>
    </div>

    {/* Content */}
    <div className="px-5 py-4 space-y-4">
      {/* Merchant name + category */}
      <div>
        <h1 className="text-2xl font-bold text-[#050505]">{merchantName}</h1>
        <p className="text-sm text-[#65676B]">{category}</p>
      </div>

      {/* Exclusive Offer Card - HIGH PRIORITY, visible without scrolling */}
      {perk && (
        <ExclusiveOfferCard title={perk.title} description={perk.description} />
      )}

      {/* Distance Card */}
      <DistanceCard distanceMiles={distance} />

      {/* Location Status - CALM design, not red error */}
      <LocationStatusCard geo={geo} />
    </div>
  </div>

  {/* Sticky Bottom CTA */}
  <div className="sticky bottom-0 px-5 py-4 bg-white border-t border-gray-100 safe-area-inset-bottom">
    <Button variant="primary" onClick={handleCTA} className="w-full">
      {geo.isNearCharger ? 'Activate Exclusive' : 'Navigate to Charger'}
    </Button>
  </div>
</div>
```

### New Component: LocationStatusCard (replaces red error)

Create new file: `src/components/MerchantDetails/LocationStatusCard.tsx`

```tsx
import { MapPin, Info } from 'lucide-react'

interface LocationStatusCardProps {
  geo: {
    loading: boolean
    error: string | null
    distanceToCharger: number | null
    isNearCharger: boolean
  }
}

export function LocationStatusCard({ geo }: LocationStatusCardProps) {
  // Loading state
  if (geo.loading) {
    return (
      <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
        <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center animate-pulse">
          <MapPin className="w-5 h-5 text-gray-400" />
        </div>
        <p className="text-sm text-gray-500">Getting your location...</p>
      </div>
    )
  }

  // Error or permission denied - CALM treatment
  if (geo.error || geo.distanceToCharger === null) {
    return (
      <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
        <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0">
          <MapPin className="w-5 h-5 text-gray-400" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-700">Location off</p>
          <p className="text-xs text-gray-500 mt-0.5">
            Turn on location to show walk times and verify you're at the charger.
          </p>
        </div>
      </div>
    )
  }

  // Near charger - success state
  if (geo.isNearCharger) {
    return (
      <div className="flex items-center gap-3 p-3 bg-green-50 rounded-xl">
        <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
          <MapPin className="w-5 h-5 text-green-600" />
        </div>
        <div>
          <p className="text-sm font-medium text-green-700">You're at the charger</p>
          <p className="text-xs text-green-600">{Math.round(geo.distanceToCharger)}m away</p>
        </div>
      </div>
    )
  }

  // Not near charger
  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
        <MapPin className="w-5 h-5 text-blue-600" />
      </div>
      <div>
        <p className="text-sm font-medium text-gray-700">Distance</p>
        <p className="text-xs text-gray-500">{Math.round(geo.distanceToCharger)}m to charger</p>
      </div>
    </div>
  )
}
```

### Update HeroImageHeader.tsx

Reduce height and remove embedded action buttons (moved to sticky header):

```tsx
// Change from h-56 to dynamic height that respects viewport
<div className="relative w-full h-[35vh] max-h-[280px] bg-gray-200">
```

Remove the X, Heart, Share buttons from HeroImageHeader - they're now in the sticky header above.

---

## 3. Improve "Find a charger" Merchant Context

### File: `src/components/PreCharging/NearbyExperiences.tsx`

### Current Problem:
The "Nearby experiences" shows tiny square cards that are hard to read and don't provide enough context.

### Solution:
Replace with a horizontal scrollable list of compact merchant cards that show:
- Merchant photo
- Merchant name
- Category
- Walk time
- Exclusive badge

### New Implementation:

```tsx
import { useNavigate } from 'react-router-dom'
import type { MerchantSummary } from '../../types'
import { PhotoPlaceholder, normalizeCategory } from '../../ui/categoryLogos'
import { Badge } from '../shared/Badge'

interface NearbyExperiencesProps {
  experiences: MerchantSummary[]
  chargerId?: string
}

export function NearbyExperiences({ experiences, chargerId }: NearbyExperiencesProps) {
  const navigate = useNavigate()

  const validExperiences = experiences.filter((exp) => exp && exp.place_id)

  if (validExperiences.length === 0) {
    return null
  }

  const handleMerchantClick = (placeId: string) => {
    navigate(`/m/${placeId}${chargerId ? `?charger_id=${chargerId}` : ''}`)
  }

  return (
    <div className="mt-4 pt-4 border-t border-gray-200">
      <p className="text-sm font-semibold text-gray-800 mb-3">Nearby experiences</p>

      {/* Horizontal scroll container */}
      <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide">
        {validExperiences.map((exp) => {
          const category = exp.types?.[0] ? normalizeCategory(exp.types[0]) : 'Other'
          const walkTime = Math.round(exp.distance_m / 80)
          const hasExclusive = exp.badges?.some(b => b.includes('Exclusive'))

          return (
            <div
              key={exp.place_id}
              onClick={() => handleMerchantClick(exp.place_id)}
              className="flex-shrink-0 w-[160px] rounded-xl overflow-hidden bg-white border border-gray-200 shadow-sm cursor-pointer active:scale-[0.98] transition-transform"
            >
              {/* Photo */}
              <div className="relative h-[100px] bg-gray-100">
                {exp.photo_url ? (
                  <img
                    src={exp.photo_url}
                    alt={exp.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <PhotoPlaceholder category={category} merchantName={exp.name} className="h-full" />
                )}

                {/* Walk time badge */}
                <div className="absolute bottom-2 left-2">
                  <Badge variant="walk-time" className="text-[10px] px-2 py-1">
                    {walkTime} min
                  </Badge>
                </div>
              </div>

              {/* Info */}
              <div className="p-2.5">
                <div className="flex items-start justify-between gap-1">
                  <h4 className="text-sm font-medium text-gray-900 truncate flex-1">
                    {exp.name}
                  </h4>
                  {hasExclusive && (
                    <span className="text-xs">⭐</span>
                  )}
                </div>
                <p className="text-xs text-gray-500 truncate mt-0.5">
                  {exp.types?.slice(0, 2).map(t => normalizeCategory(t)).join(' · ') || category}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

### Update ChargerCard.tsx to pass chargerId:

```tsx
<NearbyExperiences
  experiences={merchantExperiences}
  chargerId={charger.id}  // Add this prop
/>
```

---

## 4. CSS Additions

Add to `src/index.css`:

```css
/* Hide scrollbar but keep functionality */
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

/* Safe area inset for bottom sticky elements */
.safe-area-inset-bottom {
  padding-bottom: max(16px, env(safe-area-inset-bottom));
}
```

---

## 5. Files Summary

| File | Action |
|------|--------|
| `src/components/WhileYouCharge/WhileYouChargeScreen.tsx` | Change "Charging Active" → "Charging Now" |
| `src/components/PreCharging/PreChargingScreen.tsx` | Change "Pre-Charging" → "Find a charger" |
| `src/components/MerchantDetails/MerchantDetailsScreen.tsx` | Refactor to mobile-first layout |
| `src/components/MerchantDetails/HeroImageHeader.tsx` | Remove action buttons, reduce height |
| `src/components/MerchantDetails/LocationStatusCard.tsx` | **CREATE** - calm location status |
| `src/components/PreCharging/NearbyExperiences.tsx` | Refactor to horizontal scroll with larger cards |
| `src/components/PreCharging/ChargerCard.tsx` | Pass chargerId to NearbyExperiences |
| `src/index.css` | Add scrollbar-hide and safe-area utilities |

---

## 6. Validation Checklist

After implementation, verify:

- [ ] `npm run build` passes
- [ ] `npm run lint` passes
- [ ] On iPhone Safari with location denied:
  - [ ] App still usable (no broken state)
  - [ ] "Find a charger" screen shows readable merchant previews
  - [ ] Merchant details fits viewport
  - [ ] Location message says "Location off" (not red error)
- [ ] On iPhone Safari with location granted:
  - [ ] State pill shows "Charging Now" near charger
  - [ ] Merchant details shows walk time correctly
  - [ ] "Activate Exclusive" button is enabled when near charger

---

## 7. Non-Goals (Do NOT Do)

- No backend changes
- No new onboarding flows
- No design system overhaul
- No routing refactor
- Keep changes minimal and focused on UX fixes
