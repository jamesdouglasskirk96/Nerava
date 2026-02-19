# Web App Native Bridge Integration Guide

This document provides exact code locations and integration points for connecting the React driver web app to the iOS native session engine.

## Overview

The web app communicates with the native iOS app through a JavaScript bridge (`window.neravaNative`). The native app injects this bridge when running in a WKWebView. The web app should check for bridge availability and use it when present.

## Prerequisites

1. **Native Bridge Hook**: `apps/driver/src/hooks/useNativeBridge.ts` must be created (code provided in spec)
2. **Environment Variable**: `VITE_NATIVE_BRIDGE_ENABLED` should be set to `"true"` in production

## Integration Points

### 1. Charger Discovery Integration

**File**: `apps/driver/src/components/DriverHome/DriverHome.tsx`

**Purpose**: Notify native app when a charger is discovered so it can set up geofence monitoring.

**Current Code Location**: Around line 200-300 where `intentData` is processed.

**Integration Code**:

```typescript
import { useNativeBridge } from '../../hooks/useNativeBridge'

// Inside DriverHome component, add:
const { setChargerTarget, isNative } = useNativeBridge()

// Add this useEffect after intentData is received:
useEffect(() => {
  if (isNative && intentData?.charger_summary?.charger_id) {
    const charger = intentData.charger_summary
    
    // Verify we have valid coordinates
    if (charger.lat && charger.lng) {
      console.log('[NativeBridge] Setting charger target:', charger.charger_id)
      setChargerTarget(
        charger.charger_id,
        charger.lat,
        charger.lng
      )
    } else {
      console.warn('[NativeBridge] Charger missing coordinates:', charger)
    }
  }
}, [isNative, intentData, setChargerTarget])
```

**Exact Insertion Point**: 
- Find the `useEffect` that processes `intentData` (around line 220-250)
- Add the new `useEffect` immediately after it
- Ensure `useNativeBridge` is imported at the top of the file

**Testing**:
- Open app in iOS native shell
- Trigger charger discovery
- Verify native logs show "Setting charger target"
- Verify geofence is set in native app

---

### 2. Exclusive Activation Integration

**File**: `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx`

**Purpose**: Notify native app when exclusive is activated so it can transition to SESSION_ACTIVE state.

**Current Code Location**: Around line 86-99 in `handleActivateExclusive` function.

**Integration Code**:

```typescript
import { useNativeBridge } from '../../hooks/useNativeBridge'

// Inside MerchantDetailsScreen component, add:
const { confirmExclusiveActivated, isNative } = useNativeBridge()

// Modify handleActivateExclusive function:
const handleActivateExclusive = useCallback(async () => {
  if (!merchantId) {
    alert('Missing merchant ID')
    return
  }

  // ... existing location code ...

  try {
    const response = await activateExclusive.mutateAsync({
      merchant_id: merchantId,
      merchant_place_id: merchantId,
      charger_id: chargerId,
      lat: lat ?? 0,
      lng: lng ?? 0,
      accuracy_m,
    })

    setExclusiveSessionId(response.exclusive_session.id)
    setRemainingSeconds(response.exclusive_session.remaining_seconds)
    setShowActivateModal(false)
    
    // NEW: Notify native app of activation
    if (isNative && merchantData?.merchant) {
      const merchant = merchantData.merchant
      console.log('[NativeBridge] Confirming exclusive activated:', {
        sessionId: response.exclusive_session.id,
        merchantId: merchant.id,
        merchantLat: merchant.lat,
        merchantLng: merchant.lng
      })
      
      confirmExclusiveActivated(
        response.exclusive_session.id,
        merchant.id,
        merchant.lat,
        merchant.lng
      )
    }
    
    setFlowState('activated')
  } catch (err) {
    // ... existing error handling ...
  }
}, [isNative, confirmExclusiveActivated, merchantData, merchantId, chargerId, activateExclusive])
```

**Exact Insertion Point**:
- Find the line where `setFlowState('activated')` is called (around line 99)
- Add the native bridge notification code immediately before `setFlowState('activated')`
- Ensure merchant data includes `lat` and `lng` properties

**Testing**:
- Open app in iOS native shell
- Complete OTP activation
- Verify native logs show "Confirming exclusive activated"
- Verify native app transitions to SESSION_ACTIVE state
- Verify "You're all set" notification appears

---

### 3. Visit Verification Integration

**File**: `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx`

**Purpose**: Notify native app when visit is verified so it can transition to SESSION_ENDED state.

**Current Code Location**: Around line 120-150 in `handleVerifyVisit` function.

**Integration Code**:

```typescript
import { useNativeBridge } from '../../hooks/useNativeBridge'

// Inside MerchantDetailsScreen component, add:
const { confirmVisitVerified, isNative } = useNativeBridge()

// Modify handleVerifyVisit function:
const handleVerifyVisit = useCallback(async () => {
  if (!exclusiveSessionId || !verificationCode) {
    console.warn('[NativeBridge] Missing session ID or verification code')
    return
  }
  
  try {
    await verifyVisit.mutateAsync({
      session_id: exclusiveSessionId,
      verification_code: verificationCode,
    })
    
    // NEW: Notify native app of verification
    if (isNative) {
      console.log('[NativeBridge] Confirming visit verified:', {
        sessionId: exclusiveSessionId,
        verificationCode: verificationCode
      })
      
      confirmVisitVerified(exclusiveSessionId, verificationCode)
    }
    
    setFlowState('completed')
    // ... rest of success handling ...
  } catch (err) {
    // ... existing error handling ...
  }
}, [isNative, confirmVisitVerified, exclusiveSessionId, verificationCode, verifyVisit])
```

