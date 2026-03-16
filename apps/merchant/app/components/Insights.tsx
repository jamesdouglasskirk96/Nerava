import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { Activity, Users, Clock, Zap, Footprints, Loader2 } from 'lucide-react'
import { fetchAPI } from '../services/api'

interface InsightsData {
  period: string
  ev_sessions_nearby: number
  unique_drivers: number
  avg_duration_minutes: number | null
  avg_kwh: number | null
  peak_hours: { hour: number; sessions: number }[]
  dwell_distribution: {
    under_15min: number
    '15_30min': number
    '30_60min': number
    over_60min: number
  } | null
  walk_traffic: {
    visited_area: number
    avg_walk_distance_m: number
  } | null
  has_pro_subscription?: boolean
  session_details?: Array<{
    id: string
    start: string | null
    end: string | null
    duration_minutes: number | null
    kwh: number | null
    charger_id: string | null
  }> | null
  customer_details?: Array<{
    driver_id_hash: string
    visit_count: number
  }> | null
}

const DWELL_COLORS = ['#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8']

function StatCard({ icon: Icon, label, value }: { icon: typeof Activity; label: string; value: string | null }) {
  return (
    <div className="bg-white rounded-xl border border-neutral-200 p-5">
      <div className="flex items-center gap-2 text-neutral-500 text-sm mb-1">
        <Icon className="w-4 h-4" />
        <span>{label}</span>
      </div>
      <p className="text-2xl font-semibold text-neutral-900">
        {value ?? '—'}
      </p>
    </div>
  )
}

