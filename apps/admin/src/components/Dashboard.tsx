import { useState, useEffect, useCallback } from 'react';
import { Store, MapPin, Activity, AlertTriangle, Zap, Car, CreditCard, Target, DollarSign, TrendingUp } from 'lucide-react';
import { fetchAPI, getActiveSessions, getAuditLogs, type AuditLog } from '../services/api';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Area,
  AreaChart,
} from 'recharts';

interface RevenueBreakdown {
  campaign_gross_cents: number;
  campaign_platform_fees_cents: number;
  campaign_driver_rewards_cents: number;
  merchant_subscriptions_cents: number;
  active_subscriptions: number;
  nova_sales_cents: number;
  merchant_fees_cents: number;
  arrival_billing_cents: number;
  total_realized_cents: number;
  total_driver_payouts_cents: number;
}

interface OverviewResponse {
  total_drivers: number;
  total_merchants: number;
  total_chargers: number;
  total_charging_sessions: number;
  active_campaigns: number;
  total_driver_nova: number;
  total_merchant_nova: number;
  total_nova_outstanding: number;
  total_stripe_usd: number;
  total_tesla_connections: number;
  total_stripe_express_onboarded: number;
  revenue?: RevenueBreakdown;
}

// ---------------------------------------------------------------------------
// Analytics types
// ---------------------------------------------------------------------------

interface DailySessionCount {
  date: string;
  count: number;
  total_kwh: number;
}

interface DailyDriverCount {
  date: string;
  active_drivers: number;
  new_drivers: number;
}

interface DailyRevenue {
  date: string;
  grants_cents: number;
  payouts_cents: number;
}

type PeriodDays = 7 | 30 | 90;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Format "2026-03-15" as "Mar 15" */
function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/** Format cents as "$X.XX" */
function centsToUSD(cents: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(cents / 100);
}

// ---------------------------------------------------------------------------
// Chart card wrapper
// ---------------------------------------------------------------------------

function ChartCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white border border-neutral-200 rounded-lg">
      <div className="px-6 py-4 border-b border-neutral-200">
        <h2 className="text-lg text-neutral-900">{title}</h2>
      </div>
      <div className="p-6" style={{ height: 320 }}>
        {children}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [activeSessionsCount, setActiveSessionsCount] = useState(0);
  const [recentLogs, setRecentLogs] = useState<AuditLog[]>([]);

  // Analytics state
  const [period, setPeriod] = useState<PeriodDays>(30);
  const [sessionsSeries, setSessionsSeries] = useState<DailySessionCount[]>([]);
  const [driversSeries, setDriversSeries] = useState<DailyDriverCount[]>([]);
  const [revenueSeries, setRevenueSeries] = useState<DailyRevenue[]>([]);
  const [chartsLoading, setChartsLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  // Fetch chart data whenever period changes
  const loadCharts = useCallback(async (days: PeriodDays) => {
    setChartsLoading(true);
    try {
      const [sessions, drivers, revenue] = await Promise.all([
        fetchAPI<DailySessionCount[]>(`/v1/admin/analytics/sessions?days=${days}`),
        fetchAPI<DailyDriverCount[]>(`/v1/admin/analytics/drivers?days=${days}`),
        fetchAPI<DailyRevenue[]>(`/v1/admin/analytics/revenue?days=${days}`),
      ]);
      setSessionsSeries(sessions);
      setDriversSeries(drivers);
      setRevenueSeries(revenue);
    } catch (err) {
      console.error('Failed to load analytics charts:', err);
    } finally {
      setChartsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCharts(period);
  }, [period, loadCharts]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load overview stats
      const overviewData = await fetchAPI<OverviewResponse>('/v1/admin/overview');
      setOverview(overviewData);

      // Load active sessions count
      try {
        const sessionsData = await getActiveSessions();
        setActiveSessionsCount(sessionsData.total_active);
      } catch (err) {
        console.error('Failed to load active sessions:', err);
        setActiveSessionsCount(0);
      }

      // Load recent activity logs
      try {
        const logsData = await getAuditLogs(5, 0);
        setRecentLogs(logsData.logs);
      } catch (err) {
        console.error('Failed to load recent logs:', err);
        setRecentLogs([]);
      }
    } catch (err: any) {
      console.error('Failed to load dashboard data:', err);
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const formatCurrency = (cents: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(cents / 100);
  };

  const stats = overview
    ? [
        {
          label: 'Total Drivers',
          value: formatNumber(overview.total_drivers),
          icon: Activity,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
        },
        {
          label: 'Connected Teslas',
          value: formatNumber(overview.total_tesla_connections),
          icon: Car,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
        },
        {
          label: 'Total Chargers',
          value: formatNumber(overview.total_chargers),
          icon: Zap,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
        },
        {
          label: 'Charging Sessions',
          value: formatNumber(overview.total_charging_sessions),
          icon: Zap,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
        },
        {
          label: 'Merchants',
          value: formatNumber(overview.total_merchants),
          icon: Store,
          color: 'text-purple-600',
          bgColor: 'bg-purple-50',
        },
        {
          label: 'Active Campaigns',
          value: formatNumber(overview.active_campaigns),
          icon: Target,
          color: 'text-orange-600',
          bgColor: 'bg-orange-50',
        },
        {
          label: 'Stripe Express',
          value: formatNumber(overview.total_stripe_express_onboarded),
          icon: CreditCard,
          color: 'text-indigo-600',
          bgColor: 'bg-indigo-50',
        },
        {
          label: 'Total Revenue',
          value: formatCurrency(overview.revenue?.total_realized_cents ?? overview.total_stripe_usd),
          icon: DollarSign,
          color: 'text-emerald-600',
          bgColor: 'bg-emerald-50',
        },
      ]
    : [];

  if (loading) {
    return (
      <div className="p-8">
        <div className="mb-8">
          <h1 className="text-2xl text-neutral-900">Dashboard</h1>
          <p className="text-sm text-neutral-600 mt-1">System overview and monitoring</p>
        </div>
        <div className="text-center py-12">
          <div className="text-neutral-600">Loading dashboard data...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="mb-8">
          <h1 className="text-2xl text-neutral-900">Dashboard</h1>
          <p className="text-sm text-neutral-600 mt-1">System overview and monitoring</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-red-800 mb-2">Error loading dashboard</div>
          <div className="text-sm text-red-600 mb-4">{error}</div>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-red-600 text-white rounded-md text-sm hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl text-neutral-900">Dashboard</h1>
        <p className="text-sm text-neutral-600 mt-1">System overview and monitoring</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="bg-white border border-neutral-200 rounded-lg p-6">
              <div className="flex items-center justify-between mb-3">
                <div className={`p-2.5 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`w-5 h-5 ${stat.color}`} />
                </div>
              </div>
              <div className="text-3xl text-neutral-900 mb-1">{stat.value}</div>
              <div className="text-sm text-neutral-600">{stat.label}</div>
            </div>
          );
        })}
      </div>

      {/* Revenue Breakdown */}
      {overview?.revenue && (
        <div className="bg-white border border-neutral-200 rounded-lg mb-8">
          <div className="px-6 py-4 border-b border-neutral-200">
            <h2 className="text-lg text-neutral-900">Revenue</h2>
          </div>
          <div className="p-6">
            {/* Gross inflows */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
              {[
                { label: 'Campaign Funding', cents: overview.revenue.campaign_gross_cents, desc: 'Total collected from sponsors' },
                { label: 'Merchant Subscriptions', cents: overview.revenue.merchant_subscriptions_cents, desc: `${overview.revenue.active_subscriptions} active` },
                { label: 'Nova Sales', cents: overview.revenue.nova_sales_cents, desc: 'Merchant purchases' },
                { label: 'Merchant Fees', cents: overview.revenue.merchant_fees_cents, desc: 'Redemption commission' },
                { label: 'Arrival Billing', cents: overview.revenue.arrival_billing_cents, desc: 'EV arrival fees' },
              ].map((item) => (
                <div key={item.label}>
                  <div className="text-sm text-neutral-500">{item.label}</div>
                  <div className="text-xl font-semibold text-neutral-900 mt-1">{formatCurrency(item.cents)}</div>
                  <div className="text-xs text-neutral-400 mt-0.5">{item.desc}</div>
                </div>
              ))}
            </div>
            {/* Totals */}
            <div className="mt-6 pt-4 border-t border-neutral-100 grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <div className="text-sm text-neutral-500">Total Collected</div>
                <div className="text-2xl font-semibold text-emerald-600 mt-1">{formatCurrency(overview.revenue.total_realized_cents)}</div>
              </div>
              <div>
                <div className="text-sm text-neutral-500">Platform Fees (20%)</div>
                <div className="text-xl font-semibold text-neutral-900 mt-1">{formatCurrency(overview.revenue.campaign_platform_fees_cents)}</div>
              </div>
              <div>
                <div className="text-sm text-neutral-500">Paid to Drivers</div>
                <div className="text-xl font-semibold text-neutral-900 mt-1">{formatCurrency(overview.revenue.campaign_driver_rewards_cents)}</div>
              </div>
              <div>
                <div className="text-sm text-neutral-500">Driver Withdrawals</div>
                <div className="text-xl font-semibold text-neutral-900 mt-1">{formatCurrency(overview.revenue.total_driver_payouts_cents)}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-6">
        {/* Alerts - Coming Soon */}
        <div className="bg-white border border-neutral-200 rounded-lg">
          <div className="px-6 py-4 border-b border-neutral-200">
            <h2 className="text-lg text-neutral-900">Recent Alerts</h2>
          </div>
          <div className="px-6 py-12 text-center text-neutral-500">
            <p>Alert monitoring coming soon</p>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white border border-neutral-200 rounded-lg">
          <div className="px-6 py-4 border-b border-neutral-200">
            <h2 className="text-lg text-neutral-900">Recent Activity</h2>
          </div>
          <div className="divide-y divide-neutral-100">
            {recentLogs.length > 0 ? (
              recentLogs.map((log) => (
                <div key={log.id} className="px-6 py-4 hover:bg-neutral-50">
                  <div className="flex items-start justify-between mb-1">
                    <div className="text-sm text-neutral-900">{log.action_type}</div>
                    <div className="text-xs text-neutral-500">
                      {log.created_at
                        ? new Date(log.created_at).toLocaleTimeString('en-US', {
                            hour: '2-digit',
                            minute: '2-digit',
                          })
                        : ''}
                    </div>
                  </div>
                  <div className="text-sm text-neutral-600">
                    {log.target_type}: {log.target_id}
                  </div>
                  {log.operator_email && (
                    <div className="text-xs text-neutral-500 mt-1">by {log.operator_email}</div>
                  )}
                </div>
              ))
            ) : (
              <div className="px-6 py-12 text-center text-neutral-500">
                <p>No recent activity</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Analytics Charts                                                    */}
      {/* ------------------------------------------------------------------ */}

      {/* Period selector */}
      <div className="flex items-center justify-between mt-10 mb-4">
        <h2 className="text-xl text-neutral-900">Analytics</h2>
        <div className="flex gap-2">
          {([7, 30, 90] as PeriodDays[]).map((d) => (
            <button
              key={d}
              onClick={() => setPeriod(d)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                period === d
                  ? 'bg-neutral-900 text-white'
                  : 'bg-white border border-neutral-200 text-neutral-600 hover:bg-neutral-50'
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {chartsLoading ? (
        <div className="text-center py-12 text-neutral-500">Loading charts...</div>
      ) : (
        <div className="grid grid-cols-2 gap-6">
          {/* 1. Sessions Over Time */}
          <ChartCard title="Sessions Over Time">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={sessionsSeries}>
                <defs>
                  <linearGradient id="sessionFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatDateLabel}
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  labelFormatter={formatDateLabel}
                  formatter={(value: number, name: string) => {
                    if (name === 'count') return [value, 'Sessions'];
                    return [value, name];
                  }}
                  contentStyle={{ borderRadius: 8, border: '1px solid #e5e7eb' }}
                />
                <Legend formatter={(value) => (value === 'count' ? 'Sessions' : value)} />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fill="url(#sessionFill)"
                  dot={false}
                  activeDot={{ r: 4, fill: '#3b82f6' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* 2. Active Drivers Over Time */}
          <ChartCard title="Active Drivers Over Time">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={driversSeries}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatDateLabel}
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  labelFormatter={formatDateLabel}
                  formatter={(value: number, name: string) => {
                    if (name === 'active_drivers') return [value, 'Active Drivers'];
                    if (name === 'new_drivers') return [value, 'New Drivers'];
                    return [value, name];
                  }}
                  contentStyle={{ borderRadius: 8, border: '1px solid #e5e7eb' }}
                />
                <Legend
                  formatter={(value) => {
                    if (value === 'active_drivers') return 'Active Drivers';
                    if (value === 'new_drivers') return 'New Drivers';
                    return value;
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="active_drivers"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: '#3b82f6' }}
                />
                <Line
                  type="monotone"
                  dataKey="new_drivers"
                  stroke="#22c55e"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: '#22c55e' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* 3. Revenue Over Time */}
          <ChartCard title="Revenue Over Time">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={revenueSeries}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatDateLabel}
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v: number) => centsToUSD(v)}
                />
                <Tooltip
                  labelFormatter={formatDateLabel}
                  formatter={(value: number, name: string) => {
                    if (name === 'grants_cents') return [centsToUSD(value), 'Grants'];
                    if (name === 'payouts_cents') return [centsToUSD(value), 'Payouts'];
                    return [centsToUSD(value), name];
                  }}
                  contentStyle={{ borderRadius: 8, border: '1px solid #e5e7eb' }}
                />
                <Legend
                  formatter={(value) => {
                    if (value === 'grants_cents') return 'Grants';
                    if (value === 'payouts_cents') return 'Payouts';
                    return value;
                  }}
                />
                <Bar dataKey="grants_cents" stackId="revenue" fill="#22c55e" radius={[2, 2, 0, 0]} />
                <Bar dataKey="payouts_cents" stackId="revenue" fill="#ef4444" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* 4. Energy Delivered (bonus — uses session data) */}
          <ChartCard title="Energy Delivered (kWh)">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={sessionsSeries}>
                <defs>
                  <linearGradient id="kwhFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatDateLabel}
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v: number) => `${v} kWh`}
                />
                <Tooltip
                  labelFormatter={formatDateLabel}
                  formatter={(value: number) => [`${value.toFixed(1)} kWh`, 'Energy']}
                  contentStyle={{ borderRadius: 8, border: '1px solid #e5e7eb' }}
                />
                <Legend formatter={() => 'Total kWh'} />
                <Area
                  type="monotone"
                  dataKey="total_kwh"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  fill="url(#kwhFill)"
                  dot={false}
                  activeDot={{ r: 4, fill: '#f59e0b' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      )}
    </div>
  );
}
