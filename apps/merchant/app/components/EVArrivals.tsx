import { useState, useEffect, useCallback } from 'react'
import { fetchAPI } from '../services/api'
import { capture } from '../analytics'

interface ArrivalSession {
  session_id: string
  status: string
  arrival_type: string
  flow_type?: string
  session_code?: string
  order_number: string | null
  order_total_cents: number | null
  vehicle_color: string | null
  vehicle_model: string | null
  created_at: string
  merchant_notified_at: string | null
  verification_status?: string
}

interface NotificationConfig {
  notify_sms: boolean
  notify_email: boolean
  sms_phone: string
  email_address: string
}

interface RedeemResponse {
  redeemed: boolean
  session_id: string
  already_redeemed: boolean
  error?: string
}

export function EVArrivals() {
  const [sessions, setSessions] = useState<ArrivalSession[]>([])
  const [config, setConfig] = useState<NotificationConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [editingConfig, setEditingConfig] = useState(false)
  const [smsPhone, setSmsPhone] = useState('')
  const [emailAddress, setEmailAddress] = useState('')
  const [notifySms, setNotifySms] = useState(true)
  const [notifyEmail, setNotifyEmail] = useState(false)
  const merchantId = localStorage.getItem('merchant_id') || ''

  // Session code redemption state
  const [redeemCode, setRedeemCode] = useState('')
  const [redeemLoading, setRedeemLoading] = useState(false)
  const [redeemSuccess, setRedeemSuccess] = useState<string | null>(null)
  const [redeemError, setRedeemError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [sessionsRes, configRes] = await Promise.all([
        fetchAPI<{ sessions: ArrivalSession[] }>(`/v1/merchants/${merchantId}/arrivals`).catch(() => ({ sessions: [] })),
        fetchAPI<NotificationConfig>(`/v1/merchants/${merchantId}/notification-config`).catch(() => null),
      ])
      setSessions(sessionsRes.sessions || [])
      if (configRes) {
        setConfig(configRes)
        setSmsPhone(configRes.sms_phone || '')
        setEmailAddress(configRes.email_address || '')
        setNotifySms(configRes.notify_sms)
        setNotifyEmail(configRes.notify_email)
      }
    } catch {
      // Graceful fallback
    } finally {
      setLoading(false)
    }
  }

  const handleConfirm = async (sessionId: string) => {
    try {
      await fetchAPI(`/v1/arrival/${sessionId}/merchant-confirm`, {
        method: 'POST',
        body: JSON.stringify({ confirmed: true }),
      })
      capture('merchant.ev_arrival.confirmed', { session_id: sessionId })
      loadData()
    } catch (err) {
      console.error('Failed to confirm:', err)
    }
  }

  const handleSaveConfig = async () => {
    try {
      await fetchAPI(`/v1/merchants/${merchantId}/notification-config`, {
        method: 'PUT',
        body: JSON.stringify({
          sms_phone: smsPhone,
          email_address: emailAddress,
          notify_sms: notifySms,
          notify_email: notifyEmail,
        }),
      })
      capture('merchant.notification_config.saved')
      setEditingConfig(false)
      loadData()
    } catch (err) {
      console.error('Failed to save config:', err)
    }
  }

  const handleRedeemCode = useCallback(async () => {
    if (!redeemCode.trim() || redeemCode.length !== 6) return

    setRedeemLoading(true)
    setRedeemError(null)
    setRedeemSuccess(null)

    try {
      const response = await fetchAPI<RedeemResponse>(`/v1/checkin/redeem`, {
        method: 'POST',
        body: JSON.stringify({
          code: redeemCode.toUpperCase(),
        }),
      })

      if (response.redeemed || response.already_redeemed) {
        capture('merchant.checkin.redeemed', {
          session_code: redeemCode.toUpperCase(),
          session_id: response.session_id,
        })
        const message = response.already_redeemed
          ? `Code ${redeemCode.toUpperCase()} was already redeemed`
          : `Code ${redeemCode.toUpperCase()} redeemed successfully!`
        setRedeemSuccess(message)
        setRedeemCode('')
        // Refresh sessions list
        loadData()
        // Clear success message after 5 seconds
        setTimeout(() => setRedeemSuccess(null), 5000)
      } else {
        setRedeemError(response.error || 'Invalid or expired code')
      }
    } catch (err: unknown) {
      const error = err as { message?: string }
      console.error('Redeem error:', err)
      setRedeemError(error.message || 'Failed to redeem code. Please try again.')
    } finally {
      setRedeemLoading(false)
    }
  }, [redeemCode, merchantId])

  const activeSessions = sessions.filter(s =>
    ['arrived', 'merchant_notified', 'awaiting_arrival'].includes(s.status)
  )
  const completedSessions = sessions.filter(s =>
    ['completed', 'completed_unbillable'].includes(s.status)
  )

  const todayTotal = completedSessions
    .filter(s => {
      const d = new Date(s.created_at)
      const today = new Date()
      return d.toDateString() === today.toDateString()
    })
    .reduce((sum, s) => sum + (s.order_total_cents || 0), 0)

  if (loading) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-neutral-900 mb-6">EV Arrivals</h2>
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-24 bg-neutral-100 rounded-lg" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl">
      <h2 className="text-2xl font-bold text-neutral-900 mb-2">EV Arrivals</h2>
      <p className="text-neutral-500 mb-6">
        Today: {activeSessions.length + completedSessions.length} arrivals
        {todayTotal > 0 && ` · $${(todayTotal / 100).toFixed(2)} total`}
      </p>

      {/* Session Code Redemption */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-5 mb-8">
        <h3 className="text-lg font-semibold text-neutral-900 mb-2">Redeem Check-In Code</h3>
        <p className="text-sm text-neutral-600 mb-4">
          Enter the 6-character code shown on the customer's phone
        </p>

        {redeemSuccess && (
          <div className="bg-green-50 border border-green-200 text-green-700 rounded-lg px-4 py-3 mb-4 text-sm font-medium">
            {redeemSuccess}
          </div>
        )}

        {redeemError && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
            {redeemError}
          </div>
        )}

        <div className="flex gap-3">
          <input
            type="text"
            value={redeemCode}
            onChange={e => {
              const val = e.target.value.replace(/[^A-Za-z0-9]/g, '').toUpperCase().slice(0, 6)
              setRedeemCode(val)
              setRedeemError(null)
            }}
            onKeyDown={e => {
              if (e.key === 'Enter' && redeemCode.length === 6) {
                handleRedeemCode()
              }
            }}
            placeholder="ABC123"
            maxLength={6}
            className="flex-1 max-w-[200px] h-12 text-center text-2xl font-mono tracking-[0.3em] uppercase border-2 border-blue-300 rounded-lg focus:border-blue-500 focus:outline-none bg-white"
            disabled={redeemLoading}
          />
          <button
            onClick={handleRedeemCode}
            disabled={redeemCode.length !== 6 || redeemLoading}
            className="h-12 px-6 bg-blue-600 hover:bg-blue-700 disabled:bg-neutral-300 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
          >
            {redeemLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Checking...
              </>
            ) : (
              'Redeem'
            )}
          </button>
        </div>
      </div>

      {/* Active Sessions */}
      {activeSessions.length > 0 && (
        <div className="mb-8">
          <h3 className="text-sm font-semibold text-neutral-500 uppercase tracking-wide mb-3">Active</h3>
          {activeSessions.map(session => (
            <div key={session.session_id} className="bg-white border border-neutral-200 rounded-lg p-4 mb-3">
              <div className="flex items-center justify-between mb-2">
                <span className="inline-flex items-center gap-1.5 text-green-700 bg-green-50 text-xs font-medium px-2 py-1 rounded-full">
                  <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                  ACTIVE
                </span>
                <span className="text-xs text-neutral-400">
                  {session.arrival_type === 'ev_curbside' ? 'Curbside' : 'Dine-In'}
                </span>
              </div>
              <p className="font-medium text-neutral-900">
                Order #{session.order_number || 'N/A'} · {session.arrival_type === 'ev_curbside' ? 'EV Curbside' : 'EV Dine-In'}
              </p>
              <p className="text-sm text-neutral-600">
                {session.vehicle_color} {session.vehicle_model}
              </p>
              {session.merchant_notified_at && (
                <p className="text-xs text-neutral-400 mt-1">
                  Arrived {new Date(session.merchant_notified_at).toLocaleTimeString()}
                </p>
              )}
              <button
                onClick={() => handleConfirm(session.session_id)}
                className="mt-3 bg-neutral-900 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-neutral-800"
              >
                Mark Delivered
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Completed Sessions */}
      {completedSessions.length > 0 && (
        <div className="mb-8">
          <h3 className="text-sm font-semibold text-neutral-500 uppercase tracking-wide mb-3">Completed</h3>
          {completedSessions.slice(0, 10).map(session => (
            <div key={session.session_id} className="bg-white border border-neutral-200 rounded-lg p-4 mb-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-neutral-400 font-medium">COMPLETED</span>
                {session.order_total_cents && (
                  <span className="text-sm font-medium text-neutral-900">
                    ${(session.order_total_cents / 100).toFixed(2)}
                  </span>
                )}
              </div>
              <p className="text-sm text-neutral-700">
                Order #{session.order_number || 'N/A'} · {session.arrival_type === 'ev_curbside' ? 'EV Curbside' : 'EV Dine-In'}
              </p>
              <p className="text-xs text-neutral-400">
                {session.vehicle_color} {session.vehicle_model} · {new Date(session.created_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      )}

      {activeSessions.length === 0 && completedSessions.length === 0 && (
        <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-8 text-center mb-8">
          <p className="text-neutral-500">No EV Arrivals yet. Drivers will appear here when they create EV Arrival sessions at your location.</p>
        </div>
      )}

      {/* Notification Settings */}
      <div className="border-t border-neutral-200 pt-6">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">Notification Settings</h3>

        {!editingConfig ? (
          <div className="bg-white border border-neutral-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-700">
                  SMS: {config?.sms_phone || 'Not set'}
                  {config?.notify_sms && config?.sms_phone ? ' ✓' : ''}
                </p>
                <p className="text-sm text-neutral-700">
                  Email: {config?.notify_email ? (config?.email_address || 'Not set') : 'Off'}
                </p>
              </div>
              <button
                onClick={() => setEditingConfig(true)}
                className="text-blue-600 text-sm font-medium hover:underline"
              >
                Edit settings
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-white border border-neutral-200 rounded-lg p-4 space-y-4">
            <div>
              <label className="flex items-center gap-2 mb-2">
                <input
                  type="checkbox"
                  checked={notifySms}
                  onChange={e => setNotifySms(e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm text-neutral-700">SMS Notifications</span>
              </label>
              {notifySms && (
                <input
                  type="tel"
                  value={smsPhone}
                  onChange={e => setSmsPhone(e.target.value)}
                  placeholder="+15125551234"
                  className="w-full border border-neutral-300 rounded-lg px-3 py-2 text-sm"
                />
              )}
            </div>

            <div>
              <label className="flex items-center gap-2 mb-2">
                <input
                  type="checkbox"
                  checked={notifyEmail}
                  onChange={e => setNotifyEmail(e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm text-neutral-700">Email Notifications</span>
              </label>
              {notifyEmail && (
                <input
                  type="email"
                  value={emailAddress}
                  onChange={e => setEmailAddress(e.target.value)}
                  placeholder="manager@business.com"
                  className="w-full border border-neutral-300 rounded-lg px-3 py-2 text-sm"
                />
              )}
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleSaveConfig}
                className="bg-neutral-900 text-white px-4 py-2 rounded-lg text-sm font-medium"
              >
                Save
              </button>
              <button
                onClick={() => setEditingConfig(false)}
                className="text-neutral-500 text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
