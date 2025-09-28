from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import aiohttp
import time
import os
import yaml
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global configuration
CONFIG = {}
ENDPOINTS = []
app_start_time = time.time()

# In-memory caches (reset on restart)
robots_cache = {}  # robots.txt cache with expiry
last_results = {}  # last successful results cache
host_semaphores = {}  # concurrency control per host

def load_config():
    """Load configuration from YAML and environment variables"""
    global CONFIG, ENDPOINTS

    try:
        with open('endpoints.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        CONFIG = {
            'user_agent': config.get('user_agent', 'GovPublicStatusMonitor/1.0'),
            'timeouts': {
                'connect_s': int(os.getenv('PP_CONNECT_TIMEOUT_S', config['timeouts']['connect_s'])),
                'read_s': int(os.getenv('PP_READ_TIMEOUT_S', config['timeouts']['read_s'])),
                'total_s': int(os.getenv('PP_TOTAL_TIMEOUT_S', config['timeouts']['total_s']))
            },
            'budgets': {
                'per_host_min_interval_s': int(os.getenv('PP_HOST_MIN_INTERVAL_S', config['budgets']['per_host_min_interval_s'])),
                'per_endpoint_min_interval_s': int(os.getenv('PP_EP_MIN_INTERVAL_S', config['budgets']['per_endpoint_min_interval_s'])),
                'global_max_concurrency': int(os.getenv('PP_GLOBAL_MAX_CONCURRENCY', config['budgets']['global_max_concurrency'])),
                'per_host_concurrency': int(os.getenv('PP_PER_HOST_CONCURRENCY', config['budgets']['per_host_concurrency']))
            },
            'allowed_origins': os.getenv('PP_ALLOWED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(','),
            'reload_token': os.getenv('PP_RELOAD_TOKEN', 'change-me')
        }

        ENDPOINTS = config['endpoints']

        # Initialize host semaphores
        hosts = set(urlparse(ep['url']).netloc for ep in ENDPOINTS)
        for host in hosts:
            host_semaphores[host] = asyncio.Semaphore(CONFIG['budgets']['per_host_concurrency'])

        logger.info(f"Configuration loaded successfully. {len(ENDPOINTS)} endpoints configured.")

    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise HTTPException(status_code=500, detail="Configuration loading failed")

# Initialize configuration on startup
load_config()

# Create FastAPI app
app = FastAPI(title="Government Public Status Monitor")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG['allowed_origins'],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

async def check_robots_txt(url: str) -> bool:
    """Check if URL is allowed by robots.txt with 24h caching"""
    parsed_url = urlparse(url)
    host = parsed_url.netloc
    robots_url = f"{parsed_url.scheme}://{host}/robots.txt"

    current_time = time.time()

    # Check cache
    if host in robots_cache:
        cached_data, timestamp = robots_cache[host]
        if current_time - timestamp < 86400:  # 24h cache
            if cached_data is None:  # Failed to fetch, allow conservatively
                return True
            return cached_data.can_fetch(CONFIG['user_agent'], url)

    # Fetch robots.txt
    try:
        timeout = aiohttp.ClientTimeout(total=3)
        headers = {'User-Agent': CONFIG['user_agent']}

        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.head(robots_url) as response:
                if response.status == 200:
                    async with session.get(robots_url) as get_response:
                        if get_response.status == 200:
                            robots_content = await get_response.text()
                            rp = RobotFileParser()
                            rp.set_url(robots_url)
                            # Use the correct method for setting content
                            from io import StringIO
                            rp.fp = StringIO(robots_content)
                            rp.read()
                            robots_cache[host] = (rp, current_time)
                            logger.info(f"Robots.txt fetched for {host}")
                            return rp.can_fetch(CONFIG['user_agent'], url)

                # Failed to fetch - cache None and allow conservatively
                robots_cache[host] = (None, current_time)
                logger.warning(f"Failed to fetch robots.txt for {host}, allowing conservatively")
                return True

    except Exception as e:
        # Cache failure and allow conservatively
        robots_cache[host] = (None, current_time)
        logger.warning(f"Error fetching robots.txt for {host}: {e}, allowing conservatively")
        return True


async def check_website(endpoint: Dict) -> Dict:
    """Check a single website and return monitoring data"""
    url = endpoint['url']
    name = endpoint['name']
    start_time = time.time()

    # Check robots.txt
    if not await check_robots_txt(url):
        result = {
            "name": name,
            "url": url,
            "http": None,
            "ttfb_ms": 0,
            "outcome": "DISALLOWED",
            "error": "Blocked by robots.txt",
            "ts": datetime.now().isoformat(),
            "skipped": False
        }
        logger.info(json.dumps({
            "outcome": "DISALLOWED",
            "http": None,
            "ttfb_ms": 0,
            "elapsed_ms": 0,
            "skipped": False,
            "robots": True,
            "host": urlparse(url).netloc,
            "url": url
        }))
        return result

    # Concurrency control
    host = urlparse(url).netloc
    semaphore = host_semaphores.get(host)

    try:
        async with semaphore:
            timeout = aiohttp.ClientTimeout(
                sock_connect=CONFIG['timeouts']['connect_s'],
                sock_read=CONFIG['timeouts']['read_s'],
                total=CONFIG['timeouts']['total_s']
            )
            headers = {'User-Agent': CONFIG['user_agent']}

            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                # Try HEAD first, fallback to GET if needed
                try:
                    async with session.head(url) as response:
                        ttfb_ms = int((time.time() - start_time) * 1000)

                        if response.status == 405:  # Method not allowed, try GET
                            async with session.get(url) as get_response:
                                ttfb_ms = int((time.time() - start_time) * 1000)
                                status = get_response.status
                        else:
                            status = response.status

                except aiohttp.ClientResponseError as e:
                    status = e.status
                    ttfb_ms = int((time.time() - start_time) * 1000)

                # Determine outcome
                if status == 200:
                    outcome = "Healthy"
                elif 400 <= status < 500:
                    outcome = "Error"
                elif 500 <= status:
                    outcome = "Error"
                else:
                    outcome = "Unhealthy"

                result = {
                    "name": name,
                    "url": url,
                    "http": status,
                    "ttfb_ms": ttfb_ms,
                    "outcome": outcome,
                    "error": None,
                    "ts": datetime.now().isoformat(),
                    "skipped": False
                }

    except asyncio.TimeoutError:
        elapsed_ms = int((time.time() - start_time) * 1000)
        result = {
            "name": name,
            "url": url,
            "http": None,
            "ttfb_ms": elapsed_ms,
            "outcome": "Error",
            "error": "Request timeout",
            "ts": datetime.now().isoformat(),
            "skipped": False
        }
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        result = {
            "name": name,
            "url": url,
            "http": None,
            "ttfb_ms": elapsed_ms,
            "outcome": "Error",
            "error": str(e),
            "ts": datetime.now().isoformat(),
            "skipped": False
        }

    # Cache successful results
    if result['outcome'] in ['Healthy', 'Error', 'Unhealthy']:
        last_results[url] = {
            'last_outcome': result['outcome'],
            'last_http': result['http'],
            'last_ttfb_ms': result['ttfb_ms'],
            'last_ts': result['ts']
        }

    # Log result
    logger.info(json.dumps({
        "outcome": result['outcome'],
        "http": result['http'],
        "ttfb_ms": result['ttfb_ms'],
        "elapsed_ms": int((time.time() - start_time) * 1000),
        "skipped": result['skipped'],
        "robots": False,
        "host": urlparse(url).netloc,
        "url": url
    }))

    return result

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard with auto-refreshing cards"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Government Public Status Monitor</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { text-align: center; color: #333; }
            .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .status { font-weight: bold; padding: 4px 8px; border-radius: 4px; }
            .Healthy { background: #d4edda; color: #155724; }
            .Unhealthy { background: #fff3cd; color: #856404; }
            .Error { background: #f8d7da; color: #721c24; }
            .DISALLOWED { background: #f8d7da; color: #721c24; }
            .metric { margin: 8px 0; }
            .url { color: #007bff; text-decoration: none; }
            .timestamp { color: #666; font-size: 0.9em; }
            .last-result { color: #868e96; font-style: italic; font-size: 0.85em; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Government Public Status Monitor</h1>
            <div id="cards" class="cards">Loading...</div>
        </div>

        <script>
            async function updateDashboard() {
                try {
                    const response = await fetch('/snapshot');
                    const data = await response.json();

                    const cardsHtml = data.map(site => {

                        return `
                            <div class="card">
                                <h3><a href="${site.url}" target="_blank" class="url">${site.name}</a></h3>
                                <div class="metric">Status: <span class="status ${site.outcome}">${site.outcome}</span></div>
                                <div class="metric">HTTP: ${site.http || 'N/A'}</div>
                                <div class="metric">TTFB: ${site.ttfb_ms}ms</div>
                                ${site.error ? `<div class="metric">Error: ${site.error}</div>` : ''}
                                <div class="timestamp">Last checked: ${new Date(site.ts).toLocaleString()}</div>
                            </div>
                        `;
                    }).join('');

                    document.getElementById('cards').innerHTML = cardsHtml;
                } catch (error) {
                    document.getElementById('cards').innerHTML = '<div class="card">Error loading data</div>';
                }
            }

            // Initial load
            updateDashboard();

            // Auto-refresh every 60 seconds
            setInterval(updateDashboard, 60000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/snapshot")
async def snapshot():
    """API endpoint that returns current status of all monitored websites"""
    results = []

    for endpoint in ENDPOINTS:
        result = await check_website(endpoint)
        results.append(result)

    return results

@app.get("/health")
async def health():
    """Health check endpoint"""
    uptime_s = int(time.time() - app_start_time)
    return {
        "ok": True,
        "uptime_s": uptime_s,
        "endpoints_count": len(ENDPOINTS),
        "user_agent": CONFIG['user_agent']
    }

@app.post("/reload")
async def reload_config(x_reload_token: str = Header(None)):
    """Reload configuration from YAML (requires token)"""
    if x_reload_token != CONFIG['reload_token']:
        raise HTTPException(status_code=401, detail="Invalid reload token")

    try:
        # Clear caches
        global robots_cache, last_results, host_semaphores
        robots_cache.clear()
        last_results.clear()
        host_semaphores.clear()

        # Reload configuration
        load_config()

        return {
            "ok": True,
            "message": "Configuration reloaded successfully",
            "endpoints_count": len(ENDPOINTS),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Reload failed: {str(e)}")
