import { apiMe, apiLogout, getCurrentUser, apiGetSmartcarConnectUrl, apiGetVehicleTelemetry, apiSendTelemetryEvent } from '../core/api.js';
import { loadDemoRedemption } from '../core/demo-state.js';

// Safe MetaMask/Ethereum provider detection and connection
function isMetaMaskAvailable() {
  return typeof window !== 'undefined' &&
    window.ethereum &&
    (window.ethereum.isMetaMask || window.ethereum.isBraveWallet || true);
}

async function safeConnectMetaMask() {
  if (!isMetaMaskAvailable()) {
    console.warn('[Wallet][EV] No Ethereum provider / MetaMask extension detected. Skipping wallet connect.');
    return null;
  }

  try {
    const accounts = await window.ethereum.request({
      method: 'eth_requestAccounts',
    });
    console.log('[Wallet][EV] Connected MetaMask accounts:', accounts);
    return accounts;
  } catch (err) {
    // Silently handle MetaMask connection failures - don't block the page
    console.warn('[Wallet][EV] Failed to connect to MetaMask (non-fatal):', err.message || err);
    return null;
  }
}

// Tier thresholds for reputation display
const TIERS = [
  { name: 'Bronze', min: 0, color: '#9CA3AF' },
  { name: 'Silver', min: 100, color: '#64748B' },
  { name: 'Gold', min: 300, color: '#EAB308' },
  { name: 'Platinum', min: 700, color: '#06B6D4' },
];

function getTierInfo(score) {
  const sorted = [...TIERS].sort((a, b) => a.min - b.min);
  let current = sorted[0];
  let next = null;
  for (let i = 0; i < sorted.length; i++) {
    if (score >= sorted[i].min) current = sorted[i];
    if (score < sorted[i].min) {
      next = sorted[i];
      break;
    }
  }
  return { current, next };
}

