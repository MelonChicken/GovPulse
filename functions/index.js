// Firebase Functions v2 — Functions only + robots.txt guard
const { onRequest } = require("firebase-functions/v2/https");
const express = require("express");

// ---------- 설정 ----------
const ENDPOINTS = [
  { name: "정부24 메인",          url: "https://www.gov.kr/" },
  { name: "K-ETA 메인",          url: "https://www.k-eta.go.kr/" },
  { name: "전자입국신고",        url: "https://www.e-arrivalcard.go.kr/" },
  { name: "국가법령정보센터",    url: "https://www.law.go.kr/" },
  { name: "우정사업본부",        url: "https://www.epost.go.kr/" },
  { name: "공공데이터포털",      url: "https://www.data.go.kr/" }
];

const UA                    = "GovPublicStatusMonitor/1.0 (+contact@example.com)"; // 연락 이메일로 교체
const TOTAL_TIMEOUT_MS      = 12000;
const READ_TIMEOUT_MS       = 8000;
const SLA_TTFB_MS           = 8000;
const HOST_MIN_INTERVAL_MS  = 60 * 1000;       // 도메인당 1분
const EP_MIN_INTERVAL_MS    = 10 * 60 * 1000;  // 엔드포인트당 10분
const ROBOTS_TTL_MS         = 24 * 60 * 60 * 1000; // 24시간

// ---------- 인스턴스 메모리(Functions 인스턴스별) ----------
const lastHostCheck = new Map();  // host -> ts
const lastEpCheck   = new Map();  // url  -> ts
const lastResult    = new Map();  // url  -> { 결과 }
const robotsCache   = new Map();  // host -> { ts, policy, allows, disallows }

// ---------- 유틸 ----------
function hostOf(u) { return new URL(u).host; }
function pathOf(u) { return new URL(u).pathname || "/"; }
function protoOf(u){ return new URL(u).protocol || "https:"; }
function nowMs()    { return Date.now(); }
function sleep(ms)  { return new Promise(r => setTimeout(r, ms)); }

function rateLimited(host, url) {
  const t = nowMs();
  const hostOk = t - (lastHostCheck.get(host) || 0) >= HOST_MIN_INTERVAL_MS;
  const epOk   = t - (lastEpCheck.get(url)   || 0) >= EP_MIN_INTERVAL_MS;
  return !(hostOk && epOk);
}

// ---------- robots.txt 가드 ----------
function normLine(s){ return s.split("#")[0].trim(); }
function isBlank(s){ return !s || /^\s*$/.test(s); }

function ruleToRegex(rule) {
  const esc = rule.replace(/[.+?^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*");
  return new RegExp("^" + esc);
}

function longestMatchLen(path, rules) {
  let best = -1;
  for (const r of rules) {
    const re = r._re || (r._re = ruleToRegex(r));
    if (re.test(path)) best = Math.max(best, r.length);
  }
  return best;
}

function allowedByRules(path, allows, disallows) {
  const allowLen = longestMatchLen(path, allows);
  const disLen   = longestMatchLen(path, disallows);
  if (allowLen < 0 && disLen < 0) return true;
  if (allowLen >= disLen) return true;
  return false;
}

function parseRobotsTxt(txt) {
  const lines = txt.split(/\r?\n/).map(normLine).filter(l => !isBlank(l));
  let curUA = null, inStar = false;
  const allows = [], disallows = [];

  for (const line of lines) {
    const i = line.indexOf(":");
    if (i < 0) continue;
    const k = line.slice(0, i).trim().toLowerCase();
    const v = line.slice(i + 1).trim();

    if (k === "user-agent") {
      curUA = v;
      inStar = (v === "*");
    } else if (inStar && (k === "disallow" || k === "allow")) {
      if (!isBlank(v)) (k === "disallow" ? disallows : allows).push(v);
    }
  }
  return { allows, disallows };
}

async function fetchRobots(host, protocol = "https:") {
  const cache = robotsCache.get(host);
  if (cache && (nowMs() - cache.ts) < ROBOTS_TTL_MS) return cache;

  const robotsUrl = `${protocol}//${host}/robots.txt`;
  let policy = "allow"; // 404면 허용, 200이면 parsed, 그 외 unknown
  let allows = [], disallows = [];

  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort("robots-timeout"), 3000);
    const res = await fetch(robotsUrl, {
      signal: controller.signal,
      redirect: "follow",
      headers: { "User-Agent": UA }
    });
    clearTimeout(timer);

    if (res.status === 200) {
      const text = await res.text();
      const parsed = parseRobotsTxt(text);
      allows = parsed.allows;
      disallows = parsed.disallows;
      policy = "parsed";
    } else if (res.status === 404) {
      policy = "allow";
    } else {
      policy = "unknown";
    }
  } catch {
    policy = "unknown";
  }

  const entry = { ts: nowMs(), policy, allows, disallows };
  robotsCache.set(host, entry);
  return entry;
}

async function checkRobotsGuard(url) {
  const host = hostOf(url), path = pathOf(url), proto = protoOf(url);
  const rb = await fetchRobots(host, proto);

  if (rb.policy === "parsed") {
    const ok = allowedByRules(path, rb.allows, rb.disallows);
    return { decision: ok ? "ALLOW" : "DISALLOW", policy: rb.policy };
  }
  if (rb.policy === "allow")   return { decision: "ALLOW", policy: rb.policy };
  if (rb.policy === "unknown") return { decision: "UNKNOWN", policy: rb.policy }; // 보수적(HEAD만)
  return { decision: "ALLOW", policy: "allow" };
}

