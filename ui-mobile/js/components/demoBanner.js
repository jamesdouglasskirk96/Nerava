import { demoState } from '../core/demo.js';
export function ensureDemoBanner() {
  if (!demoState.enabled) return;
  let bar = document.getElementById('demo-banner');
  if (!bar) {
    bar = document.createElement('div');
    bar.id = 'demo-banner';
    bar.className = 'demo-banner';
    document.body.prepend(bar);
  }
  const s = demoState.state || {};
  bar.innerHTML = `
    <div class="badge">DEMO</div>
    <div class="state">
      <span>${s.grid_state || 'offpeak'}</span> •
      <span>${s.merchant_shift || 'balanced'}</span> •
      <span>${s.rep_profile || 'high'}</span> •
      <span>${s.city || 'austin'}</span>
    </div>`;
}
