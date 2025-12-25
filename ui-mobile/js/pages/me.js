import { 
  apiMe, 
  apiLogout, 
  getCurrentUser, 
  apiGetSmartcarConnectUrl, 
  apiEvStatus,
  apiEvDisconnect,
  apiWalletSummary,
  apiWalletPassStatus,
  apiWalletPassReinstall,
  apiNotifPrefsGet,
  apiNotifPrefsPut,
  apiAccountExport,
  apiAccountDelete,
} from '../core/api.js';
import { getRefreshToken, clearTokens } from '../core/auth.js';

/**
 * Format relative time (e.g., "2 hours ago", "Just now")
 */
function formatRelativeTime(dateString) {
  if (!dateString) return 'Never';
  
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  return date.toLocaleDateString();
}

/**
 * Format auth provider name for display
 */
function formatAuthProvider(provider) {
  const providers = {
    'google': 'Google',
    'apple': 'Apple',
    'phone': 'Phone',
    'local': 'Email',
  };
  return providers[provider] || provider;
}

export async function initMePage(rootEl) {
  console.log('[Profile] Initializing profile page...');

  // Get user info
  let user = null;
  try {
    user = await apiMe();
  } catch (e) {
    console.warn('[Profile] Could not load user:', e.message);
    if (e.message && (e.message.includes('401') || e.message.includes('Unauthorized'))) {
      window.location.hash = '#/login';
      return;
    }
  }

  if (!user) {
    console.error('[Profile] No user data available');
    return;
  }

  const userName = user?.display_name || user?.name || user?.email || user?.phone || 'User';
  const userEmail = user?.email || null;
  const authProvider = user?.auth_provider || 'unknown';
  const publicId = user?.public_id || null;

  // Render page structure
  rootEl.innerHTML = `
    <div class="profile-page">
      <!-- Account Section -->
      <div class="profile-section">
        <h2 class="profile-section-title">Account</h2>
        <div class="profile-card">
          <div class="profile-field">
            <span class="profile-label">Name</span>
            <span class="profile-value" id="profile-name">${userName || '—'}</span>
          </div>
          <div class="profile-field">
            <span class="profile-label">Email</span>
            <span class="profile-value" id="profile-email">${userEmail || '—'}</span>
          </div>
          <div class="profile-field">
            <span class="profile-label">Signed in with</span>
            <span class="profile-value">${formatAuthProvider(authProvider)}</span>
          </div>
        </div>
      </div>

      <!-- Vehicle Section -->
      <div class="profile-section">
        <h2 class="profile-section-title">Vehicle</h2>
        <div class="profile-card" id="vehicle-card">
          <div id="vehicle-loading" class="profile-loading">Loading vehicle status...</div>
          <div id="vehicle-error" class="profile-error" style="display: none;">
            <div class="profile-error-message"></div>
            <button class="profile-retry-btn" onclick="window._retryVehicleStatus()">Retry</button>
          </div>
          <div id="vehicle-content" style="display: none;">
            <div class="profile-field">
              <span class="profile-label">Status</span>
              <span class="profile-status-pill" id="vehicle-status-pill"></span>
            </div>
            <div class="profile-field" id="vehicle-name-field" style="display: none;">
              <span class="profile-label">Vehicle</span>
              <span class="profile-value" id="vehicle-name"></span>
            </div>
            <div class="profile-field" id="vehicle-sync-field" style="display: none;">
              <span class="profile-label">Last sync</span>
              <span class="profile-value" id="vehicle-sync"></span>
            </div>
            <div class="profile-actions" id="vehicle-actions"></div>
          </div>
        </div>
      </div>

      <!-- Wallet Section -->
      <div class="profile-section">
        <h2 class="profile-section-title">Wallet</h2>
        <div class="profile-card" id="wallet-card">
          <div id="wallet-loading" class="profile-loading">Loading wallet status...</div>
          <div id="wallet-error" class="profile-error" style="display: none;">
            <div class="profile-error-message"></div>
            <button class="profile-retry-btn" onclick="window._retryWalletStatus()">Retry</button>
          </div>
          <div id="wallet-content" style="display: none;">
            <div class="profile-field" id="wallet-balance-field" style="display: none;">
              <span class="profile-label">Nova Balance</span>
              <span class="profile-value" id="wallet-balance"></span>
            </div>
            <div class="profile-field">
              <span class="profile-label">Wallet Pass</span>
              <span class="profile-value" id="wallet-pass-status">Checking...</span>
            </div>
            <div class="profile-actions">
              <button class="profile-btn" id="wallet-pass-btn" style="display: none;">Add/Reinstall Wallet Pass</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Notifications Section -->
      <div class="profile-section">
        <h2 class="profile-section-title">Notifications</h2>
        <div class="profile-card" id="notifications-card">
          <div id="notifications-loading" class="profile-loading">Loading preferences...</div>
          <div id="notifications-error" class="profile-error" style="display: none;">
            <div class="profile-error-message"></div>
            <button class="profile-retry-btn" onclick="window._retryNotifications()">Retry</button>
          </div>
          <div id="notifications-content" style="display: none;">
            <div class="profile-toggle-field">
              <label class="profile-toggle">
                <input type="checkbox" id="notif-earned-nova">
                <span class="profile-toggle-label">Earned Nova</span>
              </label>
            </div>
            <div class="profile-toggle-field">
              <label class="profile-toggle">
                <input type="checkbox" id="notif-nearby-nova">
                <span class="profile-toggle-label">Nearby Nova merchants</span>
              </label>
            </div>
            <div class="profile-toggle-field">
              <label class="profile-toggle">
                <input type="checkbox" id="notif-wallet-reminders">
                <span class="profile-toggle-label">Wallet reminders</span>
              </label>
            </div>
            <div id="notifications-permission-warning" class="profile-warning" style="display: none;">
              Notifications are disabled. Enable in Settings.
            </div>
          </div>
        </div>
      </div>

      <!-- Privacy & Legal Section -->
      <div class="profile-section">
        <h2 class="profile-section-title">Privacy & Legal</h2>
        <div class="profile-card">
          <a href="https://nerava.app/privacy" target="_blank" class="profile-link">Privacy Policy</a>
          <a href="https://nerava.app/terms" target="_blank" class="profile-link">Terms of Use</a>
          <a href="https://nerava.app/privacy-choices" target="_blank" class="profile-link">Privacy Choices / Do Not Sell or Share</a>
          <a href="mailto:support@nerava.com?subject=Support%20Request" class="profile-link">Contact Support</a>
        </div>
      </div>

      <!-- Advanced Section (collapsed by default) -->
      <div class="profile-section">
        <h2 class="profile-section-title">
          <button class="profile-section-toggle" id="advanced-toggle">
            Advanced
            <span class="profile-toggle-icon">▼</span>
          </button>
        </h2>
        <div class="profile-card" id="advanced-card" style="display: none;">
          <div class="profile-field">
            <span class="profile-label">App Version</span>
            <span class="profile-value">1.0.0</span>
          </div>
          <div class="profile-field" id="api-url-field" style="display: none;">
            <span class="profile-label">API Base URL</span>
            <span class="profile-value" id="api-url"></span>
          </div>
          <div class="profile-field" id="account-id-field">
            <span class="profile-label">Account ID</span>
            <span class="profile-value" id="account-id">${publicId || '—'}</span>
          </div>
          <div class="profile-actions">
            <button class="profile-btn profile-btn-secondary" id="export-data-btn">Request Data Export</button>
            <button class="profile-btn profile-btn-danger" id="delete-account-btn">Delete Account</button>
          </div>
        </div>
      </div>

      <!-- Sign Out -->
      <div class="profile-section">
        <button class="profile-btn profile-btn-danger profile-btn-full" id="sign-out-btn">Sign Out</button>
      </div>
    </div>
  `;

  // Store retry functions globally for onclick handlers
  window._retryVehicleStatus = () => loadVehicleStatus(rootEl);
  window._retryWalletStatus = () => loadWalletStatus(rootEl);
  window._retryNotifications = () => loadNotifications(rootEl);

  // Wire up event handlers
  setupEventHandlers(rootEl, user);

  // Load all sections
  loadVehicleStatus(rootEl);
  loadWalletStatus(rootEl);
  loadNotifications(rootEl);

  // Show API URL in dev mode
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    const apiUrlField = rootEl.querySelector('#api-url-field');
    const apiUrlValue = rootEl.querySelector('#api-url');
    if (apiUrlField && apiUrlValue) {
      apiUrlField.style.display = 'flex';
      const BASE = window.location.origin;
      apiUrlValue.textContent = BASE || 'Same origin';
    }
  }
}

