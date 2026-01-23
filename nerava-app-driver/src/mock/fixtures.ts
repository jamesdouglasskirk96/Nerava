import type {
  MerchantSummary,
  ChargerSummary,
  MerchantDetailsResponse,
  WalletActivateResponse,
  ChargerWithExperiences,
} from './types'

// Deterministic session ID for mock mode
export const MOCK_SESSION_ID = 'mock_session_12345'

// Mock merchants matching Figma structure exactly
export const MOCK_MERCHANTS: MerchantSummary[] = [
  {
    place_id: 'mock_asadas_grill_001',
    name: 'Asadas Grill',
    lat: 30.2680,
    lng: -97.7435,
    distance_m: 200, // ~2 min walk
    types: ['restaurant', 'mexican', 'food'],
    photo_url: '/static/merchant_photos_asadas_grill/asadas_grill_01.jpg',
    icon_url: undefined,
    badges: ['Sponsored', 'Exclusive'],
    daily_cap_cents: 1000,
    // Extended fields for Figma matching
    brought_to_you_by: 'Brought to you by Asadas Grill',
    category_display: 'Mexican • Restaurant',
  } as MerchantSummary & { brought_to_you_by?: string; category_display?: string },
  {
    place_id: 'mock_juice_society_001',
    name: 'Juice Society',
    lat: 30.2680,
    lng: -97.7440,
    distance_m: 320, // ~4 min walk
    types: ['juice_bar', 'health'],
    photo_url: undefined,
    icon_url: undefined,
    badges: ['Exclusive'],
    daily_cap_cents: 750,
    category_display: 'Juice • Health',
  } as MerchantSummary & { brought_to_you_by?: string; category_display?: string },
  {
    place_id: 'mock_bookshop_001',
    name: 'The Bookshop',
    lat: 30.2690,
    lng: -97.7450,
    distance_m: 600, // "On your way out" (>500m)
    types: ['bookstore', 'retail'],
    photo_url: undefined,
    icon_url: undefined,
    badges: [],
    daily_cap_cents: 300,
    category_display: 'Books • Retail',
  } as MerchantSummary & { brought_to_you_by?: string; category_display?: string },
  {
    place_id: 'mock_tacos_001',
    name: 'Taco Deli',
    lat: 30.2700,
    lng: -97.7460,
    distance_m: 400,
    types: ['restaurant', 'mexican'],
    photo_url: undefined,
    icon_url: undefined,
    badges: ['Sponsored'],
    daily_cap_cents: 1000,
    category_display: 'Mexican • Food',
  } as MerchantSummary & { brought_to_you_by?: string; category_display?: string },
  {
    place_id: 'mock_gym_001',
    name: 'Pure Fitness',
    lat: 30.2710,
    lng: -97.7470,
    distance_m: 500,
    types: ['gym', 'fitness'],
    photo_url: undefined,
    icon_url: undefined,
    badges: [],
    daily_cap_cents: 750,
    category_display: 'Fitness • Gym',
  } as MerchantSummary & { brought_to_you_by?: string; category_display?: string },
]

// Mock chargers with nearby experiences
export const MOCK_CHARGERS: ChargerWithExperiences[] = [
  {
    id: 'mock_charger_001',
    name: 'Tesla Supercharger - Domain',
    distance_m: 500,
    network_name: 'Tesla',
    stalls: 12,
    plug_types: ['CCS', 'Tesla'],
    rating: 4.8,
    photo_url: 'https://images.unsplash.com/photo-1694266475815-19ded81303fd?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxUZXNsYSUyMFN1cGVyY2hhcmdlciUyMHN0YXRpb258ZW58MXx8fHwxNzY3OTc3NjYxfDA&ixlib=rb-4.1.0&q=80&w=1080',
    nearby_experiences: [
      MOCK_MERCHANTS[0], // Asadas Grill
      MOCK_MERCHANTS[1], // Juice Society
    ],
  },
  {
    id: 'mock_charger_002',
    name: 'ChargePoint Station',
    distance_m: 1200,
    network_name: 'ChargePoint',
    stalls: 4,
    plug_types: ['CCS', 'CHAdeMO'],
    rating: 4.5,
    photo_url: 'https://images.unsplash.com/photo-1593941707882-a5bac6861d75?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080',
    nearby_experiences: [
      MOCK_MERCHANTS[2], // The Bookshop
      MOCK_MERCHANTS[3], // Taco Deli
    ],
  },
  {
    id: 'mock_charger_003',
    name: 'EVgo Fast Charging',
    distance_m: 2000,
    network_name: 'EVgo',
    stalls: 6,
    plug_types: ['CCS'],
    rating: 4.6,
    photo_url: 'https://images.unsplash.com/photo-1593941707882-a5bac6861d75?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080',
    nearby_experiences: [
      MOCK_MERCHANTS[4], // Pure Fitness
      MOCK_MERCHANTS[0], // Asadas Grill (reuse)
    ],
  },
]

