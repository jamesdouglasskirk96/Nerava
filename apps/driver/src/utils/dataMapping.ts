// Helper functions to map backend data to UI format
import type { MerchantSummary, ChargerSummary } from '../types'
import type { MockMerchant } from '../mock/mockMerchants'
import type { MockCharger } from '../mock/mockChargers'

/**
 * Convert distance in meters to walk time string
 */
function distanceToWalkTime(distanceM: number): string {
  // Average walking speed: ~5 km/h = ~83 m/min
  const walkMinutes = Math.round(distanceM / 83)
  if (walkMinutes < 1) return '< 1 min walk'
  if (walkMinutes === 1) return '1 min walk'
  return `${walkMinutes} min walk`
}

/**
 * Convert distance in meters to miles string
 */
function distanceToMiles(distanceM: number): string {
  const miles = (distanceM / 1609.34).toFixed(1)
  return `${miles} miles`
}

/**
 * Get category label from types array
 */
function getCategoryLabel(types: string[]): string {
  // Common type mappings
  const typeMap: Record<string, string> = {
    cafe: 'Coffee',
    restaurant: 'Restaurant',
    bakery: 'Bakery',
    bar: 'Bar',
    store: 'Store',
    shopping_mall: 'Shopping',
    park: 'Park',
    gym: 'Gym',
    movie_theater: 'Movies',
  }

  // Try to find a recognizable type
  for (const type of types) {
    const key = type.replace('_', '')
    if (typeMap[key]) {
      return typeMap[key]
    }
  }

  // Fallback to first type or "Place"
  return types[0]?.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()) || 'Place'
}

/**
 * Convert MerchantSummary to MockMerchant format for UI compatibility
 */
export function merchantSummaryToMockMerchant(merchant: MerchantSummary): MockMerchant {
  return {
    id: merchant.place_id,
    name: merchant.name,
    category: getCategoryLabel(merchant.types),
    walkTime: distanceToWalkTime(merchant.distance_m),
    imageUrl: merchant.photo_url || null,
    isSponsored: merchant.badges?.includes('Sponsored') || false,
    badges: merchant.badges || [],
    types: merchant.types,
    lat: merchant.lat,
    lng: merchant.lng,
    distance_m: merchant.distance_m,
    distance: distanceToMiles(merchant.distance_m),
    hours: 'Hours vary', // Backend doesn't provide hours in summary
    hoursStatus: 'Check hours',
    description: '', // Backend doesn't provide description in summary
    exclusiveOffer: merchant.badges?.includes('Exclusive') ? 'Exclusive offer available' : undefined,
  }
}

/**
 * Convert ChargerSummary to MockCharger format for UI compatibility
 */
export function chargerSummaryToMockCharger(
  charger: ChargerSummary,
  nearbyMerchants: MerchantSummary[] = []
): MockCharger {
  const driveMinutes = Math.round(charger.distance_m / 1000) // Rough estimate: 1km per minute
  const plugTypes = charger.network_name ? [charger.network_name] : ['CCS', 'CHAdeMO']

  return {
    id: charger.id,
    name: charger.name,
    category: `${charger.network_name || 'Charging'} • ${plugTypes.join(' & ')}`,
    walkTime: `${driveMinutes} min drive`,
    imageUrl: null,
    distance: distanceToMiles(charger.distance_m),
    hours: '24/7',
    hoursStatus: 'Available now',
    description: `Charging station located ${distanceToMiles(charger.distance_m)} away`,
    rating: undefined,
    stalls: 0, // Backend doesn't provide stall count in summary
    plug_types: plugTypes,
    network_name: charger.network_name,
    lat: 0, // Backend doesn't provide lat/lng in summary
    lng: 0,
    distance_m: charger.distance_m,
    experiences: nearbyMerchants.slice(0, 5).map((m) => ({
      id: m.place_id,
      name: m.name,
      category: getCategoryLabel(m.types) || 'Place',
      walkTime: distanceToWalkTime(m.distance_m),
      imageUrl: m.photo_url || null,
      badge: m.badges?.includes('Exclusive') ? '⭐ Exclusive' : undefined,
    })),
  }
}

/**
 * Group merchants into sets (1 featured + 2 nearby)
 */
export function groupMerchantsIntoSets(merchants: MerchantSummary[]): Array<{ featured: MockMerchant; nearby: MockMerchant[] }> {
  const sets: Array<{ featured: MockMerchant; nearby: MockMerchant[] }> = []
  for (let i = 0; i < merchants.length; i += 3) {
    const featured = merchants[i]
    const nearby = merchants.slice(i + 1, i + 3)
    if (featured) {
      sets.push({
        featured: merchantSummaryToMockMerchant(featured),
        nearby: nearby.map(merchantSummaryToMockMerchant),
      })
    }
  }
  return sets
}

/**
 * Group chargers into sets (1 featured + 2 nearby)
 */
export function groupChargersIntoSets(
  charger: ChargerSummary | undefined,
  nearbyMerchants: MerchantSummary[] = []
): Array<{ featured: MockCharger; nearby: MockCharger[] }> {
  if (!charger) {
    return []
  }
  return [
    {
      featured: chargerSummaryToMockCharger(charger, nearbyMerchants),
      nearby: [],
    },
  ]
}

