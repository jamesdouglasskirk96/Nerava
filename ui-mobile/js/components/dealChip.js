export function dealChip(deal){
  const root = document.createElement('div');
  root.className='deal-chip fade-up';
  const end = new Date(deal?.window?.end || Date.now()+60_000);
  const dollars = deal?.terms?.discount ?? 2;
  function tick(){
    const s = Math.max(0, Math.floor((end - Date.now())/1000));
    root.innerHTML = `<span>Green Hour — $${dollars} off</span><em>ends in ${s}s</em>`;
  }
  tick(); const id=setInterval(tick,1000);
  root.addEventListener('remove', ()=>clearInterval(id));
  return root;
}