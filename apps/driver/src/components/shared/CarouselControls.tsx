// Carousel controls component matching Figma exactly
interface CarouselControlsProps {
  currentIndex: number
  totalItems: number
  onPrevious: () => void
  onNext: () => void
  onDotClick: (index: number) => void
  className?: string
  labelText?: string // Optional custom label text
}

export function CarouselControls({
  currentIndex,
  totalItems,
  onPrevious,
  onNext,
  onDotClick,
  className = '',
  labelText = 'More nearby while you charge',
}: CarouselControlsProps) {
  const canGoPrevious = currentIndex > 0
  const canGoNext = currentIndex < totalItems - 1

  return (
    <div className={`flex items-center justify-between px-5 pt-5 pb-4 border-t border-[#E4E6EB] ${className}`}>
      {/* Left arrow button - 50x50px matching Figma */}
      <button
        onClick={onPrevious}
        disabled={!canGoPrevious}
        className={`w-[50px] h-[50px] rounded-full flex items-center justify-center transition-all border border-[#E4E6EB] ${
          canGoPrevious
            ? 'bg-[#F7F8FA] hover:bg-gray-50 active:scale-95 text-[#050505]'
            : 'bg-gray-100 text-gray-400 cursor-not-allowed'
        }`}
        aria-label="Previous"
      >
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M15 19l-7-7 7-7"
          />
        </svg>
      </button>

      {/* Center section: Pagination dots + "More nearby while you charge" text */}
      <div className="flex flex-col items-center justify-center gap-2 flex-1 min-w-0 mx-4">
        {/* Pagination dots - properly centered and scaled */}
        <div className="flex items-center justify-center gap-0.5">
          {Array.from({ length: totalItems }).map((_, index) => (
            <button
              key={index}
              onClick={() => onDotClick(index)}
              className="relative flex items-center justify-center min-w-[44px] min-h-[44px] flex-shrink-0"
              aria-label={`Go to page ${index + 1} of ${totalItems}`}
            >
              <span className={`block transition-all rounded-full ${
                index === currentIndex
                  ? 'w-8 h-2 bg-[#1877F2]'
                  : 'w-2 h-2 bg-[#E4E6EB]'
              }`} />
            </button>
          ))}
        </div>
        
        {/* Label text - 12px Regular, gray */}
        <p className="text-xs font-normal leading-4 text-[#656A6B] text-center whitespace-nowrap">
          {labelText}
        </p>
      </div>

      {/* Right arrow button - 50x50px matching Figma */}
      <button
        onClick={onNext}
        disabled={!canGoNext}
        className={`w-[50px] h-[50px] rounded-full flex items-center justify-center transition-all border border-[#E4E6EB] ${
          canGoNext
            ? 'bg-[#F7F8FA] hover:bg-gray-50 active:scale-95 text-[#050505]'
            : 'bg-gray-100 text-gray-400 cursor-not-allowed'
        }`}
        aria-label="Next"
      >
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M9 5l7 7-7 7"
          />
        </svg>
      </button>
    </div>
  )
}
