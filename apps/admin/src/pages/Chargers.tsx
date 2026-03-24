import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Search,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Plus,
  X,
  Pencil,
  Trash2,
  ChevronDown,
} from 'lucide-react';
import { fetchAPI } from '../services/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ChargerListItem {
  id: string;
  name: string;
  address: string | null;
  city: string | null;
  state: string | null;
  network_name: string | null;
  power_kw: number | null;
  num_evse: number | null;
  status: string;
  pricing_per_kwh: number | null;
  connector_types: string[] | null;
  lat: number;
  lng: number;
  created_at: string | null;
  merchant_count: number;
}

interface LinkedMerchant {
  link_id: number;
  merchant_id: string;
  merchant_name: string | null;
  distance_m: number | null;
  walk_duration_s: number | null;
  exclusive_title: string | null;
  exclusive_description: string | null;
  is_primary: boolean;
}

interface ChargerDetail {
  id: string;
  external_id: string | null;
  name: string;
  network_name: string | null;
  lat: number;
  lng: number;
  address: string | null;
  city: string | null;
  state: string | null;
  zip_code: string | null;
  connector_types: string[] | null;
  power_kw: number | null;
  num_evse: number | null;
  is_public: boolean;
  access_code: string | null;
  pricing_per_kwh: number | null;
  pricing_source: string | null;
  nerava_score: number | null;
  status: string;
  last_verified_at: string | null;
  logo_url: string | null;
  created_at: string | null;
  updated_at: string | null;
  linked_merchants: LinkedMerchant[];
}

interface ChargerListResponse {
  chargers: ChargerListItem[];
  total: number;
  page: number;
  page_size: number;
}

interface ChargerFormData {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  lat: string;
  lng: string;
  network_name: string;
  connector_types: string;
  power_kw: string;
  num_evse: string;
  pricing_per_kwh: string;
  status: string;
}

const EMPTY_FORM: ChargerFormData = {
  id: '',
  name: '',
  address: '',
  city: '',
  state: '',
  zip_code: '',
  lat: '',
  lng: '',
  network_name: '',
  connector_types: '',
  power_kw: '',
  num_evse: '',
  pricing_per_kwh: '',
  status: 'available',
};

const NETWORKS = [
  '', 'Tesla', 'ChargePoint', 'EVgo', 'Electrify America', 'Blink', 'SemaConnect',
  'Flo', 'Shell Recharge', 'BP Pulse', 'EVCS', 'Other',
];

