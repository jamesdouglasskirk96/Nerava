# Demo-Ready Cleanup - Cursor Implementation Prompt

**Date:** 2026-01-23
**Goal:** Make driver app + admin portal demo-solid for live merchant demo

---

## OUTPUT A: State of the World

### 1. Viewport / Fullscreen / Address Bar
**Current State:**
- `index.html` has `viewport-fit=cover` meta tag
- `index.css` uses `100dvh` with `100vh` fallback
- Missing: PWA standalone meta tags, safe-area padding, manifest.json enhancements

**Files:**
- `/apps/driver/index.html` (line 6 - viewport meta)
- `/apps/driver/src/index.css` (lines 12-24 - root height)
- `/apps/driver/public/` - needs manifest.json check

**What's Missing:**
- `apple-mobile-web-app-capable` meta tag
- `display: standalone` in manifest.json
- `env(safe-area-inset-bottom)` padding on CTA containers
- Viewport stabilization helper on route changes

---

### 2. Image Loading + Cache
**Current State:**
- `ImageWithFallback.tsx` component exists but doesn't cache
- Merchant photos fetched on every render
- React keys may cause remounts

**Files:**
- `/apps/driver/src/components/shared/ImageWithFallback.tsx`
- `/apps/driver/src/components/MerchantCarousel/MerchantCarousel.tsx`
- `/apps/driver/src/components/MerchantDetail/MerchantDetailModal.tsx`
- `/apps/driver/src/components/MerchantDetails/HeroImageHeader.tsx`

**What's Missing:**
- In-memory image cache keyed by `photo_url`
- Preload next carousel image on index change
- Stable React keys (avoid using index)
- Keep previous image visible during load

---

### 3. Favorites / Like System
**Current State:**
- `DriverHome.tsx` lines 66-77: localStorage-based likes (`neravaLikes`)
- Backend has full favorites API: `GET/POST/DELETE /v1/merchants/{id}/favorite`
- Frontend NOT using backend API - only localStorage

**Files:**
- `/apps/driver/src/components/DriverHome/DriverHome.tsx` (lines 66-77, 183-198)
- `/backend/app/routers/merchants.py` (lines 23-100) - favorites endpoints
- `/backend/app/models/while_you_charge.py` (lines 262-277) - FavoriteMerchant model

**What's Missing:**
- FavoritesContext to centralize state
- API calls to backend favorites endpoints
- Sync favorites on auth/mount
- Like button uses backend when authenticated

---

### 4. Account Page / Phone Number
**Current State:**
- No dedicated Account page found in driver app
- Token stored in localStorage after OTP verify
- Backend returns `user.phone` in token response

**Files:**
- `/apps/driver/src/services/auth.ts` (lines 21-31, 107-116)
- `/apps/driver/src/components/DriverHome/DriverHome.tsx` (lines 78-81)

**What's Missing:**
- Account page component
- Display masked phone from stored user data
- Link from header to account page

---

### 5. OTP Flow
**Current State:**
- `ActivateExclusiveModal.tsx` - full OTP implementation (phone entry + code entry)
- `auth.ts` - `otpStart()` and `otpVerify()` functions calling backend
- Backend: `/v1/auth/otp/start` and `/v1/auth/otp/verify` working
- OTP currently shows "Sending..." but may timeout if backend unreachable

**Files:**
- `/apps/driver/src/components/ActivateExclusiveModal/ActivateExclusiveModal.tsx` (391 lines)
- `/apps/driver/src/services/auth.ts` (117 lines)
- `/backend/app/routers/auth.py` (lines 346-559)
- `/backend/app/services/auth/twilio_verify.py`

**What's Missing:**
- OTP timeout handling with better UX (not just "Network error")
- Better loading states
- Backend deployment must succeed for OTP to work

---

### 6. Admin Deployments Panel
**Current State:**
- Admin portal exists at `/apps/admin/`
- Has Dashboard, ActiveSessions, Exclusives, Merchants, Logs pages
- NO deployments page

**Files:**
- `/apps/admin/src/App.tsx`
- `/apps/admin/src/components/Sidebar.tsx`
- `/apps/admin/src/components/Dashboard.tsx`
- `/backend/app/routers/admin_domain.py`

