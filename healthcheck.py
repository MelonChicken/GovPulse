#!/usr/bin/env python3
"""
Enhanced Health Check Script

개선 사항:
1. 상태 표현 개선: "Error" 대신 "Healthy/Unhealthy" 사용
2. 간소화된 판정 로직: HTTP 200 + 키워드 없음 → "Healthy", 그 외 → "Unhealthy"
3. UTC 타임스탬프 지원
4. 향상된 인코딩 처리 및 오류 복구
5. 기존 JSON 키워드 설정 완전 호환
6. requests 라이브러리만 사용

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
    with open(json_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Set default values with comprehensive fallbacks
    cfg.setdefault("global_keywords", [])
    cfg.setdefault("domains", {})
    cfg.setdefault("regex_keywords", [])
    cfg.setdefault("settings", {})

    s = cfg["settings"]
    s.setdefault("case_insensitive", True)
    s.setdefault("normalize_whitespace", True)
    s.setdefault("max_bytes_to_scan", 3_000_000)
    s.setdefault("timeout_seconds", 8)
    s.setdefault("retries", 1)
    s.setdefault("user_agent", "healthcheck-bot/1.0")
    s.setdefault("check_title", True)
    s.setdefault("text_mime_only", True)

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

def extract_title(html: str) -> str:
    """
    Extract HTML title for additional keyword checking.
    Addresses JS rendering issues by checking static title tags.
    """
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not title_match:
        return ""

    title = title_match.group(1)
    # Clean up title content
    title = re.sub(r"<[^>]+>", "", title)  # Remove any nested tags
    title = re.sub(r"\s+", " ", title).strip()
    return title

def get_text_and_meta(resp: requests.Response, max_bytes: int, cfg: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Extract and normalize text content with encoding fixes.

    ENCODING PROBLEM SOLUTION:
    - Uses apparent_encoding as fallback when encoding detection fails
    - Handles encoding mismatches that cause keyword matching failures
    """
    # CRITICAL FIX: Encoding detection and correction
    if not resp.encoding or resp.encoding == 'ISO-8859-1':
        # Fall back to apparent_encoding for better detection
        resp.encoding = resp.apparent_encoding or "utf-8"

    content_type = resp.headers.get("Content-Type", "").lower()

    # Get text content with size limit
    try:
        raw_text = resp.text
    except UnicodeDecodeError:
        # Last resort: force UTF-8 with error handling
        raw_text = resp.content.decode('utf-8', errors='ignore')

    if len(raw_text) > max_bytes:
        raw_text = raw_text[:max_bytes]

    # Extract title for additional checking
    title = extract_title(raw_text) if cfg["settings"].get("check_title", True) else ""

    # Normalize the full text content
    text_normalized = normalize_text(
        raw_text,
        cfg["settings"].get("case_insensitive", True),
        cfg["settings"].get("normalize_whitespace", True),
    )

    return text_normalized, title, content_type

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
    text_norm: str,
    title: str,
    plain_keywords: List[str],
    regex_patterns: List[Tuple[re.Pattern, str]],
    case_insensitive: bool
) -> List[str]:
    """
    NEGATIVE DETECTION: Find failure indicators in content.

    Checks both main content and title for comprehensive detection.
    Handles various keyword expressions and regex patterns.
    """
    matched = []

    # Prepare title for checking
    title_norm = ""
    if title:
        title_norm = normalize_text(title, case_insensitive, True)

    # Check plain text keywords
    for keyword in plain_keywords:
        if not keyword:
            continue

        keyword_norm = keyword.lower() if case_insensitive else keyword

        # Check in main content
        if keyword_norm in text_norm:
            matched.append(f"CONTENT:{keyword}")
            continue

        # Check in title
        if title_norm and keyword_norm in title_norm:
            matched.append(f"TITLE:{keyword}")

    # Check regex patterns
    for pattern, pattern_str in regex_patterns:
        # Check main content
        if pattern.search(text_norm):
            matched.append(f"REGEX_CONTENT:{pattern_str}")
            continue

        # Check title
        if title_norm and pattern.search(title_norm):
            matched.append(f"REGEX_TITLE:{pattern_str}")

    return matched

