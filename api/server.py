"""
NeighborIQ API Server

Run:
    python -m uvicorn neighboriq.api.server:app --host 0.0.0.0 --port 8000

Endpoints:
    GET  /health
    GET  /analyze/{zip_code}
    GET  /businesses/{zip_code}
    GET  /opportunities/{zip_code}
    GET  /content/{zip_code}/{niche}
    POST /analyze (body: {zip_code, radius_mi?, run_llm?})
"""
from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel
except ImportError:
    print("FastAPI not installed. Run: pip install fastapi uvicorn")
    raise SystemExit(1)

log = logging.getLogger("neighboriq.api")

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = ROOT / "dashboard"

app = FastAPI(
    title="NeighborIQ API",
    description="Neighborhood business intelligence — underserved niche detection",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── rate limiter ──────────────────────────────────────────────────────────────

_rate_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = 10
_RATE_WINDOW = 60.0


def _check_rate(ip: str) -> bool:
    now = time.time()
    window_start = now - _RATE_WINDOW
    timestamps = [t for t in _rate_store[ip] if t > window_start]
    _rate_store[ip] = timestamps
    if len(timestamps) >= _RATE_LIMIT:
        return False
    _rate_store[ip].append(now)
    return True


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next: Any) -> Any:
    ip = request.client.host if request.client else "unknown"
    if not _check_rate(ip):
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Max 10 requests/minute."},
        )
    return await call_next(request)


# ── request models ────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    zip_code: str
    radius_mi: float = 1.5
    run_llm: bool = True


# ── endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
async def dashboard_root() -> FileResponse | JSONResponse:
    index = DASHBOARD_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({"message": "NeighborIQ API — visit /docs for Swagger UI", "version": "0.2.0"})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.2.0"}


@app.get("/opportunities/{zip_code}")
async def get_opportunities(zip_code: str, min_tier: str = "C") -> dict:
    """Return cached opportunities for a zip code from DB."""
    from neighboriq.storage.market_db import MarketDB
    db = MarketDB()
    if not db.neighborhood_exists(zip_code):
        raise HTTPException(status_code=404, detail=f"No data for {zip_code}. Run analyze first.")
    opps = db.get_opportunities(zip_code, min_tier=min_tier)
    return {"zip_code": zip_code, "opportunities": opps, "count": len(opps)}


@app.get("/businesses/{zip_code}")
async def get_businesses(zip_code: str) -> dict:
    """Return indexed businesses for a zip code."""
    from neighboriq.storage.market_db import MarketDB
    db = MarketDB()
    neighborhood = db.get_neighborhood(zip_code)
    if not neighborhood:
        raise HTTPException(status_code=404, detail=f"No data for {zip_code}. Run analyze first.")
    businesses = db.get_businesses(neighborhood["id"])
    return {"zip_code": zip_code, "businesses": businesses, "count": len(businesses)}


@app.get("/content/{zip_code}/{niche}")
async def get_content(zip_code: str, niche: str) -> dict:
    """Return generated YouTube script for a zip/niche pair."""
    content_path = ROOT / "data" / "content" / f"{zip_code}_{niche}.json"
    if not content_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No content for {zip_code}/{niche}. Run: neighboriq content --zip {zip_code} --niche {niche}",
        )
    data = json.loads(content_path.read_text(encoding="utf-8"))
    return {"zip_code": zip_code, "niche": niche, "script": data}


@app.get("/analyze/{zip_code}")
async def analyze_get(zip_code: str, radius_mi: float = 1.5, run_llm: bool = False) -> dict:
    """Trigger full analysis pipeline for a zip code."""
    return await _run_analysis(zip_code, radius_mi=radius_mi, run_llm=run_llm)


@app.post("/analyze")
async def analyze_post(req: AnalyzeRequest) -> dict:
    """Trigger full analysis pipeline with configurable options."""
    return await _run_analysis(req.zip_code, radius_mi=req.radius_mi, run_llm=req.run_llm)


