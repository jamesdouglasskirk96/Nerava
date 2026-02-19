import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { fetchAPI } from '../services/api'
import { capture } from '../analytics'
import { MERCHANT_EVENTS } from '../analytics/events'
import { LoomModal } from './LoomModal'

const CALENDLY_URL = import.meta.env.VITE_CALENDLY_URL || 'https://calendly.com/nerava'

interface NearestCharger {
  name: string
  network: string | null
  walk_minutes: number | null
  distance_m: number | null
}

interface PreviewData {
  merchant_id: string
  name: string
  address: string | null
  lat: number | null
  lng: number | null
  rating: number | null
  user_rating_count: number | null
  photo_url: string | null
  photo_urls: string[]
  open_now: boolean | null
  business_status: string | null
  category: string | null
  nearest_charger: NearestCharger | null
  verified_visit_count: number
}

export function MerchantPreview() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const merchantId = searchParams.get('merchant_id') || ''
  const exp = searchParams.get('exp') || ''
  const sig = searchParams.get('sig') || ''

  const [data, setData] = useState<PreviewData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [loomOpen, setLoomOpen] = useState(false)
  const [phone, setPhone] = useState('')
  const [textSending, setTextSending] = useState(false)
  const [textSent, setTextSent] = useState(false)

  useEffect(() => {
    if (!merchantId || !exp || !sig) {
      setError('Invalid preview link.')
      setLoading(false)
      return
    }

    fetchAPI<PreviewData>(
      `/v1/merchant/funnel/preview?merchant_id=${encodeURIComponent(merchantId)}&exp=${encodeURIComponent(exp)}&sig=${encodeURIComponent(sig)}`
    )
      .then((d) => {
        setData(d)
        capture(MERCHANT_EVENTS.FUNNEL_PREVIEW_LOADED, { merchant_id: merchantId })
      })
      .catch((e) => {
        const msg = e?.message?.includes('expired') ? 'This link has expired.' : 'Unable to load preview.'
        setError(msg)
        capture(MERCHANT_EVENTS.FUNNEL_PREVIEW_ERROR, { merchant_id: merchantId, error: msg })
      })
      .finally(() => setLoading(false))
  }, [merchantId, exp, sig])

  // Auto-open Loom after 800ms if not seen
  useEffect(() => {
    if (!data) return
    const seen = localStorage.getItem(`loom_seen_${data.merchant_id}`)
    if (seen) return
    const timer = setTimeout(() => setLoomOpen(true), 800)
    return () => clearTimeout(timer)
  }, [data])

  function handleClaim() {
    if (!data) return
    capture(MERCHANT_EVENTS.FUNNEL_CTA_CLAIM, { merchant_id: data.merchant_id })
    localStorage.setItem('merchant_id', data.merchant_id)
    navigate('/claim')
  }

  function handleSchedule() {
    capture(MERCHANT_EVENTS.FUNNEL_CTA_SCHEDULE, { merchant_id: data?.merchant_id })
    window.open(CALENDLY_URL, '_blank')
  }

  async function handleTextLink() {
    if (!phone.trim() || !data) return
    setTextSending(true)
    capture(MERCHANT_EVENTS.FUNNEL_CTA_TEXT_LINK, { merchant_id: data.merchant_id })
    try {
      await fetchAPI('/v1/merchant/funnel/text-preview-link', {
        method: 'POST',
        body: JSON.stringify({
          phone: phone.trim(),
          preview_url: `/preview?merchant_id=${merchantId}&exp=${exp}&sig=${sig}`,
          merchant_name: data.name,
        }),
      })
      setTextSent(true)
    } catch {
      // silent
    } finally {
      setTextSending(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center">
          <div className="text-5xl mb-4">&#128279;</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">{error}</h1>
          <p className="text-gray-500 mb-6">Request a new preview link from your Nerava contact.</p>
          <button
            onClick={() => navigate('/find')}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Search again
          </button>
        </div>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero */}
      <div className="relative h-64 md:h-80 bg-gray-900">
        {data.photo_url ? (
          <img
            src={data.photo_url}
            alt={data.name}
            className="w-full h-full object-cover opacity-70"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-blue-900 to-blue-600" />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        <div className="absolute bottom-6 left-6 right-6 text-white">
          <h1 className="text-3xl md:text-4xl font-bold mb-1">{data.name}</h1>
          {data.address && <p className="text-white/80 text-sm">{data.address}</p>}
          <div className="flex items-center gap-3 mt-2">
            {data.open_now !== null && (
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${data.open_now ? 'bg-green-500/80' : 'bg-red-500/80'}`}>
                {data.open_now ? 'Open' : 'Closed'}
              </span>
            )}
            {data.rating != null && (
              <span className="text-sm">
                <span className="text-yellow-400">★</span> {data.rating.toFixed(1)}
                {data.user_rating_count != null && (
                  <span className="text-white/60 ml-1">({data.user_rating_count})</span>
                )}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        {/* "What drivers see" card */}
        <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">What drivers see</h2>
          <div className="flex gap-4 items-center">
            {data.photo_url ? (
              <img src={data.photo_url} alt="" className="w-14 h-14 rounded-lg object-cover" />
            ) : (
              <div className="w-14 h-14 bg-gray-100 rounded-lg" />
            )}
            <div>
              <div className="font-semibold text-gray-900">{data.name}</div>
              {data.category && <div className="text-sm text-gray-500 capitalize">{data.category}</div>}
              {data.rating != null && (
                <div className="text-sm text-gray-600">
                  <span className="text-yellow-500">★</span> {data.rating.toFixed(1)}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Nearest charger card */}
        {data.nearest_charger && (
          <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Nearest EV charger</h2>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-50 rounded-full flex items-center justify-center text-green-600 text-lg">
                ⚡
              </div>
              <div>
                <div className="font-medium text-gray-900">{data.nearest_charger.name}</div>
                {data.nearest_charger.network && (
                  <div className="text-sm text-gray-500">{data.nearest_charger.network}</div>
                )}
              </div>
              {data.nearest_charger.walk_minutes != null && (
                <div className="ml-auto text-right">
                  <div className="text-lg font-bold text-gray-900">{data.nearest_charger.walk_minutes} min</div>
                  <div className="text-xs text-gray-400">walk</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Verified visits proof */}
        {data.verified_visit_count > 0 && (
          <div className="bg-blue-50 rounded-xl p-5 border border-blue-100">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-lg">
                &#128737;
              </div>
              <div>
                <div className="font-semibold text-blue-900">{data.verified_visit_count} verified visits</div>
                <div className="text-sm text-blue-700">from EV drivers while charging</div>
              </div>
            </div>
            <ul className="text-sm text-blue-800 space-y-1 ml-13">
              <li>Drivers discovered your business through Nerava during active charging sessions.</li>
              <li>Each visit was verified by location proximity and session status.</li>
            </ul>
          </div>
        )}

        {/* CTAs */}
        <div className="space-y-3 pt-4">
          <button
            onClick={handleClaim}
            className="w-full py-3.5 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-colors text-lg"
          >
            Claim your business
          </button>

          <button
            onClick={handleSchedule}
            className="w-full py-3 bg-white text-gray-800 font-medium rounded-xl border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            Schedule a 10-minute walkthrough
          </button>

          {/* Text me the link */}
          <div className="pt-2">
            {!textSent ? (
              <div className="flex gap-2">
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="(555) 123-4567"
                  className="flex-1 px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleTextLink}
                  disabled={textSending || !phone.trim()}
                  className="px-4 py-2.5 text-sm font-medium text-blue-600 hover:text-blue-700 disabled:opacity-50"
                >
                  {textSending ? 'Sending...' : 'Text me this link'}
                </button>
              </div>
            ) : (
              <p className="text-center text-sm text-green-600 font-medium py-2">Link sent! Check your messages.</p>
            )}
          </div>
        </div>
      </div>

      {/* Loom modal */}
      <LoomModal
        merchantId={data.merchant_id}
        open={loomOpen}
        onClose={() => setLoomOpen(false)}
      />
    </div>
  )
}
