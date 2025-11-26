/**
 * Demo Mode Runner
 * 
 * Automatically runs through the full Domain charge party flow when DEMO_MODE is enabled.
 * Simulates a driver joining an event, earning Nova, and redeeming at a merchant.
 */
import { setTab } from '../app.js';
import {
  apiJoinChargeEvent,
  apiSessionPing,
  apiDriverWallet,
  apiDriverActivity,
  apiCancelSession,
  EVENT_SLUG,
  ZONE_SLUG,
  getCurrentUser,
} from './api.js';

let demoRunning = false;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForElement(selector, timeoutMs = 10000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const el = document.querySelector(selector);
    if (el) return el;
    await sleep(100);
  }
  throw new Error(`[DEMO] Element not found: ${selector}`);
}

/**
 * Get API base URL
 * Use the same logic as api.js (will be imported/accessed via window.NERAVA_API_BASE or detected)
 */
function getApiBase() {
  // Check if api.js has set a global base URL
  if (window.NERAVA_API_BASE) {
    return window.NERAVA_API_BASE;
  }
  
  // Try to import from api.js to get the base URL function
  // Since we're in a module, we'll detect it similar to api.js
  const hostname = window.location.hostname;
  const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.includes('192.168.') || hostname.includes('10.');
  const isVercel = hostname.includes('vercel.app');
  const isNeravaNetwork = hostname.includes('nerava.network');
  const protocol = window.location.protocol;
  const isProduction = !isLocalhost && (protocol === 'https:' || isVercel || isNeravaNetwork);
  
  if (isProduction) {
    return 'https://web-production-526f6.up.railway.app';
  }
  
  // Default to localhost for development (match api.js default)
  return 'http://127.0.0.1:8001';
}

/**
 * Redeem Nova from driver to merchant
 */
async function apiRedeemNova(merchantId, amount, sessionId = null) {
  try {
    const apiBase = getApiBase();
    const res = await fetch(`${apiBase}/v1/drivers/nova/redeem`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        merchant_id: merchantId,
        amount: amount,
        session_id: sessionId,
      }),
    });
    
    if (!res.ok) {
      const errorText = await res.text().catch(() => 'Unknown error');
      throw new Error(`Redeem Nova failed (${res.status}): ${errorText}`);
    }
    
    const data = await res.json();
    console.log('[DEMO] Nova redeemed:', data);
    return data;
  } catch (e) {
    console.error('[DEMO] Failed to redeem Nova:', e.message);
    throw e;
  }
}

/**
 * Run the full demo flow
 */
