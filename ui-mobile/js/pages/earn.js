/**
 * Earn Page - Pilot Session Flow
 * 
 * Full end-to-end experience:
 * 1. Start session with charger + merchant
 * 2. Track distance to charger
 * 3. Monitor dwell progress
 * 4. Navigate to charger/merchant
 * 5. Auto-switch to code when in merchant radius
 */

import Api from '../core/api.js';
import { setTab } from '../app.js';

const $ = (s, r = document) => r.querySelector(s);

// Session state - single source of truth for timers
let _sessionId = null;
let _charger = null;
let _merchant = null;
let _userLocation = null;
let _watchId = null;
let _pingInterval = null;
let _sessionState = 'starting'; // starting, charging, ready, at_merchant
let _geolocationErrorLogged = false; // Flag to prevent error spam
let _showingMerchantDistance = false; // Track if we're showing merchant distance instead of charger distance

// Toast helper
function showToast(message) {
  const toast = document.createElement('div');
  toast.style.cssText = 'position:fixed;left:50%;bottom:100px;transform:translateX(-50%);background:#111;color:#fff;padding:10px 14px;border-radius:12px;z-index:9999;font-weight:700';
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

function normalizeNumber(n) {
  const parsed = Number(n);
  return Number.isNaN(parsed) ? 0 : Math.round(parsed);
}

function formatDistance(meters) {
  if (meters < 1000) return `${meters}m`;
  return `${(meters / 1000).toFixed(1)}km`;
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins > 0) return `${mins}m ${secs}s`;
  return `${secs}s`;
}

/**
 * Central cleanup function - stops ping loop and geolocation watcher
 * Called when: session cancelled, session completed, or navigating away
 */
export function cleanupEarnSession() {
  if (_pingInterval !== null) {
    clearInterval(_pingInterval);
    _pingInterval = null;
  }
  
  if (_watchId !== null && navigator.geolocation && navigator.geolocation.clearWatch) {
    navigator.geolocation.clearWatch(_watchId);
    _watchId = null;
  }
  
  // Reset error flag for next session
  _geolocationErrorLogged = false;
  
  // Don't clear _sessionId here - let it be cleared by cancel/complete handlers
}

/**
 * Initialize Earn Page from URL params or session state
 */
export async function initEarn(params = {}) {
  // Clean up any existing session before starting new one
  cleanupEarnSession();
  
  const rootEl = document.getElementById('page-earn');
  if (!rootEl) {
    return;
  }

  // Try to get session from global state first (preferred)
  let sessionState = null;
  if (typeof window !== 'undefined' && window.pilotSession) {
    sessionState = window.pilotSession;
  } else if (typeof sessionStorage !== 'undefined') {
    const stored = sessionStorage.getItem('pilot_session');
    if (stored) {
      try {
        sessionState = JSON.parse(stored);
        window.pilotSession = sessionState; // Cache in window for immediate access
      } catch (e) {
        // Silently ignore parse errors
      }
    }
  }

  // Get params from URL hash or passed params (fallback)
  const urlParams = new URLSearchParams(window.location.hash.split('?')[1] || '');
  const sessionId = sessionState?.session_id || params.session_id || urlParams.get('session_id');
  const merchantId = sessionState?.merchant?.id || params.merchant_id || urlParams.get('merchant_id');
  const chargerId = sessionState?.charger?.id || params.charger_id || urlParams.get('charger_id');

  if (!merchantId || !chargerId) {
    renderError(rootEl, 'Missing merchant or charger ID. Please start a session from the Explore page.');
    return;
  }

  // Get user location first
  try {
    const position = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
    });
    _userLocation = {
      lat: position.coords.latitude,
      lng: position.coords.longitude
    };
  } catch (e) {
    console.warn('Could not get user location:', e);
    _userLocation = { lat: 30.4021, lng: -97.7266 }; // Domain default
  }

  // Use session from state if available, otherwise start new session
  // sessionState was already declared above, just reuse it
  
  if (sessionState && sessionState.session_id === sessionId) {
    // Session already started, use existing data
    _sessionId = sessionState.session_id;
    _charger = sessionState.charger;
    _merchant = sessionState.merchant;
    
    if (_charger && _merchant) {
      renderSessionView(rootEl);
      startLocationTracking();
      startPingLoop();
      return;
    }
  }
  
  // Start new session or refresh data
  await startSession(rootEl, chargerId, merchantId, sessionId);
}