function setupEventHandlers(rootEl, user) {
  // Advanced section toggle
  const advancedToggle = rootEl.querySelector('#advanced-toggle');
  const advancedCard = rootEl.querySelector('#advanced-card');
  if (advancedToggle && advancedCard) {
    advancedToggle.addEventListener('click', () => {
      const isVisible = advancedCard.style.display !== 'none';
      advancedCard.style.display = isVisible ? 'none' : 'block';
      const icon = advancedToggle.querySelector('.profile-toggle-icon');
      if (icon) {
        icon.textContent = isVisible ? '▼' : '▲';
      }
    });
  }

  // Vehicle actions
  const vehicleActions = rootEl.querySelector('#vehicle-actions');
  if (vehicleActions) {
    vehicleActions.addEventListener('click', async (e) => {
      if (e.target.id === 'connect-vehicle-btn') {
        await handleConnectVehicle(rootEl);
      } else if (e.target.id === 'disconnect-vehicle-btn') {
        await handleDisconnectVehicle(rootEl);
      } else if (e.target.id === 'reconnect-vehicle-btn') {
        await handleReconnectVehicle(rootEl);
      }
    });
  }

  // Wallet pass button
  const walletPassBtn = rootEl.querySelector('#wallet-pass-btn');
  if (walletPassBtn) {
    walletPassBtn.addEventListener('click', async () => {
      await handleWalletPassReinstall(rootEl);
    });
  }

  // Notification toggles
  const earnedNovaToggle = rootEl.querySelector('#notif-earned-nova');
  const nearbyNovaToggle = rootEl.querySelector('#notif-nearby-nova');
  const walletRemindersToggle = rootEl.querySelector('#notif-wallet-reminders');
  
  if (earnedNovaToggle) {
    earnedNovaToggle.addEventListener('change', async () => {
      await updateNotificationPrefs(rootEl, {
        earned_nova: earnedNovaToggle.checked
      });
    });
  }
  if (nearbyNovaToggle) {
    nearbyNovaToggle.addEventListener('change', async () => {
      await updateNotificationPrefs(rootEl, {
        nearby_nova: nearbyNovaToggle.checked
      });
    });
  }
  if (walletRemindersToggle) {
    walletRemindersToggle.addEventListener('change', async () => {
      await updateNotificationPrefs(rootEl, {
        wallet_reminders: walletRemindersToggle.checked
      });
    });
  }

  // Export data button
  const exportBtn = rootEl.querySelector('#export-data-btn');
  if (exportBtn) {
    exportBtn.addEventListener('click', async () => {
      await handleExportData(rootEl);
    });
  }

  // Delete account button
  const deleteBtn = rootEl.querySelector('#delete-account-btn');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', async () => {
      await handleDeleteAccount(rootEl);
    });
  }

  // Sign out button
  const signOutBtn = rootEl.querySelector('#sign-out-btn');
  if (signOutBtn) {
    signOutBtn.addEventListener('click', async () => {
      await handleSignOut();
    });
  }
}

