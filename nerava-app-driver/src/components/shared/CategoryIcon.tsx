// Category icon component for fallback merchant images
import { Coffee, UtensilsCrossed, Dumbbell, ShoppingBag } from 'lucide-react'

export type CategoryType = 'coffee' | 'food' | 'fitness' | 'retail' | 'juice' | 'books' | 'grocery' | 'gym' | 'cafe' | 'restaurant' | 'mexican' | 'bookstore' | 'deli' | 'health' | 'wellness' | 'organic' | 'coworking'

interface CategoryIconProps {
  category: string
  className?: string
  size?: number
}

/**
 * Maps merchant category to appropriate icon
 * - coffee/cafe → Coffee icon
 * - food/restaurant/mexican/deli → UtensilsCrossed icon
 * - fitness/gym → Dumbbell icon
 * - retail/bookstore/books → ShoppingBag icon
 * - Default → Coffee icon
 */
export function CategoryIcon({ category, className = '', size = 48 }: CategoryIconProps) {
  const normalizedCategory = category.toLowerCase()
  
  // Coffee categories
  if (normalizedCategory.includes('coffee') || normalizedCategory.includes('cafe') || normalizedCategory.includes('bakery')) {
    return <Coffee className={className} size={size} />
  }
  
  // Food categories
  if (normalizedCategory.includes('food') || normalizedCategory.includes('restaurant') || 
      normalizedCategory.includes('mexican') || normalizedCategory.includes('deli') ||
      normalizedCategory.includes('sandwich') || normalizedCategory.includes('meal')) {
    return <UtensilsCrossed className={className} size={size} />
  }
  
  // Fitness categories
  if (normalizedCategory.includes('fitness') || normalizedCategory.includes('gym') || 
      normalizedCategory.includes('workout') || normalizedCategory.includes('exercise')) {
    return <Dumbbell className={className} size={size} />
  }
  
  // Retail categories
  if (normalizedCategory.includes('retail') || normalizedCategory.includes('book') || 
      normalizedCategory.includes('shop') || normalizedCategory.includes('store') ||
      normalizedCategory.includes('gift') || normalizedCategory.includes('shopping')) {
    return <ShoppingBag className={className} size={size} />
  }
  
  // Default to coffee icon
  return <Coffee className={className} size={size} />
}

