import { ArrowLeft, Heart, MapPin } from 'lucide-react'
import { useFavorites } from '../../contexts/FavoritesContext'
import { ImageWithFallback } from '../shared/ImageWithFallback'

interface FavoritesViewProps {
  onBack: () => void
  onMerchantClick?: (merchantId: string) => void
}

export function FavoritesView({ onBack, onMerchantClick }: FavoritesViewProps) {
  const { favorites, loading, toggleFavorite } = useFavorites()

  return (
    <div className="h-[100dvh] flex flex-col bg-white">
      {/* Header */}
      <header className="px-5 h-[60px] flex items-center border-b border-[#E4E6EB]">
        <button onClick={onBack} className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="ml-4 text-lg font-medium">Favorites</h1>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin w-8 h-8 border-2 border-[#1877F2] border-t-transparent rounded-full" />
          </div>
        ) : favorites.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-[#65676B] p-8">
            <Heart className="w-16 h-16 mb-4 text-gray-300" />
            <p className="text-lg font-medium">No favorites yet</p>
            <p className="text-sm text-center mt-2">
              Tap the heart icon on merchants you love to save them here
            </p>
          </div>
        ) : (
          <div className="divide-y divide-[#E4E6EB]">
            {favorites.map((merchant) => (
              <button
                key={merchant.merchant_id}
                onClick={() => onMerchantClick?.(merchant.merchant_id)}
                className="w-full flex items-center p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="w-16 h-16 rounded-xl overflow-hidden flex-shrink-0">
                  <ImageWithFallback
                    src={merchant.photo_url || ''}
                    alt={merchant.name || 'Merchant'}
                    category={merchant.category || 'retail'}
                    className="w-full h-full"
                  />
                </div>
                <div className="ml-4 flex-1 text-left">
                  <h3 className="font-medium text-[#050505]">{merchant.name || 'Merchant'}</h3>
                  {merchant.category && (
                    <p className="text-sm text-[#65676B]">{merchant.category}</p>
                  )}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    toggleFavorite(merchant.merchant_id)
                  }}
                  className="w-10 h-10 flex items-center justify-center"
                >
                  <Heart className="w-5 h-5 text-red-500 fill-red-500" />
                </button>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}


