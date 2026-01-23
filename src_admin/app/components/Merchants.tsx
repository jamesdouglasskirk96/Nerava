import { useState } from 'react';
import { Eye, Ban, CheckCircle, Search } from 'lucide-react';

interface Merchant {
  id: string;
  businessName: string;
  location: string;
  status: 'active' | 'paused' | 'flagged';
  activeSessions: number;
  totalSessions: number;
}

const mockMerchants: Merchant[] = [
  { id: 'M001', businessName: 'Voltage Coffee Bar', location: 'Downtown, Seattle', status: 'flagged', activeSessions: 12, totalSessions: 847 },
  { id: 'M002', businessName: 'Peak Hours Gym', location: 'Midtown, Portland', status: 'active', activeSessions: 8, totalSessions: 532 },
  { id: 'M003', businessName: 'Bolt Bistro', location: 'Capitol Hill, Seattle', status: 'paused', activeSessions: 0, totalSessions: 291 },
  { id: 'M004', businessName: 'Current Cafe', location: 'Pearl District, Portland', status: 'active', activeSessions: 15, totalSessions: 1204 },
  { id: 'M005', businessName: 'Charge & Dine', location: 'Fremont, Seattle', status: 'active', activeSessions: 6, totalSessions: 443 },
  { id: 'M006', businessName: 'FastCharge Premium', location: 'Bellevue, WA', status: 'flagged', activeSessions: 3, totalSessions: 156 },
  { id: 'M007', businessName: 'EV Lounge', location: 'South Lake Union, Seattle', status: 'active', activeSessions: 11, totalSessions: 678 },
  { id: 'M008', businessName: 'Power Station Cafe', location: 'Beaverton, OR', status: 'active', activeSessions: 9, totalSessions: 512 },
];

export function Merchants() {
  const [merchants, setMerchants] = useState(mockMerchants);
  const [searchTerm, setSearchTerm] = useState('');

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'paused':
        return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      case 'flagged':
        return 'text-red-700 bg-red-50 border-red-200';
      default:
        return 'text-neutral-700 bg-neutral-50 border-neutral-200';
    }
  };

  const handleDisable = (id: string) => {
    setMerchants((prev) =>
      prev.map((m) => (m.id === id ? { ...m, status: 'paused' as const, activeSessions: 0 } : m))
    );
  };

  const handleEnable = (id: string) => {
    setMerchants((prev) =>
      prev.map((m) => (m.id === id ? { ...m, status: 'active' as const } : m))
    );
  };

  const filteredMerchants = merchants.filter(
    (m) =>
      m.businessName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.location.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl text-neutral-900">Merchants</h1>
        <p className="text-sm text-neutral-600 mt-1">Manage and monitor merchant accounts</p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-neutral-400" />
          <input
            type="text"
            placeholder="Search merchants..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Merchants Table */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-neutral-50 border-b border-neutral-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Merchant ID
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Business Name
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Location
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Active Sessions
              </th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">
                Total Sessions
              </th>
              <th className="px-6 py-3 text-right text-xs text-neutral-600 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {filteredMerchants.map((merchant) => (
              <tr key={merchant.id} className="hover:bg-neutral-50">
                <td className="px-6 py-4 text-sm text-neutral-900">{merchant.id}</td>
                <td className="px-6 py-4 text-sm text-neutral-900">{merchant.businessName}</td>
                <td className="px-6 py-4 text-sm text-neutral-600">{merchant.location}</td>
                <td className="px-6 py-4">
                  <span
                    className={`inline-flex px-2.5 py-1 rounded-md text-xs border ${getStatusColor(
                      merchant.status
                    )}`}
                  >
                    {merchant.status.charAt(0).toUpperCase() + merchant.status.slice(1)}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-neutral-900">{merchant.activeSessions}</td>
                <td className="px-6 py-4 text-sm text-neutral-600">{merchant.totalSessions}</td>
                <td className="px-6 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button className="p-1.5 hover:bg-neutral-100 rounded text-neutral-600 hover:text-neutral-900">
                      <Eye className="w-4 h-4" />
                    </button>
                    {merchant.status === 'paused' ? (
                      <button
                        onClick={() => handleEnable(merchant.id)}
                        className="p-1.5 hover:bg-green-50 rounded text-green-600 hover:text-green-700"
                        title="Re-enable"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleDisable(merchant.id)}
                        className="p-1.5 hover:bg-red-50 rounded text-red-600 hover:text-red-700"
                        title="Disable"
                      >
                        <Ban className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredMerchants.length === 0 && (
        <div className="text-center py-12 text-neutral-500">No merchants found</div>
      )}
    </div>
  );
}
