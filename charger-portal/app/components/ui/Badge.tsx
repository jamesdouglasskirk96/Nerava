import type { ActivityType } from '@/lib/types/dashboard'

interface BadgeProps {
  children: React.ReactNode
  variant?: ActivityType | 'default' | 'success' | 'warning' | 'info'
  className?: string
}

const variantStyles: Record<string, string> = {
  SAVINGS: 'bg-green-100 text-green-800',
  REWARD: 'bg-blue-100 text-blue-800',
  TOP_UP: 'bg-purple-100 text-purple-800',
  PURCHASE: 'bg-indigo-100 text-indigo-800',
  SYSTEM: 'bg-gray-100 text-gray-800',
  default: 'bg-gray-100 text-gray-800',
  success: 'bg-green-100 text-green-800',
  warning: 'bg-yellow-100 text-yellow-800',
  info: 'bg-blue-100 text-blue-800',
}

export function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  )
}

