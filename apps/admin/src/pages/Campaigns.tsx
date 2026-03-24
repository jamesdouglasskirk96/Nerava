import { useState, useEffect, useCallback } from 'react'
import { RefreshCw, Plus, X, ChevronLeft, ChevronRight, Play, Pause, Pencil, ArrowLeft } from 'lucide-react'
import { fetchAPI } from '../services/api'

// --- Types ---

interface CampaignRules {
  charger_ids: string[] | null
  charger_networks: string[] | null
  zone_ids: string[] | null
  geo_center_lat: number | null
  geo_center_lng: number | null
  geo_radius_m: number | null
  time_start: string | null
  time_end: string | null
  days_of_week: number[] | null
  min_duration_minutes: number | null
  max_duration_minutes: number | null
  min_power_kw: number | null
  connector_types: string[] | null
  driver_session_count_min: number | null
  driver_session_count_max: number | null
  driver_allowlist: string[] | null
}

interface Campaign {
  id: string
  sponsor_name: string
  sponsor_email: string | null
  name: string
  description: string | null
  campaign_type: string
  status: string
  priority: number
  budget_cents: number
  spent_cents: number
  cost_per_session_cents: number
  max_sessions: number | null
  sessions_granted: number
  start_date: string | null
  end_date: string | null
  auto_renew: boolean
  rules: CampaignRules
  funding_status: string
  max_grants_per_driver_per_day: number | null
  max_grants_per_driver_per_campaign: number | null
  max_grants_per_driver_per_charger: number | null
  created_at: string | null
  updated_at: string | null
}

interface Grant {
  id: string
  session_event_id: string
  campaign_id: string
  driver_user_id: number
  amount_cents: number
  status: string
  granted_at: string | null
  created_at: string | null
  charger_id: string | null
  duration_minutes: number | null
}

type StatusFilter = 'all' | 'active' | 'paused' | 'completed' | 'draft'

// --- Helpers ---

const cents = (c: number) => `$${(c / 100).toFixed(2)}`

const formatDate = (iso: string | null) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const formatDateTime = (iso: string | null) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}