// ---------- HTTP 요청 ----------
async function fetchWithTimeout(url, method) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort("total-timeout"), TOTAL_TIMEOUT_MS);

  try {
    const res = await fetch(url, {
      method,
      headers: { "User-Agent": UA, "Accept": "text/html,*/*" },
      redirect: "follow",
      signal: controller.signal
    });
    return res;
  } finally {
    clearTimeout(timer);
  }
}

async function headOrGetFirstByte(url, robotsPolicy = "allow") {
  const started = performance.now();

  try {
    const head = await fetchWithTimeout(url, "HEAD");
    const ttfb = performance.now() - started;
    return { code: head.status, ttfbMs: ttfb, method: "HEAD" };
  } catch (e) {
    if (robotsPolicy === "unknown") {
      return { code: null, ttfbMs: 0, err: String(e), method: "HEAD" };
    }

    const started2 = performance.now();
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort("read-timeout"), READ_TIMEOUT_MS);
      const res = await fetch(url, {
        method: "GET",
        headers: { "User-Agent": UA, "Accept": "text/html,*/*" },
        redirect: "follow",
        signal: controller.signal
      });

      const reader = res.body?.getReader?.();
      if (reader) await reader.read(); // 첫 청크만
      clearTimeout(timer);

      const ttfb = performance.now() - started2;
      return { code: res.status, ttfbMs: ttfb, method: "GET" };
    } catch (e2) {
      return { code: null, ttfbMs: 0, err: String(e2), method: "GET" };
    }
  }
}

// ---------- 체크 로직 ----------
async function checkOne(ep) {
  const tNow = nowMs();
  const host = hostOf(ep.url);
  const url  = ep.url;

  // robots 가드
  const rb = await checkRobotsGuard(url);
  if (rb.decision === "DISALLOW") {
    return {
      name: ep.name, url, http: null, ttfb_ms: 0,
      outcome: "DISALLOWED", error: null, ts: new Date(tNow).toISOString(),
      robots: rb.policy
    };
  }

  // 레이트 제한
  if (rateLimited(host, url)) {
    const prev = lastResult.get(url);
    return {
      name: ep.name, url, skipped: true, outcome: "SKIPPED",
      last_outcome: prev?.outcome, http: prev?.http ?? null,
      ttfb_ms: prev?.ttfb_ms ?? 0, last_ts: prev?.ts ?? null,
      ts: new Date(tNow).toISOString(),
      robots: rb.policy
    };
  }

  // 소량 지터
  await sleep(200);

  // 요청 수행(robots UNKNOWN이면 HEAD만)
  let outcome = "UNKNOWN", http = null, ttfbMs = 0, err = null;
  try {
    const r = await headOrGetFirstByte(url, rb.policy);
    http = r.code;
    ttfbMs = Math.round((r.ttfbMs || 0) * 10) / 10;

    if (http && http >= 200 && http < 400) {
      outcome = (ttfbMs <= SLA_TTFB_MS) ? "OK" : "UNSTABLE";
    } else if (http) {
      outcome = http >= 500 ? "HTTP5xx" : "HTTP4xx";
    } else {
      outcome = "ERROR";
      err = r.err || "unknown error";
    }
  } catch (e) {
    outcome = "ERROR";
    err = String(e);
  }

  lastHostCheck.set(host, nowMs());
  lastEpCheck.set(url, nowMs());

  const result = {
    name: ep.name, url, http, ttfb_ms: ttfbMs,
    outcome, error: err, ts: new Date().toISOString(), robots: rb.policy
  };
  lastResult.set(url, result);
  return result;
}

// ---------- Express 앱 ----------
const app = express();

app.get("/snapshot", async (_req, res) => {
  const out = [];
  // 저부하: 직렬 수행(엔드포인트가 많아지면 도메인별 큐/소규모 병렬 고려)
  for (const ep of ENDPOINTS) {
    out.push(await checkOne(ep));
  }

  res.set("Cache-Control", "public, max-age=60, s-maxage=60"); // 중복 호출 억제
  res.json(out);
});

app.get("/", (_req, res) => {
  res.type("html").send(`<!doctype html><meta charset="utf-8">
<title>PolitePing — Snapshot (Functions only)</title>
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
<p class="meta">Functions 단독. 도메인당 ≤1 req/min, 엔드포인트당 ≤1 req/10min. robots.txt Disallow는 요청하지 않고 DISALLOWED 처리.</p>
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
    div.innerHTML = \`
      <div style="display:flex;justify-content:space-between;align-items:center">
        <strong>\${x.name||'-'}</strong>
        <span class="badge \${cls}">\${outcome}</span>
      </div>
      <div class="url">\${x.url}</div>
      <div>HTTP: \${x.http??'-'} | TTFB: \${x.ttfb_ms||0} ms</div>
      <div class="meta">robots: \${x.robots||'-'}</div>
      <div style="color:#a33">\${x.error?('err: '+x.error):''}</div>
      \${x.skipped ? '<div class="meta">SKIPPED — last: '+(x.last_outcome||'-')+' @ '+(x.last_ts? new Date(x.last_ts).toLocaleString(): '-')+'</div>' : ''}
    \`;
    grid.appendChild(div);
  }
}
run(); setInterval(run, 60000);
</script>`);
});

// 서울 리전, 15초 타임아웃, CORS 허용
exports.app = onRequest({
  region: "asia-northeast3",
  timeoutSeconds: 15,
  cors: true
}, app);