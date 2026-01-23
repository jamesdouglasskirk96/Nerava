// Badge component matching Figma specifications exactly
import type { ReactNode } from 'react'

interface BadgeProps {
  children: ReactNode
  variant?: 'default' | 'featured' | 'featured-white' | 'perk' | 'sponsored' | 'exclusive' | 'walk-time' | 'walk-time-secondary'
  className?: string
}

export function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
  // Base classes matching Figma: 12px font, Medium weight, 16px line-height, pill radius
  const baseClasses = 'inline-flex items-center whitespace-nowrap rounded-full'
  const baseTypography = 'text-xs font-medium leading-4' // 12px Medium, 16px line-height
  
  const variantClasses = {
    default: 'px-3 py-1.5 bg-gray-100 text-gray-800',
    featured: 'px-3 py-1.5 bg-facebook-blue text-white',
    'featured-white': 'px-3 py-1.5 bg-white text-facebook-blue border border-facebook-blue/20',
    perk: 'px-3 py-1.5 bg-yellow-100 text-yellow-800',
    // Figma exact variants (updated to match latest design)
    sponsored: 'px-[13px] pt-[13px] pb-[1px] bg-white/90 text-[#656A6B] border border-[#E4E6EB]',
    exclusive: 'px-[11px] pt-[11px] pb-[1px] text-[#A65F00] border border-[#D08700]/30',
    'walk-time': 'px-3 pt-3 pb-0 bg-facebook-blue text-white',
    'walk-time-secondary': 'px-[10px] pt-[10px] pb-0 bg-facebook-blue/10 text-facebook-blue',
  }

  // Exclusive badge needs gradient background
  if (variant === 'exclusive') {
    return (
      <span 
        className={`${baseClasses} ${baseTypography} ${variantClasses[variant]} ${className}`}
        style={{
          background: 'linear-gradient(90deg, rgba(240, 176, 0, 0.15) 0%, rgba(254, 154, 0, 0.15) 100%)',
        }}
      >
        {children}
      </span>
    )
  }

  return (
    <span className={`${baseClasses} ${baseTypography} ${variantClasses[variant]} ${className}`}>
      {children}
    </span>
  )
}

