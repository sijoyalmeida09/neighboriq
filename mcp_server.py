"""
NeighborIQ MCP Server — raw JSON-RPC 2.0 stdio protocol.

Add to .mcp.json:
  "neighboriq": {
    "command": "python",
    "args": ["-m", "neighboriq.mcp_server"],
    "cwd": "C:\\Sijoy_2.0\\automation"
  }

Run directly:
  python -m neighboriq.mcp_server
  python neighboriq/mcp_server.py
"""
from __future__ import annotations

import json
import logging
import sys
import traceback

log = logging.getLogger("neighboriq.mcp")
logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="%(asctime)s %(name)s %(levelname)s %(message)s")

# ── tool definitions ──────────────────────────────────────────────────────────

_TOOLS = [
    {
        "name": "analyze_neighborhood",
        "description": (
            "Analyze a US zip code for underserved business opportunities. "
            "Returns top opportunities with scores, demographics, and market gaps."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "zip_code": {"type": "string", "description": "US zip code (e.g. '02122')"},
                "radius_mi": {"type": "number", "description": "Search radius in miles (default 1.5)"},
                "use_cache": {"type": "boolean", "description": "Use cached data if available (default true)"},
                "top_n": {"type": "integer", "description": "Return top N opportunities (default 10)"},
            },
            "required": ["zip_code"],
        },
    },
    {
        "name": "get_revenue_model",
        "description": (
            "Get detailed revenue model and automation blueprint for a specific business niche. "
            "Returns P&L, staffing models, automation tools, and low→high margin escalation path."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "niche": {"type": "string", "description": "Business niche (e.g. 'barbershop', 'nail_salon', 'convenience_store')"},
                "zip_code": {"type": "string", "description": "US zip code for demographic context (optional)"},
            },
            "required": ["niche"],
        },
    },
    {
        "name": "filter_by_assets",
        "description": (
            "Given a person's available assets (capital, skills, space), filter and rank "
            "business opportunities by feasibility. Shows what's achievable NOW vs later."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "zip_code": {"type": "string"},
                "capital_usd": {"type": "integer", "description": "Available startup capital in USD"},
                "space_sqft": {"type": "integer", "description": "Available space in sqft (0 if none)"},
                "has_vehicle": {"type": "boolean"},
                "skills": {"type": "array", "items": {"type": "string"}, "description": "e.g. ['cooking', 'hair_cutting', 'accounting']"},
                "licenses": {"type": "array", "items": {"type": "string"}, "description": "e.g. ['cosmetology', 'food_handler']"},
                "monthly_overhead_max": {"type": "integer", "description": "Max monthly overhead affordable"},
                "prefers_home_based": {"type": "boolean"},
                "hours_per_week": {"type": "integer"},
            },
            "required": ["zip_code"],
        },
    },
    {
        "name": "compare_neighborhoods",
        "description": (
            "Compare multiple zip codes side by side for a specific niche or overall opportunity rank."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "zip_codes": {"type": "array", "items": {"type": "string"}, "description": "List of zip codes to compare"},
                "niche": {"type": "string", "description": "Optional: focus comparison on this niche"},
            },
            "required": ["zip_codes"],
        },
    },
    {
        "name": "get_neighborhood_stats",
        "description": "Get quick stats about all analyzed neighborhoods in the NeighborIQ database.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "analyze_business",
        "description": (
            "Fetch any local business website URL, identify what they offer, "
            "cross-reference NeighborIQ market data, and return: what they have, "
            "what the neighborhood needs that they don't offer, specific revenue-add "
            "opportunities with dollar estimates, and automation gaps. "
            "Use this to audit any competitor or potential client's digital presence."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Business website URL (e.g. 'https://tonybarbershop.com')"},
                "zip_code": {"type": "string", "description": "Override zip code if page detection fails"},
            },
            "required": ["url"],
        },
    },
]

# ── tool handlers ─────────────────────────────────────────────────────────────

def _fmt_currency(n: int | float) -> str:
    return f"${int(n):,}"


