import { apiGet } from './api.js';
export const demoState = { enabled:false, state:null };
export async function loadDemoState() {
  try {
    const res = await apiGet('/v1/demo/state');
    if (res && res.state) {
      demoState.enabled = true;
      demoState.state = res.state;
      document.body.classList.add('demo');
      document.body.setAttribute('data-demo-state', JSON.stringify(res.state));
    }
  } catch(e) { /* not in demo */ }
}