// Mock merchant details responses
export const MOCK_MERCHANT_DETAILS: Record<string, MerchantDetailsResponse> = {
  mock_asadas_grill_001: {
    merchant: {
      id: 'mock_asadas_grill_001',
      name: 'Asadas Grill',
      category: 'Restaurant',
      photo_url: '/static/merchant_photos_asadas_grill/asadas_grill_01.jpg',
      address: '501 W Canyon Ridge Dr, Austin, TX 78753, USA',
      rating: 4.5,
      price_level: 2,
    },
    moment: {
      label: '2 min walk',
      distance_miles: 0.124,
      moment_copy: 'Authentic Mexican cuisine while you charge',
    },
    perk: {
      title: 'Free Beverage Exclusive',
      badge: 'Exclusive',
      description: 'Get a free beverage with any meal during charging hours. Show your pass to redeem.',
    },
    wallet: {
      can_add: true,
      state: 'INACTIVE',
    },
    actions: {
      add_to_wallet: true,
      get_directions_url: 'https://maps.google.com/?q=30.2680,-97.7435',
    },
  },
  mock_austin_java_001: {
    merchant: {
      id: 'mock_austin_java_001',
      name: 'Austin Java',
      category: 'Coffee • Bakery',
      photo_url: undefined,
      address: '123 Domain Dr, Austin, TX 78758',
      rating: 4.7,
      price_level: 2,
    },
    moment: {
      label: '3 min walk',
      distance_miles: 0.149,
      moment_copy: 'Perfect for a quick coffee break',
    },
    perk: {
      title: 'Happy Hour',
      badge: 'Exclusive',
      description: 'Get 20% off your favorite drinks during charging hours. Show your pass at checkout to redeem.',
    },
    wallet: {
      can_add: true,
      state: 'INACTIVE',
    },
    actions: {
      add_to_wallet: true,
      get_directions_url: 'https://maps.google.com/?q=30.2672,-97.7431',
    },
  },
  mock_juice_society_001: {
    merchant: {
      id: 'mock_juice_society_001',
      name: 'Juice Society',
      category: 'Juice • Health',
      photo_url: undefined,
      address: '456 Domain Dr, Austin, TX 78758',
      rating: 4.5,
      price_level: 2,
    },
    moment: {
      label: '4 min walk',
      distance_miles: 0.199,
      moment_copy: 'Fresh juices and healthy options',
    },
    perk: {
      title: 'Wellness Discount',
      badge: 'Exclusive',
      description: 'Get 15% off all juice blends. Show your pass at checkout.',
    },
    wallet: {
      can_add: true,
      state: 'INACTIVE',
    },
    actions: {
      add_to_wallet: true,
      get_directions_url: 'https://maps.google.com/?q=30.2680,-97.7440',
    },
  },
  mock_bookshop_001: {
    merchant: {
      id: 'mock_bookshop_001',
      name: 'The Bookshop',
      category: 'Books • Retail',
      photo_url: undefined,
      address: '789 Domain Dr, Austin, TX 78758',
      rating: 4.6,
      price_level: 2,
    },
    moment: {
      label: 'On your way out',
      distance_miles: 0.373,
      moment_copy: 'Browse books while you wait',
    },
    perk: {
      title: 'Book Discount',
      badge: 'Exclusive',
      description: 'Get 10% off your purchase. Show your pass at checkout.',
    },
    wallet: {
      can_add: true,
      state: 'INACTIVE',
    },
    actions: {
      add_to_wallet: true,
      get_directions_url: 'https://maps.google.com/?q=30.2690,-97.7450',
    },
  },
  mock_starbucks_001: {
    merchant: {
      id: 'mock_starbucks_001',
      name: 'Starbucks Reserve',
      category: 'Coffee',
      photo_url: undefined,
      address: '123 Domain Dr, Austin, TX 78758',
      rating: 4.7,
      price_level: 2,
    },
    moment: {
      label: '2 min walk',
      distance_miles: 0.075,
      moment_copy: 'Perfect for a quick coffee break',
    },
    perk: {
      title: 'Happy Hour',
      badge: 'Exclusive',
      description: 'Get 20% off your favorite drinks during charging hours. Show your pass at checkout to redeem.',
    },
    wallet: {
      can_add: true,
      state: 'INACTIVE',
    },
    actions: {
      add_to_wallet: true,
      get_directions_url: 'https://maps.google.com/?q=30.2672,-97.7431',
    },
  },
  mock_tacos_001: {
    merchant: {
      id: 'mock_tacos_001',
      name: 'Taco Deli',
      category: 'Food',
      photo_url: undefined,
      address: '456 Domain Dr, Austin, TX 78758',
      rating: 4.5,
      price_level: 1,
    },
    moment: {
      label: '5 min walk',
      distance_miles: 0.155,
      moment_copy: 'Great spot for lunch',
    },
    perk: {
      title: 'Sponsored Deal',
      badge: 'Sponsored',
      description: 'Enjoy $5 off any order over $15. Valid while charging.',
    },
    wallet: {
      can_add: true,
      state: 'INACTIVE',
    },
    actions: {
      add_to_wallet: true,
      get_directions_url: 'https://maps.google.com/?q=30.2680,-97.7440',
    },
  },
  mock_gym_001: {
    merchant: {
      id: 'mock_gym_001',
      name: 'Pure Fitness',
      category: 'Fitness',
      photo_url: undefined,
      address: '789 Domain Dr, Austin, TX 78758',
      rating: 4.6,
      price_level: 3,
    },
    moment: {
      label: '8 min walk',
      distance_miles: 0.249,
      moment_copy: 'Get a quick workout in',
    },
    perk: {
      title: 'Day Pass',
      badge: 'Exclusive',
      description: 'Free day pass for charging customers. Show your pass at the front desk.',
    },
    wallet: {
      can_add: true,
      state: 'INACTIVE',
    },
    actions: {
      add_to_wallet: true,
      get_directions_url: 'https://maps.google.com/?q=30.2690,-97.7450',
    },
  },
  mock_target_001: {
    merchant: {
      id: 'mock_target_001',
      name: 'Target',
      category: 'Retail',
      photo_url: undefined,
      address: '321 Domain Dr, Austin, TX 78758',
      rating: 4.4,
      price_level: 2,
    },
    moment: {
      label: '12 min walk',
      distance_miles: 0.373,
      moment_copy: 'Pick up essentials',
    },
    perk: {
      title: '10% Off',
      badge: 'Exclusive',
      description: 'Get 10% off your purchase. Show your pass at checkout.',
    },
    wallet: {
      can_add: true,
      state: 'INACTIVE',
    },
    actions: {
      add_to_wallet: true,
      get_directions_url: 'https://maps.google.com/?q=30.2700,-97.7460',
    },
  },
  mock_pets_001: {
    merchant: {
      id: 'mock_pets_001',
      name: 'Petco',
      category: 'Pets',
      photo_url: undefined,
      address: '654 Domain Dr, Austin, TX 78758',
      rating: 4.3,
      price_level: 2,
    },
    moment: {
      label: '15 min walk',
      distance_miles: 0.497,
      moment_copy: 'Shop for your furry friend',
    },
    perk: {
      title: 'Free Treat',
      badge: 'Exclusive',
      description: 'Get a free treat for your pet with any purchase.',
    },
    wallet: {
      can_add: true,
      state: 'INACTIVE',
    },
    actions: {
      add_to_wallet: true,
      get_directions_url: 'https://maps.google.com/?q=30.2710,-97.7470',
    },
  },
  mock_wholefoods_001: {
    merchant: {
      id: 'mock_wholefoods_001',
      name: 'Whole Foods Market',
      category: 'Grocery',
      photo_url: undefined,
      address: '987 Domain Dr, Austin, TX 78758',
      rating: 4.6,
      price_level: 3,
    },
    moment: {
      label: '20 min walk',
      distance_miles: 0.621,
      moment_copy: 'Stock up on groceries',
    },
    perk: {
      title: '5% Off',
      badge: 'Exclusive',
      description: 'Get 5% off your grocery purchase. Show your pass at checkout.',
    },
    wallet: {
      can_add: true,
      state: 'INACTIVE',
    },
    actions: {
      add_to_wallet: true,
      get_directions_url: 'https://maps.google.com/?q=30.2720,-97.7480',
    },
  },
}

// Helper to get merchant details or return a default
export function getMerchantDetailsFixture(merchantId: string): MerchantDetailsResponse {
  return (
    MOCK_MERCHANT_DETAILS[merchantId] ||
    MOCK_MERCHANT_DETAILS['mock_asadas_grill_001'] || // Try Asadas Grill first
    MOCK_MERCHANT_DETAILS['mock_austin_java_001'] || // Fallback to Austin Java
    MOCK_MERCHANT_DETAILS['mock_starbucks_001'] // Final fallback
  )
}

// Helper to create wallet activation response
export function createWalletActivationResponse(
  merchantId: string
): WalletActivateResponse {
  const merchant = MOCK_MERCHANT_DETAILS[merchantId]?.merchant || {
    name: 'Merchant',
    id: merchantId,
    category: 'Other',
  }

  // Set expiration to 60 minutes from now
  const expiresAt = new Date(Date.now() + 60 * 60 * 1000).toISOString()

  return {
    status: 'activated',
    wallet_state: {
      state: 'ACTIVE',
      merchant_id: merchantId,
      expires_at: expiresAt,
      active_copy: `Active for the next 60 minutes at ${merchant.name}`,
    },
  }
}

