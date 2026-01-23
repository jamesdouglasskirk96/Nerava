import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

// Detect API base URL: use env var if set, otherwise detect from hostname
function getApiBaseUrl(): string {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  // If running on production domain, use production API
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname
    if (hostname.includes('nerava.network') || hostname.includes('nerava.app')) {
      return 'https://api.nerava.network'
    }
  }
  // Default to localhost for local development
  return 'http://localhost:8001'
}

const API_BASE_URL = getApiBaseUrl()

interface QRResponse {
  ok: boolean
  route: string
  cluster_id?: string
  charger?: {
    address: string
    lat: number
    lng: number
    charger_radius_m: number
    merchant_radius_m: number
  }
}

async function fetchQRData(token: string): Promise<QRResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/checkout/qr/${token}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch QR data: ${response.statusText}`)
  }
  return response.json()
}

export function QRHandler() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()

  const { data, isLoading, error } = useQuery({
    queryKey: ['qr', token],
    queryFn: () => fetchQRData(token!),
    enabled: !!token,
    retry: false,
  })

  useEffect(() => {
    if (data) {
      // Extract cluster_id from route or use cluster_id directly
      const clusterId = data.cluster_id || (data.route.includes('cluster_id=') 
        ? new URLSearchParams(data.route.split('?')[1]).get('cluster_id')
        : null)
      
      if (clusterId) {
        navigate(`/app/party?cluster_id=${clusterId}`, { replace: true })
      } else {
        // Fallback to route if no cluster_id
        navigate(data.route, { replace: true })
      }
    }
  }, [data, navigate])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-[#65676B]">Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600">Error loading QR code</p>
          <p className="text-sm text-[#65676B] mt-2">{error instanceof Error ? error.message : 'Unknown error'}</p>
        </div>
      </div>
    )
  }

  return null
}


