import { useState, useEffect, useRef, useCallback } from 'react'

export interface GeolocationState {
  lat: number | null
  lng: number | null
  accuracy: number | null
  error: string | null
  loading: boolean
}

/**
 * Hook for geolocation with throttled updates (5s throttle)
 * Watches position and updates on location changes
 */
export function useGeolocation(throttleMs: number = 5000): GeolocationState {
  const [state, setState] = useState<GeolocationState>({
    lat: null,
    lng: null,
    accuracy: null,
    error: null,
    loading: true,
  })

  const lastUpdateRef = useRef<number>(0)
  const watchIdRef = useRef<number | null>(null)

  const updatePosition = useCallback((position: GeolocationPosition) => {
    const now = Date.now()
    if (now - lastUpdateRef.current < throttleMs) {
      return // Throttle: skip if too soon
    }
    lastUpdateRef.current = now

    setState({
      lat: position.coords.latitude,
      lng: position.coords.longitude,
      accuracy: position.coords.accuracy || null,
      error: null,
      loading: false,
    })
  }, [throttleMs])

  useEffect(() => {
    if (!navigator.geolocation) {
      setState({
        lat: null,
        lng: null,
        accuracy: null,
        error: 'Geolocation is not supported by your browser',
        loading: false,
      })
      return
    }

    // Get initial position
    navigator.geolocation.getCurrentPosition(
      (position) => {
        updatePosition(position)
      },
      (error) => {
        setState({
          lat: null,
          lng: null,
          accuracy: null,
          error: error.message || 'Failed to get location',
          loading: false,
        })
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    )

    // Watch position changes (throttled)
    watchIdRef.current = navigator.geolocation.watchPosition(
      updatePosition,
      (error) => {
        setState(prev => ({
          ...prev,
          error: error.message || 'Failed to update location',
          loading: false,
        }))
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 5000, // Accept cached position up to 5s old
      }
    )

    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current)
      }
    }
  }, [updatePosition])

  return state
}

