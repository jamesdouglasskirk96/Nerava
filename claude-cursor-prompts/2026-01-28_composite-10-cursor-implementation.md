# CURSOR IMPLEMENTATION GUIDE: 9.1 → 10.0 Composite Score

**Date:** 2026-01-28
**Validated Baseline:** 9.1 / 10 (verified by Claude Opus 4.5 on 2026-01-27)
**Target:** 10.0 / 10

---

## CONTEXT

The Nerava system has been validated at **9.1/10 composite score** after 4 rounds of gap-closing:
- All P0 blockers: ✅ Resolved
- All P1 items: ✅ Resolved (SQLite check, merchant claim, timer expiration, empty states, pagination, consent config, reputation defaults, landing consent, accessibility)
- Remaining: **8 P2 polish items**

**DO NOT** re-implement items that are already fixed. Focus ONLY on the 8 P2 tasks below.

---

## 8 IMPLEMENTATION TASKS

### Task 1: Skeleton/Shimmer Loading States
**Files:** `apps/driver/src/components/`
**Impact:** +0.3 UX points

Create a reusable skeleton component and add loading states to async data fetches.

**Step 1: Create skeleton component**
```tsx
// apps/driver/src/components/shared/Skeleton.tsx
interface SkeletonProps {
  className?: string
  variant?: 'text' | 'circular' | 'rectangular'
}

export function Skeleton({ className = '', variant = 'rectangular' }: SkeletonProps) {
  const baseClasses = 'animate-pulse bg-gray-200'
  const variantClasses = {
    text: 'h-4 rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg'
  }

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={{
        animationDuration: '1.5s',
        animationTimingFunction: 'ease-in-out'
      }}
    />
  )
}

export function MerchantCardSkeleton() {
  return (
    <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
      <Skeleton className="h-32 w-full" />
      <div className="p-4 space-y-2">
        <Skeleton variant="text" className="w-3/4" />
        <Skeleton variant="text" className="w-1/2" />
        <div className="flex gap-2 mt-3">
          <Skeleton className="h-6 w-16 rounded-full" />
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
      </div>
    </div>
  )
}

export function ChargerCardSkeleton() {
  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm">
      <div className="flex gap-4">
        <Skeleton variant="circular" className="w-12 h-12" />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" className="w-2/3" />
          <Skeleton variant="text" className="w-1/2" />
        </div>
      </div>
    </div>
  )
}
```

**Step 2: Add to DriverHome.tsx**
```tsx
// In DriverHome.tsx, add loading state
import { MerchantCardSkeleton, ChargerCardSkeleton } from './shared/Skeleton'

// In the render, wrap merchant list:
{isLoading ? (
  <div className="grid gap-4">
    {[...Array(3)].map((_, i) => <MerchantCardSkeleton key={i} />)}
  </div>
) : (
  // existing merchant list
)}
```

**Step 3: Add to PreChargingScreen.tsx and WhileYouChargeScreen.tsx**
Apply same pattern with `ChargerCardSkeleton` and `MerchantCardSkeleton`.

---

### Task 2: ORM Migration for Raw SQL Routers
**Files:** `backend/app/routers/intents.py`, `backend/app/routers/activity.py`, `backend/app/models/`
**Impact:** +0.2 maintainability points

Replace raw SQL with SQLAlchemy ORM for type safety and schema change resilience.

**Step 1: Create ChargeIntent model if not exists**
```python
# backend/app/models/charge_intent.py
from sqlalchemy import Column, String, Integer, Float, DateTime, func
from app.db import Base

class ChargeIntent(Base):
    __tablename__ = "charge_intents"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    station_id = Column(String)
    station_name = Column(String)
    merchant_name = Column(String)
    perk_title = Column(String)
    address = Column(String)
    eta_minutes = Column(Integer)
    starts_at = Column(DateTime)
    status = Column(String, default='saved')
    merchant_lat = Column(Float)
    merchant_lng = Column(Float)
    station_lat = Column(Float)
    station_lng = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    merchant = Column(String)
    perk_id = Column(String)
    window_text = Column(String)
    distance_text = Column(String)
```

