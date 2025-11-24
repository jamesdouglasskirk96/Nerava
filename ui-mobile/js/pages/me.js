export async function initMePage(rootEl) {
  rootEl.innerHTML = `
    <div style="padding: 12px; background: white; min-height: calc(100vh - 120px); overflow-y: auto;">
      <div style="background: #f8fafc; padding: 14px; border-radius: 10px; margin-bottom: 12px;">
        <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 12px;">
          <div style="width: 36px; height: 36px; border-radius: 50%; background: #e2e8f0; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: bold;">@</div>
          <div>
            <div style="font-size: 16px; font-weight: bold; color: #111827;">@you</div>
            <div style="color: #4b5563; font-size: 13px;" id="me-rep">Energy Reputation — Silver · 12 followers · 8 following</div>
          </div>
        </div>
        <button style="background: #22c55e; color: white; border: none; padding: 10px 16px; border-radius: 6px; font-weight: 600; font-size: 14px;" id="btn-prefs">Preferences</button>
      </div>

      <div style="background: #f8fafc; padding: 14px; border-radius: 10px; margin-bottom: 12px;">
        <h2 style="color: #111827; font-size: 16px; margin-bottom: 8px;">Vehicle</h2>
        <div style="color: #4b5563; font-size: 13px; margin-bottom: 12px;" id="me-vehicle-hint">Add your EV for smarter suggestions</div>
        <button style="background: #3b5bfd; color: white; border: none; padding: 10px 16px; border-radius: 6px; font-weight: 600; font-size: 14px; margin-right: 8px;" id="me-add-vehicle">Add vehicle</button>
        <button style="background: #f1f5f9; color: #0f172a; border: none; padding: 10px 16px; border-radius: 6px; font-weight: 600; font-size: 14px; display: none;" id="me-edit-vehicle">Edit</button>
      </div>

      <div style="background: #f8fafc; padding: 14px; border-radius: 10px; margin-bottom: 12px;">
        <h2 style="color: #111827; font-size: 16px; margin-bottom: 10px;">Notifications</h2>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #e2e8f0;">
          <span style="color: #374151; font-size: 13px;">Green Hour alerts</span>
          <label style="display: flex; align-items: center; gap: 6px;">
            <input id="n-green" type="checkbox" checked style="width: 14px; height: 14px;">
            <span style="color: #374151; font-size: 13px;">On</span>
          </label>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0;">
          <span style="color: #374151; font-size: 13px;">Nearby perk alerts</span>
          <label style="display: flex; align-items: center; gap: 6px;">
            <input id="n-perk" type="checkbox" checked style="width: 14px; height: 14px;">
            <span style="color: #374151; font-size: 13px;">On</span>
          </label>
        </div>
      </div>

      <!-- Merchant Dashboard Link (hidden unless ?merchant=xxx) -->
      <div id="merchant-dashboard-link" style="background: #f8fafc; padding: 14px; border-radius: 10px; margin-bottom: 12px; display: none;">
        <h2 style="color: #111827; font-size: 16px; margin-bottom: 10px;">Merchant Tools</h2>
        <button 
          id="btn-merchant-dashboard"
          style="background: #3b5bfd; color: white; border: none; padding: 10px 16px; border-radius: 6px; font-weight: 600; font-size: 14px; width: 100%;"
        >
          Open Dashboard
        </button>
      </div>

      <div style="background: #f8fafc; padding: 14px; border-radius: 10px;">
        <h2 style="color: #111827; font-size: 16px; margin-bottom: 10px;">Account</h2>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <button style="background: #f1f5f9; color: #0f172a; border: none; padding: 10px 16px; border-radius: 6px; font-weight: 600; font-size: 14px; flex: 1; min-width: 0;">Export</button>
          <button style="background: #f1f5f9; color: #0f172a; border: none; padding: 10px 16px; border-radius: 6px; font-weight: 600; font-size: 14px; flex: 1; min-width: 0;">Support</button>
          <button style="background: #f1f5f9; color: #ef4444; border: none; padding: 10px 16px; border-radius: 6px; font-weight: 600; font-size: 14px; flex: 1; min-width: 0;">Sign out</button>
        </div>
      </div>
    </div>
  `;

  // Load profile data from API
  try {
    const data = await window.NeravaAPI.apiGet('/v1/profile/me');
    if (data) {
      
      // Update profile info
      document.querySelector('#me-rep').textContent = `Energy Reputation — Silver • ${data.followers} followers · ${data.following} following`;
      
      // Update settings
      const settings = data.settings || {};
      document.querySelector('#n-green').checked = settings.greenAlerts !== false;
      document.querySelector('#n-perk').checked = settings.perkAlerts !== false;
      
      // Update vehicle
      if (settings.vehicle) {
        document.querySelector('#me-vehicle-hint').textContent = `${settings.vehicle.model} • ${settings.vehicle.range} mi`;
        document.querySelector('#me-edit-vehicle').style.display = 'inline-flex';
      }
    }
  } catch (e) {
    console.error('Profile API error:', e);
  }

  // Check for merchant query param and show dashboard link
  const urlParams = new URLSearchParams(location.search);
  const merchantId = urlParams.get('merchant');
  if (merchantId) {
    const dashboardLink = document.querySelector('#merchant-dashboard-link');
    if (dashboardLink) {
      dashboardLink.style.display = 'block';
      const btn = document.querySelector('#btn-merchant-dashboard');
      if (btn) {
        btn.addEventListener('click', () => {
          location.hash = `#/merchant-dashboard?merchant_id=${encodeURIComponent(merchantId)}`;
        });
      }
    }
  }

  // Wire handlers
  document.querySelector('#btn-prefs').addEventListener('click', () => alert('Preferences (coming soon)'));
  document.querySelector('#me-add-vehicle').addEventListener('click', async () => {
    const vehicle = { model: 'Tesla Model 3', range: '272' };
    try {
      const result = await window.NeravaAPI.apiPost('/v1/profile/settings', JSON.stringify({ vehicle }), { 'Content-Type': 'application/json' });
      if (result) {
        document.querySelector('#me-vehicle-hint').textContent = `${vehicle.model} • ${vehicle.range} mi`;
        document.querySelector('#me-edit-vehicle').style.display = 'inline-flex';
      }
    } catch (e) {
      console.error('Save vehicle failed:', e);
    }
  });
  
  // Save settings when toggles change
  document.querySelector('#n-green').addEventListener('change', saveSettings);
  document.querySelector('#n-perk').addEventListener('change', saveSettings);
  
  async function saveSettings() {
    try {
      const settings = {
        greenAlerts: document.querySelector('#n-green').checked,
        perkAlerts: document.querySelector('#n-perk').checked
      };
      await window.NeravaAPI.apiPost('/v1/profile/settings', JSON.stringify(settings), { 'Content-Type': 'application/json' });
    } catch (e) {
      console.error('Save settings failed:', e);
    }
  }
}