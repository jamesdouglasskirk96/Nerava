export function dealChip(deal){
  const root = document.createElement('div');
  root.className='deal-chip';
  const end = new Date(deal.window?.end || Date.now());
  function tick(){
    const s = Math.max(0, Math.floor((end - Date.now())/1000));
    root.innerHTML = `<span>$${deal.terms?.discount || 2} ${deal.terms?.label||'Green Hour'}</span><em>${s}s left</em>`;
  }
  tick(); const id=setInterval(tick,1000);
  root.onremove = ()=>clearInterval(id);
  return root;
}
