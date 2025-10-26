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
      ul.innerHTML = items.map(it => `
        <li class="intent">
          <div class="intent__main">
            <div class="title">${it.title}</div>
            <div class="sub">${it.subtitle}</div>
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
          const cfg = await window.NeravaAPI.apiPost(`/v1/intent/${id}/start`, '');
          if (!cfg) {
            showToast('Cannot start');
            return;
          }
          showToast('Started! Ready to verify location');
          load();
        } catch (e) {
          console.error('Start failed:', e);
          showToast('Start failed');
        }
      });
    });
    
    ul.querySelectorAll('[data-notify]').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const id = e.currentTarget.getAttribute('data-notify');
        try {
          const result = await window.NeravaAPI.apiPost(`/v1/intent/${id}/notify`, '');
          if (result) {
            showToast('We will remind you 👍');
          } else {
            showToast('Notification setup failed');
          }
        } catch (e) {
          console.error('Notify failed:', e);
          showToast('Notification setup failed');
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
