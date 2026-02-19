import { createContext, useContext, useState, useEffect } from 'react'
import type { ReactNode } from 'react'

interface FavoritesContextType {
  favorites: Set<string>
  toggleFavorite: (merchantId: string) => Promise<void>
  isFavorite: (merchantId: string) => boolean
  isLoading: boolean
}

const FavoritesContext = createContext<FavoritesContextType | null>(null)

export function FavoritesProvider({ children }: { children: ReactNode }) {
  const [favorites, setFavorites] = useState<Set<string>>(() => {
    const stored = localStorage.getItem('neravaLikes')
    return stored ? new Set(JSON.parse(stored)) : new Set()
  })
  const [isLoading, setIsLoading] = useState(false)

  // Sync with localStorage
  useEffect(() => {
    localStorage.setItem('neravaLikes', JSON.stringify(Array.from(favorites)))
  }, [favorites])

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
        setFavorites(new Set(data.map((f: any) => f.merchant_id)))
      }
    } catch (e) {
      console.error('Failed to fetch favorites', e)
    } finally {
      setIsLoading(false)
    }
  }

  const toggleFavorite = async (merchantId: string) => {
    const token = localStorage.getItem('access_token')
    const isFav = favorites.has(merchantId)

    // Optimistic update
    setFavorites(prev => {
      const next = new Set(prev)
      isFav ? next.delete(merchantId) : next.add(merchantId)
      return next
    })

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
  }

  const isFavorite = (merchantId: string) => favorites.has(merchantId)

  return (
    <FavoritesContext.Provider value={{ favorites, toggleFavorite, isFavorite, isLoading }}>
      {children}
    </FavoritesContext.Provider>
  )
}

export function useFavorites() {
  const ctx = useContext(FavoritesContext)
  if (!ctx) throw new Error('useFavorites must be used within FavoritesProvider')
  return ctx
}




