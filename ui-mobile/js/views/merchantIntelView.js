export function renderMerchantIntel(root, data){
  const cohorts = Object.entries(data.cohorts||{}).map(([k,v])=>({name:k, value:v.count||v}));
  const hourly = Object.entries((data.forecasts?.hourly_expectations)||{}).map(([h,v])=>({hour: h, expected: v}));
  
  root.innerHTML = `
    <h2>Merchant Intelligence</h2>
    <div class="grid">
      <div class="card" id="cohort"></div>
      <div class="card" id="forecast"></div>
      <div class="card">
        <h3>Promo</h3>
        <p>${(data.promos?.[0]?.label)||'None'}</p>
        <p><small>Target: ${(data.promos?.[0]?.target)||'—'}</small></p>
      </div>
    </div>`;
  
  // Render charts
  const c = root.querySelector('#cohort'); 
  const f = root.querySelector('#forecast');
  c.style.width='100%'; 
  c.style.height='240px';
  f.style.width='100%'; 
  f.style.height='240px';
  
  // Simple chart rendering without React for now
  c.innerHTML = `
    <h4>Cohort Distribution</h4>
    <div class="chart-placeholder">
      ${cohorts.map(c => `<div>${c.name}: ${c.value}</div>`).join('')}
    </div>
  `;
  
  f.innerHTML = `
    <h4>24h Forecast</h4>
    <div class="chart-placeholder">
      ${hourly.map(h => `<div>Hour ${h.hour}: ${h.expected} expected</div>`).join('')}
    </div>
  `;
}
