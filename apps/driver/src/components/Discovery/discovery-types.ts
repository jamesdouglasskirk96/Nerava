import type { ChargerSummary, MerchantSummary } from '../../types'

export type SheetPosition = 'peek' | 'half' | 'full'

export type DiscoveryItem =
  | { type: 'charger'; data: ChargerSummary }
  | { type: 'merchant'; data: MerchantSummary }

export type AmenityFilter = 'Bathroom' | 'Food' | 'WiFi' | 'Pets' | 'Music'

export function getItemId(item: DiscoveryItem): string {
  return item.type === 'charger' ? item.data.id : item.data.place_id
}

export function getItemLat(item: DiscoveryItem): number {
  return item.data.lat ?? 0
}

export function getItemLng(item: DiscoveryItem): number {
  return item.data.lng ?? 0
}

export function distanceToMiles(distanceM: number): string {
  const miles = distanceM / 1609.34
  if (miles < 0.1) return '< 0.1mi'
  return `${miles.toFixed(1)}mi`
}

export function distanceToWalkTime(distanceM: number): string {
  const walkMinutes = Math.round(distanceM / 83) // ~5 km/h
  if (walkMinutes < 1) return '< 1min walk'
  return `${walkMinutes}min walk`
}

export function formatReward(cents: number): string {
  return `Earn $${(cents / 100).toFixed(2)}`
}

export function getCategoryLabel(types: string[]): string {
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
  for (const type of types) {
    if (typeMap[type]) return typeMap[type]
  }
  return types[0]?.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()) || 'Place'
}
