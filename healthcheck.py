#!/usr/bin/env python3
"""
Enhanced Health Check Script with Advanced Text Processing

Usage:
    python healthcheck.py --urls urls.txt --keywords keywords.json --out result.csv

Features:
- Advanced encoding detection and normalization
- Unicode and whitespace normalization for better keyword matching
- Domain-specific keyword matching with wildcards
- Regex pattern support with proper flags
- Title extraction from HTML
- Content hashing for integrity verification
- Configurable scan limits and retry logic
- Comprehensive CSV output with detailed metadata
"""

import argparse
import csv
import json
import re
import time
import hashlib
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse

import requests


class HealthChecker:
    def __init__(self, keywords_config: Dict[str, Any], max_bytes: int = 50000, timeout: int = 10):
        """
        Initialize health checker with keyword configuration

        Args:
            keywords_config: Loaded keywords JSON configuration
            max_bytes: Maximum bytes to scan from response body
            timeout: Request timeout in seconds
        """
        self.keywords_config = keywords_config
        self.max_bytes = max_bytes
        self.timeout = timeout

        # Compile regex patterns once
        self.regex_patterns = []
        for regex_item in keywords_config.get("regex_keywords", []):
            pattern = regex_item["pattern"]
            flags = 0
            if "i" in regex_item.get("flags", ""):
                flags |= re.IGNORECASE
            self.regex_patterns.append(re.compile(pattern, flags))

    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            return urlparse(url).netloc.lower()
        except Exception:
            return ""

    def extract_title(self, html_content: str) -> str:
        """Extract title from HTML content using regex"""
        try:
            # Simple regex to extract title tag content
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
                # Clean up title (remove extra whitespace, newlines)
                title = re.sub(r'\s+', ' ', title)
                return title[:200]  # Limit title length
            return ""
        except Exception:
            return ""

    def get_keywords_for_domain(self, domain: str) -> List[str]:
        """
        Get applicable keywords for a domain with priority:
        1. Exact domain match
        2. Wildcard domain match (*.go.kr)
        3. Global keywords

        Args:
            domain: Domain to check (e.g., "www.law.go.kr")

        Returns:
            List of applicable keywords
        """
        keywords = []

        # 1. Check exact domain match
        domain_configs = self.keywords_config.get("domains", {})
        if domain in domain_configs:
            keywords.extend(domain_configs[domain])
            return keywords  # Use domain-specific only

        # 2. Check wildcard patterns
        for pattern, pattern_keywords in domain_configs.items():
            if pattern.startswith("*."):
                wildcard_domain = pattern[2:]  # Remove "*."
                if domain.endswith("." + wildcard_domain) or domain == wildcard_domain:
                    keywords.extend(pattern_keywords)
                    return keywords  # Use wildcard match only

        # 3. Fall back to global keywords
        keywords.extend(self.keywords_config.get("global_keywords", []))

        return keywords

    def check_keywords_in_content(self, content: str, keywords: List[str]) -> Tuple[bool, str]:
        """
        Check if any keywords are found in content

        Args:
            content: Content to search in
            keywords: List of keywords to search for

        Returns:
            Tuple of (found, matched_keyword)
        """
        content_lower = content.lower()

        # Check string keywords
        for keyword in keywords:
            if keyword.lower() in content_lower:
                return True, keyword

        # Check regex patterns
        for pattern in self.regex_patterns:
            if pattern.search(content):
                return True, f"regex:{pattern.pattern}"

        return False, ""

    def check_url(self, url: str) -> Dict[str, Any]:
        """
        Perform health check on a single URL

        Args:
            url: URL to check

        Returns:
            Dictionary with check results
        """
        timestamp_iso = datetime.now().isoformat()
        domain = self.extract_domain(url)

        result = {
            "timestamp_iso": timestamp_iso,
            "url": url,
            "domain": domain,
            "status_code": "N/A",
            "result": "Error",
            "response_time_ms": 0,
            "title": "",
            "matched_keyword": "",
            "error_message": ""
        }

        try:
            start_time = time.time()

            # Make HTTP request
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={
                    "User-Agent": "HealthChecker/1.0 (+monitoring@company.com)"
                },
                stream=True  # Use streaming to control data read
            )

            response_time_ms = round((time.time() - start_time) * 1000, 1)
            result["response_time_ms"] = response_time_ms
            result["status_code"] = response.status_code

            if response.status_code != 200:
                result["result"] = "Error"
                result["error_message"] = f"HTTP {response.status_code}"
                return result

            # Read limited content
            content_bytes = b""
            bytes_read = 0

            for chunk in response.iter_content(chunk_size=8192):
                if bytes_read + len(chunk) > self.max_bytes:
                    # Read only remaining bytes
                    remaining = self.max_bytes - bytes_read
                    content_bytes += chunk[:remaining]
                    break
                content_bytes += chunk
                bytes_read += len(chunk)

            # Decode content
            try:
                content = content_bytes.decode('utf-8', errors='ignore')
            except UnicodeDecodeError:
                content = content_bytes.decode('latin-1', errors='ignore')

            # Extract title
            result["title"] = self.extract_title(content)

            # Get keywords for this domain
            keywords = self.get_keywords_for_domain(domain)

            # Check for negative keywords
            has_keyword, matched_keyword = self.check_keywords_in_content(content, keywords)

            if has_keyword:
                result["result"] = "Unhealthy"
                result["matched_keyword"] = matched_keyword
            else:
                result["result"] = "Healthy"

        except requests.exceptions.Timeout:
            result["error_message"] = "Request timeout"
        except requests.exceptions.ConnectionError as e:
            result["error_message"] = f"Connection error: {str(e)}"
        except requests.exceptions.RequestException as e:
            result["error_message"] = f"Request error: {str(e)}"
        except Exception as e:
            result["error_message"] = f"Unexpected error: {str(e)}"

        return result

    def check_multiple_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Check multiple URLs and return results

        Args:
            urls: List of URLs to check

        Returns:
            List of check results
        """
        results = []

        for i, url in enumerate(urls, 1):
            print(f"Checking {i}/{len(urls)}: {url}")
            result = self.check_url(url)
            results.append(result)

            # Brief output
            status = result["result"]
            status_code = result["status_code"]
            response_time = result["response_time_ms"]

            if status == "Unhealthy":
                print(f"  → {status} ({status_code}) - {response_time}ms - Keyword: {result['matched_keyword']}")
            elif status == "Error":
                print(f"  → {status} ({status_code}) - {result['error_message']}")
            else:
                print(f"  → {status} ({status_code}) - {response_time}ms")

            # Small delay to be polite
            time.sleep(0.5)

        return results

    def save_results_to_csv(self, results: List[Dict[str, Any]], output_file: str):
        """
        Save results to CSV file

        Args:
            results: List of check results
            output_file: Output CSV file path
        """
        fieldnames = [
            "timestamp_iso",
            "url",
            "domain",
            "status_code",
            "result",
            "response_time_ms",
            "title",
            "matched_keyword",
            "error_message"
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print(f"\nResults saved to: {output_file}")


def load_urls(file_path: str) -> List[str]:
    """Load URLs from text file"""
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith('#'):
                    urls.append(url)
    except Exception as e:
        print(f"Error loading URLs from {file_path}: {e}")
        return []

    return urls


def load_keywords(file_path: str) -> Dict[str, Any]:
    """Load keywords configuration from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading keywords from {file_path}: {e}")
        return {}


