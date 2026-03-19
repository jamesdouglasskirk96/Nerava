import { useState, useEffect } from 'react';
import { TrendingUp, Eye, CheckCircle, Activity, Users, Clock, Zap, Footprints, Loader2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { getMerchantAnalytics, getMerchantExclusives, fetchAPI, type MerchantAnalytics, type Exclusive } from '../services/api';
import { capture, MERCHANT_EVENTS } from '../analytics';

interface InsightsData {
  period: string
  ev_sessions_nearby: number
  unique_drivers: number
  avg_duration_minutes: number | null
  avg_kwh: number | null
  peak_hours: { hour: number; sessions: number }[]
  dwell_distribution: {
    under_15min: number
    '15_30min': number
    '30_60min': number
    over_60min: number
  } | null
  walk_traffic: {
    visited_area: number
    avg_walk_distance_m: number
  } | null
  has_pro_subscription?: boolean
  session_details?: Array<{
    id: string
    start: string | null
    end: string | null
    duration_minutes: number | null
    kwh: number | null
    charger_id: string | null
  }> | null
  customer_details?: Array<{
    driver_id_hash: string
    visit_count: number
  }> | null
}

const DWELL_COLORS = ['#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8'];

function StatCard({ icon: Icon, label, value }: { icon: typeof Activity; label: string; value: string | null }) {
  return (
    <div className="bg-white rounded-xl border border-neutral-200 p-5">
      <div className="flex items-center gap-2 text-neutral-500 text-sm mb-1">
        <Icon className="w-4 h-4" />
        <span>{label}</span>
      </div>
      <p className="text-2xl font-semibold text-neutral-900">
        {value ?? '—'}
      </p>
    </div>
  );
}

export function Overview() {
  const [analytics, setAnalytics] = useState<MerchantAnalytics | null>(null);
  const [exclusives, setExclusives] = useState<Exclusive[]>([]);
  const [insights, setInsights] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [insightsLoading, setInsightsLoading] = useState(true);
  const [insightsError, setInsightsError] = useState<string | null>(null);
  const [period, setPeriod] = useState<'week' | '30d'>('30d');
  const merchantId = localStorage.getItem('merchant_id') || '';

  useEffect(() => {
    loadData();
    capture(MERCHANT_EVENTS.ANALYTICS_VIEW);
  }, []);

  useEffect(() => {
    loadInsights();
  }, [period]);

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

  const loadInsights = () => {
    setInsightsLoading(true);
    setInsightsError(null);
    fetchAPI<InsightsData>(`/v1/merchants/me/insights?period=${period}`)
      .then(setInsights)
      .catch((e) => setInsightsError(e.message || 'Failed to load insights'))
      .finally(() => setInsightsLoading(false));
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

  const activeExclusive = exclusives.find(ex => ex.is_active) || null;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-neutral-600">Loading...</p>
      </div>
    );
  }

  const peakHoursData = insights?.peak_hours.map((h) => ({
    hour: `${h.hour % 12 || 12}${h.hour < 12 ? 'a' : 'p'}`,
    sessions: h.sessions,
  })) ?? [];

  const dwellData = insights?.dwell_distribution
    ? [
        { name: '<15 min', value: insights.dwell_distribution.under_15min },
        { name: '15-30 min', value: insights.dwell_distribution['15_30min'] },
        { name: '30-60 min', value: insights.dwell_distribution['30_60min'] },
        { name: '60+ min', value: insights.dwell_distribution.over_60min },
      ]
    : [];

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

      {/* Insights Section */}
      <div className="border-t border-neutral-200 pt-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-neutral-900">Nerava Insights</h2>
            <p className="text-sm text-neutral-500 mt-1">EV charging activity near your business</p>
          </div>
          <div className="flex gap-1 bg-neutral-100 rounded-lg p-1">
            <button
              onClick={() => setPeriod('week')}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                period === 'week' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-500'
              }`}
            >
              7 days
            </button>
            <button
              onClick={() => setPeriod('30d')}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                period === '30d' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-500'
              }`}
            >
              30 days
            </button>
          </div>
        </div>

        {insightsLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-6 h-6 animate-spin text-neutral-400" />
          </div>
        ) : insightsError ? (
          <div className="py-12 text-center">
            <p className="text-neutral-600">{insightsError}</p>
          </div>
        ) : insights ? (
          <>
            {/* Key stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <StatCard icon={Activity} label="EV Sessions" value={String(insights.ev_sessions_nearby)} />
              <StatCard icon={Users} label="Unique Drivers" value={String(insights.unique_drivers)} />
              <StatCard
                icon={Clock}
                label="Avg Duration"
                value={insights.avg_duration_minutes != null ? `${insights.avg_duration_minutes} min` : null}
              />
              <StatCard
                icon={Zap}
                label="Avg Energy"
                value={insights.avg_kwh != null ? `${insights.avg_kwh} kWh` : null}
              />
            </div>

            {/* Walk traffic callout */}
            {insights.walk_traffic && (
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 mb-8">
                <div className="flex items-center gap-2 mb-2">
                  <Footprints className="w-5 h-5 text-blue-600" />
                  <span className="font-medium text-blue-900">Walk Traffic</span>
                </div>
                <p className="text-sm text-blue-800">
                  <span className="font-semibold text-lg">{insights.walk_traffic.visited_area}%</span> of EV drivers walked within 200m of your business.
                  Average walk distance: <span className="font-medium">{insights.walk_traffic.avg_walk_distance_m}m</span>.
                </p>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Peak hours chart */}
              {peakHoursData.length > 0 && (
                <div className="bg-white rounded-xl border border-neutral-200 p-5">
                  <h3 className="text-sm font-medium text-neutral-700 mb-4">Sessions by Hour of Day</h3>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={peakHoursData}>
                      <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="sessions" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Dwell distribution */}
              {dwellData.length > 0 && (
                <div className="bg-white rounded-xl border border-neutral-200 p-5">
                  <h3 className="text-sm font-medium text-neutral-700 mb-4">Dwell Time Distribution</h3>
                  <div className="flex items-center gap-6">
                    <ResponsiveContainer width="50%" height={200}>
                      <PieChart>
                        <Pie
                          data={dwellData}
                          dataKey="value"
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={80}
                          paddingAngle={2}
                        >
                          {dwellData.map((_, i) => (
                            <Cell key={i} fill={DWELL_COLORS[i]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="space-y-2">
                      {dwellData.map((d, i) => (
                        <div key={d.name} className="flex items-center gap-2 text-sm">
                          <div
                            className="w-3 h-3 rounded-sm flex-shrink-0"
                            style={{ background: DWELL_COLORS[i] }}
                          />
                          <span className="text-neutral-600">{d.name}</span>
                          <span className="font-medium text-neutral-900 ml-auto">{d.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Pro-gated: Session Details */}
            <div className="mt-8">
              <h3 className="text-lg font-semibold text-neutral-900 mb-4">Session Details</h3>
              {insights.has_pro_subscription && insights.session_details && insights.session_details.length > 0 ? (
                <div className="bg-white rounded-xl border border-neutral-200 overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-neutral-50">
                      <tr>
                        <th className="text-left px-4 py-3 text-neutral-600 font-medium">Start</th>
                        <th className="text-left px-4 py-3 text-neutral-600 font-medium">Duration</th>
                        <th className="text-left px-4 py-3 text-neutral-600 font-medium">Energy</th>
                        <th className="text-left px-4 py-3 text-neutral-600 font-medium">Charger</th>
                      </tr>
                    </thead>
                    <tbody>
                      {insights.session_details.map((s) => (
                        <tr key={s.id} className="border-t border-neutral-100">
                          <td className="px-4 py-3 text-neutral-700">
                            {s.start ? new Date(s.start).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                          </td>
                          <td className="px-4 py-3 text-neutral-700">
                            {s.duration_minutes != null ? `${s.duration_minutes} min` : '—'}
                          </td>
                          <td className="px-4 py-3 text-neutral-700">
                            {s.kwh != null ? `${s.kwh} kWh` : '—'}
                          </td>
                          <td className="px-4 py-3 text-neutral-500 text-xs font-mono">
                            {s.charger_id ? s.charger_id.slice(0, 8) : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="relative">
                  <div className="bg-white rounded-xl border border-neutral-200 p-6 opacity-40 blur-[2px] pointer-events-none select-none">
                    <table className="w-full text-sm">
                      <thead className="bg-neutral-50"><tr><th className="text-left px-4 py-3">Start</th><th className="text-left px-4 py-3">Duration</th><th className="text-left px-4 py-3">Energy</th></tr></thead>
                      <tbody>
                        {[1,2,3].map((i) => (
                          <tr key={i} className="border-t border-neutral-100">
                            <td className="px-4 py-3">Mar {i}, 2:30 PM</td>
                            <td className="px-4 py-3">42 min</td>
                            <td className="px-4 py-3">28.5 kWh</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <a
                      href="/billing"
                      className="bg-neutral-900 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-neutral-800 transition-colors"
                    >
                      Upgrade to Pro to unlock
                    </a>
                  </div>
                </div>
              )}
            </div>

            {/* Pro-gated: Customer Visit Frequency */}
            <div className="mt-8">
              <h3 className="text-lg font-semibold text-neutral-900 mb-4">Customer Visit Frequency</h3>
              {insights.has_pro_subscription && insights.customer_details && insights.customer_details.length > 0 ? (
                <div className="bg-white rounded-xl border border-neutral-200 p-5">
                  <div className="space-y-2">
                    {insights.customer_details.map((c) => (
                      <div key={c.driver_id_hash} className="flex items-center justify-between py-2">
                        <span className="text-sm text-neutral-600 font-mono">Driver ...{c.driver_id_hash}</span>
                        <span className="text-sm font-medium text-neutral-900">{c.visit_count} visits</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="relative">
                  <div className="bg-white rounded-xl border border-neutral-200 p-5 opacity-40 blur-[2px] pointer-events-none select-none">
                    {[1,2,3].map((i) => (
                      <div key={i} className="flex items-center justify-between py-2">
                        <span className="text-sm text-neutral-600">Driver ...abc{i}def</span>
                        <span className="text-sm font-medium">{5 - i} visits</span>
                      </div>
                    ))}
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <a
                      href="/billing"
                      className="bg-neutral-900 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-neutral-800 transition-colors"
                    >
                      Upgrade to Pro to unlock
                    </a>
                  </div>
                </div>
              )}
            </div>

            {insights.unique_drivers < 5 && insights.ev_sessions_nearby > 0 && (
              <p className="text-xs text-neutral-400 mt-6 text-center">
                Some metrics are hidden until at least 5 unique drivers have charged nearby (privacy threshold).
              </p>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}