async def _run_analysis(zip_code: str, radius_mi: float, run_llm: bool) -> dict:
    from neighboriq.cli import _run_pipeline
    try:
        result = _run_pipeline(zip_code, radius_mi=radius_mi, run_llm=run_llm)
        return {
            "zip_code": zip_code,
            "demographics": result["demographics"],
            "opportunities": result["opportunities"],
            "opportunity_count": len(result["opportunities"]),
            "llm_analysis": result.get("llm_analysis", {}),
        }
    except Exception as exc:
        log.error("Analysis failed for %s: %s", zip_code, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ── Revenue model & automation ────────────────────────────────────────────────

@app.get("/revenue-model/{niche}")
async def get_revenue_model_endpoint(niche: str, zip_code: str = "") -> dict:
    """Return full revenue model + automation blueprint for a niche."""
    try:
        import dataclasses
        from neighboriq.scoring.revenue_model import get_revenue_model, format_revenue_model
        from neighboriq.scoring.automation_matrix import get_automation_blueprint, format_automation_blueprint
        demographics: dict = {}
        if zip_code:
            from neighboriq.storage.market_db import MarketDB
            db = MarketDB()
            hood = db.get_neighborhood(zip_code)
            if hood:
                demographics = {"median_income": hood.get("median_income", 0)}
        m = get_revenue_model(niche, demographics)
        b = get_automation_blueprint(niche)
        return {
            "niche": niche,
            "revenue_model": dataclasses.asdict(m),
            "automation_blueprint": dataclasses.asdict(b),
            "formatted_revenue": format_revenue_model(m),
            "formatted_automation": format_automation_blueprint(b),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Asset filter ──────────────────────────────────────────────────────────────

class AssetFilterRequest(BaseModel):
    zip_code: str
    capital_usd: int = 50_000
    space_sqft: int = 0
    has_vehicle: bool = False
    skills: list[str] = []
    licenses: list[str] = []
    monthly_overhead_max: int = 5_000
    prefers_home_based: bool = False
    hours_per_week: int = 40
    top_n: int = 10


@app.post("/asset-filter")
async def asset_filter(req: AssetFilterRequest) -> dict:
    """Filter neighborhood opportunities by operator's available assets."""
    try:
        import dataclasses
        from neighboriq.analyzers.asset_mapper import filter_by_assets, AssetProfile
        from neighboriq.storage.market_db import MarketDB
        db = MarketDB()
        if not db.neighborhood_exists(req.zip_code):
            raise HTTPException(
                status_code=404,
                detail=f"No data for {req.zip_code}. Run /analyze/{req.zip_code} first.",
            )
        opps = db.get_opportunities(req.zip_code, min_tier="C")
        profile = AssetProfile(
            capital_usd=req.capital_usd,
            space_sqft=req.space_sqft,
            has_vehicle=req.has_vehicle,
            skills=tuple(req.skills),
            licenses=tuple(req.licenses),
            existing_customers=0,
            monthly_overhead_max=req.monthly_overhead_max,
            prefers_home_based=req.prefers_home_based,
            hours_per_week=req.hours_per_week,
        )
        results = filter_by_assets(opps, profile, top_n=req.top_n)
        return {
            "zip_code": req.zip_code,
            "results": [dataclasses.asdict(r) for r in results],
            "count": len(results),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Niche roadmap ─────────────────────────────────────────────────────────────

@app.get("/roadmap/{niche}")
async def get_niche_roadmap_endpoint(niche: str) -> dict:
    """Return 3-phase scaling roadmap, Delta 4 analysis, and repeat customer mechanics for a niche."""
    import dataclasses
    from neighboriq.scoring.niche_roadmap import get_niche_roadmap, format_roadmap, list_roadmap_niches
    slug = niche.lower().replace("-", "_").replace(" ", "_")
    roadmap = get_niche_roadmap(slug)
    known = list_roadmap_niches()
    return {
        "niche": slug,
        "is_curated": slug in known,
        "curated_niches": known,
        "roadmap": dataclasses.asdict(roadmap),
        "formatted": format_roadmap(roadmap),
    }


# ── Static dashboard ──────────────────────────────────────────────────────────

if DASHBOARD_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")