const statusBadge = (status: string) => {
  const styles: Record<string, string> = {
    active: 'bg-green-50 text-green-700 border-green-200',
    paused: 'bg-amber-50 text-amber-700 border-amber-200',
    completed: 'bg-neutral-100 text-neutral-600 border-neutral-200',
    draft: 'bg-blue-50 text-blue-700 border-blue-200',
    exhausted: 'bg-red-50 text-red-700 border-red-200',
  }
  const cls = styles[status] || 'bg-neutral-50 text-neutral-600 border-neutral-200'
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-xs border capitalize ${cls}`}>
      {status}
    </span>
  )
}

// --- Create/Edit Modal ---

interface CampaignFormData {
  name: string
  sponsor_name: string
  budget_dollars: string
  reward_dollars: string
  status: 'draft' | 'active'
  start_date: string
  end_date: string
  description: string
  charger_ids: string
  charger_networks: string
  zone_ids: string
}

const emptyForm: CampaignFormData = {
  name: '',
  sponsor_name: '',
  budget_dollars: '',
  reward_dollars: '',
  status: 'draft',
  start_date: new Date().toISOString().slice(0, 10),
  end_date: '',
  description: '',
  charger_ids: '',
  charger_networks: '',
  zone_ids: '',
}

function CampaignModal({
  campaign,
  onClose,
  onSaved,
}: {
  campaign: Campaign | null // null = create new
  onClose: () => void
  onSaved: () => void
}) {
  const isEdit = !!campaign
  const [form, setForm] = useState<CampaignFormData>(() => {
    if (!campaign) return emptyForm
    return {
      name: campaign.name,
      sponsor_name: campaign.sponsor_name,
      budget_dollars: (campaign.budget_cents / 100).toFixed(2),
      reward_dollars: (campaign.cost_per_session_cents / 100).toFixed(2),
      status: campaign.status === 'active' ? 'active' : 'draft',
      start_date: campaign.start_date ? campaign.start_date.slice(0, 10) : '',
      end_date: campaign.end_date ? campaign.end_date.slice(0, 10) : '',
      description: campaign.description || '',
      charger_ids: campaign.rules?.charger_ids?.join(', ') || '',
      charger_networks: campaign.rules?.charger_networks?.join(', ') || '',
      zone_ids: campaign.rules?.zone_ids?.join(', ') || '',
    }
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const set = (field: keyof CampaignFormData, value: string) =>
    setForm(prev => ({ ...prev, [field]: value }))

  const parseList = (val: string): string[] | undefined => {
    const items = val.split(',').map(s => s.trim()).filter(Boolean)
    return items.length > 0 ? items : undefined
  }

  const handleSave = async () => {
    if (!form.name || !form.sponsor_name || !form.budget_dollars || !form.reward_dollars) {
      setError('Name, sponsor, budget, and reward are required.')
      return
    }
    setSaving(true)
    setError('')
    try {
      const budgetCents = Math.round(parseFloat(form.budget_dollars) * 100)
      const rewardCents = Math.round(parseFloat(form.reward_dollars) * 100)

      if (isEdit && campaign) {
        // PUT update
        const body: Record<string, any> = {
          name: form.name,
          description: form.description || undefined,
          budget_cents: budgetCents,
          cost_per_session_cents: rewardCents,
          start_date: form.start_date || undefined,
          end_date: form.end_date || undefined,
          rules: {
            charger_ids: parseList(form.charger_ids) || null,
            charger_networks: parseList(form.charger_networks) || null,
            zone_ids: parseList(form.zone_ids) || null,
          },
        }
        await fetchAPI(`/v1/campaigns/${campaign.id}`, {
          method: 'PUT',
          body: JSON.stringify(body),
        })
      } else {
        // POST create
        const body: Record<string, any> = {
          sponsor_name: form.sponsor_name,
          name: form.name,
          description: form.description || undefined,
          budget_cents: budgetCents,
          cost_per_session_cents: rewardCents,
          start_date: form.start_date,
          end_date: form.end_date || undefined,
          rules: {
            charger_ids: parseList(form.charger_ids) || null,
            charger_networks: parseList(form.charger_networks) || null,
            zone_ids: parseList(form.zone_ids) || null,
          },
        }
        const result: any = await fetchAPI('/v1/campaigns', {
          method: 'POST',
          body: JSON.stringify(body),
        })
        // Activate immediately if requested
        if (form.status === 'active' && result?.campaign?.id) {
          await fetchAPI(`/v1/campaigns/${result.campaign.id}/activate`, {
            method: 'POST',
          })
        }
      }
      onSaved()
      onClose()
    } catch (err: any) {
      setError(err.message || 'Failed to save campaign')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-neutral-200">
          <h2 className="text-lg text-neutral-900">{isEdit ? 'Edit Campaign' : 'Create Campaign'}</h2>
          <button onClick={onClose} className="p-1 hover:bg-neutral-100 rounded-lg">
            <X className="w-5 h-5 text-neutral-400" />
          </button>
        </div>

        <div className="px-6 py-4 space-y-4">
          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs text-neutral-500 mb-1">Campaign Name *</label>
            <input
              type="text"
              value={form.name}
              onChange={e => set('name', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-neutral-300"
              placeholder="e.g. Spring Charging Bonus"
            />
          </div>

          <div>
            <label className="block text-xs text-neutral-500 mb-1">Sponsor Name *</label>
            <input
              type="text"
              value={form.sponsor_name}
              onChange={e => set('sponsor_name', e.target.value)}
              disabled={isEdit}
              className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-neutral-300 disabled:bg-neutral-50 disabled:text-neutral-400"
              placeholder="e.g. EVject"
            />
          </div>

          <div>
            <label className="block text-xs text-neutral-500 mb-1">Description</label>
            <textarea
              value={form.description}
              onChange={e => set('description', e.target.value)}
              rows={2}
              className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-neutral-300 resize-none"
              placeholder="Optional description"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-neutral-500 mb-1">Budget ($) *</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.budget_dollars}
                onChange={e => set('budget_dollars', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-neutral-300"
                placeholder="500.00"
              />
            </div>
            <div>
              <label className="block text-xs text-neutral-500 mb-1">Reward per session ($) *</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.reward_dollars}
                onChange={e => set('reward_dollars', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-neutral-300"
                placeholder="2.00"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-neutral-500 mb-1">Start Date</label>
              <input
                type="date"
                value={form.start_date}
                onChange={e => set('start_date', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-neutral-300"
              />
            </div>
            <div>
              <label className="block text-xs text-neutral-500 mb-1">End Date</label>
              <input
                type="date"
                value={form.end_date}
                onChange={e => set('end_date', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-neutral-300"
              />
            </div>
          </div>

          {!isEdit && (
            <div>
              <label className="block text-xs text-neutral-500 mb-1">Initial Status</label>
              <select
                value={form.status}
                onChange={e => set('status', e.target.value as 'draft' | 'active')}
                className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-neutral-300"
              >
                <option value="draft">Draft</option>
                <option value="active">Active</option>
              </select>
            </div>
          )}

          <div className="pt-2 border-t border-neutral-100">
            <p className="text-xs text-neutral-500 mb-3">Targeting Rules (comma-separated)</p>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-neutral-500 mb-1">Charger IDs</label>
                <input
                  type="text"
                  value={form.charger_ids}
                  onChange={e => set('charger_ids', e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-neutral-300"
                  placeholder="charger_1, charger_2"
                />
              </div>
              <div>
                <label className="block text-xs text-neutral-500 mb-1">Charger Networks</label>
                <input
                  type="text"
                  value={form.charger_networks}
                  onChange={e => set('charger_networks', e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-neutral-300"
                  placeholder="Tesla, ChargePoint"
                />
              </div>
              <div>
                <label className="block text-xs text-neutral-500 mb-1">Zone IDs</label>
                <input
                  type="text"
                  value={form.zone_ids}
                  onChange={e => set('zone_ids', e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-neutral-300"
                  placeholder="zone_1, zone_2"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 px-6 py-4 border-t border-neutral-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-100 rounded-lg"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-sm bg-neutral-900 text-white rounded-lg hover:bg-neutral-800 disabled:opacity-50"
          >
            {saving ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Campaign'}
          </button>
        </div>
      </div>
    </div>
  )
}

// --- Targeting Rules Display ---

function RulesDisplay({ rules }: { rules: CampaignRules }) {
  const entries: { label: string; value: string }[] = []

  if (rules.charger_ids?.length)
    entries.push({ label: 'Charger IDs', value: rules.charger_ids.join(', ') })
  if (rules.charger_networks?.length)
    entries.push({ label: 'Networks', value: rules.charger_networks.join(', ') })
  if (rules.zone_ids?.length)
    entries.push({ label: 'Zones', value: rules.zone_ids.join(', ') })
  if (rules.geo_center_lat != null && rules.geo_center_lng != null)
    entries.push({ label: 'Geo Center', value: `${rules.geo_center_lat}, ${rules.geo_center_lng}` })
  if (rules.geo_radius_m != null)
    entries.push({ label: 'Geo Radius', value: `${rules.geo_radius_m}m` })
  if (rules.time_start)
    entries.push({ label: 'Time Window', value: `${rules.time_start} - ${rules.time_end || '...'}` })
  if (rules.days_of_week?.length)
    entries.push({ label: 'Days', value: rules.days_of_week.map(d => ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][d] || d).join(', ') })
  if (rules.min_duration_minutes != null)
    entries.push({ label: 'Min Duration', value: `${rules.min_duration_minutes} min` })
  if (rules.max_duration_minutes != null)
    entries.push({ label: 'Max Duration', value: `${rules.max_duration_minutes} min` })
  if (rules.min_power_kw != null)
    entries.push({ label: 'Min Power', value: `${rules.min_power_kw} kW` })
  if (rules.connector_types?.length)
    entries.push({ label: 'Connectors', value: rules.connector_types.join(', ') })
  if (rules.driver_session_count_min != null)
    entries.push({ label: 'Min Driver Sessions', value: String(rules.driver_session_count_min) })
  if (rules.driver_session_count_max != null)
    entries.push({ label: 'Max Driver Sessions', value: String(rules.driver_session_count_max) })
  if (rules.driver_allowlist?.length)
    entries.push({ label: 'Allowlist', value: `${rules.driver_allowlist.length} drivers` })

  if (entries.length === 0) {
    return <span className="text-sm text-neutral-400 italic">No targeting rules (all sessions eligible)</span>
  }

  return (
    <div className="space-y-1.5">
      {entries.map(e => (
        <div key={e.label} className="flex items-start gap-2 text-sm">
          <span className="text-neutral-500 min-w-[120px] shrink-0">{e.label}:</span>
          <span className="text-neutral-900 font-mono text-xs break-all">{e.value}</span>
        </div>
      ))}
    </div>
  )
}

// --- Campaign Detail View ---

function CampaignDetail({
  campaign,
  onBack,
  onRefresh,
}: {
  campaign: Campaign
  onBack: () => void
  onRefresh: () => void
}) {
  const [grants, setGrants] = useState<Grant[]>([])
  const [grantsTotal, setGrantsTotal] = useState(0)
  const [grantsLoading, setGrantsLoading] = useState(true)
  const [showEditModal, setShowEditModal] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)

  const loadGrants = useCallback(async () => {
    setGrantsLoading(true)
    try {
      const data: any = await fetchAPI(`/v1/campaigns/${campaign.id}/grants?limit=50`)
      setGrants(data.grants || [])
      setGrantsTotal(data.total || 0)
    } catch (err) {
      console.error('Failed to load grants:', err)
    } finally {
      setGrantsLoading(false)
    }
  }, [campaign.id])

  useEffect(() => {
    loadGrants()
  }, [loadGrants])

  const handlePause = async () => {
    setActionLoading(true)
    try {
      await fetchAPI(`/v1/campaigns/${campaign.id}/pause`, { method: 'POST' })
      onRefresh()
    } catch (err: any) {
      alert(err.message || 'Failed to pause campaign')
    } finally {
      setActionLoading(false)
    }
  }

  const handleResume = async () => {
    setActionLoading(true)
    try {
      await fetchAPI(`/v1/campaigns/${campaign.id}/resume`, { method: 'POST' })
      onRefresh()
    } catch (err: any) {
      alert(err.message || 'Failed to resume campaign')
    } finally {
      setActionLoading(false)
    }
  }

  const handleActivate = async () => {
    setActionLoading(true)
    try {
      await fetchAPI(`/v1/campaigns/${campaign.id}/activate`, { method: 'POST' })
      onRefresh()
    } catch (err: any) {
      alert(err.message || 'Failed to activate campaign')
    } finally {
      setActionLoading(false)
    }
  }

  const remaining = campaign.budget_cents - campaign.spent_cents
  const spentPct = campaign.budget_cents > 0
    ? Math.min(100, Math.round((campaign.spent_cents / campaign.budget_cents) * 100))
    : 0

  return (
    <div className="p-8">
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-sm text-neutral-500 hover:text-neutral-700 mb-4"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Campaigns
      </button>

      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl text-neutral-900">{campaign.name}</h1>
            {statusBadge(campaign.status)}
          </div>
          <p className="text-sm text-neutral-500 mt-1">
            {campaign.sponsor_name} &middot; {campaign.campaign_type} &middot; Created {formatDate(campaign.created_at)}
          </p>
          {campaign.description && (
            <p className="text-sm text-neutral-600 mt-2">{campaign.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {campaign.status === 'active' && (
            <button
              onClick={handlePause}
              disabled={actionLoading}
              className="flex items-center gap-1.5 px-3 py-2 text-sm text-amber-700 bg-amber-50 hover:bg-amber-100 rounded-lg border border-amber-200 disabled:opacity-50"
            >
              <Pause className="w-3.5 h-3.5" /> Pause
            </button>
          )}
          {campaign.status === 'paused' && (
            <button
              onClick={handleResume}
              disabled={actionLoading}
              className="flex items-center gap-1.5 px-3 py-2 text-sm text-green-700 bg-green-50 hover:bg-green-100 rounded-lg border border-green-200 disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5" /> Resume
            </button>
          )}
          {campaign.status === 'draft' && (
            <button
              onClick={handleActivate}
              disabled={actionLoading}
              className="flex items-center gap-1.5 px-3 py-2 text-sm text-green-700 bg-green-50 hover:bg-green-100 rounded-lg border border-green-200 disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5" /> Activate
            </button>
          )}
          <button
            onClick={() => setShowEditModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 text-sm text-neutral-600 hover:bg-neutral-100 rounded-lg border border-neutral-200"
          >
            <Pencil className="w-3.5 h-3.5" /> Edit
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-xs text-neutral-500 mb-1">Budget</div>
          <div className="text-xl text-neutral-900 font-medium">{cents(campaign.budget_cents)}</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-xs text-neutral-500 mb-1">Spent</div>
          <div className="text-xl text-neutral-900 font-medium">{cents(campaign.spent_cents)}</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-xs text-neutral-500 mb-1">Remaining</div>
          <div className={`text-xl font-medium ${remaining <= 0 ? 'text-red-600' : 'text-neutral-900'}`}>
            {cents(Math.max(0, remaining))}
          </div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-xs text-neutral-500 mb-1">Reward / Session</div>
          <div className="text-xl text-neutral-900 font-medium">{cents(campaign.cost_per_session_cents)}</div>
        </div>
      </div>

      {/* Budget progress bar */}
      <div className="bg-white border border-neutral-200 rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-neutral-600">Budget Utilization</span>
          <span className="text-sm font-medium text-neutral-900">{spentPct}%</span>
        </div>
        <div className="w-full h-3 bg-neutral-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              spentPct >= 90 ? 'bg-red-500' : spentPct >= 70 ? 'bg-amber-500' : 'bg-green-500'
            }`}
            style={{ width: `${spentPct}%` }}
          />
        </div>
        <div className="flex items-center justify-between mt-2 text-xs text-neutral-400">
          <span>{campaign.sessions_granted} grants</span>
          <span>{cents(campaign.spent_cents)} of {cents(campaign.budget_cents)}</span>
        </div>
      </div>

      {/* Campaign details grid */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-neutral-900 mb-3">Campaign Details</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-neutral-500">Priority</span>
              <span className="text-neutral-900">{campaign.priority}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-500">Start Date</span>
              <span className="text-neutral-900">{formatDate(campaign.start_date)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-500">End Date</span>
              <span className="text-neutral-900">{formatDate(campaign.end_date)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-500">Max Sessions</span>
              <span className="text-neutral-900">{campaign.max_sessions ?? 'Unlimited'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-500">Auto-Renew</span>
              <span className="text-neutral-900">{campaign.auto_renew ? 'Yes' : 'No'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-500">Funding</span>
              <span className="text-neutral-900 capitalize">{campaign.funding_status}</span>
            </div>
            {campaign.max_grants_per_driver_per_day != null && (
              <div className="flex justify-between">
                <span className="text-neutral-500">Daily Cap / Driver</span>
                <span className="text-neutral-900">{campaign.max_grants_per_driver_per_day}</span>
              </div>
            )}
            {campaign.max_grants_per_driver_per_campaign != null && (
              <div className="flex justify-between">
                <span className="text-neutral-500">Total Cap / Driver</span>
                <span className="text-neutral-900">{campaign.max_grants_per_driver_per_campaign}</span>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-neutral-900 mb-3">Targeting Rules</h3>
          <RulesDisplay rules={campaign.rules} />
        </div>
      </div>

      {/* Grants table */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-neutral-200 flex items-center justify-between">
          <h3 className="text-sm font-medium text-neutral-900">
            Grants ({grantsTotal})
          </h3>
        </div>
        {grantsLoading ? (
          <div className="p-8 text-center text-neutral-400">Loading grants...</div>
        ) : grants.length === 0 ? (
          <div className="p-8 text-center text-neutral-400">No grants yet</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-neutral-50 border-b border-neutral-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Grant ID</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Driver</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Amount</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Charger</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Duration</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Granted</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {grants.map(g => (
                  <tr key={g.id} className="hover:bg-neutral-50">
                    <td className="px-4 py-3 text-sm font-mono text-neutral-600">{g.id.toString().slice(0, 8)}</td>
                    <td className="px-4 py-3 text-sm text-neutral-900">#{g.driver_user_id}</td>
                    <td className="px-4 py-3 text-sm text-neutral-900 font-medium">{cents(g.amount_cents)}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-0.5 rounded text-xs border capitalize ${
                        g.status === 'granted' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-neutral-50 text-neutral-600 border-neutral-200'
                      }`}>
                        {g.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-neutral-600">{g.charger_id ? g.charger_id.slice(0, 12) : '-'}</td>
                    <td className="px-4 py-3 text-sm text-neutral-600">{g.duration_minutes != null ? `${g.duration_minutes} min` : '-'}</td>
                    <td className="px-4 py-3 text-sm text-neutral-600">{formatDateTime(g.granted_at || g.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showEditModal && (
        <CampaignModal
          campaign={campaign}
          onClose={() => setShowEditModal(false)}
          onSaved={onRefresh}
        />
      )}
    </div>
  )
}

// --- Main Campaigns Page ---

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)
  const pageSize = 50

  const loadCampaigns = useCallback(async () => {
    setLoading(true)
    try {
      const qs = new URLSearchParams()
      qs.append('limit', pageSize.toString())
      qs.append('offset', (page * pageSize).toString())
      if (statusFilter !== 'all') qs.append('status', statusFilter)

      const data: any = await fetchAPI(`/v1/campaigns?${qs.toString()}`)
      setCampaigns(data.campaigns || [])
      setTotal(data.count || data.campaigns?.length || 0)
    } catch (err) {
      console.error('Failed to load campaigns:', err)
      setCampaigns([])
    } finally {
      setLoading(false)
    }
  }, [statusFilter, page])

  useEffect(() => {
    loadCampaigns()
  }, [loadCampaigns])

  const handleRefresh = () => {
    if (selectedCampaign) {
      // Re-fetch the selected campaign from the list
      fetchAPI<any>(`/v1/campaigns/${selectedCampaign.id}`)
        .then(data => {
          if (data.campaign) setSelectedCampaign(data.campaign)
        })
        .catch(() => {})
    }
    loadCampaigns()
  }

  const handleStatusFilterChange = (filter: StatusFilter) => {
    setStatusFilter(filter)
    setPage(0)
  }

  // Detail view
  if (selectedCampaign) {
    return (
      <CampaignDetail
        campaign={selectedCampaign}
        onBack={() => setSelectedCampaign(null)}
        onRefresh={handleRefresh}
      />
    )
  }

  const totalPages = Math.ceil(total / pageSize)

  // Summary stats from loaded campaigns
  const totalBudget = campaigns.reduce((sum, c) => sum + c.budget_cents, 0)
  const totalSpent = campaigns.reduce((sum, c) => sum + c.spent_cents, 0)
  const totalGrants = campaigns.reduce((sum, c) => sum + c.sessions_granted, 0)
  const activeCampaigns = campaigns.filter(c => c.status === 'active').length

  const statusTabs: { id: StatusFilter; label: string }[] = [
    { id: 'all', label: 'All' },
    { id: 'active', label: 'Active' },
    { id: 'paused', label: 'Paused' },
    { id: 'completed', label: 'Completed' },
    { id: 'draft', label: 'Draft' },
  ]

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl text-neutral-900">Campaigns</h1>
          <p className="text-sm text-neutral-500 mt-1">
            Manage sponsor and merchant campaigns
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 text-sm bg-neutral-900 text-white rounded-lg hover:bg-neutral-800"
          >
            <Plus className="w-4 h-4" /> Create Campaign
          </button>
          <button onClick={loadCampaigns} className="p-2 hover:bg-neutral-100 rounded-lg" title="Refresh">
            <RefreshCw className="w-4 h-4 text-neutral-600" />
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-xs text-neutral-500 mb-1">Active Campaigns</div>
          <div className="text-xl text-neutral-900 font-medium">{activeCampaigns}</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-xs text-neutral-500 mb-1">Total Budget</div>
          <div className="text-xl text-neutral-900 font-medium">{cents(totalBudget)}</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-xs text-neutral-500 mb-1">Total Spent</div>
          <div className="text-xl text-neutral-900 font-medium">{cents(totalSpent)}</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-xs text-neutral-500 mb-1">Total Grants</div>
          <div className="text-xl text-neutral-900 font-medium">{totalGrants}</div>
        </div>
      </div>

      {/* Status filter tabs */}
      <div className="flex items-center gap-1 mb-6 bg-neutral-100 rounded-lg p-1 w-fit">
        {statusTabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => handleStatusFilterChange(tab.id)}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
              statusFilter === tab.id
                ? 'bg-white text-neutral-900 shadow-sm'
                : 'text-neutral-500 hover:text-neutral-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-neutral-400">Loading campaigns...</div>
        ) : campaigns.length === 0 ? (
          <div className="p-12 text-center text-neutral-400">
            {statusFilter !== 'all' ? `No ${statusFilter} campaigns found` : 'No campaigns found'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-neutral-50 border-b border-neutral-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Name</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Budget</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Spent</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Progress</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Grants</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Reward</th>
                  <th className="px-4 py-3 text-left text-xs text-neutral-500 uppercase tracking-wider">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {campaigns.map(c => {
                  const pct = c.budget_cents > 0
                    ? Math.min(100, Math.round((c.spent_cents / c.budget_cents) * 100))
                    : 0
                  return (
                    <tr
                      key={c.id}
                      onClick={() => setSelectedCampaign(c)}
                      className="hover:bg-neutral-50 cursor-pointer"
                    >
                      <td className="px-4 py-3">
                        <div className="text-sm text-neutral-900 font-medium">{c.name}</div>
                        <div className="text-xs text-neutral-400">{c.sponsor_name}</div>
                      </td>
                      <td className="px-4 py-3">{statusBadge(c.status)}</td>
                      <td className="px-4 py-3 text-sm text-neutral-900">{cents(c.budget_cents)}</td>
                      <td className="px-4 py-3 text-sm text-neutral-900">{cents(c.spent_cents)}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-neutral-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-amber-500' : 'bg-green-500'
                              }`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="text-xs text-neutral-500">{pct}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-neutral-900">{c.sessions_granted}</td>
                      <td className="px-4 py-3 text-sm text-neutral-600">{cents(c.cost_per_session_cents)}</td>
                      <td className="px-4 py-3 text-sm text-neutral-600">{formatDate(c.created_at)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-neutral-500">
            Showing {page * pageSize + 1}-{Math.min((page + 1) * pageSize, total)} of {total}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="p-2 rounded-lg hover:bg-neutral-100 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm text-neutral-600">Page {page + 1} of {totalPages}</span>
            <button
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="p-2 rounded-lg hover:bg-neutral-100 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CampaignModal
          campaign={null}
          onClose={() => setShowCreateModal(false)}
          onSaved={loadCampaigns}
        />
      )}
    </div>
  )
}
