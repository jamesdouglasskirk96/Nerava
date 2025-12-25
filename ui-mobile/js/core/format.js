/**
 * Formatting utilities for wallet display
 */

/**
 * Format seconds into "Xh Ym" format (rounds down minutes)
 * @param {number} seconds - Total seconds
 * @returns {string} Formatted string like "5h 30m" or "45m"
 */
export function formatHoursMinutes(seconds) {
  if (seconds < 0) return "0m";
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (hours > 0 && minutes > 0) {
    return `${hours}h ${minutes}m`;
  } else if (hours > 0) {
    return `${hours}h`;
  } else {
    return `${minutes}m`;
  }
}

/**
 * Format cents into USD string format
 * @param {number} cents - Amount in cents
 * @returns {string} Formatted string like "$56.09"
 */
export function formatUsdFromCents(cents) {
  const dollars = cents / 100;
  return `$${dollars.toFixed(2)}`;
}


