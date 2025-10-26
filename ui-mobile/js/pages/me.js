export async function initMePage(rootEl) {
  rootEl.innerHTML = `
    <div class="me-content stack">

      <!-- Profile -->
      <section class="card card--xl">
        <div class="row">
          <div class="avatar" style="border-radius:50%; width:48px; height:48px; font-size:18px;">@</div>
          <div class="col">
            <div class="card-title">@you</div>
            <div class="subtle" id="me-rep">Energy Reputation — Silver • 12 followers · 8 following</div>
          </div>
        </div>
        <div class="hr"></div>
        <button class="btn btn-ghost btn-block" id="me-prefs">Preferences</button>
      </section>

      <!-- Vehicle -->
      <section class="card card--pad">
        <div class="row-between">
          <div class="card-title">Vehicle</div>
          <div class="subtle" id="me-vehicle-hint">Add your EV for smarter suggestions</div>
        </div>
        <div class="row" style="margin-top:12px">
          <button class="btn btn-success" id="me-add-vehicle">Add vehicle</button>
          <button class="btn btn-ghost" id="me-edit-vehicle" style="display:none">Edit</button>
        </div>
      </section>

      <!-- Notifications -->
      <section class="card card--pad">
        <div class="card-title">Notifications</div>
        <ul class="list" style="margin-top:6px">
          <li class="li">
            <div class="col">
              <div>Green Hour alerts</div>
              <div class="subtle">Save more when the grid is green</div>
            </div>
            <label class="pill"><input id="n-green" type="checkbox" style="accent-color:#3b5bfd"> On</label>
          </li>
          <li class="li">
            <div class="col">
              <div>Nearby perk alerts</div>
              <div class="subtle">When you're close to a perk you can claim</div>
            </div>
            <label class="pill"><input id="n-perk" type="checkbox" style="accent-color:#3b5bfd"> On</label>
          </li>
        </ul>
      </section>

      <!-- Account -->
      <section class="card card--pad">
        <div class="card-title">Account</div>
        <div class="row" style="margin-top:12px; gap:8px">
          <button class="btn btn-ghost">Export data</button>
          <button class="btn btn-ghost">Support</button>
          <button class="btn btn-ghost" style="margin-left:auto; color:#ef4444">Sign out</button>
        </div>
      </section>
    </div>
  `;

  // Demo handlers
  document.querySelector('#me-prefs').addEventListener('click', () => alert('Preferences (coming soon)'));
  document.querySelector('#me-add-vehicle').addEventListener('click', () => {
    document.querySelector('#me-vehicle-hint').textContent = 'Tesla Model 3 • 272 mi';
    document.querySelector('#me-edit-vehicle').style.display = 'inline-flex';
  });
}