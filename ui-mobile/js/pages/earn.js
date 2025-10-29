export async function initEarnPage(rootEl) {
  rootEl.innerHTML = `
    <section class="card card--pad">
      <div class="eyebrow">Soon to be claimed perks</div>
      <ul id="intent-list" class="list list--intents"></ul>
    </section>`;

  const ul = rootEl.querySelector('#intent-list');

  async function load() {
    try {
      const items = await window.NeravaAPI.apiGet('/v1/intent') || [];
      
      if (items.length === 0) {
        ul.innerHTML = '<li class="intent"><div class="sub">No saved intents yet. Tap "Notify" on a perk to save it!</div></li>';
        return;
      }
      
      ul.innerHTML = items.map(it => `
        <li class="intent">
          <div class="intent__main">
            <div class="title">${it.merchant || it.merchant_name || 'Unknown Merchant'}</div>
            <div class="sub">${it.window_text || ''} • ${it.distance_text || ''}</div>
            <div class="sub" style="font-size: 11px; color: #666; margin-top: 4px;">${it.station_name || ''}</div>
          </div>
          <div class="intent__cta">
            <button data-activate="${it.id}" class="btn btn-blue">Activate</button>
          </div>
        </li>`).join('');
      bind();
    } catch (e) {
      console.error('Failed to load intents:', e);
      ul.innerHTML = '<li class="intent"><div class="sub">No saved intents yet</div></li>';
    }
  }

  function bind() {
    ul.querySelectorAll('[data-activate]').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const id = e.currentTarget.getAttribute('data-activate');
        try {
          // Placeholder for activation flow
          // In the future, this could start a session or open navigation
          showToast('Activation flow coming soon!');
          console.log('Activate intent:', id);
          
          // Optional: remove the intent after activation
          // await window.NeravaAPI.apiPost(`/v1/intent/${id}/start`, '');
          // load();
        } catch (e) {
          console.error('Activation failed:', e);
          showToast('Activation failed');
        }
      });
    });
  }

  load();
}

// Toast helper
function showToast(message) {
  const toast = document.createElement('div');
  toast.style.cssText = 'position:fixed;left:50%;bottom:100px;transform:translateX(-50%);background:#111;color:#fff;padding:10px 14px;border-radius:12px;z-index:9999;font-weight:700';
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}