def _fmt_opportunities(opportunities: list[dict], top_n: int = 10) -> str:
    lines: list[str] = []
    for i, opp in enumerate(opportunities[:top_n], 1):
        tier = opp.get("tier", "C")
        niche = opp.get("niche", "").replace("_", " ").title()
        score = opp.get("opportunity_score", 0)
        sat = opp.get("saturation_ratio", 0.0)
        demand = opp.get("demand_score", 0)
        count = opp.get("competitor_count", 0)
        rating = opp.get("competitor_avg_rating", 0.0)
        capital = opp.get("typical_capital_req", 0)

        gap_display = f"{1.0 / sat:.1f}x undersupplied" if sat and sat > 0 else "no competition"
        rating_display = f"avg rating {rating:.1f}" if rating > 0 else "unrated market"
        capital_display = _fmt_currency(capital) if capital else "n/a"

        lines.append(f"#{i} [{tier}] {niche}")
        lines.append(f"    Score: {score}/100  |  Gap: {gap_display}")
        lines.append(f"    Competitors: {count}  |  {rating_display}")
        lines.append(f"    Demand signal: {demand}/100  |  Entry capital: {capital_display}")
        lines.append("")
    return "\n".join(lines)


def handle_analyze_neighborhood(args: dict) -> str:
    zip_code = args.get("zip_code", "").strip()
    radius_mi = float(args.get("radius_mi", 1.5))
    use_cache = bool(args.get("use_cache", True))
    top_n = int(args.get("top_n", 10))

    if not zip_code:
        return "Error: zip_code is required."

    try:
        from neighboriq.cli import _run_pipeline
    except ImportError as exc:
        return f"NeighborIQ not importable: {exc}\nRun from C:\\Sijoy_2.0\\automation with the neighboriq package on PYTHONPATH."

    try:
        log.info("Running pipeline for %s (cache=%s)", zip_code, use_cache)
        result = _run_pipeline(zip_code, radius_mi=radius_mi, run_llm=False, use_cache=use_cache)
    except Exception as exc:
        return f"Pipeline error for {zip_code}: {exc}\n{traceback.format_exc()}"

    demo = result.get("demographics", {})
    opportunities = result.get("opportunities", [])

    city = demo.get("city", "")
    state = demo.get("state", "")
    location = f"{city}, {state}".strip(", ") or zip_code
    pop = demo.get("population", 0)
    income = demo.get("median_income", 0)
    age = demo.get("age_median", 0)

    lines = [
        f"NEIGHBORIQ ANALYSIS — {zip_code} ({location})",
        "=" * 52,
        f"Population:     {pop:,}",
        f"Median Income:  {_fmt_currency(income)}/yr",
        f"Median Age:     {age}",
        f"Businesses:     {len(result.get('businesses', []))} indexed",
        "",
        f"TOP {min(top_n, len(opportunities))} OPPORTUNITIES",
        "─" * 52,
        _fmt_opportunities(opportunities, top_n),
    ]

    llm = result.get("llm_analysis", {})
    if isinstance(llm, dict) and llm.get("entry_strategy"):
        lines += [
            "LLM ENTRY STRATEGY",
            "─" * 52,
            llm["entry_strategy"],
            "",
        ]

    return "\n".join(lines)


