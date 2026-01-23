import { useState, useEffect } from 'react';
import { Pause, Play, Edit, Ban } from 'lucide-react';
import { getAllExclusives, toggleExclusive, type Exclusive } from '../services/api';

export function Exclusives() {
  const [exclusives, setExclusives] = useState<Exclusive[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'active' | 'paused'>('all');
  const [total, setTotal] = useState(0);
  const [toggleDialog, setToggleDialog] = useState<{ id: string; currentState: boolean } | null>(null);
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadExclusives();
  }, [filter]);

  async function loadExclusives() {
    setLoading(true);
    setError(null);
    try {
      const status = filter === 'all' ? undefined : filter;
      const response = await getAllExclusives(status);
      setExclusives(response.exclusives);
      setTotal(response.total);
    } catch (err: any) {
      console.error('Failed to load exclusives:', err);
      setError(err.message || 'Failed to load exclusives');
    } finally {
      setLoading(false);
    }
  }

  async function handleToggle(exclusiveId: string, currentState: boolean) {
    setToggleDialog({ id: exclusiveId, currentState });
  }

  async function confirmToggle() {
    if (!toggleDialog) return;
    if (!reason || reason.length < 5) {
      alert('Please provide a reason (minimum 5 characters)');
      return;
    }

    try {
      await toggleExclusive(toggleDialog.id, reason);
      setToggleDialog(null);
      setReason('');
      loadExclusives(); // Refresh
    } catch (err: any) {
      console.error('Failed to toggle exclusive:', err);
      alert(err.message || 'Failed to toggle exclusive');
    }
  }

  const getStatusColor = (status: boolean) => {
    return status
      ? 'text-green-700 bg-green-50 border-green-200'
      : 'text-yellow-700 bg-yellow-50 border-yellow-200';
  };

  const activeCount = exclusives.filter((e) => e.is_active).length;
  const pausedCount = exclusives.filter((e) => !e.is_active).length;
  const totalActivationsToday = exclusives.reduce((sum, e) => sum + e.activations_today, 0);

  if (loading) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center h-64">
          <p className="text-neutral-600">Loading exclusives...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl text-neutral-900">Exclusives</h1>
        <p className="text-sm text-neutral-600 mt-1">Manage merchant exclusive offers and promotions</p>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
          <button onClick={loadExclusives} className="ml-4 underline">Retry</button>
        </div>
      )}

      {/* Filter */}
      <div className="mb-6">
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as 'all' | 'active' | 'paused')}
          className="px-4 py-2 border border-neutral-300 rounded-lg"
        >
          <option value="all">All Exclusives</option>
          <option value="active">Active Only</option>
          <option value="paused">Paused Only</option>
        </select>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-sm text-neutral-600 mb-1">Total Exclusives</div>
          <div className="text-2xl text-neutral-900">{total}</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-sm text-neutral-600 mb-1">Active</div>
          <div className="text-2xl text-green-600">{activeCount}</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-sm text-neutral-600 mb-1">Paused</div>
          <div className="text-2xl text-yellow-600">{pausedCount}</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-sm text-neutral-600 mb-1">Activations Today</div>
          <div className="text-2xl text-blue-600">{totalActivationsToday}</div>
        </div>
      </div>

      {/* Exclusives Table */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-neutral-50 border-b border-neutral-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">ID</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Merchant</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Title</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Activations Today</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Daily Cap</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Monthly Activations</th>
              <th className="px-6 py-3 text-right text-xs text-neutral-600 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {exclusives.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center text-neutral-500">
                  No exclusives found
                </td>
              </tr>
            ) : (
              exclusives.map((exclusive) => {
                const dailyPercent = exclusive.daily_cap
                  ? (exclusive.activations_today / exclusive.daily_cap) * 100
                  : 0;

                return (
                  <tr key={exclusive.id} className="hover:bg-neutral-50">
                    <td className="px-6 py-4 text-sm text-neutral-900">{exclusive.id}</td>
                    <td className="px-6 py-4 text-sm text-neutral-900">{exclusive.merchant_name}</td>
                    <td className="px-6 py-4 text-sm text-neutral-600">{exclusive.title}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex px-2.5 py-1 rounded-md text-xs border ${getStatusColor(
                          exclusive.is_active
                        )}`}
                      >
                        {exclusive.is_active ? 'Active' : 'Paused'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-neutral-900">{exclusive.activations_today}</div>
                      {exclusive.daily_cap && (
                        <div className="w-24 h-1.5 bg-neutral-100 rounded-full mt-1">
                          <div
                            className="h-full bg-blue-500 rounded-full"
                            style={{ width: `${Math.min(dailyPercent, 100)}%` }}
                          />
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-neutral-600">
                      {exclusive.daily_cap || 'No cap'}
                    </td>
                    <td className="px-6 py-4 text-sm text-neutral-900">
                      {exclusive.activations_this_month}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {exclusive.is_active ? (
                          <button
                            onClick={() => handleToggle(exclusive.id, true)}
                            className="p-1.5 hover:bg-yellow-50 rounded text-yellow-600 hover:text-yellow-700"
                            title="Pause"
                          >
                            <Pause className="w-4 h-4" />
                          </button>
                        ) : (
                          <button
                            onClick={() => handleToggle(exclusive.id, false)}
                            className="p-1.5 hover:bg-green-50 rounded text-green-600 hover:text-green-700"
                            title="Resume"
                          >
                            <Play className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Toggle Reason Dialog */}
      {toggleDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">
              {toggleDialog.currentState ? 'Pause' : 'Resume'} Exclusive
            </h3>
            <p className="text-sm text-neutral-600 mb-4">
              Please provide a reason for this action (minimum 5 characters):
            </p>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg mb-4"
              rows={3}
              placeholder="Enter reason..."
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setToggleDialog(null);
                  setReason('');
                }}
                className="px-4 py-2 border border-neutral-300 rounded-lg hover:bg-neutral-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmToggle}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
