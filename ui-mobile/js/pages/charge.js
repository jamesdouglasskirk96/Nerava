export function initChargePage(){
  // placeholder; no scan UI. Could show "Verify by location" card later.
  const el = document.getElementById('page-charge');
  if (!el) return;
  el.innerHTML = el.innerHTML || '<div style="padding:16px;color:#6b7280">Charge tools coming soon.</div>';
}