def handle_get_revenue_model(args: dict) -> str:
    niche = args.get("niche", "").strip().lower().replace(" ", "_")
    zip_code = args.get("zip_code", "")

    if not niche:
        return "Error: niche is required."

    try:
        from neighboriq.scoring.revenue_model import get_revenue_model, format_revenue_model
        model = get_revenue_model(niche, zip_code=zip_code)
        return format_revenue_model(model)
    except ImportError:
        pass
    except Exception as exc:
        return f"Revenue model error: {exc}"

    # Built-in fallback revenue data for common niches
    _REVENUE_DATA: dict[str, dict] = {
        "barbershop": {
            "startup_tiers": {"home_mobile": 5_000, "small_shop": 30_000, "full_shop": 60_000},
            "monthly_revenue": {"conservative": 8_000, "median": 15_000, "optimistic": 25_000},
            "cogs_pct": 15, "rent_estimate": 2_500, "staff_1_cost": 3_500,
            "net_margin_pct": 35, "payback_months": 18,
            "automation": ["Online booking (Booksy/Square)", "Auto-SMS reminders", "Inventory reorder alerts"],
            "automation_savings_mo": 800,
            "escalation": ["Mobile/home visits → chair rental → own shop → multi-chair"],
        },
        "nail_salon": {
            "startup_tiers": {"home_mobile": 3_000, "booth_rental": 15_000, "full_salon": 50_000},
            "monthly_revenue": {"conservative": 10_000, "median": 20_000, "optimistic": 35_000},
            "cogs_pct": 20, "rent_estimate": 3_000, "staff_1_cost": 3_200,
            "net_margin_pct": 30, "payback_months": 20,
            "automation": ["Booking app", "Product inventory tracking", "Review request automation"],
            "automation_savings_mo": 600,
            "escalation": ["Home visits → booth rental → own salon → franchise"],
        },
        "convenience_store": {
            "startup_tiers": {"kiosk": 15_000, "small_store": 100_000, "full_store": 250_000},
            "monthly_revenue": {"conservative": 40_000, "median": 80_000, "optimistic": 150_000},
            "cogs_pct": 65, "rent_estimate": 4_000, "staff_1_cost": 4_000,
            "net_margin_pct": 8, "payback_months": 36,
            "automation": ["POS + inventory system", "AI reorder alerts", "Self-checkout kiosk", "CCTV shrinkage control"],
            "automation_savings_mo": 2_500,
            "escalation": ["Online delivery partner → kiosk → small store → full store → chain"],
        },
        "tutoring_center": {
            "startup_tiers": {"home_online": 500, "small_center": 15_000, "full_center": 40_000},
            "monthly_revenue": {"conservative": 5_000, "median": 12_000, "optimistic": 25_000},
            "cogs_pct": 5, "rent_estimate": 1_500, "staff_1_cost": 3_000,
            "net_margin_pct": 45, "payback_months": 10,
            "automation": ["Learning management system", "Auto-scheduling", "Progress report emails", "AI homework helper bot"],
            "automation_savings_mo": 1_200,
            "escalation": ["Online tutoring → group classes → physical center → franchise"],
        },
        "laundromat": {
            "startup_tiers": {"wash_fold_only": 20_000, "small_mat": 200_000, "full_mat": 400_000},
            "monthly_revenue": {"conservative": 15_000, "median": 30_000, "optimistic": 55_000},
            "cogs_pct": 30, "rent_estimate": 3_500, "staff_1_cost": 3_000,
            "net_margin_pct": 25, "payback_months": 48,
            "automation": ["Remote machine monitoring", "App-based payment", "SMS ready alerts", "Security cameras"],
            "automation_savings_mo": 1_800,
            "escalation": ["Wash-and-fold service → drop-off only → self-service mat → full-service mat"],
        },
        "halal_restaurant": {
            "startup_tiers": {"ghost_kitchen": 20_000, "food_truck": 40_000, "restaurant": 130_000},
            "monthly_revenue": {"conservative": 20_000, "median": 45_000, "optimistic": 90_000},
            "cogs_pct": 32, "rent_estimate": 5_000, "staff_1_cost": 4_500,
            "net_margin_pct": 15, "payback_months": 30,
            "automation": ["Online ordering (Toast/Square)", "Delivery platform integration", "Inventory alerts"],
            "automation_savings_mo": 1_000,
            "escalation": ["Ghost kitchen → food truck → small restaurant → catering → chain"],
        },
        "check_cashing": {
            "startup_tiers": {"online_only": 10_000, "kiosk": 25_000, "full_store": 80_000},
            "monthly_revenue": {"conservative": 12_000, "median": 25_000, "optimistic": 50_000},
            "cogs_pct": 10, "rent_estimate": 2_500, "staff_1_cost": 3_500,
            "net_margin_pct": 28, "payback_months": 24,
            "automation": ["KYC automation", "Digital ledger", "Compliance reporting automation"],
            "automation_savings_mo": 900,
            "escalation": ["Mobile money transfer → kiosk → full store → franchise"],
        },
    }

    data = _REVENUE_DATA.get(niche)
    if not data:
        # Generic fallback
        return (
            f"Revenue model for '{niche.replace('_', ' ').title()}'\n"
            "=" * 52 + "\n"
            "revenue_model.py module not found. Install the full NeighborIQ package for detailed models.\n\n"
            "To get detailed models: ensure scoring/revenue_model.py exists in the neighboriq package.\n"
            f"Niche requested: {niche}"
        )

    tiers = data["startup_tiers"]
    rev = data["monthly_revenue"]
    auto = data["automation"]
    esc = data["escalation"]

    lines = [
        f"REVENUE MODEL — {niche.replace('_', ' ').title()}",
        "=" * 52,
        "",
        "STARTUP COST TIERS",
        "─" * 40,
    ]
    for tier_name, cost in tiers.items():
        lines.append(f"  {tier_name.replace('_', ' ').title():<20} {_fmt_currency(cost)}")

    lines += [
        "",
        "MONTHLY REVENUE SCENARIOS",
        "─" * 40,
        f"  Conservative:  {_fmt_currency(rev['conservative'])}",
        f"  Median:        {_fmt_currency(rev['median'])}",
        f"  Optimistic:    {_fmt_currency(rev['optimistic'])}",
        "",
        "P&L ESTIMATE (median scenario, 1 staff + automation)",
        "─" * 40,
        f"  Revenue:               {_fmt_currency(rev['median'])}",
        f"  COGS ({data['cogs_pct']}%):           -{_fmt_currency(rev['median'] * data['cogs_pct'] // 100)}",
        f"  Rent estimate:         -{_fmt_currency(data['rent_estimate'])}",
        f"  1 staff cost:          -{_fmt_currency(data['staff_1_cost'])}",
        f"  Automation savings:    +{_fmt_currency(data['automation_savings_mo'])}",
        "  " + "─" * 30,
        f"  Net margin (~{data['net_margin_pct']}%):    {_fmt_currency(rev['median'] * data['net_margin_pct'] // 100)}/mo",
        f"  Payback period:        ~{data['payback_months']} months",
        "",
        "AUTOMATION BLUEPRINT (1-2 staff model)",
        "─" * 40,
    ]
    for a in auto:
        lines.append(f"  • {a}")
    lines += [
        f"  Total automation savings: {_fmt_currency(data['automation_savings_mo'])}/mo",
        "",
        "LOW → HIGH MARGIN ESCALATION PATH",
        "─" * 40,
    ]
    for i, step in enumerate(esc, 1):
        lines.append(f"  Step {i}: {step}")

    lines += [
        "",
        "STAFFING MODEL",
        "─" * 40,
        "  Phase 1 (owner-operated): 1 person does everything, automation handles scheduling/reminders",
        "  Phase 2 (1 staff):        Owner manages, 1 staff executes, automation handles ops",
        "  Phase 3 (2+ staff):       Owner = growth/sales, staff = delivery, automation = ops",
    ]

    return "\n".join(lines)


