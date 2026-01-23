import { useState, useEffect } from 'react'
import './Merchants.css'
import { searchMerchants, getMerchantStatus, type Merchant } from '../services/api'
import { capture, ADMIN_EVENTS } from '../analytics'

interface MerchantStatus {
  merchant_id: string
  name: string
  status: string
  square_connected: boolean
  square_last_error: string | null
  nova_balance: number
}

export default function Merchants() {
  const [merchants, setMerchants] = useState<Merchant[]>([])
  const [selectedMerchant, setSelectedMerchant] = useState<Merchant | null>(null)
  const [merchantStatus, setMerchantStatus] = useState<MerchantStatus | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // Capture merchants view event on mount
    capture(ADMIN_EVENTS.MERCHANTS_VIEW)
    
    if (searchQuery) {
      searchMerchantsHandler()
    }
  }, [searchQuery])

  const searchMerchantsHandler = async () => {
    setLoading(true)
    try {
      const data = await searchMerchants(searchQuery)
      setMerchants(data.merchants || [])
    } catch (error) {
      console.error('Error searching merchants:', error)
      setMerchants([])
    } finally {
      setLoading(false)
    }
  }

  const loadMerchantStatus = async (merchantId: string) => {
    setLoading(true)
    try {
      const data = await getMerchantStatus(merchantId)
      setMerchantStatus(data as MerchantStatus)
    } catch (error) {
      console.error('Error loading merchant status:', error)
      setMerchantStatus(null)
    } finally {
      setLoading(false)
    }
  }

  const handleMerchantClick = (merchant: Merchant) => {
    setSelectedMerchant(merchant)
    loadMerchantStatus(merchant.id)
  }

  return (
    <div className="merchants-page">
      <h1>Merchants</h1>
      
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
          <h2>Search Results</h2>
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
                <span>Nova: {merchant.nova_balance}</span>
              </div>
            </div>
          ))}
        </div>

        {selectedMerchant && merchantStatus && (
          <div className="merchant-detail">
            <h2>Merchant Status</h2>
            <div className="detail-section">
              <h3>{merchantStatus.name}</h3>
              <p>ID: {merchantStatus.merchant_id}</p>
              <p>Status: {merchantStatus.status}</p>
            </div>

            <div className="detail-section">
              <h3>Square Integration</h3>
              <p>Connected: {merchantStatus.square_connected ? 'Yes' : 'No'}</p>
              {merchantStatus.square_last_error && (
                <div className="error-box">
                  <strong>Last Error:</strong> {merchantStatus.square_last_error}
                </div>
              )}
            </div>

            <div className="detail-section">
              <h3>Balance</h3>
              <p>Nova Balance: {merchantStatus.nova_balance}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}