def sha256_of_text(s: str) -> str:
    """Generate SHA256 hash of text content for integrity verification"""
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()[:16]  # Shortened for readability

def health_check_url(url: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform comprehensive health check on a single URL.

    Returns detailed status information including matched keywords,
    response metadata, and content analysis.
    """
    failure_keywords_global = cfg.get("global_keywords", [])
    settings = cfg["settings"]

    case_insensitive = settings.get("case_insensitive", True)
    max_bytes = settings.get("max_bytes_to_scan", 3_000_000)
    timeout = settings.get("timeout_seconds", 8)
    retries = settings.get("retries", 1)
    user_agent = settings.get("user_agent", "healthcheck-bot/1.0")
    text_mime_only = settings.get("text_mime_only", True)

    # Use UTC timestamp as requested
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parsed = urlparse(url)
    domain = extract_domain(parsed.hostname or "")

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate"
    }

    last_exception = None

    # Retry logic for network resilience
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            status_code = response.status_code
            response_time_ms = int(response.elapsed.total_seconds() * 1000)

            # Check MIME type for text content (addresses JS rendering issues)
            content_type = response.headers.get("Content-Type", "").lower()
            if text_mime_only and not any(mime in content_type for mime in ["text/", "application/json", "application/xml"]):
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

            # Extract and normalize content
            text_normalized, title, content_type = get_text_and_meta(response, max_bytes, cfg)
            content_hash = sha256_of_text(text_normalized)

            # Simplified logic: HTTP 200 + no keywords → Healthy, everything else → Unhealthy
            if status_code != 200:
                result = "Unhealthy"
                matched_keywords = [f"HTTP_{status_code}"]
            else:
                # Comprehensive keyword matching for HTTP 200 responses
                domain_keywords = pick_domain_keywords(cfg, domain)
                all_plain_keywords = domain_keywords + failure_keywords_global
                regex_patterns = compile_regexes(cfg.get("regex_keywords", []), case_insensitive)

                matched_keywords = match_negative_keywords(
                    text_normalized, title, all_plain_keywords, regex_patterns, case_insensitive
                )

                result = "Unhealthy" if matched_keywords else "Healthy"

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

    # All retries failed - treat as Unhealthy with N/A status code
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

    Provides detailed analysis including keyword matches, content hashes,
    and response metadata for thorough monitoring.
    """
    cfg = load_keywords(cfg_path)

    # Deduplicate URLs while preserving order
    seen = set()
    unique_urls = [url for url in urls if url not in seen and not seen.add(url)]

    results = []
    total_urls = len(unique_urls)

    print(f"Starting health check for {total_urls} URLs...")
    print(f"Configuration: {cfg_path}")
    print("-" * 60)

    for i, url in enumerate(unique_urls, 1):
        print(f"[{i:2d}/{total_urls}] Checking: {url}")

        result = health_check_url(url, cfg)
        results.append(result)

        # Status display
        status_icon = {
            "Healthy": "[OK]",
            "Unhealthy": "[FAIL]"
        }.get(result['result'], "[UNKNOWN]")

        print(f"   {status_icon} {result['result']} (HTTP: {result['status_code']}) "
              f"[{result['response_time_ms']}ms]")

        if result['matched_keywords']:
            print(f"   Keywords: {result['matched_keywords']}")

        if result['title']:
            title_preview = result['title'][:50] + "..." if len(result['title']) > 50 else result['title']
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

    # Summary statistics
    healthy = sum(1 for r in results if r['result'] == 'Healthy')
    unhealthy = sum(1 for r in results if r['result'] == 'Unhealthy')

    print("-" * 60)
    print(f"Results Summary:")
    print(f"   Healthy: {healthy}")
    print(f"   Unhealthy: {unhealthy}")
    print(f"   Total: {len(results)}")
    print(f"   Saved to: {csv_filename}")

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