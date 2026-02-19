import { useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { fetchAPI, ApiError } from '../services/api';

interface ExclusiveSession {
  id: string
  merchant_id: string | null
  charger_id: string | null
  expires_at: string
  activated_at: string
  remaining_seconds: number
}

interface ExclusiveSessionResponse {
  exclusive_session: ExclusiveSession | null
  merchant_name: string | null
  exclusive_title: string | null
  staff_instructions: string | null
}

export function CustomerExclusiveView() {
  const { exclusiveId } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<ExclusiveSession | null>(null);
  const [merchantName, setMerchantName] = useState<string>('');
  const [exclusiveName, setExclusiveName] = useState<string>('');
  const [staffInstructions, setStaffInstructions] = useState<string>('');
  const [timeRemaining, setTimeRemaining] = useState<number>(0);
  
  useEffect(() => {
    if (exclusiveId) {
      loadExclusiveSession(exclusiveId);
    }
  }, [exclusiveId]);

  const loadExclusiveSession = async (sessionId: string) => {
    try {
      setLoading(true);
      setError(null);

      const data = await fetchAPI<ExclusiveSessionResponse>(`/v1/exclusive/session/${sessionId}`);
      
      if (!data.exclusive_session) {
        setError('Exclusive session not found or expired');
        setLoading(false);
        return;
      }

      setSession(data.exclusive_session);
      setMerchantName(data.merchant_name || 'Merchant');
      setExclusiveName(data.exclusive_title || 'Active Exclusive');
      setStaffInstructions(data.staff_instructions || 'Verify customer activation');
      
    } catch (err) {
      console.error('Failed to load exclusive session:', err);
      setError(err instanceof ApiError ? err.message : 'Failed to load exclusive session');
    } finally {
      setLoading(false);
    }
  };

  // Countdown timer - update timeRemaining when session changes
  useEffect(() => {
    if (!session) return;
    
    // Initialize from session
    setTimeRemaining(session.remaining_seconds || 0);
    
    const interval = setInterval(() => {
      setTimeRemaining(prev => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(interval);
  }, [session]);

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
        <div className="text-center">
          <p className="text-neutral-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl text-neutral-900 mb-2">Exclusive Not Found</h1>
          <p className="text-neutral-600">{error || 'This exclusive session is not available'}</p>
        </div>
      </div>
    );
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-6">
      <div className="max-w-lg w-full">
        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
          {/* Merchant Info */}
          <div className="text-center mb-8">
            <div className="text-sm text-neutral-600 mb-2">Exclusive at</div>
            <h1 className="text-2xl text-neutral-900">{merchantName}</h1>
          </div>

          {/* Active Badge */}
          <div className="bg-green-100 rounded-2xl p-8 mb-8">
            <div className="flex flex-col items-center text-center">
              <div className="mb-4">
                <div className="p-4 bg-white rounded-full shadow-sm">
                  <CheckCircle className="w-12 h-12 text-green-600" />
                </div>
              </div>
              <h2 className="text-xl text-green-900 mb-2">Exclusive Active</h2>
              <p className="text-lg text-green-800">{exclusiveName}</p>
            </div>
          </div>

          {/* Countdown */}
          <div className="bg-neutral-50 rounded-xl p-6 mb-8">
            <div className="flex items-center justify-center gap-3">
              <Clock className="w-6 h-6 text-neutral-600" />
              <div>
                <div className="text-xs text-neutral-600 mb-1">Time Remaining</div>
                <div className="text-3xl text-neutral-900 tabular-nums">{formatTime(timeRemaining)}</div>
              </div>
            </div>
          </div>

          {/* Staff Instructions */}
          {staffInstructions && (
            <div className="border-t border-neutral-200 pt-6">
              <div className="text-xs text-neutral-600 mb-2">Staff Instructions</div>
              <p className="text-sm text-neutral-900">{staffInstructions}</p>
            </div>
          )}
        </div>

        {/* Info Footer */}
        <div className="text-center">
          <p className="text-sm text-neutral-600">
            Show this screen to staff to redeem your exclusive
          </p>
        </div>
      </div>
    </div>
  );
}