async function startSession(rootEl, chargerId, merchantId, existingSessionId = null) {
  renderLoading(rootEl);

  try {
    // Fetch merchant/charger info from bootstrap/while_you_charge
    const bootstrap = await Api.fetchPilotBootstrap();
    const whileYouCharge = await Api.fetchPilotWhileYouCharge();
    
    _charger = bootstrap.chargers.find(c => c.id === chargerId);
    _merchant = whileYouCharge.recommended_merchants.find(m => m.id === merchantId);

    if (!_charger || !_merchant) {
      renderError(rootEl, 'Charger or merchant not found');
      return;
    }

    // Start pilot session if we don't have an existing one
    let sessionData;
    if (existingSessionId) {
      // Use existing session ID, but verify we have merchant/charger data
      sessionData = {
        session_id: existingSessionId,
        charger: _charger,
        merchant: _merchant
      };
    } else {
      // Start new session
      sessionData = await Api.pilotStartSession(
        _userLocation.lat,
        _userLocation.lng,
        chargerId,
        merchantId,
        123 // TODO: Get actual user_id
      );
    }

    _sessionId = sessionData.session_id;
    _charger = sessionData.charger || _charger;
    _merchant = sessionData.merchant || _merchant;

    // Store session state for persistence
    const sessionState = {
      session_id: _sessionId,
      charger: _charger,
      merchant: _merchant
    };
    
    if (typeof sessionStorage !== 'undefined') {
      sessionStorage.setItem('pilot_session', JSON.stringify(sessionState));
    }
    window.pilotSession = sessionState;

    // Render session UI
    renderSessionView(rootEl);
    
    // Start GPS tracking first (async, but we don't wait)
    startLocationTracking();
    
    // Start ping loop (will wait for location)
    startPingLoop();
    
    // Send immediate first ping after a short delay to ensure UI is rendered and location is available
    setTimeout(() => {
      if (_sessionId && _userLocation) {
        console.log('[Earn] Sending immediate ping on session start...', {
          sessionId: _sessionId,
          location: _userLocation
        });
        Api.pilotVerifyPing(_sessionId, _userLocation.lat, _userLocation.lng)
          .then((result) => {
            console.log('[Earn] Initial ping result:', result);
            updateSessionUI(result);
          })
          .catch((err) => {
            console.error('[Earn] Initial ping failed:', err);
            // Still update UI with default values
            updateSessionUI({
              distance_to_charger_m: null,
              dwell_seconds: 0,
              needed_seconds: 180,
              verified: false,
              ready_to_claim: false
            });
          });
      } else {
        console.warn('[Earn] Cannot send initial ping - missing sessionId or location', {
          sessionId: _sessionId,
          location: _userLocation
        });
        // Update UI with placeholder values
        updateSessionUI({
          distance_to_charger_m: null,
          dwell_seconds: 0,
          needed_seconds: 180,
          verified: false,
          ready_to_claim: false
        });
      }
    }, 500); // Small delay to ensure UI is fully rendered

  } catch (e) {
    console.error('Failed to start session:', e);
    renderError(rootEl, `Failed to start session: ${e.message}`);
  }
}

function renderLoading(rootEl) {
  rootEl.innerHTML = `
    <div style="padding: 20px; text-align: center;">
      <div style="font-size: 24px; margin-bottom: 10px;">⚡</div>
      <div>Starting session...</div>
    </div>
  `;
}

function renderError(rootEl, message) {
  rootEl.innerHTML = `
    <div style="padding: 20px; text-align: center;">
      <div style="color: #ef4444; margin-bottom: 10px;">❌</div>
      <div>${message}</div>
      <button onclick="location.hash='#/explore'" style="margin-top: 20px; padding: 10px 20px; background: #22c55e; color: white; border: none; border-radius: 8px; cursor: pointer;">
        Back to Explore
      </button>
    </div>
  `;
}

