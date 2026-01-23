import { useState, useEffect } from 'react';
import { TrendingUp, Eye, CheckCircle, Star } from 'lucide-react';
import { getMerchantAnalytics, type MerchantAnalytics } from '../services/api';
import { capture, MERCHANT_EVENTS } from '../analytics';

export function Overview() {
  const [analytics, setAnalytics] = useState<MerchantAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const merchantId = localStorage.getItem('merchant_id') || 'current_merchant';

  useEffect(() => {
    loadAnalytics();
    // Capture analytics view event
    capture(MERCHANT_EVENTS.ANALYTICS_VIEW);
  }, []);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const data = await getMerchantAnalytics(merchantId);
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
      // Use mock data on error
      setAnalytics({
        merchant_id: merchantId,
        activations: 0,
        completes: 0,
        unique_drivers: 0,
        completion_rate: 0,
      });
    } finally {
      setLoading(false);
    }
  };

  const todayStats = analytics ? {
    activationsToday: analytics.activations,
    completedVisits: analytics.completes,
    conversionRate: Math.round(analytics.completion_rate),
  } : {
    activationsToday: 0,
    completedVisits: 0,
    conversionRate: 0,
  };

const activeExclusive = {
  name: 'Free Pastry with Coffee',
  timeWindow: '7:00 AM - 11:00 AM',
  status: 'on',
  activationsToday: 43,
  dailyCap: 100,
};

const primaryExperience = {
  status: 'available', // 'available' | 'active' | 'taken'
  explanation: 'Only one business per charging location can be the Primary Experience. This gives you maximum visibility to customers.',
};

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-neutral-600">Loading...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl text-neutral-900 mb-2">Overview</h1>
        <p className="text-neutral-600">
          Welcome back. Here's what's happening today.
        </p>
      </div>

      {/* Today Stats */}
      <div className="mb-8">
        <h2 className="text-lg text-neutral-900 mb-4">Today</h2>
        <div className="grid grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg border border-neutral-200">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-neutral-100 rounded-lg">
                <TrendingUp className="w-5 h-5 text-neutral-700" />
              </div>
              <span className="text-sm text-neutral-600">Activations Today</span>
            </div>
            <div className="text-4xl text-neutral-900">{todayStats.activationsToday}</div>
          </div>

          <div className="bg-white p-6 rounded-lg border border-neutral-200">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-neutral-100 rounded-lg">
                <CheckCircle className="w-5 h-5 text-neutral-700" />
              </div>
              <span className="text-sm text-neutral-600">Completed Visits</span>
            </div>
            <div className="text-4xl text-neutral-900">{todayStats.completedVisits}</div>
          </div>

          <div className="bg-white p-6 rounded-lg border border-neutral-200">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-neutral-100 rounded-lg">
                <Eye className="w-5 h-5 text-neutral-700" />
              </div>
              <span className="text-sm text-neutral-600">Conversion Rate</span>
            </div>
            <div className="text-4xl text-neutral-900">{todayStats.conversionRate}%</div>
          </div>
        </div>
      </div>

      {/* Active Exclusive */}
      <div className="mb-8">
        <h2 className="text-lg text-neutral-900 mb-4">Active Exclusive</h2>
        <div className="bg-white p-6 rounded-lg border border-neutral-200">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-xl text-neutral-900 mb-1">{activeExclusive.name}</h3>
              <p className="text-sm text-neutral-600">{activeExclusive.timeWindow}</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-neutral-600">Status:</span>
              <div className={`px-3 py-1 rounded-full text-sm ${
                activeExclusive.status === 'on' 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-neutral-100 text-neutral-600'
              }`}>
                {activeExclusive.status === 'on' ? 'On' : 'Off'}
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-6">
            <div>
              <div className="text-sm text-neutral-600 mb-1">Activations Today</div>
              <div className="text-2xl text-neutral-900">{activeExclusive.activationsToday}</div>
            </div>
            <div>
              <div className="text-sm text-neutral-600 mb-1">Daily Cap</div>
              <div className="text-2xl text-neutral-900">{activeExclusive.dailyCap}</div>
            </div>
          </div>

          <div className="mt-4 h-2 bg-neutral-100 rounded-full overflow-hidden">
            <div 
              className="h-full bg-neutral-900 rounded-full transition-all"
              style={{ width: `${(activeExclusive.activationsToday / activeExclusive.dailyCap) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Primary Experience */}
      <div>
        <h2 className="text-lg text-neutral-900 mb-4">Primary Experience</h2>
        <div className="bg-white p-6 rounded-lg border border-neutral-200">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-amber-50 rounded-lg">
              <Star className="w-6 h-6 text-amber-600" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="text-lg text-neutral-900">
                  {primaryExperience.status === 'available' && 'Available'}
                  {primaryExperience.status === 'active' && 'You are Primary'}
                  {primaryExperience.status === 'taken' && 'Taken by Another Business'}
                </h3>
                {primaryExperience.status === 'available' && (
                  <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                    Available
                  </span>
                )}
              </div>
              <p className="text-sm text-neutral-600 mb-4">
                {primaryExperience.explanation}
              </p>
              {primaryExperience.status === 'available' && (
                <button className="bg-neutral-900 text-white px-6 py-2 rounded-lg hover:bg-neutral-800 transition-colors">
                  Reserve Primary Experience
                </button>
              )}
              {primaryExperience.status === 'taken' && (
                <button className="border border-neutral-300 text-neutral-700 px-6 py-2 rounded-lg hover:bg-neutral-50 transition-colors">
                  Join Waitlist
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
