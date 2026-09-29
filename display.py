"""display.py — Rich output formatting for NeighborIQ analyze command."""
from __future__ import annotations

__all__ = [
    "print_opportunity_table",
    "print_full_analysis",
    "print_asset_filter",
    "print_llm_analysis",
    "format_demographics_box",
]

try:
    from neighboriq.scoring.revenue_model import get_revenue_model
    from neighboriq.scoring.automation_matrix import get_automation_blueprint
    _HAS_MODELS = True
except ImportError:
    _HAS_MODELS = False

try:
    from neighboriq.analyzers.asset_mapper import filter_by_assets, parse_asset_profile_from_dict  # noqa: F401
    _HAS_ASSETS = True
except ImportError:
    _HAS_ASSETS = False

_W = 57  # display width


def _bar(score: float, width: int = 10) -> str:
    filled = round(score / 100 * width)
    return "█" * filled + "░" * (width - filled)


def _fmt_currency(n: int) -> str:
    return f"${n:,}"


def _fmt_mo(n: int) -> str:
    return f"${n:,}/mo"


def _sep(char: str = "━") -> None:
    print(char * _W)


def format_demographics_box(demographics: dict) -> list[str]:
    city = demographics.get("city", "")
    state = demographics.get("state", "")
    loc = f"{city}, {state}".strip(", ")
    pop = demographics.get("population", 0)
    income = demographics.get("median_income", 0)
    age = demographics.get("age_median", 0)
    lines = [loc]
    if pop:
        lines.append(f"Population: {pop:,}  ·  Median income: {_fmt_currency(income)}  ·  Median age: {age}")
    return lines


# ── quick table ──────────────────────────────────────────────────────────────

def print_opportunity_table(opportunities: list[dict], top: int = 10) -> None:
    print()
    print("TOP OPPORTUNITIES")
    _sep()
    for i, opp in enumerate(opportunities[:top], 1):
        tier = opp.get("tier", "C")
        niche = opp.get("niche", "").replace("_", " ").title()
        score = opp.get("opportunity_score", 0)
        sat = opp.get("saturation_ratio", 0.0)
        demand = opp.get("demand_score", 0)
        count = opp.get("competitor_count", 0)
        rating = opp.get("competitor_avg_rating", 0.0)
        capital = opp.get("typical_capital_req", 0)

        gap_display = f"{1.0 / sat:.1f}x undersupply" if sat and sat > 0 else "∞ gap"
        rating_display = f"avg {rating:.1f}★" if rating > 0 else "no ratings"
        capital_display = f"~{_fmt_currency(capital)}" if capital else "n/a"

        print(f"#{i} [{tier}] {niche:<30}  Score: {score}  Demand: {demand}/100")
        print(f"     {count} existing  ·  {gap_display}  ·  {rating_display}  ·  Entry: {capital_display}")
        print()


# ── full depth analysis ──────────────────────────────────────────────────────

def _print_market_gap(opp: dict) -> None:
    sat = opp.get("saturation_ratio", 0.0)
    count = opp.get("competitor_count", 0)
    rating = opp.get("competitor_avg_rating", 0.0)
    capital = opp.get("typical_capital_req", 0)
    gap_str = f"{1.0 / sat:.1f}x undersupply" if sat and sat > 0 else "∞ (no competition)"
    rating_str = f"Avg rating: {rating:.1f}/5" if rating > 0 else "No rating data"
    print("MARKET GAP")
    print(f"  Existing: {count} businesses  ·  {rating_str}")
    print(f"  Gap: {gap_str}  ·  Entry capital: ~{_fmt_currency(capital)} (small storefront)")
    print()


def _print_revenue_model(niche: str, demographics: dict) -> None:
    if not _HAS_MODELS:
        print("  [revenue_model module not loaded — run from neighboriq directory]")
        return
    m = get_revenue_model(niche, demographics)
    med = m.revenue_median
    cogs_amt = int(med * m.cogs_pct / 100)
    print("REVENUE MODEL  (low / median / high per month)")
    print(f"  Revenue:          {_fmt_mo(m.revenue_conservative)} – {_fmt_mo(m.revenue_median)} – {_fmt_mo(m.revenue_optimistic)}")
    print(f"  COGS:             {m.cogs_pct:.0f}%  →  {_fmt_currency(cogs_amt)} direct costs at median")
    print(f"  Rent (mid):       {_fmt_mo(m.rent_monthly_mid)}")
    print(f"  Utilities:        {_fmt_mo(m.utilities_monthly)}")
    print(f"  {'─' * 45}")
    print(f"  Net — solo owner: {_fmt_mo(int(med * m.net_margin_solo_pct / 100))}  ({m.net_margin_solo_pct:.0f}% margin)")
    print(f"  Net — 1 employee: {_fmt_mo(int(med * m.net_margin_1staff_pct / 100))}  ({m.net_margin_1staff_pct:.0f}% margin)")
    print(f"  Payback (small):  {m.payback_solo_months} mo solo  ·  {m.payback_1staff_months} mo with employee")
    print(f"  Automation saves: {_fmt_mo(m.automation_monthly_savings)}")
    print()
    print("STAFFING MODEL")
    print(f"  Solo:    {m.model_solo_description}")
    print(f"  1 staff: {m.model_1staff_description}")
    print(f"  2 staff: {m.model_2staff_description}")
    print(f"  Margin tier: {m.margin_tier.upper()}")
    print()


