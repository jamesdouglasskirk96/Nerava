import { useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { fetchAPI, ApiError } from '../services/api';

type ClaimStep = 'form' | 'verify-phone' | 'verify-email' | 'success';

interface ClaimFormData {
  businessName: string;
  email: string;
  phone: string;
}

export function ClaimBusiness() {
  const { merchantId } = useParams<{ merchantId?: string }>();
  const [searchParams] = useSearchParams();
  
  // Get merchant_id from URL param or query param
  const merchantIdFromUrl = merchantId || searchParams.get('merchant_id');
  
  const [step, setStep] = useState<ClaimStep>('form');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [formData, setFormData] = useState<ClaimFormData>({
    businessName: '',
    email: '',
    phone: '',
  });
  const [otpCode, setOtpCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    if (!merchantIdFromUrl) {
      setError('Merchant ID is required');
      setLoading(false);
      return;
    }

    try {
      const response = await fetchAPI<{ session_id: string; message: string }>(
        '/v1/merchant/claim/start',
        {
          method: 'POST',
          body: JSON.stringify({
            merchant_id: merchantIdFromUrl,
            email: formData.email,
            phone: formData.phone,
            business_name: formData.businessName,
          }),
        }
      );
      setSessionId(response.session_id);
      setStep('verify-phone');
      setError(null);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || 'Failed to start claim');
      } else {
        setError('Failed to start claim');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyPhone = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    if (!sessionId) {
      setError('Session not found');
      setLoading(false);
      return;
    }

    try {
      await fetchAPI<{ phone_verified: boolean; message: string }>(
        '/v1/merchant/claim/verify-phone',
        {
          method: 'POST',
          body: JSON.stringify({
            session_id: sessionId,
            code: otpCode,
          }),
        }
      );
      
      // Send magic link automatically after phone verification
      await sendMagicLink();
      setStep('verify-email');
      setError(null);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || 'Invalid verification code');
      } else {
        setError('Invalid verification code');
      }
    } finally {
      setLoading(false);
    }
  };

  const sendMagicLink = async () => {
    if (!sessionId) return;

    try {
      await fetchAPI<{ email_sent: boolean; message: string }>(
        '/v1/merchant/claim/send-magic-link',
        {
          method: 'POST',
          body: JSON.stringify({
            session_id: sessionId,
          }),
        }
      );
    } catch (err) {
      console.error('Failed to send magic link:', err);
      // Don't show error to user, they can resend
    }
  };

  const handleResendCode = async () => {
    if (!sessionId) return;
    setError(null);
    setLoading(true);

    try {
      await fetchAPI<{ session_id: string; message: string }>(
        '/v1/merchant/claim/start',
        {
          method: 'POST',
          body: JSON.stringify({
            merchant_id: merchantIdFromUrl,
            email: formData.email,
            phone: formData.phone,
            business_name: formData.businessName,
          }),
        }
      );
      setOtpCode('');
      setError(null);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || 'Failed to resend code');
      } else {
        setError('Failed to resend code');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-xl shadow-sm border border-neutral-200 p-8">
        {/* Progress indicator */}
        <div className="flex justify-between mb-8">
          {['form', 'verify-phone', 'verify-email'].map((s, i) => (
            <div
              key={s}
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                step === s
                  ? 'bg-green-500 text-white'
                  : ['form', 'verify-phone', 'verify-email'].indexOf(step) > i
                  ? 'bg-green-200 text-green-800'
                  : 'bg-neutral-200 text-neutral-500'
              }`}
            >
              {i + 1}
            </div>
          ))}
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Step 1: Form */}
        {step === 'form' && (
          <form onSubmit={handleFormSubmit}>
            <h2 className="text-2xl font-bold mb-6 text-neutral-900">Claim Your Business</h2>

            {!merchantIdFromUrl && (
              <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 text-yellow-700 rounded-lg text-sm">
                Merchant ID required. Add ?merchant_id=XXX to URL or use /claim/:merchantId
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  Business Name
                </label>
                <input
                  type="text"
                  required
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  value={formData.businessName}
                  onChange={(e) => setFormData({ ...formData, businessName: e.target.value })}
                  placeholder="Your Business Name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="you@business.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  Phone Number
                </label>
                <input
                  type="tel"
                  required
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="+1 (555) 123-4567"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !merchantIdFromUrl}
              className="w-full mt-6 py-3 bg-neutral-900 text-white rounded-lg font-medium hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Sending code...' : 'Continue'}
            </button>
          </form>
        )}

        {/* Step 2: Verify Phone */}
        {step === 'verify-phone' && (
          <form onSubmit={handleVerifyPhone}>
            <h2 className="text-2xl font-bold mb-2 text-neutral-900">Verify Your Phone</h2>
            <p className="text-neutral-600 mb-6">
              Enter the 6-digit code sent to {formData.phone}
            </p>

            <input
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={6}
              required
              className="w-full px-3 py-4 text-center text-2xl tracking-widest border border-neutral-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              value={otpCode}
              onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
              placeholder="000000"
              autoFocus
            />

            <button
              type="submit"
              disabled={loading || otpCode.length !== 6}
              className="w-full mt-6 py-3 bg-neutral-900 text-white rounded-lg font-medium hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Verifying...' : 'Verify Code'}
            </button>

            <button
              type="button"
              onClick={handleResendCode}
              disabled={loading}
              className="w-full mt-2 py-2 text-green-600 text-sm hover:text-green-700 disabled:opacity-50"
            >
              Resend code
            </button>
          </form>
        )}

        {/* Step 3: Check Email */}
        {step === 'verify-email' && (
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>

            <h2 className="text-2xl font-bold mb-2 text-neutral-900">Check Your Email</h2>
            <p className="text-neutral-600 mb-6">
              We sent a magic link to <strong>{formData.email}</strong>
            </p>
            <p className="text-sm text-neutral-500">
              Click the link in your email to complete the claim process.
              The link expires in 15 minutes.
            </p>

            <button
              type="button"
              onClick={sendMagicLink}
              disabled={loading}
              className="mt-6 text-green-600 text-sm hover:text-green-700 disabled:opacity-50"
            >
              {loading ? 'Sending...' : 'Resend email'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