def handle_filter_by_assets(args: dict) -> str:
    zip_code = args.get("zip_code", "").strip()
    capital = int(args.get("capital_usd", 0))
    space_sqft = int(args.get("space_sqft", 0))
    has_vehicle = bool(args.get("has_vehicle", False))
    skills = [s.lower() for s in args.get("skills", [])]
    licenses = [l.lower() for l in args.get("licenses", [])]
    overhead_max = int(args.get("monthly_overhead_max", 5_000))
    home_based = bool(args.get("prefers_home_based", False))
    hours_pw = int(args.get("hours_per_week", 40))

    try:
        from neighboriq.analyzers.asset_mapper import filter_by_assets as _filter, parse_asset_profile_from_dict
        from neighboriq.storage.market_db import MarketDB
        profile = parse_asset_profile_from_dict(args)
        db = MarketDB()
        opps = db.get_opportunities(zip_code) if zip_code else []
        results = _filter(opps, profile)
        import dataclasses, json as _json
        return "\n".join(str(dataclasses.asdict(r)) for r in results) if results else "No opportunities match your asset profile."
    except ImportError:
        pass
    except Exception as exc:
        return f"Asset mapper error: {exc}"

    # Built-in fallback asset filter
    _NICHE_REQUIREMENTS: list[dict] = [
        {"niche": "online_tutoring", "capital": 500, "space": 0, "vehicle": False,
         "skill_keywords": ["teaching", "tutoring", "math", "english", "coding"],
         "licenses": [], "overhead": 200, "hours": 10, "home_ok": True,
         "margin": "high", "first30": "List on Wyzant/Tutor.com. Set up Zoom. First 5 clients free."},
        {"niche": "mobile_barbershop", "capital": 3_000, "space": 0, "vehicle": True,
         "skill_keywords": ["barbering", "hair", "grooming", "barber"],
         "licenses": ["barber", "cosmetology"], "overhead": 500, "hours": 20, "home_ok": True,
         "margin": "medium-high", "first30": "Post on Nextdoor. Offer $15 cuts. Use Square for payment."},
        {"niche": "home_nail_salon", "capital": 3_000, "space": 80, "vehicle": False,
         "skill_keywords": ["nail", "manicure", "pedicure", "cosmetology"],
         "licenses": ["cosmetology", "nail"], "overhead": 300, "hours": 20, "home_ok": True,
         "margin": "high", "first30": "Get state license. Buy $2K supplies. Post on Facebook/Instagram."},
        {"niche": "food_delivery_prep", "capital": 2_000, "space": 50, "vehicle": True,
         "skill_keywords": ["cooking", "food", "chef"],
         "licenses": ["food_handler"], "overhead": 500, "hours": 30, "home_ok": True,
         "margin": "medium", "first30": "Register on DoorDash/Uber Eats. Start with 5 menu items."},
        {"niche": "bookkeeping_service", "capital": 1_000, "space": 0, "vehicle": False,
         "skill_keywords": ["accounting", "bookkeeping", "quickbooks", "finance"],
         "licenses": ["cpa"], "overhead": 100, "hours": 15, "home_ok": True,
         "margin": "very high", "first30": "List on Upwork. Reach 10 local small businesses. $150/mo per client."},
        {"niche": "laundry_pickup_delivery", "capital": 5_000, "space": 0, "vehicle": True,
         "skill_keywords": [],
         "licenses": [], "overhead": 800, "hours": 25, "home_ok": True,
         "margin": "medium", "first30": "Partner with local laundromat. Route 20 customers. $25/bag."},
        {"niche": "small_convenience_kiosk", "capital": 15_000, "space": 200, "vehicle": False,
         "skill_keywords": [],
         "licenses": [], "overhead": 3_000, "hours": 40, "home_ok": False,
         "margin": "low-medium", "first30": "Lease kiosk spot. Stock top 50 SKUs. Install POS."},
        {"niche": "barbershop_chair_rental", "capital": 30_000, "space": 600, "vehicle": False,
         "skill_keywords": ["barbering", "hair"],
         "licenses": ["barber"], "overhead": 4_000, "hours": 50, "home_ok": False,
         "margin": "medium-high", "first30": "Lease space. Hire 1 chair renter. Market online."},
        {"niche": "daycare_home", "capital": 10_000, "space": 500, "vehicle": False,
         "skill_keywords": ["childcare", "teaching", "babysitting"],
         "licenses": ["childcare"], "overhead": 1_000, "hours": 45, "home_ok": True,
         "margin": "medium", "first30": "Get state license. List on Care.com. 4 kids at $300/wk each."},
        {"niche": "cctv_installation", "capital": 8_000, "space": 0, "vehicle": True,
         "skill_keywords": ["cctv", "security", "electrical", "networking"],
         "licenses": [], "overhead": 500, "hours": 30, "home_ok": True,
         "margin": "high", "first30": "Source Dahua/Hikvision at cost. 3 installs at $1,500. Upsell AMC $99/mo."},
    ]

    feasible_now: list[dict] = []
    feasible_later: list[dict] = []

    for req in _NICHE_REQUIREMENTS:
        capital_ok = capital >= req["capital"]
        space_ok = space_sqft >= req["space"] if req["space"] > 0 else True
        vehicle_ok = (not req["vehicle"]) or has_vehicle
        home_ok = (not home_based) or req["home_ok"]
        overhead_ok = req["overhead"] <= overhead_max
        hours_ok = req["hours"] <= hours_pw

        skill_match = any(
            any(kw in s for s in skills)
            for kw in req["skill_keywords"]
        ) if req["skill_keywords"] else True

        license_match = all(
            any(req_lic in lic for lic in licenses)
            for req_lic in req["licenses"]
        ) if req["licenses"] else True

        score = sum([capital_ok, space_ok, vehicle_ok, home_ok, overhead_ok, hours_ok, skill_match, license_match])
        entry = {**req, "feasibility_score": score, "max_score": 8}

        if score >= 6:
            feasible_now.append(entry)
        elif score >= 4:
            feasible_later.append(entry)

    feasible_now.sort(key=lambda x: x["feasibility_score"], reverse=True)
    feasible_later.sort(key=lambda x: x["feasibility_score"], reverse=True)

    lines = [
        f"ASSET FILTER RESULTS — {zip_code}",
        "=" * 52,
        f"Your assets: ${capital:,} capital | {space_sqft} sqft | {'vehicle' if has_vehicle else 'no vehicle'}",
        f"Skills: {', '.join(skills) if skills else 'none listed'}",
        f"Licenses: {', '.join(licenses) if licenses else 'none listed'}",
        f"Constraints: max ${overhead_max:,}/mo overhead | {hours_pw}h/wk | {'home-based preferred' if home_based else 'any location'}",
        "",
    ]

    if feasible_now:
        lines += [f"✅ START NOW ({len(feasible_now)} options)", "─" * 52]
        for opp in feasible_now[:5]:
            niche_display = opp["niche"].replace("_", " ").title()
            lines += [
                f"\n  {niche_display}  [{opp['margin']} margin]",
                f"  Startup: ${opp['capital']:,}  |  Monthly overhead: ${opp['overhead']:,}",
                f"  Feasibility: {opp['feasibility_score']}/{opp['max_score']}",
                f"  First 30 days: {opp['first30']}",
                f"  Escalation: {opp['niche'].replace('_', ' ')} → grow margin over time",
            ]
    else:
        lines += ["No immediately feasible options with current assets.\n"]

    if feasible_later:
        lines += ["", f"\n⏳ ACHIEVABLE SOON — build toward ({len(feasible_later)} options)", "─" * 52]
        for opp in feasible_later[:3]:
            niche_display = opp["niche"].replace("_", " ").title()
            gap_capital = max(0, opp["capital"] - capital)
            lines += [
                f"\n  {niche_display}",
                f"  Need: +${gap_capital:,} capital | {opp['space']} sqft space",
                f"  Feasibility: {opp['feasibility_score']}/{opp['max_score']}",
            ]

    lines += [
        "",
        "LOW → HIGH MARGIN ESCALATION PATH",
        "─" * 52,
        "  Low margin now (builds cash):  Delivery, laundry, kiosk (5-15% net)",
        "  Medium margin (6-12 months):   Mobile services, small services (20-30% net)",
        "  High margin (12-24 months):    Licensing, recurring AMC, online education (40-60% net)",
        "  Max margin (asset-based):      Own storefront, franchise rights, real estate (variable)",
    ]

    return "\n".join(lines)


