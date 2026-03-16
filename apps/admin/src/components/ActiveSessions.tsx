import { useState, useEffect } from 'react';
import { Search, RefreshCw, ChevronLeft, ChevronRight, Download } from 'lucide-react';
import { getSessionHistory, type ChargingSession } from '../services/api';

export function ActiveSessions() {
  const [sessions, setSessions] = useState<ChargingSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const pageSize = 50;

  // Filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [driverFilter, setDriverFilter] = useState('');

  useEffect(() => {
    loadSessions();
  }, [page]);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const data = await getSessionHistory({
        limit: pageSize,
        offset: page * pageSize,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        driver_id: driverFilter ? parseInt(driverFilter) : undefined,
      });
      setSessions(data.sessions);
      setTotal(data.total);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Failed to load sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(0);
    loadSessions();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return '-';
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
  };

  const getStatusBadge = (session: ChargingSession) => {
    if (!session.session_end) {
      return <span className="inline-flex px-2 py-0.5 rounded text-xs bg-green-50 text-green-700 border border-green-200">Active</span>;
    }
    return <span className="inline-flex px-2 py-0.5 rounded text-xs bg-neutral-50 text-neutral-600 border border-neutral-200">Ended</span>;
  };

  const getRewardBadge = (session: ChargingSession) => {
    if (!session.has_reward) {
      return <span className="text-xs text-neutral-400">—</span>;
    }
    const cents = session.reward_cents || 0;
    const color = session.reward_status === 'granted'
      ? 'bg-green-50 text-green-700 border-green-200'
      : 'bg-amber-50 text-amber-700 border-amber-200';
    return (
      <span className={`inline-flex px-2 py-0.5 rounded text-xs border ${color}`}>
        ${(cents / 100).toFixed(2)} {session.reward_status}
      </span>
    );
  };

  const totalPages = Math.ceil(total / pageSize);

  const exportCSV = () => {
    const headers = ['Session ID', 'Driver ID', 'Driver Name', 'Start', 'End', 'Duration (min)', 'kWh', 'Charger', 'Network', 'Quality', 'Reason', 'Reward', 'Reward Status'];
    const rows = sessions.map(s => [
      s.id, s.driver_id, s.driver_name || '', s.session_start || '', s.session_end || '',
      s.duration_minutes ?? '', s.kwh_delivered ?? '', s.charger_id || '', s.charger_network || '',
      s.quality_score ?? '', s.ended_reason || '',
      s.has_reward ? `$${((s.reward_cents || 0) / 100).toFixed(2)}` : '', s.reward_status || '',
    ]);
    const csv = [headers, ...rows].map(r => r.map(c => `"${c}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nerava-sessions-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl text-neutral-900">Charging Sessions</h1>
          <p className="text-sm text-neutral-500 mt-1">
            {total} total sessions &middot; Last updated: {lastRefresh.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={exportCSV} className="flex items-center gap-1.5 px-3 py-2 text-sm text-neutral-600 hover:bg-neutral-100 rounded-lg border border-neutral-200" title="Export CSV">
            <Download className="w-4 h-4" /> Export
          </button>
          <button onClick={loadSessions} className="p-2 hover:bg-neutral-100 rounded-lg" title="Refresh">
            <RefreshCw className="w-4 h-4 text-neutral-600" />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-end gap-3 mb-6">
        <div>
          <label className="block text-xs text-neutral-500 mb-1">Start Date</label>
          <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} onKeyDown={handleKeyDown}
            className="px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white" />
        </div>
        <div>
          <label className="block text-xs text-neutral-500 mb-1">End Date</label>
          <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} onKeyDown={handleKeyDown}
            className="px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white" />
        </div>
        <div>
          <label className="block text-xs text-neutral-500 mb-1">Driver ID</label>
          <input type="text" placeholder="e.g. 3" value={driverFilter} onChange={e => setDriverFilter(e.target.value)} onKeyDown={handleKeyDown}
            className="px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white w-24" />
        </div>
        <button onClick={handleSearch} className="flex items-center gap-1.5 px-4 py-2 text-sm bg-neutral-900 text-white rounded-lg hover:bg-neutral-800">
          <Search className="w-3.5 h-3.5" /> Search
        </button>
        {(startDate || endDate || driverFilter) && (
          <button onClick={() => { setStartDate(''); setEndDate(''); setDriverFilter(''); setPage(0); setTimeout(loadSessions, 0); }}
            className="px-3 py-2 text-sm text-neutral-500 hover:text-neutral-700">
            Clear
          </button>
        )}
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-xs text-neutral-500 mb-1">Total Sessions</div>
          <div className="text-xl text-neutral-900 font-medium">{total}</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-xs text-neutral-500 mb-1">Unique Drivers</div>
          <div className="text-xl text-neutral-900 font-medium">{new Set(sessions.map(s => s.driver_id)).size}</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-xs text-neutral-500 mb-1">Total kWh</div>
          <div className="text-xl text-neutral-900 font-medium">{sessions.reduce((sum, s) => sum + (s.kwh_delivered || 0), 0).toFixed(1)}</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-xs text-neutral-500 mb-1">Rewarded</div>
          <div className="text-xl text-neutral-900 font-medium">{sessions.filter(s => s.has_reward).length}</div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-neutral-400">Loading sessions...</div>
        ) : sessions.length === 0 ? (
          <div className="p-12 text-center text-neutral-400">No sessions found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-neutral-50 border-b border-neutral-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Session ID</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Driver</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Start</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Duration</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">kWh</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Network</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Quality</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Reward</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {sessions.map((s) => (
                  <tr key={s.id} className="hover:bg-neutral-50">
                    <td className="px-4 py-3 text-sm font-mono text-neutral-600">{s.id.slice(0, 8)}</td>
                    <td className="px-4 py-3 text-sm">
                      <div className="text-neutral-900">{s.driver_name || `#${s.driver_id}`}</div>
                      <div className="text-xs text-neutral-400">ID: {s.driver_id}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-neutral-600">{formatDate(s.session_start)}</td>
                    <td className="px-4 py-3 text-sm text-neutral-900">{s.duration_minutes != null ? `${s.duration_minutes} min` : '-'}</td>
                    <td className="px-4 py-3 text-sm text-neutral-900">{s.kwh_delivered != null ? `${s.kwh_delivered.toFixed(1)}` : '-'}</td>
                    <td className="px-4 py-3 text-sm text-neutral-600">{s.charger_network || s.source || '-'}</td>
                    <td className="px-4 py-3 text-sm">
                      {s.quality_score != null ? (
                        <span className={`font-medium ${s.quality_score >= 80 ? 'text-green-600' : s.quality_score >= 50 ? 'text-amber-600' : 'text-red-600'}`}>
                          {s.quality_score}
                        </span>
                      ) : '-'}
                    </td>
                    <td className="px-4 py-3">{getStatusBadge(s)}</td>
                    <td className="px-4 py-3">{getRewardBadge(s)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-neutral-500">
            Showing {page * pageSize + 1}-{Math.min((page + 1) * pageSize, total)} of {total}
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
              className="p-2 rounded-lg hover:bg-neutral-100 disabled:opacity-30 disabled:cursor-not-allowed">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm text-neutral-600">Page {page + 1} of {totalPages}</span>
            <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}
              className="p-2 rounded-lg hover:bg-neutral-100 disabled:opacity-30 disabled:cursor-not-allowed">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