**What's Missing:**
- Deployments page component
- Backend endpoint to trigger GitHub Actions
- Rate limiting + confirmation modal

---

### 7. Demo Simulation Tooling
**Current State:**
- No demo simulation endpoints
- ExclusiveSession model exists for activation tracking
- RewardEvent model exists for verified visits

**Files:**
- `/backend/app/models/exclusive_session.py`
- `/backend/app/models/extra.py` (RewardEvent lines 55-64)
- `/backend/app/routers/exclusive.py`

**What's Missing:**
- `POST /v1/internal/demo/simulate-verified-visit` endpoint
- Demo runner script or Playwright test

---

## OUTPUT B: Cursor Implementation Prompt

---

# P0 TASKS (Must fix for demo)

## Task 1: Viewport / Fullscreen Hardening

### Step 1.1: Update index.html PWA meta tags

**File:** `/apps/driver/index.html`

Add after line 6 (existing viewport meta):
```html
<!-- PWA standalone mode for iOS -->
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Nerava">
<meta name="mobile-web-app-capable" content="yes">
```

### Step 1.2: Update CSS for safe-area

**File:** `/apps/driver/src/index.css`

Replace lines 12-24 with:
```css
#root {
  height: 100vh; /* Fallback */
  height: 100dvh;
  width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

body {
  overflow: hidden;
  height: 100vh;
  height: 100dvh;
  padding-bottom: env(safe-area-inset-bottom, 0);
}

/* CSS variable for dynamic height */
:root {
  --app-height: 100dvh;
}
```

### Step 1.3: Add viewport stabilization helper

**File:** `/apps/driver/src/hooks/useViewportHeight.ts` (NEW FILE)

```typescript
import { useEffect } from 'react'

export function useViewportHeight() {
  useEffect(() => {
    const setAppHeight = () => {
      document.documentElement.style.setProperty('--app-height', `${window.innerHeight}px`)
    }

    setAppHeight()
    window.addEventListener('resize', setAppHeight)

    // Best-effort scroll trick for iOS
    window.scrollTo(0, 1)

    return () => window.removeEventListener('resize', setAppHeight)
  }, [])
}
```

### Step 1.4: Use hook in App.tsx

**File:** `/apps/driver/src/App.tsx`

Add import and call:
```typescript
import { useViewportHeight } from './hooks/useViewportHeight'

function App() {
  useViewportHeight()
  // ... rest of component
}
```

### Step 1.5: Fix CTA button containers

**File:** `/apps/driver/src/components/MerchantDetail/MerchantDetailModal.tsx`

Search for the CTA button container (around line 200+) and ensure:
```css
/* Add safe-area padding to bottom CTA container */
className="... pb-safe" /* or padding-bottom: env(safe-area-inset-bottom) */
```

**Acceptance Criteria:**
- [ ] iOS Safari: CTA buttons visible without scrolling
- [ ] Google in-app browser: No content hidden behind browser UI
- [ ] No white gap below content

---

## Task 2: Image Caching

### Step 2.1: Create image cache utility

**File:** `/apps/driver/src/utils/imageCache.ts` (NEW FILE)

```typescript
const imageCache = new Map<string, string>()

export function getCachedImage(url: string): string | null {
  return imageCache.get(url) || null
}

export function setCachedImage(url: string): void {
  if (!imageCache.has(url)) {
    imageCache.set(url, url)
  }
}

export function preloadImage(url: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (imageCache.has(url)) {
      resolve()
      return
    }
    const img = new Image()
    img.onload = () => {
      setCachedImage(url)
      resolve()
    }
    img.onerror = reject
    img.src = url
  })
}
```

### Step 2.2: Update ImageWithFallback component

**File:** `/apps/driver/src/components/shared/ImageWithFallback.tsx`

