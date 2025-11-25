/**
 * Demo State Helper - Client-side state for demo redemption flow
 * 
 * Stores redemption state in localStorage to persist across page navigations.
 * This allows Earn → Wallet → Activity flow to show consistent demo data.
 */

const DEMO_REDEMPTION_KEY = 'nerava_demo_redemption';

/**
 * Load demo redemption state from localStorage
 * @returns {Object|null} Demo state object or null if not found
 */
export function loadDemoRedemption() {
  try {
    const raw = localStorage.getItem(DEMO_REDEMPTION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    console.warn('[Demo] Failed to parse demo redemption state', e);
    return null;
  }
}

/**
 * Save demo redemption state to localStorage
 * Merges with existing state and calculates cumulative fields
 * @param {Object} update - Partial state update
 * @returns {Object} Merged state object
 */
export function saveDemoRedemption(update) {
  const prev = loadDemoRedemption() || {};
  const merged = { ...prev, ...update };

  // Default / cumulative fields
  if (typeof merged.wallet_nova_balance !== 'number') {
    merged.wallet_nova_balance = prev.wallet_nova_balance || 0;
  }
  
  // If nova_awarded is provided, add it to cumulative balance
  if (typeof merged.nova_awarded === 'number') {
    merged.wallet_nova_balance = (prev.wallet_nova_balance || 0) + merged.nova_awarded;
  }
  
  // Default reputation score (small positive bump)
  if (typeof merged.reputation_score !== 'number') {
    merged.reputation_score = prev.reputation_score || 10;
  }
  
  // Default streak days
  if (typeof merged.streak_days !== 'number') {
    merged.streak_days = prev.streak_days || 1;
  }

  localStorage.setItem(DEMO_REDEMPTION_KEY, JSON.stringify(merged));
  return merged;
}

/**
 * Clear demo redemption state (for testing/reset)
 */
export function clearDemoRedemption() {
  localStorage.removeItem(DEMO_REDEMPTION_KEY);
}

// Make functions available on window for non-module contexts
if (typeof window !== 'undefined') {
  window.loadDemoRedemption = loadDemoRedemption;
  window.saveDemoRedemption = saveDemoRedemption;
  window.clearDemoRedemption = clearDemoRedemption;
}

