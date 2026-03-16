import { useRef, useState, useEffect, useCallback } from 'react'
import { DiscoveryCard } from './DiscoveryCard'
import type { DiscoveryItem, SheetPosition } from './discovery-types'
import { getItemId } from './discovery-types'

interface DiscoverySheetProps {
  items: DiscoveryItem[]
  selectedId: string | null
  onSelectItem: (id: string) => void
  position: SheetPosition
  onPositionChange: (position: SheetPosition) => void
  likedMerchants: string[]
  onToggleLike: (id: string) => void
  onRefresh: () => void
  isLoading: boolean
}

export function DiscoverySheet({
  items,
  selectedId,
  onSelectItem,
  position,
  onPositionChange,
  likedMerchants,
  onToggleLike,
  onRefresh,
  isLoading,
}: DiscoverySheetProps) {
  const contentRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [startY, setStartY] = useState(0)
  const [currentY, setCurrentY] = useState(0)

  // Scroll to selected card
  useEffect(() => {
    if (selectedId && contentRef.current) {
      const selectedIndex = items.findIndex(
        (item) => getItemId(item) === selectedId
      )
      if (selectedIndex !== -1) {
        const cardElement = contentRef.current.children[selectedIndex] as HTMLElement
        cardElement?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      }
    }
  }, [selectedId, items])

  const getSheetHeight = () => {
    if (position === 'peek') return '160px'
    if (position === 'half') return '45vh'
    return '92vh'
  }

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    setIsDragging(true)
    setStartY(e.touches[0].clientY)
    setCurrentY(e.touches[0].clientY)
  }, [])

  const handleTouchMove = useCallback(
    (e: React.TouchEvent) => {
      if (!isDragging) return
      setCurrentY(e.touches[0].clientY)
    },
    [isDragging]
  )

  const handleTouchEnd = useCallback(() => {
    if (!isDragging) return

    const deltaY = currentY - startY
    const threshold = 50

    if (deltaY > threshold) {
      // Swipe down
      if (position === 'full') onPositionChange('half')
      else if (position === 'half') onPositionChange('peek')
    } else if (deltaY < -threshold) {
      // Swipe up
      if (position === 'peek') onPositionChange('half')
      else if (position === 'half') onPositionChange('full')
    }

    setIsDragging(false)
  }, [isDragging, currentY, startY, position, onPositionChange])

  const chargerCount = items.filter((item) => item.type === 'charger').length

  return (
    <div
      className="absolute left-0 right-0 bottom-0 bg-white rounded-t-[20px] shadow-[0_-4px_20px_rgba(0,0,0,0.08)] z-[2000]"
      style={{
        height: getSheetHeight(),
        transition: isDragging ? 'none' : 'height 0.3s cubic-bezier(0.22, 1, 0.36, 1)',
        touchAction: 'none',
      }}
    >
      {/* Drag Handle */}
      <div
        className="pt-3 pb-2 cursor-grab active:cursor-grabbing"
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <div className="w-9 h-1 bg-[#E4E6EB] rounded-full mx-auto" />
        <div className="px-4 mt-2">
          <p className="text-xs font-medium text-[#656A6B]">
            {chargerCount} {chargerCount === 1 ? 'charger' : 'chargers'} nearby
          </p>
        </div>
      </div>

      {/* Card List */}
      <div
        ref={contentRef}
        className="overflow-y-auto"
        style={{ height: 'calc(100% - 60px)' }}
      >
        {items.length > 0 ? (
          items.map((item) => {
            const id = getItemId(item)
            const isFav = likedMerchants.includes(id)
            return (
              <DiscoveryCard
                key={id}
                item={item}
                isSelected={selectedId === id}
                onSelect={() => onSelectItem(id)}
                isFavorite={isFav}
                onToggleFavorite={() => onToggleLike(id)}
              />
            )
          })
        ) : (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <div className="w-12 h-12 rounded-full bg-[#F7F8FA] flex items-center justify-center mb-3">
              <svg
                className="w-6 h-6 text-[#9E9E9E]"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-[#050505] mb-1">
              {isLoading ? 'Loading nearby chargers...' : 'No chargers found nearby'}
            </h3>
            <p className="text-sm text-[#656A6B] mb-4">
              Try expanding your search area
            </p>
            {!isLoading && (
              <button
                onClick={onRefresh}
                className="px-6 py-2 bg-[#1877F2] text-white rounded-full text-sm font-medium hover:bg-[#0D5DBF] transition-colors"
              >
                Refresh
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
