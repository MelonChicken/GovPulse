#!/usr/bin/env python3
"""
Enhanced Health Check Script - v2024.12

개선 사항:
1. 확장된 텍스트 검사: 본문 + title + meta + noscript 통합 분석
2. 간소화된 상태: Healthy/Unhealthy만 존재 (Error, SKIPPED 제거)
3. 강화된 probe 검사: 텍스트 길이, 구조적 완성도 확인
4. 추가 regex 패턴: 일반적인 장애 메시지 탐지
5. UTF-8 우선 인코딩 처리

사용법:
    python healthcheck.py [url_file.txt]
    python healthcheck.py  # 기본 테스트 URL 사용
"""

import requests
import csv
import datetime
import json
import re
import hashlib
import unicodedata
from urllib.parse import urlparse
from typing import List, Dict, Any, Tuple

def load_keywords(json_path: str) -> Dict[str, Any]:
    """Load and validate keywords configuration from JSON file"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        # 기본 설정 생성
        cfg = {
            "global_keywords": [
                "시스템 점검", "서비스 중단", "maintenance", "temporarily unavailable",
                "server error", "503 service", "502 bad gateway", "504 gateway timeout",
                "일시적으로 사용할 수 없습니다", "서비스 장애", "접속 불가"
            ],
            "domains": {},
            "regex_keywords": [
                {"pattern": r"(시스템\s*점검|서비스\s*중단|일시\s*중단)", "flags": "i"},
                {"pattern": r"(maintenance|temporarily\s*unavailable|service\s*unavailable)", "flags": "i"},
                {"pattern": r"(server\s*error|internal\s*error|50[0-9]\s*error)", "flags": "i"},
                {"pattern": r"(gateway\s*time\s*out|service\s*unavailable)", "flags": "i"},
                {"pattern": r"(access\s*denied|temporarily\s*unavailable|we\s*are\s*working\s*to\s*restore)", "flags": "i"}
            ],
            "settings": {
                "case_insensitive": True,
                "normalize_whitespace": True,
                "max_bytes_to_scan": 3000000,
                "timeout_seconds": 8,
                "retries": 1,
                "user_agent": "healthcheck-bot/1.0",
                "min_text_length": 100
            }
        }

    # Set default values with comprehensive fallbacks
    cfg.setdefault("global_keywords", [])
    cfg.setdefault("domains", {})
    cfg.setdefault("regex_keywords", [])
    cfg.setdefault("settings", {})

    s = cfg["settings"]
    s.setdefault("case_insensitive", True)
    s.setdefault("normalize_whitespace", True)
    s.setdefault("max_bytes_to_scan", 3000000)
    s.setdefault("timeout_seconds", 8)
    s.setdefault("retries", 1)
    s.setdefault("user_agent", "healthcheck-bot/1.0")
    s.setdefault("min_text_length", 100)

    return cfg

def extract_domain(host: str) -> str:
    """Extract and normalize domain from hostname"""
    return host.lower() if host else ""

def pick_domain_keywords(cfg: Dict[str, Any], domain: str) -> List[str]:
    """
    Select domain-specific keywords with wildcard support.
    Supports exact matches and wildcard patterns like *.go.kr
    """
    selected = []
    domains_cfg = cfg.get("domains", {})

    # Exact domain match
    if domain in domains_cfg:
        selected.extend(domains_cfg[domain])

    # Wildcard matching (*.go.kr matches any.go.kr)
    for pattern, keywords in domains_cfg.items():
        if pattern.startswith("*.") and domain.endswith(pattern[1:]):
            selected.extend(keywords)

    return selected

def normalize_text(s: str, case_insensitive: bool, normalize_ws: bool) -> str:
    """
    Advanced text normalization addressing encoding/spacing issues:
    - Unicode normalization (NFKC) for consistent character representation
    - Whitespace normalization to handle mixed spaces/newlines
    - Case normalization for case-insensitive matching
    """
    # Unicode normalization - converts similar characters to canonical form
    s = unicodedata.normalize("NFKC", s)

    # Whitespace normalization - collapse multiple whitespace to single space
    if normalize_ws:
        s = re.sub(r"\s+", " ", s).strip()

    # Case normalization
    if case_insensitive:
        s = s.lower()

    return s

def extract_comprehensive_text(html: str) -> Tuple[str, str, str, str]:
    """
    Extract comprehensive text from HTML including:
    - Title tag content
    - Meta description and og:* properties
    - Noscript content
    - Main body text
    """
    # Extract title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    title = ""
    if title_match:
        title = title_match.group(1)
        title = re.sub(r"<[^>]+>", "", title)  # Remove nested tags
        title = re.sub(r"\s+", " ", title).strip()

    # Extract meta description
    meta_desc = ""
    meta_desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html, re.IGNORECASE)
    if meta_desc_match:
        meta_desc = meta_desc_match.group(1)

    # Extract og:* meta properties
    og_metas = []
    og_matches = re.findall(r'<meta[^>]*property=["\']og:[^"\']*["\'][^>]*content=["\']([^"\']*)["\']', html, re.IGNORECASE)
    og_metas.extend(og_matches)

    # Also check reverse order (content first, then property)
    og_matches_rev = re.findall(r'<meta[^>]*content=["\']([^"\']*)["\'][^>]*property=["\']og:[^"\']*["\']', html, re.IGNORECASE)
    og_metas.extend(og_matches_rev)

    # Extract noscript content
    noscript_content = ""
    noscript_matches = re.findall(r"<noscript[^>]*>(.*?)</noscript>", html, flags=re.IGNORECASE | re.DOTALL)
    if noscript_matches:
        noscript_combined = " ".join(noscript_matches)
        # Remove HTML tags from noscript content
        noscript_content = re.sub(r"<[^>]+>", " ", noscript_combined)
        noscript_content = re.sub(r"\s+", " ", noscript_content).strip()

    # Combine all extracted text
    combined_parts = []
    if title:
        combined_parts.append(title)
    if meta_desc:
        combined_parts.append(meta_desc)
    if og_metas:
        combined_parts.extend(og_metas)
    if noscript_content:
        combined_parts.append(noscript_content)

    # Add main body (remove script and style tags first)
    body_text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.IGNORECASE | re.DOTALL)
    body_text = re.sub(r"<[^>]+>", " ", body_text)
    body_text = re.sub(r"\s+", " ", body_text).strip()
    combined_parts.append(body_text)

    comprehensive_text = " ".join(combined_parts)

    return comprehensive_text, title, meta_desc, noscript_content

def get_comprehensive_content(resp: requests.Response, max_bytes: int, cfg: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
    """
    Extract comprehensive content with improved encoding handling.
    Returns: (comprehensive_text, title, meta_desc, noscript, content_type)
    """
    # Enhanced encoding detection - prioritize UTF-8
    if not resp.encoding or resp.encoding == 'ISO-8859-1':
        # Check if content looks like UTF-8
        try:
            resp.content.decode('utf-8')
            resp.encoding = 'utf-8'
        except UnicodeDecodeError:
            # Fall back to apparent_encoding
            resp.encoding = resp.apparent_encoding or "utf-8"

    content_type = resp.headers.get("Content-Type", "").lower()

    # Get text content with size limit
    try:
        raw_html = resp.text
    except UnicodeDecodeError:
        # Last resort: force UTF-8 with error handling
        raw_html = resp.content.decode('utf-8', errors='ignore')

    if len(raw_html) > max_bytes:
        raw_html = raw_html[:max_bytes]

    # Extract comprehensive text content
    comprehensive_text, title, meta_desc, noscript = extract_comprehensive_text(raw_html)

    # Normalize the comprehensive text
    comprehensive_normalized = normalize_text(
        comprehensive_text,
        cfg["settings"].get("case_insensitive", True),
        cfg["settings"].get("normalize_whitespace", True),
    )

    return comprehensive_normalized, title, meta_desc, noscript, content_type

def compile_regexes(regex_cfg: List[Dict[str, str]], case_insensitive_default: bool) -> List[Tuple[re.Pattern, str]]:
    """
    Compile regex patterns with proper flag handling.
    Returns list of (compiled_pattern, original_pattern_string) tuples.
    """
    patterns = []
    for item in regex_cfg:
        pattern_str = item.get("pattern", "")
        flags_str = item.get("flags", "")

        flag_val = 0
        if "i" in flags_str or case_insensitive_default:
            flag_val |= re.IGNORECASE
        if "m" in flags_str:
            flag_val |= re.MULTILINE
        if "s" in flags_str:
            flag_val |= re.DOTALL

        try:
            compiled_pattern = re.compile(pattern_str, flags=flag_val)
            patterns.append((compiled_pattern, pattern_str))
        except re.error as e:
            print(f"Warning: Invalid regex pattern '{pattern_str}': {e}")
            continue

    return patterns

def match_negative_keywords(
    comprehensive_text: str,
    plain_keywords: List[str],
    regex_patterns: List[Tuple[re.Pattern, str]],
    case_insensitive: bool
) -> List[str]:
    """
    NEGATIVE DETECTION: Find failure indicators in comprehensive content.
    Checks the combined text from all sources.
    """
    matched = []

    # Check plain text keywords
    for keyword in plain_keywords:
        if not keyword:
            continue

        keyword_norm = keyword.lower() if case_insensitive else keyword

        if keyword_norm in comprehensive_text:
            matched.append(f"KEYWORD:{keyword}")

    # Check regex patterns
    for pattern, pattern_str in regex_patterns:
        if pattern.search(comprehensive_text):
            matched.append(f"REGEX:{pattern_str}")

    return matched

def perform_content_probe(comprehensive_text: str, title: str, min_length: int) -> Tuple[bool, List[str]]:
    """
    Perform comprehensive content probes to detect incomplete/error pages.
    Returns: (is_healthy, issues_found)
    """
    issues = []

    # Text length probe
    if len(comprehensive_text) < min_length:
        issues.append(f"SHORT_CONTENT:{len(comprehensive_text)}")

    # Title probe
    if not title or len(title.strip()) == 0:
        issues.append("NO_TITLE")

    # Basic structure probe - check for common HTML elements
    if comprehensive_text:
        # Very basic check - if we have some reasonable amount of text, consider it structured
        word_count = len(comprehensive_text.split())
        if word_count < 10:
            issues.append(f"FEW_WORDS:{word_count}")

    # JavaScript error probe
    js_error_patterns = [
        r"javascript\s*error",
        r"uncaught\s*exception",
        r"syntax\s*error",
        r"reference\s*error"
    ]

    for pattern in js_error_patterns:
        if re.search(pattern, comprehensive_text, re.IGNORECASE):
            issues.append(f"JS_ERROR:{pattern}")

    return len(issues) == 0, issues

def sha256_of_text(s: str) -> str:
    """Generate SHA256 hash of text content for integrity verification"""
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()[:16]

def health_check_url(url: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform comprehensive health check on a single URL.

    Logic: HTTP 200 + no negative keywords + sufficient content + probes pass → Healthy
           Everything else → Unhealthy
    """
    failure_keywords_global = cfg.get("global_keywords", [])
    settings = cfg["settings"]

    case_insensitive = settings.get("case_insensitive", True)
    max_bytes = settings.get("max_bytes_to_scan", 3000000)
    timeout = settings.get("timeout_seconds", 8)
    retries = settings.get("retries", 1)
    user_agent = settings.get("user_agent", "healthcheck-bot/1.0")
    min_text_length = settings.get("min_text_length", 100)

    # Use UTC timestamp
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parsed = urlparse(url)
    domain = extract_domain(parsed.hostname or "")

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Charset": "utf-8, iso-8859-1;q=0.5"
    }

    last_exception = None

    # Retry logic for network resilience
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            status_code = response.status_code
            response_time_ms = int(response.elapsed.total_seconds() * 1000)

            # Check MIME type for text content
            content_type = response.headers.get("Content-Type", "").lower()
            if not any(mime in content_type for mime in ["text/", "application/json", "application/xml"]):
                return {
                    "timestamp": timestamp,
                    "url": url,
                    "domain": domain,
                    "status_code": status_code,
                    "result": "Unhealthy",
                    "response_time_ms": response_time_ms,
                    "content_type": content_type,
                    "matched_keywords": "BINARY_CONTENT",
                    "title": "",
                    "content_sha256": "",
                    "error": "Non-text content type"
                }

            # Extract comprehensive content
            comprehensive_text, title, meta_desc, noscript, content_type = get_comprehensive_content(response, max_bytes, cfg)
            content_hash = sha256_of_text(comprehensive_text)

            # Health determination logic
            if status_code != 200:
                result = "Unhealthy"
                matched_keywords = [f"HTTP_{status_code}"]
            else:
                # Check negative keywords in comprehensive text
                domain_keywords = pick_domain_keywords(cfg, domain)
                all_plain_keywords = domain_keywords + failure_keywords_global
                regex_patterns = compile_regexes(cfg.get("regex_keywords", []), case_insensitive)

                matched_keywords = match_negative_keywords(
                    comprehensive_text, all_plain_keywords, regex_patterns, case_insensitive
                )

                # Perform content probes
                probe_healthy, probe_issues = perform_content_probe(comprehensive_text, title, min_text_length)

                if not probe_healthy:
                    matched_keywords.extend(probe_issues)

                # Final determination: Healthy only if no keywords matched AND probes passed
                result = "Healthy" if (not matched_keywords and probe_healthy) else "Unhealthy"

            return {
                "timestamp": timestamp,
                "url": url,
                "domain": domain,
                "status_code": status_code,
                "result": result,
                "response_time_ms": response_time_ms,
                "content_type": content_type,
                "matched_keywords": ";".join(matched_keywords),
                "title": title,
                "content_sha256": content_hash,
                "error": None
            }

        except requests.exceptions.Timeout:
            last_exception = "Request timeout"
        except requests.exceptions.ConnectionError as e:
            last_exception = f"Connection error: {str(e)}"
        except requests.exceptions.RequestException as e:
            last_exception = f"Request failed: {str(e)}"
        except Exception as e:
            last_exception = f"Unexpected error: {str(e)}"

    # All retries failed - always Unhealthy
    return {
        "timestamp": timestamp,
        "url": url,
        "domain": domain,
        "status_code": "N/A",
        "result": "Unhealthy",
        "response_time_ms": -1,
        "content_type": "",
        "matched_keywords": f"CONNECTION_ERROR:{last_exception}",
        "title": "",
        "content_sha256": "",
        "error": last_exception
    }

