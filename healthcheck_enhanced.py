#!/usr/bin/env python3
"""
Enhanced Health Check Script with Advanced Text Processing

Improvements:
- Advanced encoding detection with apparent_encoding fallback
- Unicode normalization (NFKC) and whitespace normalization
- Better keyword matching with text preprocessing
- Content SHA256 hashing for integrity verification
- Configurable retry logic and timeouts
- Enhanced error handling and reporting
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

    # Set default values
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

    return cfg

def extract_domain(host: str) -> str:
    """Extract and normalize domain from hostname"""
    return host.lower() if host else ""

def pick_domain_keywords(cfg: Dict[str, Any], domain: str) -> List[str]:
    """
    Select applicable keywords for domain with priority:
    1. Exact domain match
    2. Wildcard pattern match (*.go.kr)
    """
    selected = []
    domains_cfg = cfg.get("domains", {})

    # Exact domain match
    if domain in domains_cfg:
        selected.extend(domains_cfg[domain])
        return selected  # Use exact match only

    # Wildcard matching
    for pattern, keywords in domains_cfg.items():
        if pattern.startswith("*.") and domain.endswith(pattern[1:]):  # "*.go.kr" -> ".go.kr"
            selected.extend(keywords)
            return selected  # Use wildcard match only

    return selected

def normalize_text(s: str, case_insensitive: bool, normalize_ws: bool) -> str:
    """
    Normalize text for better keyword matching:
    - Unicode normalization (NFKC)
    - Whitespace normalization
    - Case normalization
    """
    # Unicode normalization
    s = unicodedata.normalize("NFKC", s)

    # Whitespace normalization
    if normalize_ws:
        s = re.sub(r"\s+", " ", s)

    # Case normalization
    if case_insensitive:
        s = s.lower()

    return s

def extract_title(html: str) -> str:
    """Extract title from HTML content with improved parsing"""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return ""

    title = m.group(1)
    # Clean up title
    title = re.sub(r"\s+", " ", title).strip()
    return title[:200]  # Limit title length

def get_text_and_meta(resp: requests.Response, max_bytes: int, cfg: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Extract and normalize text content with proper encoding detection
    """
    # Fix encoding detection issue
    if not resp.encoding:
        resp.encoding = resp.apparent_encoding or "utf-8"

    content_type = resp.headers.get("Content-Type", "")

    # Get text content with size limit
    raw = resp.text
    if len(raw) > max_bytes:
        raw = raw[:max_bytes]

    # Extract title
    title = extract_title(raw)

    # Normalize text for keyword matching
    text_norm = normalize_text(
        raw,
        cfg["settings"].get("case_insensitive", True),
        cfg["settings"].get("normalize_whitespace", True),
    )

    return text_norm, title, content_type

def compile_regexes(regex_cfg: List[Dict[str, str]], case_insensitive_default: bool) -> List[re.Pattern]:
    """Compile regex patterns with proper flags"""
    patterns = []
    for item in regex_cfg:
        pat = item.get("pattern", "")
        flags = item.get("flags", "")
        flag_val = 0

        if "i" in flags or case_insensitive_default:
            flag_val |= re.IGNORECASE

        try:
            patterns.append(re.compile(pat, flags=flag_val))
        except re.error as e:
            print(f"Warning: Invalid regex pattern '{pat}': {e}")

    return patterns

def match_negative(text_norm: str, plain_keywords: List[str], regex_patterns: List[re.Pattern], case_insensitive: bool) -> List[str]:
    """
    Perform negative keyword matching (find unwanted keywords)
    Returns list of matched keywords
    """
    matched = []

    # Check string keywords
    for kw in plain_keywords:
        if not kw:
            continue

        kw_cmp = kw.lower() if case_insensitive else kw

        if kw_cmp in text_norm:
            matched.append(kw)

    # Check regex patterns
    for rp in regex_patterns:
        if rp.search(text_norm):
            matched.append(f"REGEX:{rp.pattern}")

    return matched

def sha256_of_text(s: str) -> str:
    """Generate SHA256 hash of text content for integrity verification"""
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()

