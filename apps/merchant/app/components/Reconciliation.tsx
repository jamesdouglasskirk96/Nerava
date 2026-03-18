import { useState, useEffect } from 'react';
import { Download, FileText, Calendar, CheckCircle, XCircle, Clock } from 'lucide-react';
import {
  getReconciliationSummary,
  getReconciliationExportUrl,
  type ReconciliationSummary,
} from '../services/api';

export function Reconciliation() {
  const [summary, setSummary] = useState<ReconciliationSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<'week' | 'month' | 'quarter'>('month');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [useCustomRange, setUseCustomRange] = useState(false);

  useEffect(() => {
    loadSummary();
  }, [period, useCustomRange]);

  const loadSummary = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getReconciliationSummary(
        period,
        useCustomRange ? startDate : undefined,
        useCustomRange ? endDate : undefined
      );
      setSummary(data);
    } catch (err) {
      console.error('Failed to load reconciliation data:', err);
      setError('Failed to load reconciliation data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    const url = getReconciliationExportUrl(
      period,
      useCustomRange ? startDate : undefined,
      useCustomRange ? endDate : undefined
    );
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = res.headers.get('content-disposition')?.split('filename=')[1] || 'nerava-claims.csv';
      a.click();
      URL.revokeObjectURL(a.href);
    } catch {
      setError('Failed to download export. Please try again.');
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-neutral-600">Loading reconciliation data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        {error}
        <button onClick={loadSummary} className="ml-4 underline">Retry</button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl text-neutral-900 mb-2">Reconciliation</h1>
          <p className="text-neutral-600">
            Claims-based billing summary. Compare against your Toast export for disputes.
          </p>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 bg-neutral-900 text-white rounded-lg hover:bg-neutral-800 transition-colors"
        >
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

      {/* Period Selector */}
      <div className="mb-6 flex items-end gap-4">
        <div>
          <label className="block text-sm text-neutral-600 mb-1">Period</label>
          <select
            value={useCustomRange ? 'custom' : period}
            onChange={(e) => {
              if (e.target.value === 'custom') {
                setUseCustomRange(true);
              } else {
                setUseCustomRange(false);
                setPeriod(e.target.value as 'week' | 'month' | 'quarter');
              }
            }}
            className="px-3 py-2 border border-neutral-300 rounded-lg text-sm"
          >
            <option value="week">Last 7 Days</option>
            <option value="month">Last 30 Days</option>
            <option value="quarter">Last 90 Days</option>
            <option value="custom">Custom Range</option>
          </select>
        </div>
        {useCustomRange && (
          <>
            <div>
              <label className="block text-sm text-neutral-600 mb-1">Start</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="px-3 py-2 border border-neutral-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-neutral-600 mb-1">End</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="px-3 py-2 border border-neutral-300 rounded-lg text-sm"
              />
            </div>
            <button
              onClick={loadSummary}
              className="px-4 py-2 bg-neutral-200 rounded-lg text-sm hover:bg-neutral-300 transition-colors"
            >
              Apply
            </button>
          </>
        )}
      </div>

      {summary && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="bg-white rounded-lg border border-neutral-200 p-6">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-sm text-neutral-600">Billable Claims</span>
              </div>
              <p className="text-3xl text-neutral-900">{summary.total_claims}</p>
              <p className="text-xs text-neutral-500 mt-1">
                Completed exclusive sessions
              </p>
            </div>
            <div className="bg-white rounded-lg border border-neutral-200 p-6">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="w-5 h-5 text-blue-600" />
                <span className="text-sm text-neutral-600">Verified & Redeemed</span>
              </div>
              <p className="text-3xl text-neutral-900">{summary.total_redeemed}</p>
              <p className="text-xs text-neutral-500 mt-1">
                Visits with POS confirmation
              </p>
            </div>
            <div className="bg-white rounded-lg border border-neutral-200 p-6">
              <div className="flex items-center gap-2 mb-2">
                <XCircle className="w-5 h-5 text-neutral-400" />
                <span className="text-sm text-neutral-600">Expired</span>
              </div>
              <p className="text-3xl text-neutral-900">{summary.total_expired}</p>
              <p className="text-xs text-neutral-500 mt-1">
                Activated but not completed
              </p>
            </div>
          </div>

          {/* How This Works */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-8">
            <h3 className="text-sm font-medium text-blue-900 mb-1">How billing works</h3>
            <p className="text-sm text-blue-800">
              You are billed per <strong>completed claim</strong> (driver activates offer and visits your location).
              Export this report and compare it against your Toast sales export for the same period.
              If the numbers don't match, contact us with both exports to resolve.
            </p>
          </div>

          {/* Daily Breakdown */}
          <div className="bg-white rounded-lg border border-neutral-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-neutral-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-neutral-500" />
                <h2 className="text-lg text-neutral-900">Daily Breakdown</h2>
              </div>
              <span className="text-sm text-neutral-500">
                {summary.period_start} to {summary.period_end}
              </span>
            </div>
            {summary.daily_breakdown.length === 0 ? (
              <div className="p-12 text-center">
                <Clock className="w-10 h-10 text-neutral-300 mx-auto mb-3" />
                <p className="text-neutral-600">No claims in this period</p>
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-neutral-50 border-b border-neutral-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-right text-xs text-neutral-600 uppercase tracking-wider">Claims</th>
                    <th className="px-6 py-3 text-right text-xs text-neutral-600 uppercase tracking-wider">Redeemed</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100">
                  {summary.daily_breakdown.map((day) => (
                    <tr key={day.date} className="hover:bg-neutral-50">
                      <td className="px-6 py-4 text-sm text-neutral-900">
                        {formatDate(day.date)}
                      </td>
                      <td className="px-6 py-4 text-sm text-neutral-900 text-right">
                        {day.claims}
                      </td>
                      <td className="px-6 py-4 text-sm text-neutral-900 text-right">
                        {day.redeemed}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-neutral-50 border-t border-neutral-200">
                  <tr>
                    <td className="px-6 py-3 text-sm font-medium text-neutral-900">Total</td>
                    <td className="px-6 py-3 text-sm font-medium text-neutral-900 text-right">
                      {summary.total_claims}
                    </td>
                    <td className="px-6 py-3 text-sm font-medium text-neutral-900 text-right">
                      {summary.total_redeemed}
                    </td>
                  </tr>
                </tfoot>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  );
}
