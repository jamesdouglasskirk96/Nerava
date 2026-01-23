// Mock merchants data with isSponsored flags and complete merchant information
import type { ExclusiveMerchant } from '../hooks/useExclusiveSessionState'

export interface MockMerchant extends ExclusiveMerchant {
  isSponsored: boolean
  badges: string[]
  types: string[]
  lat: number
  lng: number
  distance_m: number
  exclusiveOffer?: string // The exclusive offer description
}

export const mockMerchants: MockMerchant[] = [
  {
    id: 'mock_austin_java_001',
    name: 'Austin Java',
    category: 'Coffee • Bakery',
    walkTime: '3 min walk',
    imageUrl: null, // Will use fallback icon
    isSponsored: true,
    badges: ['Sponsored', 'Exclusive'],
    types: ['cafe', 'coffee', 'bakery'],
    lat: 30.2672,
    lng: -97.7431,
    distance_m: 240,
    distance: '0.2 miles',
    hours: '7:00 AM - 8:00 PM',
    hoursStatus: 'Open now',
    description: 'A local favorite offering premium coffee, fresh pastries, and a welcoming atmosphere. Free WiFi available for remote workers.',
    exclusiveOffer: 'Free pastry with any coffee purchase',
  },
  {
    id: 'mock_juice_society_001',
    name: 'Juice Society',
    category: 'Smoothies • Wellness',
    walkTime: '4 min walk',
    imageUrl: null,
    isSponsored: false,
    badges: ['Exclusive'],
    types: ['juice_bar', 'health'],
    lat: 30.2680,
    lng: -97.7440,
    distance_m: 320,
    distance: '0.3 miles',
    hours: '8:00 AM - 6:00 PM',
    hoursStatus: 'Open now',
    description: 'Fresh pressed juices and organic smoothies made to order. Perfect for a healthy boost.',
    exclusiveOffer: 'Get 15% off all juice blends',
  },
  {
    id: 'mock_bookshop_001',
    name: 'The Bookshop',
    category: 'Books • Gifts',
    walkTime: 'On your way out',
    imageUrl: null,
    isSponsored: false,
    badges: [],
    types: ['bookstore', 'retail'],
    lat: 30.2690,
    lng: -97.7450,
    distance_m: 600,
    distance: '0.1 miles',
    hours: '9:00 AM - 9:00 PM',
    hoursStatus: 'Open now',
    description: 'Independent bookstore with curated selections and unique gifts. Browse our cozy reading nooks.',
  },
  {
    id: 'mock_tacos_001',
    name: 'Taco Deli',
    category: 'Mexican • Food',
    walkTime: '5 min walk',
    imageUrl: null,
    isSponsored: true,
    badges: ['Sponsored'],
    types: ['restaurant', 'mexican'],
    lat: 30.2700,
    lng: -97.7460,
    distance_m: 400,
    distance: '0.3 miles',
    hours: '11:00 AM - 9:00 PM',
    hoursStatus: 'Open now',
    description: 'Authentic Mexican street food with fresh ingredients and bold flavors. Perfect for a quick lunch.',
  },
  {
    id: 'mock_gym_001',
    name: 'Pure Fitness',
    category: 'Fitness • Gym',
    walkTime: '8 min walk',
    imageUrl: null,
    isSponsored: false,
    badges: ['Exclusive'],
    types: ['gym', 'fitness'],
    lat: 30.2710,
    lng: -97.7470,
    distance_m: 500,
    distance: '0.4 miles',
    hours: '5:00 AM - 10:00 PM',
    hoursStatus: 'Open now',
    description: 'Modern fitness facility with state-of-the-art equipment. Day passes available for charging customers.',
  },
  {
    id: 'mock_green_leaf_001',
    name: 'Green Leaf Café',
    category: 'Organic • Coffee',
    walkTime: '5 min walk',
    imageUrl: null,
    isSponsored: false,
    badges: [],
    types: ['cafe', 'organic'],
    lat: 30.2720,
    lng: -97.7480,
    distance_m: 450,
    distance: '0.4 miles',
    hours: '8:00 AM - 6:00 PM',
    hoursStatus: 'Open now',
    description: 'Organic café with a focus on sustainable practices. Enjoy a variety of coffee drinks and light bites.',
  },
  {
    id: 'mock_urban_grounds_001',
    name: 'Urban Grounds',
    category: 'Coffee • Work Space',
    walkTime: '2 min walk',
    imageUrl: null,
    isSponsored: false,
    badges: ['Exclusive'],
    types: ['cafe', 'coworking'],
    lat: 30.2730,
    lng: -97.7490,
    distance_m: 150,
    distance: '0.1 miles',
    hours: '8:00 AM - 6:00 PM',
    hoursStatus: 'Open now',
    description: 'Cozy coffee shop with a dedicated workspace area. Perfect for remote workers and freelancers.',
  },
  {
    id: 'mock_fresh_market_001',
    name: 'Fresh Market',
    category: 'Groceries • Deli',
    walkTime: '4 min walk',
    imageUrl: null,
    isSponsored: false,
    badges: [],
    types: ['grocery', 'deli'],
    lat: 30.2740,
    lng: -97.7500,
    distance_m: 350,
    distance: '0.3 miles',
    hours: '7:00 AM - 8:00 PM',
    hoursStatus: 'Open now',
    description: 'Local grocery store with a deli section offering fresh sandwiches and salads.',
  },
]

// Helper to get merchants for carousel (returns sets of 3: 1 featured + 2 secondary)
export function getMerchantSets(): Array<{ featured: MockMerchant; nearby: MockMerchant[] }> {
  const sets: Array<{ featured: MockMerchant; nearby: MockMerchant[] }> = []
  
  for (let i = 0; i < mockMerchants.length; i += 3) {
    const featured = mockMerchants[i]
    const nearby = mockMerchants.slice(i + 1, i + 3)
    
    if (featured) {
      sets.push({
        featured,
        nearby: nearby.length > 0 ? nearby : [],
      })
    }
  }
  
  return sets
}

