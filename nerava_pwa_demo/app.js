async function runDemo() {
  const out = document.getElementById('output');
  const log = (msg) => out.innerHTML += `<p>${msg}</p>`;

  log(`<strong>Running Nerava demo...</strong>`);
  try {
    const health = await fetch(`${CONFIG.baseUrl}/v1/health`).then(r=>r.json());
    log(`✅ Health: ${JSON.stringify(health)}`);

    const hubs = await fetch(`${CONFIG.baseUrl}/v1/hubs/nearby?lat=${CONFIG.lat}&lng=${CONFIG.lng}&radius_km=2`)
      .then(r=>r.json());
    log(`⚡ Found ${hubs.length} hubs`);

    const rec = await fetch(`${CONFIG.baseUrl}/v1/hubs/recommend?lat=${CONFIG.lat}&lng=${CONFIG.lng}&radius_km=2&user_id=${CONFIG.user}`)
      .then(r=>r.json());
    log(`🏁 Recommended hub: ${rec.name}`);

    const merchants = await fetch(`${CONFIG.baseUrl}${rec.merchants_url}`).then(r=>r.json());
    log(`🛍️ Nearby merchants: ${merchants.length}`);

    const wallet = await fetch(`${CONFIG.baseUrl}/v1/wallet?user_id=${CONFIG.user}`).then(r=>r.json());
    log(`💰 Wallet balance: ${wallet.balance_cents}¢`);

    log("<strong>✅ Demo complete!</strong>");
  } catch (e) {
    log(`<span style='color:red'>Error: ${e}</span>`);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('backend-url').textContent = CONFIG.baseUrl;
  document.getElementById('run-demo').addEventListener('click', runDemo);
});
