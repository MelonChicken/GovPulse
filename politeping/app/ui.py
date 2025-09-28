HTML = """<!doctype html><meta charset="utf-8">
<title>PolitePing — Snapshot</title>
<style>
body{font-family:sans-serif;margin:24px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}
.card{border:1px solid #ddd;border-radius:10px;padding:12px}
.badge{padding:2px 8px;border-radius:999px;font-size:12px}
.ok{background:#e6ffec}.unhealthy{background:#fff8e1}.err{background:#ffebe6}.dis{background:#eee}
.keyword-info{background:#f8f9fa;border:1px solid #e9ecef;border-radius:6px;padding:8px;margin-top:8px;font-size:11px;color:#495057}
.status-detail{margin-top:6px;font-size:11px;color:#6c757d}
.url{color:#555;font-size:12px;word-break:break-all}
.meta{color:#666;font-size:12px}
</style>
<h1>PolitePing — Snapshot</h1>
<p class="meta">공개 .go.kr 대표 페이지만 저부하로 확인합니다. robots Disallow는 요청하지 않습니다.<br>키워드 기반 장애 감지 기능이 포함되어 있습니다.</p>
<button onclick="run()">지금 새로고침</button>
<div id="ts" class="meta"></div><div id="grid" class="grid"></div>
<script>
async function run(){
  const r = await fetch('/snapshot', {cache:'no-store'});
  const data = await r.json();
  document.getElementById('ts').textContent = 'Last update: '+ new Date().toLocaleString();
  const grid = document.getElementById('grid'); grid.innerHTML='';
  for (const x of data){
    const outcome=(x.outcome||'').toLowerCase();
    const cls= outcome==='healthy'?'ok': (outcome==='unhealthy'?'unhealthy':(outcome==='disallowed'?'dis':'err'));

    // 상태 표현 개선
    let statusDisplay = outcome;
    if (outcome === 'unhealthy') {
      const keywords = x.matched_keywords || '';
      if (keywords.includes('CONTENT:') || keywords.includes('TITLE:')) {
        const keywordMatch = keywords.split(';')[0];
        const keywordText = keywordMatch.includes(':') ? keywordMatch.split(':')[1] : '';
        statusDisplay = `Unhealthy (HTTP ${x.http}, keyword="${keywordText}")`;
      } else {
        statusDisplay = `Unhealthy (HTTP ${x.http})`;
      }
    } else if (outcome === 'disallowed') {
      statusDisplay = '로봇 차단 (robots.txt)';
    }
    const div=document.createElement('div'); div.className='card';
    div.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center">
        <strong>${x.name||'-'}</strong>
        <span class="badge ${cls}">${statusDisplay}</span>
      </div>
      <div class="url">${x.url}</div>
      <div>HTTP: ${x.http??'-'} | TTFB: ${x.ttfb_ms||0} ms</div>
      <div class="meta">robots: ${x.robots||'-'}</div>
      ${x.title ? '<div class="meta">Title: ' + (x.title.length > 60 ? x.title.substring(0, 60) + '...' : x.title) + '</div>' : ''}
      <div style="color:#a33">${x.error?('err: '+x.error):''}</div>
      ${x.matched_keywords && x.matched_keywords !== '' ? '<div class="keyword-info">키워드 매칭: ' + x.matched_keywords.split(';').map(k => k.includes(':') ? k.split(':')[1] : k).join(', ') + '</div>' : ''}
    `;
    grid.appendChild(div);
  }
}
run(); setInterval(run, 60000);
</script>
"""