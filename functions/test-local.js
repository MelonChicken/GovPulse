// Simple local test for the Firebase Functions logic
// Run with: node test-local.js

// Simulate the core logic without Firebase Functions wrapper
const ENDPOINTS = [
  { name: "정부24 메인", url: "https://www.gov.kr/" },
  { name: "공공데이터포털", url: "https://www.data.go.kr/" }
];

const UA = "GovPublicStatusMonitor/1.0 (+test@example.com)";
const TOTAL_TIMEOUT_MS = 12000;
const ROBOTS_TTL_MS = 24 * 60 * 60 * 1000;

const robotsCache = new Map();
const lastHostCheck = new Map();
const lastEpCheck = new Map();
const lastResult = new Map();

function hostOf(u) { return new URL(u).host; }
function pathOf(u) { return new URL(u).pathname || "/"; }
function protoOf(u) { return new URL(u).protocol || "https:"; }
function nowMs() { return Date.now(); }

function parseRobotsTxt(txt) {
  const lines = txt.split(/\r?\n/)
    .map(s => s.split("#")[0].trim())
    .filter(l => l && !/^\s*$/.test(l));

  let inStar = false;
  const allows = [], disallows = [];

  for (const line of lines) {
    const i = line.indexOf(":");
    if (i < 0) continue;
    const k = line.slice(0, i).trim().toLowerCase();
    const v = line.slice(i + 1).trim();

    if (k === "user-agent") {
      inStar = (v === "*");
    } else if (inStar && (k === "disallow" || k === "allow")) {
      if (v) (k === "disallow" ? disallows : allows).push(v);
    }
  }
  return { allows, disallows };
}

async function fetchRobots(host, protocol = "https:") {
  const cache = robotsCache.get(host);
  if (cache && (nowMs() - cache.ts) < ROBOTS_TTL_MS) return cache;

  const robotsUrl = `${protocol}//${host}/robots.txt`;
  let policy = "allow";
  let allows = [], disallows = [];

  try {
    console.log(`Fetching robots.txt: ${robotsUrl}`);
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
      console.log(`Robots.txt parsed for ${host}: ${disallows.length} disallow rules`);
    } else if (res.status === 404) {
      policy = "allow";
      console.log(`No robots.txt for ${host} (404)`);
    } else {
      policy = "unknown";
      console.log(`Unknown robots.txt status for ${host}: ${res.status}`);
    }
  } catch (e) {
    policy = "unknown";
    console.log(`Error fetching robots.txt for ${host}: ${e.message}`);
  }

  const entry = { ts: nowMs(), policy, allows, disallows };
  robotsCache.set(host, entry);
  return entry;
}

async function testEndpoint(ep) {
  console.log(`\nTesting: ${ep.name} (${ep.url})`);

  const host = hostOf(ep.url);
  const path = pathOf(ep.url);

  // Test robots.txt check
  const rb = await fetchRobots(host);
  console.log(`Robots policy: ${rb.policy}`);

  if (rb.policy === "parsed" && rb.disallows.length > 0) {
    console.log(`Disallow rules: ${rb.disallows.join(", ")}`);
    // Simple check if path matches any disallow rule
    const blocked = rb.disallows.some(rule => path.startsWith(rule));
    if (blocked) {
      console.log(`❌ DISALLOWED by robots.txt`);
      return;
    }
  }

  console.log(`✅ Allowed by robots.txt`);

  // Test actual HTTP request
  try {
    const startTime = performance.now();
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort("timeout"), TOTAL_TIMEOUT_MS);

    const response = await fetch(ep.url, {
      method: "HEAD",
      headers: { "User-Agent": UA },
      signal: controller.signal,
      redirect: "follow"
    });

    clearTimeout(timer);
    const ttfb = performance.now() - startTime;

    console.log(`📡 HEAD ${response.status} - TTFB: ${Math.round(ttfb)}ms`);

  } catch (e) {
    console.log(`❌ Request failed: ${e.message}`);
  }
}

async function main() {
  console.log("🚀 Testing Firebase Functions logic locally\n");

  for (const ep of ENDPOINTS) {
    await testEndpoint(ep);
    await new Promise(r => setTimeout(r, 1000)); // 1초 대기
  }

  console.log("\n✅ Local test completed");
}

main().catch(console.error);