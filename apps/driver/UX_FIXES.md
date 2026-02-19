# Driver App UX Fixes - Implementation Summary

This document summarizes the UX improvements implemented for the Nerava driver app.

## Overview

The following changes were made to improve first-time user experience, error handling, state transitions, and terminology clarity without redesigning the entire app.

## Changes Summary

### Phase 1: Fix Mock Data Leaking + API Failure Visibility

**Changes:**
- Added `VITE_DEMO_MODE` environment variable support (default: false)
- Created `ErrorBanner` component for displaying API errors with retry functionality
- Removed silent fallback to mock data in `DriverHome` and `WhileYouChargeScreen`
- Added error state handling for API failures
- Shows "Demo Mode" badge when `VITE_DEMO_MODE=true`

**Files Modified:**
- `apps/driver/src/services/api.ts` - Added `isDemoMode()` function
- `apps/driver/src/components/DriverHome/DriverHome.tsx` - Removed silent fallback, added error handling
- `apps/driver/src/components/WhileYouCharge/WhileYouChargeScreen.tsx` - Removed mock data fallback

**Files Created:**
- `apps/driver/src/components/shared/ErrorBanner.tsx`

### Phase 2: Onboarding + Location Permission Pre-Prompt

**Changes:**
- Created 3-screen onboarding flow shown only once (stored in localStorage)
- Removed auto-request of location permission on app mount
- Added location permission pre-prompt explaining why location is needed
- Added "Not now" option to skip location permission

**Files Modified:**
- `apps/driver/src/contexts/DriverSessionContext.tsx` - Removed auto-request, added 'skipped' permission state
- `apps/driver/src/App.tsx` - Added onboarding gate

**Files Created:**
- `apps/driver/src/hooks/useOnboarding.ts` - Hook for managing onboarding state
- `apps/driver/src/components/Onboarding/OnboardingFlow.tsx` - 3-screen onboarding component
- `apps/driver/src/components/Onboarding/OnboardingGate.tsx` - Gate component that shows onboarding if not completed

### Phase 3: Location Denied / Error Recovery

**Changes:**
- Created recovery screen when location is denied or fails
- Added "Browse mode" that allows browsing chargers without location
- Uses default center (Austin, TX) for charger discovery in browse mode
- Shows "Browse mode" badge in header when location is unavailable

**Files Modified:**
- `apps/driver/src/components/DriverHome/DriverHome.tsx` - Added location denied check, browse mode support
- `apps/driver/src/components/PreCharging/PreChargingScreen.tsx` - Added browse mode badge

**Files Created:**
- `apps/driver/src/components/LocationDenied/LocationDeniedScreen.tsx` - Recovery screen component

### Phase 4: State Transition UX

**Changes:**
- Created toast notification for PRE_CHARGING → CHARGING_ACTIVE transition
- Added fade transition animations between screens
- Toast auto-hides after 3 seconds

**Files Modified:**
- `apps/driver/src/components/DriverHome/DriverHome.tsx` - Added transition detection and toast display

**Files Created:**
- `apps/driver/src/components/shared/StateTransitionToast.tsx` - Toast component for state transitions

### Phase 5: Clarify "Exclusive" Terminology

**Changes:**
- Created reusable tooltip component explaining "Exclusive"
- Added tooltip to merchant details header, offer card header, and activation modal

**Files Modified:**
- `apps/driver/src/components/MerchantDetails/HeroImageHeader.tsx` - Added tooltip next to Exclusive badge
- `apps/driver/src/components/MerchantDetails/ExclusiveOfferCard.tsx` - Added tooltip in card header
- `apps/driver/src/components/ActivateExclusiveModal/ActivateExclusiveModal.tsx` - Added tooltip near activation CTA

**Files Created:**
- `apps/driver/src/components/shared/ExclusiveInfoTooltip.tsx` - Reusable tooltip component

### Phase 6: Auth Friction - Improve Copy

**Changes:**
- Updated OTP modal title: "Verify to redeem"
- Updated subtext: "We'll text you a one-time code so the merchant can confirm your exclusive."
- Updated privacy note: "No spam. One verification code."
- Improved error messages for backend failures

**Files Modified:**
- `apps/driver/src/components/ActivateExclusiveModal/ActivateExclusiveModal.tsx` - Updated copy and error messages

## Environment Variables

### VITE_DEMO_MODE
- **Type:** boolean (string: "true" or "false")
- **Default:** false
- **Description:** When set to "true", allows mock data fallback when API fails and shows "Demo Mode" badge. When false, shows error banner instead of silently falling back to mock data.

**Example:**
```bash
VITE_DEMO_MODE=false  # Production: show errors, no mock fallback
VITE_DEMO_MODE=true   # Development: allow mock fallback, show demo badge
```

## LocalStorage Keys

### nerava_onboarding_seen
- **Type:** string ("true")
- **Description:** Set when user completes onboarding flow. Prevents onboarding from showing again.
- **Location:** Set in `apps/driver/src/hooks/useOnboarding.ts`

### Existing Keys (Unchanged)
- `nerava_driver_session` - Session data (coordinates, sessionId, etc.)
- `nerava_app_charging_state` - Current charging state (PRE_CHARGING, CHARGING_ACTIVE, EXCLUSIVE_ACTIVE)
- `neravaLikes` - Liked merchants
- `access_token` - Authentication token
- `refresh_token` - Refresh token

## Component Architecture

### New Components

1. **ErrorBanner** - Displays API errors with retry button
2. **OnboardingFlow** - 3-screen onboarding flow
3. **OnboardingGate** - Wrapper that gates app behind onboarding check
4. **LocationDeniedScreen** - Recovery screen for denied location
5. **StateTransitionToast** - Toast for state transitions
6. **ExclusiveInfoTooltip** - Tooltip explaining "Exclusive" terminology

### Updated Components

1. **DriverHome** - Added error handling, browse mode, transition detection
2. **DriverSessionContext** - Removed auto-request location, added 'skipped' state
3. **ActivateExclusiveModal** - Improved copy and error messages
4. **PreChargingScreen** - Added browse mode badge
5. **HeroImageHeader** - Added Exclusive tooltip
6. **ExclusiveOfferCard** - Added Exclusive tooltip

## Testing Checklist

1. ✅ Fresh user (clear localStorage) → sees onboarding → no location prompt until "Enable location"
2. ✅ "Not now" path → app usable → shows browse mode
3. ✅ Denied permission → shows recovery screen
4. ✅ API failure → no mock data shown silently → error banner with retry
5. ✅ Transition to CHARGING_ACTIVE → toast appears and fades
6. ✅ Exclusive tooltip → appears in all specified locations
7. ✅ OTP modal → improved copy visible

## Notes

- All new components use existing Tailwind tokens and design system
- No new dependencies required
- Maintains backward compatibility with existing flows
- Demo mode badge uses existing Badge component pattern
- Browse mode uses default center (Austin: 30.2672, -97.7431) for charger discovery





