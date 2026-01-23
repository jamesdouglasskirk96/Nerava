import { useState } from 'react';
import { AlertTriangle, XCircle, Power, RotateCcw, StopCircle } from 'lucide-react';

interface OverrideAction {
  id: string;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium';
  icon: typeof XCircle;
}

const overrideActions: OverrideAction[] = [
  {
    id: 'force-close-all',
    title: 'Force-Close All Sessions at Location',
    description: 'Immediately terminate all active charging sessions at a specific location',
    severity: 'critical',
    icon: XCircle,
  },
  {
    id: 'disable-primary',
    title: 'Disable Primary Experience',
    description: 'Turn off the primary charging experience for a location or merchant',
    severity: 'critical',
    icon: Power,
  },
  {
    id: 'reset-caps',
    title: 'Reset Caps',
    description: 'Reset daily or monthly activation caps for exclusives',
    severity: 'medium',
    icon: RotateCcw,
  },
  {
    id: 'emergency-pause',
    title: 'Emergency Pause',
    description: 'Pause all merchant operations system-wide immediately',
    severity: 'critical',
    icon: StopCircle,
  },
];

const recentOverrides = [
  {
    action: 'Force-Close All Sessions',
    target: 'Downtown Station #2',
    operator: 'ops@nerava.com',
    timestamp: '2026-01-05 13:56:12',
    reason: 'Equipment maintenance',
  },
  {
    action: 'Disable Primary Experience',
    target: 'Capitol Hill Station',
    operator: 'admin@nerava.com',
    timestamp: '2026-01-05 11:23:45',
    reason: 'Location mis-mapped',
  },
  {
    action: 'Reset Caps',
    target: 'Voltage Coffee Bar - Free Premium Coffee',
    operator: 'support@nerava.com',
    timestamp: '2026-01-05 09:15:22',
    reason: 'Merchant request - New Year promotion',
  },
];

