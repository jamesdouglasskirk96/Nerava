import { useState, useRef, useEffect } from 'react'
import { X } from 'lucide-react'
import { otpStart, otpVerify, emailOtpStart, emailOtpVerify, ApiError } from '../../services/auth'

interface LoginModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export function LoginModal({ isOpen, onClose, onSuccess }: LoginModalProps) {
  const [step, setStep] = useState<'input' | 'code'>('input')
  const [mode, setMode] = useState<'email' | 'phone'>('email')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [countdown, setCountdown] = useState(0)

  const codeInputRef = useRef<HTMLInputElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Countdown timer for resend
  useEffect(() => {
    if (countdown <= 0) return
    const timer = setTimeout(() => setCountdown(c => c - 1), 1000)
    return () => clearTimeout(timer)
  }, [countdown])

  // Auto-focus inputs
  useEffect(() => {
    if (!isOpen) return
    if (step === 'input') inputRef.current?.focus()
    if (step === 'code') codeInputRef.current?.focus()
  }, [isOpen, step])

  if (!isOpen) return null

  const formatPhone = (value: string) => {
    const digits = value.replace(/\D/g, '')
    if (digits.length <= 3) return digits
    if (digits.length <= 6) return `(${digits.slice(0, 3)}) ${digits.slice(3)}`
    return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 10)}`
  }

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/\D/g, '').slice(0, 10)
    setPhone(raw)
    setError(null)
  }

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value)
    setError(null)
  }

  const isValidEmail = (val: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val.trim())

  const handleSendCode = async () => {
    if (mode === 'phone' && phone.length < 10) {
      setError('Please enter a valid 10-digit phone number.')
      return
    }
    if (mode === 'email' && !isValidEmail(email)) {
      setError('Please enter a valid email address.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      if (mode === 'email') {
        await emailOtpStart(email)
      } else {
        await otpStart(phone)
      }
      setStep('code')
      setCountdown(60)
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
    if (code.length < 6) {
      setError('Please enter the 6-digit code.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      if (mode === 'email') {
        await emailOtpVerify(email, code)
      } else {
        await otpVerify(phone, code)
      }
      onSuccess()
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Verification failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    if (countdown > 0) return
    setLoading(true)
    setError(null)
    try {
      if (mode === 'email') {
        await emailOtpStart(email)
      } else {
        await otpStart(phone)
      }
      setCountdown(60)
      setCode('')
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Failed to resend code.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setStep('input')
    setPhone('')
    setEmail('')
    setCode('')
    setError(null)
    setCountdown(0)
    onClose()
  }

  const handleBack = () => {
    setStep('input')
    setCode('')
    setError(null)
  }

  const switchMode = () => {
    setMode(mode === 'email' ? 'phone' : 'email')
    setError(null)
  }

  const canSend = mode === 'email' ? isValidEmail(email) : phone.length >= 10
  const sentTo = mode === 'email'
    ? email.trim()
    : `+1 ${formatPhone(phone)}`

  return (
    <div className="fixed inset-0 bg-black/50 z-[3100] flex items-end sm:items-center justify-center">
      <div className="bg-white w-full sm:max-w-md sm:rounded-2xl rounded-t-2xl p-6 animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            {step === 'code' && (
              <button
                onClick={handleBack}
                className="p-1 hover:bg-gray-100 rounded-full transition-colors"
              >
                <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            )}
            <h2 className="text-xl font-bold">
              {step === 'input' ? 'Sign in' : 'Enter code'}
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">
            {error}
          </div>
        )}

        {step === 'input' ? (
          <>
            <p className="text-[#65676B] text-sm mb-4">
              {mode === 'email'
                ? 'Enter your email to sign in or create an account.'
                : 'Enter your phone number to sign in or create an account.'}
            </p>

            <div className="mb-4">
              {mode === 'email' ? (
                <>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email address
                  </label>
                  <input
                    ref={inputRef}
                    type="email"
                    value={email}
                    onChange={handleEmailChange}
                    placeholder="you@example.com"
                    className="w-full py-3 px-4 text-base border border-gray-300 rounded-xl outline-none focus:ring-2 focus:ring-[#1877F2] focus:border-transparent"
                    onKeyDown={e => e.key === 'Enter' && handleSendCode()}
                  />
                </>
              ) : (
                <>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Phone number
                  </label>
                  <div className="flex items-center border border-gray-300 rounded-xl overflow-hidden focus-within:ring-2 focus-within:ring-[#1877F2] focus-within:border-transparent">
                    <span className="pl-4 pr-2 text-gray-500 text-sm">+1</span>
                    <input
                      ref={inputRef}
                      type="tel"
                      value={formatPhone(phone)}
                      onChange={handlePhoneChange}
                      placeholder="(555) 123-4567"
                      className="flex-1 py-3 pr-4 text-base outline-none"
                      onKeyDown={e => e.key === 'Enter' && handleSendCode()}
                    />
                  </div>
                </>
              )}
            </div>

            <button
              onClick={handleSendCode}
              disabled={loading || !canSend}
              className="w-full py-3 bg-[#1877F2] text-white font-semibold rounded-xl hover:bg-[#166FE5] disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                'Send Code'
              )}
            </button>

            <button
              onClick={switchMode}
              className="w-full text-sm text-[#1877F2] font-medium mt-3"
            >
              {mode === 'email' ? 'Use phone number instead' : 'Use email instead'}
            </button>
          </>
        ) : (
          <>
            <p className="text-[#65676B] text-sm mb-4">
              We sent a 6-digit code to <span className="font-medium text-gray-900">{sentTo}</span>
            </p>

            <div className="mb-4">
              <input
                ref={codeInputRef}
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                value={code}
                onChange={e => {
                  setCode(e.target.value.replace(/\D/g, '').slice(0, 6))
                  setError(null)
                }}
                placeholder="000000"
                className="w-full py-3 px-4 text-center text-2xl font-mono tracking-[0.5em] border border-gray-300 rounded-xl outline-none focus:ring-2 focus:ring-[#1877F2] focus:border-transparent"
                onKeyDown={e => e.key === 'Enter' && handleVerifyCode()}
              />
            </div>

            <button
              onClick={handleVerifyCode}
              disabled={loading || code.length < 6}
              className="w-full py-3 bg-[#1877F2] text-white font-semibold rounded-xl hover:bg-[#166FE5] disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center mb-3"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                'Verify'
              )}
            </button>

            <button
              onClick={handleResend}
              disabled={countdown > 0 || loading}
              className="w-full text-sm text-[#1877F2] font-medium disabled:text-gray-400"
            >
              {countdown > 0 ? `Resend code in ${countdown}s` : 'Resend code'}
            </button>
          </>
        )}

        <p className="text-xs text-[#65676B] text-center mt-4">
          By continuing, you agree to our Terms of Service and Privacy Policy
        </p>
      </div>
    </div>
  )
}
