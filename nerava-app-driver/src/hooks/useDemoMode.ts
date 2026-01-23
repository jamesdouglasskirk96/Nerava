// Hook for demo mode toggle (?demo=1)
import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate, useLocation } from 'react-router-dom'

export type DemoState = 'charging' | 'pre-charging'

export function useDemoMode() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const location = useLocation()
  const isDemoMode = searchParams.get('demo') === '1'

  const [currentState, setCurrentState] = useState<DemoState>(() => {
    // Determine initial state from current route
    if (location.pathname === '/pre-charging') {
      return 'pre-charging'
    }
    return 'charging'
  })

  useEffect(() => {
    // Update state when route changes
    if (location.pathname === '/pre-charging') {
      setCurrentState('pre-charging')
    } else if (location.pathname === '/wyc' || location.pathname === '/') {
      setCurrentState('charging')
    }
  }, [location.pathname])

  const toggleState = () => {
    if (!isDemoMode) return

    const newState: DemoState = currentState === 'charging' ? 'pre-charging' : 'charging'
    setCurrentState(newState)

    // Navigate to appropriate route
    if (newState === 'pre-charging') {
      navigate('/pre-charging?demo=1')
    } else {
      navigate('/wyc?demo=1')
    }
  }

  return {
    isDemoMode,
    currentState,
    toggleState,
  }
}

