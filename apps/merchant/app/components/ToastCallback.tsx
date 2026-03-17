import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { handleToastCallback } from '../services/api';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export function ToastCallback() {
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

    handleToastCallback(code, state)
      .then((response) => {
        toast.success(`Connected to ${response.restaurant_name}`);
        navigate('/settings');
      })
      .catch((err) => {
        setError(err.message || 'Failed to connect Toast account');
      });
  }, [searchParams, navigate]);

  if (error) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-white rounded-xl shadow-sm border border-neutral-200 p-8 text-center">
          <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-red-600 text-xl">!</span>
          </div>
          <h2 className="text-xl font-semibold text-neutral-900 mb-2">Connection Failed</h2>
          <p className="text-neutral-600 text-sm mb-6">{error}</p>
          <button
            onClick={() => navigate('/settings')}
            className="bg-neutral-900 text-white px-6 py-2.5 rounded-lg hover:bg-neutral-800 transition-colors"
          >
            Back to Settings
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
      <div className="text-center">
        <Loader2 className="w-8 h-8 animate-spin text-neutral-400 mx-auto mb-4" />
        <p className="text-neutral-600">Connecting Toast account...</p>
      </div>
    </div>
  );
}
