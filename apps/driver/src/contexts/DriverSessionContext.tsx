// Driver Session Context - Source of truth for location and app state
import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'
import type { ReactNode } from 'react'

export type LocationPermissionState = 'unknown' | 'granted' | 'denied' | 'skipped'
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
  setLocationPermission: (permission: LocationPermissionState) => void
}

const DriverSessionContext = createContext<DriverSessionContextValue | undefined>(undefined)

const STORAGE_KEY = 'nerava_driver_session'
const STORAGE_CHARGING_STATE_KEY = 'nerava_app_charging_state'
const STORAGE_LOCATION_PERMISSION_KEY = 'nerava_location_permission'

export function DriverSessionProvider({ children }: { children: ReactNode }) {
  const [locationPermission, setLocationPermissionRaw] = useState<LocationPermissionState>(() => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      return 'denied'
    }
    // Restore last known permission state to avoid re-prompting on every app open
    const stored = localStorage.getItem(STORAGE_LOCATION_PERMISSION_KEY)
    if (stored === 'granted' || stored === 'denied' || stored === 'skipped') {
      return stored
    }
    return 'unknown'
  })

  // Wrap setLocationPermission to persist to localStorage
  const setLocationPermission = useCallback((state: LocationPermissionState) => {
    setLocationPermissionRaw(state)
    if (state !== 'unknown') {
      localStorage.setItem(STORAGE_LOCATION_PERMISSION_KEY, state)
    }
  }, [])

  const [locationFix, setLocationFix] = useState<LocationFixState>('idle')
  const [coordinates, setCoordinates] = useState<Coordinates | null>(null)
  const lastCoordsRef = useRef<Coordinates | null>(null)

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
      },
      (error) => {
        if (error.code === error.PERMISSION_DENIED) {
          setLocationPermission('denied')
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

  // Auto-check location permission on mount — if the OS already granted
  // permission, getCurrentPosition succeeds silently without prompting.
  // This prevents showing the "enable location" screen on every app open.
  useEffect(() => {
    if (locationPermission !== 'unknown') return

    // Use the Permissions API if available for an instant check
    if (navigator.permissions) {
      navigator.permissions.query({ name: 'geolocation' }).then((result) => {
        if (result.state === 'granted') {
          requestLocationPermission()
        } else if (result.state === 'denied') {
          setLocationPermission('denied')
          setLocationFix('error')
        }
        // 'prompt' → leave as 'unknown', user must click the button
      }).catch(() => {
        // Permissions API not supported (some WKWebView versions), try directly
        requestLocationPermission()
      })
    } else {
      // No Permissions API — just try to get location (works if already authorized)
      requestLocationPermission()
    }
  }, [locationPermission, requestLocationPermission])

  // Watch location changes
  useEffect(() => {
    if (locationPermission !== 'granted' || locationFix === 'error') {
      return
    }

    setLocationFix('locating')

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        setLocationFix('located')
        const newCoords: Coordinates = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy_m: position.coords.accuracy || 0,
          last_fix_ts: Date.now(),
        }

        // Skip state update if user hasn't moved >50m — prevents GPS jitter
        // from cascading re-renders and intent capture refetches
        const prev = lastCoordsRef.current
        if (prev) {
          const dlat = newCoords.lat - prev.lat
          const dlng = newCoords.lng - prev.lng
          const approxDistM = Math.sqrt(dlat * dlat + dlng * dlng) * 111320
          if (approxDistM < 50) return
        }

        lastCoordsRef.current = newCoords
        setCoordinates(newCoords)
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

  // Location permission is handled by the iOS native layer (ContentView.swift)
  // Do NOT auto-request here — it causes duplicate prompts in the WKWebView

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

  const setLocationPermissionState = useCallback((permission: LocationPermissionState) => {
    setLocationPermission(permission)
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
    setLocationPermission: setLocationPermissionState,
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

