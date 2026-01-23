// State management hook for exclusive activation state
import { useState, useEffect, useCallback } from 'react'

export interface ExclusiveMerchant {
  id: string
  name: string
  category?: string
  walkTime: string
  imageUrl?: string | null
  badge?: string
  distance?: string
  hours?: string
  hoursStatus?: string
  description?: string
  exclusiveOffer?: string // The exclusive offer description
  expiresAt?: string // ISO 8601 expiration timestamp from backend
}

const STORAGE_KEY = 'nerava_active_exclusive'
const STORAGE_START_TIME_KEY = 'nerava_exclusive_start_time'

const EXCLUSIVE_DURATION_MINUTES = 60

/**
 * Hook to manage exclusive activation state
 * - Tracks active exclusive merchant (null | ExclusiveMerchant)
 * - Manages 60-minute countdown timer (mocked with setInterval)
 * - Persists to localStorage
 */
export function useExclusiveSessionState() {
  const [activeExclusive, setActiveExclusive] = useState<ExclusiveMerchant | null>(() => {
    // Load from localStorage on mount
    const stored = localStorage.getItem(STORAGE_KEY)
    const startTime = localStorage.getItem(STORAGE_START_TIME_KEY)
    
    if (stored && startTime) {
      try {
        const merchant = JSON.parse(stored) as ExclusiveMerchant
        const start = parseInt(startTime, 10)
        const elapsed = Date.now() - start
        const elapsedMinutes = Math.floor(elapsed / 60000)
        
        // If expired, clear it
        if (elapsedMinutes >= EXCLUSIVE_DURATION_MINUTES) {
          localStorage.removeItem(STORAGE_KEY)
          localStorage.removeItem(STORAGE_START_TIME_KEY)
          return null
        }
        
        return merchant
      } catch {
        // Invalid JSON, clear it
        localStorage.removeItem(STORAGE_KEY)
        localStorage.removeItem(STORAGE_START_TIME_KEY)
        return null
      }
    }
    return null
  })

  const [remainingMinutes, setRemainingMinutes] = useState<number>(() => {
    const startTime = localStorage.getItem(STORAGE_START_TIME_KEY)
    const expiresAt = localStorage.getItem('nerava_exclusive_expires_at')
    
    if (startTime && activeExclusive) {
      if (expiresAt) {
        // Use backend expires_at
        const expiresDate = new Date(expiresAt).getTime()
        const now = Date.now()
        const remainingMs = Math.max(0, expiresDate - now)
        return Math.floor(remainingMs / 60000)
      } else {
        // Use default 60 minutes
        const start = parseInt(startTime, 10)
        const elapsed = Date.now() - start
        const elapsedMinutes = Math.floor(elapsed / 60000)
        return Math.max(0, EXCLUSIVE_DURATION_MINUTES - elapsedMinutes)
      }
    }
    return 0
  })

  // Define callbacks before effects that use them
  const activateExclusive = useCallback((merchant: ExclusiveMerchant, expiresAt?: string) => {
    const now = Date.now()
    setActiveExclusive(merchant)

    // Use backend expires_at if provided, otherwise use default 60 minutes
    let expirationTime: number
    if (expiresAt) {
      const expiresDate = new Date(expiresAt).getTime()
      expirationTime = expiresDate
      // Store expires_at in localStorage for persistence
      localStorage.setItem('nerava_exclusive_expires_at', expiresAt)
    } else {
      expirationTime = now + EXCLUSIVE_DURATION_MINUTES * 60000
      localStorage.removeItem('nerava_exclusive_expires_at')
    }

    const remainingMs = Math.max(0, expirationTime - now)
    const remainingMins = Math.floor(remainingMs / 60000)
    setRemainingMinutes(remainingMins)

    // Persist to localStorage
    localStorage.setItem(STORAGE_KEY, JSON.stringify(merchant))
    localStorage.setItem(STORAGE_START_TIME_KEY, String(now))
  }, [])

  const clearExclusive = useCallback(() => {
    setActiveExclusive(null)
    setRemainingMinutes(0)
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(STORAGE_START_TIME_KEY)
    localStorage.removeItem('nerava_exclusive_expires_at')
  }, [])

  // Timer countdown - updates every minute
  useEffect(() => {
    if (!activeExclusive) {
      // Remaining minutes is already 0 from initial state or clearExclusive
      return
    }

    const startTime = localStorage.getItem(STORAGE_START_TIME_KEY)
    const expiresAt = localStorage.getItem('nerava_exclusive_expires_at')
    if (!startTime) return

    const updateTimer = () => {
      let remaining: number
      
      if (expiresAt) {
        // Use backend expires_at
        const expiresDate = new Date(expiresAt).getTime()
        const now = Date.now()
        const remainingMs = Math.max(0, expiresDate - now)
        remaining = Math.floor(remainingMs / 60000)
      } else {
        // Use default 60 minutes
        const start = parseInt(startTime, 10)
        const elapsed = Date.now() - start
        const elapsedMinutes = Math.floor(elapsed / 60000)
        remaining = Math.max(0, EXCLUSIVE_DURATION_MINUTES - elapsedMinutes)
      }

      setRemainingMinutes(remaining)

      // If expired, clear exclusive
      if (remaining === 0) {
        clearExclusive()
      }
    }

    // Update immediately
    updateTimer()

    // Then update every minute
    const interval = setInterval(updateTimer, 60000)

    return () => clearInterval(interval)
  }, [activeExclusive, clearExclusive])

  return {
    activeExclusive,
    remainingMinutes,
    activateExclusive,
    clearExclusive,
  }
}

