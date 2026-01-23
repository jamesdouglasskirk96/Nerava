import { useState, useEffect } from 'react';
import { Clock, User, Zap, CheckCircle } from 'lucide-react';
import { getMerchantVisits, type Visit } from '../services/api';

export function Visits() {
  const [visits, setVisits] = useState<Visit[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [verifiedCount, setVerifiedCount] = useState(0);
  const [period, setPeriod] = useState<'week' | 'month' | 'all'>('week');
  const [statusFilter, setStatusFilter] = useState<'VERIFIED' | 'PARTIAL' | 'REJECTED' | 'all'>('all');
  const [error, setError] = useState<string | null>(null);
  const merchantId = localStorage.getItem('merchant_id') || new URLSearchParams(window.location.search).get('merchant_id') || '';

  useEffect(() => {
    loadVisits();
  }, [merchantId, period, statusFilter]);

  const loadVisits = async () => {
    if (!merchantId) return;
    try {
      setLoading(true);
      setError(null);
      const status = statusFilter === 'all' ? undefined : statusFilter;
      const data = await getMerchantVisits(merchantId, period, status);
      setVisits(data.visits);
      setTotal(data.total);
      setVerifiedCount(data.verified_count);
    } catch (err) {
      console.error('Failed to load visits:', err);
      setError('Failed to load visit data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getVerificationStatusColor = (status: string) => {
    switch (status) {
      case 'VERIFIED': return 'text-green-700 bg-green-50 border-green-200';
      case 'PARTIAL': return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      case 'REJECTED': return 'text-red-700 bg-red-50 border-red-200';
      default: return 'text-neutral-700 bg-neutral-50';
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const getPeriodLabel = () => {
    switch (period) {
      case 'week': return 'Last 7 Days';
      case 'month': return 'Last 30 Days';
      case 'all': return 'All Time';
    }
  };

  if (loading && visits.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-neutral-600">Loading visits...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        {error}
        <button onClick={loadVisits} className="ml-4 underline">Retry</button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl text-neutral-900 mb-2">Verified Visits</h1>
        <p className="text-neutral-600">
          {total} total visits ({getPeriodLabel()})
        </p>
      </div>

      {/* Verified Count Banner */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
        <div className="flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <p className="text-green-800">
            <strong>{verifiedCount}</strong> verified visits this {period === 'week' ? 'week' : period === 'month' ? 'month' : 'period'} = billable events
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 flex gap-4">
        <div>
          <label className="block text-sm text-neutral-600 mb-1">Period</label>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as 'week' | 'month' | 'all')}
            className="px-3 py-2 border border-neutral-300 rounded-lg text-sm"
          >
            <option value="week">Last 7 Days</option>
            <option value="month">Last 30 Days</option>
            <option value="all">All Time</option>
          </select>
        </div>
        <div>
          <label className="block text-sm text-neutral-600 mb-1">Status</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as 'VERIFIED' | 'PARTIAL' | 'REJECTED' | 'all')}
            className="px-3 py-2 border border-neutral-300 rounded-lg text-sm"
          >
            <option value="all">All Statuses</option>
            <option value="VERIFIED">Verified Only</option>
            <option value="PARTIAL">Partial Only</option>
            <option value="REJECTED">Rejected Only</option>
          </select>
        </div>
      </div>

      {visits.length === 0 ? (
        <div className="bg-white p-12 rounded-lg border border-neutral-200 text-center">
          <Zap className="w-12 h-12 text-neutral-300 mx-auto mb-4" />
          <h3 className="text-lg text-neutral-900 mb-2">No visits yet</h3>
          <p className="text-neutral-600">
            Visits will appear here when EV drivers activate exclusives at your location.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-neutral-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-neutral-50 border-b border-neutral-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Timestamp</th>
                <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Offer</th>
                <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Driver</th>
                <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Duration</th>
                <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Location</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {visits.map((visit) => (
                <tr key={visit.id} className="hover:bg-neutral-50">
                  <td className="px-6 py-4 text-sm text-neutral-900">
                    {formatDate(visit.timestamp)}
                  </td>
                  <td className="px-6 py-4 text-sm text-neutral-900">
                    {visit.exclusive_title}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-neutral-100 rounded">
                        <User className="w-3.5 h-3.5 text-neutral-600" />
                      </div>
                      <span className="text-sm text-neutral-600">{visit.driver_id_anonymized}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex px-2.5 py-1 rounded-md text-xs border ${getVerificationStatusColor(visit.verification_status)}`}>
                      {visit.verification_status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-neutral-500" />
                      <span className="text-sm text-neutral-900">
                        {visit.duration_minutes ? `${visit.duration_minutes} min` : '-'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-neutral-600">
                    {visit.location_name || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
