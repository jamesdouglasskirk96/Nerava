import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { fetchAPI, ApiError } from '../services/api';

export function ClaimVerify() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      setStatus('error');
      setError('Invalid link');
      return;
    }

    fetchAPI<{ access_token: string; token_type: string; user: any; merchant_id: string }>(
      `/v1/merchant/claim/verify-magic-link?token=${token}`
    )
      .then((response) => {
        // Store token
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('businessClaimed', 'true');
        
        // Store merchant_id from response
        if (response.merchant_id) {
          localStorage.setItem('merchant_id', response.merchant_id);
        }
        
        // Store user info if available
        if (response.user) {
          localStorage.setItem('user_id', response.user.id || '');
        }
        
        setStatus('success');
        // Redirect to dashboard after 2 seconds
        setTimeout(() => navigate('/overview'), 2000);
      })
      .catch((err) => {
        setStatus('error');
        if (err instanceof ApiError) {
          setError(err.message || 'Failed to verify link');
        } else {
          setError('Failed to verify link');
        }
      });
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
        {status === 'loading' && (
          <>
            <div className="w-12 h-12 border-4 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-neutral-600">Verifying your claim...</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-neutral-900 mb-2">Claim Complete!</h2>
            <p className="text-neutral-600">Redirecting to your dashboard...</p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-neutral-900 mb-2">Verification Failed</h2>
            <p className="text-neutral-600 mb-4">{error}</p>
            <button
              onClick={() => navigate('/claim')}
              className="text-green-600 hover:text-green-700"
            >
              Try again
            </button>
          </>
        )}
      </div>
    </div>
  );
}




