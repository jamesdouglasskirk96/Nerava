# Demo-Ready UI Implementation

**Date:** 2026-01-23
**Priority:** P0 - Needed for live merchant demos
**Tech Stack:** React 19, Vite, TailwindCSS 4, TypeScript

---

## Context

The driver app needs several UX improvements before live merchant demos. All changes should maintain the existing design language and work reliably on iOS Safari, Chrome, and in-app browsers.

**Current state:** v19 backend is running, OTP works but times out. Frontend needs viewport fixes, image caching, favorites sync, and account page.

---

## Task 1: Viewport/Fullscreen Hardening (P0)

### Problem
iOS Safari toolbar and in-app browser chrome cause layout issues. Content gets hidden behind browser UI, especially the CTA button.

### Implementation

**File: `apps/driver/index.html`**

Add these meta tags in `<head>`:
```html
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Nerava">
<meta name="mobile-web-app-capable" content="yes">
```

**File: `apps/driver/src/index.css`**

Update body and :root:
```css
:root {
  --app-height: 100dvh;
}

body {
  padding-bottom: env(safe-area-inset-bottom, 0);
}

#root {
  height: var(--app-height);
  width: 100%;
  overflow: hidden;
}
```

**File: `apps/driver/src/hooks/useViewportHeight.ts` (NEW)**

```typescript
import { useEffect } from 'react';

export function useViewportHeight() {
  useEffect(() => {
    const setViewportHeight = () => {
      const vh = window.innerHeight;
      document.documentElement.style.setProperty('--app-height', `${vh}px`);
    };

    setViewportHeight();
    window.addEventListener('resize', setViewportHeight);
    window.addEventListener('orientationchange', setViewportHeight);

    // iOS scroll trick to stabilize viewport
    const scrollFix = () => {
      if (window.scrollY !== 0) {
        window.scrollTo(0, 0);
      }
    };
    window.addEventListener('scroll', scrollFix, { passive: true });

    return () => {
      window.removeEventListener('resize', setViewportHeight);
      window.removeEventListener('orientationchange', setViewportHeight);
      window.removeEventListener('scroll', scrollFix);
    };
  }, []);
}
```

**File: `apps/driver/src/App.tsx`**

Add the hook:
```typescript
import { useViewportHeight } from './hooks/useViewportHeight';

function App() {
  useViewportHeight();
  // ... rest of component
}
```

**File: `apps/driver/src/components/MerchantDetail/MerchantDetailModal.tsx`**

Add safe-area padding to CTA container:
```typescript
// Find the bottom CTA button container and add:
<div className="fixed bottom-0 left-0 right-0 p-4 pb-[calc(1rem+env(safe-area-inset-bottom))] bg-white border-t">
  {/* CTA button */}
</div>
```

### Acceptance Criteria
- [ ] App fills viewport without scrolling
- [ ] CTA button never hidden behind iOS Safari toolbar
- [ ] No layout shift on route changes
- [ ] Works in standalone PWA mode

---

## Task 2: Image Caching System (P0)

### Problem
Merchant photos flash/reload when swiping carousel. Same images load multiple times per session.

### Implementation

**File: `apps/driver/src/utils/imageCache.ts` (NEW)**

```typescript
const imageCache = new Map<string, string>();

export function getCachedImage(url: string): string | null {
  return imageCache.get(url) || null;
}

export function setCachedImage(url: string, objectUrl: string): void {
  imageCache.set(url, objectUrl);
}

export function preloadImage(url: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (imageCache.has(url)) {
      resolve();
      return;
    }

    const img = new Image();
    img.onload = () => {
      setCachedImage(url, url);
      resolve();
    };
    img.onerror = reject;
    img.src = url;
  });
}

export function preloadImages(urls: string[]): Promise<void[]> {
  return Promise.all(urls.map(preloadImage));
}
```

**File: `apps/driver/src/components/shared/ImageWithFallback.tsx`**

Update to use cache:
```typescript
import { getCachedImage, setCachedImage } from '../../utils/imageCache';

export function ImageWithFallback({ src, alt, fallback, className }: Props) {
  const cachedSrc = getCachedImage(src);
  const [imgSrc, setImgSrc] = useState(cachedSrc || src);
  const [loaded, setLoaded] = useState(!!cachedSrc);

  const handleLoad = () => {
    setCachedImage(src, src);
    setLoaded(true);
  };

  // ... rest of component
}
```

**File: `apps/driver/src/components/DriverHome/DriverHome.tsx`**

Add preloading effect:
```typescript
import { preloadImage } from '../../utils/imageCache';

// Inside component:
useEffect(() => {
  if (merchants.length > currentIndex + 1) {
    const nextMerchant = merchants[currentIndex + 1];
    if (nextMerchant?.photo_url) {
      preloadImage(nextMerchant.photo_url);
    }
  }
}, [currentIndex, merchants]);
```