async function loadVehicleStatus(rootEl) {
  const loadingEl = rootEl.querySelector('#vehicle-loading');
  const errorEl = rootEl.querySelector('#vehicle-error');
  const contentEl = rootEl.querySelector('#vehicle-content');
  const errorMsgEl = rootEl.querySelector('#vehicle-error .profile-error-message');
  const statusPill = rootEl.querySelector('#vehicle-status-pill');
  const vehicleName = rootEl.querySelector('#vehicle-name');
  const vehicleNameField = rootEl.querySelector('#vehicle-name-field');
  const vehicleSync = rootEl.querySelector('#vehicle-sync');
  const vehicleSyncField = rootEl.querySelector('#vehicle-sync-field');
  const vehicleActions = rootEl.querySelector('#vehicle-actions');

  try {
    loadingEl.style.display = 'block';
    errorEl.style.display = 'none';
    contentEl.style.display = 'none';

    const status = await apiEvStatus();

    loadingEl.style.display = 'none';
    contentEl.style.display = 'block';

    // Set status pill
    if (statusPill) {
      const statusText = status.status === 'connected' ? 'Connected' :
                        status.status === 'needs_attention' ? 'Needs attention' :
                        'Not connected';
      const statusClass = status.status === 'connected' ? 'status-connected' :
                         status.status === 'needs_attention' ? 'status-warning' :
                         'status-disconnected';
      statusPill.textContent = statusText;
      statusPill.className = `profile-status-pill ${statusClass}`;
    }

    // Set vehicle name
    if (status.vehicle_label) {
      if (vehicleName) vehicleName.textContent = status.vehicle_label;
      if (vehicleNameField) vehicleNameField.style.display = 'flex';
    } else {
      if (vehicleNameField) vehicleNameField.style.display = 'none';
    }

    // Set last sync
    if (status.last_sync_at) {
      if (vehicleSync) vehicleSync.textContent = formatRelativeTime(status.last_sync_at);
      if (vehicleSyncField) vehicleSyncField.style.display = 'flex';
    } else {
      if (vehicleSync) vehicleSync.textContent = 'Never';
      if (vehicleSyncField) vehicleSyncField.style.display = 'flex';
    }

    // Set actions
    if (vehicleActions) {
      if (status.connected) {
        vehicleActions.innerHTML = `
          <button class="profile-btn profile-btn-secondary" id="disconnect-vehicle-btn">Disconnect</button>
          <button class="profile-btn" id="reconnect-vehicle-btn">Reconnect</button>
        `;
      } else {
        vehicleActions.innerHTML = `
          <button class="profile-btn" id="connect-vehicle-btn">Connect Vehicle</button>
        `;
      }
    }
  } catch (e) {
    loadingEl.style.display = 'none';
    errorEl.style.display = 'block';
    if (errorMsgEl) {
      errorMsgEl.textContent = `Failed to load vehicle status: ${e.message}`;
    }
  }
}