export async function runDemoFlow(demoOptions = {}) {
  if (demoRunning) {
    console.warn('[DEMO] Demo already running, skipping');
    return;
  }
  
  const user = getCurrentUser();
  if (!user) {
    console.error('[DEMO] No user logged in, cannot run demo');
    return;
  }
  
  demoRunning = true;
  
  try {
    console.log('[DEMO] ========================================');
    console.log('[DEMO] Starting demo flow for user', user.email || user.id);
    console.log('[DEMO] ========================================');
    
    // Wait a moment for UI to stabilize
    await sleep(1000);
    
    // 1) Navigate to Explore
    console.log('[DEMO] Step 1: Navigate to Explore');
    setTab('explore');
    await sleep(1500);
    
    // 2) Wait for Explore page to load and find elements
    console.log('[DEMO] Step 2: Waiting for Explore page to load...');
    
    // Wait for perk cards to appear - try multiple selectors
    let perkCard = null;
    let attempts = 0;
    while (!perkCard && attempts < 30) {
      // Try various selectors for perk cards (updated to match actual DOM structure)
      const explorePage = document.getElementById('page-explore');
      if (explorePage) {
        // Look for perk cards in the recommended perks row (the actual structure)
        const perksRow = explorePage.querySelector('#recommended-perks-row');
        if (perksRow && perksRow.children.length > 0) {
          perkCard = perksRow.children[0]; // First perk card
        } else {
          // Fallback selectors
          perkCard = explorePage.querySelector('.perk-card-compact') ||
                     explorePage.querySelector('[data-perk-id]') ||
                     explorePage.querySelector('[class*="perk-card"]') ||
                     explorePage.querySelector('[class*="merchant"]');
        }
      }
      
      if (!perkCard) {
        await sleep(300);
        attempts++;
        if (attempts % 10 === 0) {
          console.log(`[DEMO] Still waiting for perk card... (attempt ${attempts}/30)`);
        }
      }
    }
    
    if (!perkCard) {
      console.error('[DEMO] Could not find perk card after waiting. Demo will be incomplete.');
      console.log('[DEMO] Explore page element:', document.getElementById('page-explore'));
      console.log('[DEMO] Available card-like elements:', document.querySelectorAll('[class*="card"], [data-*]'));
      return;
    }
    
    console.log('[DEMO] Found perk card:', perkCard);
    
    // Store charger/merchant location hints before clicking
    // These will be set by explore.js when the session starts
    // Use defaults based on Domain Austin locations
    const chargerLocation = {
      lat: 30.37665,  // Default Domain charger
      lng: -97.65168,
    };
    
    const merchantLocation = {
      lat: 30.4021,   // Default Domain merchant
      lng: -97.7266,
    };
    
    console.log('[DEMO] Using charger location:', chargerLocation);
    console.log('[DEMO] Using merchant location:', merchantLocation);
    
    // Store defaults in window (will be overridden by explore.js if available)
    window.__neravaDemoChargerLocation = chargerLocation;
    window.__neravaDemoMerchantLocation = merchantLocation;
    
    // 3) Click the perk card to start session
    console.log('[DEMO] Step 3: Clicking perk card to start session...');
    
    // Trigger a click event (use both click() and dispatchEvent for compatibility)
    if (perkCard.click) {
      perkCard.click();
    } else {
      const clickEvent = new MouseEvent('click', {
        bubbles: true,
        cancelable: true,
        view: window
      });
      perkCard.dispatchEvent(clickEvent);
    }
    
    // Wait for session to start and navigation to Earn page
    await sleep(2000);
    
    // 4) Wait for session to start and get session ID
    console.log('[DEMO] Step 4: Waiting for session to start...');
    
    let sessionId = null;
    let sessionAttempts = 0;
    while (!sessionId && sessionAttempts < 15) {
      // Check global state first
      sessionId = window.__neravaCurrentSessionId;
      
      // Also try to get from URL params
      if (!sessionId) {
        const hash = location.hash;
        const match = hash.match(/session_id=([^&]+)/);
        if (match) {
          sessionId = decodeURIComponent(match[1]);
          window.__neravaCurrentSessionId = sessionId;
        }
      }
      
      // Also check window.pilotSession
      if (!sessionId && window.pilotSession && window.pilotSession.session_id) {
        sessionId = window.pilotSession.session_id;
        window.__neravaCurrentSessionId = sessionId;
      }
      
      if (!sessionId) {
        await sleep(500);
        sessionAttempts++;
        if (sessionAttempts % 5 === 0) {
          console.log(`[DEMO] Still waiting for session ID... (attempt ${sessionAttempts}/15)`);
        }
      }
    }
    
    if (!sessionId) {
      console.error('[DEMO] No session ID found after waiting. Session may not have started.');
      console.log('[DEMO] Current hash:', location.hash);
      console.log('[DEMO] Global state:', window.__neravaCurrentSessionId);
      console.log('[DEMO] Window.pilotSession:', window.pilotSession);
      return;
    }
    
    console.log('[DEMO] Session started, ID:', sessionId);
    console.log('[DEMO] Step 5: Simulating movement and charging...');
    
    // 5) Simulate movement: Start at charger, accumulate dwell time
    console.log('[DEMO] Phase 1: At charger - accumulating dwell time');
    for (let i = 0; i < 8; i++) {
      try {
        const res = await apiSessionPing({
          sessionId,
          location: { lat: chargerLocation.lat, lng: chargerLocation.lng },
        });
        console.log(`[DEMO] Ping ${i + 1}/8 at charger:`, {
          verified: res.verified,
          dwell_seconds: res.dwell_seconds,
          needed_seconds: res.needed_seconds,
          reward_earned: res.reward_earned,
        });
        
        if (res.verified && res.reward_earned) {
          console.log('[DEMO] ✓ Session verified and Nova awarded!');
          break;
        }
      } catch (e) {
        console.warn(`[DEMO] Ping ${i + 1} failed:`, e.message);
      }
      await sleep(1500);
    }
    
    // 6) Simulate walking to merchant (interpolate between charger and merchant)
    console.log('[DEMO] Phase 2: Walking to merchant');
    for (let i = 0; i < 5; i++) {
      const t = (i + 1) / 5;
      const loc = {
        lat: chargerLocation.lat + (merchantLocation.lat - chargerLocation.lat) * t,
        lng: chargerLocation.lng + (merchantLocation.lng - chargerLocation.lng) * t,
      };
      
      try {
        const res = await apiSessionPing({
          sessionId,
          location: { lat: loc.lat, lng: loc.lng },
        });
        console.log(`[DEMO] Ping en route ${i + 1}/5:`, {
          distance_to_charger_m: res.distance_to_charger_m,
          distance_to_merchant_m: res.distance_to_merchant_m,
        });
      } catch (e) {
        console.warn(`[DEMO] En route ping ${i + 1} failed:`, e.message);
      }
      await sleep(1000);
    }
    
    // Final ping at merchant
    try {
      const finalPing = await apiSessionPing({
        sessionId,
        location: { lat: merchantLocation.lat, lng: merchantLocation.lng },
      });
      console.log('[DEMO] Final ping at merchant:', finalPing);
    } catch (e) {
      console.warn('[DEMO] Final ping failed:', e.message);
    }
    
    // 7) Show updated wallet
    console.log('[DEMO] Step 6: Showing wallet with Nova balance');
    setTab('wallet');
    await sleep(1500);
    
    try {
      const wallet = await apiDriverWallet();
      console.log('[DEMO] Wallet after charge:', wallet);
    } catch (e) {
      console.warn('[DEMO] Failed to load wallet:', e.message);
    }
    
    // 8) Show Activity page
    console.log('[DEMO] Step 7: Showing activity feed');
    setTab('activity');
    await sleep(1500);
    
    try {
      const activity = await apiDriverActivity({ limit: 10 });
      console.log('[DEMO] Activity after charge:', activity);
    } catch (e) {
      console.warn('[DEMO] Failed to load activity:', e.message);
    }
    
    // 9) Simulate merchant redeem (optional, based on options)
    const merchantId = window.__neravaDemoMerchantId || demoOptions.merchantId;
    const shouldRedeem = demoOptions.simulateRedeem !== false;
    
    if (shouldRedeem && merchantId) {
      try {
        const wallet = await apiDriverWallet();
        const redeemAmount = Math.min(
          wallet.nova_balance || 0,
          demoOptions.redeemAmount || 10
        );
        
        if (redeemAmount > 0) {
          console.log('[DEMO] Step 8: Simulating merchant redeem of', redeemAmount, 'Nova');
          
          await apiRedeemNova(merchantId, redeemAmount, sessionId);
          
          // Show updated wallet after redeem
          setTab('wallet');
          await sleep(1000);
          
          const walletAfter = await apiDriverWallet();
          console.log('[DEMO] Wallet after redeem:', walletAfter);
          
          // Show updated activity
          setTab('activity');
          await sleep(1000);
          
          const activityAfter = await apiDriverActivity({ limit: 10 });
          console.log('[DEMO] Activity after redeem:', activityAfter);
        } else {
          console.log('[DEMO] Skipping redeem - no Nova balance');
        }
      } catch (e) {
        console.warn('[DEMO] Redeem failed (continuing):', e.message);
      }
    } else {
      console.log('[DEMO] Skipping redeem - disabled or no merchant ID');
    }
    
    console.log('[DEMO] ========================================');
    console.log('[DEMO] Demo flow complete!');
    console.log('[DEMO] ========================================');
    
  } catch (err) {
    console.error('[DEMO] Demo flow failed:', err);
    console.error('[DEMO] Stack:', err.stack);
  } finally {
    demoRunning = false;
  }
}

/**
 * Check if demo mode is enabled
 */
export function isDemoMode() {
  return window.NERAVA_DEMO_MODE === true;
}

