import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock import.meta.env before importing anything that uses it
vi.stubEnv('VITE_API_BASE_URL', 'https://api.test.local')
vi.stubEnv('VITE_MOCK_MODE', 'false')

// Must mock fetch globally before importing the module under test
const mockFetch = vi.fn()
;(globalThis as Record<string, unknown>).fetch = mockFetch

describe('fetchAPI (via api.get/post)', () => {
  let api: typeof import('../../services/api')

  beforeEach(async () => {
    vi.clearAllMocks()
    localStorage.clear()

    // Re-import to get fresh module state
    vi.resetModules()
    vi.stubEnv('VITE_API_BASE_URL', 'https://api.test.local')
    vi.stubEnv('VITE_MOCK_MODE', 'false')
    ;(globalThis as Record<string, unknown>).fetch = mockFetch
    api = await import('../../services/api')
  })

  afterEach(() => {
    localStorage.clear()
  })

  // --- Test 1: Successful GET request with auth token ---
  it('sends Authorization header when access_token is in localStorage', async () => {
    localStorage.setItem('access_token', 'test-jwt-token')

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ result: 'ok' }),
    })

    const result = await api.api.get('/v1/test')

    expect(mockFetch).toHaveBeenCalledTimes(1)
    const [url, options] = mockFetch.mock.calls[0]
    expect(url).toBe('https://api.test.local/v1/test')
    expect(options.headers.get('Authorization')).toBe('Bearer test-jwt-token')
    expect(options.headers.get('Content-Type')).toBe('application/json')
    expect(result).toEqual({ result: 'ok' })
  })

  // --- Test 2: 401 triggers token refresh and retries the original request ---
  it('refreshes token on 401 and retries the original request', async () => {
    localStorage.setItem('access_token', 'expired-token')
    localStorage.setItem('refresh_token', 'valid-refresh-token')

    // First call: 401
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: async () => ({ detail: 'Token expired' }),
    })

    // Refresh call: success
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
      }),
    })

    // Retry of original call: success
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: 'retried-result' }),
    })

    const result = await api.api.get('/v1/protected')

    // 3 fetch calls: original 401 + refresh + retry
    expect(mockFetch).toHaveBeenCalledTimes(3)

    // Check refresh call went to /v1/auth/refresh
    const [refreshUrl, refreshOpts] = mockFetch.mock.calls[1]
    expect(refreshUrl).toBe('https://api.test.local/v1/auth/refresh')
    expect(JSON.parse(refreshOpts.body)).toEqual({ refresh_token: 'valid-refresh-token' })

    // Check retried call used new token
    const [, retryOpts] = mockFetch.mock.calls[2]
    expect(retryOpts.headers.get('Authorization')).toBe('Bearer new-access-token')

    // Check new tokens stored
    expect(localStorage.getItem('access_token')).toBe('new-access-token')
    expect(localStorage.getItem('refresh_token')).toBe('new-refresh-token')

    expect(result).toEqual({ data: 'retried-result' })
  })

  // --- Test 3: 401 with no refresh token clears access_token and throws ---
  it('clears tokens and throws ApiError when no refresh_token available on 401', async () => {
    localStorage.setItem('access_token', 'expired-token')
    // No refresh_token set

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: async () => ({ detail: 'Token expired' }),
    })

    try {
      await api.api.get('/v1/protected')
      expect.unreachable('Should have thrown')
    } catch (err) {
      expect(err).toBeInstanceOf(api.ApiError)
      expect((err as InstanceType<typeof api.ApiError>).status).toBe(401)
      expect((err as InstanceType<typeof api.ApiError>).code).toBe('no_refresh_token')
    }

    // Access token should be cleared
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  // --- Test 4: Failed token refresh dispatches session-expired event ---
  it('dispatches nerava:session-expired event when token refresh fails', async () => {
    localStorage.setItem('access_token', 'expired-token')
    localStorage.setItem('refresh_token', 'invalid-refresh-token')

    const sessionExpiredHandler = vi.fn()
    window.addEventListener('nerava:session-expired', sessionExpiredHandler)

    // First call: 401
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: async () => ({ detail: 'Token expired' }),
    })

    // Refresh call: fails (403)
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      statusText: 'Forbidden',
      json: async () => ({ detail: 'Refresh token invalid' }),
    })

    await expect(api.api.get('/v1/protected')).rejects.toThrow()

    expect(sessionExpiredHandler).toHaveBeenCalledTimes(1)
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()

    window.removeEventListener('nerava:session-expired', sessionExpiredHandler)
  })

  // --- Test 5: Non-401 error returns proper ApiError with details ---
  it('throws ApiError with status and message on non-401 errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      json: async () => ({ detail: 'Validation error: field is required' }),
    })

    try {
      await api.api.post('/v1/action', { data: 'bad' })
      expect.unreachable('Should have thrown')
    } catch (err) {
      expect(err).toBeInstanceOf(api.ApiError)
      const apiErr = err as InstanceType<typeof api.ApiError>
      expect(apiErr.status).toBe(422)
      expect(apiErr.message).toBe('Validation error: field is required')
    }
  })

  // --- Test 6: Network error is wrapped as ApiError with status 0 ---
  it('wraps network errors as ApiError with status 0 and code network_error', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

    try {
      await api.api.get('/v1/data')
      expect.unreachable('Should have thrown')
    } catch (err) {
      expect(err).toBeInstanceOf(api.ApiError)
      const apiErr = err as InstanceType<typeof api.ApiError>
      expect(apiErr.status).toBe(0)
      expect(apiErr.code).toBe('network_error')
      expect(apiErr.message).toBe('Failed to fetch')
    }
  })
})