def _print_automation(niche: str) -> None:
    if not _HAS_MODELS:
        return
    bp = get_automation_blueprint(niche)
    auto_tasks = " · ".join(bp.automated_tasks[:4]) or "none"
    human_tasks = " · ".join(bp.human_tasks[:3]) or "none"
    tool_strs = [f"{t['tool']} (${t['cost_mo']}/mo)" if t.get('cost_mo') else t['tool']
                 for t in list(bp.recommended_tools)[:3]]
    tools_str = " · ".join(tool_strs)
    print(f"AUTOMATION STACK  (score: {bp.automation_score}/100  ·  {bp.automation_pct * 100:.0f}% ops automated)")
    print(f"  Automate:  {auto_tasks}")
    print(f"  Human:     {human_tasks}")
    print(f"  Tools:     {tools_str}")
    print(f"  Staffing:  {bp.staff_with_automation}")
    print(f"  Saves:     {_fmt_mo(bp.monthly_savings_usd)}")
    print()


def _print_escalation(niche: str) -> None:
    if not _HAS_MODELS:
        return
    m = get_revenue_model(niche, {})
    print("LOW → HIGH MARGIN PATH")
    for line in m.escalation_path.split("→"):
        line = line.strip()
        if line:
            print(f"  → {line}")
    print()


def print_full_analysis(
    opportunities: list[dict],
    demographics: dict,
    top: int = 5,
) -> None:
    print()
    for i, opp in enumerate(opportunities[:top], 1):
        niche = opp.get("niche", "")
        niche_title = niche.replace("_", " ").upper()
        tier = opp.get("tier", "C")
        score = opp.get("opportunity_score", 0)
        demand = opp.get("demand_score", 0)

        _sep()
        print(f"#{i} [{tier}] {niche_title}  ·  Score: {score}  ·  Demand: {demand}/100")
        _sep()
        print()
        _print_market_gap(opp)
        _print_revenue_model(niche, demographics)
        _print_automation(niche)
        _print_escalation(niche)


# ── asset filter display ─────────────────────────────────────────────────────

def print_asset_filter(feasibility_results: list) -> None:
    if not feasibility_results:
        print("\nNo feasibility results to display.")
        return
    print()
    print("FEASIBILITY FILTER (based on your assets)")
    _sep()
    print()
    for i, r in enumerate(feasibility_results, 1):
        niche = r.niche.replace("_", " ").upper()
        print(f"#{i}  {niche}  ·  Feasibility: {r.feasibility_score}  ·  Combined: {r.combined_score}")
        print(f"    Capital:  {r.capital_fit.upper()}  ·  Skill match: {_bar(r.skill_match * 100)} {r.skill_match * 100:.0f}%")
        print(f"    Entry:    {r.recommended_entry_tier.replace('_', ' ')}")
        print()
        if r.what_you_have:
            print(f"    YOU HAVE:  {' · '.join(r.what_you_have)}")
        if r.what_you_need:
            print(f"    YOU NEED:  {' · '.join(r.what_you_need)}")
        print()
        if r.first_30_days:
            print("    FIRST 30 DAYS:")
            for line in r.first_30_days.split(". "):
                line = line.strip().rstrip(".")
                if line:
                    print(f"    {line}.")
        print()
        if r.low_to_high_path:
            print("    LOW → HIGH:")
            snippet = r.low_to_high_path[:200]
            print(f"    {snippet}{'...' if len(r.low_to_high_path) > 200 else ''}")
        _sep("─")
        print()


# ── LLM analysis display ─────────────────────────────────────────────────────

def print_llm_analysis(llm_analysis: dict) -> None:
    if not isinstance(llm_analysis, dict):
        return
    summary = llm_analysis.get("market_summary", "")
    strategy = llm_analysis.get("entry_strategy", "")
    risks = llm_analysis.get("critical_risks", [])
    source = llm_analysis.get("source", "")
    if not (summary or strategy):
        return
    print()
    print(f"LLM ANALYSIS  (source: {source})")
    _sep()
    if summary:
        print(f"  {summary}")
        print()
    if strategy:
        print("  ENTRY STRATEGY:")
        print(f"  {strategy}")
        print()
    if risks:
        print("  RISKS:")
        for r in risks:
            print(f"  • {r}")
    print()
