import { useState } from 'react';
import { XCircle, Clock, Flag } from 'lucide-react';

interface Session {
  id: string;
  userId: string;
  merchant: string;
  location: string;
  timeRemaining: number; // in minutes
  status: 'active' | 'charging' | 'flagged';
  startTime: string;
}

const mockSessions: Session[] = [
  { id: 'S8472', userId: 'U001', merchant: 'Voltage Coffee Bar', location: 'Downtown Station #1', timeRemaining: 23, status: 'charging', startTime: '14:12' },
  { id: 'S8473', userId: 'U042', merchant: 'Peak Hours Gym', location: 'Midtown Plaza', timeRemaining: 45, status: 'active', startTime: '13:50' },
  { id: 'S8474', userId: 'U089', merchant: 'Current Cafe', location: 'Pearl District Hub', timeRemaining: 12, status: 'charging', startTime: '14:35' },
  { id: 'S8475', userId: 'U124', merchant: 'Voltage Coffee Bar', location: 'Downtown Station #1', timeRemaining: 8, status: 'flagged', startTime: '14:38' },
  { id: 'S8476', userId: 'U156', merchant: 'EV Lounge', location: 'Capitol Hill Station', timeRemaining: 31, status: 'active', startTime: '14:15' },
  { id: 'S8477', userId: 'U203', merchant: 'Power Station Cafe', location: 'Pearl District Hub', timeRemaining: 54, status: 'charging', startTime: '13:45' },
  { id: 'S8478', userId: 'U287', merchant: 'Charge & Dine', location: 'Downtown Station #4', timeRemaining: 19, status: 'active', startTime: '14:27' },
  { id: 'S8479', userId: 'U301', merchant: 'FastCharge Premium', location: 'Bellevue Center', timeRemaining: 41, status: 'charging', startTime: '14:05' },
];

export function ActiveSessions() {
  const [sessions, setSessions] = useState(mockSessions);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'charging':
        return 'text-blue-700 bg-blue-50 border-blue-200';
      case 'flagged':
        return 'text-red-700 bg-red-50 border-red-200';
      default:
        return 'text-neutral-700 bg-neutral-50 border-neutral-200';
    }
  };

  const handleForceClose = (id: string) => {
    if (confirm(`Force close session ${id}?`)) {
      setSessions((prev) => prev.filter((s) => s.id !== id));
    }
  };

  const handleExtend = (id: string) => {
    setSessions((prev) =>
      prev.map((s) => (s.id === id ? { ...s, timeRemaining: s.timeRemaining + 30 } : s))
    );
  };

  const handleFlag = (id: string) => {
    setSessions((prev) =>
      prev.map((s) => (s.id === id ? { ...s, status: 'flagged' as const } : s))
    );
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl text-neutral-900">Active Sessions</h1>
        <p className="text-sm text-neutral-600 mt-1">Monitor and manage live charging sessions</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-sm text-neutral-600 mb-1">Total Active</div>
          <div className="text-2xl text-neutral-900">{sessions.length}</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-sm text-neutral-600 mb-1">Currently Charging</div>
          <div className="text-2xl text-blue-600">
            {sessions.filter((s) => s.status === 'charging').length}
          </div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-sm text-neutral-600 mb-1">Flagged</div>
          <div className="text-2xl text-red-600">
            {sessions.filter((s) => s.status === 'flagged').length}
          </div>
        </div>
      </div>

      {/* Sessions Table */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-neutral-50 border-b border-neutral-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Session ID
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                User ID
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Merchant
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Location
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Time Remaining
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Started
              </th>
              <th className="px-6 py-3 text-right text-xs text-neutral-600 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {sessions.map((session) => (
              <tr key={session.id} className="hover:bg-neutral-50">
                <td className="px-6 py-4 text-sm text-neutral-900">{session.id}</td>
                <td className="px-6 py-4 text-sm text-neutral-600">{session.userId}</td>
                <td className="px-6 py-4 text-sm text-neutral-900">{session.merchant}</td>
                <td className="px-6 py-4 text-sm text-neutral-600">{session.location}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-neutral-500" />
                    <span className="text-sm text-neutral-900">{session.timeRemaining} min</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span
                    className={`inline-flex px-2.5 py-1 rounded-md text-xs border ${getStatusColor(
                      session.status
                    )}`}
                  >
                    {session.status.charAt(0).toUpperCase() + session.status.slice(1)}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-neutral-600">{session.startTime}</td>
                <td className="px-6 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => handleExtend(session.id)}
                      className="px-3 py-1.5 text-xs border border-neutral-300 rounded hover:bg-neutral-50"
                    >
                      Extend
                    </button>
                    <button
                      onClick={() => handleFlag(session.id)}
                      className="p-1.5 hover:bg-yellow-50 rounded text-yellow-600 hover:text-yellow-700"
                      title="Flag session"
                    >
                      <Flag className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleForceClose(session.id)}
                      className="p-1.5 hover:bg-red-50 rounded text-red-600 hover:text-red-700"
                      title="Force close"
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
