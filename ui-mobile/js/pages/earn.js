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

// Session state
let _sessionId = null;
let _charger = null;
let _merchant = null;
let _userLocation = null;
let _watchId = null;
let _pingInterval = null;
let _sessionState = 'starting'; // starting, charging, ready, at_merchant
let _geolocationErrorLogged = false; // Flag to prevent error spam

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
 * Initialize Earn Page from URL params or session state
 */
export async function initEarn(params = {}) {
  console.log('[Earn] ====== INIT EARN CALLED ======', params);
  
  const rootEl = document.getElementById('page-earn');
  if (!rootEl) {
    console.error('[Earn] ❌ Earn page element not found');
    return;
  }
  
  console.log('[Earn] ✅ Earn page element found');

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
        console.warn('Failed to parse stored session:', e);
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

      <!-- Distance to Charger -->
      <div id="charger-distance-block" style="background: white; padding: 16px; border-radius: 12px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <div style="font-size: 14px; color: #64748b; margin-bottom: 8px;">Distance to Charger</div>
        <div id="distance-to-charger" style="font-size: 32px; font-weight: 700; color: #22c55e; margin-bottom: 4px;">Loading...</div>
        <div style="font-size: 12px; color: #94a3b8; margin-bottom: 8px;">Stay within <span id="charger-radius">60m</span> of the charger</div>
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
        <div style="display: flex; justify-content: space-between; font-size: 12px; color: #64748b;">
          <span id="dwell-current">0s</span>
          <span id="dwell-required">3m</span>
        </div>
        <div style="margin-top: 8px; font-size: 14px;">
          <span id="dwell-status">Starting session...</span>
        </div>
      </div>

      <!-- Navigate Button -->
      <button id="navigate-to-charger-btn" style="width: 100%; padding: 14px; background: #22c55e; color: white; border: none; border-radius: 12px; font-weight: 600; font-size: 16px; cursor: pointer; margin-bottom: 16px;">
        Navigate to Charger
      </button>

      <!-- Ready to Claim Card (hidden initially) -->
      <div id="ready-to-claim-card" style="display: none; background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); padding: 20px; border-radius: 12px; color: white; margin-bottom: 16px;">
        <div style="font-size: 18px; font-weight: 600; margin-bottom: 8px;">✅ Ready to Claim!</div>
        <div style="font-size: 14px; margin-bottom: 16px; opacity: 0.9;">Your reward is ready. Visit ${_merchant.name} to claim it.</div>
        <button id="navigate-to-merchant-btn" style="width: 100%; padding: 12px; background: white; color: #22c55e; border: none; border-radius: 8px; font-weight: 600; cursor: pointer;">
          Navigate to ${_merchant.name}
        </button>
      </div>

      <!-- Merchant Distance (shown after ready to claim) -->
      <div id="merchant-distance-block" style="display: none; background: white; padding: 16px; border-radius: 12px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <div style="font-size: 14px; color: #64748b; margin-bottom: 8px;">Distance to ${_merchant.name}</div>
        <div id="distance-to-merchant" style="font-size: 24px; font-weight: 700; color: #3b82f6;">-</div>
        <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">You'll see your code when you're inside the merchant area.</div>
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
  $('#navigate-to-merchant-btn')?.addEventListener('click', () => navigateToMerchant());
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
  console.log('[Earn] Starting location tracking...');
  
  // Set fallback location in case geolocation fails
  if (!_userLocation) {
    _userLocation = { lat: 30.4021, lng: -97.7266 }; // Domain default
    console.log('[Earn] Using fallback location:', _userLocation);
  } else {
    console.log('[Earn] Starting with existing location:', _userLocation);
  }
  
  // Update UI immediately with current location
  updateLocationDisplay();
  
  if (!navigator.geolocation) {
    console.warn('[Earn] Geolocation not supported, using default location');
    return;
  }

  // Clear any existing watch
  if (_watchId !== null) {
    navigator.geolocation.clearWatch(_watchId);
  }

  _watchId = navigator.geolocation.watchPosition(
    (position) => {
      _userLocation = {
        lat: position.coords.latitude,
        lng: position.coords.longitude
      };
      console.log('[Earn] Location updated:', _userLocation);
      updateLocationDisplay();
    },
    (error) => {
      // Don't spam console with errors - just log once
      if (!_geolocationErrorLogged) {
        console.warn('[Earn] Geolocation unavailable (using fallback location):', error.message || 'Position unavailable');
        _geolocationErrorLogged = true;
      }
      // Keep using existing _userLocation or default
      if (!_userLocation) {
        _userLocation = { lat: 30.4021, lng: -97.7266 };
        updateLocationDisplay();
      }
    },
    { enableHighAccuracy: false, timeout: 5000, maximumAge: 10000 } // Less strict settings
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
  console.log('[Earn] Starting ping loop...', { sessionId: _sessionId, location: _userLocation });
  
  // Clear any existing interval
  if (_pingInterval !== null) {
    clearInterval(_pingInterval);
  }
  
  // Function to send a ping
  const sendPing = async () => {
    if (!_sessionId || !_userLocation) {
      console.warn('[Earn] Ping skipped - missing sessionId or location', { sessionId: _sessionId, location: _userLocation });
      return;
    }

    try {
      console.log('[Earn] Sending ping...', { sessionId: _sessionId, location: _userLocation });
      const pingResult = await Api.pilotVerifyPing(_sessionId, _userLocation.lat, _userLocation.lng);
      console.log('[Earn] Ping result:', pingResult);
      updateSessionUI(pingResult);
    } catch (e) {
      console.error('[Earn] Ping failed:', e);
      // Update UI with placeholder on error
      updateSessionUI({
        distance_to_charger_m: null,
        dwell_seconds: 0,
        needed_seconds: 180,
        verified: false,
        ready_to_claim: false
      });
    }
  };
  
  // Send immediate first ping
  sendPing();
  
  // Then ping every 5 seconds
  _pingInterval = setInterval(sendPing, 5000);
}

function updateSessionUI(pingResult) {
  console.log('[Earn] Updating session UI with:', pingResult);
  
  // Update distance to charger
  const distanceEl = $('#distance-to-charger');
  const radiusEl = $('#charger-radius');
  
  if (distanceEl) {
    const distance = normalizeNumber(pingResult.distance_to_charger_m);
    if (distance > 0) {
      distanceEl.textContent = formatDistance(distance);
      distanceEl.style.color = distance <= (pingResult.charger_radius_m || 60) ? '#22c55e' : '#ef4444';
    } else if (pingResult.distance_to_charger_m === null || pingResult.distance_to_charger_m === undefined) {
      distanceEl.textContent = 'Calculating...';
      distanceEl.style.color = '#64748b';
    } else {
      distanceEl.textContent = formatDistance(0);
      distanceEl.style.color = '#64748b';
    }
  }
  
  if (radiusEl) {
    if (pingResult.charger_radius_m) {
      radiusEl.textContent = `${normalizeNumber(pingResult.charger_radius_m)}m`;
    }
  }
  
  // Update location display
  updateLocationDisplay();

  // Update dwell progress
  const dwellEl = $('#dwell-current');
  const requiredEl = $('#dwell-required');
  const progressBar = $('#dwell-progress-bar');
  const statusEl = $('#dwell-status');
  const dwellSecs = normalizeNumber(pingResult.dwell_seconds || 0);
  const neededSecs = normalizeNumber(pingResult.needed_seconds || 180);
  const requiredSecs = neededSecs; // Total time needed (not including already elapsed)
  
  if (dwellEl) {
    dwellEl.textContent = formatTime(dwellSecs);
  }
  if (requiredEl) {
    requiredEl.textContent = formatTime(requiredSecs);
  }
  if (progressBar) {
    const totalRequired = neededSecs || 180; // 3 minutes default
    const percent = Math.min(100, (dwellSecs / totalRequired) * 100);
    progressBar.style.width = `${percent}%`;
    progressBar.style.transition = 'width 0.5s ease';
  }
  if (statusEl) {
    if (pingResult.ready_to_claim || pingResult.verified) {
      statusEl.textContent = '✅ Ready to claim!';
      statusEl.style.color = '#22c55e';
    } else {
      const remaining = Math.max(0, neededSecs - dwellSecs);
      statusEl.textContent = remaining > 0 ? `${formatTime(remaining)} remaining` : 'Charge for at least 3 minutes';
      statusEl.style.color = '#64748b';
    }
  }

  // Show ready to claim card
  if (pingResult.ready_to_claim || pingResult.verified) {
    _sessionState = 'ready';
    const readyCard = $('#ready-to-claim-card');
    if (readyCard) readyCard.style.display = 'block';
  }

  // Update merchant distance if ready to claim
  if (_sessionState === 'ready' || _sessionState === 'at_merchant') {
    const merchantDistanceEl = $('#distance-to-merchant');
    const merchantBlock = $('#merchant-distance-block');
    const distance = normalizeNumber(pingResult.distance_to_merchant_m || 0);
    
    if (merchantDistanceEl) {
      merchantDistanceEl.textContent = `${formatDistance(distance)} away`;
    }
    if (merchantBlock) {
      merchantBlock.style.display = 'block';
    }

    // Check if within merchant radius
    if (pingResult.within_merchant_radius) {
      _sessionState = 'at_merchant';
      // Verify visit and get code
      verifyVisitAndShowCode();
    }
  }
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

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (_watchId) navigator.geolocation.clearWatch(_watchId);
  if (_pingInterval) clearInterval(_pingInterval);
});

// Export for app.js routing
export async function initEarnPage(rootEl) {
  await initEarn();
}
