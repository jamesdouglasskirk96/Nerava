// Category logo mapping and component
import type { ReactElement } from 'react'

export type Category =
  | 'Coffee'
  | 'Food'
  | 'Fitness'
  | 'Retail'
  | 'Pets'
  | 'Grocery'
  | 'Entertainment'
  | 'Pharmacy'
  | 'Other'

// Map category names to normalized categories
export function normalizeCategory(category: string): Category {
  const lower = category.toLowerCase()
  if (lower.includes('coffee') || lower.includes('cafe')) return 'Coffee'
  if (lower.includes('food') || lower.includes('restaurant') || lower.includes('dining')) return 'Food'
  if (lower.includes('fitness') || lower.includes('gym') || lower.includes('workout')) return 'Fitness'
  if (lower.includes('retail') || lower.includes('store') || lower.includes('shop')) return 'Retail'
  if (lower.includes('pet')) return 'Pets'
  if (lower.includes('grocery') || lower.includes('supermarket') || lower.includes('market')) return 'Grocery'
  if (lower.includes('entertainment') || lower.includes('movie') || lower.includes('theater')) return 'Entertainment'
  if (lower.includes('pharmacy') || lower.includes('drug')) return 'Pharmacy'
  return 'Other'
}

// Category logo SVG components
function CoffeeIcon({ className = 'w-8 h-8' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
      />
    </svg>
  )
}

function FoodIcon({ className = 'w-8 h-8' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
      />
    </svg>
  )
}

function FitnessIcon({ className = 'w-8 h-8' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M13 10V3L4 14h7v7l9-11h-7z"
      />
    </svg>
  )
}

function RetailIcon({ className = 'w-8 h-8' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"
      />
    </svg>
  )
}

function PetsIcon({ className = 'w-8 h-8' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
      />
    </svg>
  )
}

function GroceryIcon({ className = 'w-8 h-8' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
      />
    </svg>
  )
}

function EntertainmentIcon({ className = 'w-8 h-8' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  )
}

function PharmacyIcon({ className = 'w-8 h-8' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
      />
    </svg>
  )
}

function OtherIcon({ className = 'w-8 h-8' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
      />
    </svg>
  )
}

// Category to icon mapping
const categoryIcons: Record<Category, (props: { className?: string }) => ReactElement> = {
  Coffee: CoffeeIcon,
  Food: FoodIcon,
  Fitness: FitnessIcon,
  Retail: RetailIcon,
  Pets: PetsIcon,
  Grocery: GroceryIcon,
  Entertainment: EntertainmentIcon,
  Pharmacy: PharmacyIcon,
  Other: OtherIcon,
}

// Get category icon component
export function getCategoryIcon(category: string): (props: { className?: string }) => ReactElement {
  const normalized = normalizeCategory(category)
  return categoryIcons[normalized]
}

// Category logo component
interface CategoryLogoProps {
  category: string
  className?: string
  size?: 'sm' | 'md' | 'lg'
}

export function CategoryLogo({ category, className = '', size = 'md' }: CategoryLogoProps) {
  const Icon = getCategoryIcon(category)
  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }
  return <Icon className={`${sizeClasses[size]} ${className}`} />
}

// Placeholder component for missing photos
interface PhotoPlaceholderProps {
  category: string
  merchantName: string
  className?: string
}

export function PhotoPlaceholder({ category, merchantName, className = '' }: PhotoPlaceholderProps) {
  return (
    <div className={`w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 ${className}`}>
      <div className="text-center">
        <div className="w-16 h-16 mx-auto mb-2 rounded-full bg-facebook-blue/10 flex items-center justify-center">
          <CategoryLogo category={category} size="lg" className="text-facebook-blue" />
        </div>
        <p className="text-xs text-gray-500 font-medium px-2">{merchantName}</p>
      </div>
    </div>
  )
}

