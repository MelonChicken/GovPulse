import asyncio, time
from typing import Dict, Any
from urllib.parse import urlparse
import httpx
from .config import settings
from .rate_limit import RateState
from .robots import check_robots_allow

def host_of(url: str) -> str:
    return urlparse(url).netloc

class Checker:
    def __init__(self, rate: RateState):
        self.rate = rate
        self.last_result: Dict[str, Dict[str, Any]] = {}

    async def _head_or_firstbyte(self, client: httpx.AsyncClient, url: str, robots_policy: str):
        started = time.monotonic()
        try:
            r = await client.request(
                "HEAD", url,
                headers={"User-Agent": settings.UA, "Accept": "text/html,*/*"},
                follow_redirects=True,
                timeout=httpx.Timeout(settings.TOTAL_TIMEOUT_S,
                                      connect=settings.CONNECT_TIMEOUT_S,
                                      read=settings.READ_TIMEOUT_S)
            )
            return r.status_code, (time.monotonic() - started), None
        except Exception as e:
            if robots_policy == "UNKNOWN":
                return None, 0.0, str(e)
            try:
                started2 = time.monotonic()
                async with client.stream(
                    "GET", url,
                    headers={"User-Agent": settings.UA, "Accept": "text/html,*/*"},
                    follow_redirects=True,
                    timeout=httpx.Timeout(settings.TOTAL_TIMEOUT_S,
                                          connect=settings.CONNECT_TIMEOUT_S,
                                          read=settings.READ_TIMEOUT_S)
                ) as r2:
                    async for _ in r2.aiter_bytes():
                        break
                return r2.status_code, (time.monotonic() - started2), None
            except Exception as e2:
                return None, 0.0, str(e2)

    async def check_one(self, client: httpx.AsyncClient, ep: Dict[str, Any]) -> Dict[str, Any]:
        h = host_of(ep["url"])
        ep_key = ep["url"]
        decision = await check_robots_allow(client, ep["url"])
        if decision == "DISALLOW":
            return {"name": ep["name"], "url": ep["url"], "http": None, "ttfb_ms": 0,
                    "outcome": "DISALLOWED", "error": None, "ts": time.time(), "robots": "parsed"}

        if not self.rate.allowed_now(h, ep_key, settings.HOST_MIN_INTERVAL_S, settings.EP_MIN_INTERVAL_S):
            prev = self.last_result.get(ep_key, {})
            return {
                "name": ep["name"], "url": ep["url"], "outcome": "SKIPPED", "skipped": True,
                "http": prev.get("http"), "ttfb_ms": prev.get("ttfb_ms", 0),
                "last_outcome": prev.get("outcome"), "last_ts": prev.get("ts"),
                "ts": time.time(), "robots": "allow"
            }

        async with self.rate.global_sem, self.rate.host_sems[h]:
            await asyncio.sleep(0.2)
            code, ttfb, err = await self._head_or_firstbyte(client, ep["url"], decision or "allow")
            self.rate.mark(h, ep_key)

        ttfb_ms = round(ttfb * 1000, 1)
        if code and 200 <= code < 400:
            outcome = "OK" if ttfb <= settings.TTFB_SLA_S else "UNSTABLE"
        elif code:
            outcome = "HTTP5xx" if code >= 500 else "HTTP4xx"
        else:
            outcome = "ERROR"

        res = {"name": ep["name"], "url": ep["url"], "http": code, "ttfb_ms": ttfb_ms,
               "outcome": outcome, "error": err, "ts": time.time(),
               "robots": (decision or "allow").lower()}
        self.last_result[ep_key] = res
        return res