export function renderBehaviorCloud(root, data){
  const part = Object.entries(data.participation||{}).map(([h,v])=>({hour:h, rate:v}));
  const segs = Object.entries(data.segments||{}).map(([k,v])=>({name:k, count:v}));
  const els = Object.entries(data.elasticity||{}).map(([p,l])=>({price:+p, lift:l}));
  
  root.innerHTML = `
    <h2>Behavior Cloud</h2>
    <div class="grid">
      <div class="card" id="part"></div>
      <div class="card">
        <h3>Top segments</h3>
        <ul>${segs.sort((a,b)=>b.count-a.count).slice(0,5).map(s=>`<li>${s.name}: ${s.count}</li>`).join('')}</ul>
      </div>
      <div class="card" id="elas"></div>
    </div>`;
  
  // Render charts
  const p = root.querySelector('#part');
  const e = root.querySelector('#elas');
  p.style.width='100%'; 
  p.style.height='240px';
  e.style.width='100%'; 
  e.style.height='240px';
  
  p.innerHTML = `
    <h4>Participation Rate</h4>
    <div class="chart-placeholder">
      ${part.map(p => `<div>Hour ${p.hour}: ${p.rate}%</div>`).join('')}
    </div>
  `;
  
  e.innerHTML = `
    <h4>Price Elasticity</h4>
    <div class="chart-placeholder">
      ${els.map(e => `<div>$${e.price}: ${e.lift}% lift</div>`).join('')}
    </div>
  `;
}