**Step 2: Update intents.py to use ORM**
```python
# Replace raw SQL in GET /v1/intent
from app.models.charge_intent import ChargeIntent

@router.get("/v1/intent")
async def get_intent(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        intents = db.query(ChargeIntent).filter(
            ChargeIntent.user_id == str(current_user.id)
        ).order_by(ChargeIntent.created_at.desc()).all()

        return [
            {
                'id': i.id,
                'user_id': i.user_id,
                'station_id': i.station_id,
                'station_name': i.station_name,
                'merchant_name': i.merchant_name,
                'perk_title': i.perk_title,
                'address': i.address,
                'eta_minutes': i.eta_minutes,
                'starts_at': i.starts_at.isoformat() if i.starts_at else None,
                'status': i.status or 'saved',
                'merchant_lat': i.merchant_lat,
                'merchant_lng': i.merchant_lng,
                'station_lat': i.station_lat,
                'station_lng': i.station_lng,
                'merchant': i.merchant,
                'perk_id': i.perk_id,
                'window_text': i.window_text,
                'distance_text': i.distance_text,
                'created_at': i.created_at.isoformat() if i.created_at else None
            }
            for i in intents
        ]
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Error fetching intents: {e}", exc_info=True)
        return []
```

**Step 3: Create UserReputation model**
```python
# backend/app/models/user_reputation.py
from sqlalchemy import Column, String, Integer, DateTime, func
from app.db import Base

class UserReputation(Base):
    __tablename__ = "user_reputations"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, unique=True, index=True)
    score = Column(Integer, default=0)
    tier = Column(String, default='Bronze')
    streak_days = Column(Integer, default=0)
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

**Step 4: Update activity.py to use ORM**
```python
from app.models.user_reputation import UserReputation

@router.get("/v1/activity/reputation")
async def get_reputation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rep = db.query(UserReputation).filter(
        UserReputation.user_id == str(current_user.id)
    ).first()

    if rep:
        return {
            'score': rep.score or 0,
            'tier': rep.tier or 'Bronze',
            'streakDays': rep.streak_days or 0,
            'followers_count': rep.followers_count or 0,
            'following_count': rep.following_count or 0,
            'status': 'active'
        }
    else:
        return {
            'score': 0,
            'tier': 'Bronze',
            'streakDays': 0,
            'followers_count': 0,
            'following_count': 0,
            'status': 'new'
        }
```

---

### Task 3: Admin RBAC (Role-Based Access Control)
**Files:** `backend/app/models/user.py`, `backend/app/dependencies_domain.py`, `backend/alembic/versions/`
**Impact:** +0.3 infrastructure points

Add role-based permissions for admin users.

**Step 1: Add AdminRole enum and permissions**
```python
# backend/app/models/admin_role.py
from enum import Enum

class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"      # Full access
    ZONE_MANAGER = "zone_manager"    # Manage merchants in assigned zones
    SUPPORT = "support"              # Read-only + handle support tickets
    ANALYST = "analyst"              # Read-only analytics access

ROLE_PERMISSIONS = {
    AdminRole.SUPER_ADMIN: {
        "merchants": ["read", "write", "delete"],
        "users": ["read", "write", "delete"],
        "analytics": ["read"],
        "settings": ["read", "write"],
        "kill_switch": ["read", "write"],
    },
    AdminRole.ZONE_MANAGER: {
        "merchants": ["read", "write"],
        "users": ["read"],
        "analytics": ["read"],
        "settings": ["read"],
    },
    AdminRole.SUPPORT: {
        "merchants": ["read"],
        "users": ["read"],
        "analytics": ["read"],
    },
    AdminRole.ANALYST: {
        "analytics": ["read"],
        "merchants": ["read"],
    },
}

def has_permission(role: AdminRole, resource: str, action: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, {})
    return action in perms.get(resource, [])
```

**Step 2: Add admin_role to User model**
```python
# In backend/app/models/user.py, add:
from app.models.admin_role import AdminRole

class User(Base):
    # ... existing fields ...
    admin_role = Column(String, nullable=True)  # AdminRole enum value
```

**Step 3: Create migration**
```python
# backend/alembic/versions/061_add_admin_role_to_users.py
"""Add admin_role to users table

Revision ID: 061
"""
from alembic import op
import sqlalchemy as sa

revision = '061'
down_revision = '060'

def upgrade():
    op.add_column('users', sa.Column('admin_role', sa.String(), nullable=True))

def downgrade():
    op.drop_column('users', 'admin_role')
