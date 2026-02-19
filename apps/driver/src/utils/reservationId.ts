/**
 * Generate a Reservation ID in the format: {LOCATION}-{MERCHANT}-{DAY}
 * Example: ATX-ASADAS-025
 *
 * Properties:
 * - Resets daily (based on day of year)
 * - Unique per merchant per day (within location)
 * - Human-readable and easy to communicate verbally
 * - Generated client-side (no backend call required)
 *
 * V3 LIMITATION: IDs are informational only. Backend does NOT validate them.
 * V4 TODO: Add backend endpoint to generate/validate Reservation IDs.
 *
 * COLLISION WARNING: Two merchants with same first 6 letters (e.g., "Starbucks Downtown"
 * and "Starbucks Airport") will have same merchant code. Acceptable for V3 demo.
 *
 * @param merchantName - Merchant display name (e.g., "Asadas Grill")
 * @param locationCode - 3-letter location code (default: "ATX" for Austin)
 * @returns Formatted Reservation ID (e.g., "ATX-ASADAS-025")
 */
export function generateReservationId(merchantName: string, locationCode = 'ATX'): string {
  // V4 TODO: Get locationCode from backend merchant data or user's geolocation

  // Extract letters from merchant name (uppercase, letters only)
  const lettersOnly = merchantName.toUpperCase().replace(/[^A-Z]/g, '')

  // Ensure minimum 3 characters, maximum 6
  // If name has < 3 letters, pad with 'X'
  // Examples: "A1 Diner" -> "ADINER", "42" -> "XXX", "Jo's" -> "JOSXXX"
  const merchantCode = lettersOnly.length >= 3
    ? lettersOnly.substring(0, 6)
    : lettersOnly.padEnd(3, 'X')

  // Get day of year (1-366) for daily reset
  const now = new Date()
  const start = new Date(now.getFullYear(), 0, 0)
  const diff = now.getTime() - start.getTime()
  const oneDay = 1000 * 60 * 60 * 24
  const dayOfYear = Math.floor(diff / oneDay)

  // Format as 3-digit string (001-366)
  const dailyNumber = String(dayOfYear).padStart(3, '0')

  return `${locationCode}-${merchantCode}-${dailyNumber}`
}

/**
 * Parse a Reservation ID to extract components.
 * Useful for future backend validation.
 *
 * @param id - Reservation ID string
 * @returns Parsed components or null if invalid format
 */
export function parseReservationId(id: string): {
  locationCode: string
  merchantCode: string
  dayOfYear: number
} | null {
  const parts = id.split('-')
  if (parts.length !== 3) return null

  const [locationCode, merchantCode, dayStr] = parts

  // Validate location code (3 uppercase letters)
  if (!/^[A-Z]{3}$/.test(locationCode)) return null

  // Validate merchant code (3-6 uppercase letters)
  if (!/^[A-Z]{3,6}$/.test(merchantCode)) return null

  const dayOfYear = parseInt(dayStr, 10)
  if (isNaN(dayOfYear) || dayOfYear < 1 || dayOfYear > 366) return null

  return { locationCode, merchantCode, dayOfYear }
}

/**
 * Check if a Reservation ID was generated today.
 *
 * @param id - Reservation ID to validate
 * @returns true if ID was generated today
 */
export function isReservationIdFromToday(id: string): boolean {
  const parsed = parseReservationId(id)
  if (!parsed) return false

  const now = new Date()
  const start = new Date(now.getFullYear(), 0, 0)
  const diff = now.getTime() - start.getTime()
  const oneDay = 1000 * 60 * 60 * 24
  const todayDayOfYear = Math.floor(diff / oneDay)

  return parsed.dayOfYear === todayDayOfYear
}
