import { useEffect } from 'react'

export function useViewportHeight() {
  useEffect(() => {
    const setAppHeight = () => {
      document.documentElement.style.setProperty('--app-height', `${window.innerHeight}px`)
    }

    setAppHeight()
    window.addEventListener('resize', setAppHeight)

    // Best-effort scroll trick for iOS
    window.scrollTo(0, 1)

    return () => window.removeEventListener('resize', setAppHeight)
  }, [])
}




