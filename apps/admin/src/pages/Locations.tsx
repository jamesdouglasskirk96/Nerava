import { useState, useEffect } from 'react'
import './Locations.css'

interface Merchant {
  id: string
  name: string
  status: string
  zone_slug: string
  nova_balance: number
  created_at: string
}

interface GooglePlaceCandidate {
  place_id: string
  name: string
  formatted_address: string
  geometry: {
    location: {
      lat: number
      lng: number
    }
  }
  rating?: number
  types: string[]
}

export default function Locations() {
  const [merchants, setMerchants] = useState<Merchant[]>([])
  const [selectedMerchant, setSelectedMerchant] = useState<Merchant | null>(null)
  const [candidates, setCandidates] = useState<GooglePlaceCandidate[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [resolving, setResolving] = useState(false)

  useEffect(() => {
    if (searchQuery) {
      searchMerchants()
    }
  }, [searchQuery])

  const searchMerchants = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/v1/admin/merchants?query=${encodeURIComponent(searchQuery)}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token') || localStorage.getItem('admin_token') || ''}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setMerchants(data.merchants || [])
      } else {
        console.error('Failed to search merchants:', response.statusText)
      }
    } catch (error) {
      console.error('Error searching merchants:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadCandidates = async (merchantId: string) => {
    setLoading(true)
    try {
      const response = await fetch(`/api/v1/admin/locations/${merchantId}/google-place/candidates`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token') || localStorage.getItem('admin_token') || ''}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setCandidates(data.candidates || [])
      } else {
        console.error('Failed to load candidates:', response.statusText)
      }
    } catch (error) {
      console.error('Error loading candidates:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleMerchantClick = (merchant: Merchant) => {
    setSelectedMerchant(merchant)
    loadCandidates(merchant.id)
  }

  const handleResolve = async (placeId: string) => {
    if (!selectedMerchant) return

    setResolving(true)
    try {
      const response = await fetch(`/api/v1/admin/locations/${selectedMerchant.id}/google-place/resolve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token') || localStorage.getItem('admin_token') || ''}`
        },
        body: JSON.stringify({ place_id: placeId })
      })
      if (response.ok) {
        const data = await response.json()
        alert(`Google Place ID resolved: ${data.google_place_id}`)
        // Reload candidates
        await loadCandidates(selectedMerchant.id)
      } else {
        const error = await response.json()
        alert(`Failed to resolve: ${error.detail || response.statusText}`)
      }
    } catch (error) {
      console.error('Error resolving place:', error)
      alert('Error resolving Google Place ID')
    } finally {
      setResolving(false)
    }
  }

  return (
    <div className="locations-page">
      <h1>Google Places Mapping</h1>
      
      <div className="search-section">
        <input
          type="text"
          placeholder="Search by merchant name or ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="content-grid">
        <div className="merchants-list">
          <h2>Merchants</h2>
          {loading && <p>Loading...</p>}
          {!loading && merchants.length === 0 && searchQuery && <p>No merchants found</p>}
          {!loading && merchants.length === 0 && !searchQuery && <p>Enter a search query to find merchants</p>}
          {merchants.map(merchant => (
            <div
              key={merchant.id}
              className={`merchant-card ${selectedMerchant?.id === merchant.id ? 'selected' : ''}`}
              onClick={() => handleMerchantClick(merchant)}
            >
              <div className="merchant-name">{merchant.name}</div>
              <div className="merchant-meta">
                <span>Status: {merchant.status}</span>
              </div>
            </div>
          ))}
        </div>

        {selectedMerchant && (
          <div className="candidates-section">
            <h2>Google Places Candidates for {selectedMerchant.name}</h2>
            {loading && <p>Loading candidates...</p>}
            {!loading && candidates.length === 0 && <p>No candidates found</p>}
            {candidates.map(candidate => (
              <div key={candidate.place_id} className="candidate-card">
                <div className="candidate-name">{candidate.name}</div>
                <div className="candidate-address">{candidate.formatted_address}</div>
                {candidate.rating && (
                  <div className="candidate-rating">Rating: {candidate.rating}</div>
                )}
                <button
                  className="btn-primary"
                  onClick={() => handleResolve(candidate.place_id)}
                  disabled={resolving}
                >
                  {resolving ? 'Resolving...' : 'Resolve'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}