async function loadWalletStatus(rootEl) {
  const loadingEl = rootEl.querySelector('#wallet-loading');
  const errorEl = rootEl.querySelector('#wallet-error');
  const contentEl = rootEl.querySelector('#wallet-content');
  const errorMsgEl = rootEl.querySelector('#wallet-error .profile-error-message');
  const balanceEl = rootEl.querySelector('#wallet-balance');
  const balanceField = rootEl.querySelector('#wallet-balance-field');
  const passStatusEl = rootEl.querySelector('#wallet-pass-status');
  const passBtn = rootEl.querySelector('#wallet-pass-btn');

  try {
    loadingEl.style.display = 'block';
    errorEl.style.display = 'none';
    contentEl.style.display = 'none';

    // Load wallet summary for balance
    try {
      const summary = await apiWalletSummary();
      if (summary && summary.nova_balance !== undefined) {
        if (balanceEl) balanceEl.textContent = `${summary.nova_balance} Nova`;
        if (balanceField) balanceField.style.display = 'flex';
      }
    } catch (e) {
      console.warn('[Profile] Could not load wallet balance:', e.message);
      // Continue without balance
    }

    // Load pass status
    const passStatus = await apiWalletPassStatus();
    
    loadingEl.style.display = 'none';
    contentEl.style.display = 'block';

    if (passStatusEl) {
      if (passStatus.wallet_pass_last_generated_at) {
        passStatusEl.textContent = 'Installed';
      } else {
        passStatusEl.textContent = 'Not installed';
      }
    }

    if (passBtn) {
      passBtn.style.display = 'block';
    }
  } catch (e) {
    loadingEl.style.display = 'none';
    errorEl.style.display = 'block';
    if (errorMsgEl) {
      errorMsgEl.textContent = `Failed to load wallet status: ${e.message}`;
    }
  }
}

async function loadNotifications(rootEl) {
  const loadingEl = rootEl.querySelector('#notifications-loading');
  const errorEl = rootEl.querySelector('#notifications-error');
  const contentEl = rootEl.querySelector('#notifications-content');
  const errorMsgEl = rootEl.querySelector('#notifications-error .profile-error-message');
  const earnedToggle = rootEl.querySelector('#notif-earned-nova');
  const nearbyToggle = rootEl.querySelector('#notif-nearby-nova');
  const remindersToggle = rootEl.querySelector('#notif-wallet-reminders');
  const permissionWarning = rootEl.querySelector('#notifications-permission-warning');

  try {
    loadingEl.style.display = 'block';
    errorEl.style.display = 'none';
    contentEl.style.display = 'none';

    // Check notification permission
    if ('Notification' in window) {
      const permission = Notification.permission;
      if (permission === 'denied' && permissionWarning) {
        permissionWarning.style.display = 'block';
      }
    }

    const prefs = await apiNotifPrefsGet();

    loadingEl.style.display = 'none';
    contentEl.style.display = 'block';

    if (earnedToggle) earnedToggle.checked = prefs.earned_nova;
    if (nearbyToggle) nearbyToggle.checked = prefs.nearby_nova;
    if (remindersToggle) remindersToggle.checked = prefs.wallet_reminders;
  } catch (e) {
    loadingEl.style.display = 'none';
    errorEl.style.display = 'block';
    if (errorMsgEl) {
      errorMsgEl.textContent = `Failed to load notification preferences: ${e.message}`;
    }
  }
}

