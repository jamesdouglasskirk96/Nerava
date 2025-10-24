(function(){
  const API = (localStorage.NERAVA_URL || "http://127.0.0.1:8001");
  const KEY = (localStorage.DEMO_KEY || "demo_admin_key");
  let running = false;

  async function getJSON(path){
    const r = await fetch(API + path, {
      headers: { 'Accept':'application/json', 'Authorization': `Bearer ${KEY}` }
    });
    if(!r.ok) throw new Error(r.status+' '+path);
    return r.json();
  }

  async function postJSON(path, body){
    const r = await fetch(API + path, {
      method:'POST',
      headers: { 'Content-Type':'application/json', 'Authorization': `Bearer ${KEY}` },
      body: JSON.stringify(body||{})
    });
    if(!r.ok) throw new Error(r.status+' '+path);
    return r.json();
  }

  async function tick(){
    if(running) return;
    try{
      const s = await getJSON('/v1/demo/autorun');
      if(s && s.autorun && s.run_id && window.NeravaDemoRunner){
        running = true;
        await window.NeravaDemoRunner.runInvestorScript();
        await postJSON('/v1/demo/ack', { run_id: s.run_id });
      }
    }catch(e){ /* silent */ }
    finally{
      running = false;
      setTimeout(tick, 2000);
    }
  }
  setTimeout(tick, 1500);
})();
