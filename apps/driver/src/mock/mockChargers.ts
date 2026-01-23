// Mock chargers data for PRE_CHARGING state
import { mockMerchants } from './mockMerchants'

export interface MockCharger {
  id: string
  name: string
  category: string
  walkTime: string
  imageUrl?: string | null
  distance: string
  hours: string
  hoursStatus: string
  description: string
  rating?: number
  stalls: number
  plug_types: string[]
  network_name?: string
  lat: number
  lng: number
  distance_m: number
  experiences?: Array<{
    id: string
    name: string
    category: string
    walkTime: string
    imageUrl?: string | null
    badge?: string
  }>
}

// Helper to get charger sets with nearby experiences
export function getChargerSetsWithExperiences(): Array<{ featured: MockCharger; nearby: MockCharger[] }> {
  const chargersWithExperiences = mockChargers.map((charger) => ({
    ...charger,
    experiences: mockMerchants.slice(0, 5).map((merchant) => ({
      id: merchant.id,
      name: merchant.name,
      category: merchant.category || 'Other',
      walkTime: merchant.walkTime,
      imageUrl: merchant.imageUrl,
      badge: merchant.badges?.includes('Exclusive') ? '⭐ Exclusive' : undefined,
    })),
  }))

  // Group into sets of 3 (1 featured + 2 nearby)
  const sets: Array<{ featured: MockCharger; nearby: MockCharger[] }> = []
  for (let i = 0; i < chargersWithExperiences.length; i += 3) {
    const featured = chargersWithExperiences[i]
    const nearby = chargersWithExperiences.slice(i + 1, i + 3)
    if (featured) {
      sets.push({ featured, nearby: nearby.length > 0 ? nearby : [] })
    }
  }
  return sets
}

export const mockChargers: MockCharger[] = [
  {
    id: 'mock_charger_001',
    name: 'Downtown Tesla Supercharger',
    category: '8 stalls • CCS & Tesla',
    walkTime: '10 min drive',
    imageUrl: null,
    distance: '2.1 miles',
    hours: '24/7',
    hoursStatus: 'Available now',
    description: 'High-speed charging station with 8 superchargers. Located in the heart of downtown with multiple dining and shopping options nearby.',
    rating: 4.8,
    stalls: 8,
    plug_types: ['CCS', 'Tesla'],
    network_name: 'Tesla',
    lat: 30.2672,
    lng: -97.7431,
    distance_m: 3380,
  },
  {
    id: 'mock_charger_002',
    name: 'Riverside Charging Hub',
    category: '6 stalls • Level 2',
    walkTime: '8 min drive',
    imageUrl: null,
    distance: '1.8 miles',
    hours: '24/7',
    hoursStatus: 'Available now',
    description: 'Convenient charging hub with 6 Level 2 chargers. Located near Riverside Park with scenic walking trails.',
    rating: 4.5,
    stalls: 6,
    plug_types: ['CCS', 'CHAdeMO'],
    network_name: 'ChargePoint',
    lat: 30.2680,
    lng: -97.7440,
    distance_m: 2897,
  },
  {
    id: 'mock_charger_003',
    name: 'Westside Fast Charge',
    category: '4 stalls • CCS',
    walkTime: '15 min drive',
    imageUrl: null,
    distance: '3.2 miles',
    hours: '24/7',
    hoursStatus: 'Available now',
    description: 'Fast charging station with 4 CCS-compatible stalls. Adjacent to shopping center with restaurants and retail.',
    rating: 4.6,
    stalls: 4,
    plug_types: ['CCS'],
    network_name: 'EVgo',
    lat: 30.2690,
    lng: -97.7450,
    distance_m: 5150,
  },
  {
    id: 'mock_charger_004',
    name: 'Lakeside EV Station',
    category: '10 stalls • Universal',
    walkTime: '12 min drive',
    imageUrl: null,
    distance: '3.5 miles',
    hours: '24/7',
    hoursStatus: 'Available now',
    description: 'Premium charging facility with covered stalls and amenities. Adjacent to lakeside park with walking trails.',
    rating: 4.5,
    stalls: 10,
    plug_types: ['CCS', 'CHAdeMO', 'Tesla'],
    network_name: 'Universal',
    lat: 30.2700,
    lng: -97.7460,
    distance_m: 5633,
  },
]

