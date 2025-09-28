import os, time, httpx, asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from .config import settings
from .endpoints import load_endpoints
from .rate_limit import RateState
from .checker import Checker
from .ui import HTML as INDEX_HTML

APP_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(APP_DIR, ".."))

endpoints = load_endpoints(os.path.join(ROOT_DIR, "endpoints.yaml"))
rate = RateState(per_host_conc=settings.PER_HOST_CONCURRENCY,
                 global_conc=settings.GLOBAL_MAX_CONCURRENCY)
# keywords.json 파일 경로 설정
keywords_path = os.path.join(os.path.dirname(ROOT_DIR), "keywords.json")
checker = Checker(rate, keywords_path)

app = FastAPI(title="PolitePing — FastAPI only")

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(INDEX_HTML)

@app.get("/health", response_class=JSONResponse)
def health():
    return JSONResponse({"ok": True, "ts": time.time()})

@app.get("/snapshot", response_class=JSONResponse)
async def snapshot():
    limits = httpx.Limits(max_connections=5, max_keepalive_connections=5)
    async with httpx.AsyncClient(limits=limits) as client:
        results = []
        for ep in endpoints:
            results.append(await checker.check_one(client, ep))
    return JSONResponse(results, headers={"Cache-Control": "public, max-age=60, s-maxage=60"})