```

**Step 4: Add permission check dependency**
```python
# In backend/app/dependencies_domain.py, add:
from app.models.admin_role import AdminRole, has_permission
from fastapi import HTTPException

def require_permission(resource: str, action: str):
    def dependency(current_user: User = Depends(get_current_admin_user)):
        if not current_user.admin_role:
            raise HTTPException(status_code=403, detail="No admin role assigned")

        role = AdminRole(current_user.admin_role)
        if not has_permission(role, resource, action):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {action} on {resource}"
            )
        return current_user
    return dependency

# Usage in routers:
# @router.delete("/merchants/{id}")
# async def delete_merchant(
#     id: str,
#     admin: User = Depends(require_permission("merchants", "delete"))
# ):
```

---

### Task 4: Open Graph / Twitter Card Meta Tags
**Files:** `apps/landing/app/layout.tsx`
**Impact:** +0.2 compliance points

Add SEO meta tags for better social sharing.

```tsx
// apps/landing/app/layout.tsx
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Nerava - Turn EV Charging into Local Discovery',
  description: 'Discover local restaurants, cafes, and experiences while your EV charges. Exclusive perks for drivers.',
  keywords: ['EV charging', 'electric vehicle', 'local discovery', 'restaurant deals', 'charging stations'],
  authors: [{ name: 'Nerava' }],
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://nerava.network',
    siteName: 'Nerava',
    title: 'Nerava - Turn EV Charging into Local Discovery',
    description: 'Discover local restaurants, cafes, and experiences while your EV charges. Exclusive perks for drivers.',
    images: [
      {
        url: 'https://nerava.network/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Nerava - EV Charging Discovery',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Nerava - Turn EV Charging into Local Discovery',
    description: 'Discover local restaurants, cafes, and experiences while your EV charges.',
    images: ['https://nerava.network/twitter-card.png'],
    creator: '@neaborhood',
  },
  robots: {
    index: true,
    follow: true,
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
}
```

**Note:** Create `og-image.png` (1200x630) and `twitter-card.png` (1200x600) in `apps/landing/public/`.

---

### Task 5: prefers-reduced-motion Support
**Files:** `apps/driver/src/index.css`
**Impact:** +0.2 accessibility points

Add CSS media query to disable animations for motion-sensitive users.

```css
/* apps/driver/src/index.css - add at the end */

/* Respect user's motion preferences */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  /* Disable specific animations */
  .animate-pulse,
  .animate-spin,
  .animate-bounce,
  .animate-ping {
    animation: none !important;
  }
}
```

Also update Tailwind config to include reduced-motion variant:
```js
// apps/driver/tailwind.config.js
module.exports = {
  // ... existing config
  theme: {
    extend: {
      // ... existing extensions
    },
  },
  plugins: [],
  // Add this to enable motion-reduce variant
  future: {
    respectDefaultRingColorOpacity: true,
  },
}
```

---

### Task 6: Next.js Image Optimization for Landing Page
**Files:** `apps/landing/app/page.tsx`, `apps/landing/next.config.js`
**Impact:** +0.2 performance points

Replace unoptimized PNGs with Next.js Image component.

**Step 1: Update next.config.js**
```js
// apps/landing/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
}

module.exports = nextConfig
```

**Step 2: Replace img tags with Image component**
```tsx
// In landing page components, replace:
// <img src="/hero-image.png" alt="..." />

// With:
import Image from 'next/image'

<Image
  src="/hero-image.png"
  alt="Nerava app showing nearby merchants while charging"
  width={800}
  height={600}
  priority // for above-the-fold images
  placeholder="blur"
  blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDA..."
/>
```

**Step 3: Optimize existing images**
Run: `npx next-image-optimize` or manually convert large PNGs to WebP/AVIF.

---

### Task 7: iOS Deep-Link Routing (Documentation)
**Files:** `docs/ios-deep-link-routing.md`
**Impact:** +0.1 infrastructure points

This is primarily a native iOS change. Create documentation for the iOS developer.

```markdown
# iOS Deep-Link Routing Implementation

## Overview
Enable deep-link routing so push notifications can open specific screens.

## URL Scheme
Register `nerava://` scheme in Info.plist:
```xml
<key>CFBundleURLTypes</key>
<array>
  <dict>
    <key>CFBundleURLSchemes</key>
    <array>
      <string>nerava</string>
    </array>
  </dict>
</array>
```

