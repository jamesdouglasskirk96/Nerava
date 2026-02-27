import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock import.meta.env
vi.stubEnv('VITE_API_BASE_URL', 'https://api.test.local')

// Mock fetch globally
const mockFetch = vi.fn()
;(globalThis as Record<string, unknown>).fetch = mockFetch

describe('Auth service', () => {
  let auth: typeof import('../../services/auth')

  beforeEach(async () => {
    vi.clearAllMocks()
    localStorage.clear()

    vi.resetModules()
    vi.stubEnv('VITE_API_BASE_URL', 'https://api.test.local')
    ;(globalThis as Record<string, unknown>).fetch = mockFetch
    auth = await import('../../services/auth')
  })

  afterEach(() => {
    localStorage.clear()
  })

  // --- Test 1: otpStart sends normalized phone and returns success ---
  it('otpStart normalizes 10-digit phone to +1 prefix and sends to /v1/auth/otp/start', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ otp_sent: true }),
    })

    const result = await auth.otpStart('5125551234')

    expect(mockFetch).toHaveBeenCalledTimes(1)
    const [url, opts] = mockFetch.mock.calls[0]
    expect(url).toBe('https://api.test.local/v1/auth/otp/start')
    expect(opts.method).toBe('POST')
    expect(JSON.parse(opts.body)).toEqual({ phone: '+15125551234' })
    expect(result).toEqual({ otp_sent: true })
  })

  // --- Test 2: otpStart handles rate limiting (429) ---
  it('otpStart throws ApiError with rate_limit code on 429', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 429,
      statusText: 'Too Many Requests',
      json: async () => ({ error: 'rate_limit', message: 'Wait 60s' }),
    })

    try {
      await auth.otpStart('5125551234')
      expect.unreachable('Should have thrown')
    } catch (err) {
      expect(err).toBeInstanceOf(auth.ApiError)
      const apiErr = err as InstanceType<typeof auth.ApiError>
      expect(apiErr.status).toBe(429)
      expect(apiErr.code).toBe('rate_limit')
    }
  })

  // --- Test 3: otpVerify stores tokens and user in localStorage ---
  it('otpVerify stores access_token, refresh_token, and user in localStorage', async () => {
    const tokenResponse = {
      access_token: 'jwt-abc-123',
      refresh_token: 'refresh-xyz-789',
      token_type: 'bearer',
      user: {
        public_id: 'user-001',
        auth_provider: 'phone',
        phone: '+15125551234',
      },
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => tokenResponse,
    })

    const result = await auth.otpVerify('5125551234', '123456')

    expect(result.access_token).toBe('jwt-abc-123')
    expect(localStorage.getItem('access_token')).toBe('jwt-abc-123')
    expect(localStorage.getItem('refresh_token')).toBe('refresh-xyz-789')
    expect(JSON.parse(localStorage.getItem('nerava_user')!)).toEqual({
      public_id: 'user-001',
      auth_provider: 'phone',
      phone: '+15125551234',
    })
  })

  // --- Test 4: otpVerify throws ApiError on invalid code (401) ---
  it('otpVerify throws ApiError with invalid_code on 401', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: async () => ({ error: 'invalid_code', message: 'Bad code' }),
    })

    try {
      await auth.otpVerify('5125551234', '000000')
      expect.unreachable('Should have thrown')
    } catch (err) {
      expect(err).toBeInstanceOf(auth.ApiError)
      const apiErr = err as InstanceType<typeof auth.ApiError>
      expect(apiErr.status).toBe(401)
      expect(apiErr.code).toBe('invalid_code')
    }
  })

  // --- Test 5: googleAuth stores tokens and returns response ---
  it('googleAuth exchanges id_token, stores tokens, and returns user data', async () => {
    const tokenResponse = {
      access_token: 'google-jwt-token',
      refresh_token: 'google-refresh',
      token_type: 'bearer',
      user: {
        public_id: 'user-google-001',
        auth_provider: 'google',
        email: 'driver@gmail.com',
      },
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => tokenResponse,
    })

    const result = await auth.googleAuth('google-id-token-xyz')

    const [url, opts] = mockFetch.mock.calls[0]
    expect(url).toBe('https://api.test.local/v1/auth/google')
    expect(JSON.parse(opts.body)).toEqual({ id_token: 'google-id-token-xyz' })
    expect(result.access_token).toBe('google-jwt-token')
    expect(localStorage.getItem('access_token')).toBe('google-jwt-token')
    expect(localStorage.getItem('refresh_token')).toBe('google-refresh')
    expect(JSON.parse(localStorage.getItem('nerava_user')!).email).toBe('driver@gmail.com')
  })

  // --- Test 6: appleAuth stores tokens and returns response ---
  it('appleAuth exchanges id_token, stores tokens, and returns user data', async () => {
    const tokenResponse = {
      access_token: 'apple-jwt-token',
      refresh_token: 'apple-refresh',
      token_type: 'bearer',
      user: {
        public_id: 'user-apple-001',
        auth_provider: 'apple',
        email: 'driver@icloud.com',
      },
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => tokenResponse,
    })

    const result = await auth.appleAuth('apple-id-token-abc')

    const [url, opts] = mockFetch.mock.calls[0]
    expect(url).toBe('https://api.test.local/v1/auth/apple')
    expect(JSON.parse(opts.body)).toEqual({ id_token: 'apple-id-token-abc' })
    expect(result.access_token).toBe('apple-jwt-token')
    expect(localStorage.getItem('access_token')).toBe('apple-jwt-token')
    expect(localStorage.getItem('refresh_token')).toBe('apple-refresh')
    expect(JSON.parse(localStorage.getItem('nerava_user')!).auth_provider).toBe('apple')
  })
})