function renderSessionView(rootEl) {
  const rewardNova = normalizeNumber(_merchant?.nova_reward || 0);
  const rewardText = rewardNova > 0 ? `Earn ${rewardNova} Nova` : 'Earn rewards';
  
  rootEl.innerHTML = `
    <div id="earn-session-view" style="padding: 16px; max-width: 600px; margin: 0 auto;">
      <!-- Session Header -->
      <div style="background: #f8fafc; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
        <div style="font-size: 14px; color: #64748b; margin-bottom: 4px;">Active Session</div>
        <div style="font-size: 18px; font-weight: 600; margin-bottom: 4px;">${_charger.name}</div>
        <div style="font-size: 14px; color: #64748b;">${_merchant.name} • ${rewardText}</div>
      </div>

      <!-- Distance Card (shows charger or merchant distance) -->
      <div id="distance-card" style="background: white; padding: 16px; border-radius: 12px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <div id="distance-title" style="font-size: 14px; color: #64748b; margin-bottom: 8px;">Distance to Charger</div>
        <div id="distance-value" style="font-size: 32px; font-weight: 700; color: #22c55e; margin-bottom: 4px;">Loading...</div>
        <div id="distance-subtitle" style="font-size: 12px; color: #94a3b8; margin-bottom: 8px;">Stay within <span id="charger-radius">60m</span> of the charger</div>
        <div id="user-location-display" style="font-size: 10px; color: #cbd5e1; font-family: monospace;">Location: -</div>
      </div>

      <!-- Dwell Progress -->
      <div id="dwell-progress-block" style="background: white; padding: 16px; border-radius: 12px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <div style="font-size: 14px; color: #64748b; margin-bottom: 8px;">Charging Progress</div>
        <div style="margin-bottom: 8px;">
          <div style="background: #e5e7eb; height: 8px; border-radius: 4px; overflow: hidden;">
            <div id="dwell-progress-bar" style="background: #22c55e; height: 100%; width: 0%; transition: width 0.5s ease;"></div>
          </div>
        </div>
        <div style="margin-top: 8px; font-size: 14px;">
          <span id="dwell-status">Starting session...</span>
        </div>
      </div>

      <!-- Navigate Button (hidden when ready to claim) -->
      <button id="navigate-to-charger-btn" style="width: 100%; padding: 14px; background: #22c55e; color: white; border: none; border-radius: 12px; font-weight: 600; font-size: 16px; cursor: pointer; margin-bottom: 12px;">
        Navigate to Charger
      </button>

      <!-- Cancel Session Button -->
      <button id="cancel-session-btn" style="width: 100%; padding: 12px; background: #f1f5f9; color: #64748b; border: none; border-radius: 12px; font-weight: 500; font-size: 14px; cursor: pointer; margin-bottom: 16px;">
        Cancel Session
      </button>

      <!-- Ready to Claim Card (hidden initially, only shown when ready_to_claim is true) -->
      <div id="ready-to-claim-card" style="display: none; background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); padding: 20px; border-radius: 12px; color: white; margin-bottom: 16px;">
        <div style="font-size: 18px; font-weight: 600; margin-bottom: 8px;">✅ Ready to Claim!</div>
        <div style="font-size: 14px; margin-bottom: 16px; opacity: 0.9;">Your reward is ready. Visit ${_merchant?.name || 'the merchant'} to claim it.</div>
        <button id="navigate-to-merchant-btn" style="width: 100%; padding: 12px; background: white; color: #22c55e; border: none; border-radius: 8px; font-weight: 600; cursor: pointer;">
          Navigate to ${_merchant?.name || 'Merchant'}
        </button>
      </div>


      <!-- Code View (shown when in merchant radius) -->
      <div id="code-view" style="display: none; background: white; padding: 24px; border-radius: 12px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <div style="font-size: 20px; font-weight: 600; margin-bottom: 16px;">Your Discount Code</div>
        <div id="merchant-code" style="font-size: 48px; font-weight: 700; letter-spacing: 4px; color: #22c55e; margin-bottom: 8px; font-family: monospace;">-</div>
        <div style="font-size: 14px; color: #64748b; margin-bottom: 16px;">Show this to the cashier for your Nerava reward</div>
        <button id="copy-code-btn" style="padding: 10px 20px; background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 8px; cursor: pointer; font-size: 14px;">
          Copy Code
        </button>
      </div>
    </div>
  `;

  // Bind event handlers
  $('#navigate-to-charger-btn')?.addEventListener('click', () => navigateToCharger());
  
  // Cancel Session button
  $('#cancel-session-btn')?.addEventListener('click', () => cancelCurrentSession());
  
  // Navigate to Merchant button (in Ready to Claim card) - switches distance card to merchant
  const navigateToMerchantBtn = $('#navigate-to-merchant-btn');
  if (navigateToMerchantBtn) {
    navigateToMerchantBtn.addEventListener('click', () => {
      // Switch to showing merchant distance
      _showingMerchantDistance = true;
      // Navigate to merchant
      if (_merchant) {
        navigateToMerchant();
      }
    });
  }
  
  $('#copy-code-btn')?.addEventListener('click', () => copyCode());
}

