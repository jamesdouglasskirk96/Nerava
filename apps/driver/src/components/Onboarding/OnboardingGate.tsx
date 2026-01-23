// Gate component that shows onboarding if not completed, otherwise shows children
import { useOnboarding } from '../../hooks/useOnboarding'
import { OnboardingFlow } from './OnboardingFlow'
import { useDriverSessionContext } from '../../contexts/DriverSessionContext'
import type { ReactNode } from 'react'

interface OnboardingGateProps {
  children: ReactNode
}

export function OnboardingGate({ children }: OnboardingGateProps) {
  const { hasSeenOnboarding, completeOnboarding } = useOnboarding()
  const { requestLocationPermission, locationPermission, setLocationPermission } = useDriverSessionContext()

  const handleRequestLocation = () => {
    requestLocationPermission()
  }

  const handleSkipLocation = () => {
    // Set location permission to 'skipped' state
    setLocationPermission('skipped')
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

