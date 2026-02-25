import { useState, useEffect, useRef } from 'react'

/**
 * Hook that tracks page visibility (foreground/background).
 * Returns `true` when page is visible, `false` when hidden.
 *
 * Also fires an optional onForeground callback when app returns
 * from background — useful for refreshing stale data, location, etc.
 */
export function usePageVisibility(onForeground?: () => void): boolean {
  const [isVisible, setIsVisible] = useState(!document.hidden)
  const callbackRef = useRef(onForeground)
  callbackRef.current = onForeground

  useEffect(() => {
    const handleVisibility = () => {
      const visible = !document.hidden
      setIsVisible(visible)
      if (visible && callbackRef.current) {
        callbackRef.current()
      }
    }

    document.addEventListener('visibilitychange', handleVisibility)
    return () => document.removeEventListener('visibilitychange', handleVisibility)
  }, [])

  return isVisible
}

/**
 * Hook that creates an interval that automatically pauses when the page
 * is hidden (backgrounded) and resumes when visible again.
 * Also fires immediately on foreground return so data isn't stale.
 */
export function useVisibilityAwareInterval(
  callback: () => void,
  intervalMs: number,
  enabled: boolean = true,
) {
  const callbackRef = useRef(callback)
  callbackRef.current = callback

  const isVisible = usePageVisibility()

  useEffect(() => {
    if (!enabled || !isVisible) return

    // Fire immediately on (re-)activation
    callbackRef.current()

    const id = setInterval(() => callbackRef.current(), intervalMs)
    return () => clearInterval(id)
  }, [enabled, isVisible, intervalMs])
}