function navigateToCharger() {
  if (!_charger) return;
  const url = `https://www.google.com/maps/dir/?api=1&destination=${_charger.lat},${_charger.lng}`;
  window.open(url, '_blank');
}

function navigateToMerchant() {
  if (!_merchant) return;
  const url = `https://www.google.com/maps/dir/?api=1&destination=${_merchant.lat},${_merchant.lng}`;
  window.open(url, '_blank');
}

function copyCode() {
  const codeEl = $('#merchant-code');
  if (!codeEl) return;
  const code = codeEl.textContent.trim();
  if (code && code !== '-') {
    navigator.clipboard.writeText(code).then(() => {
      showToast('Code copied!');
    }).catch(() => {
      showToast('Failed to copy');
    });
  }
}

function startLocationTracking() {
  // Clear any existing watch before starting new one
  if (_watchId !== null && navigator.geolocation && navigator.geolocation.clearWatch) {
    navigator.geolocation.clearWatch(_watchId);
    _watchId = null;
  }
  
  // Set fallback location in case geolocation fails
  if (!_userLocation) {
    _userLocation = { lat: 30.4021, lng: -97.7266 }; // Domain default
  }
  
  // Update UI immediately with current location
  updateLocationDisplay();
  
  if (!navigator.geolocation) {
    return; // Geolocation not supported, use fallback
  }

  _watchId = navigator.geolocation.watchPosition(
    (position) => {
      _userLocation = {
        lat: position.coords.latitude,
        lng: position.coords.longitude
      };
      updateLocationDisplay();
    },
    (error) => {
      // Log geolocation errors only once
      if (!_geolocationErrorLogged) {
        console.warn(`[Earn] Geolocation error: ${error.message || 'Unavailable'}`);
        _geolocationErrorLogged = true;
      }
      // Keep using existing _userLocation or default
      if (!_userLocation) {
        _userLocation = { lat: 30.4021, lng: -97.7266 };
        updateLocationDisplay();
      }
    },
    { enableHighAccuracy: false, timeout: 5000, maximumAge: 10000 }
  );
}

function updateLocationDisplay() {
  // Update location display if elements exist
  const locationDisplay = document.getElementById('user-location-display');
  if (locationDisplay && _userLocation) {
    locationDisplay.textContent = `${_userLocation.lat.toFixed(6)}, ${_userLocation.lng.toFixed(6)}`;
  }
  
  // Also trigger a ping if we have session ID and location
  if (_sessionId && _userLocation && _pingInterval === null) {
    // Ping loop not started yet, trigger immediate update
    Api.pilotVerifyPing(_sessionId, _userLocation.lat, _userLocation.lng)
      .then(updateSessionUI)
      .catch(err => console.error('[Earn] Location update ping failed:', err));
  }
}