### Acceptance Criteria
- [ ] No flash when returning to previously viewed merchant
- [ ] Smooth carousel transitions
- [ ] Next image preloads while viewing current
- [ ] Memory efficient (Map-based, not unlimited)

---

## Task 3: Unified Favorites System (P0)

### Problem
Favorites stored only in localStorage, don't sync with backend. Inconsistent state between sessions.

### Implementation

**File: `apps/driver/src/contexts/FavoritesContext.tsx` (NEW)**

```typescript
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { getAuthToken } from '../services/auth';

interface FavoritesContextType {
  favorites: Set<string>;
  isFavorite: (merchantId: string) => boolean;
  toggleFavorite: (merchantId: string) => Promise<void>;
  loading: boolean;
}

const FavoritesContext = createContext<FavoritesContextType | null>(null);

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://api.nerava.network';
const STORAGE_KEY = 'neravaLikes';

export function FavoritesProvider({ children }: { children: ReactNode }) {
  const [favorites, setFavorites] = useState<Set<string>>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? new Set(JSON.parse(stored)) : new Set();
  });
  const [loading, setLoading] = useState(false);

  // Sync with backend when authenticated
  useEffect(() => {
    const token = getAuthToken();
    if (!token) return;

    const fetchFavorites = async () => {
      try {
        const response = await fetch(`${API_BASE}/v1/merchants/favorites`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          const ids = data.map((m: { id: string }) => m.id);
          setFavorites(new Set(ids));
          localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
        }
      } catch (e) {
        console.error('Failed to fetch favorites:', e);
      }
    };
    fetchFavorites();
  }, []);

  const isFavorite = (merchantId: string) => favorites.has(merchantId);

  const toggleFavorite = async (merchantId: string) => {
    const token = getAuthToken();
    const isCurrentlyFavorite = favorites.has(merchantId);

    // Optimistic update
    setFavorites(prev => {
      const next = new Set(prev);
      if (isCurrentlyFavorite) {
        next.delete(merchantId);
      } else {
        next.add(merchantId);
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify([...next]));
      return next;
    });

    // Sync with backend if authenticated
    if (token) {
      try {
        const method = isCurrentlyFavorite ? 'DELETE' : 'POST';
        const response = await fetch(`${API_BASE}/v1/merchants/${merchantId}/favorite`, {
          method,
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to sync');
      } catch (e) {
        // Rollback on failure
        setFavorites(prev => {
          const next = new Set(prev);
          if (isCurrentlyFavorite) {
            next.add(merchantId);
          } else {
            next.delete(merchantId);
          }
          localStorage.setItem(STORAGE_KEY, JSON.stringify([...next]));
          return next;
        });
      }
    }
  };

  return (
    <FavoritesContext.Provider value={{ favorites, isFavorite, toggleFavorite, loading }}>
      {children}
    </FavoritesContext.Provider>
  );
}

export function useFavorites() {
  const context = useContext(FavoritesContext);
  if (!context) throw new Error('useFavorites must be used within FavoritesProvider');
  return context;
}
```

**File: `apps/driver/src/App.tsx`**

Wrap with provider:
```typescript
import { FavoritesProvider } from './contexts/FavoritesContext';

function App() {
  return (
    <FavoritesProvider>
      {/* existing content */}
    </FavoritesProvider>
  );
}
```

**File: `apps/driver/src/components/DriverHome/DriverHome.tsx`**

Replace local state with context:
```typescript
import { useFavorites } from '../../contexts/FavoritesContext';

// Inside component:
const { isFavorite, toggleFavorite } = useFavorites();

// Replace: const [likedMerchants, setLikedMerchants] = useState(...)
// Replace: handleToggleLike function with toggleFavorite
// Replace: likedMerchants.has(id) with isFavorite(id)
```

### Acceptance Criteria
- [ ] Favorites persist across sessions
- [ ] Sync with backend when authenticated
- [ ] Optimistic updates (instant UI feedback)
- [ ] Rollback on failure
- [ ] Works offline (localStorage fallback)

---

## Task 4: Account Page with Phone Number (P0)

### Problem
No way for users to see their account info or logout. Phone number not visible after login.

### Implementation

**File: `apps/driver/src/components/Account/AccountPage.tsx` (NEW)**

