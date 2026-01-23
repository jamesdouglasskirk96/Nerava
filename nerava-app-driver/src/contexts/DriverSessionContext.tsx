// Driver Session Context - Source of truth for location and app state
import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import type { ReactNode } from 'react'

export type LocationPermissionState = 'unknown' | 'granted' | 'denied'
export type LocationFixState = 'idle' | 'locating' | 'located' | 'error'
export type AppChargingState = 'PRE_CHARGING' | 'CHARGING_ACTIVE' | 'EXCLUSIVE_ACTIVE'

export interface Coordinates {
  lat: number
  lng: number
  accuracy_m: number
  last_fix_ts: number
}

export interface DriverSessionState {
  locationPermission: LocationPermissionState
  locationFix: LocationFixState
  coordinates: Coordinates | null
  appChargingState: AppChargingState
  sessionId: string | null
  activeExclusiveSessionId: string | null
  activeExclusiveExpiresAt: string | null
}

interface DriverSessionContextValue extends DriverSessionState {
  setAppChargingState: (state: AppChargingState) => void
  setSessionId: (sessionId: string | null) => void
  setActiveExclusive: (sessionId: string, expiresAt: string) => void
  clearActiveExclusive: () => void
  requestLocationPermission: () => void
}

const DriverSessionContext = createContext<DriverSessionContextValue | undefined>(undefined)

const STORAGE_KEY = 'nerava_driver_session'
const STORAGE_CHARGING_STATE_KEY = 'nerava_app_charging_state'

export function DriverSessionProvider({ children }: { children: ReactNode }) {
  const [locationPermission, setLocationPermission] = useState<LocationPermissionState>(() => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      return 'denied'
    }
    return 'unknown'
  })

  const [locationFix, setLocationFix] = useState<LocationFixState>('idle')
  const [coordinates, setCoordinates] = useState<Coordinates | null>(() => {
    // Try to load from localStorage
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        const data = JSON.parse(stored)
        if (data.coordinates && data.coordinates.lat && data.coordinates.lng) {
          return data.coordinates
        }
      } catch {
        // Invalid JSON, ignore
      }
    }
    return null
  })

  const [appChargingState, setAppChargingStateState] = useState<AppChargingState>(() => {
    const stored = localStorage.getItem(STORAGE_CHARGING_STATE_KEY)
    if (stored === 'PRE_CHARGING' || stored === 'CHARGING_ACTIVE' || stored === 'EXCLUSIVE_ACTIVE') {
      return stored
    }
    return 'PRE_CHARGING'
  })

  const [sessionId, setSessionIdState] = useState<string | null>(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        const data = JSON.parse(stored)
        return data.sessionId || null
      } catch {
        return null
      }
    }
    return null
  })

  const [activeExclusiveSessionId, setActiveExclusiveSessionId] = useState<string | null>(null)
  const [activeExclusiveExpiresAt, setActiveExclusiveExpiresAt] = useState<string | null>(null)

  // Persist app charging state
  useEffect(() => {
    localStorage.setItem(STORAGE_CHARGING_STATE_KEY, appChargingState)
  }, [appChargingState])

  // Persist session data
  useEffect(() => {
    const data = {
      coordinates,
      sessionId,
      activeExclusiveSessionId,
      activeExclusiveExpiresAt,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  }, [coordinates, sessionId, activeExclusiveSessionId, activeExclusiveExpiresAt])

  // Request location permission
  const requestLocationPermission = useCallback(() => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      setLocationPermission('denied')
      setLocationFix('error')
      return
    }

    // Track permission prompt
    import('../lib/analytics').then(({ track, AnalyticsEvents }) => {
      track(AnalyticsEvents.LOCATION_PERMISSION_PROMPTED)
    })

    setLocationFix('locating')

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocationPermission('granted')
        setLocationFix('located')
        setCoordinates({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy_m: position.coords.accuracy || 0,
          last_fix_ts: Date.now(),
        })
        // Track permission granted
        import('../lib/analytics').then(({ track, AnalyticsEvents }) => {
          track(AnalyticsEvents.LOCATION_PERMISSION_GRANTED)
        })
      },
      (error) => {
        if (error.code === error.PERMISSION_DENIED) {
          setLocationPermission('denied')
          // Track permission denied
          import('../lib/analytics').then(({ track, AnalyticsEvents }) => {
            track(AnalyticsEvents.LOCATION_PERMISSION_DENIED)
          })
        } else {
          setLocationPermission('granted') // Permission granted but error getting location
        }
        setLocationFix('error')
        setCoordinates(null)
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    )
  }, [])

  // Watch location changes
  useEffect(() => {
    if (locationPermission !== 'granted' || locationFix === 'error') {
      return
    }

    setLocationFix('locating')

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        setLocationFix('located')
        setCoordinates({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy_m: position.coords.accuracy || 0,
          last_fix_ts: Date.now(),
        })
      },
      (error) => {
        setLocationFix('error')
        if (error.code === error.PERMISSION_DENIED) {
          setLocationPermission('denied')
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000, // Accept cached location up to 1 minute old
      }
    )

    return () => {
      navigator.geolocation.clearWatch(watchId)
    }
  }, [locationPermission])

  // Request permission on mount
  useEffect(() => {
    if (locationPermission === 'unknown') {
      requestLocationPermission()
    }
  }, [locationPermission, requestLocationPermission])

  const setAppChargingState = useCallback((state: AppChargingState) => {
    setAppChargingStateState(state)
  }, [])

  const setSessionId = useCallback((id: string | null) => {
    setSessionIdState(id)
  }, [])

  const setActiveExclusive = useCallback((sessionId: string, expiresAt: string) => {
    setActiveExclusiveSessionId(sessionId)
    setActiveExclusiveExpiresAt(expiresAt)
    setAppChargingStateState('EXCLUSIVE_ACTIVE')
  }, [])

  const clearActiveExclusive = useCallback(() => {
    setActiveExclusiveSessionId(null)
    setActiveExclusiveExpiresAt(null)
    // Return to previous state or default to PRE_CHARGING
    const stored = localStorage.getItem(STORAGE_CHARGING_STATE_KEY)
    if (stored === 'CHARGING_ACTIVE') {
      setAppChargingStateState('CHARGING_ACTIVE')
    } else {
      setAppChargingStateState('PRE_CHARGING')
    }
  }, [])

  const value: DriverSessionContextValue = {
    locationPermission,
    locationFix,
    coordinates,
    appChargingState,
    sessionId,
    activeExclusiveSessionId,
    activeExclusiveExpiresAt,
    setAppChargingState,
    setSessionId,
    setActiveExclusive,
    clearActiveExclusive,
    requestLocationPermission,
  }

  return <DriverSessionContext.Provider value={value}>{children}</DriverSessionContext.Provider>
}

export function useDriverSessionContext(): DriverSessionContextValue {
  const context = useContext(DriverSessionContext)
  if (!context) {
    throw new Error('useDriverSessionContext must be used within DriverSessionProvider')
  }
  return context
}

