'use client'
import { useState, useEffect } from 'react'

export function ConsentBanner() {
  const [show, setShow] = useState(false)
  const [analyticsEnabled, setAnalyticsEnabled] = useState(false)

  useEffect(() => {
    // Check if PostHog is enabled
    const posthogKey = process.env.NEXT_PUBLIC_POSTHOG_KEY
    const analyticsEnabledEnv = process.env.NEXT_PUBLIC_ANALYTICS_ENABLED !== 'false'
    const isEnabled = analyticsEnabledEnv && !!posthogKey
    setAnalyticsEnabled(isEnabled)

    // Only show banner if analytics is enabled and consent not set
    if (isEnabled) {
      const consent = localStorage.getItem('consent_analytics')
      if (!consent) {
        setShow(true)
      }
    }
  }, [])

  const handleAccept = () => {
    localStorage.setItem('consent_analytics', 'granted')
    setShow(false)
  }

  const handleDecline = () => {
    localStorage.setItem('consent_analytics', 'denied')
    setShow(false)
  }

  if (!show || !analyticsEnabled) {
    return null
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-neutral-200 shadow-lg p-4">
      <div className="max-w-4xl mx-auto flex items-center justify-between gap-4">
        <div className="flex-1">
          <p className="text-sm text-neutral-700">
            We use analytics to improve your experience. You can accept or decline analytics cookies.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDecline}
            className="px-4 py-2 text-sm font-medium text-neutral-700 bg-neutral-100 hover:bg-neutral-200 rounded-lg transition-colors"
          >
            Decline
          </button>
          <button
            onClick={handleAccept}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            Accept analytics
          </button>
        </div>
      </div>
    </div>
  )
}
