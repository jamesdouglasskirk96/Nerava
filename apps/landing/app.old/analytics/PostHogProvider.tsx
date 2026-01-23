'use client'

import { useEffect } from 'react'
import { usePathname, useSearchParams } from 'next/navigation'
import { initPostHog, page } from './posthog'

/**
 * PostHog provider component for Next.js
 * Initializes PostHog and captures page views
 */
export function PostHogProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const searchParams = useSearchParams()

  useEffect(() => {
    // Initialize PostHog on mount
    initPostHog()
  }, [])

  useEffect(() => {
    // Capture page view on route change
    if (pathname) {
      page(pathname)
    }
  }, [pathname, searchParams])

  return <>{children}</>
}

