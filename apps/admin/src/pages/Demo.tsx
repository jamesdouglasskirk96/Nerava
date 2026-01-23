import { useState } from 'react'
import { setDemoLocation } from '../services/api'
import { capture, ADMIN_EVENTS } from '../analytics'

export default function Demo() {
  const [lat, setLat] = useState('30.2672')
  const [lng, setLng] = useState('-97.7431')
  const [chargerId, setChargerId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(false)

    try {
      await setDemoLocation(parseFloat(lat), parseFloat(lng), chargerId || undefined)
      
      capture(ADMIN_EVENTS.DEMO_LOCATION_OVERRIDE_SET_SUCCESS, {
        latitude: parseFloat(lat),
        longitude: parseFloat(lng),
        charger_id: chargerId || undefined,
      })
      
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to set demo location'
      
      capture(ADMIN_EVENTS.DEMO_LOCATION_OVERRIDE_SET_FAIL, {
        error: errorMessage,
        latitude: parseFloat(lat),
        longitude: parseFloat(lng),
      })
      
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '600px' }}>
      <h1>Demo Location Override</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Set a static location for demo driver mode. Requires DEMO_STATIC_DRIVER_ENABLED=true.
      </p>

      {error && (
        <div style={{ 
          background: '#fee', 
          border: '1px solid #fcc', 
          padding: '1rem', 
          borderRadius: '4px',
          marginBottom: '1rem',
          color: '#c33'
        }}>
          {error}
        </div>
      )}

      {success && (
        <div style={{ 
          background: '#efe', 
          border: '1px solid #cfc', 
          padding: '1rem', 
          borderRadius: '4px',
          marginBottom: '1rem',
          color: '#3c3'
        }}>
          Demo location set successfully!
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Latitude
          </label>
          <input
            type="number"
            step="any"
            value={lat}
            onChange={(e) => setLat(e.target.value)}
            required
            style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Longitude
          </label>
          <input
            type="number"
            step="any"
            value={lng}
            onChange={(e) => setLng(e.target.value)}
            required
            style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Charger ID (optional)
          </label>
          <input
            type="text"
            value={chargerId}
            onChange={(e) => setChargerId(e.target.value)}
            style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '0.75rem 1.5rem',
            background: loading ? '#ccc' : '#000',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontWeight: 'bold'
          }}
        >
          {loading ? 'Setting...' : 'Set Demo Location'}
        </button>
      </form>
    </div>
  )
}

