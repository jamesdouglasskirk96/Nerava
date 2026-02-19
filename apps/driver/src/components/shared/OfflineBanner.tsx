// Offline detection banner — shows when network connection is lost
import { useState, useEffect } from 'react'
import { WifiOff } from 'lucide-react'

/**
 * Monitors navigator.onLine and renders a sticky banner when offline.
 * Auto-dismisses when connectivity is restored.
 */
export function OfflineBanner() {
  const [isOffline, setIsOffline] = useState(!navigator.onLine)

  useEffect(() => {
    const handleOffline = () => setIsOffline(true)
    const handleOnline = () => setIsOffline(false)

    window.addEventListener('offline', handleOffline)
    window.addEventListener('online', handleOnline)

    return () => {
      window.removeEventListener('offline', handleOffline)
      window.removeEventListener('online', handleOnline)
    }
  }, [])

  if (!isOffline) return null

  return (
    <div
      className="sticky top-0 z-[80] bg-[#050505] text-white px-4 py-3 flex items-center justify-center gap-2"
      role="alert"
      aria-live="assertive"
    >
      <WifiOff className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
      <span className="text-sm font-medium">You're offline. Some features may not work.</span>
    </div>
  )
}