function startPingLoop() {
  // Clear any existing interval before starting new one
  if (_pingInterval !== null) {
    clearInterval(_pingInterval);
    _pingInterval = null;
  }
  
  if (!_sessionId) {
    return; // No session, don't start loop
  }
  
  // Function to send a ping
  const sendPing = async () => {
    // Check if session still exists (might have been cancelled)
    if (!_sessionId || !_userLocation || _pingInterval === null) {
      return; // Cleanup happened, stop pinging
    }

    try {
      const pingResult = await Api.pilotVerifyPing(_sessionId, _userLocation.lat, _userLocation.lng);
      
      // Only log if state changed or there's an important update
      if (pingResult.ready_to_claim || pingResult.reward_earned) {
        console.log('[Earn] Session update:', { ready_to_claim: pingResult.ready_to_claim, reward_earned: pingResult.reward_earned });
      }
      
      updateSessionUI(pingResult);
      
      // If session is completed/cancelled, stop pinging
      if (pingResult.reward_earned || pingResult.status === 'completed' || pingResult.status === 'cancelled') {
        cleanupEarnSession();
      }
    } catch (e) {
      // Only log errors, don't spam - update UI with placeholder
      if (e.message && !e.message.includes('404')) {
        console.warn(`[Earn] Ping failed: ${e.message}`);
      }
      // Update UI with placeholder on error (silent fail for 404s - session might be cancelled)
      updateSessionUI({
        distance_to_charger_m: null,
        dwell_seconds: 0,
        needed_seconds: 180,
        verified: false,
        ready_to_claim: false,
        nova_awarded: 0,
        wallet_balance_nova: 0,
        wallet_balance: 0,
        charger_radius_m: 60,
        within_merchant_radius: false,
        reward_earned: false
      });
    }
  };
  
  // Send immediate first ping
  sendPing();
  
  // Then ping every 5 seconds
  _pingInterval = setInterval(sendPing, 5000);
}

// State machine: derive session state from ping response
function deriveSessionState(data) {
  const dist = normalizeNumber(data.distance_to_charger_m ?? data.distance_m ?? 0);
  const radius = normalizeNumber(data.charger_radius_m ?? 60);
  const dwell = normalizeNumber(data.dwell_seconds ?? 0);
  const remaining = normalizeNumber(data.needed_seconds ?? 180);
  
  const insideRadius = dist <= radius;
  
  if (data.reward_earned || data.nova_awarded > 0) return "earned";
  if (data.ready_to_claim || (remaining <= 0 && insideRadius)) return "ready_to_claim";
  if (insideRadius) return "verifying";
  return "navigate_to_charger";
}

