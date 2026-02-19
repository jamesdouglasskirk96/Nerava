// Guaranteed fallback data - ALWAYS shows Tesla Supercharger with Asadas Grill
// This ensures the app NEVER shows empty state, even if API fails
import type { MockCharger } from '../mock/mockChargers'
import type { MerchantSummary } from '../types'

/**
 * Get guaranteed fallback charger (Tesla Supercharger - Canyon Ridge) with Asadas Grill
 * This is ALWAYS available, even if API fails
 */
export function getGuaranteedFallbackCharger(): MockCharger {
  return {
    id: 'canyon_ridge_tesla',
    name: 'Tesla Supercharger - Canyon Ridge',
    category: 'Tesla • CCS & Tesla',
    walkTime: '< 1 min drive',
    imageUrl: '/tesla-logo.svg',  // Tesla logo for Tesla Superchargers
    distance: '0.0 miles',
    hours: '24/7',
    hoursStatus: 'Available now',
    description: 'High-speed Tesla Supercharger located at Canyon Ridge. Perfect charging spot with great nearby experiences.',
    rating: 4.8,
    stalls: 12,
    plug_types: ['Tesla', 'CCS'],
    network_name: 'Tesla',
    lat: 30.3979,
    lng: -97.7044,
    distance_m: 0.0,
    experiences: [
      {
        id: 'm_asadas_grill',
        name: 'Asadas Grill',
        category: 'Mexican • Restaurant',
        walkTime: '< 1 min walk',
        imageUrl: '/static/merchant_photos_asadas_grill/asadas_grill_01.jpg',
        badge: '⭐ Exclusive',
      },
    ],
  }
}

/**
 * Get guaranteed fallback charger set
 * Always returns at least one charger with Asadas Grill
 */
export function getGuaranteedFallbackChargerSet(): Array<{ featured: MockCharger; nearby: MockCharger[] }> {
  return [
    {
      featured: getGuaranteedFallbackCharger(),
      nearby: [],
    },
  ]
}

/**
 * Get guaranteed fallback merchant (Asadas Grill)
 */
export function getGuaranteedFallbackMerchant(): MerchantSummary {
  return {
    place_id: 'm_asadas_grill',
    name: 'Asadas Grill',
    lat: 30.3979,
    lng: -97.7044,
    distance_m: 0,
    types: ['restaurant', 'mexican', 'food'],
    photo_url: '/static/merchant_photos_asadas_grill/asadas_grill_01.jpg',
    icon_url: undefined,
    badges: ['Sponsored', 'Exclusive'],
    daily_cap_cents: 1000,
  }
}

