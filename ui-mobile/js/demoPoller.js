// Demo poller disabled by default. Flip on with: localStorage.DEMO_POLL='on'
(function(){
  if (localStorage.DEMO_POLL !== 'on') return;
  // (Kept here for future: when enabled, it will poll same-origin with auth)
  let running=false, backoff=1000;
  const KEY=(localStorage.DEMO_KEY||"");
  const hdr=KEY?{'Accept':'application/json','Authorization':`Bearer ${KEY}`}:{'Accept':'application/json'};
  async function getJ(p){ const r=await fetch(p,{headers:hdr}); if(!r.ok) throw new Error('http '+r.status); return r.json(); }
  async function postJ(p,b){ const r=await fetch(p,{method:'POST',headers:{...hdr,'Content-Type':'application/json'},body:JSON.stringify(b||{})}); if(!r.ok) throw new Error('http '+r.status); return r.json(); }
  async function tick(){
    if(running) return;
    try{
      const s=await getJ('/v1/demo/autorun');
      if(s&&s.autorun&&s.run_id&&window.NeravaDemoRunner){
        running=true; await window.NeravaDemoRunner.runInvestorScript?.(); await postJ('/v1/demo/ack',{run_id:s.run_id});
      }
      backoff=1000;
    }catch(_){ backoff=Math.min(backoff*2,15000); }
    finally{ running=false; setTimeout(tick, backoff); }
  }
  setTimeout(tick, backoff);
})();