const US_STATES = [
  '', 'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS',
  'KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY',
  'NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY',
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function Chargers() {
  const [chargers, setChargers] = useState<ChargerListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 25;
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // Filters
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [networkFilter, setNetworkFilter] = useState('');
  const [stateFilter, setStateFilter] = useState('');

  // Sort
  const [sortField, setSortField] = useState<'name' | 'city' | 'network_name' | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  // Detail drawer
  const [selectedCharger, setSelectedCharger] = useState<ChargerDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Create/Edit modal
  const [showFormModal, setShowFormModal] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [formData, setFormData] = useState<ChargerFormData>(EMPTY_FORM);
  const [formError, setFormError] = useState('');
  const [formSaving, setFormSaving] = useState(false);

  // Delete confirmation
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Debounce timer ref
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ---------------------------------------------------------------------------
  // Data loading
  // ---------------------------------------------------------------------------

  const loadChargers = useCallback(async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams();
      qs.append('page', page.toString());
      qs.append('page_size', pageSize.toString());
      if (search) qs.append('search', search);
      if (networkFilter) qs.append('network', networkFilter);
      if (stateFilter) qs.append('state', stateFilter);

      const data = await fetchAPI<ChargerListResponse>(`/v1/admin/chargers?${qs.toString()}`);
      setChargers(data.chargers);
      setTotal(data.total);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Failed to load chargers:', err);
    } finally {
      setLoading(false);
    }
  }, [page, search, networkFilter, stateFilter]);

  useEffect(() => {
    loadChargers();
  }, [loadChargers]);

  // Debounced search
  const handleSearchInput = (value: string) => {
    setSearchInput(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setPage(1);
      setSearch(value);
    }, 400);
  };

  const loadChargerDetail = async (id: string) => {
    setDetailLoading(true);
    try {
      const data = await fetchAPI<ChargerDetail>(`/v1/admin/chargers/${id}`);
      setSelectedCharger(data);
    } catch (err) {
      console.error('Failed to load charger detail:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Sorting (client-side within current page)
  // ---------------------------------------------------------------------------

  const handleSort = (field: 'name' | 'city' | 'network_name') => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('asc');
    }
  };

  const sortedChargers = [...chargers].sort((a, b) => {
    if (!sortField) return 0;
    const aVal = (a[sortField] || '').toLowerCase();
    const bVal = (b[sortField] || '').toLowerCase();
    const cmp = aVal.localeCompare(bVal);
    return sortDir === 'asc' ? cmp : -cmp;
  });

  // ---------------------------------------------------------------------------
  // CRUD actions
  // ---------------------------------------------------------------------------

  const openCreateModal = () => {
    setFormMode('create');
    setFormData(EMPTY_FORM);
    setFormError('');
    setShowFormModal(true);
  };

  const openEditModal = () => {
    if (!selectedCharger) return;
    setFormMode('edit');
    setFormData({
      id: selectedCharger.id,
      name: selectedCharger.name,
      address: selectedCharger.address || '',
      city: selectedCharger.city || '',
      state: selectedCharger.state || '',
      zip_code: selectedCharger.zip_code || '',
      lat: selectedCharger.lat.toString(),
      lng: selectedCharger.lng.toString(),
      network_name: selectedCharger.network_name || '',
      connector_types: (selectedCharger.connector_types || []).join(', '),
      power_kw: selectedCharger.power_kw?.toString() || '',
      num_evse: selectedCharger.num_evse?.toString() || '',
      pricing_per_kwh: selectedCharger.pricing_per_kwh?.toString() || '',
      status: selectedCharger.status || 'available',
    });
    setFormError('');
    setShowFormModal(true);
  };

  const handleFormSubmit = async () => {
    setFormError('');

    if (!formData.name.trim()) {
      setFormError('Name is required');
      return;
    }
    if (!formData.lat || !formData.lng) {
      setFormError('Latitude and Longitude are required');
      return;
    }

    const connectorArr = formData.connector_types
      ? formData.connector_types.split(',').map((s) => s.trim()).filter(Boolean)
      : [];

    const payload: Record<string, unknown> = {
      name: formData.name.trim(),
      address: formData.address.trim() || null,
      city: formData.city.trim() || null,
      state: formData.state.trim() || null,
      zip_code: formData.zip_code.trim() || null,
      lat: parseFloat(formData.lat),
      lng: parseFloat(formData.lng),
      network_name: formData.network_name || null,
      connector_types: connectorArr.length > 0 ? connectorArr : null,
      power_kw: formData.power_kw ? parseFloat(formData.power_kw) : null,
      num_evse: formData.num_evse ? parseInt(formData.num_evse) : null,
      pricing_per_kwh: formData.pricing_per_kwh ? parseFloat(formData.pricing_per_kwh) : null,
      status: formData.status || 'available',
    };

    setFormSaving(true);
    try {
      if (formMode === 'create') {
        if (!formData.id.trim()) {
          setFormError('Charger ID is required');
          setFormSaving(false);
          return;
        }
        payload.id = formData.id.trim();
        await fetchAPI('/v1/admin/chargers', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      } else {
        await fetchAPI(`/v1/admin/chargers/${selectedCharger!.id}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
      }
      setShowFormModal(false);
      loadChargers();
      if (formMode === 'edit' && selectedCharger) {
        loadChargerDetail(selectedCharger.id);
      }
    } catch (err: any) {
      setFormError(err?.message || 'Failed to save charger');
    } finally {
      setFormSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedCharger) return;
    setDeleting(true);
    try {
      await fetchAPI(`/v1/admin/chargers/${selectedCharger.id}`, {
        method: 'DELETE',
      });
      setShowDeleteConfirm(false);
      setSelectedCharger(null);
      loadChargers();
    } catch (err: any) {
      alert(`Delete failed: ${err?.message || 'Unknown error'}`);
    } finally {
      setDeleting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  const totalPages = Math.ceil(total / pageSize);

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      available: 'bg-green-50 text-green-700 border-green-200',
      offline: 'bg-neutral-50 text-neutral-600 border-neutral-200',
      removed: 'bg-red-50 text-red-700 border-red-200',
      maintenance: 'bg-amber-50 text-amber-700 border-amber-200',
    };
    return (
      <span className={`inline-flex px-2 py-0.5 rounded text-xs border ${colors[status] || colors.offline}`}>
        {status}
      </span>
    );
  };

  const SortHeader = ({ field, label }: { field: 'name' | 'city' | 'network_name'; label: string }) => (
    <th
      className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider cursor-pointer select-none hover:text-neutral-700"
      onClick={() => handleSort(field)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {sortField === field && (
          <ChevronDown className={`w-3 h-3 transition-transform ${sortDir === 'desc' ? 'rotate-180' : ''}`} />
        )}
      </span>
    </th>
  );

  const handleFilterChange = (setter: (v: string) => void) => (e: React.ChangeEvent<HTMLSelectElement>) => {
    setter(e.target.value);
    setPage(1);
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl text-neutral-900">Charger Management</h1>
          <p className="text-sm text-neutral-500 mt-1">
            {total} chargers &middot; Last updated: {lastRefresh.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={openCreateModal}
            className="flex items-center gap-1.5 px-3 py-2 text-sm bg-neutral-900 text-white rounded-lg hover:bg-neutral-800"
          >
            <Plus className="w-4 h-4" /> Add Charger
          </button>
          <button onClick={loadChargers} className="p-2 hover:bg-neutral-100 rounded-lg" title="Refresh">
            <RefreshCw className="w-4 h-4 text-neutral-600" />
          </button>
        </div>
      </div>

      {/* Filters row */}
      <div className="flex items-end gap-3 mb-6 flex-wrap">
        <div className="flex-1 min-w-[200px]">
          <label className="block text-xs text-neutral-500 mb-1">Search</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
            <input
              type="text"
              placeholder="Search by name or address..."
              value={searchInput}
              onChange={(e) => handleSearchInput(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
            />
          </div>
        </div>
        <div>
          <label className="block text-xs text-neutral-500 mb-1">Network</label>
          <select
            value={networkFilter}
            onChange={handleFilterChange(setNetworkFilter)}
            className="px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white"
          >
            <option value="">All Networks</option>
            {NETWORKS.filter(Boolean).map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-neutral-500 mb-1">State</label>
          <select
            value={stateFilter}
            onChange={handleFilterChange(setStateFilter)}
            className="px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white"
          >
            <option value="">All States</option>
            {US_STATES.filter(Boolean).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        {(searchInput || networkFilter || stateFilter) && (
          <button
            onClick={() => {
              setSearchInput('');
              setSearch('');
              setNetworkFilter('');
              setStateFilter('');
              setPage(1);
            }}
            className="px-3 py-2 text-sm text-neutral-500 hover:text-neutral-700"
          >
            Clear
          </button>
        )}
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-xs text-neutral-500 mb-1">Total Chargers</div>
          <div className="text-xl text-neutral-900 font-medium">{total}</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-xs text-neutral-500 mb-1">Networks</div>
          <div className="text-xl text-neutral-900 font-medium">
            {new Set(chargers.map((c) => c.network_name).filter(Boolean)).size}
          </div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-xs text-neutral-500 mb-1">States</div>
          <div className="text-xl text-neutral-900 font-medium">
            {new Set(chargers.map((c) => c.state).filter(Boolean)).size}
          </div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-xs text-neutral-500 mb-1">With Merchants</div>
          <div className="text-xl text-neutral-900 font-medium">
            {chargers.filter((c) => c.merchant_count > 0).length}
          </div>
        </div>
      </div>

      {/* Main content: table + optional detail drawer */}
      <div className="flex gap-6">
        {/* Table */}
        <div className={`bg-white border border-neutral-200 rounded-lg overflow-hidden ${selectedCharger ? 'flex-1 min-w-0' : 'w-full'}`}>
          {loading ? (
            <div className="p-12 text-center text-neutral-400">Loading chargers...</div>
          ) : chargers.length === 0 ? (
            <div className="p-12 text-center text-neutral-400">No chargers found</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-neutral-50 border-b border-neutral-200">
                  <tr>
                    <SortHeader field="name" label="Name" />
                    <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Address</th>
                    <SortHeader field="city" label="City" />
                    <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">State</th>
                    <SortHeader field="network_name" label="Network" />
                    <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Power</th>
                    <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Stalls</th>
                    <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Merchants</th>
                    <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Pricing</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100">
                  {sortedChargers.map((c) => (
                    <tr
                      key={c.id}
                      className={`cursor-pointer transition-colors ${selectedCharger?.id === c.id ? 'bg-neutral-100' : 'hover:bg-neutral-50'}`}
                      onClick={() => loadChargerDetail(c.id)}
                    >
                      <td className="px-4 py-3 text-sm text-neutral-900 font-medium max-w-[200px] truncate">{c.name}</td>
                      <td className="px-4 py-3 text-sm text-neutral-600 max-w-[180px] truncate">{c.address || '-'}</td>
                      <td className="px-4 py-3 text-sm text-neutral-600">{c.city || '-'}</td>
                      <td className="px-4 py-3 text-sm text-neutral-600">{c.state || '-'}</td>
                      <td className="px-4 py-3 text-sm text-neutral-600">{c.network_name || '-'}</td>
                      <td className="px-4 py-3 text-sm text-neutral-900">{c.power_kw != null ? `${c.power_kw} kW` : '-'}</td>
                      <td className="px-4 py-3 text-sm text-neutral-900">{c.num_evse ?? '-'}</td>
                      <td className="px-4 py-3">{getStatusBadge(c.status)}</td>
                      <td className="px-4 py-3 text-sm text-neutral-900">{c.merchant_count}</td>
                      <td className="px-4 py-3 text-sm text-neutral-600">
                        {c.pricing_per_kwh != null ? `$${c.pricing_per_kwh.toFixed(2)}/kWh` : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Detail drawer */}
        {selectedCharger && (
          <div className="w-96 flex-shrink-0 bg-white border border-neutral-200 rounded-lg overflow-hidden">
            <div className="p-4 border-b border-neutral-200 flex items-center justify-between">
              <h2 className="text-sm font-medium text-neutral-900">Charger Detail</h2>
              <button onClick={() => setSelectedCharger(null)} className="p-1 hover:bg-neutral-100 rounded">
                <X className="w-4 h-4 text-neutral-500" />
              </button>
            </div>

            {detailLoading ? (
              <div className="p-8 text-center text-neutral-400 text-sm">Loading...</div>
            ) : (
              <div className="p-4 space-y-4 overflow-y-auto max-h-[calc(100vh-220px)]">
                {/* Basic info */}
                <div>
                  <h3 className="text-base font-medium text-neutral-900 mb-1">{selectedCharger.name}</h3>
                  <p className="text-xs text-neutral-400 font-mono">{selectedCharger.id}</p>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <div className="text-xs text-neutral-500">Network</div>
                    <div className="text-neutral-900">{selectedCharger.network_name || '-'}</div>
                  </div>
                  <div>
                    <div className="text-xs text-neutral-500">Status</div>
                    <div>{getStatusBadge(selectedCharger.status)}</div>
                  </div>
                  <div>
                    <div className="text-xs text-neutral-500">Power</div>
                    <div className="text-neutral-900">
                      {selectedCharger.power_kw != null ? `${selectedCharger.power_kw} kW` : '-'}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-neutral-500">Stalls</div>
                    <div className="text-neutral-900">{selectedCharger.num_evse ?? '-'}</div>
                  </div>
                  <div>
                    <div className="text-xs text-neutral-500">Pricing</div>
                    <div className="text-neutral-900">
                      {selectedCharger.pricing_per_kwh != null
                        ? `$${selectedCharger.pricing_per_kwh.toFixed(2)}/kWh`
                        : '-'}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-neutral-500">Public</div>
                    <div className="text-neutral-900">{selectedCharger.is_public ? 'Yes' : 'No'}</div>
                  </div>
                </div>

                {/* Location */}
                <div className="border-t border-neutral-100 pt-3">
                  <div className="text-xs text-neutral-500 mb-1">Location</div>
                  <div className="text-sm text-neutral-900">
                    {[selectedCharger.address, selectedCharger.city, selectedCharger.state, selectedCharger.zip_code]
                      .filter(Boolean)
                      .join(', ') || '-'}
                  </div>
                  <div className="text-xs text-neutral-400 mt-1">
                    {selectedCharger.lat.toFixed(6)}, {selectedCharger.lng.toFixed(6)}
                  </div>
                </div>

                {/* Connectors */}
                {selectedCharger.connector_types && selectedCharger.connector_types.length > 0 && (
                  <div className="border-t border-neutral-100 pt-3">
                    <div className="text-xs text-neutral-500 mb-1">Connectors</div>
                    <div className="flex flex-wrap gap-1">
                      {selectedCharger.connector_types.map((ct, i) => (
                        <span
                          key={i}
                          className="inline-flex px-2 py-0.5 rounded text-xs bg-neutral-100 text-neutral-700"
                        >
                          {ct}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Nerava Score */}
                {selectedCharger.nerava_score != null && (
                  <div className="border-t border-neutral-100 pt-3">
                    <div className="text-xs text-neutral-500 mb-1">Nerava Score</div>
                    <div className="text-sm text-neutral-900 font-medium">{selectedCharger.nerava_score}</div>
                  </div>
                )}

                {/* Linked merchants */}
                <div className="border-t border-neutral-100 pt-3">
                  <div className="text-xs text-neutral-500 mb-2">
                    Linked Merchants ({selectedCharger.linked_merchants.length})
                  </div>
                  {selectedCharger.linked_merchants.length === 0 ? (
                    <p className="text-xs text-neutral-400">No merchants linked</p>
                  ) : (
                    <div className="space-y-2">
                      {selectedCharger.linked_merchants.map((m) => (
                        <div
                          key={m.link_id}
                          className="bg-neutral-50 rounded-lg p-2.5 text-sm"
                        >
                          <div className="font-medium text-neutral-900 text-sm">
                            {m.merchant_name || m.merchant_id}
                          </div>
                          <div className="text-xs text-neutral-500 mt-0.5">
                            {m.distance_m != null ? `${Math.round(m.distance_m)}m away` : ''}
                            {m.walk_duration_s != null ? ` · ${Math.round(m.walk_duration_s / 60)} min walk` : ''}
                            {m.is_primary && (
                              <span className="ml-1 text-green-600 font-medium">Primary</span>
                            )}
                          </div>
                          {m.exclusive_title && (
                            <div className="text-xs text-amber-700 mt-0.5">
                              Exclusive: {m.exclusive_title}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Timestamps */}
                <div className="border-t border-neutral-100 pt-3 text-xs text-neutral-400 space-y-1">
                  {selectedCharger.created_at && (
                    <div>Created: {new Date(selectedCharger.created_at).toLocaleString()}</div>
                  )}
                  {selectedCharger.updated_at && (
                    <div>Updated: {new Date(selectedCharger.updated_at).toLocaleString()}</div>
                  )}
                  {selectedCharger.last_verified_at && (
                    <div>Verified: {new Date(selectedCharger.last_verified_at).toLocaleString()}</div>
                  )}
                </div>

                {/* Action buttons */}
                <div className="border-t border-neutral-100 pt-3 flex gap-2">
                  <button
                    onClick={openEditModal}
                    className="flex items-center gap-1.5 px-3 py-2 text-sm text-neutral-700 hover:bg-neutral-100 rounded-lg border border-neutral-200"
                  >
                    <Pencil className="w-3.5 h-3.5" /> Edit
                  </button>
                  <button
                    onClick={() => setShowDeleteConfirm(true)}
                    className="flex items-center gap-1.5 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg border border-red-200"
                  >
                    <Trash2 className="w-3.5 h-3.5" /> Delete
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-neutral-500">
            Showing {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, total)} of {total}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-2 rounded-lg hover:bg-neutral-100 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm text-neutral-600">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="p-2 rounded-lg hover:bg-neutral-100 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ================================================================= */}
      {/* Create / Edit Modal                                               */}
      {/* ================================================================= */}
      {showFormModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          onClick={() => setShowFormModal(false)}
        >
          <div
            className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[85vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-5 border-b border-neutral-200 flex items-center justify-between">
              <h2 className="text-lg font-medium text-neutral-900">
                {formMode === 'create' ? 'Add Charger' : 'Edit Charger'}
              </h2>
              <button onClick={() => setShowFormModal(false)} className="p-1 hover:bg-neutral-100 rounded">
                <X className="w-5 h-5 text-neutral-500" />
              </button>
            </div>

            <div className="p-5 space-y-4">
              {formError && (
                <div className="bg-red-50 text-red-700 text-sm rounded-lg px-3 py-2 border border-red-200">
                  {formError}
                </div>
              )}

              {formMode === 'create' && (
                <div>
                  <label className="block text-xs text-neutral-500 mb-1">Charger ID *</label>
                  <input
                    type="text"
                    value={formData.id}
                    onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                    placeholder="e.g. ch_tesla_001"
                    className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs text-neutral-500 mb-1">Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Charger name"
                  className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-neutral-500 mb-1">Address</label>
                  <input
                    type="text"
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
                  />
                </div>
                <div>
                  <label className="block text-xs text-neutral-500 mb-1">City</label>
                  <input
                    type="text"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-neutral-500 mb-1">State</label>
                  <select
                    value={formData.state}
                    onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
                  >
                    <option value="">--</option>
                    {US_STATES.filter(Boolean).map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-neutral-500 mb-1">Zip Code</label>
                  <input
                    type="text"
                    value={formData.zip_code}
                    onChange={(e) => setFormData({ ...formData, zip_code: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
                  />
                </div>
                <div>
                  <label className="block text-xs text-neutral-500 mb-1">Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
                  >
                    <option value="available">Available</option>
                    <option value="offline">Offline</option>
                    <option value="maintenance">Maintenance</option>
                    <option value="removed">Removed</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-neutral-500 mb-1">Latitude *</label>
                  <input
                    type="text"
                    value={formData.lat}
                    onChange={(e) => setFormData({ ...formData, lat: e.target.value })}
                    placeholder="e.g. 29.7604"
                    className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
                  />
                </div>
                <div>
                  <label className="block text-xs text-neutral-500 mb-1">Longitude *</label>
                  <input
                    type="text"
                    value={formData.lng}
                    onChange={(e) => setFormData({ ...formData, lng: e.target.value })}
                    placeholder="e.g. -95.3698"
                    className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs text-neutral-500 mb-1">Network</label>
                <select
                  value={formData.network_name}
                  onChange={(e) => setFormData({ ...formData, network_name: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
                >
                  <option value="">-- Select --</option>
                  {NETWORKS.filter(Boolean).map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs text-neutral-500 mb-1">Connector Types</label>
                <input
                  type="text"
                  value={formData.connector_types}
                  onChange={(e) => setFormData({ ...formData, connector_types: e.target.value })}
                  placeholder="e.g. CCS, Tesla, CHAdeMO"
                  className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
                />
                <p className="text-xs text-neutral-400 mt-0.5">Comma-separated</p>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-neutral-500 mb-1">Power (kW)</label>
                  <input
                    type="number"
                    value={formData.power_kw}
                    onChange={(e) => setFormData({ ...formData, power_kw: e.target.value })}
                    placeholder="e.g. 150"
                    className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
                  />
                </div>
                <div>
                  <label className="block text-xs text-neutral-500 mb-1">Num Stalls</label>
                  <input
                    type="number"
                    value={formData.num_evse}
                    onChange={(e) => setFormData({ ...formData, num_evse: e.target.value })}
                    placeholder="e.g. 8"
                    className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
                  />
                </div>
                <div>
                  <label className="block text-xs text-neutral-500 mb-1">$/kWh</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.pricing_per_kwh}
                    onChange={(e) => setFormData({ ...formData, pricing_per_kwh: e.target.value })}
                    placeholder="e.g. 0.32"
                    className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
                  />
                </div>
              </div>
            </div>

            <div className="p-5 border-t border-neutral-200 flex justify-end gap-2">
              <button
                onClick={() => setShowFormModal(false)}
                className="px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-100 rounded-lg border border-neutral-200"
              >
                Cancel
              </button>
              <button
                onClick={handleFormSubmit}
                disabled={formSaving}
                className="px-4 py-2 text-sm bg-neutral-900 text-white rounded-lg hover:bg-neutral-800 disabled:opacity-50"
              >
                {formSaving ? 'Saving...' : formMode === 'create' ? 'Create Charger' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ================================================================= */}
      {/* Delete Confirmation Dialog                                        */}
      {/* ================================================================= */}
      {showDeleteConfirm && selectedCharger && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          onClick={() => setShowDeleteConfirm(false)}
        >
          <div
            className="bg-white rounded-xl shadow-xl w-full max-w-sm"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-5">
              <h2 className="text-lg font-medium text-neutral-900 mb-2">Delete Charger</h2>
              <p className="text-sm text-neutral-600">
                Are you sure you want to delete <strong>{selectedCharger.name}</strong>? This will mark the charger as
                removed (soft delete).
              </p>
            </div>
            <div className="p-5 border-t border-neutral-200 flex justify-end gap-2">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-100 rounded-lg border border-neutral-200"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
