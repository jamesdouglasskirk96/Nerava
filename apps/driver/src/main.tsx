// Sentry must init before anything else
import './sentry'

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App.tsx'
import { init as initAnalytics, storeSourceParams, capture, DRIVER_EVENTS } from './analytics'

// Initialize analytics before rendering
initAnalytics()

// Capture session start with query params
const searchParams = new URLSearchParams(window.location.search)
storeSourceParams(searchParams)
capture(DRIVER_EVENTS.SESSION_START, {
  src: searchParams.get('src'),
  cta: searchParams.get('cta'),
  utm_source: searchParams.get('utm_source'),
  utm_medium: searchParams.get('utm_medium'),
  utm_campaign: searchParams.get('utm_campaign'),
})

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
