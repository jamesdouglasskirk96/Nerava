// Hook for managing merchant favorites
import { useState, useEffect, useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchAPI } from '../services/api'
import { ApiError } from '../services/api'

interface FavoriteResponse {
  ok: boolean
  is_favorite: boolean
}

/**
 * Hook to manage favorite status for a merchant
 * Returns favorite state and toggle function
 */
export function useFavoriteMerchant(merchantId: string | null) {
  const queryClient = useQueryClient()
  const [isFavorite, setIsFavorite] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  // Check if user is authenticated by checking for access token
  const isAuthenticated = !!localStorage.getItem('access_token')

  // Check favorite status - only fetch favorites if authenticated
  const { data: favoritesData } = useQuery({
    queryKey: ['favorites'],
    queryFn: async () => {
      // Guard: don't fetch if not authenticated
      if (!isAuthenticated) {
        return { favorites: [] }
      }
      return fetchAPI<{ favorites: Array<{ merchant_id: string }> }>('/v1/merchants/favorites')
    },
    enabled: isAuthenticated,  // Disable query when not authenticated
    staleTime: 1000 * 60 * 5,  // Cache for 5 minutes
    retry: false,
  })

  // Update local state when favorites data changes
  useEffect(() => {
    if (isAuthenticated && favoritesData && merchantId) {
      const isFav = favoritesData.favorites.some(f => f.merchant_id === merchantId)
      setIsFavorite(isFav)
    } else if (!isAuthenticated) {
      // Unauthenticated users see isFavorite = false
      setIsFavorite(false)
    }
  }, [favoritesData, merchantId, isAuthenticated])

  // Add favorite mutation
  const addFavoriteMutation = useMutation({
    mutationFn: async (merchantId: string) => {
      return fetchAPI<FavoriteResponse>(`/v1/merchants/${merchantId}/favorite`, {
        method: 'POST',
      })
    },
    onSuccess: () => {
      // Invalidate favorites query to refetch
      queryClient.invalidateQueries({ queryKey: ['favorites'] })
    },
  })

  // Remove favorite mutation
  const removeFavoriteMutation = useMutation({
    mutationFn: async (merchantId: string) => {
      return fetchAPI<FavoriteResponse>(`/v1/merchants/${merchantId}/favorite`, {
        method: 'DELETE',
      })
    },
    onSuccess: () => {
      // Invalidate favorites query to refetch
      queryClient.invalidateQueries({ queryKey: ['favorites'] })
    },
  })

  // Toggle favorite
  const toggleFavorite = useCallback(async () => {
    if (!merchantId) return

    setIsLoading(true)
    try {
      if (isFavorite) {
        await removeFavoriteMutation.mutateAsync(merchantId)
        setIsFavorite(false)
      } else {
        await addFavoriteMutation.mutateAsync(merchantId)
        setIsFavorite(true)
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error)
      // Revert optimistic update on error
      setIsFavorite(!isFavorite)
      if (error instanceof ApiError) {
        throw error
      }
    } finally {
      setIsLoading(false)
    }
  }, [merchantId, isFavorite, addFavoriteMutation, removeFavoriteMutation])

  return {
    isFavorite,
    toggleFavorite,
    isLoading: isLoading || addFavoriteMutation.isPending || removeFavoriteMutation.isPending,
  }
}

