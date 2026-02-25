// Gate component that shows onboarding if not completed, otherwise shows children
import { useOnboarding } from '../../hooks/useOnboarding'
import { OnboardingFlow } from './OnboardingFlow'
import { useDriverSessionContext } from '../../contexts/DriverSessionContext'
import { useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'

// Routes that must bypass onboarding (e.g. OAuth callbacks)
const BYPASS_PATHS = ['/tesla-callback', '/select-vehicle']

interface OnboardingGateProps {
  children: ReactNode
}

export function OnboardingGate({ children }: OnboardingGateProps) {
  const { hasSeenOnboarding, completeOnboarding } = useOnboarding()
  const { requestLocationPermission, setLocationPermission } = useDriverSessionContext()
  const location = useLocation()

  const handleRequestLocation = () => {
    requestLocationPermission()
  }

  const handleSkipLocation = () => {
    // Set location permission to 'skipped' state
    setLocationPermission('skipped')
  }

  // Always let OAuth callbacks through, even if onboarding is incomplete
  if (BYPASS_PATHS.some(p => location.pathname.startsWith(p))) {
    return <>{children}</>
  }

  if (!hasSeenOnboarding) {
    return (
      <OnboardingFlow
        onComplete={completeOnboarding}
        onRequestLocation={handleRequestLocation}
        onSkipLocation={handleSkipLocation}
      />
    )
  }

  return <>{children}</>
}

