// Activate Exclusive Modal with phone number and OTP entry
import { useState, useRef, useEffect } from 'react'
import { Smartphone, AlertCircle } from 'lucide-react'
import { otpStart, otpVerify } from '../../services/auth'
import { ApiError } from '../../services/api'
import { capture, identify, DRIVER_EVENTS } from '../../analytics'
import { ExclusiveInfoTooltip } from '../shared/ExclusiveInfoTooltip'

interface ActivateExclusiveModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

/**
 * Two-step modal for activating exclusive:
 * 1. Enter phone number
 * 2. Enter OTP (6 digits, mocked - any 6 digits pass)
 */
export function ActivateExclusiveModal({
  isOpen,
  onClose,
  onSuccess,
}: ActivateExclusiveModalProps) {
  const [step, setStep] = useState<'phone' | 'code'>('phone')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [otp, setOtp] = useState(['', '', '', '', '', ''])
  const [error, setError] = useState('')
  const [canResend, setCanResend] = useState(false)
  const [resendTimer, setResendTimer] = useState(30)
  const [isLoading, setIsLoading] = useState(false)
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!isOpen) {
      setStep('phone')
      setPhoneNumber('')
      setOtp(['', '', '', '', '', ''])
      setError('')
      setCanResend(false)
      setResendTimer(30)
    }
  }, [isOpen])

  // Format phone number as user types
  const formatPhoneNumber = (value: string) => {
    const cleaned = value.replace(/\D/g, '')
    const match = cleaned.match(/^(\d{0,3})(\d{0,3})(\d{0,4})$/)
    if (match) {
      const formatted = [match[1], match[2], match[3]].filter(Boolean).join('-')
      return formatted
    }
    return value
  }

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhoneNumber(e.target.value)
    setPhoneNumber(formatted)
    setError('')
  }

  const handleSendCode = async () => {
    const cleaned = phoneNumber.replace(/\D/g, '')
    if (cleaned.length !== 10) {
      setError('Please enter a valid 10-digit phone number')
      return
    }
    
    setIsLoading(true)
    setError('')
    
    try {
      await otpStart(phoneNumber)
      // Track both the original event and the button click event
      capture(DRIVER_EVENTS.OTP_START, {
        phone_last4: cleaned.slice(-4),
      })
      capture(DRIVER_EVENTS.OTP_SEND_CODE_CLICKED, {
        phone_last4: cleaned.slice(-4),
        path: window.location.pathname,
      })
      setStep('code')
      setResendTimer(30)
      setCanResend(false)
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 429) {
          setError('Too many requests. Please try again in a moment.')
        } else if (err.status === 400) {
          setError('Invalid phone number format. Please check and try again.')
        } else {
          setError(err.message || 'Failed to send code. Please try again.')
        }
      } else {
        setError('Network error. Please check your connection and try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleOTPChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return
    
    const newOtp = [...otp]
    newOtp[index] = value
    setOtp(newOtp)
    setError('')

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }

    // Auto-submit when all 6 digits are entered
    if (index === 5 && value && newOtp.every(digit => digit)) {
      handleVerifyCode(newOtp.join(''))
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handleVerifyCode = async (code?: string) => {
    const codeToVerify = code || otp.join('')
    
    if (codeToVerify.length !== 6) {
      setError('Please enter the complete 6-digit code')
      return
    }

    setIsLoading(true)
    setError('')

    try {
      const result = await otpVerify(phoneNumber, codeToVerify)
      const cleaned = phoneNumber.replace(/\D/g, '')
      
      // Identify user after successful OTP verification
      if (result.user?.public_id) {
        identify(result.user.public_id, {
          phone_last4: cleaned.slice(-4),
          created_at: new Date().toISOString(),
        })
      }
      
      // Track both the original event and the button click event
      capture(DRIVER_EVENTS.OTP_VERIFY_SUCCESS, {
        phone_last4: cleaned.slice(-4),
        driver_id: result.user?.public_id,
      })
      capture(DRIVER_EVENTS.OTP_VERIFY_CLICKED, {
        phone_last4: cleaned.slice(-4),
        driver_id: result.user?.public_id,
        path: window.location.pathname,
      })
      
      // Tokens are stored in otpVerify function
      onSuccess()
    } catch (err: unknown) {
      const cleaned = phoneNumber.replace(/\D/g, '')
      capture(DRIVER_EVENTS.OTP_VERIFY_FAIL, {
        phone_last4: cleaned.slice(-4),
      })
      
      if (err instanceof ApiError) {
        if (err.status === 401) {
          setError('Incorrect code. Please try again.')
        } else if (err.status === 429) {
          setError('Too many requests. Please try again in a moment.')
        } else if (err.status >= 500) {
          setError('Verification unavailable right now. Try again.')
        } else {
          setError(err.message || 'Verification failed. Please try again.')
        }
      } else {
        setError('Network error. Please check your connection and try again.')
      }
      setOtp(['', '', '', '', '', ''])
      inputRefs.current[0]?.focus()
    } finally {
      setIsLoading(false)
    }
  }

  const handleResend = async () => {
    if (!canResend) return
    
    setIsLoading(true)
    setError('')
    
    try {
      await otpStart(phoneNumber)
      setCanResend(false)
      setResendTimer(30)
      setOtp(['', '', '', '', '', ''])
      inputRefs.current[0]?.focus()
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 429) {
          setError('Too many requests. Please try again in a moment.')
        } else {
          setError(err.message || 'Failed to resend code. Please try again.')
        }
      } else {
        setError('Network error. Please check your connection and try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleEditPhone = () => {
    setStep('phone')
    setOtp(['', '', '', '', '', ''])
    setError('')
  }

  // Resend timer countdown
  useEffect(() => {
    if (step === 'code' && resendTimer > 0) {
      const timer = setTimeout(() => {
        setResendTimer(prev => {
          if (prev <= 1) {
            setCanResend(true)
            return 0
          }
          return prev - 1
        })
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [step, resendTimer])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-[60] p-4">
      <div className="bg-white rounded-3xl p-8 max-w-md w-full mb-8 shadow-2xl">
        {step === 'phone' ? (
          <>
            {/* Icon */}
            <div className="w-16 h-16 bg-[#1877F2]/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <Smartphone className="w-8 h-8 text-[#1877F2]" />
            </div>

            {/* Title */}
            <div className="flex items-center justify-center gap-2 mb-3">
              <h2 className="text-2xl text-center">Verify to redeem</h2>
              <ExclusiveInfoTooltip />
            </div>

            {/* Subtext */}
            <p className="text-center text-[#65676B] mb-6">
              We'll text you a one-time code so the merchant can confirm your exclusive.
            </p>

            {/* Phone Input */}
            <div className="mb-4">
              <input
                type="tel"
                value={phoneNumber}
                onChange={handlePhoneChange}
                placeholder="555-123-4567"
                maxLength={12}
                className="w-full px-4 py-4 bg-[#F7F8FA] border-2 border-[#E4E6EB] rounded-2xl text-center text-lg tracking-wider focus:border-[#1877F2] focus:outline-none transition-colors"
              />
              {error && (
                <div className="flex items-center gap-2 mt-2 text-red-600">
                  <AlertCircle className="w-4 h-4" />
                  <p className="text-sm">{error}</p>
                </div>
              )}
            </div>

            {/* Privacy Note */}
            <p className="text-xs text-center text-[#65676B] mb-6">
              No spam. One verification code.
            </p>

            {/* Send Code Button */}
            <button
              onClick={handleSendCode}
              disabled={isLoading}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all mb-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Sending...' : 'Send code'}
            </button>

            {/* Cancel Button */}
            <button
              onClick={onClose}
              className="w-full py-4 bg-[#F7F8FA] text-[#050505] rounded-2xl font-medium hover:bg-[#E4E6EB] active:scale-98 transition-all"
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            {/* Icon */}
            <div className="w-16 h-16 bg-[#1877F2]/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <Smartphone className="w-8 h-8 text-[#1877F2]" />
            </div>

            {/* Title */}
            <h2 className="text-2xl text-center mb-3">Enter the code we sent</h2>

            {/* Phone Number Display */}
            <p className="text-center text-[#65676B] mb-6">
              Sent to {phoneNumber} ·{' '}
              <button
                onClick={handleEditPhone}
                className="text-[#1877F2] font-medium hover:underline"
              >
                Edit
              </button>
            </p>

            {/* OTP Input */}
            <div className="flex gap-2 justify-center mb-4">
              {otp.map((digit, index) => (
                <input
                  key={index}
                  ref={el => { inputRefs.current[index] = el }}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleOTPChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  className={`w-12 h-14 text-center text-xl font-medium bg-[#F7F8FA] border-2 rounded-xl focus:border-[#1877F2] focus:outline-none transition-colors ${
                    error ? 'border-red-500' : 'border-[#E4E6EB]'
                  }`}
                  autoFocus={index === 0}
                />
              ))}
            </div>

            {/* Error Message */}
            {error && (
              <div className="flex items-center justify-center gap-2 mb-4 text-red-600">
                <AlertCircle className="w-4 h-4" />
                <p className="text-sm">{error}</p>
              </div>
            )}

            {/* Resend Code */}
            <div className="text-center mb-6">
              {canResend ? (
                <button
                  onClick={handleResend}
                  disabled={isLoading}
                  className="text-sm text-[#1877F2] font-medium hover:underline disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Resending...' : 'Resend code'}
                </button>
              ) : (
                <p className="text-sm text-[#65676B]">
                  Resend code in {resendTimer}s
                </p>
              )}
            </div>

            {/* Confirm Button */}
            <button
              onClick={() => handleVerifyCode()}
              disabled={isLoading}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all mb-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Verifying...' : 'Confirm & Activate'}
            </button>

            {/* Cancel Button */}
            <button
              onClick={onClose}
              className="w-full py-4 bg-[#F7F8FA] text-[#050505] rounded-2xl font-medium hover:bg-[#E4E6EB] active:scale-98 transition-all"
            >
              Cancel
            </button>
          </>
        )}
      </div>
    </div>
  )
}

