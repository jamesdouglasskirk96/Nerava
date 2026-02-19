import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { capture } from '../../analytics'
import { DRIVER_EVENTS } from '../../analytics/events'

const API_BASE = import.meta.env.VITE_API_URL || ''

interface SessionResponse {
  session_id: string
  status: string
  session_code: string
  merchant_name: string
  merchant_address?: string
  charger_name?: string
  is_activated: boolean
  expires_at: string
  verification_status?: string
}

type ViewState =
  | 'loading'
  | 'otp_required'
  | 'otp_verifying'
  | 'activating'
  | 'location_verify'
  | 'verifying_location'
  | 'success'
  | 'expired'
  | 'error'

export function PhoneCheckinScreen() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()

  const [viewState, setViewState] = useState<ViewState>('loading')
  const [session, setSession] = useState<SessionResponse | null>(null)
  const [otpCode, setOtpCode] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [timeLeft, setTimeLeft] = useState('')

  // Fetch session on mount
  useEffect(() => {
    if (!token) {
      setViewState('error')
      setErrorMessage('Invalid link. Please request a new check-in link from your vehicle.')
      return
    }

    fetchSession()
  }, [token])

  // Timer for expiration
  useEffect(() => {
    if (!session?.expires_at) return

    const timer = setInterval(() => {
      const diff = new Date(session.expires_at).getTime() - Date.now()
      if (diff <= 0) {
        setTimeLeft('Expired')
        setViewState('expired')
        clearInterval(timer)
        return
      }
      const m = Math.floor(diff / 60000)
      const s = Math.floor((diff % 60000) / 1000)
      setTimeLeft(`${m}:${s.toString().padStart(2, '0')}`)
    }, 1000)

    return () => clearInterval(timer)
  }, [session?.expires_at])

  const fetchSession = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/checkin/s/${token}`)
      const data = await response.json()

      if (!response.ok) {
        if (response.status === 404 || response.status === 410) {
          setViewState('expired')
          setErrorMessage('This link has expired. Please request a new one from your vehicle.')
        } else {
          setViewState('error')
          setErrorMessage(data.detail?.message || 'Unable to load session')
        }
        return
      }

      setSession(data)
      capture(DRIVER_EVENTS.CHECKIN_SESSION_LOADED, {
        session_id: data.session_id,
        status: data.status,
      })

      // Determine next step
      if (data.status === 'expired') {
        setViewState('expired')
      } else if (!data.is_activated) {
        setViewState('otp_required')
      } else if (data.verification_status !== 'verified') {
        setViewState('location_verify')
      } else {
        setViewState('success')
      }
    } catch (err) {
      console.error('Fetch session error:', err)
      setViewState('error')
      setErrorMessage('Unable to connect. Please check your connection.')
    }
  }

  const handleOtpSubmit = async () => {
    if (otpCode.length !== 6) return

    setViewState('otp_verifying')
    setErrorMessage('')

    try {
      // First verify OTP with auth endpoint
      const otpResponse = await fetch(`${API_BASE}/api/v1/auth/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ code: otpCode }),
      })

      if (!otpResponse.ok) {
        const data = await otpResponse.json()
        setErrorMessage(data.detail?.message || 'Invalid code. Please try again.')
        setViewState('otp_required')
        return
      }

      // Now activate the session
      setViewState('activating')

      const activateResponse = await fetch(`${API_BASE}/api/v1/checkin/s/${token}/activate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      })

      if (!activateResponse.ok) {
        const data = await activateResponse.json()
        setErrorMessage(data.detail?.message || 'Unable to activate session')
        setViewState('error')
        return
      }

      capture(DRIVER_EVENTS.CHECKIN_SESSION_ACTIVATED, {
        session_id: session?.session_id,
      })

      // Refresh session and proceed to location verify
      await fetchSession()

    } catch (err) {
      console.error('OTP verify error:', err)
      setErrorMessage('Unable to verify. Please try again.')
      setViewState('otp_required')
    }
  }

  const handleLocationVerify = useCallback(async () => {
    setViewState('verifying_location')
    setErrorMessage('')

    try {
      // Get current location
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        })
      })

      const response = await fetch(`${API_BASE}/api/v1/checkin/s/${token}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        setErrorMessage(data.detail?.message || 'Location verification failed')
        setViewState('location_verify')
        return
      }

      if (data.verified) {
        capture(DRIVER_EVENTS.CHECKIN_LOCATION_VERIFIED, {
          session_id: session?.session_id,
        })
        setViewState('success')
      } else {
        setErrorMessage(`You appear to be ${data.distance_m}m away. Please move closer to the charger.`)
        setViewState('location_verify')
      }
    } catch (err) {
      if (err instanceof GeolocationPositionError) {
        setErrorMessage('Location access denied. Please enable location services.')
      } else {
        setErrorMessage('Unable to verify location. Please try again.')
      }
      setViewState('location_verify')
    }
  }, [token, session?.session_id])

  // Render loading state
  if (viewState === 'loading') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex items-center justify-center p-6">
        <div className="animate-spin w-8 h-8 border-4 border-sky-400 border-t-transparent rounded-full" />
      </div>
    )
  }

  // Render expired state
  if (viewState === 'expired') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex flex-col items-center justify-center p-6 text-center">
        <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mb-4">
          <svg className="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">Session Expired</h1>
        <p className="text-slate-400 mb-6">{errorMessage || 'This check-in link has expired.'}</p>
        <p className="text-slate-500 text-sm">Request a new link from your Tesla browser.</p>
      </div>
    )
  }

  // Render error state
  if (viewState === 'error') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex flex-col items-center justify-center p-6 text-center">
        <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mb-4">
          <svg className="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">Something went wrong</h1>
        <p className="text-slate-400">{errorMessage}</p>
      </div>
    )
  }

  // OTP verification screens
  if (viewState === 'otp_required' || viewState === 'otp_verifying' || viewState === 'activating') {
    const isSubmitting = viewState === 'otp_verifying' || viewState === 'activating'

    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex flex-col p-6">
        <div className="flex-1 flex flex-col items-center justify-center text-center">
          <h1 className="text-3xl font-bold text-white mb-2">Verify your phone</h1>
          <p className="text-slate-400 mb-8">
            Enter the 6-digit code we sent to your phone
          </p>

          {errorMessage && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mb-6 w-full max-w-xs">
              <p className="text-red-400 text-sm">{errorMessage}</p>
            </div>
          )}

          <input
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={6}
            value={otpCode}
            onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            placeholder="000000"
            disabled={isSubmitting}
            className="w-full max-w-xs h-16 text-center text-3xl font-mono tracking-[0.5em] bg-slate-800 border-2 border-slate-600 rounded-xl text-white placeholder-slate-600 focus:border-sky-400 focus:outline-none disabled:opacity-50"
          />

          <button
            onClick={handleOtpSubmit}
            disabled={otpCode.length !== 6 || isSubmitting}
            className="w-full max-w-xs mt-6 h-14 bg-sky-500 hover:bg-sky-400 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
                Verifying...
              </>
            ) : (
              'Verify'
            )}
          </button>
        </div>

        {timeLeft && (
          <p className="text-center text-slate-500 text-sm">
            Link expires in {timeLeft}
          </p>
        )}
      </div>
    )
  }

  // Location verification screen
  if (viewState === 'location_verify' || viewState === 'verifying_location') {
    const isVerifying = viewState === 'verifying_location'

    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex flex-col p-6">
        <div className="flex-1 flex flex-col items-center justify-center text-center">
          <div className="w-20 h-20 bg-sky-500/20 rounded-full flex items-center justify-center mb-6">
            <svg className="w-10 h-10 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>

          <h1 className="text-3xl font-bold text-white mb-2">Verify your location</h1>
          <p className="text-slate-400 mb-2">
            Confirm you're at {session?.charger_name || 'the charging location'}
          </p>
          {session?.merchant_address && (
            <p className="text-slate-500 text-sm mb-8">{session.merchant_address}</p>
          )}

          {errorMessage && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 mb-6 w-full max-w-xs">
              <p className="text-amber-400 text-sm">{errorMessage}</p>
            </div>
          )}

          <button
            onClick={handleLocationVerify}
            disabled={isVerifying}
            className="w-full max-w-xs h-14 bg-sky-500 hover:bg-sky-400 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            {isVerifying ? (
              <>
                <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
                Checking location...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                </svg>
                Verify I'm here
              </>
            )}
          </button>
        </div>

        {timeLeft && (
          <p className="text-center text-slate-500 text-sm">
            Session expires in {timeLeft}
          </p>
        )}
      </div>
    )
  }

  // Success screen - show code to merchant
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex flex-col p-6">
      <div className="flex-1 flex flex-col items-center justify-center text-center">
        <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mb-6">
          <svg className="w-10 h-10 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>

        <h1 className="text-3xl font-bold text-white mb-2">You're checked in!</h1>
        <p className="text-slate-400 mb-8">
          Show this code at {session?.merchant_name || 'the merchant'}
        </p>

        <div className="bg-slate-800 rounded-2xl p-6 mb-4">
          <p className="text-5xl font-bold font-mono tracking-[0.3em] text-sky-400">
            {session?.session_code}
          </p>
        </div>

        <p className="text-slate-500 text-sm mb-8">
          Valid for {timeLeft || 'limited time'}
        </p>

        <div className="bg-slate-800/50 rounded-xl p-4 w-full max-w-xs">
          <p className="text-slate-400 text-sm">
            <span className="text-slate-500">Location:</span> {session?.charger_name}
          </p>
          {session?.merchant_address && (
            <p className="text-slate-500 text-xs mt-1">{session.merchant_address}</p>
          )}
        </div>
      </div>

      <button
        onClick={() => navigate('/')}
        className="w-full h-12 border border-slate-600 text-slate-400 font-medium rounded-xl hover:bg-slate-800 transition-colors"
      >
        Done
      </button>
    </div>
  )
}
