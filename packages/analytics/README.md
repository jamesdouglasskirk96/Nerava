# @nerava/analytics

Shared analytics wrapper for PostHog across Nerava applications.

## Usage

### Initialization

```typescript
import { initAnalytics } from '@nerava/analytics'

// Initialize analytics at app startup
initAnalytics('driver', {
  enabled: true, // Optional, defaults to env var
  host: 'http://localhost:8080', // Optional, defaults to env var
  key: 'your-posthog-key', // Optional, defaults to env var
  debug: true // Optional, enables console logging
})
```

### Tracking Events

```typescript
import { track } from '@nerava/analytics'

track('button_clicked', {
  button_name: 'activate_exclusive',
  merchant_id: '123',
  path: window.location.pathname
})
```

### Identifying Users

```typescript
import { identify, setUserProps } from '@nerava/analytics'

// Identify user after authentication
identify('user-123', {
  email: 'user@example.com',
  phone: '+1234567890'
})

// Set additional user properties
setUserProps({
  user_type: 'driver',
  last_login_at: new Date().toISOString()
})
```

### Resetting Analytics

```typescript
import { reset } from '@nerava/analytics'

// Call on logout
reset()
```

## Environment Variables

The package supports both Vite and Next.js environment variable prefixes:

- `VITE_POSTHOG_ENABLED` or `NEXT_PUBLIC_POSTHOG_ENABLED` - Enable/disable analytics
- `VITE_POSTHOG_HOST` or `NEXT_PUBLIC_POSTHOG_HOST` - PostHog host URL
- `VITE_POSTHOG_KEY` or `NEXT_PUBLIC_POSTHOG_KEY` - PostHog project API key
- `VITE_ANALYTICS_DEBUG` or `NEXT_PUBLIC_ANALYTICS_DEBUG` - Enable debug logging

## Features

- ✅ Automatic anonymous ID persistence
- ✅ Error handling that never breaks the app
- ✅ Consistent event property enrichment
- ✅ Source/UTM parameter tracking
- ✅ Dev-only by default (requires explicit enable)
- ✅ Debug mode for development







