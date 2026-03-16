import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { handleGoogleCallback, fetchMyMerchant } from '../services/api';
import { Loader2 } from 'lucide-react';

export function GoogleCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');

    if (!code || !state) {
      setError('Missing authorization code or state. Please try again.');
      return;
    }

    handleGoogleCallback(code, state)
      .then(async (response) => {
        // Store auth tokens
        localStorage.setItem('access_token', response.access_token);
        if (response.refresh_token) {
          localStorage.setItem('refresh_token', response.refresh_token);
        }
        if (response.merchant_account_id) {
          localStorage.setItem('merchant_account_id', response.merchant_account_id);
        }

        // Check if user already has a claimed merchant — skip location selection if so
        try {
          const merchantData = await fetchMyMerchant();
          if (merchantData.merchant?.id) {
            localStorage.setItem('merchant_id', merchantData.merchant.id);
            localStorage.setItem('businessClaimed', 'true');
            if (merchantData.merchant.name) {
              localStorage.setItem('merchant_name', merchantData.merchant.name);
            }
            navigate('/overview');
            return;
          }
        } catch {
          // No merchant yet — proceed to location selection
        }

        navigate('/claim/location');
      })
      .catch((err) => {
        setError(err.message || 'Failed to complete Google sign-in');
      });
  }, [searchParams, navigate]);

  if (error) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-white rounded-xl shadow-sm border border-neutral-200 p-8 text-center">
          <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-red-600 text-xl">!</span>
          </div>
          <h2 className="text-xl font-semibold text-neutral-900 mb-2">Sign-in Failed</h2>
          <p className="text-neutral-600 text-sm mb-6">{error}</p>
          <button
            onClick={() => navigate('/claim')}
            className="bg-neutral-900 text-white px-6 py-2.5 rounded-lg hover:bg-neutral-800 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
      <div className="text-center">
        <Loader2 className="w-8 h-8 animate-spin text-neutral-400 mx-auto mb-4" />
        <p className="text-neutral-600">Completing sign-in...</p>
      </div>
    </div>
  );
}
