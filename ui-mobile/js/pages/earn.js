export async function initEarnPage(rootEl) {
  rootEl.innerHTML = `
    <section class="card card--pad">
      <div class="eyebrow">Soon to be claimed perks</div>
      <ul id="intent-list" class="list list--intents"></ul>
    </section>`;

  const ul = rootEl.querySelector('#intent-list');

  async function load() {
    try {
      const res = await fetch('/v1/intents/me', { credentials: 'include' });
      const items = res.ok ? await res.json() : [];
      ul.innerHTML = items.map(it => `
        <li class="intent">
          <div class="intent__main">
            <div class="title">${it.merchant_name || it.station_name}</div>
            <div class="sub">${it.perk_title || ''} • ${it.address || ''}</div>
          </div>
          <div class="intent__cta">
            <button data-start="${it.id}" class="btn btn-blue">Start</button>
            <button data-notify="${it.id}" class="btn">Notify</button>
          </div>
        </li>`).join('');
      bind();
    } catch (e) {
      console.error('Failed to load intents:', e);
      ul.innerHTML = '<li class="intent"><div class="sub">No saved intents yet</div></li>';
    }
  }

  function bind() {
    ul.querySelectorAll('[data-start]').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const id = e.currentTarget.getAttribute('data-start');
        try {
          const r = await fetch(`/v1/intents/${id}/start`, {
            method: 'PATCH',
            credentials: 'include'
          });
          if (!r.ok) {
            showToast('Cannot start');
            return;
          }
          const cfg = await r.json();
          
          // Quick geo read
          if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(async pos => {
              const body = {
                lat: pos.coords.latitude,
                lng: pos.coords.longitude
              };
              const vr = await fetch(`/v1/intents/${id}/verify-geo`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
              });
              const vj = await vr.json();
              showToast(vj.pass ? 'Verified ✅' : 'Not in both zones yet');
              load();
            }, () => showToast('Location denied'));
          } else {
            showToast('Location unavailable');
          }
        } catch (e) {
          console.error('Start failed:', e);
          showToast('Start failed');
        }
      });
    });
    
    ul.querySelectorAll('[data-notify]').forEach(btn => {
      btn.addEventListener('click', () => showToast('We will remind you 👍'));
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