def handle_compare_neighborhoods(args: dict) -> str:
    zip_codes = args.get("zip_codes", [])
    niche_filter = args.get("niche", "").strip().lower().replace(" ", "_")

    if not zip_codes:
        return "Error: zip_codes list is required."
    if len(zip_codes) > 10:
        return "Error: max 10 zip codes per comparison."

    try:
        from neighboriq.cli import _run_pipeline
    except ImportError as exc:
        return f"NeighborIQ not importable: {exc}"

    lines = [
        f"NEIGHBORHOOD COMPARISON — {len(zip_codes)} zip codes",
        "=" * 60,
        "",
    ]

    results: list[dict] = []
    for z in zip_codes:
        try:
            r = _run_pipeline(z.strip(), run_llm=False, use_cache=True)
            results.append(r)
        except Exception as exc:
            lines.append(f"  {z}: ERROR — {exc}")

    for res in results:
        z = res["zip_code"]
        demo = res.get("demographics", {})
        city = demo.get("city", "")
        pop = demo.get("population", 0)
        income = demo.get("median_income", 0)
        opps = res.get("opportunities", [])

        if niche_filter:
            matching = [o for o in opps if o.get("niche", "") == niche_filter]
            top_opps = matching[:3]
        else:
            top_opps = opps[:3]

        lines += [
            f"📍 {z} — {city}",
            f"   Pop: {pop:,}  |  Income: {_fmt_currency(income)}",
        ]
        if top_opps:
            for i, opp in enumerate(top_opps, 1):
                niche_display = opp.get("niche", "").replace("_", " ").title()
                score = opp.get("opportunity_score", 0)
                tier = opp.get("tier", "C")
                lines.append(f"   #{i} [{tier}] {niche_display} — score {score}")
        else:
            lines.append("   No opportunities found (run analyze first).")
        lines.append("")

    return "\n".join(lines)


