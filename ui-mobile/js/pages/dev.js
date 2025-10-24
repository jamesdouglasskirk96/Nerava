import { apiGet } from '../core/api.js';
import { demoState } from '../core/demo.js';
import { renderMerchantIntel } from '../views/merchantIntelView.js';
import { renderBehaviorCloud } from '../views/behaviorCloudView.js';

export async function mountDev(root){
  if(!demoState.enabled){ 
    root.innerHTML='<p>Demo not enabled.</p>'; 
    return; 
  }
  root.innerHTML = `
    <div class="dev-tabs">
      <button data-v="merchant">Merchant Intel</button>
      <button data-v="cloud">Behavior Cloud</button>
    </div>
    <div id="dev-view"></div>`;
  
  const view = root.querySelector('#dev-view');
  root.querySelector('[data-v="merchant"]').onclick = async ()=>{
    const data = await apiGet('/v1/merchant/intel/overview?merchant_id=M_A&grid_load_pct=65');
    renderMerchantIntel(view, data);
  };
  root.querySelector('[data-v="cloud"]').onclick = async ()=>{
    const data = await apiGet('/v1/utility/behavior/cloud?utility_id=UT_TX&window=24h');
    renderBehaviorCloud(view, data);
  };
}
