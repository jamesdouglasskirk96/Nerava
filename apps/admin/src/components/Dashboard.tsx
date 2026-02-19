import { useState, useEffect } from 'react';
import { Store, MapPin, Activity, AlertTriangle } from 'lucide-react';
import { fetchAPI, getActiveSessions, getAuditLogs, type AuditLog } from '../services/api';

interface OverviewResponse {
  total_drivers: number;
  total_merchants: number;
  total_driver_nova: number;
  total_merchant_nova: number;
  total_nova_outstanding: number;
  total_stripe_usd: number;
}

export function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [activeSessionsCount, setActiveSessionsCount] = useState(0);
  const [recentLogs, setRecentLogs] = useState<AuditLog[]>([]);

  useEffect(() => {
    loadData();
  }, []);

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
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(cents / 100);
  };

  const stats = overview
    ? [
        {
          label: 'Total Merchants',
          value: formatNumber(overview.total_merchants),
          icon: Store,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
        },
        {
          label: 'Total Drivers',
          value: formatNumber(overview.total_drivers),
          icon: Activity,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
        },
        {
          label: 'Live Exclusive Sessions',
          value: formatNumber(activeSessionsCount),
          icon: Activity,
          color: 'text-purple-600',
          bgColor: 'bg-purple-50',
        },
        {
          label: 'Total Stripe Revenue',
          value: formatCurrency(overview.total_stripe_usd),
          icon: AlertTriangle,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
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
      <div className="grid grid-cols-4 gap-6 mb-8">
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
    </div>
  );
}