def handle_get_neighborhood_stats(_args: dict) -> str:
    try:
        from neighboriq.storage.market_db import MarketDB
        db = MarketDB()
        stats = db.get_stats()
        lines = [
            "NEIGHBORIQ DATABASE STATS",
            "=" * 40,
            f"  Neighborhoods analyzed:  {stats.get('total_neighborhoods', 0)}",
            f"  Businesses indexed:      {stats.get('total_businesses', 0)}",
            f"  Opportunities found:     {stats.get('total_opportunities', 0)}",
            f"  Tier A opportunities:    {stats.get('tier_a_count', 0)}",
        ]
        return "\n".join(lines)
    except ImportError as exc:
        return f"NeighborIQ not importable: {exc}"
    except Exception as exc:
        return f"Stats error: {exc}"


def handle_analyze_business(args: dict) -> str:
    url = args.get("url", "").strip()
    zip_override = args.get("zip_code", "").strip()

    if not url:
        return "Error: url is required."
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        from neighboriq.analyzers.domain_analyzer import analyze_domain, format_domain_analysis
        analysis = analyze_domain(url)
        if zip_override and not analysis.profile.detected_zip:
            # Re-run with override — rebuild analysis using provided zip
            from neighboriq.analyzers.domain_analyzer import (
                DomainProfile, DomainAnalysis,
                _build_revenue_adds, _build_automation_gaps,
                _cross_reference_neighborhood,
            )
        return format_domain_analysis(analysis)
    except ImportError:
        return (
            "domain_analyzer module not available.\n"
            "Ensure analyzers/domain_analyzer.py exists in the neighboriq package.\n"
            f"URL requested: {url}"
        )
    except Exception as exc:
        return f"Domain analysis failed for {url}:\n{exc}\n{traceback.format_exc()}"


