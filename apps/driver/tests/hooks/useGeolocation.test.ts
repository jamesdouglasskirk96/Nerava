import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useGeolocation } from '../../src/hooks/useGeolocation'

describe('useGeolocation', () => {
  const mockGeolocation = {
    getCurrentPosition: vi.fn(),
  }

  beforeEach(() => {
    // @ts-ignore
    global.navigator.geolocation = mockGeolocation
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns location when geolocation is successful', async () => {
    mockGeolocation.getCurrentPosition.mockImplementation((success) => {
      success({
        coords: {
          latitude: 30.2672,
          longitude: -97.7431,
          accuracy: 50,
        },
      })
    })

    const { result } = renderHook(() => useGeolocation())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.lat).toBe(30.2672)
    expect(result.current.lng).toBe(-97.7431)
    expect(result.current.accuracy).toBe(50)
    expect(result.current.error).toBeNull()
  })

  it('returns error when geolocation is denied', async () => {
    mockGeolocation.getCurrentPosition.mockImplementation((_, error) => {
      error({
        code: 1,
        message: 'User denied geolocation',
      })
    })

    const { result } = renderHook(() => useGeolocation())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.lat).toBeNull()
    expect(result.current.lng).toBeNull()
    expect(result.current.error).toBe('User denied geolocation')
  })

  it('returns error when geolocation is not supported', async () => {
    // @ts-ignore
    delete global.navigator.geolocation

    const { result } = renderHook(() => useGeolocation())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.error).toContain('not supported')
  })
})