def check_multiple_urls(urls: List[str], cfg_path: str, csv_filename: str = "health_check_ultimate.csv") -> List[Dict[str, Any]]:
    """
    Check multiple URLs and save comprehensive results to CSV.
    Only reports Healthy/Unhealthy states - no other status values.
    """
    cfg = load_keywords(cfg_path)

    # Deduplicate URLs while preserving order
    seen = set()
    unique_urls = [url for url in urls if url not in seen and not seen.add(url)]

    results = []
    total_urls = len(unique_urls)

    print(f"Starting enhanced health check for {total_urls} URLs...")
    print(f"Configuration: {cfg_path}")
    print("Enhanced features: comprehensive text analysis, content probes, UTF-8 priority")
    print("-" * 70)

    for i, url in enumerate(unique_urls, 1):
        print(f"[{i:2d}/{total_urls}] Checking: {url}")

        result = health_check_url(url, cfg)
        results.append(result)

        # Status display - only Healthy/Unhealthy
        status_icon = "✓ [OK]" if result['result'] == "Healthy" else "✗ [FAIL]"

        print(f"   {status_icon} {result['result']} (HTTP: {result['status_code']}) "
              f"[{result['response_time_ms']}ms]")

        if result['matched_keywords']:
            keywords_preview = result['matched_keywords'][:80] + "..." if len(result['matched_keywords']) > 80 else result['matched_keywords']
            print(f"   Issues: {keywords_preview}")

        if result['title']:
            title_preview = result['title'][:60] + "..." if len(result['title']) > 60 else result['title']
            print(f"   Title: {title_preview}")

    # Save detailed results to CSV
    fieldnames = [
        "timestamp", "url", "domain", "status_code", "result",
        "response_time_ms", "content_type", "matched_keywords",
        "title", "content_sha256", "error"
    ]

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Summary statistics - only Healthy/Unhealthy
    healthy = sum(1 for r in results if r['result'] == 'Healthy')
    unhealthy = sum(1 for r in results if r['result'] == 'Unhealthy')

    print("-" * 70)
    print(f"Results Summary:")
    print(f"   ✓ Healthy: {healthy}")
    print(f"   ✗ Unhealthy: {unhealthy}")
    print(f"   📊 Total: {len(results)}")
    print(f"   💾 Saved to: {csv_filename}")

    return results

def load_urls_from_file(filename: str) -> List[str]:
    """Load URLs from a text file, one per line"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return urls
    except FileNotFoundError:
        print(f"Error: URL file '{filename}' not found")
        return []

if __name__ == "__main__":
    import sys

    # Example usage with multiple input methods
    if len(sys.argv) > 1:
        # Load URLs from file
        url_file = sys.argv[1]
        urls = load_urls_from_file(url_file)
        if not urls:
            print("No valid URLs found in file")
            sys.exit(1)
    else:
        # Default test URLs
        urls = [
            "https://www.law.go.kr",
            "https://www.google.com",
            "https://httpbin.org/status/503",  # Test failure detection
            "https://httpbin.org/html",       # Test success detection
        ]

    # Run comprehensive health check
    results = check_multiple_urls(
        urls,
        cfg_path="keywords.json",
        csv_filename="health_check_ultimate.csv"
    )