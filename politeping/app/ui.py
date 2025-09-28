HTML = """<!doctype html><meta charset="utf-8">
<title>PolitePing — Snapshot</title>
<style>
body{font-family:sans-serif;margin:24px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}
.card{border:1px solid #ddd;border-radius:10px;padding:12px}
.badge{padding:2px 8px;border-radius:999px;font-size:12px}
.ok{background:#e6ffec}.unstable{background:#fff8e1}.err{background:#ffe6e6}.skip{background:#f2f2f2}.dis{background:#eee}
.url{color:#555;font-size:12px;word-break:break-all}
.meta{color:#666;font-size:12px}
</style>
<h1>PolitePing — Snapshot</h1>
<p class="meta">공개 .go.kr 대표 페이지만 저부하로 확인합니다. robots Disallow는 요청하지 않습니다.</p>
<button onclick="run()">지금 새로고침</button>
<div id="ts" class="meta"></div><div id="grid" class="grid"></div>
<script>
async function run(){
  const r = await fetch('/snapshot', {cache:'no-store'});
  const data = await r.json();
  document.getElementById('ts').textContent = 'Last update: '+ new Date().toLocaleString();
  const grid = document.getElementById('grid'); grid.innerHTML='';
  for (const x of data){
    const outcome=(x.outcome||'').toUpperCase();
    const cls= outcome==='OK'?'ok': (outcome==='UNSTABLE'?'unstable':(outcome==='SKIPPED'?'skip':(outcome==='DISALLOWED'?'dis':'err')));
    const div=document.createElement('div'); div.className='card';
    div.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center">
        <strong>${x.name||'-'}</strong>
        <span class="badge ${cls}">${outcome}</span>
      </div>
      <div class="url">${x.url}</div>
      <div>HTTP: ${x.http??'-'} | TTFB: ${x.ttfb_ms||0} ms</div>
      <div class="meta">robots: ${x.robots||'-'}</div>
      <div style="color:#a33">${x.error?('err: '+x.error):''}</div>
      ${x.skipped ? '<div class="meta">SKIPPED — last: '+(x.last_outcome||'-')+' @ '+(x.last_ts? new Date(x.last_ts*1000).toLocaleString(): '-')+'</div>' : ''}
    `;
    grid.appendChild(div);
  }
}
run(); setInterval(run, 60000);
</script>
"""