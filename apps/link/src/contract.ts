/**
 * Contract validation for phone-start API response.
 * 
 * This ensures the link app and backend stay in sync.
 * If backend changes, this will catch it at build time.
 */

export interface PhoneStartResponse {
  /** Must be 'ok' (not 'success') - matches backend PhoneStartResponse */
  ok: boolean
  /** 6-character session code */
  session_code?: string
  /** Error message if ok=false */
  error?: string
  /** Success message */
  message?: string
  /** TTL in seconds */
  expires_in_seconds?: number
}

/**
 * Validate response matches expected contract.
 * Throws if contract is violated.
 */
export function validatePhoneStartResponse(data: unknown): PhoneStartResponse {
  if (!data || typeof data !== 'object') {
    throw new Error('Response must be an object')
  }

  const response = data as Record<string, unknown>

  // Critical: must have 'ok' field (not 'success')
  if (!('ok' in response)) {
    throw new Error(
      `Contract violation: response missing 'ok' field. ` +
      `Got keys: ${Object.keys(response).join(', ')}`
    )
  }

  if (typeof response.ok !== 'boolean') {
    throw new Error(`Contract violation: 'ok' must be boolean, got ${typeof response.ok}`)
  }

  // Validate optional fields
  if ('session_code' in response && response.session_code !== undefined) {
    if (typeof response.session_code !== 'string') {
      throw new Error(`Contract violation: 'session_code' must be string`)
    }
    if (response.session_code.length !== 6) {
      throw new Error(
        `Contract violation: 'session_code' must be 6 chars, got ${response.session_code.length}`
      )
    }
  }

  if ('error' in response && response.error !== undefined) {
    if (typeof response.error !== 'string') {
      throw new Error(`Contract violation: 'error' must be string`)
    }
  }

  if ('message' in response && response.message !== undefined) {
    if (typeof response.message !== 'string') {
      throw new Error(`Contract violation: 'message' must be string`)
    }
  }

  if ('expires_in_seconds' in response && response.expires_in_seconds !== undefined) {
    if (typeof response.expires_in_seconds !== 'number') {
      throw new Error(`Contract violation: 'expires_in_seconds' must be number`)
    }
  }

  return response as unknown as PhoneStartResponse
}
