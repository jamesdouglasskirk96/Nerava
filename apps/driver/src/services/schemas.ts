/**
 * Zod schemas for API response validation
 * Ensures backend changes break UI loudly at runtime
 */
import { z } from 'zod'

// Intent Capture Response Schema
export const CaptureIntentResponseSchema = z.object({
  session_id: z.string(),
  merchants: z.array(z.object({
    id: z.string(),
    name: z.string(),
    category: z.string().optional(),
    lat: z.number(),
    lng: z.number(),
    distance_m: z.number().optional(),
    image_url: z.string().nullable().optional(),
    exclusive_offer: z.string().optional(),
  })).optional(),
  charger_summary: z.object({
    distance_m: z.number().optional(),
    nearest_charger_id: z.string().optional(),
  }).optional(),
  confidence_tier: z.enum(['A', 'B', 'C']).optional(),
})

export type CaptureIntentResponse = z.infer<typeof CaptureIntentResponseSchema>

// Exclusive Session Response Schema
export const ExclusiveSessionResponseSchema = z.object({
  id: z.string(),
  merchant_id: z.string(),
  charger_id: z.string(),
  expires_at: z.string(), // ISO datetime string
  activated_at: z.string(), // ISO datetime string
  remaining_seconds: z.number().optional(),
})

export type ExclusiveSessionResponse = z.infer<typeof ExclusiveSessionResponseSchema>

// Activate Exclusive Response Schema
export const ActivateExclusiveResponseSchema = z.object({
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

// Merchant Details Response Schema
export const MerchantDetailsResponseSchema = z.object({
  id: z.string(),
  name: z.string(),
  category: z.string().optional(),
  lat: z.number(),
  lng: z.number(),
  address: z.string().optional(),
  phone: z.string().optional(),
  image_url: z.string().nullable().optional(),
  brand_image_url: z.string().nullable().optional(),
  exclusive_offer: z.string().optional(),
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