function updateSessionUI(pingResult) {
  // Derive state from ping response
  const state = deriveSessionState(pingResult);
  const chargerDist = normalizeNumber(pingResult.distance_to_charger_m ?? 0);
  const merchantDist = normalizeNumber(pingResult.distance_to_merchant_m ?? 0);
  const radius = normalizeNumber(pingResult.charger_radius_m ?? 60);
  const dwell = normalizeNumber(pingResult.dwell_seconds ?? 0);
  const remaining = normalizeNumber(pingResult.needed_seconds ?? 180);
  const totalRequired = dwell + remaining; // Total time needed (elapsed + remaining)
  
  // Update distance card (switches between charger and merchant)
  const distanceCard = $('#distance-card');
  const distanceTitleEl = $('#distance-title');
  const distanceValueEl = $('#distance-value');
  const distanceSubtitleEl = $('#distance-subtitle');
  const radiusEl = $('#charger-radius');
  
  // Determine what to show: merchant distance if showing merchant, otherwise charger distance
  if (_showingMerchantDistance) {
    // Show merchant distance
    if (distanceTitleEl) {
      distanceTitleEl.textContent = `Distance to ${_merchant?.name || 'Merchant'}`;
    }
    if (distanceValueEl) {
      if (merchantDist > 0) {
        distanceValueEl.textContent = formatDistance(merchantDist);
        distanceValueEl.style.color = pingResult.within_merchant_radius ? '#22c55e' : '#3b82f6';
      } else {
        distanceValueEl.textContent = 'Calculating...';
        distanceValueEl.style.color = '#64748b';
      }
    }
    if (distanceSubtitleEl) {
      distanceSubtitleEl.textContent = pingResult.within_merchant_radius 
        ? "You're here! Your code is below." 
        : "You'll see your code when you're inside the merchant area.";
    }
  } else {
    // Show charger distance (default)
    if (distanceTitleEl) {
      distanceTitleEl.textContent = 'Distance to Charger';
    }
    if (distanceValueEl) {
      if (chargerDist > 0) {
        distanceValueEl.textContent = formatDistance(chargerDist);
        distanceValueEl.style.color = chargerDist <= radius ? '#22c55e' : '#ef4444';
      } else {
        distanceValueEl.textContent = chargerDist === 0 && state !== 'navigate_to_charger' ? '0m' : 'Calculating...';
        distanceValueEl.style.color = state === 'navigate_to_charger' ? '#ef4444' : '#22c55e';
      }
    }
    if (distanceSubtitleEl) {
      if (state === 'navigate_to_charger') {
        distanceSubtitleEl.textContent = `Arrive at the charger to start earning.`;
      } else {
        distanceSubtitleEl.innerHTML = `Stay within <span id="charger-radius">${radius}m</span> of the charger.`;
      }
    }
  }
  
  if (radiusEl && pingResult.charger_radius_m) {
    radiusEl.textContent = `${radius}m`;
  }

  // Update dwell progress - show as percentage
  const progressBar = $('#dwell-progress-bar');
  const statusEl = $('#dwell-status');
  
  // Calculate progress percentage
  // Backend provides: dwell_seconds (time already elapsed) and needed_seconds (time still needed)
  // Total required = dwell + needed_seconds (already calculated above)
  // Percent = (dwell / total_required) * 100
  let percent = 0;
  // Note: totalRequired is already declared above at line 492
  
  // Handle edge cases
  if (pingResult.reward_earned || pingResult.nova_awarded > 0) {
    percent = 100;
  } else if (totalRequired > 0) {
    percent = Math.min(100, Math.round((dwell / totalRequired) * 100));
  } else if (remaining <= 0 && state === 'ready_to_claim') {
    percent = 100; // Ready to claim means we're done
  } else if (remaining === 0 && dwell === 0) {
    // No time elapsed yet, backend might not have needed_seconds
    percent = 0;
  }
  
  // Defensive logging for debugging (only log if values seem wrong)
  // Commented out to reduce noise - uncomment if debugging progress issues
  // if ((percent === 0 && dwell > 0) || (remaining > 0 && percent >= 100)) {
  //   console.warn('[Earn] Progress calculation warning:', { dwell, remaining, totalRequired, percent, state });
  // }
  
  // Update progress bar
  if (progressBar) {
    progressBar.style.width = `${percent}%`;
    progressBar.style.transition = 'width 0.5s ease';
  }
  
  // Update status text based on state and percentage
  if (statusEl) {
    switch (state) {
      case 'earned':
        statusEl.textContent = `Done! You've earned ${pingResult.nova_awarded || 0} Nova.`;
        statusEl.style.color = '#22c55e';
        break;
      case 'ready_to_claim':
        const rewardNova = _merchant?.nova_reward || pingResult.nova_awarded || 0;
        statusEl.textContent = `Done! You've earned ${rewardNova} Nova.`;
      statusEl.style.color = '#22c55e';
        break;
      case 'verifying':
        // Show percentage with optional remaining time
        if (remaining > 0) {
          statusEl.textContent = `${percent}% complete • ${formatTime(remaining)} remaining`;
    } else {
          statusEl.textContent = `${percent}% complete`;
        }
        statusEl.style.color = '#64748b';
        break;
      case 'navigate_to_charger':
      default:
        statusEl.textContent = 'Arrive at the charger to start earning.';
      statusEl.style.color = '#64748b';
        break;
    }
  }

  // Update CTA button based on state
  const navigateBtn = $('#navigate-to-charger-btn');
  const readyCard = $('#ready-to-claim-card');
  const navigateToMerchantBtn = $('#navigate-to-merchant-btn');
  const codeView = $('#code-view');
  
  if (navigateBtn) {
    switch (state) {
      case 'earned':
        navigateBtn.textContent = 'View Wallet';
        navigateBtn.style.background = '#3b82f6';
        navigateBtn.style.display = 'block';
        navigateBtn.style.opacity = '1';
        navigateBtn.style.cursor = 'pointer';
        navigateBtn.onclick = () => setTab('Wallet');
        break;
      case 'ready_to_claim':
        // In ready_to_claim state, hide the main navigate button
        // Merchant navigation will be in the Ready to Claim card only
        navigateBtn.style.display = 'none';
        break;
      case 'verifying':
        navigateBtn.style.display = 'block';
        navigateBtn.textContent = 'Keep Charging';
        navigateBtn.style.background = '#64748b';
        navigateBtn.style.opacity = '0.6';
        navigateBtn.style.cursor = 'not-allowed';
        navigateBtn.onclick = null;
        break;
      case 'navigate_to_charger':
      default:
        navigateBtn.style.display = 'block'; // Show button
        navigateBtn.textContent = 'Navigate to Charger';
        navigateBtn.style.background = '#22c55e';
        navigateBtn.style.opacity = '1';
        navigateBtn.style.cursor = 'pointer';
        navigateBtn.onclick = () => navigateToCharger();
        break;
    }
  }
  
  // Navigate to Merchant button is already wired up in renderSessionView
  // Just ensure it's visible when ready
  
  // Show/hide ready to claim card
  if (readyCard) {
    if (state === 'ready_to_claim' || state === 'earned') {
      readyCard.style.display = 'block';
      _sessionState = 'ready';
    } else {
      readyCard.style.display = 'none';
    }
  }
  
  // Check if within merchant radius - show code
  if (state === 'ready_to_claim' || state === 'earned') {
    if (pingResult.within_merchant_radius) {
      _sessionState = 'at_merchant';
      _showingMerchantDistance = true; // Keep showing merchant distance
      verifyVisitAndShowCode();
    }
  }
  
  // Show/hide code view based on state
  if (codeView) {
    if (state === 'earned' || (state === 'ready_to_claim' && pingResult.within_merchant_radius)) {
      // Code view will be shown by verifyVisitAndShowCode if we have a code
    } else {
      codeView.style.display = 'none';
    }
  }
  
  // Update location display
  updateLocationDisplay();
}