export function Overrides() {
  const [selectedLocation, setSelectedLocation] = useState('');
  const [selectedMerchant, setSelectedMerchant] = useState('');
  const [selectedExclusive, setSelectedExclusive] = useState('');

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'border-red-300 bg-red-50';
      case 'high':
        return 'border-orange-300 bg-orange-50';
      case 'medium':
        return 'border-yellow-300 bg-yellow-50';
      default:
        return 'border-neutral-300 bg-neutral-50';
    }
  };

  const getSeverityTextColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-700';
      case 'high':
        return 'text-orange-700';
      case 'medium':
        return 'text-yellow-700';
      default:
        return 'text-neutral-700';
    }
  };

  const handleOverrideAction = (actionId: string) => {
    const action = overrideActions.find((a) => a.id === actionId);
    if (action && confirm(`Execute: ${action.title}?\n\nThis action cannot be undone.`)) {
      alert(`Override executed: ${action.title}`);
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 text-red-600" />
          <div>
            <h1 className="text-2xl text-neutral-900">Overrides</h1>
            <p className="text-sm text-neutral-600 mt-1">
              Critical manual controls - Use with extreme caution
            </p>
          </div>
        </div>
      </div>

      {/* Warning Banner */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
          <div>
            <h3 className="text-sm text-red-900">Critical Control Section</h3>
            <p className="text-sm text-red-700 mt-1">
              Actions performed here have immediate system-wide effects and cannot be undone. All
              actions are logged and require operator authentication.
            </p>
          </div>
        </div>
      </div>

      {/* Override Actions */}
      <div className="grid grid-cols-1 gap-4 mb-8">
        {overrideActions.map((action) => {
          const Icon = action.icon;
          return (
            <div
              key={action.id}
              className={`border rounded-lg p-6 ${getSeverityColor(action.severity)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1">
                  <div className={`p-3 rounded-lg bg-white border ${
                    action.severity === 'critical' ? 'border-red-300' : 'border-neutral-300'
                  }`}>
                    <Icon className={`w-6 h-6 ${getSeverityTextColor(action.severity)}`} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-lg text-neutral-900">{action.title}</h3>
                      <span
                        className={`px-2 py-0.5 rounded text-xs uppercase tracking-wider ${
                          action.severity === 'critical'
                            ? 'bg-red-200 text-red-800'
                            : action.severity === 'high'
                            ? 'bg-orange-200 text-orange-800'
                            : 'bg-yellow-200 text-yellow-800'
                        }`}
                      >
                        {action.severity}
                      </span>
                    </div>
                    <p className="text-sm text-neutral-700 mb-4">{action.description}</p>

                    {/* Action-specific controls */}
                    {action.id === 'force-close-all' && (
                      <div className="flex items-center gap-3">
                        <select
                          value={selectedLocation}
                          onChange={(e) => setSelectedLocation(e.target.value)}
                          className="px-3 py-2 border border-neutral-300 rounded-lg text-sm bg-white"
                        >
                          <option value="">Select location...</option>
                          <option value="L001">Downtown Station #1</option>
                          <option value="L002">Midtown Plaza</option>
                          <option value="L003">Capitol Hill Station</option>
                          <option value="L004">Downtown Station #4</option>
                        </select>
                        <button
                          onClick={() => handleOverrideAction(action.id)}
                          disabled={!selectedLocation}
                          className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 disabled:bg-neutral-300 disabled:cursor-not-allowed"
                        >
                          Execute Override
                        </button>
                      </div>
                    )}

                    {action.id === 'disable-primary' && (
                      <div className="flex items-center gap-3">
                        <select
                          value={selectedMerchant}
                          onChange={(e) => setSelectedMerchant(e.target.value)}
                          className="px-3 py-2 border border-neutral-300 rounded-lg text-sm bg-white"
                        >
                          <option value="">Select merchant...</option>
                          <option value="M001">Voltage Coffee Bar</option>
                          <option value="M002">Peak Hours Gym</option>
                          <option value="M003">Bolt Bistro</option>
                          <option value="M004">Current Cafe</option>
                        </select>
                        <button
                          onClick={() => handleOverrideAction(action.id)}
                          disabled={!selectedMerchant}
                          className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 disabled:bg-neutral-300 disabled:cursor-not-allowed"
                        >
                          Execute Override
                        </button>
                      </div>
                    )}

                    {action.id === 'reset-caps' && (
                      <div className="flex items-center gap-3">
                        <select
                          value={selectedExclusive}
                          onChange={(e) => setSelectedExclusive(e.target.value)}
                          className="px-3 py-2 border border-neutral-300 rounded-lg text-sm bg-white"
                        >
                          <option value="">Select exclusive...</option>
                          <option value="E001">Voltage Coffee Bar - Free Premium Coffee</option>
                          <option value="E002">Peak Hours Gym - Complimentary Day Pass</option>
                          <option value="E004">Current Cafe - Free Pastry with Drink</option>
                        </select>
                        <button
                          onClick={() => handleOverrideAction(action.id)}
                          disabled={!selectedExclusive}
                          className="px-4 py-2 bg-yellow-600 text-white text-sm rounded-lg hover:bg-yellow-700 disabled:bg-neutral-300 disabled:cursor-not-allowed"
                        >
                          Execute Override
                        </button>
                      </div>
                    )}

                    {action.id === 'emergency-pause' && (
                      <button
                        onClick={() => handleOverrideAction(action.id)}
                        className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700"
                      >
                        Execute Emergency Pause
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Overrides Log */}
      <div className="bg-white border border-neutral-200 rounded-lg">
        <div className="px-6 py-4 border-b border-neutral-200">
          <h2 className="text-lg text-neutral-900">Recent Override Actions</h2>
        </div>
        <div className="divide-y divide-neutral-100">
          {recentOverrides.map((override, index) => (
            <div key={index} className="px-6 py-4">
              <div className="flex items-start justify-between mb-2">
                <div className="text-sm text-neutral-900">{override.action}</div>
                <div className="text-xs text-neutral-500">{override.timestamp}</div>
              </div>
              <div className="text-sm text-neutral-600 mb-1">Target: {override.target}</div>
              <div className="flex items-center justify-between">
                <div className="text-xs text-neutral-500">Operator: {override.operator}</div>
                <div className="text-xs text-neutral-600">Reason: {override.reason}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