Add caching logic:
```typescript
import { useState, useEffect, useMemo } from 'react'
import { getCachedImage, setCachedImage } from '../../utils/imageCache'

// In component:
const cachedSrc = useMemo(() => getCachedImage(src), [src])
const [loaded, setLoaded] = useState(!!cachedSrc)

useEffect(() => {
  if (cachedSrc) {
    setLoaded(true)
  }
}, [cachedSrc])

const handleLoad = () => {
  setCachedImage(src)
  setLoaded(true)
}
```

### Step 2.3: Preload next carousel image

**File:** `/apps/driver/src/components/MerchantCarousel/MerchantCarousel.tsx`

Add preload effect when index changes:
```typescript
import { preloadImage } from '../../utils/imageCache'

// Inside component, after currentSetIndex changes:
useEffect(() => {
  const nextIndex = (currentSetIndex + 1) % totalSets
  const nextSet = merchantSets[nextIndex]
  if (nextSet?.featured?.imageUrl) {
    preloadImage(nextSet.featured.imageUrl)
  }
}, [currentSetIndex, merchantSets, totalSets])
```

### Step 2.4: Use stable keys in carousel

**File:** `/apps/driver/src/components/MerchantCarousel/MerchantCarousel.tsx`

Search for `.map()` calls and ensure keys use `merchant.id` not index:
```typescript
{merchants.map((merchant) => (
  <div key={merchant.id}> {/* NOT key={index} */}
```

**Acceptance Criteria:**
- [ ] Swiping merchants: no blank image flash
- [ ] Same photo loads once per session
- [ ] Smooth transitions between carousel items

---

## Task 3: Unified Favorites System

### Step 3.1: Create FavoritesContext

**File:** `/apps/driver/src/contexts/FavoritesContext.tsx` (NEW FILE)

```typescript
import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface FavoritesContextType {
  favorites: Set<string>
  toggleFavorite: (merchantId: string) => Promise<void>
  isFavorite: (merchantId: string) => boolean
  isLoading: boolean
}

const FavoritesContext = createContext<FavoritesContextType | null>(null)

export function FavoritesProvider({ children }: { children: ReactNode }) {
  const [favorites, setFavorites] = useState<Set<string>>(() => {
    const stored = localStorage.getItem('neravaLikes')
    return stored ? new Set(JSON.parse(stored)) : new Set()
  })
  const [isLoading, setIsLoading] = useState(false)

  // Sync with localStorage
  useEffect(() => {
    localStorage.setItem('neravaLikes', JSON.stringify(Array.from(favorites)))
  }, [favorites])

  // Load from backend if authenticated
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      fetchFavorites(token)
    }
  }, [])

  const fetchFavorites = async (token: string) => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/v1/merchants/favorites`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setFavorites(new Set(data.map((f: any) => f.merchant_id)))
      }
    } catch (e) {
      console.error('Failed to fetch favorites', e)
    }
  }

  const toggleFavorite = async (merchantId: string) => {
    const token = localStorage.getItem('access_token')
    const isFav = favorites.has(merchantId)

    // Optimistic update
    setFavorites(prev => {
      const next = new Set(prev)
      isFav ? next.delete(merchantId) : next.add(merchantId)
      return next
    })

    // Sync with backend if authenticated
    if (token) {
      try {
        await fetch(`${import.meta.env.VITE_API_BASE_URL}/v1/merchants/${merchantId}/favorite`, {
          method: isFav ? 'DELETE' : 'POST',
          headers: { Authorization: `Bearer ${token}` }
        })
      } catch (e) {
        // Revert on failure
        setFavorites(prev => {
          const next = new Set(prev)
          isFav ? next.add(merchantId) : next.delete(merchantId)
          return next
        })
      }
    }
  }

  const isFavorite = (merchantId: string) => favorites.has(merchantId)

  return (
    <FavoritesContext.Provider value={{ favorites, toggleFavorite, isFavorite, isLoading }}>
      {children}
    </FavoritesContext.Provider>
  )
}

export function useFavorites() {
  const ctx = useContext(FavoritesContext)
  if (!ctx) throw new Error('useFavorites must be used within FavoritesProvider')
  return ctx
}
```

### Step 3.2: Wrap app with FavoritesProvider

**File:** `/apps/driver/src/App.tsx`

```typescript
import { FavoritesProvider } from './contexts/FavoritesContext'

