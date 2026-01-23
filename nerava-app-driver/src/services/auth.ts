// Authentication API functions
import { ApiError } from './api'

export { ApiError }

// Detect API base URL: use env var if set, otherwise detect from hostname
function getApiBaseUrl(): string {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  // If running on production domain, use production API
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname
    if (hostname.includes('nerava.network') || hostname.includes('nerava.app')) {
      return 'https://api.nerava.network'
    }
  }
  // Default to localhost for local development
  return 'http://localhost:8001'
}

const API_BASE_URL = getApiBaseUrl()

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

  const response = await fetch(`${API_BASE_URL}/v1/auth/otp/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ phone: normalizedPhone }),
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

    // Handle rate limiting
    if (response.status === 429) {
      throw new ApiError(429, errorCode || 'rate_limit', 'Too many requests. Please try again in a moment.')
    }

    throw new ApiError(response.status, errorCode, errorMessage)
  }

  return await response.json()
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

  return data
}