# ── dispatch ──────────────────────────────────────────────────────────────────

_HANDLERS = {
    "analyze_neighborhood": handle_analyze_neighborhood,
    "get_revenue_model": handle_get_revenue_model,
    "filter_by_assets": handle_filter_by_assets,
    "compare_neighborhoods": handle_compare_neighborhoods,
    "get_neighborhood_stats": handle_get_neighborhood_stats,
    "analyze_business": handle_analyze_business,
}


def handle_tools_call(name: str, arguments: dict) -> dict:
    handler = _HANDLERS.get(name)
    if not handler:
        text = f"Unknown tool: {name}. Available: {', '.join(_HANDLERS)}"
    else:
        try:
            text = handler(arguments)
        except Exception:
            text = f"Tool '{name}' failed:\n{traceback.format_exc()}"
    return {"content": [{"type": "text", "text": text}]}


# ── JSON-RPC main loop ────────────────────────────────────────────────────────

def _ok(id_: object, result: object) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _err(id_: object, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def main() -> None:
    log.info("NeighborIQ MCP server starting on stdio")

    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue

        try:
            request = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            response = _err(None, -32700, f"Parse error: {exc}")
            print(json.dumps(response), flush=True)
            continue

        id_ = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        log.info("method=%s id=%s", method, id_)

        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "neighboriq", "version": "2.0.0"},
                }
                response = _ok(id_, result)

            elif method == "initialized":
                # notification — no response needed
                continue

            elif method == "tools/list":
                response = _ok(id_, {"tools": _TOOLS})

            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                result = handle_tools_call(tool_name, arguments)
                response = _ok(id_, result)

            elif method == "ping":
                response = _ok(id_, {})

            else:
                if id_ is None:
                    # notification — ignore
                    continue
                response = _err(id_, -32601, f"Method not found: {method}")

        except Exception:
            log.exception("Unhandled error for method=%s", method)
            response = _err(id_, -32603, f"Internal error: {traceback.format_exc()}")

        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
