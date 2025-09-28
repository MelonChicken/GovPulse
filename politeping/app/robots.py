import re, time
from typing import Dict, List, Tuple
from urllib.parse import urlparse
import httpx

_CACHE: Dict[str, Tuple[float, dict]] = {}
_TTL = 24 * 60 * 60  # seconds

def _rule_to_re(rule: str) -> re.Pattern:
    esc = re.escape(rule).replace("\\*", ".*")
    return re.compile(r"^" + esc)

def _longest_match(path: str, rules: List[str]) -> int:
    best = -1
    for r in rules:
        if _rule_to_re(r).search(path):
            best = max(best, len(r))
    return best

def _allowed(path: str, allows: List[str], disallows: List[str]) -> bool:
    a = _longest_match(path, allows)
    d = _longest_match(path, disallows)
    if a < 0 and d < 0: return True
    return a >= d

def _parse(txt: str) -> dict:
    allows, disallows = [], []
    in_star = False
    for line in txt.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line: continue
        k, v = [s.strip() for s in line.split(":", 1)]
        k = k.lower()
        if k == "user-agent":
            in_star = (v == "*")
        elif in_star and k in ("allow", "disallow"):
            if v: (allows if k == "allow" else disallows).append(v)
    return {"policy": "parsed", "allows": allows, "disallows": disallows}

async def check_robots_allow(client: httpx.AsyncClient, url: str) -> str:
    u = urlparse(url)
    host = u.netloc
    path = u.path or "/"

    now = time.time()
    cached = _CACHE.get(host)
    if cached and (now - cached[0] < _TTL):
        rb = cached[1]
    else:
        robots_url = f"{u.scheme}://{host}/robots.txt"
        try:
            r = await client.get(robots_url, timeout=3.0, follow_redirects=True)
            if r.status_code == 200:
                rb = _parse(r.text)
            elif r.status_code == 404:
                rb = {"policy": "allow", "allows": [], "disallows": []}
            else:
                rb = {"policy": "unknown", "allows": [], "disallows": []}
        except Exception:
            rb = {"policy": "unknown", "allows": [], "disallows": []}
        _CACHE[host] = (now, rb)

    policy = rb["policy"]
    if policy == "parsed":
        return "ALLOW" if _allowed(path, rb["allows"], rb["disallows"]) else "DISALLOW"
    if policy == "allow":
        return "ALLOW"
    if policy == "unknown":
        return "UNKNOWN"
    return "ALLOW"