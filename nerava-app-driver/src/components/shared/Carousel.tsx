// Carousel component - single card at a time
import { useState } from 'react'
import { CarouselControls } from './CarouselControls'

interface CarouselItem {
  id: string
  [key: string]: unknown
}

interface CarouselProps<T extends CarouselItem> {
  items: T[]
  renderItem: (item: T) => React.ReactNode
  className?: string
  transitionMessage?: React.ReactNode
}

export function Carousel<T extends CarouselItem>({
  items,
  renderItem,
  className = '',
  transitionMessage,
}: CarouselProps<T>) {
  const [currentIndex, setCurrentIndex] = useState(0)

  const currentItem = items[currentIndex]

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
    <div className={`flex flex-col h-full ${className}`}>
      {/* Single merchant card */}
      <div className="flex-1 min-h-0">
        {currentItem && (
          <div className="h-full transition-opacity duration-300">
            {renderItem(currentItem)}
          </div>
        )}
      </div>

      {/* Transition message - below card, above navigation */}
      {transitionMessage && (
        <div className="flex-shrink-0">
          {transitionMessage}
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
          className="flex-shrink-0"
          labelText="Swipe for more"
        />
      )}
    </div>
  )
}

