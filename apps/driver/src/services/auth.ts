// Authentication API functions
import { ApiError } from './api'

export { ApiError }

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.nerava.network'

export interface OTPStartRequest {
  phone: string
}

export interface OTPStartResponse {
  otp_sent: boolean
}

export interface OTPVerifyRequest {
  phone: string
  code: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user?: {
    public_id: string
    auth_provider: string
    email?: string
    phone?: string
  }
}

/**
 * Start OTP flow by sending code to phone number
 */
export async function otpStart(phone: string): Promise<OTPStartResponse> {
  // Normalize phone number: remove dashes and ensure +1 prefix
  const cleaned = phone.replace(/\D/g, '')
  const normalizedPhone = cleaned.length === 10 ? `+1${cleaned}` : cleaned.startsWith('+') ? cleaned : `+${cleaned}`

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 15000) // 15s timeout

  try {
    const response = await fetch(`${API_BASE_URL}/v1/auth/otp/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ phone: normalizedPhone }),
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      let errorData: { error?: string; message?: string; detail?: string } = {}
      try {
        errorData = await response.json()
      } catch {
        errorData = { message: response.statusText }
      }
      const errorMessage = errorData.message || errorData.detail || response.statusText
      const errorCode = errorData.error

      // Handle rate limiting
      if (response.status === 429) {
        throw new ApiError(429, errorCode || 'rate_limit', 'Too many requests. Please try again in a moment.')
      }

      throw new ApiError(response.status, errorCode, errorMessage)
    }

    return await response.json()
  } catch (err) {
    clearTimeout(timeoutId)
    if (err instanceof Error && err.name === 'AbortError') {
      throw new ApiError(408, 'timeout', 'Request timed out. Please try again.')
    }
    throw err
  }
}

/**
 * Verify OTP code and get access token
 */
export async function otpVerify(phone: string, code: string): Promise<TokenResponse> {
  // Normalize phone number: remove dashes and ensure +1 prefix
  const cleaned = phone.replace(/\D/g, '')
  const normalizedPhone = cleaned.length === 10 ? `+1${cleaned}` : cleaned.startsWith('+') ? cleaned : `+${cleaned}`

  const response = await fetch(`${API_BASE_URL}/v1/auth/otp/verify`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ phone: normalizedPhone, code }),
  })

  if (!response.ok) {
    let errorData: { error?: string; message?: string; detail?: string } = {}
    try {
      errorData = await response.json()
    } catch {
      errorData = { message: response.statusText }
    }
    const errorMessage = errorData.message || errorData.detail || response.statusText
    const errorCode = errorData.error

    // Handle specific error cases
    if (response.status === 401) {
      throw new ApiError(401, errorCode || 'invalid_code', 'Incorrect code. Please try again.')
    }
    if (response.status === 429) {
      throw new ApiError(429, errorCode || 'rate_limit', 'Too many requests. Please try again in a moment.')
    }

    throw new ApiError(response.status, errorCode, errorMessage)
  }

  const data = await response.json()
  
  // Store tokens
  localStorage.setItem('access_token', data.access_token)
  if (data.refresh_token) {
    localStorage.setItem('refresh_token', data.refresh_token)
  }
  
  // Store user info for account page
  if (data.user) {
    localStorage.setItem('nerava_user', JSON.stringify(data.user))
  }

  return data
}

/**
 * Authenticate with Google ID token
 */
export async function googleAuth(idToken: string): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/auth/google`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ id_token: idToken }),
  })

  if (!response.ok) {
    let errorData: { error?: string; message?: string; detail?: string } = {}
    try {
      errorData = await response.json()
    } catch {
      errorData = { message: response.statusText }
    }
    const errorMessage = errorData.message || errorData.detail || response.statusText
    const errorCode = errorData.error
    throw new ApiError(response.status, errorCode, errorMessage)
  }

  const data = await response.json()

  localStorage.setItem('access_token', data.access_token)
  if (data.refresh_token) {
    localStorage.setItem('refresh_token', data.refresh_token)
  }
  if (data.user) {
    localStorage.setItem('nerava_user', JSON.stringify(data.user))
  }

  return data
}

/**
 * Authenticate with Apple ID token
 */
export async function appleAuth(idToken: string): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/auth/apple`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ id_token: idToken }),
  })

  if (!response.ok) {
    let errorData: { error?: string; message?: string; detail?: string } = {}
    try {
      errorData = await response.json()
    } catch {
      errorData = { message: response.statusText }
    }
    const errorMessage = errorData.message || errorData.detail || response.statusText
    const errorCode = errorData.error
    throw new ApiError(response.status, errorCode, errorMessage)
  }

  const data = await response.json()

  localStorage.setItem('access_token', data.access_token)
  if (data.refresh_token) {
    localStorage.setItem('refresh_token', data.refresh_token)
  }
  if (data.user) {
    localStorage.setItem('nerava_user', JSON.stringify(data.user))
  }

  return data
}

