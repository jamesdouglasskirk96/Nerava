// Carousel component matching Figma: shows exactly 3 cards (1 featured + 2 secondary)
import { useState, useMemo } from 'react'
import { CarouselControls } from './CarouselControls'

interface CarouselItem {
  id: string
}

interface CarouselProps<T extends CarouselItem> {
  items: T[]
  renderPrimary: (item: T) => React.ReactNode
  renderSecondary: (item: T) => React.ReactNode
  className?: string
}

export function Carousel<T extends CarouselItem>({
  items,
  renderPrimary,
  renderSecondary,
  className = '',
}: CarouselProps<T>) {
  const [currentIndex, setCurrentIndex] = useState(0)

  // Rotate items array based on current index - always show 3 cards
  const rotatedItems = useMemo(() => {
    if (items.length === 0) return []
    const rotated: T[] = []
    // Always show 3 cards: current + next 2
    for (let i = 0; i < Math.min(3, items.length); i++) {
      rotated.push(items[(currentIndex + i) % items.length])
    }
    return rotated
  }, [items, currentIndex])

  const primaryItem = rotatedItems[0]
  const secondaryItems = rotatedItems.slice(1, 3) // Get next 2 items

  const handlePrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? items.length - 1 : prev - 1))
  }

  const handleNext = () => {
    setCurrentIndex((prev) => (prev === items.length - 1 ? 0 : prev + 1))
  }

  const handleDotClick = (index: number) => {
    setCurrentIndex(index)
  }

  if (items.length === 0) {
    return <div className="text-center text-gray-500 py-8">No items to display</div>
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Primary card */}
      {primaryItem && (
        <div className="transition-opacity duration-300 flex-shrink-0">
          {renderPrimary(primaryItem)}
        </div>
      )}

      {/* Secondary cards - 2-column grid with reduced gap for mobile */}
      {secondaryItems.length > 0 && (
        <div className="grid grid-cols-2 gap-2 flex-shrink-0">
          {/* Always render 2 slots - fill with items or empty divs */}
          {Array.from({ length: 2 }).map((_, index) => {
            const item = secondaryItems[index]
            if (item) {
              return (
                <div key={item.id} className="transition-opacity duration-300">
                  {renderSecondary(item)}
                </div>
              )
            }
            // Empty slot - use a stable key
            return (
              <div 
                key={`empty-slot-${currentIndex}-${index}`} 
                className="transition-opacity duration-300" 
                aria-hidden="true"
              />
            )
          })}
        </div>
      )}

      {/* Controls */}
      {items.length > 1 && (
        <CarouselControls
          currentIndex={currentIndex}
          totalItems={items.length}
          onPrevious={handlePrevious}
          onNext={handleNext}
          onDotClick={handleDotClick}
          className="mt-4"
        />
      )}
    </div>
  )
}