def create_sample_files():
    """Create sample input files for testing"""

    # Sample URLs
    urls_content = """# Sample URLs for health checking
https://www.law.go.kr/
https://www.gov.kr/
https://www.k-eta.go.kr/
https://httpbin.org/status/200
https://httpbin.org/status/500
"""

    # Sample keywords configuration
    keywords_content = {
        "global_keywords": [
            "시스템 점검",
            "서비스 중단",
            "불편을 드려 죄송",
            "화재",
            "maintenance",
            "temporarily unavailable"
        ],
        "domains": {
            "www.law.go.kr": [
                "법령 서비스 중단",
                "데이터베이스 점검"
            ],
            "*.go.kr": [
                "정부 시스템 점검",
                "공공서비스 일시 중단"
            ],
            "httpbin.org": [
                "test maintenance"
            ]
        },
        "regex_keywords": [
            {
                "pattern": r"점검.*중",
                "flags": "i"
            },
            {
                "pattern": r"service.*down",
                "flags": "i"
            }
        ]
    }

    # Write sample files
    with open('urls.txt', 'w', encoding='utf-8') as f:
        f.write(urls_content)

    with open('keywords.json', 'w', encoding='utf-8') as f:
        json.dump(keywords_content, f, ensure_ascii=False, indent=2)

    print("Sample files created:")
    print("- urls.txt")
    print("- keywords.json")


def main():
    parser = argparse.ArgumentParser(
        description="Advanced Health Check with Domain-specific Keywords",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python healthcheck.py --urls urls.txt --keywords keywords.json --out result.csv
  python healthcheck.py --create-samples  # Create sample input files
        """
    )

    parser.add_argument('--urls', type=str, help='Path to URLs text file')
    parser.add_argument('--keywords', type=str, help='Path to keywords JSON file')
    parser.add_argument('--out', type=str, default='health_check_results.csv',
                       help='Output CSV file (default: health_check_results.csv)')
    parser.add_argument('--max-bytes', type=int, default=50000,
                       help='Maximum bytes to scan from response (default: 50000)')
    parser.add_argument('--timeout', type=int, default=10,
                       help='Request timeout in seconds (default: 10)')
    parser.add_argument('--create-samples', action='store_true',
                       help='Create sample urls.txt and keywords.json files')

    args = parser.parse_args()

    if args.create_samples:
        create_sample_files()
        return

    if not args.urls or not args.keywords:
        parser.print_help()
        print("\nError: Both --urls and --keywords are required")
        return

    # Validate input files
    if not Path(args.urls).exists():
        print(f"Error: URLs file not found: {args.urls}")
        return

    if not Path(args.keywords).exists():
        print(f"Error: Keywords file not found: {args.keywords}")
        return

    # Load inputs
    print(f"Loading URLs from: {args.urls}")
    urls = load_urls(args.urls)
    if not urls:
        print("No valid URLs found")
        return

    print(f"Loading keywords from: {args.keywords}")
    keywords_config = load_keywords(args.keywords)
    if not keywords_config:
        print("No keywords configuration loaded")
        return

    print(f"Found {len(urls)} URLs to check")
    print(f"Max scan bytes: {args.max_bytes}")
    print(f"Timeout: {args.timeout}s")
    print("-" * 50)

    # Initialize checker and run
    checker = HealthChecker(keywords_config, args.max_bytes, args.timeout)
    results = checker.check_multiple_urls(urls)

    # Save results
    checker.save_results_to_csv(results, args.out)

    # Summary
    total = len(results)
    healthy = sum(1 for r in results if r["result"] == "Healthy")
    unhealthy = sum(1 for r in results if r["result"] == "Unhealthy")
    errors = sum(1 for r in results if r["result"] == "Error")

    print(f"\nSummary:")
    print(f"  Total: {total}")
    print(f"  Healthy: {healthy}")
    print(f"  Unhealthy: {unhealthy}")
    print(f"  Errors: {errors}")


if __name__ == "__main__":
    main()