def health_check_url(url: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform enhanced health check on a single URL
    """
    settings = cfg["settings"]
    failure_keywords_global = cfg.get("global_keywords", [])
    case_insensitive = settings.get("case_insensitive", True)
    max_bytes = settings.get("max_bytes_to_scan", 3_000_000)
    timeout = settings.get("timeout_seconds", 8)
    retries = settings.get("retries", 1)
    ua = settings.get("user_agent", "healthcheck-bot/1.0")

    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    parsed = urlparse(url)
    domain = extract_domain(parsed.hostname or "")

    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    last_exc = None

    # Retry logic
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            status_code = resp.status_code

            # Extract and normalize content
            text_norm, title, content_type = get_text_and_meta(resp, max_bytes, cfg)
            content_hash = sha256_of_text(text_norm)

            if status_code != 200:
                result = "Error"
                matched = []
            else:
                # Combine keywords: domain-specific + global + regex
                domain_kws = pick_domain_keywords(cfg, domain)
                plain_kws = domain_kws + failure_keywords_global
                regex_patterns = compile_regexes(cfg.get("regex_keywords", []), case_insensitive)

                # Perform negative matching
                matched = match_negative(text_norm, plain_kws, regex_patterns, case_insensitive)
                result = "Unhealthy" if matched else "Healthy"

            return {
                "timestamp": timestamp,
                "url": url,
                "domain": domain,
                "status_code": status_code,
                "result": result,
                "response_time_ms": int(resp.elapsed.total_seconds() * 1000),
                "content_type": content_type,
                "matched_keywords": ";".join(matched),
                "title": title,
                "content_sha256": content_hash,
                "error_message": ""
            }

        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.RequestException) as e:
            last_exc = e
            if attempt < retries:
                print(f"  Attempt {attempt + 1} failed, retrying...")
                continue

    # All attempts failed
    return {
        "timestamp": timestamp,
        "url": url,
        "domain": domain,
        "status_code": "N/A",
        "result": "Error",
        "response_time_ms": -1,
        "content_type": "",
        "matched_keywords": "",
        "title": "",
        "content_sha256": "",
        "error_message": str(last_exc) if last_exc else "Unknown error"
    }

def check_multiple_urls(urls: List[str], cfg_path: str, csv_filename: str = "health_check_results.csv"):
    """
    Check multiple URLs with enhanced error handling and deduplication
    """
    cfg = load_keywords(cfg_path)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = [u for u in urls if u not in seen and not seen.add(u)]

    results = []

    print(f"Starting health check for {len(unique_urls)} unique URLs...")
    print("-" * 60)

    for i, url in enumerate(unique_urls, 1):
        print(f"[{i}/{len(unique_urls)}] Checking: {url}")
        result = health_check_url(url, cfg)
        results.append(result)

        # Status display
        status = result["result"]
        status_code = result["status_code"]
        response_time = result["response_time_ms"]
        matched = result["matched_keywords"]

        if status == "Unhealthy":
            print(f"  → ❌ {status} ({status_code}) - {response_time}ms")
            print(f"      Keywords: {matched}")
        elif status == "Error":
            print(f"  → 🚫 {status} ({status_code}) - {result['error_message']}")
        else:
            print(f"  → ✅ {status} ({status_code}) - {response_time}ms")

        # Small delay to be polite
        time.sleep(0.5)

    # Save results to CSV
    fieldnames = [
        "timestamp", "url", "domain", "status_code", "result",
        "response_time_ms", "content_type", "matched_keywords",
        "title", "content_sha256", "error_message"
    ]

    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults saved to: {csv_filename}")

    # Summary statistics
    total = len(results)
    healthy = sum(1 for r in results if r["result"] == "Healthy")
    unhealthy = sum(1 for r in results if r["result"] == "Unhealthy")
    errors = sum(1 for r in results if r["result"] == "Error")

    print(f"\nSummary:")
    print(f"  Total: {total}")
    print(f"  ✅ Healthy: {healthy}")
    print(f"  ❌ Unhealthy: {unhealthy}")
    print(f"  🚫 Errors: {errors}")

    return results

def load_urls_from_file(file_path: str) -> List[str]:
    """Load URLs from text file, filtering out comments and empty lines"""
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)
    except Exception as e:
        print(f"Error loading URLs from {file_path}: {e}")
        return []
    return urls

def create_enhanced_sample_files():
    """Create enhanced sample files with improved keyword detection"""

    # Enhanced keywords.json with better coverage
    keywords_content = {
        "global_keywords": [
            "시스템 점검",
            "서비스 중단",
            "불편을 드려 죄송",
            "화재",
            "서비스 이용이 제한",
            "대체사이트",
            "원복 중",
            "복구 중",
            "긴급 점검",
            "maintenance",
            "temporarily unavailable",
            "service down",
            "under construction"
        ],
        "domains": {
            "law.go.kr": [
                "법령정보 열람 관련 대체사이트",
                "국가정보자원관리원 전산실 화재",
                "법령 서비스 중단"
            ],
            "www.law.go.kr": [
                "법령 데이터베이스 점검",
                "검색 서비스 일시 중단"
            ],
            "*.go.kr": [
                "정부 시스템 점검",
                "공공서비스 일시 중단",
                "전산 장애",
                "네트워크 점검"
            ]
        },
        "regex_keywords": [
            { "pattern": "점검\\s*중", "flags": "i" },
            { "pattern": "원복\\s*중", "flags": "i" },
            { "pattern": "복구\\s*중", "flags": "i" },
            { "pattern": "service.*down", "flags": "i" },
            { "pattern": "temporarily.*unavailable", "flags": "i" }
        ],
        "settings": {
            "case_insensitive": True,
            "normalize_whitespace": True,
            "max_bytes_to_scan": 3000000,
            "timeout_seconds": 8,
            "retries": 1,
            "user_agent": "HealthChecker/2.0 (+monitoring@company.com)"
        }
    }

    # Write enhanced files
    with open('keywords_enhanced.json', 'w', encoding='utf-8') as f:
        json.dump(keywords_content, f, ensure_ascii=False, indent=2)

    print("Enhanced sample files created:")
    print("- keywords_enhanced.json")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhanced Health Check with Advanced Text Processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python healthcheck_enhanced.py --urls urls.txt --keywords keywords_enhanced.json
  python healthcheck_enhanced.py --create-samples  # Create enhanced sample files
        """
    )

    parser.add_argument('--urls', type=str, help='Path to URLs text file')
    parser.add_argument('--keywords', type=str, help='Path to keywords JSON file')
    parser.add_argument('--out', type=str, default='health_check_enhanced.csv',
                       help='Output CSV file (default: health_check_enhanced.csv)')
    parser.add_argument('--create-samples', action='store_true',
                       help='Create enhanced sample files')

    args = parser.parse_args()

    if args.create_samples:
        create_enhanced_sample_files()
        exit(0)

    if not args.urls or not args.keywords:
        parser.print_help()
        print("\nError: Both --urls and --keywords are required")
        exit(1)

    # Load and process
    urls = load_urls_from_file(args.urls)
    if not urls:
        print("No valid URLs found")
        exit(1)

    # Run enhanced health check
    check_multiple_urls(urls, args.keywords, args.out)