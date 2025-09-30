import os, time, httpx, asyncio, datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from .config import settings
from .endpoints import load_endpoints
from .rate_limit import RateState
from .checker import Checker
from .ui import HTML as INDEX_HTML
from .enhanced_ui import HTML as ENHANCED_HTML

APP_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(APP_DIR, ".."))

endpoints = load_endpoints(os.path.join(os.path.dirname(ROOT_DIR), "res/endpoints.yaml"))
rate = RateState(per_host_conc=settings.PER_HOST_CONCURRENCY,
                 global_conc=settings.GLOBAL_MAX_CONCURRENCY)
# keywords.json 파일 경로 설정
keywords_path = os.path.join(os.path.dirname(ROOT_DIR), "res/keywords.json")
checker = Checker(rate, keywords_path)

app = FastAPI(title="PolitePing — FastAPI only")

@app.get("/", response_class=HTMLResponse)
def index():
    """Enhanced dashboard with TypeScript utilities and local caching"""
    return HTMLResponse(ENHANCED_HTML)

@app.get("/legacy", response_class=HTMLResponse)
def legacy_index():
    """Legacy dashboard for backward compatibility"""
    return HTMLResponse(INDEX_HTML)

@app.get("/health", response_class=JSONResponse)
def health():
    return JSONResponse({"ok": True, "ts": time.time()})

@app.get("/snapshot", response_class=JSONResponse)
async def snapshot():
    """Legacy endpoint for backward compatibility"""
    return await api_status()

@app.get("/api/status", response_class=JSONResponse)
async def api_status():
    """Enhanced API endpoint with detailed status information"""
    limits = httpx.Limits(max_connections=5, max_keepalive_connections=5)
    async with httpx.AsyncClient(limits=limits) as client:
        results = []
        for ep in endpoints:
            result = await checker.check_one(client, ep)
            # Add timestamp in ISO format for frontend
            result["checked_at"] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()
            results.append(result)

    response_data = {
        "timestamp": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
        "status": "success",
        "data": results,
        "total_endpoints": len(results),
        "healthy": len([r for r in results if r["outcome"] == "OK"]),
        "unhealthy": len([r for r in results if r["outcome"] == "UNHEALTHY"]),
        "errors": len([r for r in results if r["outcome"] in ["ERROR", "HTTP4xx", "HTTP5xx"]])
    }

    return JSONResponse(response_data, headers={
        "Cache-Control": "public, max-age=30, s-maxage=30",
        "Access-Control-Allow-Origin": "*"
    })