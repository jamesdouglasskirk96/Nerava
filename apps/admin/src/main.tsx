import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { init as initAnalytics, storeSourceParams, capture, ADMIN_EVENTS } from './analytics'

// Initialize analytics before rendering
initAnalytics()

// Capture session start with query params
const searchParams = new URLSearchParams(window.location.search)
storeSourceParams(searchParams)
capture(ADMIN_EVENTS.SESSION_START, {
  src: searchParams.get('src'),
  cta: searchParams.get('cta'),
  utm_source: searchParams.get('utm_source'),
  utm_medium: searchParams.get('utm_medium'),
  utm_campaign: searchParams.get('utm_campaign'),
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)







