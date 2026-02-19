import { useState, useEffect } from 'react';
import { TrendingUp, Eye, CheckCircle, Star } from 'lucide-react';
import { getMerchantAnalytics, getMerchantExclusives, type MerchantAnalytics, type Exclusive } from '../services/api';
import { capture, MERCHANT_EVENTS } from '../analytics';

export function Overview() {
  const [analytics, setAnalytics] = useState<MerchantAnalytics | null>(null);
  const [exclusives, setExclusives] = useState<Exclusive[]>([]);
  const [loading, setLoading] = useState(true);
  const merchantId = localStorage.getItem('merchant_id') || '';

  useEffect(() => {
    loadData();
    // Capture analytics view event
    capture(MERCHANT_EVENTS.ANALYTICS_VIEW);
  }, []);

  const loadData = async () => {
    if (!merchantId) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const [analyticsData, exclusivesData] = await Promise.all([
        getMerchantAnalytics(merchantId).catch(() => ({
          merchant_id: merchantId,
          activations: 0,
          completes: 0,
          unique_drivers: 0,
          completion_rate: 0,
        })),
        getMerchantExclusives(merchantId).catch(() => []),
      ]);
      setAnalytics(analyticsData);
      setExclusives(exclusivesData);
    } catch (err) {
      console.error('Failed to load data:', err);
      setAnalytics({
        merchant_id: merchantId,
        activations: 0,
        completes: 0,
        unique_drivers: 0,
        completion_rate: 0,
      });
      setExclusives([]);
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

  // Find active exclusive (first active exclusive)
  const activeExclusive = exclusives.find(ex => ex.is_active) || null;

  const primaryExperience: { status: 'available' | 'active' | 'taken'; explanation: string } = {
    status: 'available', // TODO: Fetch real status from backend
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
        {activeExclusive ? (
          <div className="bg-white p-6 rounded-lg border border-neutral-200">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-xl text-neutral-900 mb-1">{activeExclusive.title}</h3>
                {activeExclusive.description && (
                  <p className="text-sm text-neutral-600">{activeExclusive.description}</p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-neutral-600">Status:</span>
                <div className={`px-3 py-1 rounded-full text-sm ${
                  activeExclusive.is_active 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-neutral-100 text-neutral-600'
                }`}>
                  {activeExclusive.is_active ? 'Active' : 'Paused'}
                </div>
              </div>
            </div>
            
            {activeExclusive.daily_cap && activeExclusive.daily_cap > 0 ? (
              <>
                <div className="grid grid-cols-2 gap-6 mb-4">
                  <div>
                    <div className="text-sm text-neutral-600 mb-1">Activations Today</div>
                    <div className="text-2xl text-neutral-900">{todayStats.activationsToday}</div>
                  </div>
                  <div>
                    <div className="text-sm text-neutral-600 mb-1">Daily Cap</div>
                    <div className="text-2xl text-neutral-900">{activeExclusive.daily_cap}</div>
                  </div>
                </div>

                <div className="h-2 bg-neutral-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-neutral-900 rounded-full transition-all"
                    style={{ width: `${Math.min((todayStats.activationsToday / activeExclusive.daily_cap) * 100, 100)}%` }}
                  />
                </div>
              </>
            ) : (
              <div className="text-sm text-neutral-600">
                No daily cap set. Unlimited activations.
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white p-6 rounded-lg border border-neutral-200 text-center">
            <p className="text-neutral-600">No active exclusive</p>
            <p className="text-sm text-neutral-500 mt-2">Create an exclusive to start attracting charging customers</p>
          </div>
        )}
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
                <span className="inline-block px-4 py-2 bg-blue-50 text-blue-700 text-sm rounded-lg">
                  Coming Soon
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