async function verifyVisitAndShowCode() {
  if (!_sessionId || !_merchant || !_userLocation) return;

  try {
    const visitResult = await Api.pilotVerifyVisit(
      _sessionId,
      _merchant.id,
      _userLocation.lat,
      _userLocation.lng
    );

    if (visitResult.visit_verified && visitResult.merchant_code) {
      // Show code view
      const codeView = $('#code-view');
      const codeEl = $('#merchant-code');
      if (codeView) codeView.style.display = 'block';
      if (codeEl) codeEl.textContent = visitResult.merchant_code;

      // Hide other blocks
      const readyCard = $('#ready-to-claim-card');
      const merchantBlock = $('#merchant-distance-block');
      if (readyCard) readyCard.style.display = 'none';
      if (merchantBlock) merchantBlock.style.display = 'none';

      showToast(`Earned ${visitResult.nova_awarded || 0} Nova!`);
    }
  } catch (e) {
    console.error('Failed to verify visit:', e);
  }
}

/**
 * Cancel current session - calls backend and cleans up UI
 */
async function cancelCurrentSession() {
  if (!_sessionId) {
    // No active session, just clean up and navigate away
    cleanupEarnSession();
    setTab('explore');
    return;
  }
  
  const sessionIdToCancel = _sessionId;
  
  try {
    // Call backend to cancel session
    await Api.pilotCancelSession(sessionIdToCancel);
  } catch (e) {
    // Log but don't block - UI cleanup should happen anyway
    console.warn(`[Earn] Cancel API call failed: ${e.message || 'Unknown error'}`);
  }
  
  // Clean up UI regardless of API result
  cleanupEarnSession();
  
  // Clear session state
  _sessionId = null;
  if (typeof sessionStorage !== 'undefined') {
    sessionStorage.removeItem('pilot_session');
  }
  if (window.pilotSession) {
    delete window.pilotSession;
  }
  
  // Navigate back to Explore
  setTab('explore');
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  cleanupEarnSession();
});

// Export for app.js routing
export async function initEarnPage(rootEl) {
  await initEarn();
}