async function updateNotificationPrefs(rootEl, partialPrefs) {
  try {
    // Get current prefs first
    const currentPrefs = await apiNotifPrefsGet();
    const updatedPrefs = { ...currentPrefs, ...partialPrefs };
    
    await apiNotifPrefsPut(updatedPrefs);
    console.log('[Profile] Notification preferences updated');
  } catch (e) {
    console.error('[Profile] Failed to update notification preferences:', e);
    alert(`Failed to update preferences: ${e.message}`);
    // Reload to restore previous state
    loadNotifications(rootEl);
  }
}

async function handleConnectVehicle(rootEl) {
  try {
    const res = await apiGetSmartcarConnectUrl();
    if (res?.url) {
      window.location.href = res.url;
    } else {
      alert('Unable to start vehicle connection. Please try again.');
    }
  } catch (e) {
    console.error('[Profile] Connect vehicle failed:', e);
    alert(`Failed to connect vehicle: ${e.message}`);
  }
}

async function handleDisconnectVehicle(rootEl) {
  if (!confirm('Are you sure you want to disconnect your vehicle?')) {
    return;
  }

  try {
    await apiEvDisconnect();
    alert('Vehicle disconnected successfully.');
    loadVehicleStatus(rootEl);
  } catch (e) {
    console.error('[Profile] Disconnect vehicle failed:', e);
    alert(`Failed to disconnect vehicle: ${e.message}`);
  }
}

async function handleReconnectVehicle(rootEl) {
  await handleConnectVehicle(rootEl);
}

async function handleWalletPassReinstall(rootEl) {
  // Detect platform
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  const isAndroid = /Android/.test(navigator.userAgent);
  const platform = isIOS ? 'apple' : isAndroid ? 'google' : 'apple'; // Default to Apple

  const btn = rootEl.querySelector('#wallet-pass-btn');
  const originalText = btn ? btn.textContent : 'Add/Reinstall Wallet Pass';
  
  try {
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Processing...';
    }

    if (platform === 'apple') {
      // For Apple, redirect to create endpoint which returns .pkpass file
      // Use fetch to get the file and trigger download
      try {
        const response = await fetch('/v1/wallet/pass/apple/create', {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Authorization': `Bearer ${(await import('../core/auth.js')).getAccessToken()}`,
          },
        });
        
        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = 'nerava-wallet.pkpass';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
        } else {
          throw new Error(`Failed to create pass: ${response.status}`);
        }
      } catch (e) {
        // Fallback: redirect to endpoint
        window.location.href = '/v1/wallet/pass/apple/create';
      }
    } else {
      // For Google, call reinstall API
      const res = await apiWalletPassReinstall(platform);
      
      if (res && res.add_to_google_wallet_url) {
        window.open(res.add_to_google_wallet_url, '_blank');
      } else {
        alert('Wallet pass reinstall initiated. Check your Google Wallet app.');
      }
      
      if (btn) {
        btn.disabled = false;
        btn.textContent = originalText;
      }
    }
  } catch (e) {
    console.error('[Profile] Wallet pass reinstall failed:', e);
    alert(`Failed to reinstall wallet pass: ${e.message}`);
    if (btn) {
      btn.disabled = false;
      btn.textContent = originalText;
    }
  }
}

async function handleExportData(rootEl) {
  if (!confirm('Request a copy of your account data? You will receive an email when it\'s ready.')) {
    return;
  }

  try {
    const res = await apiAccountExport();
    alert(res.message || 'Export request submitted. You will receive an email when your data is ready.');
  } catch (e) {
    console.error('[Profile] Export data failed:', e);
    alert(`Failed to request data export: ${e.message}`);
  }
}

async function handleDeleteAccount(rootEl) {
  const confirmation = prompt('Type "DELETE" to confirm account deletion:');
  if (confirmation !== 'DELETE') {
    return;
  }

  if (!confirm('Are you absolutely sure? This action cannot be undone.')) {
    return;
  }

  try {
    await apiAccountDelete();
    alert('Account deletion requested. You will be signed out.');
    await handleSignOut();
  } catch (e) {
    console.error('[Profile] Delete account failed:', e);
    if (e.message && e.message.includes('CONFIRMATION_REQUIRED')) {
      alert('Please type "DELETE" exactly to confirm.');
    } else {
      alert(`Failed to delete account: ${e.message}`);
    }
  }
}

async function handleSignOut() {
  try {
    const refreshToken = getRefreshToken();
    await apiLogout(refreshToken);
  } catch (e) {
    console.warn('[Profile] Logout API call failed:', e.message);
    // Continue to clear tokens anyway
  } finally {
    clearTokens();
    window.location.hash = '#/login';
    window.location.reload();
  }
}