```typescript
import { X, LogOut, Heart } from 'lucide-react';
import { useFavorites } from '../../contexts/FavoritesContext';

interface AccountPageProps {
  onClose: () => void;
  onLogout: () => void;
}

export function AccountPage({ onClose, onLogout }: AccountPageProps) {
  const { favorites } = useFavorites();

  // Get user data from localStorage
  const userData = JSON.parse(localStorage.getItem('nerava_user') || '{}');
  const phone = userData.phone || '';

  // Mask phone: +1234567890 -> ***-***-7890
  const maskedPhone = phone ? `***-***-${phone.slice(-4)}` : 'Not set';

  return (
    <div className="fixed inset-0 bg-white z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <h1 className="text-xl font-semibold">Account</h1>
        <button onClick={onClose} className="p-2 -m-2">
          <X className="w-6 h-6" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 p-4 space-y-6">
        {/* Phone Number */}
        <div>
          <label className="text-sm text-gray-500">Phone Number</label>
          <p className="text-lg font-medium">{maskedPhone}</p>
        </div>

        {/* Favorites Count */}
        <div className="flex items-center gap-2">
          <Heart className="w-5 h-5 text-red-500 fill-red-500" />
          <span>{favorites.size} favorite merchants</span>
        </div>
      </div>

      {/* Logout Button */}
      <div className="p-4 pb-[calc(1rem+env(safe-area-inset-bottom))] border-t">
        <button
          onClick={onLogout}
          className="w-full flex items-center justify-center gap-2 py-3 bg-red-50 text-red-600 rounded-lg font-medium"
        >
          <LogOut className="w-5 h-5" />
          Log Out
        </button>
      </div>
    </div>
  );
}
```

**File: `apps/driver/src/services/auth.ts`**

Store user data after OTP verification:
```typescript
// In otpVerify function, after successful verification:
localStorage.setItem('nerava_user', JSON.stringify({
  public_id: response.public_id,
  auth_provider: response.auth_provider,
  phone: phone // the phone number used for OTP
}));
```

**File: `apps/driver/src/components/DriverHome/DriverHome.tsx`**

Add account button and modal:
```typescript
import { User } from 'lucide-react';
import { AccountPage } from '../Account/AccountPage';
import { getAuthToken, logout } from '../../services/auth';

// Inside component:
const [showAccountPage, setShowAccountPage] = useState(false);
const isAuthenticated = !!getAuthToken();

const handleLogout = () => {
  logout();
  setShowAccountPage(false);
  // Optionally refresh state
};

// In header:
{isAuthenticated && (
  <button onClick={() => setShowAccountPage(true)} className="p-2 -m-2">
    <User className="w-6 h-6" />
  </button>
)}

// Render modal:
{showAccountPage && (
  <AccountPage
    onClose={() => setShowAccountPage(false)}
    onLogout={handleLogout}
  />
)}
```

### Acceptance Criteria
- [ ] Account page accessible from header when authenticated
- [ ] Phone number displayed masked (***-***-1234)
- [ ] Favorites count shown
- [ ] Logout clears tokens and closes modal
- [ ] Safe-area padding on logout button

---

## Task 5: OTP Flow Reliability (P0)

### Problem
OTP requests hang indefinitely when backend is slow. No timeout or cancellation.

### Implementation

**File: `apps/driver/src/services/auth.ts`**

Add timeout to otpStart:
```typescript
export async function otpStart(phone: string): Promise<OTPStartResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout

  try {
    const cleaned = phone.replace(/\D/g, '');
    const normalizedPhone = cleaned.length === 10 ? `+1${cleaned}` : `+${cleaned}`;

    const response = await fetch(`${API_BASE_URL}/v1/auth/otp/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: normalizedPhone }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const data = await response.json();
      throw new ApiError(response.status, data.detail || 'Failed to send OTP');
    }

    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiError(408, 'Request timed out. Please try again.');
    }
    throw error;
  }
}
```

**File: `apps/driver/src/components/ActivateExclusiveModal/ActivateExclusiveModal.tsx`**

Enhance loading state:
```typescript
// In the "Send Code" button:
<button
  disabled={sending || !isValidPhone}
  className="..."
>
  {sending ? (
    <span className="flex items-center gap-2">
      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
      Sending code...
    </span>
  ) : (
    'Send Code'
  )}
</button>
```

### Acceptance Criteria
- [ ] OTP request times out after 15 seconds
- [ ] User sees clear error message on timeout
- [ ] Loading spinner during send
- [ ] Button disabled while sending
- [ ] Clean abort on component unmount

---

## Testing Checklist

After implementing all tasks, test on:
- [ ] iOS Safari (iPhone 12+)
- [ ] Chrome Android
- [ ] In-app browser (Instagram, TikTok)
- [ ] Desktop Chrome (dev tools mobile mode)

Test flows:
- [ ] Open app, swipe through merchants - no image flash
- [ ] Like/unlike merchants - persists after refresh
- [ ] Login with OTP - timeout handled gracefully
- [ ] View account page - phone masked correctly
- [ ] Logout - tokens cleared, favorites synced

---

## Notes

- Keep existing Tailwind classes and design patterns
- All new components should match existing styling
- Use lucide-react for icons (already installed)
- Test on real device before deploying
- Backend endpoints already exist, just need frontend integration

