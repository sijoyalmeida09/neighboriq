"""pipeline.py — Automated content generation pipeline.

Given a zip code, analyzes the neighborhood and generates YouTube video
scripts for the top Tier A/B opportunities. Sends a Telegram preview
for human review before posting.

Usage:
    python -m neighboriq.content.pipeline --zip 02122
    python -m neighboriq.content.pipeline --zip 02122 --post     # send to Telegram
    python -m neighboriq.content.pipeline --zip 02122 --top 3   # top 3 opps
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

log = logging.getLogger("neighboriq.pipeline")

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "data" / "content"
CONTENT_DIR.mkdir(parents=True, exist_ok=True)


def _get_opportunities_from_db(zip_code: str) -> list[dict]:
    """Load cached opportunities from MarketDB if available."""
    try:
        from neighboriq.storage.market_db import MarketDB
        db = MarketDB()
        return db.get_opportunities(zip_code, min_tier="C")
    except Exception as exc:
        log.warning("Could not load from DB: %s", exc)
        return []


def _run_analysis(zip_code: str) -> tuple[list[dict], dict]:
    """Run full pipeline and return (opportunities, demographics)."""
    try:
        from neighboriq.collectors.census_collector import fetch_demographics
        from neighboriq.collectors.google_maps_collector import scrape_businesses
        from neighboriq.scoring.opportunity_scorer import score_opportunities
        from neighboriq.scoring.niche_classifier import classify_businesses
        from neighboriq.storage.market_db import MarketDB

        log.info("Running analysis for %s", zip_code)
        demographics = fetch_demographics(zip_code)
        businesses = scrape_businesses(zip_code, headless=True, max_results=60)
        classified = classify_businesses(businesses)

        db = MarketDB()
        neighborhood_id = db.upsert_neighborhood(
            zip_code=zip_code,
            city=demographics.get("city", ""),
            state=demographics.get("state", ""),
            population=demographics.get("population", 0),
            median_income=demographics.get("median_income", 0),
        )
        db.add_businesses(neighborhood_id, classified)

        opportunities = score_opportunities(classified, demographics)
        for opp in opportunities:
            db.upsert_opportunity(neighborhood_id, opp["niche"], **{
                k: v for k, v in opp.items()
                if k not in ("niche", "neighborhood_id")
            })
        return opportunities, demographics
    except Exception as exc:
        log.warning("Full pipeline failed (%s), falling back to DB cache", exc)
        cached = _get_opportunities_from_db(zip_code)
        return cached, {}


def _filter_top_opportunities(
    opportunities: list[dict], top_n: int
) -> list[dict]:
    """Filter Tier A/B opportunities, fall back to score >= 60."""
    tier_ab = [
        o for o in opportunities
        if o.get("tier") in ("A", "B") or o.get("opportunity_score", 0) >= 60
    ]
    tier_ab_sorted = sorted(
        tier_ab, key=lambda o: o.get("opportunity_score", 0), reverse=True
    )
    return tier_ab_sorted[:top_n]


def _generate_and_save(
    zip_code: str,
    niche: str,
    opportunity: dict,
    demographics: dict,
) -> dict:
    """Generate script for one opportunity and save to disk."""
    from neighboriq.content.video_generator import generate_script, save_script

    competitor_analysis = {
        "avg_rating": opportunity.get("competitor_avg_rating", 3.5),
        "total_businesses_nearby": opportunity.get("competitor_count", 0) * 8,
    }
    city = opportunity.get("city", demographics.get("city", zip_code))
    llm_analysis_raw = opportunity.get("llm_analysis", "{}")
    if isinstance(llm_analysis_raw, str):
        try:
            llm_analysis = json.loads(llm_analysis_raw)
        except Exception:
            llm_analysis = {}
    else:
        llm_analysis = llm_analysis_raw or {}

    script = generate_script(
        zip_code=zip_code,
        city=city,
        niche=niche,
        opportunity_data=opportunity,
        demographics=demographics,
        competitor_analysis=competitor_analysis,
        llm_analysis=llm_analysis,
    )
    save_script(zip_code, niche, script)
    return script


def _format_pipeline_summary(zip_code: str, scripts: list[dict]) -> str:
    """Format a text summary of what was generated."""
    lines = [
        f"NeighborIQ Pipeline — {zip_code}",
        f"Generated {len(scripts)} video script(s)",
        "",
    ]
    for i, s in enumerate(scripts, 1):
        niche = s.get("niche", "unknown").replace("_", " ").title()
        score = s.get("opportunity_score", 0)
        revenue = s.get("revenue_estimate", 0)
        title = s.get("title", "")
        lines.append(f"{i}. [{niche}] Score: {score}/100 · Rev: ${revenue:,}/yr")
        lines.append(f"   Title: {title[:80]}")
        lines.append("")
    lines.append(f"Scripts saved to: {CONTENT_DIR}")
    return "\n".join(lines)


def _post_pipeline_summary(zip_code: str, scripts: list[dict]) -> None:
    """Post summary of generated scripts to Telegram for review."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat_id):
        log.warning("Telegram not configured — set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return

    try:
        import urllib.request
        text = _format_pipeline_summary(zip_code, scripts)
        payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                log.info("Pipeline summary sent to Telegram")
            else:
                log.warning("Telegram API error: %s", result)
    except Exception as exc:
        log.warning("Failed to post to Telegram: %s", exc)


def run_pipeline(
    zip_code: str, top_n: int = 3, post_to_telegram: bool = False
) -> list[dict]:
    """Full pipeline: analyze → filter → generate scripts → optionally post Telegram.

    Returns list of generated script dicts.
    """
    print(f"[NeighborIQ Pipeline] Analyzing {zip_code}...")

    # Step 1: get opportunities (cached or fresh run)
    cached = _get_opportunities_from_db(zip_code)
    if cached:
        print(f"  Loaded {len(cached)} opportunities from cache")
        opportunities = cached
        demographics: dict[str, Any] = {}
    else:
        print(f"  No cache found — running full analysis (may take 2-3 minutes)")
        opportunities, demographics = _run_analysis(zip_code)
        print(f"  Analysis complete: {len(opportunities)} opportunities found")

    # Step 2: filter top A/B
    top_opps = _filter_top_opportunities(opportunities, top_n)
    if not top_opps:
        print("  No Tier A/B opportunities found. Try lowering score threshold.")
        return []
    print(f"  Selected top {len(top_opps)} opportunities: "
          f"{', '.join(o.get('niche','?') for o in top_opps)}")

    # Step 3: generate scripts
    scripts: list[dict] = []
    for opp in top_opps:
        niche = opp.get("niche", "unknown")
        print(f"  Generating script for: {niche}...")
        try:
            script = _generate_and_save(zip_code, niche, opp, demographics)
            scripts.append(script)
            print(f"    Title: {script.get('title', '')[:70]}")
        except Exception as exc:
            log.error("Script generation failed for %s/%s: %s", zip_code, niche, exc)

    # Step 4: Telegram preview
    if post_to_telegram and scripts:
        print("  Posting pipeline summary to Telegram...")
        _post_pipeline_summary(zip_code, scripts)

    print(f"\n[Done] {len(scripts)} scripts saved to {CONTENT_DIR}")
    return scripts


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="NeighborIQ auto content pipeline")
    parser.add_argument("--zip", required=True, help="ZIP code to analyze")
    parser.add_argument("--top", type=int, default=3, help="Max scripts to generate")
    parser.add_argument("--post", action="store_true", help="Post summary to Telegram")
    args = parser.parse_args()

    generated = run_pipeline(args.zip, top_n=args.top, post_to_telegram=args.post)
    print(f"\nGenerated {len(generated)} scripts for {args.zip}")
