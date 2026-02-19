/**
 * Zod schemas for API response validation
 * Ensures backend changes break UI loudly at runtime
 */
import { z } from 'zod'

// Intent Capture Response Schema
// Note: Schema matches backend MerchantSummary format (place_id, photo_url, types)
// The frontend transforms this to MockMerchant format (id, image_url, category) in dataMapping.ts
export const CaptureIntentResponseSchema = z.object({
  session_id: z.string().nullable().optional(),
  merchants: z.array(z.object({
    place_id: z.string(),
    name: z.string(),
    lat: z.number(),
    lng: z.number(),
    distance_m: z.number(),
    types: z.array(z.string()),
    photo_url: z.string().nullable().optional(),
    icon_url: z.string().nullable().optional(),
    badges: z.array(z.string()).nullable().optional(),
    daily_cap_cents: z.number().nullable().optional(),
    // Primary merchant override fields
    is_primary: z.boolean().optional(),
    exclusive_title: z.string().optional(),
    exclusive_description: z.string().optional(),
    open_now: z.boolean().optional(),
    open_until: z.string().optional(),
    rating: z.number().optional(),
    user_rating_count: z.number().optional(),
  })).optional(),
  charger_summary: z.object({
    id: z.string(),
    name: z.string(),
    distance_m: z.number(),
    network_name: z.string().nullable().optional(),
  }).nullable().optional(),
  chargers: z.array(z.object({
    id: z.string(),
    name: z.string(),
    distance_m: z.number(),
    network_name: z.string().nullable().optional(),
  })).optional(),
  confidence_tier: z.enum(['A', 'B', 'C']),
  fallback_message: z.string().nullable().optional(),
  next_actions: z.object({
    request_wallet_pass: z.boolean(),
    require_vehicle_onboarding: z.boolean(),
  }).optional(),
})

export type CaptureIntentResponse = z.infer<typeof CaptureIntentResponseSchema>

// Exclusive Session Response Schema
export const ExclusiveSessionResponseSchema = z.object({
  id: z.string(),
  merchant_id: z.string().nullable(),
  charger_id: z.string().nullable(),
  expires_at: z.string(), // ISO datetime string
  activated_at: z.string(), // ISO datetime string
  remaining_seconds: z.number().optional(),
})

export type ExclusiveSessionResponse = z.infer<typeof ExclusiveSessionResponseSchema>

// Activate Exclusive Response Schema
export const ActivateExclusiveResponseSchema = z.object({
  status: z.string(),
  exclusive_session: ExclusiveSessionResponseSchema,
})

export type ActivateExclusiveResponse = z.infer<typeof ActivateExclusiveResponseSchema>

// Active Exclusive Response Schema
export const ActiveExclusiveResponseSchema = z.object({
  exclusive_session: ExclusiveSessionResponseSchema.nullable(),
})

export type ActiveExclusiveResponse = z.infer<typeof ActiveExclusiveResponseSchema>

// Location Check Response Schema
export const LocationCheckResponseSchema = z.object({
  in_charger_radius: z.boolean(),
  distance_m: z.number().optional(),
  nearest_charger_id: z.string().optional(),
})

export type LocationCheckResponse = z.infer<typeof LocationCheckResponseSchema>

// Merchant Details Response Schema - matches actual API response structure
export const MerchantDetailsResponseSchema = z.object({
  merchant: z.object({
    id: z.string(),
    name: z.string(),
    category: z.string().optional().nullable(),
    photo_url: z.string().optional().nullable(),
    photo_urls: z.array(z.string()).optional(),
    description: z.string().optional().nullable(),
    hours_today: z.string().optional().nullable(),
    address: z.string().optional().nullable(),
    rating: z.number().optional().nullable(),
    price_level: z.number().optional().nullable(),
    activations_today: z.number().optional(),
    verified_visits_today: z.number().optional(),
    place_id: z.string().optional().nullable(),
    amenities: z.object({
      bathroom: z.object({
        upvotes: z.number(),
        downvotes: z.number(),
      }),
      wifi: z.object({
        upvotes: z.number(),
        downvotes: z.number(),
      }),
    }).optional(),
  }),
  moment: z.object({
    label: z.string().nullable(),
    distance_miles: z.number(),
    moment_copy: z.string().optional(),
  }),
  perk: z.object({
    title: z.string(),
    badge: z.string().optional().nullable(),
    description: z.string(),
  }).nullable().optional(),
  wallet: z.object({
    can_add: z.boolean(),
    state: z.string(),
    active_copy: z.string().optional().nullable(),
  }),
  actions: z.object({
    add_to_wallet: z.boolean().optional(),
    get_directions_url: z.string().optional().nullable(),
  }),
})

export type MerchantDetailsResponse = z.infer<typeof MerchantDetailsResponseSchema>

// OTP Start Response Schema
export const OTPStartResponseSchema = z.object({
  challenge_id: z.string().optional(),
  message: z.string().optional(),
})

export type OTPStartResponse = z.infer<typeof OTPStartResponseSchema>

// OTP Verify Response Schema
export const OTPVerifyResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string(),
  refresh_token: z.string().optional(),
  user: z.object({
    public_id: z.string(),
    auth_provider: z.string(),
    email: z.string().optional().nullable(),
    phone: z.string().optional().nullable(),
  }).optional(),
})

export type OTPVerifyResponse = z.infer<typeof OTPVerifyResponseSchema>

/**
 * Validate API response against schema
 * Throws error with details if validation fails
 */
export function validateResponse<T>(
  schema: z.ZodSchema<T>,
  data: unknown,
  endpoint: string
): T {
  try {
    return schema.parse(data)
  } catch (error) {
    if (error instanceof z.ZodError) {
      const zodError = error as z.ZodError<T>
      console.error(`[Schema Validation Failed] ${endpoint}:`, {
        errors: zodError.errors,
        received: data,
      })
      throw new Error(
        `API response validation failed for ${endpoint}: ${zodError.errors.map((e: z.ZodIssue) => `${e.path.join('.')}: ${e.message}`).join(', ')}`
      )
    }
    throw error
  }
}