// Wrap existing providers:
<FavoritesProvider>
  <DriverSessionProvider>
    {/* ... */}
  </DriverSessionProvider>
</FavoritesProvider>
```

### Step 3.3: Update DriverHome to use FavoritesContext

**File:** `/apps/driver/src/components/DriverHome/DriverHome.tsx`

Replace lines 66-77 (likedMerchants state) and lines 183-198 (handleToggleLike):
```typescript
import { useFavorites } from '../../contexts/FavoritesContext'

// Replace local state with:
const { favorites: likedMerchants, toggleFavorite: handleToggleLike, isFavorite } = useFavorites()
```

**Acceptance Criteria:**
- [ ] Like from card -> appears in Account Favorites
- [ ] Like from detail -> card reflects liked state
- [ ] Unlike removes everywhere

---

## Task 4: Account Page with Phone Number

### Step 4.1: Create Account page component

**File:** `/apps/driver/src/components/Account/AccountPage.tsx` (NEW FILE)

```typescript
import { useState, useEffect } from 'react'
import { ArrowLeft, Heart, Settings, LogOut } from 'lucide-react'
import { useFavorites } from '../../contexts/FavoritesContext'

export function AccountPage({ onClose }: { onClose: () => void }) {
  const { favorites } = useFavorites()
  const [userPhone, setUserPhone] = useState<string | null>(null)

  useEffect(() => {
    // Try to get phone from stored user data
    const storedUser = localStorage.getItem('nerava_user')
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser)
        if (user.phone) {
          // Mask phone: ***-***-1234
          const last4 = user.phone.slice(-4)
          setUserPhone(`***-***-${last4}`)
        }
      } catch {}
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('nerava_user')
    window.location.reload()
  }

  return (
    <div className="fixed inset-0 bg-white z-50 flex flex-col">
      <header className="flex items-center p-4 border-b">
        <button onClick={onClose} className="p-2">
          <ArrowLeft className="w-6 h-6" />
        </button>
        <h1 className="flex-1 text-center font-semibold text-lg">Account</h1>
        <div className="w-10" />
      </header>

      <div className="flex-1 p-4 space-y-4">
        {userPhone && (
          <div className="p-4 bg-gray-50 rounded-xl">
            <p className="text-sm text-gray-500">Phone</p>
            <p className="font-medium">{userPhone}</p>
          </div>
        )}

        <div className="p-4 bg-gray-50 rounded-xl flex items-center gap-3">
          <Heart className="w-5 h-5 text-red-500" />
          <div>
            <p className="font-medium">Favorites</p>
            <p className="text-sm text-gray-500">{favorites.size} saved</p>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="w-full p-4 bg-red-50 text-red-600 rounded-xl flex items-center gap-3"
        >
          <LogOut className="w-5 h-5" />
          <span>Log out</span>
        </button>
      </div>
    </div>
  )
}
```

### Step 4.2: Store user data on OTP verify

**File:** `/apps/driver/src/services/auth.ts`

After line 113 (where tokens are stored), add:
```typescript
// Store user info for account page
if (data.user) {
  localStorage.setItem('nerava_user', JSON.stringify(data.user))
}
```

### Step 4.3: Add account button to header

**File:** `/apps/driver/src/components/DriverHome/DriverHome.tsx`

Add account icon in header (around line 578-599):
```typescript
import { AccountPage } from '../Account/AccountPage'

// Add state:
const [showAccountPage, setShowAccountPage] = useState(false)

// In header, add account button:
<button onClick={() => setShowAccountPage(true)} className="p-2">
  <User className="w-5 h-5" />
</button>

