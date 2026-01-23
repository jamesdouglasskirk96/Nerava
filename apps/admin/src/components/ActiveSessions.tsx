import { useState, useEffect } from 'react';
import { Clock, RefreshCw } from 'lucide-react';
import { getActiveSessions, type ActiveSession } from '../services/api';

export function ActiveSessions() {
  const [sessions, setSessions] = useState<ActiveSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  useEffect(() => {
    loadSessions();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadSessions, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadSessions = async () => {
    try {
      const data = await getActiveSessions();
      setSessions(data.sessions);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Failed to load active sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'text-green-700 bg-green-50 border-green-200';
      case 'COMPLETED': return 'text-blue-700 bg-blue-50 border-blue-200';
      case 'EXPIRED': return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      default: return 'text-neutral-700 bg-neutral-50 border-neutral-200';
    }
  };

  if (loading) {
    return <div className="p-8"><p>Loading sessions...</p></div>;
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl text-neutral-900">Active Sessions</h1>
          <p className="text-sm text-neutral-600 mt-1">
            Live exclusive sessions • Last updated: {lastRefresh.toLocaleTimeString()}
          </p>
        </div>
        <button
          onClick={loadSessions}
          className="p-2 hover:bg-neutral-100 rounded-lg"
          title="Refresh"
        >
          <RefreshCw className="w-5 h-5 text-neutral-600" />
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-sm text-neutral-600 mb-1">Total Active</div>
          <div className="text-2xl text-neutral-900">{sessions.length}</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-sm text-neutral-600 mb-1">Avg Time Remaining</div>
          <div className="text-2xl text-neutral-900">
            {sessions.length > 0
              ? Math.round(sessions.reduce((acc, s) => acc + s.time_remaining_minutes, 0) / sessions.length)
              : 0} min
          </div>
        </div>
      </div>

      {/* Sessions Table */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-neutral-50 border-b border-neutral-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Session ID</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Driver</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Merchant</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Charger</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Time Remaining</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {sessions.map((session) => (
              <tr key={session.id} className="hover:bg-neutral-50">
                <td className="px-6 py-4 text-sm text-neutral-900 font-mono">{session.id.slice(0, 8)}...</td>
                <td className="px-6 py-4 text-sm text-neutral-600">#{session.driver_id}</td>
                <td className="px-6 py-4 text-sm text-neutral-900">{session.merchant_name || '-'}</td>
                <td className="px-6 py-4 text-sm text-neutral-600">{session.charger_name || session.charger_id?.slice(0, 8) || '-'}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-neutral-500" />
                    <span className="text-sm text-neutral-900">{session.time_remaining_minutes} min</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`inline-flex px-2.5 py-1 rounded-md text-xs border ${getStatusColor(session.status)}`}>
                    {session.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {sessions.length === 0 && (
        <div className="text-center py-12 text-neutral-500">No active sessions</div>
      )}
    </div>
  );
}
