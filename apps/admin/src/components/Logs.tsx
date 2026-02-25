import { useState, useEffect } from 'react';
import { Search, Filter, Download } from 'lucide-react';
import { getAuditLogs, type AuditLog } from '../services/api';

export function Logs() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [limit] = useState(100);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadLogs();
  }, [filterType, searchTerm, offset]);

  async function loadLogs() {
    setLoading(true);
    setError(null);
    try {
      const type = filterType === 'all' ? undefined : filterType;
      const search = searchTerm || undefined;
      const response = await getAuditLogs(limit, offset, type, search);
      setLogs(response.logs);
      setTotal(response.total);
    } catch (err: any) {
      console.error('Failed to load logs:', err);
      setError(err.message || 'Failed to load logs');
    } finally {
      setLoading(false);
    }
  }

  const getTypeColor = (actionType: string) => {
    if (actionType.includes('admin') || actionType.includes('toggle') || actionType.includes('pause') || actionType.includes('resume')) {
      return 'text-purple-700 bg-purple-50 border-purple-200';
    }
    if (actionType.includes('error') || actionType.includes('force')) {
      return 'text-red-700 bg-red-50 border-red-200';
    }
    if (actionType.includes('system') || actionType.includes('emergency')) {
      return 'text-blue-700 bg-blue-50 border-blue-200';
    }
    return 'text-neutral-700 bg-neutral-50 border-neutral-200';
  };

  const filteredLogs = logs.filter((log) => {
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      return (
        log.action_type.toLowerCase().includes(searchLower) ||
        log.target_id.toLowerCase().includes(searchLower) ||
        (log.reason && log.reason.toLowerCase().includes(searchLower))
      );
    }
    return true;
  });

  const adminLogs = logs.filter((l) => l.action_type.includes('admin') || l.action_type.includes('toggle') || l.action_type.includes('pause')).length;
  const errorLogs = logs.filter((l) => l.action_type.includes('error') || l.action_type.includes('force')).length;
  const systemLogs = logs.filter((l) => l.action_type.includes('system') || l.action_type.includes('emergency')).length;

  if (loading && logs.length === 0) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center h-64">
          <p className="text-neutral-600">Loading logs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl text-neutral-900">System Logs</h1>
        <p className="text-sm text-neutral-600 mt-1">Complete audit trail of system activities</p>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
          <button onClick={loadLogs} className="ml-4 underline">Retry</button>
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-neutral-400" />
          <input
            type="text"
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setOffset(0);
            }}
            className="w-full pl-10 pr-4 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-neutral-500" />
          <select
            value={filterType}
            onChange={(e) => {
              setFilterType(e.target.value);
              setOffset(0);
            }}
            className="px-3 py-2 border border-neutral-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Types</option>
            <option value="admin">Admin</option>
            <option value="error">Error</option>
            <option value="system">System</option>
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-sm text-neutral-600 mb-1">Total Logs</div>
          <div className="text-2xl text-neutral-900">{total}</div>
        </div>
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="text-sm text-purple-600 mb-1">Admin</div>
          <div className="text-2xl text-purple-900">{adminLogs}</div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-sm text-red-600 mb-1">Errors/Force</div>
          <div className="text-2xl text-red-900">{errorLogs}</div>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-sm text-blue-600 mb-1">System</div>
          <div className="text-2xl text-blue-900">{systemLogs}</div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-neutral-50 border-b border-neutral-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Timestamp</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Type</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Action</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Target</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Operator</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Reason</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">IP Address</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {filteredLogs.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-neutral-500">
                  No logs found
                </td>
              </tr>
            ) : (
              filteredLogs.map((log) => (
                <tr key={log.id} className="hover:bg-neutral-50">
                  <td className="px-6 py-4 text-sm text-neutral-900">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex px-2.5 py-1 rounded-md text-xs border ${getTypeColor(log.action_type)}`}>
                      {log.action_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-neutral-900">{log.action_type}</td>
                  <td className="px-6 py-4 text-sm text-neutral-600">
                    {log.target_type}: {log.target_id}
                  </td>
                  <td className="px-6 py-4 text-sm text-neutral-600">{log.operator_email || `User ${log.operator_id}`}</td>
                  <td className="px-6 py-4 text-sm text-neutral-600">{log.reason || '—'}</td>
                  <td className="px-6 py-4 text-sm text-neutral-500">{log.ip_address || '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {total > limit && (
        <div className="mt-4 flex items-center justify-between">
          <div className="text-sm text-neutral-600">
            Showing {offset + 1} to {Math.min(offset + limit, total)} of {total} logs
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0}
              className="px-4 py-2 border border-neutral-300 rounded-lg hover:bg-neutral-50 disabled:bg-neutral-100 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= total}
              className="px-4 py-2 border border-neutral-300 rounded-lg hover:bg-neutral-50 disabled:bg-neutral-100 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
