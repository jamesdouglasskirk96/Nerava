import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import type { ReactNode } from 'react'

export interface FavoriteMerchantInfo {
  name: string
  category?: string
  photo_url?: string
}

interface FavoritesContextType {
  favorites: Set<string>
  favoriteDetails: Map<string, FavoriteMerchantInfo>
  toggleFavorite: (merchantId: string, name?: string) => Promise<void>
  isFavorite: (merchantId: string) => boolean
  getMerchantName: (merchantId: string) => string
  isLoading: boolean
}

const FavoritesContext = createContext<FavoritesContextType | null>(null)

function formatMerchantIdFallback(id: string): string {
  return id
    .replace(/^(way_|node_|m_)/, '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
}

export function FavoritesProvider({ children }: { children: ReactNode }) {
  const [favorites, setFavorites] = useState<Set<string>>(() => {
    const stored = localStorage.getItem('neravaLikes')
    return stored ? new Set(JSON.parse(stored)) : new Set()
  })
  const [favoriteDetails, setFavoriteDetails] = useState<Map<string, FavoriteMerchantInfo>>(() => {
    const stored = localStorage.getItem('neravaLikeDetails')
    if (stored) {
      try {
        return new Map(JSON.parse(stored))
      } catch { /* ignore */ }
    }
    return new Map()
  })
  const [isLoading, setIsLoading] = useState(false)

  // Sync with localStorage
  useEffect(() => {
    localStorage.setItem('neravaLikes', JSON.stringify(Array.from(favorites)))
  }, [favorites])

  useEffect(() => {
    localStorage.setItem('neravaLikeDetails', JSON.stringify(Array.from(favoriteDetails.entries())))
  }, [favoriteDetails])

  // Load from backend if authenticated
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      fetchFavorites(token)
    }
  }, [])

  const fetchFavorites = async (token: string) => {
    try {
      setIsLoading(true)
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'https://api.nerava.network'
      const res = await fetch(`${apiBaseUrl}/v1/merchants/favorites`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        const items = data.favorites || data || []
        if (Array.isArray(items)) {
          setFavorites(new Set(items.map((f: any) => f.merchant_id)))
          const details = new Map<string, FavoriteMerchantInfo>()
          for (const f of items) {
            if (f.name) {
              details.set(f.merchant_id, {
                name: f.name,
                category: f.category,
                photo_url: f.photo_url,
              })
            }
          }
          setFavoriteDetails(prev => {
            const merged = new Map(prev)
            details.forEach((v, k) => merged.set(k, v))
            return merged
          })
        }
      }
    } catch (e) {
      console.error('Failed to fetch favorites', e)
    } finally {
      setIsLoading(false)
    }
  }

  const toggleFavorite = useCallback(async (merchantId: string, name?: string) => {
    const token = localStorage.getItem('access_token')
    const isFav = favorites.has(merchantId)

    // Optimistic update
    setFavorites(prev => {
      const next = new Set(prev)
      isFav ? next.delete(merchantId) : next.add(merchantId)
      return next
    })

    // Store name if adding and name provided
    if (!isFav && name) {
      setFavoriteDetails(prev => {
        const next = new Map(prev)
        next.set(merchantId, { name })
        return next
      })
    }

    // Sync with backend if authenticated
    if (token) {
      try {
        const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'https://api.nerava.network'
        await fetch(`${apiBaseUrl}/v1/merchants/${merchantId}/favorite`, {
          method: isFav ? 'DELETE' : 'POST',
          headers: { Authorization: `Bearer ${token}` }
        })
      } catch (e) {
        // Revert on failure
        setFavorites(prev => {
          const next = new Set(prev)
          isFav ? next.add(merchantId) : next.delete(merchantId)
          return next
        })
        console.error('Failed to toggle favorite', e)
      }
    }
  }, [favorites])

  const isFavorite = useCallback((merchantId: string) => favorites.has(merchantId), [favorites])

  const getMerchantName = useCallback((merchantId: string) => {
    const details = favoriteDetails.get(merchantId)
    return details?.name || formatMerchantIdFallback(merchantId)
  }, [favoriteDetails])

  return (
    <FavoritesContext.Provider value={{ favorites, favoriteDetails, toggleFavorite, isFavorite, getMerchantName, isLoading }}>
      {children}
    </FavoritesContext.Provider>
  )
}

export function useFavorites() {
  const ctx = useContext(FavoritesContext)
  if (!ctx) throw new Error('useFavorites must be used within FavoritesProvider')
  return ctx
}




