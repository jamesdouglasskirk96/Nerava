// Hook for managing onboarding state
import { useState, useEffect } from 'react'

const ONBOARDING_STORAGE_KEY = 'nerava_onboarding_seen'

export function useOnboarding() {
  const [hasSeenOnboarding, setHasSeenOnboarding] = useState<boolean>(() => {
    return localStorage.getItem(ONBOARDING_STORAGE_KEY) === 'true'
  })

  const completeOnboarding = () => {
    localStorage.setItem(ONBOARDING_STORAGE_KEY, 'true')
    setHasSeenOnboarding(true)
  }

  return {
    hasSeenOnboarding,
    completeOnboarding,
  }
}


