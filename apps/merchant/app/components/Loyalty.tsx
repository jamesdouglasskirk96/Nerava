import { useEffect, useState } from 'react';
import { Plus, ToggleLeft, ToggleRight } from 'lucide-react';
import {
  getLoyaltyCards,
  createLoyaltyCard,
  updateLoyaltyCard,
  getLoyaltyCustomers,
  getLoyaltyStats,
  type LoyaltyCard,
  type LoyaltyCustomer,
  type LoyaltyStats,
} from '../services/api';

export function Loyalty() {
  const merchantId = localStorage.getItem('merchant_id') || '';
  const [cards, setCards] = useState<LoyaltyCard[]>([]);
  const [customers, setCustomers] = useState<LoyaltyCustomer[]>([]);
  const [stats, setStats] = useState<LoyaltyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Create form state
  const [showCreate, setShowCreate] = useState(false);
  const [formName, setFormName] = useState('');
  const [formVisits, setFormVisits] = useState(5);
  const [formRewardCents, setFormRewardCents] = useState(500);
  const [formRewardDesc, setFormRewardDesc] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!merchantId) return;
    loadAll();
  }, [merchantId]);

  async function loadAll() {
    setLoading(true);
    setError('');
    try {
      const [cardsData, statsData, custData] = await Promise.all([
        getLoyaltyCards(merchantId),
        getLoyaltyStats(merchantId),
        getLoyaltyCustomers(merchantId),
      ]);
      setCards(cardsData);
      setStats(statsData);
      setCustomers(custData.customers);
    } catch (e: any) {
      setError(e.message || 'Failed to load loyalty data');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!formName.trim() || formVisits < 1) return;
    setSaving(true);
    try {
      await createLoyaltyCard(merchantId, {
        program_name: formName,
        visits_required: formVisits,
        reward_cents: formRewardCents,
        reward_description: formRewardDesc || undefined,
      });
      setShowCreate(false);
      setFormName('');
      setFormVisits(5);
      setFormRewardCents(500);
      setFormRewardDesc('');
      await loadAll();
    } catch (e: any) {
      setError(e.message || 'Failed to create card');
    } finally {
      setSaving(false);
    }
  }

  async function handleToggle(card: LoyaltyCard) {
    try {
      await updateLoyaltyCard(merchantId, card.id, { is_active: !card.is_active });
      await loadAll();
    } catch (e: any) {
      setError(e.message || 'Failed to update card');
    }
  }

  if (!merchantId) {
    return <p className="text-neutral-500 p-8">No merchant selected.</p>;
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-neutral-900">Loyalty</h1>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-neutral-900 text-white rounded-lg hover:bg-neutral-800 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create Punch Card
        </button>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm">{error}</div>
      )}

      {/* Stats Row */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Enrolled Drivers" value={stats.enrolled_drivers} />
          <StatCard label="Total Visits" value={stats.total_visits} />
          <StatCard label="Rewards Unlocked" value={stats.rewards_unlocked} />
          <StatCard label="Rewards Claimed" value={stats.rewards_claimed} />
        </div>
      )}

      {/* Create Form */}
      {showCreate && (
        <div className="bg-white border border-neutral-200 rounded-xl p-6 space-y-4">
          <h2 className="text-lg font-medium text-neutral-900">New Punch Card Program</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">Program Name</label>
              <input
                type="text"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="e.g., Coffee Loyalty Card"
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">Visits Required</label>
              <input
                type="number"
                value={formVisits}
                onChange={(e) => setFormVisits(parseInt(e.target.value) || 1)}
                min={1}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">Reward Amount ($)</label>
              <input
                type="number"
                value={formRewardCents / 100}
                onChange={(e) => setFormRewardCents(Math.round(parseFloat(e.target.value) * 100) || 0)}
                step="0.50"
                min={0}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">Reward Description</label>
              <input
                type="text"
                value={formRewardDesc}
                onChange={(e) => setFormRewardDesc(e.target.value)}
                placeholder="e.g., Free medium coffee"
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900"
              />
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleCreate}
              disabled={saving || !formName.trim()}
              className="px-4 py-2 bg-neutral-900 text-white rounded-lg hover:bg-neutral-800 disabled:opacity-50 transition-colors"
            >
              {saving ? 'Creating...' : 'Create'}
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="px-4 py-2 text-neutral-600 hover:text-neutral-900 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Cards List */}
      {loading ? (
        <div className="text-neutral-500 text-center py-12">Loading...</div>
      ) : cards.length === 0 && !showCreate ? (
        <div className="text-center py-12 bg-white border border-neutral-200 rounded-xl">
          <p className="text-neutral-500 mb-4">No punch card programs yet.</p>
          <button
            onClick={() => setShowCreate(true)}
            className="text-neutral-900 underline hover:no-underline"
          >
            Create your first one
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {cards.map((card) => (
            <div
              key={card.id}
              className="bg-white border border-neutral-200 rounded-xl p-5 flex items-center justify-between"
            >
              <div>
                <h3 className="font-medium text-neutral-900">{card.program_name}</h3>
                <p className="text-sm text-neutral-500 mt-1">
                  {card.visits_required} visits = ${(card.reward_cents / 100).toFixed(2)} off
                  {card.reward_description && ` — ${card.reward_description}`}
                </p>
              </div>
              <button
                onClick={() => handleToggle(card)}
                className="flex items-center gap-2 text-sm"
                title={card.is_active ? 'Deactivate' : 'Activate'}
              >
                {card.is_active ? (
                  <ToggleRight className="w-6 h-6 text-green-600" />
                ) : (
                  <ToggleLeft className="w-6 h-6 text-neutral-400" />
                )}
                <span className={card.is_active ? 'text-green-600' : 'text-neutral-400'}>
                  {card.is_active ? 'Active' : 'Inactive'}
                </span>
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Customer Table */}
      {customers.length > 0 && (
        <div>
          <h2 className="text-lg font-medium text-neutral-900 mb-4">Loyalty Customers</h2>
          <div className="bg-white border border-neutral-200 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-neutral-50 border-b border-neutral-200">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-neutral-600">Driver</th>
                  <th className="text-left px-4 py-3 font-medium text-neutral-600">Card</th>
                  <th className="text-left px-4 py-3 font-medium text-neutral-600">Progress</th>
                  <th className="text-left px-4 py-3 font-medium text-neutral-600">Last Visit</th>
                  <th className="text-left px-4 py-3 font-medium text-neutral-600">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {customers.map((c, i) => (
                  <tr key={i} className="hover:bg-neutral-50">
                    <td className="px-4 py-3 text-neutral-900">{c.driver_id_anonymized}</td>
                    <td className="px-4 py-3 text-neutral-600">{c.card_name}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-neutral-100 rounded-full overflow-hidden max-w-[120px]">
                          <div
                            className="h-full bg-neutral-900 rounded-full transition-all"
                            style={{ width: `${Math.min(100, (c.visit_count / c.visits_required) * 100)}%` }}
                          />
                        </div>
                        <span className="text-neutral-600 whitespace-nowrap">
                          {c.visit_count}/{c.visits_required}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-neutral-500">
                      {c.last_visit_at ? new Date(c.last_visit_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge unlocked={c.reward_unlocked} claimed={c.reward_claimed} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white border border-neutral-200 rounded-xl p-4">
      <p className="text-sm text-neutral-500">{label}</p>
      <p className="text-2xl font-semibold text-neutral-900 mt-1">{value}</p>
    </div>
  );
}

function StatusBadge({ unlocked, claimed }: { unlocked: boolean; claimed: boolean }) {
  if (claimed) {
    return <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Claimed</span>;
  }
  if (unlocked) {
    return <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Unlocked</span>;
  }
  return <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-neutral-100 text-neutral-600">In Progress</span>;
}