// Add AccountPage modal:
{showAccountPage && <AccountPage onClose={() => setShowAccountPage(false)} />}
```

**Acceptance Criteria:**
- [ ] After OTP auth, account shows masked phone
- [ ] Account accessible from header

---

## Task 5: OTP Flow Reliability

### Step 5.1: Add timeout handling to OTP start

**File:** `/apps/driver/src/services/auth.ts`

Wrap fetch with timeout:
```typescript
export async function otpStart(phone: string): Promise<OTPStartResponse> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 15000) // 15s timeout

  try {
    const response = await fetch(`${API_BASE_URL}/v1/auth/otp/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: normalizedPhone }),
      signal: controller.signal,
    })
    // ... existing error handling
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new ApiError(408, 'timeout', 'Request timed out. Please try again.')
    }
    throw err
  } finally {
    clearTimeout(timeoutId)
  }
}
```

### Step 5.2: Better loading state in modal

**File:** `/apps/driver/src/components/ActivateExclusiveModal/ActivateExclusiveModal.tsx`

Replace "Sending..." (line 291) with:
```typescript
{isLoading ? (
  <span className="flex items-center justify-center gap-2">
    <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
    Sending code...
  </span>
) : 'Send code'}
```

**Acceptance Criteria:**
- [ ] OTP works end-to-end (requires backend deployment)
- [ ] Timeout shows user-friendly message
- [ ] Loading spinner visible during send

---

# P1 TASKS (Important for demo)

## Task 6: Admin Deployments Panel

### Step 6.1: Create Deployments component

**File:** `/apps/admin/src/components/Deployments.tsx` (NEW FILE)

```typescript
import { useState } from 'react'
import { Rocket, RefreshCw, ExternalLink, AlertTriangle } from 'lucide-react'

interface DeployTarget {
  id: string
  name: string
  description: string
  lastDeploy?: string
}

const DEPLOY_TARGETS: DeployTarget[] = [
  { id: 'backend', name: 'Backend API', description: 'App Runner service' },
  { id: 'driver', name: 'Driver App', description: 'S3 + CloudFront' },
  { id: 'admin', name: 'Admin Portal', description: 'S3 + CloudFront' },
  { id: 'merchant', name: 'Merchant Portal', description: 'S3 + CloudFront' },
]

export function Deployments() {
  const [selectedTarget, setSelectedTarget] = useState<string | null>(null)
  const [isDeploying, setIsDeploying] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const handleTriggerDeploy = async () => {
    if (!selectedTarget) return
    setIsDeploying(true)

    try {
      const response = await fetch('/api/v1/admin/deployments/trigger', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
        },
        body: JSON.stringify({ target: selectedTarget, ref: 'main' }),
      })

      if (response.ok) {
        alert('Deployment triggered successfully!')
      } else {
        alert('Failed to trigger deployment')
      }
    } catch (e) {
      alert('Error triggering deployment')
    } finally {
      setIsDeploying(false)
      setShowConfirm(false)
      setSelectedTarget(null)
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <Rocket className="w-6 h-6 text-blue-600" />
        <h1 className="text-2xl font-bold">Deployments</h1>
      </div>

      <div className="grid gap-4">
        {DEPLOY_TARGETS.map(target => (
          <div
            key={target.id}
            className={`p-4 border rounded-lg cursor-pointer transition ${
              selectedTarget === target.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => setSelectedTarget(target.id)}
          >
            <h3 className="font-medium">{target.name}</h3>
            <p className="text-sm text-gray-500">{target.description}</p>
          </div>
        ))}
      </div>

      <button
        onClick={() => setShowConfirm(true)}
        disabled={!selectedTarget || isDeploying}
        className="mt-6 w-full py-3 bg-blue-600 text-white rounded-lg font-medium disabled:opacity-50"
      >
        {isDeploying ? 'Deploying...' : 'Deploy Selected'}
      </button>

      {/* Confirmation Modal */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-xl max-w-sm">
            <div className="flex items-center gap-2 text-amber-600 mb-4">
              <AlertTriangle className="w-5 h-5" />
              <h3 className="font-semibold">Confirm Deployment</h3>
            </div>
            <p className="text-gray-600 mb-6">
              Deploy {selectedTarget} to production? This cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowConfirm(false)}
                className="flex-1 py-2 border rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleTriggerDeploy}
                className="flex-1 py-2 bg-blue-600 text-white rounded-lg"
              >
                Deploy
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
```

### Step 6.2: Add backend endpoint

**File:** `/backend/app/routers/admin_domain.py`

Add new endpoint (after existing admin endpoints):
```python
@router.post("/deployments/trigger")
async def trigger_deployment(
    request: DeploymentTriggerRequest,
    current_user: User = Depends(require_admin),
):
    """Trigger GitHub Actions deployment workflow."""
    import httpx

    GITHUB_TOKEN = os.getenv("GITHUB_DEPLOY_TOKEN")
    GITHUB_REPO = "your-org/nerava"  # Update this

    if not GITHUB_TOKEN:
        raise HTTPException(500, "GitHub token not configured")

    # Map target to workflow file
    workflows = {
        "backend": "deploy-backend.yml",
        "driver": "deploy-driver.yml",
        "admin": "deploy-admin.yml",
        "merchant": "deploy-merchant.yml",
    }

    workflow = workflows.get(request.target)
    if not workflow:
        raise HTTPException(400, f"Invalid target: {request.target}")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{workflow}/dispatches",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
            },
            json={"ref": request.ref or "main"},
        )

        if response.status_code != 204:
            raise HTTPException(500, f"GitHub API error: {response.text}")

    return {"status": "triggered", "workflow": workflow}