**Exact Insertion Point**:
- Find the line where `verifyVisit.mutateAsync` succeeds (around line 130-140)
- Add the native bridge notification code immediately after successful verification
- Ensure `exclusiveSessionId` and `verificationCode` are available

**Testing**:
- Open app in iOS native shell
- Complete visit verification
- Verify native logs show "Confirming visit verified"
- Verify native app transitions to SESSION_ENDED state

---

## State Synchronization

### Listening to Native State Changes

The web app should listen to native state changes to update UI accordingly:

```typescript
// In DriverHome or MerchantDetailsScreen
const { sessionState, isNative } = useNativeBridge()

useEffect(() => {
  if (!isNative) return
  
  console.log('[NativeBridge] Session state changed:', sessionState)
  
  // Update UI based on native state
  switch (sessionState) {
    case 'NEAR_CHARGER':
      // Show "Approaching charger" indicator
      break
    case 'ANCHORED':
      // Show "Ready to activate" indicator
      break
    case 'SESSION_ACTIVE':
      // Show active session UI
      break
    case 'IN_TRANSIT':
      // Show transit UI
      break
    case 'AT_MERCHANT':
      // Show "You've arrived" UI
      break
    case 'SESSION_ENDED':
      // Show completion UI
      break
  }
}, [isNative, sessionState])
```

### Handling Rejection Events

If native app rejects activation (e.g., not anchored), web app should show error:

```typescript
// Listen for rejection events
useEffect(() => {
  if (!isNative) return
  
  const handleNativeEvent = (event: CustomEvent<{ action: string; payload: any }>) => {
    if (event.detail.action === 'SESSION_START_REJECTED') {
      const reason = event.detail.payload.reason
      console.warn('[NativeBridge] Session start rejected:', reason)
      
      if (reason === 'NOT_ANCHORED') {
        alert('Please wait until you are anchored at the charger before activating.')
      }
    }
  }
  
  window.addEventListener('neravaNative', handleNativeEvent as EventListener)
  return () => window.removeEventListener('neravaNative', handleNativeEvent as EventListener)
}, [isNative])
```

---

## Error Handling

### Bridge Not Available

Always check `isNative` before calling bridge methods:

```typescript
if (isNative && window.neravaNative) {
  // Safe to call bridge methods
  window.neravaNative.setChargerTarget(...)
} else {
  // Fallback to web-only behavior
  console.log('[NativeBridge] Bridge not available, using web-only mode')
}
```

### Bridge Call Failures

Bridge methods are fire-and-forget. If you need to verify success, listen for state changes:

```typescript
// Instead of:
try {
  setChargerTarget(...) // No return value
} catch (err) {
  // Won't catch bridge errors
}

// Do:
setChargerTarget(...)
// Listen for SESSION_STATE_CHANGED event to confirm
```

---

## Testing Checklist

### Manual Testing

- [ ] Charger discovery triggers `setChargerTarget` in native app
- [ ] Exclusive activation triggers `confirmExclusiveActivated` in native app
- [ ] Visit verification triggers `confirmVisitVerified` in native app
- [ ] Native state changes are reflected in web UI
- [ ] Rejection events are handled gracefully
- [ ] Web-only mode works when bridge is unavailable

### Debugging

Enable verbose logging:

```typescript
// In useNativeBridge.ts, add:
useEffect(() => {
  if (isNative) {
    console.log('[NativeBridge] Bridge available:', !!window.neravaNative)
  }
}, [isNative])
```

Check native logs:
- Xcode console shows bridge messages
- Native app logs show state transitions
- Backend logs show event emissions

---

## Rollout Strategy

### Phase 1: Development
- Enable bridge in dev environment: `VITE_NATIVE_BRIDGE_ENABLED=true`
- Test with iOS simulator
- Verify all integration points work

### Phase 2: TestFlight
- Enable bridge in TestFlight build
- Test with real devices
- Monitor for errors

### Phase 3: Production
- Enable bridge in production: `VITE_NATIVE_BRIDGE_ENABLED=true`
- Monitor analytics for bridge usage
- Gradually roll out to all users

### Rollback

To disable native bridge without app update:

```bash
# Set environment variable
VITE_NATIVE_BRIDGE_ENABLED=false

# Rebuild web app
npm run build
```

Web app will fall back to web-only mode.

---

## Common Issues

### Issue: Bridge Not Available

**Symptoms**: `isNative === false` even in native app

**Solutions**:
1. Check that bridge injection script is loaded (check Xcode console)
2. Verify web app URL matches allowed origins
3. Check that `VITE_NATIVE_BRIDGE_ENABLED` is set correctly

### Issue: State Not Syncing

**Symptoms**: Native state changes but web UI doesn't update

**Solutions**:
1. Verify event listener is registered: `window.addEventListener('neravaNative', ...)`
2. Check browser console for event logs
3. Verify `useNativeBridge` hook is mounted

### Issue: Activation Rejected

**Symptoms**: Web activates but native rejects

**Solutions**:
1. Check native logs for rejection reason
2. Verify user is in ANCHORED state before activation
3. Check that charger target was set correctly

---

## References

- [iOS Shell App Spec](../claude-cursor-prompts/2026-01-25_ios-shell-app-v1-implementation.md)
- [Native Bridge Hook Implementation](../claude-cursor-prompts/2026-01-25_ios-shell-app-v1-implementation.md#web-app-bridge-integration)

