# Wallet Balance Update Flow Analysis

## Executive Summary

The wallet balance appears to "always update" due to **three concurrent systems** working together:
1. **Backend Nova Accrual Service** - Auto-credits 1 Nova every 5 seconds when `charging_detected = true`
2. **Frontend Balance Resolution** - Merges multiple data sources on every wallet page load
3. **Demo State Persistence** - localStorage saves and restores balance across page navigations

---

## Part 1: Backend Auto-Accrual (Primary Cause)

### Nova Accrual Service
**File:** `nerava-backend-v9/app/services/nova_accrual.py`

- **What it does:** Credits **1 Nova every 5 seconds** to any wallet with `charging_detected = true`
- **When it runs:** Automatically starts when `DEMO_MODE=true` (line 673-677 in `main_simple.py`)
- **Rate:** 12 Nova/minute = 720 Nova/hour
- **Impact:** If your wallet has `charging_detected = True`, the balance increases continuously

### Status Check
```python
wallet.charging_detected = True  # ← This causes constant accrual
```

**Solution:** Set `wallet.charging_detected = False` to stop accrual (already done in previous session).

---

## Part 2: Frontend Balance Resolution (Secondary Cause)

### Balance Loading Priority
**File:** `ui-mobile/js/pages/wallet-new.js:112-158`

The wallet page loads balance from **3 sources in priority order:**

| Step | Source | Code Location | Description |
|------|--------|---------------|-------------|
| 1 | **Default** | Line 116 | Hardcoded `nova_balance: 1000` |
| 2 | **localStorage** | Line 121-127 | `loadDemoRedemption()` - persists across refreshes |
| 3 | **API** | Line 134-143 | `apiDriverWallet()` - backend balance |
| 4 | **Merge Logic** | Line 146-150 | Takes **higher** value between demo and API |

### The Merge Logic Problem
```javascript
// Line 146-150
if (demo && demo.wallet_nova_balance > walletData.nova_balance) {
    walletData.nova_balance = demo.wallet_nova_balance;  // Demo wins if higher
}
```

**Issue:** If backend accrual increases the API balance, but demo localStorage has an old higher value, the wallet shows whichever is higher. This creates inconsistent displays.

---

## Part 3: Demo State Persistence (Tertiary Cause)

### localStorage Save/Load Cycle
**File:** `ui-mobile/js/core/demo-state.js`

### Save Flow
```javascript
// earn.js:391 - When redemption completes
saveDemoRedemption({
    nova_awarded: 300,  // This sets wallet_nova_balance
    ...
});
```

### Load Flow
```javascript
// wallet-new.js:121 - On every wallet page load
const demo = loadDemoRedemption();
if (demo && demo.wallet_nova_balance > walletData.nova_balance) {
    walletData.nova_balance = demo.wallet_nova_balance;
}
```

### The Fix (Already Applied)
**File:** `demo-state.js:39-41`

```javascript
// OLD (accumulating):
merged.wallet_nova_balance = prev.wallet_nova_balance + merged.nova_awarded;

// NEW (replacing):
if (typeof merged.nova_awarded === 'number') {
    merged.wallet_nova_balance = merged.nova_awarded;  // Replace, don't accumulate
}
```

**Status:** ✅ Fixed - localStorage no longer accumulates.

---

## Part 4: Wallet Page Initialization

### Initialization Guard
**File:** `ui-mobile/js/app.js:831-840`

```javascript
async function initWallet() {
    const walletEl = document.getElementById('page-wallet');
    if (walletEl && !walletEl.dataset.initialized) {  // Only runs ONCE per page load
        const { initWalletPage } = await import('./pages/wallet-new.js');
        await initWalletPage(walletEl);
        walletEl.dataset.initialized = 'true';
    }
}
```

**Behavior:** Wallet only initializes **once per page load**. Switching tabs and coming back won't re-initialize unless you refresh the page.

### When It Re-runs
- **Page refresh** (F5 or full reload)
- **Hash navigation** with `#/wallet` if page wasn't initialized
- **New browser session**

---

## Complete Update Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Wallet Update Sources                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  1. Backend Nova Accrual Service    │
        │  (1 Nova every 5 seconds)           │
        │  Status: charging_detected = True   │
        └──────────────┬──────────────────────┘
                       │
                       ▼ (API call)
        ┌─────────────────────────────────────┐
        │  2. Frontend Wallet Page Load       │
        │  initWalletPage() called            │
        └──────────────┬──────────────────────┘
                       │
                       ├──► Default: 1000 Nova (hardcoded)
                       │
                       ├──► localStorage: loadDemoRedemption()
                       │    (was accumulating, now fixed)
                       │
                       └──► API: apiDriverWallet()
                            (reflects backend accrual)
                            │
                            ▼
        ┌─────────────────────────────────────┐
        │  3. Merge Logic                     │
        │  Takes MAX(demo, API) balance       │
        └──────────────┬──────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────┐
        │  4. Display Update                  │
        │  Balance shown to user              │
        └─────────────────────────────────────┘
```

---

## Why Balance Kept Increasing

### Root Causes (in order of impact):

1. **Backend Accrual (HIGHEST IMPACT)**
   - Wallet had `charging_detected = True`
   - Service credits 1 Nova every 5 seconds
   - Balance increases by ~720 Nova/hour

2. **localStorage Accumulation (FIXED)**
   - `saveDemoRedemption()` was adding instead of replacing
   - Each redemption added to previous balance
   - **Fixed in:** `demo-state.js:39-41`

3. **Hardcoded Default (MINOR)**
   - Default balance of 1000 Nova always shown first
   - Gets overwritten by localStorage or API, but creates initial display

4. **Merge Logic (BY DESIGN)**
   - Takes higher value between demo and API
   - If backend accrual makes API higher, it shows that
   - If localStorage has higher value, it shows that

---

## Current Status

✅ **Backend Accrual:** Disabled (`charging_detected = False`)  
✅ **localStorage Accumulation:** Fixed (replaces instead of adds)  
⚠️ **Hardcoded Default:** Still exists (1000 Nova)  
✅ **Merge Logic:** Working as designed (takes max value)

---

## Recommendations

### 1. Remove Hardcoded Default
**File:** `wallet-new.js:116`

```javascript
// Current:
nova_balance: 1000,  // ← Remove this

// Better:
nova_balance: 0,  // Start at 0, let API/localStorage set it
```

### 2. Clear localStorage When Testing
```javascript
// In browser console:
localStorage.removeItem('nerava_demo_redemption');
```

### 3. Control Backend Accrual
```python
# Disable accrual:
wallet.charging_detected = False

# Enable accrual (for demo):
wallet.charging_detected = True
```

### 4. Consider Balance Source Priority
Instead of `MAX(demo, API)`, consider:
- **For demo:** Use demo state if present
- **For production:** Always use API
- **Fallback:** Use 0 if neither available

---

## Testing Checklist

- [x] Backend accrual disabled (`charging_detected = False`)
- [x] localStorage accumulation fixed
- [ ] Hardcoded default removed
- [ ] Balance decreases when redeeming Nova
- [ ] Balance stable when not charging
- [ ] Balance reflects API correctly after redemption

---

## Conclusion

The wallet balance "always updates" due to:
1. **Backend Nova accrual** (now disabled)
2. **localStorage accumulation bug** (now fixed)
3. **Hardcoded default** (minor, but should be removed)
4. **Merge logic** (by design, but can cause confusion)

The primary culprit was backend accrual crediting 1 Nova every 5 seconds. With that disabled, the balance should now be stable unless you're actively earning or spending Nova.

