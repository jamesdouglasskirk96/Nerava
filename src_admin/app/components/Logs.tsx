import { useState } from 'react';
import { Search, Filter, Download } from 'lucide-react';

interface LogEntry {
  id: string;
  timestamp: string;
  type: 'system' | 'user' | 'merchant' | 'admin' | 'error';
  action: string;
  details: string;
  operator?: string;
  ipAddress?: string;
}

const mockLogs: LogEntry[] = [
  {
    id: 'L1001',
    timestamp: '2026-01-05 14:45:23',
    type: 'admin',
    action: 'Merchant paused',
    details: 'Bolt Bistro (M003) paused by admin',
    operator: 'admin@nerava.com',
    ipAddress: '192.168.1.100',
  },
  {
    id: 'L1002',
    timestamp: '2026-01-05 14:32:15',
    type: 'admin',
    action: 'Session extended',
    details: 'Session S8472 extended by 30 minutes',
    operator: 'support@nerava.com',
    ipAddress: '192.168.1.101',
  },
  {
    id: 'L1003',
    timestamp: '2026-01-05 14:23:47',
    type: 'error',
    action: 'Merchant abuse flagged',
    details: 'Voltage Coffee Bar flagged for suspicious activity pattern',
    operator: 'system',
  },
  {
    id: 'L1004',
    timestamp: '2026-01-05 14:18:09',
    type: 'admin',
    action: 'Exclusive disabled',
    details: 'FastCharge Premium - Priority Charging Access disabled',
    operator: 'admin@nerava.com',
    ipAddress: '192.168.1.100',
  },
  {
    id: 'L1005',
    timestamp: '2026-01-05 13:56:12',
    type: 'admin',
    action: 'Override executed',
    details: 'Force-close all sessions at Downtown Station #2',
    operator: 'ops@nerava.com',
    ipAddress: '192.168.1.102',
  },
  {
    id: 'L1006',
    timestamp: '2026-01-05 13:47:33',
    type: 'error',
    action: 'Charger data unavailable',
    details: 'Location Downtown Station #4 - charger telemetry offline',
    operator: 'system',
  },
  {
    id: 'L1007',
    timestamp: '2026-01-05 12:15:28',
    type: 'system',
    action: 'Location mis-mapped',
    details: 'Midtown Plaza coordinates mismatch detected',
    operator: 'system',
  },
  {
    id: 'L1008',
    timestamp: '2026-01-05 11:23:45',
    type: 'admin',
    action: 'Primary Experience disabled',
    details: 'Capitol Hill Station primary experience turned off',
    operator: 'admin@nerava.com',
    ipAddress: '192.168.1.100',
  },
  {
    id: 'L1009',
    timestamp: '2026-01-05 11:02:11',
    type: 'error',
    action: 'Exclusive misconfiguration',
    details: 'Peak Hours Gym daily cap exceeds monthly cap limit',
    operator: 'system',
  },
  {
    id: 'L1010',
    timestamp: '2026-01-05 10:45:03',
    type: 'user',
    action: 'Session started',
    details: 'User U301 started session S8479 at Bellevue Center',
  },
  {
    id: 'L1011',
    timestamp: '2026-01-05 10:32:17',
    type: 'merchant',
    action: 'Exclusive activated',
    details: 'Current Cafe - Free Pastry with Drink claimed by User U089',
  },
  {
    id: 'L1012',
    timestamp: '2026-01-05 10:18:52',
    type: 'user',
    action: 'Session completed',
    details: 'User U042 completed session S8455 at Midtown Plaza',
  },
];

export function Logs() {
  const [logs] = useState(mockLogs);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'admin':
        return 'text-purple-700 bg-purple-50 border-purple-200';
      case 'error':
        return 'text-red-700 bg-red-50 border-red-200';
      case 'system':
        return 'text-blue-700 bg-blue-50 border-blue-200';
      case 'user':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'merchant':
        return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      default:
        return 'text-neutral-700 bg-neutral-50 border-neutral-200';
    }
  };

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.details.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterType === 'all' || log.type === filterType;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl text-neutral-900">System Logs</h1>
        <p className="text-sm text-neutral-600 mt-1">Complete audit trail of system activities</p>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-neutral-400" />
          <input
            type="text"
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-neutral-500" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-2 border border-neutral-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Types</option>
            <option value="admin">Admin</option>
            <option value="error">Error</option>
            <option value="system">System</option>
            <option value="user">User</option>
            <option value="merchant">Merchant</option>
          </select>
        </div>

        <button className="flex items-center gap-2 px-4 py-2 bg-neutral-900 text-white text-sm rounded-lg hover:bg-neutral-800">
          <Download className="w-4 h-4" />
          Export
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-5 gap-4 mb-6">
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-sm text-neutral-600 mb-1">Total Logs</div>
          <div className="text-2xl text-neutral-900">{logs.length}</div>
        </div>
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="text-sm text-purple-600 mb-1">Admin</div>
          <div className="text-2xl text-purple-900">
            {logs.filter((l) => l.type === 'admin').length}
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-sm text-red-600 mb-1">Errors</div>
          <div className="text-2xl text-red-900">
            {logs.filter((l) => l.type === 'error').length}
          </div>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-sm text-blue-600 mb-1">System</div>
          <div className="text-2xl text-blue-900">
            {logs.filter((l) => l.type === 'system').length}
          </div>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="text-sm text-green-600 mb-1">User</div>
          <div className="text-2xl text-green-900">
            {logs.filter((l) => l.type === 'user').length}
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-neutral-50 border-b border-neutral-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Timestamp
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Action
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Details
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Operator
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                IP Address
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {filteredLogs.map((log) => (
              <tr key={log.id} className="hover:bg-neutral-50">
                <td className="px-6 py-4 text-sm text-neutral-900">{log.timestamp}</td>
                <td className="px-6 py-4">
                  <span
                    className={`inline-flex px-2.5 py-1 rounded-md text-xs border ${getTypeColor(
                      log.type
                    )}`}
                  >
                    {log.type.charAt(0).toUpperCase() + log.type.slice(1)}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-neutral-900">{log.action}</td>
                <td className="px-6 py-4 text-sm text-neutral-600">{log.details}</td>
                <td className="px-6 py-4 text-sm text-neutral-600">{log.operator || '—'}</td>
                <td className="px-6 py-4 text-sm text-neutral-500">{log.ipAddress || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredLogs.length === 0 && (
        <div className="text-center py-12 text-neutral-500">No logs found</div>
      )}
    </div>
  );
}
