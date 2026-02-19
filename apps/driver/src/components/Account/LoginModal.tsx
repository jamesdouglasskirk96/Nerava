import { useState } from 'react'
import { X, ArrowRight } from 'lucide-react'
import { otpStart, otpVerify, ApiError } from '../../services/auth'

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

  const handleClose = () => {
    setStep('phone')
    setPhone('')
    setCode('')
    setError(null)
    onClose()
  }

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
            <p className="text-[#65676B] text-sm mb-6">
              Enter your phone number to sign in or create an account
            </p>

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
                  autoFocus
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
