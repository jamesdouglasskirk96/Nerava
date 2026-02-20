import { useState } from 'react'
import { X, ArrowRight } from 'lucide-react'
import { otpStart, otpVerify, googleAuth, appleAuth, ApiError } from '../../services/auth'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined
const APPLE_CLIENT_ID = import.meta.env.VITE_APPLE_CLIENT_ID as string | undefined

interface LoginModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

type Step = 'phone' | 'code' | 'success'

export function LoginModal({ isOpen, onClose, onSuccess }: LoginModalProps) {
  const [step, setStep] = useState<Step>('phone')
  const [phone, setPhone] = useState('')
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const formatPhoneDisplay = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 10)
    if (digits.length <= 3) return digits
    if (digits.length <= 6) return `${digits.slice(0, 3)}-${digits.slice(3)}`
    return `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6)}`
  }

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhoneDisplay(e.target.value)
    setPhone(formatted)
    setError(null)
  }

  const handleSendCode = async () => {
    const digits = phone.replace(/\D/g, '')
    if (digits.length !== 10) {
      setError('Please enter a valid 10-digit phone number')
      return
    }

    setLoading(true)
    setError(null)

    try {
      await otpStart(digits)
      setStep('code')
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Failed to send code. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyCode = async () => {
    if (code.length !== 6) {
      setError('Please enter the 6-digit code')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const digits = phone.replace(/\D/g, '')
      await otpVerify(digits, code)
      setStep('success')
      setTimeout(() => {
        onSuccess()
        onClose()
      }, 1500)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Invalid code. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSignIn = () => {
    if (!GOOGLE_CLIENT_ID || typeof google === 'undefined') return

    setLoading(true)
    setError(null)

    google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: async (response) => {
        try {
          await googleAuth(response.credential)
          setStep('success')
          setTimeout(() => {
            onSuccess()
            onClose()
          }, 1500)
        } catch (err) {
          if (err instanceof ApiError) {
            setError(err.message)
          } else {
            setError('Google sign-in failed. Please try again.')
          }
        } finally {
          setLoading(false)
        }
      },
    })

    google.accounts.id.prompt((notification) => {
      if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
        // One Tap not available — fall back to renderButton approach
        const container = document.getElementById('google-signin-fallback')
        if (container) {
          container.innerHTML = ''
          google.accounts.id.renderButton(container, {
            type: 'standard',
            theme: 'outline',
            size: 'large',
            width: 400,
          })
          // Auto-click the rendered button
          const btn = container.querySelector('div[role="button"]') as HTMLElement | null
          btn?.click()
        }
        setLoading(false)
      }
    })
  }

  const handleAppleSignIn = async () => {
    if (!APPLE_CLIENT_ID || typeof AppleID === 'undefined') return

    setLoading(true)
    setError(null)

    try {
      AppleID.auth.init({
        clientId: APPLE_CLIENT_ID,
        scope: 'name email',
        redirectURI: window.location.origin,
        usePopup: true,
      })

      const response = await AppleID.auth.signIn()
      await appleAuth(response.authorization.id_token)
      setStep('success')
      setTimeout(() => {
        onSuccess()
        onClose()
      }, 1500)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        // User closed the popup — not an error worth showing
        const isCancel = err instanceof Error && (err.message.includes('popup') || err.message.includes('cancel'))
        if (!isCancel) {
          setError('Apple sign-in failed. Please try again.')
        }
      }
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setStep('phone')
    setPhone('')
    setCode('')
    setError(null)
    onClose()
  }

  const showSocialButtons = GOOGLE_CLIENT_ID || APPLE_CLIENT_ID

  return (
    <div className="fixed inset-0 bg-black/50 z-[60] flex items-end sm:items-center justify-center">
      <div className="bg-white w-full sm:max-w-md sm:rounded-2xl rounded-t-2xl p-6 animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold">
            {step === 'phone' && 'Sign in'}
            {step === 'code' && 'Enter code'}
            {step === 'success' && 'Welcome!'}
          </h2>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Phone Step */}
        {step === 'phone' && (
          <>
            {showSocialButtons && (
              <>
                {APPLE_CLIENT_ID && (
                  <button
                    onClick={handleAppleSignIn}
                    disabled={loading}
                    className="w-full py-3 bg-black text-white font-semibold rounded-xl hover:bg-gray-900 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-3 mb-3"
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/>
                    </svg>
                    Continue with Apple
                  </button>
                )}

                {GOOGLE_CLIENT_ID && (
                  <button
                    onClick={handleGoogleSignIn}
                    disabled={loading}
                    className="w-full py-3 bg-white text-gray-700 font-semibold rounded-xl border border-[#E4E6EB] hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-3 mb-3"
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
                      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                    </svg>
                    Continue with Google
                  </button>
                )}

                {/* Hidden fallback container for Google rendered button */}
                <div id="google-signin-fallback" className="hidden" />

                <div className="flex items-center gap-3 my-4">
                  <div className="flex-1 h-px bg-[#E4E6EB]" />
                  <span className="text-sm text-[#65676B]">or</span>
                  <div className="flex-1 h-px bg-[#E4E6EB]" />
                </div>
              </>
            )}

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Phone Number
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <span className="text-gray-500">+1</span>
                </div>
                <input
                  type="tel"
                  inputMode="numeric"
                  value={phone}
                  onChange={handlePhoneChange}
                  placeholder="555-123-4567"
                  className="w-full pl-12 pr-4 py-3 border border-[#E4E6EB] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1877F2] focus:border-transparent text-lg"
                  autoFocus={!showSocialButtons}
                />
              </div>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">
                {error}
              </div>
            )}

            <button
              onClick={handleSendCode}
              disabled={loading || phone.replace(/\D/g, '').length !== 10}
              className="w-full py-3 bg-[#1877F2] text-white font-semibold rounded-xl hover:bg-[#1664d9] disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  Send Code
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>

            <p className="text-xs text-[#65676B] text-center mt-4">
              By continuing, you agree to our Terms of Service and Privacy Policy
            </p>
          </>
        )}

        {/* Code Step */}
        {step === 'code' && (
          <>
            <p className="text-[#65676B] text-sm mb-6">
              We sent a 6-digit code to +1 {phone}
            </p>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Verification Code
              </label>
              <input
                type="text"
                inputMode="numeric"
                value={code}
                onChange={(e) => {
                  setCode(e.target.value.replace(/\D/g, '').slice(0, 6))
                  setError(null)
                }}
                placeholder="000000"
                className="w-full px-4 py-3 border border-[#E4E6EB] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1877F2] focus:border-transparent text-2xl text-center tracking-[0.5em] font-mono"
                autoFocus
              />
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">
                {error}
              </div>
            )}

            <button
              onClick={handleVerifyCode}
              disabled={loading || code.length !== 6}
              className="w-full py-3 bg-[#1877F2] text-white font-semibold rounded-xl hover:bg-[#1664d9] disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                'Verify'
              )}
            </button>

            <button
              onClick={() => {
                setStep('phone')
                setCode('')
                setError(null)
              }}
              className="w-full py-3 text-[#1877F2] font-medium mt-3"
            >
              Use different number
            </button>
          </>
        )}

        {/* Success Step */}
        {step === 'success' && (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-xl font-bold mb-2">You're signed in!</h3>
            <p className="text-[#65676B]">Redirecting...</p>
          </div>
        )}
      </div>
    </div>
  )
}
