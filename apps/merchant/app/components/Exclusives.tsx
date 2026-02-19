import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Users, AlertCircle } from 'lucide-react';
import { 
  getMerchantExclusives, 
  toggleExclusive,
  getMerchantAnalytics,
  type Exclusive,
  type MerchantAnalytics,
  ApiError 
} from '../services/api';
import { capture, MERCHANT_EVENTS } from '../analytics';

export function Exclusives() {
  const navigate = useNavigate();
  const [exclusives, setExclusives] = useState<Exclusive[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toggleError, setToggleError] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<MerchantAnalytics | null>(null);
  
  // Get merchant ID from localStorage or context (for MVP, use a placeholder)
  const merchantId = localStorage.getItem('merchant_id') || '';

  useEffect(() => {
    loadExclusives();
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    if (!merchantId) return;
    try {
      const data = await getMerchantAnalytics(merchantId);
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
      setAnalytics({
        merchant_id: merchantId,
        activations: 0,
        completes: 0,
        unique_drivers: 0,
        completion_rate: 0,
      });
    }
  };

  const loadExclusives = async () => {
    if (!merchantId) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const data = await getMerchantExclusives(merchantId);
      setExclusives(data);
      setError(null);
    } catch (err) {
      console.error('Failed to load exclusives:', err);
      setError(err instanceof ApiError ? err.message : 'Failed to load exclusives');
      // Fallback to empty array
      setExclusives([]);
    } finally {
      setLoading(false);
    }
  };

  const toggleExclusiveStatus = async (id: string, currentStatus: boolean) => {
    const newStatus = !currentStatus
    setToggleError(null);
    try {
      await toggleExclusive(merchantId, id, newStatus);
      
      // Capture toggle event
      capture(newStatus ? MERCHANT_EVENTS.EXCLUSIVE_TOGGLE_ON : MERCHANT_EVENTS.EXCLUSIVE_TOGGLE_OFF, {
        exclusive_id: id,
        merchant_id: merchantId,
      })
      
      // Reload exclusives
      await loadExclusives();
    } catch (err) {
      console.error('Failed to toggle exclusive:', err);
      setToggleError(err instanceof ApiError ? err.message : 'Failed to update exclusive');
    }
  };

  const getStatusColor = (exclusive: Exclusive) => {
    if (!exclusive.is_active) {
      return 'bg-neutral-100 text-neutral-600';
    }
    if (analytics && exclusive.daily_cap && analytics.activations >= exclusive.daily_cap) {
      return 'bg-amber-100 text-amber-700';
    }
    return 'bg-green-100 text-green-700';
  };

  const getStatusText = (exclusive: Exclusive) => {
    if (!exclusive.is_active) return 'Paused';
    if (analytics && exclusive.daily_cap && analytics.activations >= exclusive.daily_cap) return 'Cap Reached';
    return 'Active';
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl text-neutral-900 mb-2">Exclusives</h1>
          <p className="text-neutral-600">
            Manage your exclusive offers for charging customers
          </p>
        </div>
        <button
          onClick={() => navigate('/exclusives/new')}
          className="bg-neutral-900 text-white px-6 py-3 rounded-lg hover:bg-neutral-800 transition-colors flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Create Exclusive
        </button>
      </div>

      {toggleError && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center justify-between">
          <span>{toggleError}</span>
          <button
            onClick={() => setToggleError(null)}
            className="text-red-700 hover:text-red-900"
          >
            ×
          </button>
        </div>
      )}

      {loading ? (
        <div className="bg-white rounded-lg border border-neutral-200 p-12 text-center">
          <p className="text-neutral-600">Loading exclusives...</p>
        </div>
      ) : error ? (
        <div className="bg-white rounded-lg border border-neutral-200 p-12 text-center">
          <p className="text-red-600">{error}</p>
          <button
            onClick={loadExclusives}
            className="mt-4 bg-neutral-900 text-white px-6 py-3 rounded-lg hover:bg-neutral-800 transition-colors"
          >
            Retry
          </button>
        </div>
      ) : exclusives.length === 0 ? (
        <div className="bg-white rounded-lg border border-neutral-200 p-12 text-center">
          <div className="max-w-md mx-auto">
            <div className="p-4 bg-neutral-100 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-neutral-400" />
            </div>
            <h2 className="text-xl text-neutral-900 mb-2">No Exclusives Yet</h2>
            <p className="text-neutral-600 mb-6">
              Create your first exclusive to start attracting charging customers
            </p>
            <button
              onClick={() => navigate('/exclusives/new')}
              className="bg-neutral-900 text-white px-6 py-3 rounded-lg hover:bg-neutral-800 transition-colors inline-flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Create Exclusive
            </button>
          </div>
        </div>
      ) : (
        <div className="grid gap-6">
          {exclusives.map((exclusive) => (
            <div key={exclusive.id} className="bg-white p-6 rounded-lg border border-neutral-200">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl text-neutral-900">{exclusive.title}</h3>
                    <span className={`px-3 py-1 rounded-full text-sm ${getStatusColor(exclusive)}`}>
                      {getStatusText(exclusive)}
                    </span>
                  </div>
                  <p className="text-sm text-neutral-600 mb-3">{exclusive.description}</p>

                  <div className="flex items-center gap-6 text-sm">
                    <div className="flex items-center gap-2 text-neutral-600">
                      <span className="px-2 py-1 rounded bg-green-100 text-green-700">
                        {exclusive.eligibility || 'All Customers'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-neutral-600">
                      <Users className="w-4 h-4" />
                      Daily cap: {exclusive.daily_cap || 'Unlimited'}
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => toggleExclusiveStatus(exclusive.id, exclusive.is_active)}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    exclusive.is_active
                      ? 'bg-neutral-900 text-white hover:bg-neutral-800'
                      : 'border border-neutral-300 text-neutral-700 hover:bg-neutral-50'
                  }`}
                >
                  {exclusive.is_active ? 'Turn Off' : 'Turn On'}
                </button>
              </div>

              {/* Progress bar - show only if daily_cap is set and we have activation data */}
              {exclusive.daily_cap && exclusive.daily_cap > 0 && analytics && (
                <div className="mt-4">
                  <div className="flex items-center justify-between text-xs text-neutral-600 mb-1">
                    <span>Daily Cap</span>
                    <span>{analytics.activations} / {exclusive.daily_cap} activations</span>
                  </div>
                  <div className="h-2 bg-neutral-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all bg-neutral-900"
                      style={{ width: `${Math.min((analytics.activations / exclusive.daily_cap) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
