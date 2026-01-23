import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { initSentry } from './lib/sentry'
import { initAnalytics, track, AnalyticsEvents } from './lib/analytics'
import './index.css'
import App from './App.tsx'

// Initialize Sentry before app renders
initSentry()

// Initialize analytics
initAnalytics()
track(AnalyticsEvents.APP_OPENED)

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
