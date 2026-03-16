// Gate component — onboarding is now handled by iOS native layer
// (location permission via ContentView.swift, notification via SessionEngine)
// This gate auto-completes onboarding so the web app goes straight to DriverHome.
import { useOnboarding } from '../../hooks/useOnboarding'
import { useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import type { ReactNode } from 'react'

// Routes that must bypass onboarding (e.g. OAuth callbacks)
const BYPASS_PATHS = ['/tesla-callback', '/tesla-connected', '/select-vehicle']

interface OnboardingGateProps {
  children: ReactNode
}

export function OnboardingGate({ children }: OnboardingGateProps) {
  const { hasSeenOnboarding, completeOnboarding } = useOnboarding()
  const location = useLocation()

  // Auto-complete onboarding — native iOS handles permissions
  useEffect(() => {
    if (!hasSeenOnboarding) {
      completeOnboarding()
    }
  }, [hasSeenOnboarding, completeOnboarding])

  // Always let OAuth callbacks through
  if (BYPASS_PATHS.some(p => location.pathname.startsWith(p))) {
    return <>{children}</>
  }

  return <>{children}</>
}
