import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Info } from 'lucide-react';
import { createExclusive, ApiError } from '../services/api';
import { capture, MERCHANT_EVENTS } from '../analytics';

export function CreateExclusive() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const merchantId = localStorage.getItem('merchant_id') || '';
  
  // Capture exclusive create open event
  useEffect(() => {
    capture(MERCHANT_EVENTS.EXCLUSIVE_CREATE_OPEN)
  }, [])
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    dailyCap: '100',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!merchantId) {
      setError('No merchant ID found. Please complete the claim flow.');
      return;
    }
    setLoading(true);
    setError(null);
    
    try {
      const result = await createExclusive(merchantId, {
        title: formData.name,
        description: formData.description,
        daily_cap: parseInt(formData.dailyCap) || undefined,
        eligibility: 'charging_only', // Default for MVP
      });
      
      capture(MERCHANT_EVENTS.EXCLUSIVE_CREATE_SUBMIT_SUCCESS, {
        exclusive_id: result.id,
        merchant_id: merchantId,
      })
      
      navigate('/exclusives');
    } catch (err) {
      console.error('Failed to create exclusive:', err);
      const errorMessage = err instanceof ApiError ? err.message : 'Failed to create exclusive'
      
      capture(MERCHANT_EVENTS.EXCLUSIVE_CREATE_SUBMIT_FAIL, {
        error: errorMessage,
        merchant_id: merchantId,
      })
      
      setError(errorMessage);
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div>
      <button
        onClick={() => navigate('/exclusives')}
        className="flex items-center gap-2 text-neutral-600 hover:text-neutral-900 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Exclusives
      </button>

      <div className="mb-8">
        <h1 className="text-3xl text-neutral-900 mb-2">Create Exclusive</h1>
        <p className="text-neutral-600">
          Design a special offer for customers charging at your location
        </p>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}
      
      <div className="max-w-3xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Name */}
          <div className="bg-white p-6 rounded-lg border border-neutral-200">
            <label className="block mb-2">
              <span className="text-sm text-neutral-900">Exclusive Name</span>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                placeholder="e.g., Free Pastry with Coffee"
                className="mt-1 w-full px-4 py-3 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                required
              />
            </label>
          </div>

          {/* Description */}
          <div className="bg-white p-6 rounded-lg border border-neutral-200">
            <label className="block mb-2">
              <span className="text-sm text-neutral-900">What Customers Receive</span>
              <textarea
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                placeholder="Describe what the customer gets..."
                rows={3}
                className="mt-1 w-full px-4 py-3 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent resize-none"
                required
              />
            </label>
          </div>

          {/* Daily Cap */}
          <div className="bg-white p-6 rounded-lg border border-neutral-200">
            <label className="block">
              <span className="text-sm text-neutral-900">Daily Activation Cap</span>
              <input
                type="number"
                value={formData.dailyCap}
                onChange={(e) => handleChange('dailyCap', e.target.value)}
                min="1"
                className="mt-1 w-full px-4 py-3 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                required
              />
              <div className="mt-2 flex items-start gap-2 text-xs text-neutral-600">
                <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />
                <span>Maximum number of customers who can activate this exclusive per day</span>
              </div>
            </label>
          </div>

          {/* Note: Type, time window, and staff instructions are not yet supported by backend API */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-start gap-2">
              <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-900">
                <div className="font-semibold mb-1">Coming Soon</div>
                <div className="text-xs text-blue-700">
                  Exclusive type, time windows, and staff instructions will be available in a future update.
                </div>
              </div>
            </div>
          </div>

          {/* Safety Note */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-start gap-2">
              <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <div className="text-sm text-blue-900 mb-1">You're in Control</div>
                <div className="text-xs text-blue-700">
                  You can pause, edit, or delete this exclusive at any time. Daily caps reset automatically at midnight.
                </div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => navigate('/exclusives')}
              className="flex-1 border border-neutral-300 text-neutral-700 py-3 px-6 rounded-lg hover:bg-neutral-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-neutral-900 text-white py-3 px-6 rounded-lg hover:bg-neutral-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Publishing...' : 'Publish Exclusive'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
