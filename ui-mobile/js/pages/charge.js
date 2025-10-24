// Minimal placeholder to satisfy import and show a simple screen
export function initChargePage() {
  const root = document.getElementById('page-charge');
  if (!root) return;
  root.innerHTML = `
    <section class="pad">
      <h2>Charge</h2>
      <p>Location-based verification is enabled. When you start a session, we'll verify automatically by proximity.</p>
      <button class="btn primary" id="btn-start-session">Start session</button>
    </section>
  `;
  document.getElementById('btn-start-session')?.addEventListener('click', ()=> {
    alert('Starting demo session (placeholder).');
  });
}