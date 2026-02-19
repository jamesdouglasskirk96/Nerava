import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchAPI } from '../services/api'
import { capture } from '../analytics'
import { MERCHANT_EVENTS } from '../analytics/events'

interface SearchResult {
  place_id: string
  name: string
  address: string | null
  lat: number | null
  lng: number | null
  rating: number | null
  user_rating_count: number | null
  photo_url: string | null
  types: string[]
}

interface ResolveResponse {
  merchant_id: string
  preview_url: string
  sig: string
  expires_at: number
}

export function FindBusiness() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const [resolving, setResolving] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)
  const navigate = useNavigate()
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (!query.trim()) {
      setResults([])
      setHasSearched(false)
      return
    }

    debounceRef.current = setTimeout(async () => {
      setSearching(true)
      try {
        const data = await fetchAPI<{ results: SearchResult[] }>(
          `/v1/merchant/funnel/search?q=${encodeURIComponent(query.trim())}`
        )
        setResults(data.results)
        setHasSearched(true)
        capture(MERCHANT_EVENTS.FUNNEL_SEARCH, { query: query.trim(), result_count: data.results.length })
        if (data.results.length === 0) {
          capture(MERCHANT_EVENTS.FUNNEL_SEARCH_NO_RESULTS, { query: query.trim() })
        }
      } catch {
        setResults([])
        setHasSearched(true)
      } finally {
        setSearching(false)
      }
    }, 300)

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query])

  async function handleSelect(result: SearchResult) {
    setResolving(result.place_id)
    capture(MERCHANT_EVENTS.FUNNEL_SELECT_BUSINESS, { place_id: result.place_id, name: result.name })

    try {
      const data = await fetchAPI<ResolveResponse>('/v1/merchant/funnel/resolve', {
        method: 'POST',
        body: JSON.stringify({
          place_id: result.place_id,
          name: result.name,
          lat: result.lat ?? 0,
          lng: result.lng ?? 0,
        }),
      })
      navigate(`/preview?merchant_id=${data.merchant_id}&exp=${data.expires_at}&sig=${data.sig}`)
    } catch {
      setResolving(null)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Find your business</h1>
          <p className="text-gray-600">
            See how your business appears to EV drivers charging nearby.
          </p>
        </div>

        <div className="relative mb-6">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by business name or address..."
            className="w-full px-4 py-3 rounded-xl border border-gray-300 shadow-sm text-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            autoFocus
          />
          {searching && (
            <div className="absolute right-4 top-1/2 -translate-y-1/2">
              <div className="h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>

        {/* Skeleton loading cards */}
        {searching && results.length === 0 && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-xl p-4 shadow-sm animate-pulse flex gap-4">
                <div className="w-16 h-16 bg-gray-200 rounded-lg flex-shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-2/3" />
                  <div className="h-3 bg-gray-200 rounded w-full" />
                  <div className="h-3 bg-gray-200 rounded w-1/3" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Results */}
        {!searching && results.length > 0 && (
          <div className="space-y-3">
            {results.map((r) => (
              <button
                key={r.place_id}
                onClick={() => handleSelect(r)}
                disabled={resolving !== null}
                className="w-full bg-white rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow text-left flex gap-4 items-center disabled:opacity-60"
              >
                {r.photo_url ? (
                  <img
                    src={r.photo_url}
                    alt={r.name}
                    className="w-16 h-16 rounded-lg object-cover flex-shrink-0"
                  />
                ) : (
                  <div className="w-16 h-16 bg-gray-100 rounded-lg flex-shrink-0 flex items-center justify-center text-gray-400 text-2xl">
                    🏪
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-gray-900 truncate">{r.name}</div>
                  {r.address && (
                    <div className="text-sm text-gray-500 truncate">{r.address}</div>
                  )}
                  {r.rating != null && (
                    <div className="text-sm text-gray-600 mt-0.5">
                      <span className="text-yellow-500">★</span> {r.rating.toFixed(1)}
                      {r.user_rating_count != null && (
                        <span className="text-gray-400 ml-1">({r.user_rating_count})</span>
                      )}
                    </div>
                  )}
                </div>
                {resolving === r.place_id ? (
                  <div className="h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin flex-shrink-0" />
                ) : (
                  <svg className="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        )}

        {/* No results */}
        {!searching && hasSearched && results.length === 0 && query.trim() && (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-1">No businesses found</p>
            <p className="text-sm">Try a different search term.</p>
          </div>
        )}
      </div>
    </div>
  )
}
