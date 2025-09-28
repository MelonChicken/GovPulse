import asyncio, time, json, re, hashlib, unicodedata
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse
import httpx
from .config import settings
from .rate_limit import RateState
from .robots import check_robots_allow

def host_of(url: str) -> str:
    return urlparse(url).netloc

class Checker:
    def __init__(self, rate: RateState, keywords_path: str = "keywords.json"):
        self.rate = rate
        self.last_result: Dict[str, Dict[str, Any]] = {}
        self.keywords_cfg = self._load_keywords(keywords_path)

    def _load_keywords(self, json_path: str) -> Dict[str, Any]:
        """JSON 설정 파일에서 키워드 로드"""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except FileNotFoundError:
            # 기본 설정
            cfg = {
                "global_keywords": [
                    "시스템 점검", "서비스 중단", "maintenance", "temporarily unavailable",
                    "server error", "503 service", "502 bad gateway", "504 gateway timeout"
                ],
                "domains": {},
                "regex_keywords": [],
                "settings": {
                    "case_insensitive": True,
                    "normalize_whitespace": True,
                    "max_bytes_to_scan": 3000000
                }
            }

        # 기본값 설정
        cfg.setdefault("global_keywords", [])
        cfg.setdefault("domains", {})
        cfg.setdefault("regex_keywords", [])
        cfg.setdefault("settings", {})

        return cfg

    def _extract_domain(self, url: str) -> str:
        """도메인 추출"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower() if parsed.netloc else ""
        except:
            return ""

    def _get_domain_keywords(self, domain: str) -> List[str]:
        """도메인별 키워드 선택 (와일드카드 지원)"""
        keywords = []
        domains_cfg = self.keywords_cfg.get("domains", {})

        # 정확한 도메인 매치
        if domain in domains_cfg:
            keywords.extend(domains_cfg[domain])

        # 와일드카드 매치 (*.go.kr 형태)
        for pattern, kw_list in domains_cfg.items():
            if pattern.startswith("*.") and domain.endswith(pattern[1:]):
                keywords.extend(kw_list)

        return keywords

    def _normalize_text(self, text: str) -> str:
        """텍스트 정규화"""
        settings = self.keywords_cfg.get("settings", {})
        case_insensitive = settings.get("case_insensitive", True)
        normalize_ws = settings.get("normalize_whitespace", True)

        # 유니코드 정규화
        text = unicodedata.normalize("NFKC", text)

        # 공백 정규화
        if normalize_ws:
            text = re.sub(r"\s+", " ", text).strip()

        # 대소문자 정규화
        if case_insensitive:
            text = text.lower()

        return text

    def _extract_title(self, html: str) -> str:
        """HTML title 태그 추출"""
        try:
            title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
            if title_match:
                title = title_match.group(1)
                # HTML 태그 제거
                title = re.sub(r"<[^>]+>", "", title)
                title = re.sub(r"\s+", " ", title).strip()
                return title
        except:
            pass
        return ""

    def _compile_regex_patterns(self) -> List[Tuple[re.Pattern, str]]:
        """정규식 패턴 컴파일"""
        patterns = []
        case_insensitive = self.keywords_cfg.get("settings", {}).get("case_insensitive", True)

        for item in self.keywords_cfg.get("regex_keywords", []):
            pattern_str = item.get("pattern", "")
            flags_str = item.get("flags", "")

            flag_val = 0
            if "i" in flags_str or case_insensitive:
                flag_val |= re.IGNORECASE
            if "m" in flags_str:
                flag_val |= re.MULTILINE
            if "s" in flags_str:
                flag_val |= re.DOTALL

            try:
                compiled_pattern = re.compile(pattern_str, flags=flag_val)
                patterns.append((compiled_pattern, pattern_str))
            except re.error:
                continue

        return patterns

    def _check_negative_keywords(self, content: str, title: str, domain: str) -> List[str]:
        """부정 키워드 검사"""
        matched = []
        case_insensitive = self.keywords_cfg.get("settings", {}).get("case_insensitive", True)

        # 텍스트 정규화
        content_norm = self._normalize_text(content)
        title_norm = self._normalize_text(title) if title else ""

        # 키워드 수집
        global_keywords = self.keywords_cfg.get("global_keywords", [])
        domain_keywords = self._get_domain_keywords(domain)
        all_keywords = global_keywords + domain_keywords

        # 일반 키워드 검사
        for keyword in all_keywords:
            if not keyword:
                continue

            keyword_norm = keyword.lower() if case_insensitive else keyword

            if keyword_norm in content_norm:
                matched.append(f"CONTENT:{keyword}")
            elif title_norm and keyword_norm in title_norm:
                matched.append(f"TITLE:{keyword}")

        # 정규식 패턴 검사
        regex_patterns = self._compile_regex_patterns()
        for pattern, pattern_str in regex_patterns:
            if pattern.search(content_norm):
                matched.append(f"REGEX_CONTENT:{pattern_str}")
            elif title_norm and pattern.search(title_norm):
                matched.append(f"REGEX_TITLE:{pattern_str}")

        return matched

    async def _get_content_for_analysis(self, client: httpx.AsyncClient, url: str) -> Tuple[int, float, str, str, str]:
        """콘텐츠 분석을 위한 GET 요청"""
        started = time.monotonic()
        try:
            response = await client.get(
                url,
                headers={"User-Agent": settings.UA, "Accept": "text/html,*/*"},
                follow_redirects=True,
                timeout=httpx.Timeout(settings.TOTAL_TIMEOUT_S,
                                      connect=settings.CONNECT_TIMEOUT_S,
                                      read=settings.READ_TIMEOUT_S)
            )

            ttfb = time.monotonic() - started

            # 콘텐츠 추출 (최대 3MB)
            max_bytes = self.keywords_cfg.get("settings", {}).get("max_bytes_to_scan", 3000000)

            try:
                # 인코딩 자동 감지 및 수정
                if not response.encoding or response.encoding == 'ISO-8859-1':
                    response.encoding = 'utf-8'

                content = response.text
            except UnicodeDecodeError:
                content = response.content.decode('utf-8', errors='ignore')

            if len(content) > max_bytes:
                content = content[:max_bytes]

            title = self._extract_title(content)
            content_hash = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()[:16]

            return response.status_code, ttfb, content, title, content_hash

        except Exception as e:
            return None, 0.0, "", "", ""

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

        # 콘텐츠 분석을 위한 추가 요청 (기본 HEAD/GET이 성공하고 200 OK인 경우)
        matched_keywords = []
        title = ""
        content_hash = ""

        if code == 200:
            # 콘텐츠 분석을 위한 GET 요청
            domain = self._extract_domain(ep["url"])
            status_code_content, ttfb_content, content, title, content_hash = await self._get_content_for_analysis(client, ep["url"])

            if content:
                matched_keywords = self._check_negative_keywords(content, title, domain)

        # 결과 판정
        if code and 200 <= code < 400:
            if matched_keywords:
                outcome = "UNHEALTHY"
            else:
                outcome = "OK" if ttfb <= settings.TTFB_SLA_S else "UNSTABLE"
        elif code:
            outcome = "HTTP5xx" if code >= 500 else "HTTP4xx"
            matched_keywords = [f"HTTP_{code}"]
        else:
            outcome = "ERROR"
            matched_keywords = ["CONNECTION_ERROR"]

        res = {"name": ep["name"], "url": ep["url"], "http": code, "ttfb_ms": ttfb_ms,
               "outcome": outcome, "error": err, "ts": time.time(),
               "robots": (decision or "allow").lower(),
               "matched_keywords": ";".join(matched_keywords),
               "title": title,
               "content_sha256": content_hash}
        self.last_result[ep_key] = res
        return res