import { useState } from 'react';
import { Pause, Play, Edit, Ban } from 'lucide-react';

interface Exclusive {
  id: string;
  merchant: string;
  type: string;
  status: 'active' | 'paused' | 'disabled';
  activationsToday: number;
  dailyCap: number;
  monthlyCap: number;
  monthlyActivations: number;
}

const mockExclusives: Exclusive[] = [
  {
    id: 'E001',
    merchant: 'Voltage Coffee Bar',
    type: 'Free Premium Coffee',
    status: 'active',
    activationsToday: 47,
    dailyCap: 100,
    monthlyCap: 2000,
    monthlyActivations: 1234,
  },
  {
    id: 'E002',
    merchant: 'Peak Hours Gym',
    type: 'Complimentary Day Pass',
    status: 'active',
    activationsToday: 23,
    dailyCap: 50,
    monthlyCap: 1000,
    monthlyActivations: 678,
  },
  {
    id: 'E003',
    merchant: 'Bolt Bistro',
    type: '20% Off Lunch Menu',
    status: 'paused',
    activationsToday: 0,
    dailyCap: 75,
    monthlyCap: 1500,
    monthlyActivations: 892,
  },
  {
    id: 'E004',
    merchant: 'Current Cafe',
    type: 'Free Pastry with Drink',
    status: 'active',
    activationsToday: 61,
    dailyCap: 150,
    monthlyCap: 3000,
    monthlyActivations: 2156,
  },
  {
    id: 'E005',
    merchant: 'FastCharge Premium',
    type: 'Priority Charging Access',
    status: 'disabled',
    activationsToday: 0,
    dailyCap: 30,
    monthlyCap: 500,
    monthlyActivations: 234,
  },
  {
    id: 'E006',
    merchant: 'EV Lounge',
    type: 'Premium Seating',
    status: 'active',
    activationsToday: 38,
    dailyCap: 80,
    monthlyCap: 1600,
    monthlyActivations: 1045,
  },
];

export function Exclusives() {
  const [exclusives, setExclusives] = useState(mockExclusives);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'paused':
        return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      case 'disabled':
        return 'text-neutral-700 bg-neutral-100 border-neutral-300';
      default:
        return 'text-neutral-700 bg-neutral-50 border-neutral-200';
    }
  };

  const handlePause = (id: string) => {
    setExclusives((prev) =>
      prev.map((e) => (e.id === id ? { ...e, status: 'paused' as const } : e))
    );
  };

  const handleResume = (id: string) => {
    setExclusives((prev) =>
      prev.map((e) => (e.id === id ? { ...e, status: 'active' as const } : e))
    );
  };

  const handleDisable = (id: string) => {
    if (confirm(`Disable exclusive ${id}?`)) {
      setExclusives((prev) =>
        prev.map((e) => (e.id === id ? { ...e, status: 'disabled' as const } : e))
      );
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl text-neutral-900">Exclusives</h1>
        <p className="text-sm text-neutral-600 mt-1">Manage merchant exclusive offers and promotions</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-sm text-neutral-600 mb-1">Total Exclusives</div>
          <div className="text-2xl text-neutral-900">{exclusives.length}</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-sm text-neutral-600 mb-1">Active</div>
          <div className="text-2xl text-green-600">
            {exclusives.filter((e) => e.status === 'active').length}
          </div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-sm text-neutral-600 mb-1">Paused</div>
          <div className="text-2xl text-yellow-600">
            {exclusives.filter((e) => e.status === 'paused').length}
          </div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-sm text-neutral-600 mb-1">Activations Today</div>
          <div className="text-2xl text-blue-600">
            {exclusives.reduce((sum, e) => sum + e.activationsToday, 0)}
          </div>
        </div>
      </div>

      {/* Exclusives Table */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-neutral-50 border-b border-neutral-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                ID
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Merchant
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Activations Today
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Daily Cap
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Monthly Progress
              </th>
              <th className="px-6 py-3 text-right text-xs text-neutral-600 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {exclusives.map((exclusive) => {
              const dailyPercent = (exclusive.activationsToday / exclusive.dailyCap) * 100;
              const monthlyPercent = (exclusive.monthlyActivations / exclusive.monthlyCap) * 100;

              return (
                <tr key={exclusive.id} className="hover:bg-neutral-50">
                  <td className="px-6 py-4 text-sm text-neutral-900">{exclusive.id}</td>
                  <td className="px-6 py-4 text-sm text-neutral-900">{exclusive.merchant}</td>
                  <td className="px-6 py-4 text-sm text-neutral-600">{exclusive.type}</td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex px-2.5 py-1 rounded-md text-xs border ${getStatusColor(
                        exclusive.status
                      )}`}
                    >
                      {exclusive.status.charAt(0).toUpperCase() + exclusive.status.slice(1)}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-neutral-900">{exclusive.activationsToday}</div>
                    <div className="w-24 h-1.5 bg-neutral-100 rounded-full mt-1">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${Math.min(dailyPercent, 100)}%` }}
                      />
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-neutral-600">{exclusive.dailyCap}</td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-neutral-900">
                      {exclusive.monthlyActivations} / {exclusive.monthlyCap}
                    </div>
                    <div className="w-32 h-1.5 bg-neutral-100 rounded-full mt-1">
                      <div
                        className="h-full bg-green-500 rounded-full"
                        style={{ width: `${Math.min(monthlyPercent, 100)}%` }}
                      />
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button className="p-1.5 hover:bg-blue-50 rounded text-blue-600 hover:text-blue-700">
                        <Edit className="w-4 h-4" />
                      </button>
                      {exclusive.status === 'paused' ? (
                        <button
                          onClick={() => handleResume(exclusive.id)}
                          className="p-1.5 hover:bg-green-50 rounded text-green-600 hover:text-green-700"
                          title="Resume"
                        >
                          <Play className="w-4 h-4" />
                        </button>
                      ) : exclusive.status === 'active' ? (
                        <button
                          onClick={() => handlePause(exclusive.id)}
                          className="p-1.5 hover:bg-yellow-50 rounded text-yellow-600 hover:text-yellow-700"
                          title="Pause"
                        >
                          <Pause className="w-4 h-4" />
                        </button>
                      ) : null}
                      <button
                        onClick={() => handleDisable(exclusive.id)}
                        className="p-1.5 hover:bg-red-50 rounded text-red-600 hover:text-red-700"
                        title="Disable"
                      >
                        <Ban className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