export async function initMePage(rootEl) {
  console.log('[Profile] Initializing profile page...');

  // Safely attempt MetaMask connection (non-blocking, non-fatal)
  // This prevents unhandled promise rejections if MetaMask is not available
  safeConnectMetaMask().catch(() => {
    // Silently ignore - MetaMask connection is optional
  });

  // Get user info from /me endpoint
  let user = null;
  try {
    user = await apiMe();
  } catch (e) {
    console.warn('[Profile] Could not load user:', e.message);
    // If not authenticated, redirect to login
    if (e.message && (e.message.includes('401') || e.message.includes('Unauthorized'))) {
      window.location.hash = '#/login';
      return;
    }
  }

  if (!user) {
    console.error('[Profile] No user data available');
    return;
  }

  const userName = user?.display_name || user?.email || user?.phone || 'User';
  const userEmail = user?.email || null;
  const userPhone = user?.phone || null;
  const authProvider = user?.auth_provider || 'unknown';

  // Get reputation score (from demo or API)
  const demo = loadDemoRedemption();
  const repScore = demo?.reputation_score || user?.reputation_score || 0;
  const tierInfo = getTierInfo(repScore);

  rootEl.innerHTML = `
    <div style="padding: 20px; background: white; min-height: calc(100vh - 140px);">
      <!-- Profile Header -->
      <div style="background: #f8fafc; padding: 20px; border-radius: 12px; margin-bottom: 20px; text-align: center; position: relative;">
        <button id="settings-btn" class="settings-btn" aria-label="Settings" style="position: absolute; top: 16px; right: 16px;">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
          </svg>
        </button>
        <div style="width: 64px; height: 64px; border-radius: 50%; background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); display: flex; align-items: center; justify-content: center; margin: 0 auto 12px; font-size: 28px; font-weight: bold; color: white;">
          ${userName.charAt(0).toUpperCase()}
        </div>
        <div style="font-size: 20px; font-weight: 700; color: #111827; margin-bottom: 4px;" id="me-name">${userName}</div>
        ${userPhone ? `<div style="font-size: 14px; color: #64748b; margin-bottom: 12px;" id="me-phone">${userPhone}</div>` : ''}
        <div style="font-size: 12px; color: #9ca3af; margin-bottom: 12px;">Signed in as "${userName}"</div>
        
        <!-- Badge Tier -->
        <div style="display: inline-block; background: ${tierInfo.current.color}20; color: ${tierInfo.current.color}; padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; margin-bottom: 8px;" id="me-tier-badge">
          ${tierInfo.current.name}
        </div>
      </div>

      <!-- EV Vehicle Connection -->
      <div style="background: white; border-radius: 12px; margin-bottom: 20px; border: 1px solid #e2e8f0;">
        <div style="padding: 16px;">
          <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin: 0 0 12px 0;">EV Vehicle Connection</h3>
          <div id="me-vehicle-status" style="margin-bottom: 12px; padding: 12px; background: #f8fafc; border-radius: 8px; font-size: 14px; color: #6b7280;">
            Checking connection status...
          </div>
          <button id="me-connect-ev-btn" style="width: 100%; background: #1e40af; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: 600; font-size: 14px; cursor: pointer; margin-bottom: 8px;">
            Connect Vehicle
          </button>
          <button id="me-test-telemetry-btn" style="width: 100%; background: #10b981; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: 600; font-size: 14px; cursor: pointer; display: none;">
            Test Telemetry
          </button>
          <div id="me-telemetry-display" style="margin-top: 12px; padding: 12px; background: #f0fdf4; border-radius: 8px; display: none;">
            <div style="font-size: 12px; color: #059669; font-weight: 600; margin-bottom: 8px;">Latest Telemetry</div>
            <div id="me-telemetry-data" style="font-size: 13px; color: #047857;"></div>
          </div>
        </div>
      </div>

      <!-- Account Options -->
      <div style="background: white; border-radius: 12px; margin-bottom: 20px; border: 1px solid #e2e8f0;">
        <div style="padding: 16px;">
          <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin: 0 0 12px 0;">Account</h3>
          <button id="me-settings-btn" style="width: 100%; background: #f1f5f9; border: none; text-align: center; padding: 12px; border-radius: 8px; color: #374151; font-size: 14px; font-weight: 600; cursor: pointer;">
            Settings
          </button>
        </div>
      </div>

      <!-- Sign Out -->
      <div style="margin-top: 20px;">
        <button id="me-signout-btn" style="width: 100%; background: #ef4444; color: white; border: none; padding: 14px; border-radius: 8px; font-weight: 600; font-size: 14px; cursor: pointer;">
          Sign out
        </button>
      </div>
    </div>
    
    <!-- Settings Bottom Sheet -->
    <div id="settings-sheet" class="settings-sheet">
      <div class="settings-sheet-backdrop"></div>
      <div class="settings-sheet-content">
        <div class="settings-sheet-header">
          <h3 class="settings-sheet-title">Settings</h3>
          <button id="settings-close-btn" class="settings-sheet-close" aria-label="Close">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="settings-sheet-body">
          <div class="settings-row">
            <div class="settings-label">
              <span class="settings-title">Push Notifications</span>
              <span class="settings-desc">Get alerts for rewards and charging</span>
            </div>
            <label class="toggle-switch">
              <input type="checkbox" id="settings-notifications-toggle">
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>
      </div>
    </div>
  `;

  // Wire sign out button
  rootEl.querySelector('#me-signout-btn')?.addEventListener('click', async () => {
    console.log('[Profile] Sign out clicked');
    try {
      // Get refresh token for logout
      const { getRefreshToken } = await import('../core/auth.js');
      const refreshToken = getRefreshToken();
      
      await apiLogout(refreshToken);
      
      // Redirect to login
      window.location.hash = '#/login';
      window.location.reload();
    } catch (e) {
      console.error('[Profile] Sign out failed:', e);
      // Clear tokens and redirect anyway
      const { clearTokens } = await import('../core/auth.js');
      clearTokens();
      window.location.hash = '#/login';
      window.location.reload();
    }
  });

  // Settings sheet functions
  function openSettingsSheet() {
    const sheet = document.getElementById('settings-sheet');
    if (sheet) {
      sheet.classList.add('open');
      // Load saved preference (default: enabled)
      const notifEnabled = localStorage.getItem('nerava_notifications') !== 'false';
      const toggle = document.getElementById('settings-notifications-toggle');
      if (toggle) {
        toggle.checked = notifEnabled;
      }
    }
  }
  
  function closeSettingsSheet() {
    const sheet = document.getElementById('settings-sheet');
    if (sheet) {
      sheet.classList.remove('open');
    }
  }
  
  // Wire settings button (gear icon in header)
  rootEl.querySelector('#settings-btn')?.addEventListener('click', openSettingsSheet);
  
  // Wire settings button (in Account section - keep for backward compatibility)
  rootEl.querySelector('#me-settings-btn')?.addEventListener('click', openSettingsSheet);
  
  // Wire close button
  const closeBtn = rootEl.querySelector('#settings-close-btn');
  if (closeBtn) {
    closeBtn.addEventListener('click', closeSettingsSheet);
  }
  
  // Wire backdrop click to close
  const backdrop = rootEl.querySelector('.settings-sheet-backdrop');
  if (backdrop) {
    backdrop.addEventListener('click', closeSettingsSheet);
  }
  
  // Save notification preference on toggle
  rootEl.querySelector('#settings-notifications-toggle')?.addEventListener('change', (e) => {
    localStorage.setItem('nerava_notifications', e.target.checked ? 'true' : 'false');
    console.log('[Settings] Notifications:', e.target.checked ? 'enabled' : 'disabled');
  });

  // Check vehicle connection status
  async function checkVehicleStatus() {
    const statusEl = rootEl.querySelector('#me-vehicle-status');
    const connectBtn = rootEl.querySelector('#me-connect-ev-btn');
    const testBtn = rootEl.querySelector('#me-test-telemetry-btn');
    
    try {
      const telemetry = await apiGetVehicleTelemetry();
      if (telemetry) {
        statusEl.textContent = '✓ Vehicle connected';
        statusEl.style.background = '#f0fdf4';
        statusEl.style.color = '#059669';
        connectBtn.textContent = 'Reconnect Vehicle';
        testBtn.style.display = 'block';
        return true;
      }
    } catch (err) {
      if (err.message && err.message.includes('404')) {
        statusEl.textContent = 'Your vehicle is not connected yet';
        statusEl.style.background = '#fef3c7';
        statusEl.style.color = '#92400e';
        connectBtn.textContent = 'Connect Vehicle';
        testBtn.style.display = 'none';
        return false;
      }
      // Send telemetry event for failure
      apiSendTelemetryEvent({
        event: 'TELEMETRY_FETCH_FAILED',
        ts: Date.now(),
        page: '#/me',
        meta: {
          error: err.message ? err.message.substring(0, 200) : 'Unknown error' // No secrets
        }
      }).catch(() => {});
      console.warn('[Profile][EV] Status check failed:', err);
    }
    return false;
  }

  // Wire Smartcar EV Connect button
  async function handleConnectEvClick() {
    const btn = rootEl.querySelector('#me-connect-ev-btn');
    const originalText = btn.textContent;
    
    // Send telemetry event
    apiSendTelemetryEvent({
      event: 'EV_CONNECT_CLICKED',
      ts: Date.now(),
      page: '#/me',
      meta: {}
    }).catch(() => {});
    
    try {
      btn.disabled = true;
      btn.textContent = 'Redirecting to Secure Vehicle Login...';
      console.log('[Profile][EV] Fetching Smartcar connect URL...');
      const res = await apiGetSmartcarConnectUrl();
      if (res?.url) {
        window.location.href = res.url;
      } else {
        alert('Unable to start EV connection. Please try again.');
        btn.disabled = false;
        btn.textContent = originalText;
      }
    } catch (err) {
      console.error('[Profile][EV] Connect failed', err);
      alert('Unable to start EV connection. Please try again.');
      btn.disabled = false;
      btn.textContent = originalText;
    }
  }

  // Wire test telemetry button
  async function handleTestTelemetryClick() {
    const btn = rootEl.querySelector('#me-test-telemetry-btn');
    const displayEl = rootEl.querySelector('#me-telemetry-display');
    const dataEl = rootEl.querySelector('#me-telemetry-data');
    
    try {
      btn.disabled = true;
      btn.textContent = 'Loading...';
      const telemetry = await apiGetVehicleTelemetry();
      
      if (telemetry) {
        const soc = telemetry.soc_pct !== null ? `${telemetry.soc_pct.toFixed(1)}%` : 'N/A';
        const state = telemetry.charging_state || 'Unknown';
        const lat = telemetry.latitude !== null ? telemetry.latitude.toFixed(4) : 'N/A';
        const lng = telemetry.longitude !== null ? telemetry.longitude.toFixed(4) : 'N/A';
        const recorded = telemetry.recorded_at ? new Date(telemetry.recorded_at).toLocaleString() : 'N/A';
        
        dataEl.innerHTML = `
          <div><strong>Battery:</strong> ${soc}</div>
          <div><strong>Charging State:</strong> ${state}</div>
          <div><strong>Location:</strong> ${lat}, ${lng}</div>
          <div><strong>Recorded:</strong> ${recorded}</div>
        `;
        displayEl.style.display = 'block';
      }
    } catch (err) {
      console.error('[Profile][EV] Telemetry test failed', err);
      alert('Failed to fetch telemetry. Please try again.');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Test Telemetry';
    }
  }

  rootEl.querySelector('#me-connect-ev-btn')?.addEventListener('click', handleConnectEvClick);
  rootEl.querySelector('#me-test-telemetry-btn')?.addEventListener('click', handleTestTelemetryClick);
  
  // Check status on page load
  checkVehicleStatus();
  
  // Check for callback success/error in URL
  const urlParams = new URLSearchParams(window.location.search);
  const vehicleConnected = urlParams.get('vehicle');
  const error = urlParams.get('error');
  
  if (vehicleConnected === 'connected') {
    setTimeout(() => {
      checkVehicleStatus();
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname);
    }, 500);
  } else if (error) {
    const statusEl = rootEl.querySelector('#me-vehicle-status');
    statusEl.textContent = `Connection failed: ${error}`;
    statusEl.style.background = '#fee2e2';
    statusEl.style.color = '#dc2626';
    // Clean URL
    window.history.replaceState({}, '', window.location.pathname);
  }
}