```

### Step 6.3: Add to admin sidebar

**File:** `/apps/admin/src/components/Sidebar.tsx`

Add Deployments link:
```typescript
{ name: 'Deployments', icon: Rocket, path: '/deployments' }
```

**Acceptance Criteria:**
- [ ] Admin can trigger deploy with confirmation
- [ ] Access controlled (admin only)

---

## Task 7: Demo Simulation Endpoint

### Step 7.1: Add internal demo endpoint

**File:** `/backend/app/routers/admin_domain.py`

```python
@router.post("/internal/demo/simulate-verified-visit")
async def simulate_verified_visit(
    request: DemoSimulateRequest,
    x_internal_secret: str = Header(..., alias="X-Internal-Secret"),
    db: Session = Depends(get_db),
):
    """
    DEV ONLY: Simulate a verified visit for demo purposes.
    Creates ExclusiveSession + RewardEvent.
    """
    INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")
    if x_internal_secret != INTERNAL_SECRET:
        raise HTTPException(403, "Invalid internal secret")

    # Find or create driver
    driver = db.query(User).filter(User.phone == request.driver_phone).first()
    if not driver:
        driver = User(phone=request.driver_phone, auth_provider="phone", role_flags="driver")
        db.add(driver)
        db.flush()

    # Create exclusive session
    session = ExclusiveSession(
        driver_id=driver.id,
        merchant_id=request.merchant_id,
        charger_id=request.charger_id,
        status=ExclusiveSessionStatus.COMPLETED,
        activated_at=datetime.utcnow() - timedelta(minutes=15),
        completed_at=datetime.utcnow(),
    )
    db.add(session)

    # Create reward event
    reward = RewardEvent(
        user_id=driver.id,
        source="MERCHANT",
        gross_cents=0,
        community_cents=0,
        net_cents=0,
        meta={"demo": True, "merchant_id": request.merchant_id},
    )
    db.add(reward)

    db.commit()

    return {
        "session_id": session.id,
        "driver_id": driver.public_id,
        "status": "simulated",
    }
```

**Acceptance Criteria:**
- [ ] Demo simulation creates DB records
- [ ] Records appear in admin portal

---

## Environment Variables Needed

```bash
# OTP
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_VERIFY_SERVICE_SID=xxx
OTP_PROVIDER=twilio_verify

# Admin Deployments
GITHUB_DEPLOY_TOKEN=xxx

# Demo Simulation
INTERNAL_SECRET=xxx
```

---

## Testing Checklist

- [ ] **iOS Safari**: CTA visible, no scroll needed
- [ ] **Google in-app browser**: Content not cut off
- [ ] **Swipe merchants**: No photo flash/reload
- [ ] **Like/unlike**: Persists and shows in account
- [ ] **OTP flow**: Works and returns JWT
- [ ] **Activation**: Requires charger radius
- [ ] **Admin deployments**: Gated + functional
- [ ] **Demo simulator**: Creates DB records

---

**End of Demo-Ready Cleanup Prompt**
