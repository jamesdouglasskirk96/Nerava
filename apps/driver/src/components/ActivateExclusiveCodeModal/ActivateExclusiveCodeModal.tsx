// Simple 6-digit code entry modal for exclusive activation
import { useState, useRef, useEffect } from 'react'
import { AlertCircle, CheckCircle } from 'lucide-react'

interface ActivateExclusiveCodeModalProps {
  isOpen: boolean
  onClose: () => void
  onActivate: (code: string) => Promise<void>
  merchantName?: string
  exclusiveTitle?: string
}

/**
 * Simple 6-digit code entry modal for activating exclusive.
 * Accepts any 6-digit code for demo purposes.
 */
export function ActivateExclusiveCodeModal({
  isOpen,
  onClose,
  onActivate,
  merchantName = 'Merchant',
  exclusiveTitle = 'Exclusive',
}: ActivateExclusiveCodeModalProps) {
  const [code, setCode] = useState(['', '', '', '', '', ''])
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!isOpen) {
      setCode(['', '', '', '', '', ''])
      setError('')
      setIsLoading(false)
      setSuccess(false)
    }
  }, [isOpen])

  const handleCodeChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return
    
    const newCode = [...code]
    newCode[index] = value
    setCode(newCode)
    setError('')

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }

    // Auto-submit when all 6 digits are entered
    if (index === 5 && value && newCode.every(digit => digit)) {
      handleActivate(newCode.join(''))
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handleActivate = async (codeToActivate?: string) => {
    const codeToUse = codeToActivate || code.join('')
    
    if (codeToUse.length !== 6) {
      setError('Please enter the complete 6-digit code')
      return
    }

    setIsLoading(true)
    setError('')

    try {
      await onActivate(codeToUse)
      setSuccess(true)
      // Close modal after 1.5 seconds on success
      setTimeout(() => {
        onClose()
      }, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to activate exclusive. Please try again.')
      setCode(['', '', '', '', '', ''])
      inputRefs.current[0]?.focus()
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl">
        {success ? (
          <>
            {/* Success State */}
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-2xl text-center mb-3 text-gray-900">Exclusive Activated!</h2>
            <p className="text-center text-[#65676B] mb-6">
              Your exclusive at {merchantName} is now active.
            </p>
          </>
        ) : (
          <>
            {/* Icon */}
            <div className="w-16 h-16 bg-[#1877F2]/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-8 h-8 text-[#1877F2]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>

            {/* Title */}
            <h2 className="text-2xl text-center mb-3">Activate your exclusive</h2>

            {/* Subtext */}
            <p className="text-center text-[#65676B] mb-6">
              Enter the 6-digit code to activate {exclusiveTitle} at {merchantName}
            </p>

            {/* Code Input */}
            <div className="flex gap-2 justify-center mb-4">
              {code.map((digit, index) => (
                <input
                  key={index}
                  ref={el => { inputRefs.current[index] = el }}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleCodeChange(index, e.target.value)}
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

            {/* Activate Button */}
            <button
              onClick={() => handleActivate()}
              disabled={isLoading || code.some(d => !d)}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all mb-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Activating...' : 'Activate Exclusive'}
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






