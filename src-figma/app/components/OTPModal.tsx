import { useState, useRef, useEffect } from "react";
import { Smartphone, AlertCircle } from "lucide-react";

interface OTPModalProps {
  onSuccess: () => void;
  onClose: () => void;
}

export function OTPModal({ onSuccess, onClose }: OTPModalProps) {
  const [step, setStep] = useState<'phone' | 'code'>('phone');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [canResend, setCanResend] = useState(false);
  const [resendTimer, setResendTimer] = useState(30);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Format phone number as user types
  const formatPhoneNumber = (value: string) => {
    const cleaned = value.replace(/\D/g, '');
    const match = cleaned.match(/^(\d{0,3})(\d{0,3})(\d{0,4})$/);
    if (match) {
      const formatted = [match[1], match[2], match[3]].filter(Boolean).join('-');
      return formatted;
    }
    return value;
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhoneNumber(e.target.value);
    setPhoneNumber(formatted);
    setError('');
  };

  const handleSendCode = () => {
    const cleaned = phoneNumber.replace(/\D/g, '');
    if (cleaned.length !== 10) {
      setError('Please enter a valid 10-digit phone number');
      return;
    }
    
    // In production, this would call an API to send SMS
    console.log('Sending OTP to:', phoneNumber);
    
    setStep('code');
    setError('');
    setResendTimer(30);
    setCanResend(false);
  };

  const handleOTPChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    setError('');

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    // Auto-submit when all 6 digits are entered
    if (index === 5 && value && newOtp.every(digit => digit)) {
      handleVerifyCode(newOtp.join(''));
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleVerifyCode = (code?: string) => {
    const codeToVerify = code || otp.join('');
    
    if (codeToVerify.length !== 6) {
      setError('Please enter the complete 6-digit code');
      return;
    }

    // In production, this would call an API to verify OTP
    // For demo, accept ANY 6-digit code
    if (/^\d{6}$/.test(codeToVerify)) {
      // Store auth state silently
      localStorage.setItem('neravaAuth', JSON.stringify({
        phone: phoneNumber,
        authenticated: true,
        timestamp: Date.now()
      }));
      
      onSuccess();
    } else {
      setError('Incorrect code. Please try again.');
      setOtp(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    }
  };

  const handleResend = () => {
    if (!canResend) return;
    
    // In production, call API to resend OTP
    console.log('Resending OTP to:', phoneNumber);
    
    setCanResend(false);
    setResendTimer(30);
    setError('');
    setOtp(['', '', '', '', '', '']);
    inputRefs.current[0]?.focus();
  };

  const handleEditPhone = () => {
    setStep('phone');
    setOtp(['', '', '', '', '', '']);
    setError('');
  };

  // Resend timer countdown
  useEffect(() => {
    if (step === 'code' && resendTimer > 0) {
      const timer = setTimeout(() => {
        setResendTimer(prev => {
          if (prev <= 1) {
            setCanResend(true);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [step, resendTimer]);

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
            <h2 className="text-2xl text-center mb-3">Activate your exclusive</h2>

            {/* Subtext */}
            <p className="text-center text-[#65676B] mb-6">
              We'll send you one text during your charging session.
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
              No spam. One message per session.
            </p>

            {/* Send Code Button */}
            <button
              onClick={handleSendCode}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all mb-3"
            >
              Send code
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
                  ref={el => inputRefs.current[index] = el}
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
                  className="text-sm text-[#1877F2] font-medium hover:underline"
                >
                  Resend code
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
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all mb-3"
            >
              Confirm & Activate
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
  );
}