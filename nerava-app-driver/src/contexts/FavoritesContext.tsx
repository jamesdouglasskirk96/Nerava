import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchAPI } from '../services/api'

interface Favorite {
  merchant_id: string
  name?: string
  category?: string
  photo_url?: string
}

interface FavoritesContextType {
  favorites: Favorite[]
  favoriteIds: Set<string>
  loading: boolean
  isFavorited: (merchantId: string) => boolean
  toggleFavorite: (merchantId: string) => Promise<void>
  refreshFavorites: () => void
}

const FavoritesContext = createContext<FavoritesContextType | null>(null)

export function FavoritesProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const isAuthenticated = !!localStorage.getItem('access_token')

  // Local state for immediate UI updates
  const [favoriteIds, setFavoriteIds] = useState<Set<string>>(() => {
    // Initialize from localStorage for instant display
    const stored = localStorage.getItem('neravaLikes')
    if (stored) {
      try {
        return new Set(JSON.parse(stored) as string[])
      } catch {
        return new Set()
      }
    }
    return new Set()
  })

  // Fetch favorites from backend
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['favorites'],
    queryFn: async () => {
      if (!isAuthenticated) return { favorites: [] }
      return fetchAPI<{ favorites: Favorite[] }>('/v1/merchants/favorites')
    },
    enabled: isAuthenticated,
    staleTime: 1000 * 60 * 5,
  })

  // Sync backend data to local state
  useEffect(() => {
    if (data?.favorites) {
      const ids = new Set(data.favorites.map(f => f.merchant_id))
      setFavoriteIds(ids)
      localStorage.setItem('neravaLikes', JSON.stringify([...ids]))
    }
  }, [data])

  // Add mutation
  const addMutation = useMutation({
    mutationFn: (merchantId: string) =>
      fetchAPI(`/v1/merchants/${merchantId}/favorite`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['favorites'] }),
  })

  // Remove mutation
  const removeMutation = useMutation({
    mutationFn: (merchantId: string) =>
      fetchAPI(`/v1/merchants/${merchantId}/favorite`, { method: 'DELETE' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['favorites'] }),
  })

  const isFavorited = useCallback((merchantId: string) => {
    return favoriteIds.has(merchantId)
  }, [favoriteIds])

  const toggleFavorite = useCallback(async (merchantId: string) => {
    const isCurrentlyFavorited = favoriteIds.has(merchantId)

    // Optimistic update
    setFavoriteIds(prev => {
      const next = new Set(prev)
      if (isCurrentlyFavorited) {
        next.delete(merchantId)
      } else {
        next.add(merchantId)
      }
      localStorage.setItem('neravaLikes', JSON.stringify([...next]))
      return next
    })

    // Backend call
    try {
      if (isCurrentlyFavorited) {
        await removeMutation.mutateAsync(merchantId)
      } else {
        await addMutation.mutateAsync(merchantId)
      }
    } catch (error) {
      // Revert on error
      refetch()
    }
  }, [favoriteIds, addMutation, removeMutation, refetch])

  return (
    <FavoritesContext.Provider value={{
      favorites: data?.favorites || [],
      favoriteIds,
      loading: isLoading,
      isFavorited,
      toggleFavorite,
      refreshFavorites: refetch,
    }}>
      {children}
    </FavoritesContext.Provider>
  )
}

export function useFavorites() {
  const context = useContext(FavoritesContext)
  if (!context) {
    throw new Error('useFavorites must be used within FavoritesProvider')
  }
  return context
}