## Universal Links
Add Associated Domains capability:
- `applinks:app.nerava.network`
- `applinks:nerava.network`

## Route Mapping
| Deep Link | Web Path | Screen |
|-----------|----------|--------|
| `nerava://charger/{id}` | `/charger/{id}` | Charger details |
| `nerava://merchant/{id}` | `/merchant/{id}` | Merchant details |
| `nerava://session/{id}` | `/session/{id}` | Active session |
| `nerava://wallet` | `/wallet` | Wallet screen |

## Implementation
In `AppDelegate.swift`:
```swift
func application(_ app: UIApplication, open url: URL, options: [UIApplication.OpenURLOptionsKey : Any] = [:]) -> Bool {
    guard let components = URLComponents(url: url, resolvingAgainstBaseURL: true),
          let host = components.host else { return false }

    let path = "/\(host)\(components.path)"
    webView?.evaluateJavaScript("window.location.href = '\(path)'")
    return true
}
```

## Testing
1. `xcrun simctl openurl booted "nerava://merchant/abc123"`
2. Verify WebView navigates to `/merchant/abc123`
```

---

### Task 8: aria-live on Timer Countdown
**Files:** `apps/driver/src/components/ExclusiveActiveView/ExclusiveActiveView.tsx`
**Impact:** +0.1 accessibility points

Add `aria-live` so screen readers announce timer changes.

```tsx
// In ExclusiveActiveView.tsx, update the countdown timer div:

{/* Countdown Timer — color-coded urgency */}
<div className="absolute bottom-4 left-4 right-4 flex justify-center">
  <div
    className={`px-4 py-2 backdrop-blur-sm rounded-full border ${
      minutes <= 0
        ? 'bg-red-50/95 border-red-300'
        : minutes <= 5
        ? 'bg-red-50/95 border-red-300'
        : minutes <= 15
        ? 'bg-yellow-50/95 border-yellow-300'
        : 'bg-white/95 border-[#E4E6EB]'
    }`}
    role="timer"
    aria-live="polite"
    aria-atomic="true"
    aria-label={
      minutes <= 0
        ? 'Session expired'
        : `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} remaining`
    }
  >
    <span className={`text-sm font-medium ${
      minutes <= 0
        ? 'text-red-600'
        : minutes <= 5
        ? 'text-red-600'
        : minutes <= 15
        ? 'text-yellow-700'
        : 'text-[#050505]'
    }`}>
      {minutes <= 0
        ? 'Expired'
        : `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} remaining`
      }
    </span>
  </div>
</div>
```

**Note:** `aria-live="polite"` announces changes without interrupting. `aria-atomic="true"` reads the entire region on change.

---

## VALIDATION CHECKLIST

After implementing all 8 tasks, verify:

### Code Quality
- [ ] TypeScript compiles: `cd apps/driver && npx tsc --noEmit`
- [ ] Python tests pass: `cd backend && pytest -q`
- [ ] No linter errors: `npm run lint` and `ruff check backend/`
- [ ] Migrations apply: `cd backend && alembic upgrade head`

### Functionality
- [ ] Skeleton loaders appear during network requests
- [ ] ORM queries work (no raw SQL errors)
- [ ] Admin RBAC blocks unauthorized actions
- [ ] Social share preview shows correct meta tags
- [ ] Animations disabled with `prefers-reduced-motion: reduce`
- [ ] Landing images load as WebP/AVIF
- [ ] Timer announces changes to screen readers

### Performance
- [ ] Landing page images < 500KB total
- [ ] No N+1 queries introduced

---

## EXPECTED OUTCOME

| Dimension | Before | After | Delta |
|-----------|--------|-------|-------|
| App Logic & Features | 9.7 | 10.0 | +0.3 |
| Infrastructure & Ops | 8.0 | 9.5 | +1.5 |
| Compliance & Privacy | 9.2 | 9.8 | +0.6 |
| Performance & Scale | 9.0 | 9.8 | +0.8 |
| UX & Polish | 9.3 | 10.0 | +0.7 |
| **Composite** | **9.1** | **10.0** | **+0.9** |

---

*Cursor: Implement these 8 tasks in order. Keep changes surgical. Use existing patterns. No new dependencies unless specified.*