export function Insights() {
  const [data, setData] = useState<InsightsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [period, setPeriod] = useState<'week' | '30d'>('30d')

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetchAPI<InsightsData>(`/v1/merchants/me/insights?period=${period}`)
      .then(setData)
      .catch((e) => setError(e.message || 'Failed to load insights'))
      .finally(() => setLoading(false))
  }, [period])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-6 h-6 animate-spin text-neutral-400" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="py-20 text-center">
        <p className="text-neutral-600">{error}</p>
      </div>
    )
  }

  if (!data) return null

  const peakHoursData = data.peak_hours.map((h) => ({
    hour: `${h.hour % 12 || 12}${h.hour < 12 ? 'a' : 'p'}`,
    sessions: h.sessions,
  }))

  const dwellData = data.dwell_distribution
    ? [
        { name: '<15 min', value: data.dwell_distribution.under_15min },
        { name: '15-30 min', value: data.dwell_distribution['15_30min'] },
        { name: '30-60 min', value: data.dwell_distribution['30_60min'] },
        { name: '60+ min', value: data.dwell_distribution.over_60min },
      ]
    : []

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-neutral-900">Nerava Insights</h2>
          <p className="text-sm text-neutral-500 mt-1">EV charging activity near your business</p>
        </div>
        <div className="flex gap-1 bg-neutral-100 rounded-lg p-1">
          <button
            onClick={() => setPeriod('week')}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
              period === 'week' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-500'
            }`}
          >
            7 days
          </button>
          <button
            onClick={() => setPeriod('30d')}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
              period === '30d' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-500'
            }`}
          >
            30 days
          </button>
        </div>
      </div>

      {/* Key stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard icon={Activity} label="EV Sessions" value={String(data.ev_sessions_nearby)} />
        <StatCard icon={Users} label="Unique Drivers" value={String(data.unique_drivers)} />
        <StatCard
          icon={Clock}
          label="Avg Duration"
          value={data.avg_duration_minutes != null ? `${data.avg_duration_minutes} min` : null}
        />
        <StatCard
          icon={Zap}
          label="Avg Energy"
          value={data.avg_kwh != null ? `${data.avg_kwh} kWh` : null}
        />
      </div>

      {/* Walk traffic callout */}
      {data.walk_traffic && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 mb-8">
          <div className="flex items-center gap-2 mb-2">
            <Footprints className="w-5 h-5 text-blue-600" />
            <span className="font-medium text-blue-900">Walk Traffic</span>
          </div>
          <p className="text-sm text-blue-800">
            <span className="font-semibold text-lg">{data.walk_traffic.visited_area}%</span> of EV drivers walked within 200m of your business.
            Average walk distance: <span className="font-medium">{data.walk_traffic.avg_walk_distance_m}m</span>.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Peak hours chart */}
        {peakHoursData.length > 0 && (
          <div className="bg-white rounded-xl border border-neutral-200 p-5">
            <h3 className="text-sm font-medium text-neutral-700 mb-4">Sessions by Hour of Day</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={peakHoursData}>
                <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="sessions" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Dwell distribution */}
        {dwellData.length > 0 && (
          <div className="bg-white rounded-xl border border-neutral-200 p-5">
            <h3 className="text-sm font-medium text-neutral-700 mb-4">Dwell Time Distribution</h3>
            <div className="flex items-center gap-6">
              <ResponsiveContainer width="50%" height={200}>
                <PieChart>
                  <Pie
                    data={dwellData}
                    dataKey="value"
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={2}
                  >
                    {dwellData.map((_, i) => (
                      <Cell key={i} fill={DWELL_COLORS[i]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2">
                {dwellData.map((d, i) => (
                  <div key={d.name} className="flex items-center gap-2 text-sm">
                    <div
                      className="w-3 h-3 rounded-sm flex-shrink-0"
                      style={{ background: DWELL_COLORS[i] }}
                    />
                    <span className="text-neutral-600">{d.name}</span>
                    <span className="font-medium text-neutral-900 ml-auto">{d.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Pro-gated: Session Details */}
      <div className="mt-8">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">Session Details</h3>
        {data.has_pro_subscription && data.session_details && data.session_details.length > 0 ? (
          <div className="bg-white rounded-xl border border-neutral-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-neutral-50">
                <tr>
                  <th className="text-left px-4 py-3 text-neutral-600 font-medium">Start</th>
                  <th className="text-left px-4 py-3 text-neutral-600 font-medium">Duration</th>
                  <th className="text-left px-4 py-3 text-neutral-600 font-medium">Energy</th>
                  <th className="text-left px-4 py-3 text-neutral-600 font-medium">Charger</th>
                </tr>
              </thead>
              <tbody>
                {data.session_details.map((s) => (
                  <tr key={s.id} className="border-t border-neutral-100">
                    <td className="px-4 py-3 text-neutral-700">
                      {s.start ? new Date(s.start).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                    </td>
                    <td className="px-4 py-3 text-neutral-700">
                      {s.duration_minutes != null ? `${s.duration_minutes} min` : '—'}
                    </td>
                    <td className="px-4 py-3 text-neutral-700">
                      {s.kwh != null ? `${s.kwh} kWh` : '—'}
                    </td>
                    <td className="px-4 py-3 text-neutral-500 text-xs font-mono">
                      {s.charger_id ? s.charger_id.slice(0, 8) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="relative">
            <div className="bg-white rounded-xl border border-neutral-200 p-6 opacity-40 blur-[2px] pointer-events-none select-none">
              <table className="w-full text-sm">
                <thead className="bg-neutral-50"><tr><th className="text-left px-4 py-3">Start</th><th className="text-left px-4 py-3">Duration</th><th className="text-left px-4 py-3">Energy</th></tr></thead>
                <tbody>
                  {[1,2,3].map((i) => (
                    <tr key={i} className="border-t border-neutral-100">
                      <td className="px-4 py-3">Mar {i}, 2:30 PM</td>
                      <td className="px-4 py-3">42 min</td>
                      <td className="px-4 py-3">28.5 kWh</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="absolute inset-0 flex items-center justify-center">
              <a
                href="/billing"
                className="bg-neutral-900 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-neutral-800 transition-colors"
              >
                Upgrade to Pro to unlock
              </a>
            </div>
          </div>
        )}
      </div>

      {/* Pro-gated: Customer Visit Frequency */}
      <div className="mt-8">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">Customer Visit Frequency</h3>
        {data.has_pro_subscription && data.customer_details && data.customer_details.length > 0 ? (
          <div className="bg-white rounded-xl border border-neutral-200 p-5">
            <div className="space-y-2">
              {data.customer_details.map((c) => (
                <div key={c.driver_id_hash} className="flex items-center justify-between py-2">
                  <span className="text-sm text-neutral-600 font-mono">Driver ...{c.driver_id_hash}</span>
                  <span className="text-sm font-medium text-neutral-900">{c.visit_count} visits</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="relative">
            <div className="bg-white rounded-xl border border-neutral-200 p-5 opacity-40 blur-[2px] pointer-events-none select-none">
              {[1,2,3].map((i) => (
                <div key={i} className="flex items-center justify-between py-2">
                  <span className="text-sm text-neutral-600">Driver ...abc{i}def</span>
                  <span className="text-sm font-medium">{5 - i} visits</span>
                </div>
              ))}
            </div>
            <div className="absolute inset-0 flex items-center justify-center">
              <a
                href="/billing"
                className="bg-neutral-900 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-neutral-800 transition-colors"
              >
                Upgrade to Pro to unlock
              </a>
            </div>
          </div>
        )}
      </div>

      {data.unique_drivers < 5 && data.ev_sessions_nearby > 0 && (
        <p className="text-xs text-neutral-400 mt-6 text-center">
          Some metrics are hidden until at least 5 unique drivers have charged nearby (privacy threshold).
        </p>
      )}
    </div>
  )
}
