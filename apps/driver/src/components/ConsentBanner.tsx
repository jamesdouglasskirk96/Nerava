import { useEffect } from 'react'

export function ConsentBanner() {
  // Auto-accept analytics — no banner shown to users
  useEffect(() => {
    if (!localStorage.getItem('consent_analytics')) {
      localStorage.setItem('consent_analytics', 'granted')
    }
  }, [])

  return null
}
