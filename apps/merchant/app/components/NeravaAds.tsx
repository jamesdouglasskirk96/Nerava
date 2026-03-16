import { useState, useEffect } from 'react';
import { Megaphone, CheckCircle, BarChart3, Loader2 } from 'lucide-react';
import { createSubscription, getSubscription, getAdStats } from '../services/api';

type PricingTab = 'flat' | 'cpm';

export function NeravaAds() {
  const [tab, setTab] = useState<PricingTab>('flat');
  const [loading, setLoading] = useState(false);
  const [subscription, setSubscription] = useState<any>(null);
  const [adStats, setAdStats] = useState<any>(null);
  const [loadingSub, setLoadingSub] = useState(true);

  useEffect(() => {
    Promise.all([
      getSubscription().catch(() => ({ subscription: null })),
      getAdStats('30d').catch(() => null),
    ]).then(([subData, stats]) => {
      const sub = subData?.subscription;
      if (sub && (sub.plan === 'ads_flat' || sub.plan === 'ads_cpm')) {
        setSubscription(sub);
      }
      setAdStats(stats);
      setLoadingSub(false);
    });
  }, []);

  const handleSubscribe = async (plan: 'ads_flat' | 'ads_cpm') => {
    setLoading(true);
    try {
      const placeId = localStorage.getItem('place_id') || '';
      const { checkout_url } = await createSubscription(placeId, plan);
      window.location.href = checkout_url;
    } catch (err: any) {
      alert(err.message || 'Failed to start checkout');
    } finally {
      setLoading(false);
    }
  };

  if (loadingSub) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-6 h-6 animate-spin text-neutral-400" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl text-neutral-900 mb-2">Nerava Ads</h1>
        <p className="text-neutral-600">
          Boost your visibility to EV drivers at nearby charging stations
        </p>
      </div>

      {/* Explanation Card */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-8 rounded-xl border border-blue-200 mb-8">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-white rounded-lg shadow-sm">
            <Megaphone className="w-8 h-8 text-blue-600" />
          </div>
          <div className="flex-1">
            <h2 className="text-2xl text-neutral-900 mb-3">What are Nerava Ads?</h2>
            <ul className="space-y-2 text-neutral-700">
              <li className="flex items-start gap-2">
                <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <span><strong>Featured placement</strong> in the driver's charging screen carousel</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <span><strong>Search boost</strong> — appear higher in nearby merchant results</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <span><strong>Impression tracking</strong> — see exactly how many drivers see your listing</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Active subscription state */}
      {subscription && (
        <div className="bg-white p-6 rounded-xl border border-neutral-200 mb-8">
          <div className="flex items-center gap-2 mb-4">
            <div className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
              Active
            </div>
            <span className="text-neutral-600 text-sm capitalize">
              {subscription.plan === 'ads_flat' ? 'Flat Rate — $99/mo' : 'CPM — $5 per 1K views'}
            </span>
          </div>

          {subscription.current_period_end && (
            <p className="text-sm text-neutral-500 mb-4">
              Current period ends: {new Date(subscription.current_period_end).toLocaleDateString()}
            </p>
          )}

          {/* Impression stats */}
          {adStats && (
            <div className="grid grid-cols-3 gap-4 mt-4">
              <div className="p-4 bg-neutral-50 rounded-lg">
                <div className="text-2xl font-semibold text-neutral-900">{adStats.total?.toLocaleString() ?? 0}</div>
                <div className="text-sm text-neutral-500">Total Impressions</div>
              </div>
              <div className="p-4 bg-neutral-50 rounded-lg">
                <div className="text-2xl font-semibold text-neutral-900">
                  {adStats.by_type?.carousel ?? 0}
                </div>
                <div className="text-sm text-neutral-500">Carousel Views</div>
              </div>
              <div className="p-4 bg-neutral-50 rounded-lg">
                <div className="text-2xl font-semibold text-neutral-900">
                  {adStats.by_type?.featured ?? 0}
                </div>
                <div className="text-sm text-neutral-500">Featured Views</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Pricing — only show if no active ads subscription */}
      {!subscription && (
        <div className="bg-white p-8 rounded-xl border border-neutral-200">
          {/* Tab Switcher */}
          <div className="flex gap-1 bg-neutral-100 rounded-lg p-1 mb-8 max-w-xs">
            <button
              onClick={() => setTab('flat')}
              className={`flex-1 px-4 py-2 text-sm rounded-md transition-colors ${
                tab === 'flat' ? 'bg-white shadow-sm text-neutral-900 font-medium' : 'text-neutral-500'
              }`}
            >
              Flat Rate
            </button>
            <button
              onClick={() => setTab('cpm')}
              className={`flex-1 px-4 py-2 text-sm rounded-md transition-colors ${
                tab === 'cpm' ? 'bg-white shadow-sm text-neutral-900 font-medium' : 'text-neutral-500'
              }`}
            >
              Pay Per View
            </button>
          </div>

          {tab === 'flat' && (
            <div className="text-center max-w-lg mx-auto">
              <div className="mb-6">
                <span className="text-4xl font-bold text-neutral-900">$99</span>
                <span className="text-neutral-500 text-lg">/month</span>
              </div>
              <p className="text-neutral-600 mb-8">
                Unlimited impressions at a predictable monthly price. Best for high-traffic locations.
              </p>
              <button
                onClick={() => handleSubscribe('ads_flat')}
                disabled={loading}
                className="bg-neutral-900 text-white px-8 py-3 rounded-lg hover:bg-neutral-800 transition-colors disabled:opacity-50"
              >
                {loading ? 'Redirecting...' : 'Subscribe — $99/mo'}
              </button>
            </div>
          )}

          {tab === 'cpm' && (
            <div className="text-center max-w-lg mx-auto">
              <div className="mb-6">
                <span className="text-4xl font-bold text-neutral-900">$5</span>
                <span className="text-neutral-500 text-lg"> per 1,000 views</span>
              </div>
              <p className="text-neutral-600 mb-8">
                Only pay for actual driver impressions. Best for lower-traffic or seasonal locations.
              </p>
              <div className="bg-blue-50 p-4 rounded-lg text-sm text-blue-800 mb-6">
                <BarChart3 className="w-4 h-4 inline mr-1" />
                CPM billing is metered monthly. You'll receive an invoice based on actual impression count.
              </div>
              <button
                onClick={() => handleSubscribe('ads_cpm')}
                disabled={loading}
                className="bg-neutral-900 text-white px-8 py-3 rounded-lg hover:bg-neutral-800 transition-colors disabled:opacity-50"
              >
                {loading ? 'Redirecting...' : 'Get Started — CPM'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
