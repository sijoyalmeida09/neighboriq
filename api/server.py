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


# ── Growth forecast ───────────────────────────────────────────────────────────

class ForecastRequest(BaseModel):
    biz_name: str
    domain_id: str
    monthly_revenue: int = 0
    monthly_expenses: int = 0
    city_population: int = 700_000
    weeks: int = 12


@app.post("/forecast")
async def get_forecast_endpoint(req: ForecastRequest) -> dict:
    """Generate date-stamped growth forecast with TAM/SAM/SOM and weekly action plan."""
    import dataclasses
    from neighboriq.intelligence.benchmark_engine import get_benchmarks
    from neighboriq.intelligence.domain_taxonomy import get_domain
    from neighboriq.intelligence.biz_profile import BizProfile
    from neighboriq.intelligence.milestone_engine import generate_forecast

    domain = get_domain(req.domain_id)
    if domain is None:
        raise HTTPException(status_code=400, detail=f"Unknown domain: {req.domain_id}")

    try:
        benchmarks = get_benchmarks(req.domain_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Benchmark fetch failed: {exc}")

    profile = BizProfile(
        name=req.biz_name,
        description=req.domain_id.replace("_", " "),
        naics_code=None,
        year_founded=None,
        website=None,
        equipment=(),
        inventory_value=0,
        vehicles=0,
        sqft_owned=0,
        sqft_leased=0,
        real_estate_value=0,
        monthly_web_traffic=0,
        email_list_size=0,
        social_followers=(),
        software_tools=(),
        data_assets=(),
        ip_patents=(),
        headcount=0,
        roles=(),
        owner_certifications=(),
        owner_network_size=0,
        monthly_revenue=req.monthly_revenue,
        monthly_expenses=req.monthly_expenses,
        cash_on_hand=0,
        credit_line=0,
        monthly_debt_service=0,
        years_in_market=0,
        avg_rating=4.0,
        review_count=0,
        recognition="neighborhood",
        licenses=(),
        certifications=(),
        exclusive_supplier_contracts=(),
        proprietary_processes=(),
        revenue_streams=(),
    )

    try:
        forecast = generate_forecast(profile, benchmarks, domain, city_population=req.city_population)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Forecast generation failed: {exc}")

    return {
        "biz_name": forecast.biz_name,
        "domain_id": forecast.domain_id,
        "start_date": forecast.start_date,
        "market": {
            "tam_usd": forecast.market.tam_usd,
            "sam_usd": forecast.market.sam_usd,
            "som_usd": forecast.market.som_usd,
            "year1_revenue": forecast.market.year1_revenue,
            "year3_revenue": forecast.market.year3_revenue,
            "market_phase": forecast.market.market_phase,
            "tam_description": forecast.market.tam_description,
            "sam_description": forecast.market.sam_description,
            "som_description": forecast.market.som_description,
        },
        "break_even_week": forecast.break_even_week,
        "year1_roi_pct": forecast.year1_roi_pct,
        "total_investment_needed": forecast.total_investment_needed,
        "weekly_milestones": [
            {
                "week_number": m.week_number,
                "date": m.date,
                "theme": m.theme,
                "actions": list(m.actions),
                "revenue_impact_monthly": m.revenue_impact_monthly,
                "go_signal": m.go_signal,
                "no_go_signal": m.no_go_signal,
                "cost_to_execute": m.cost_to_execute,
            }
            for m in forecast.weekly_milestones[: req.weeks]
        ],
        "monthly_targets": [
            {
                "month_number": t.month_number,
                "date": t.date,
                "revenue_target": t.revenue_target,
                "profit_target": t.profit_target,
                "key_metric": t.key_metric,
                "key_metric_target": t.key_metric_target,
                "what_unlocks_next": t.what_unlocks_next,
                "risk_if_missed": t.risk_if_missed,
            }
            for t in forecast.monthly_targets
        ],
        "novel_opportunities": list(forecast.novel_opportunities),
        "recommended_llm": forecast.recommended_llm,
        "recommended_automation": forecast.recommended_automation,
        "recommended_agent_framework": forecast.recommended_agent_framework,
        "llm_cost_monthly": forecast.llm_cost_monthly,
    }


# ── Static dashboard ──────────────────────────────────────────────────────────

if DASHBOARD_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")
