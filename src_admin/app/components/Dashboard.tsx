import { Store, MapPin, Activity, AlertTriangle } from 'lucide-react';

const stats = [
  {
    label: 'Active Merchants',
    value: '847',
    icon: Store,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
  },
  {
    label: 'Active Charging Locations',
    value: '1,243',
    icon: MapPin,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
  },
  {
    label: 'Live Exclusive Sessions',
    value: '312',
    icon: Activity,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
  },
  {
    label: 'Alerts',
    value: '7',
    icon: AlertTriangle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
  },
];

const recentAlerts = [
  {
    id: 1,
    type: 'Merchant Abuse Flagged',
    merchant: 'Voltage Coffee Bar',
    timestamp: '2026-01-05 14:23',
    severity: 'high',
  },
  {
    id: 2,
    type: 'Charger Data Unavailable',
    location: 'Downtown Station #4',
    timestamp: '2026-01-05 13:47',
    severity: 'medium',
  },
  {
    id: 3,
    type: 'Location Mis-mapped',
    location: 'Midtown Plaza',
    timestamp: '2026-01-05 12:15',
    severity: 'low',
  },
  {
    id: 4,
    type: 'Exclusive Misconfiguration',
    merchant: 'Peak Hours Gym',
    timestamp: '2026-01-05 11:02',
    severity: 'medium',
  },
];

const recentActivity = [
  { action: 'Merchant paused', user: 'admin@nerava.com', target: 'Bolt Bistro', timestamp: '14:45' },
  { action: 'Session extended', user: 'support@nerava.com', target: 'Session #8472', timestamp: '14:32' },
  { action: 'Exclusive disabled', user: 'admin@nerava.com', target: 'FastCharge Premium', timestamp: '14:18' },
  { action: 'Location reset', user: 'ops@nerava.com', target: 'Downtown Station #2', timestamp: '13:56' },
];

export function Dashboard() {
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
        {/* Alerts */}
        <div className="bg-white border border-neutral-200 rounded-lg">
          <div className="px-6 py-4 border-b border-neutral-200">
            <h2 className="text-lg text-neutral-900">Recent Alerts</h2>
          </div>
          <div className="divide-y divide-neutral-100">
            {recentAlerts.map((alert) => (
              <div key={alert.id} className="px-6 py-4 hover:bg-neutral-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`inline-block w-2 h-2 rounded-full ${
                          alert.severity === 'high'
                            ? 'bg-red-500'
                            : alert.severity === 'medium'
                            ? 'bg-yellow-500'
                            : 'bg-blue-500'
                        }`}
                      />
                      <span className="text-sm text-neutral-900">{alert.type}</span>
                    </div>
                    <div className="text-sm text-neutral-600">
                      {alert.merchant || alert.location}
                    </div>
                  </div>
                  <div className="text-xs text-neutral-500">{alert.timestamp}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white border border-neutral-200 rounded-lg">
          <div className="px-6 py-4 border-b border-neutral-200">
            <h2 className="text-lg text-neutral-900">Recent Activity</h2>
          </div>
          <div className="divide-y divide-neutral-100">
            {recentActivity.map((item, index) => (
              <div key={index} className="px-6 py-4 hover:bg-neutral-50">
                <div className="flex items-start justify-between mb-1">
                  <div className="text-sm text-neutral-900">{item.action}</div>
                  <div className="text-xs text-neutral-500">{item.timestamp}</div>
                </div>
                <div className="text-sm text-neutral-600">{item.target}</div>
                <div className="text-xs text-neutral-500 mt-1">by {item.user}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
