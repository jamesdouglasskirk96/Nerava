// Tooltip component explaining "Exclusive" terminology
import { useState, useRef, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { Info } from 'lucide-react'

interface ExclusiveInfoTooltipProps {
  className?: string
}

export function ExclusiveInfoTooltip({ className = '' }: ExclusiveInfoTooltipProps) {
  const [showTooltip, setShowTooltip] = useState(false)
  const [tooltipStyle, setTooltipStyle] = useState<React.CSSProperties>({})
  const buttonRef = useRef<HTMLButtonElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)

  const updatePosition = useCallback(() => {
    if (!buttonRef.current) return

    const buttonRect = buttonRef.current.getBoundingClientRect()
    const tooltipWidth = 256 // w-64 = 16rem = 256px
    const padding = 12

    // Position tooltip above the button, centered
    let left = buttonRect.left + buttonRect.width / 2 - tooltipWidth / 2

    // Ensure tooltip stays within viewport bounds
    if (left < padding) {
      left = padding
    } else if (left + tooltipWidth > window.innerWidth - padding) {
      left = window.innerWidth - tooltipWidth - padding
    }

    setTooltipStyle({
      position: 'fixed',
      top: buttonRect.top - 8, // 8px above button
      left,
      transform: 'translateY(-100%)',
      width: tooltipWidth,
      zIndex: 9999,
    })
  }, [])

  useEffect(() => {
    if (showTooltip) {
      updatePosition()
      window.addEventListener('scroll', updatePosition, true)
      window.addEventListener('resize', updatePosition)
      return () => {
        window.removeEventListener('scroll', updatePosition, true)
        window.removeEventListener('resize', updatePosition)
      }
    }
  }, [showTooltip, updatePosition])

  const handleClick = () => {
    setShowTooltip(!showTooltip)
  }

  const handleClickOutside = useCallback((e: MouseEvent) => {
    if (
      buttonRef.current &&
      !buttonRef.current.contains(e.target as Node) &&
      tooltipRef.current &&
      !tooltipRef.current.contains(e.target as Node)
    ) {
      setShowTooltip(false)
    }
  }, [])

  useEffect(() => {
    if (showTooltip) {
      document.addEventListener('click', handleClickOutside)
      return () => document.removeEventListener('click', handleClickOutside)
    }
  }, [showTooltip, handleClickOutside])

  return (
    <div className={`relative inline-block ${className}`}>
      <button
        ref={buttonRef}
        type="button"
        onClick={handleClick}
        className="inline-flex items-center justify-center w-4 h-4 rounded-full bg-[#1877F2]/10 text-[#1877F2] hover:bg-[#1877F2]/20 transition-colors"
        aria-label="What is Exclusive?"
      >
        <Info className="w-3 h-3" />
      </button>

      {showTooltip && createPortal(
        <div
          ref={tooltipRef}
          style={tooltipStyle}
          className="p-3 bg-[#050505] text-white text-xs rounded-lg shadow-lg"
        >
          <p className="leading-relaxed">
            Exclusive = a special offer for Nerava users, redeemable during your charging session.
          </p>
          {/* Arrow - positioned based on button location */}
          <div
            className="absolute top-full -mt-1"
            style={{
              left: buttonRef.current
                ? buttonRef.current.getBoundingClientRect().left + buttonRef.current.getBoundingClientRect().width / 2 - (tooltipStyle.left as number || 0)
                : '50%',
              transform: 'translateX(-50%)'
            }}
          >
            <div className="w-2 h-2 bg-[#050505] rotate-45"></div>
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}





