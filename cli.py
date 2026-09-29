"""
NeighborIQ CLI

Usage:
    python -m neighboriq analyze --zip 02122
    python -m neighboriq analyze --zip 02122 --radius 1.5 --no-llm
    python -m neighboriq compare --zips 02122,02124
    python -m neighboriq content --zip 02122 --niche indian_restaurant
    python -m neighboriq run --zip 02122 --post
    python -m neighboriq stats
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import os
import sys
from pathlib import Path

# Ensure stdout handles Unicode on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("neighboriq.cli")

ROOT = Path(__file__).resolve().parent


# ── helpers ───────────────────────────────────────────────────────────────────

def _fmt_currency(n: int) -> str:
    return f"${n:,}"


def _fmt_population(n: int) -> str:
    return f"{n:,}"


def _print_box(lines: list[str]) -> None:
    width = max(len(l) for l in lines) + 4
    print("┌" + "─" * (width - 2) + "┐")
    for line in lines:
        pad = width - 4 - len(line)
        print("│  " + line + " " * pad + "  │")
    print("└" + "─" * (width - 2) + "┘")


def _print_opportunities(opportunities: list[dict], top: int = 10) -> None:
    print()
    print("TOP OPPORTUNITIES")
    print("━" * 52)
    for i, opp in enumerate(opportunities[:top], 1):
        tier = opp.get("tier", "C")
        niche = opp.get("niche", "")
        score = opp.get("opportunity_score", 0)
        sat = opp.get("saturation_ratio", 0.0)
        demand = opp.get("demand_score", 0)
        count = opp.get("competitor_count", 0)
        rating = opp.get("competitor_avg_rating", 0.0)
        capital = opp.get("typical_capital_req", 0)

        gap_display = f"{1.0 / sat:.1f}x" if sat > 0 else "∞"
        rating_display = f"avg rating {rating:.1f}" if rating > 0 else "n/a"
        capital_display = f"~{_fmt_currency(capital)}" if capital else "n/a"

        print(f"#{i} [{tier}] {niche:<32} Score: {score}  Gap: {gap_display}")
        print(f"     {count} existing • {rating_display} • demand {demand}/100")
        print(f"     Entry capital: {capital_display}")
        print()


# ── pipeline runner ───────────────────────────────────────────────────────────

def _run_pipeline(
    zip_code: str,
    radius_mi: float = 1.5,
    run_llm: bool = True,
    use_cache: bool = True,
) -> dict:
    """
    Full analysis pipeline. Returns {demographics, businesses, opportunities, llm_analysis}.
    Import order matters — collectors are slow, analyzers are fast.
    """
    from neighboriq.collectors.census_collector import get_demographics
    from neighboriq.collectors.google_maps_collector import collect_by_zip
    from neighboriq.collectors.google_trends_collector import get_demand_signals
    from neighboriq.collectors.yelp_collector import collect as yelp_collect
    from neighboriq.collectors.overpass_collector import count_businesses_by_category
    from neighboriq.analyzers.saturation_analyzer import compute_density
    from neighboriq.analyzers.gap_detector import detect_gaps
    from neighboriq.analyzers.sentiment_analyzer import analyze_competition_quality
    from neighboriq.analyzers.pattern_analyzer import compute_profile, profile_hash, get_lessons, SEED_PATTERNS
    from neighboriq.scoring.niche_classifier import classify_businesses, classify
    from neighboriq.scoring.opportunity_scorer import score_all_opportunities
    from neighboriq.storage.market_db import MarketDB

    db = MarketDB()

    log.info("Step 1/7 — Census demographics for %s", zip_code)
    demographics = get_demographics(zip_code)
    neighborhood_id = db.upsert_neighborhood(
        zip_code=zip_code,
        city=demographics.get("city", ""),
        state=demographics.get("state", ""),
        lat=0.0,
        lng=0.0,
        population=demographics.get("population", 0),
        median_income=demographics.get("median_income", 0),
        age_median=demographics.get("age_median", 0.0),
        growth_rate_5yr=demographics.get("growth_rate_5yr", 0.0),
    )

    # Fast-path for scraping: if businesses already in DB, reuse them (skip 7-min scrape).
    # Scoring (steps 3-7) always re-runs so opportunities stay fresh.
    log.info("Step 2/7 — Collecting businesses")
    cached_businesses: list[dict] = []
    if use_cache:
        hood = db.get_neighborhood(zip_code)
        if hood:
            cached_businesses = db.get_businesses(hood["id"])

    if cached_businesses:
        log.info("Using %d cached businesses from DB (skipping scrape)", len(cached_businesses))
        businesses_raw = cached_businesses
    else:
        businesses_raw = collect_by_zip(zip_code, radius_mi=radius_mi)
        if os.environ.get("YELP_API_KEY"):
            log.info("Step 2b — Supplementing with Yelp data")
            yelp_biz = yelp_collect(zip_code)
            businesses_raw = businesses_raw + yelp_biz

    businesses = classify_businesses(businesses_raw)

    # Only persist to DB when we scraped fresh data (not re-using cached rows)
    if not cached_businesses:
        db.add_businesses(neighborhood_id, businesses)

    log.info("Step 3/7 — Google Trends demand signals")
    niches = list({b["niche"] for b in businesses if b.get("niche") and b["niche"] != "other"})
    demand_signals = get_demand_signals(niches, location=zip_code)

    log.info("Step 4/7 — Saturation analysis")
    population = demographics.get("population", 10000) or 10000
    saturation_results = compute_density(businesses, population)

    log.info("Step 5/7 — Gap detection")
    gap_results = detect_gaps(saturation_results, demand_signals)

    log.info("Step 6/7 — Sentiment / competition quality")
    sentiment_results = analyze_competition_quality(businesses)
    sentiment_map = {s.niche: s for s in sentiment_results}

    log.info("Step 7/7 — Opportunity scoring")
    profile = compute_profile(demographics)
    phash = profile_hash(profile)

    # Seed patterns DB if empty
    existing_patterns = db.get_patterns(phash)
    if not existing_patterns:
        for p in SEED_PATTERNS:
            db.add_pattern(
                demographic_profile_hash=p["demographic_profile_hash"],
                niche=p["niche"],
                outcome=p["outcome"],
                years_to_profit=p.get("years_to_profit", 2.0),
                entry_capital_usd=p.get("entry_capital_usd", 100000),
                source=p.get("source", "seed"),
                notes=p.get("notes", ""),
            )
        existing_patterns = db.get_patterns(phash)

    lessons = get_lessons(existing_patterns)
    lessons_map = {l.niche: l for l in lessons}

    raw_scores = score_all_opportunities(
        saturation_results=saturation_results,
        gap_results=gap_results,
        sentiment_results=sentiment_results,
        pattern_lessons_by_niche={n: [l] for n, l in lessons_map.items()},
        demographics=demographics,
    )

    # Convert frozen dataclasses → mutable dicts with consistent key names
    sat_count_by_niche = {r.niche: r.actual_count for r in saturation_results}
    opportunities: list[dict] = []
    for o in raw_scores:
        d = dataclasses.asdict(o)
        d["opportunity_score"] = d.pop("score")
        d["pattern_confidence"] = d.pop("pattern_success_rate")
        d["competitor_count"] = sat_count_by_niche.get(d["niche"], 0)
        opportunities.append(d)

    llm_analysis: dict = {}
    if run_llm:
        try:
            from neighboriq.scoring.market_eval import evaluate_neighborhood
            llm_analysis = evaluate_neighborhood(zip_code, demographics, opportunities[:5], businesses=businesses[:50])
        except Exception as exc:
            log.warning("LLM eval skipped: %s", exc)

    # Persist opportunities
    for opp in opportunities:
        niche_cls = classify(opp["niche"])
        db.upsert_opportunity(
            neighborhood_id=neighborhood_id,
            niche=opp["niche"],
            opportunity_score=opp.get("opportunity_score", 0),
            saturation_ratio=opp.get("saturation_ratio", 0.0),
            demand_score=opp.get("demand_score", 0),
            competitor_avg_rating=opp.get("competitor_avg_rating", 0.0),
            competitor_count=opp.get("competitor_count", 0),
            pattern_confidence=opp.get("pattern_confidence", 0.0),
            llm_analysis=json.dumps(llm_analysis),
            tier=opp.get("tier", "C"),
            typical_capital_req=niche_cls.typical_capital_req,
        )

    # Enrich with capital estimates for display
    for opp in opportunities:
        niche_cls = classify(opp["niche"])
        opp["typical_capital_req"] = niche_cls.typical_capital_req

    return {
        "zip_code": zip_code,
        "demographics": demographics,
        "businesses": businesses,
        "opportunities": opportunities,
        "llm_analysis": llm_analysis,
    }


# ── subcommand handlers ───────────────────────────────────────────────────────

def _cmd_analyze(args: argparse.Namespace) -> None:
    zip_code = args.zip
    print(f"NeighborIQ — Analyzing zip {zip_code}...")
    print()

    result = _run_pipeline(
        zip_code=zip_code,
        radius_mi=args.radius,
        run_llm=not args.no_llm,
        use_cache=not args.no_cache,
    )

    demo = result["demographics"]
    city = demo.get("city", "")
    state = demo.get("state", "")
    location_str = f"{city}, {state}".strip(", ") or zip_code
    pop = demo.get("population", 0)
    income = demo.get("median_income", 0)

    _print_box([
        f"NeighborIQ — {zip_code} ({location_str})",
        f"Population: {_fmt_population(pop)}  |  Median Income: {_fmt_currency(income)}",
    ])

    opportunities = result["opportunities"]
    if not opportunities:
        print("No opportunities found. Try increasing --radius or checking data sources.")
        return

    from neighboriq.display import (
        print_opportunity_table,
        print_full_analysis,
        print_asset_filter,
        print_llm_analysis,
    )

    if args.output == "json":
        print(json.dumps(result["opportunities"], indent=2))
    elif args.output == "report":
        try:
            from content.report_generator import generate_report
            path = generate_report(zip_code, result)
            print(f"Report saved: {path}")
        except Exception as exc:
            log.warning("Report generation failed: %s", exc)
            print_opportunity_table(opportunities)
    elif getattr(args, "depth", "table") == "full":
        print_full_analysis(opportunities, result["demographics"])
    else:
        print_opportunity_table(opportunities)

    # Asset filter — works with any output/depth mode
    if getattr(args, "assets", None):
        try:
            import json as _json
            asset_dict = _json.loads(args.assets)
            asset_dict.setdefault("zip_code", zip_code)
            from neighboriq.analyzers.asset_mapper import filter_by_assets, parse_asset_profile_from_dict
            profile = parse_asset_profile_from_dict(asset_dict)
            feasibility = filter_by_assets(opportunities, profile, top_n=5)
            print_asset_filter(feasibility)
        except Exception as exc:
            log.warning("Asset filter failed: %s", exc)

    if result.get("llm_analysis") and getattr(args, "depth", "table") != "full":
        print_llm_analysis(result["llm_analysis"])


def _cmd_compare(args: argparse.Namespace) -> None:
    zips = [z.strip() for z in args.zips.split(",") if z.strip()]
    if not zips:
        print("No zip codes provided.")
        return

    results: list[dict] = []
    for z in zips:
        print(f"Analyzing {z}...")
        try:
            results.append(_run_pipeline(z, run_llm=False))
        except Exception as exc:
            log.error("Failed for %s: %s", z, exc)

    if not results:
        return

    print()
    print("COMPARISON")
    print("━" * 52)
    for res in results:
        z = res["zip_code"]
        top = res["opportunities"][:3] if res["opportunities"] else []
        print(f"\n{z}:")
        for i, opp in enumerate(top, 1):
            print(f"  #{i} [{opp.get('tier','C')}] {opp.get('niche','')} — score {opp.get('opportunity_score',0)}")


def _cmd_content(args: argparse.Namespace) -> None:
    zip_code = args.zip
    niche = args.niche

    from storage.market_db import MarketDB
    db = MarketDB()
    opps = db.get_opportunities(zip_code, min_tier="C")
    opp = next((o for o in opps if o.get("niche") == niche), None)

    if not opp:
        print(f"No opportunity data found for {niche} in {zip_code}. Run analyze first.")
        return

    try:
        from content.video_generator import generate_video_script
        script = generate_video_script(zip_code, niche, opp)
        print(json.dumps(script, indent=2))
    except Exception as exc:
        log.error("Content generation failed: %s", exc)


def _cmd_run(args: argparse.Namespace) -> None:
    zip_code = args.zip
    print(f"NeighborIQ — Full run for {zip_code}...")

    result = _run_pipeline(zip_code, radius_mi=1.5, run_llm=True)
    opportunities = result["opportunities"]

    if not opportunities:
        print("No opportunities found.")
        return

    # Generate content for top opportunity
    top = opportunities[0]
    niche = top.get("niche", "")
    try:
        from content.video_generator import generate_video_script
        from content.report_generator import generate_report
        script = generate_video_script(zip_code, niche, top)
        report_path = generate_report(zip_code, result)

        content_path = ROOT / "data" / "content" / f"{zip_code}_{niche}.json"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        content_path.write_text(json.dumps(script, indent=2), encoding="utf-8")
        log.info("Script saved: %s", content_path)
        log.info("Report saved: %s", report_path)
    except Exception as exc:
        log.warning("Content generation failed: %s", exc)

    if args.post:
        _post_to_telegram(zip_code, opportunities[:3])

    _print_opportunities(opportunities)


def _post_to_telegram(zip_code: str, opportunities: list[dict]) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_SIJOY_CHAT_ID")
    if not token or not chat_id:
        log.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_SIJOY_CHAT_ID not set — skipping Telegram post")
        return

    import requests

    lines = [f"📍 *NeighborIQ — {zip_code}*\n"]
    for i, opp in enumerate(opportunities, 1):
        lines.append(
            f"#{i} [{opp.get('tier','C')}] `{opp.get('niche','')}` — score {opp.get('opportunity_score',0)}"
        )
    lines.append("\n_Review and approve before posting._")
    text = "\n".join(lines)

    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        timeout=10,
    )
    if resp.ok:
        log.info("Sent to Telegram.")
    else:
        log.warning("Telegram post failed: %s", resp.text)


def _cmd_analyze_business(args: argparse.Namespace) -> None:
    url = args.url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    print(f"NeighborIQ — Analyzing business at {url}...")
    print()
    try:
        from neighboriq.analyzers.domain_analyzer import analyze_domain, format_domain_analysis
        analysis = analyze_domain(url)
        print(format_domain_analysis(analysis))
    except ImportError as exc:
        log.error("domain_analyzer not available: %s", exc)
    except Exception as exc:
        log.error("Business analysis failed: %s", exc, exc_info=True)


def _cmd_stats(args: argparse.Namespace) -> None:
    from storage.market_db import MarketDB
    db = MarketDB()
    stats = db.get_stats()
    print()
    print("NeighborIQ — Database Stats")
    print("━" * 40)
    print(f"  Neighborhoods analyzed : {stats.get('total_neighborhoods', 0)}")
    print(f"  Businesses indexed     : {stats.get('total_businesses', 0)}")
    print(f"  Opportunities found    : {stats.get('total_opportunities', 0)}")
    print(f"  Tier A opportunities   : {stats.get('tier_a_count', 0)}")
    print()


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="neighboriq",
        description="NeighborIQ — Neighborhood Business Intelligence Engine",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # analyze
    p_analyze = sub.add_parser("analyze", help="Analyze a zip code for business opportunities")
    p_analyze.add_argument("--zip", required=True, help="US zip code to analyze")
    p_analyze.add_argument("--radius", type=float, default=1.5, help="Search radius in miles (default 1.5)")
    p_analyze.add_argument("--no-llm", action="store_true", help="Skip LLM deep evaluation")
    p_analyze.add_argument("--no-cache", action="store_true", help="Ignore cached data")
    p_analyze.add_argument(
        "--output",
        choices=["table", "json", "report"],
        default="table",
        help="Output format (default: table)",
    )
    p_analyze.add_argument(
        "--depth",
        choices=["table", "full"],
        default="table",
        help="Analysis depth: table=quick scores, full=P&L + automation + staffing (default: table)",
    )
    p_analyze.add_argument(
        "--assets",
        default=None,
        help='JSON of owner assets, e.g. \'{"capital_usd":20000,"skills":["hair_cutting"],"has_vehicle":true}\'',
    )

    # compare
    p_compare = sub.add_parser("compare", help="Compare multiple zip codes")
    p_compare.add_argument("--zips", required=True, help="Comma-separated zip codes")

    # content
    p_content = sub.add_parser("content", help="Generate YouTube script for a niche")
    p_content.add_argument("--zip", required=True, help="Zip code")
    p_content.add_argument("--niche", required=True, help="Business niche (e.g. indian_restaurant)")

    # run
    p_run = sub.add_parser("run", help="Full pipeline: analyze + generate content")
    p_run.add_argument("--zip", required=True, help="Zip code")
    p_run.add_argument("--post", action="store_true", help="Send results to Telegram for review")

    # stats
    sub.add_parser("stats", help="Show database statistics")

    # analyze-business
    p_biz = sub.add_parser("analyze-business", help="Audit any business website for revenue gaps")
    p_biz.add_argument("--url", required=True, help="Business website URL")
    p_biz.add_argument("--zip", default="", help="Override zip code if page detection fails")

    args = parser.parse_args()

    dispatch = {
        "analyze": _cmd_analyze,
        "compare": _cmd_compare,
        "content": _cmd_content,
        "run": _cmd_run,
        "stats": _cmd_stats,
        "analyze-business": _cmd_analyze_business,
    }
    try:
        dispatch[args.command](args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)
    except Exception as exc:
        log.error("Fatal: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
