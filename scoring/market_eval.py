"""market_eval.py — LLM deep evaluation of neighborhood business opportunities.

Provider failover: Groq (llama-3.3-70b) → Anthropic (claude-haiku-4-5-20251001) → template.
Pattern adapted from job_hunter_v2/deep_eval.py.
"""
from __future__ import annotations

import json
import logging
import os
import re

log = logging.getLogger("market_eval")

_SYSTEM = """You are a top-tier small business intelligence analyst with 20 years of experience opening businesses in underserved urban neighborhoods. You have opened barbershops in Dorchester, laundromats in Mattapan, halal restaurants in Queens, and convenience stores in South Boston. You give SPECIFIC dollar figures, not ranges. You name exact tools, vendors, and suppliers. You identify exact revenue per unit. You never say "varies" — you give your best estimate with a confidence flag. Respond in valid JSON only."""

_RESPONSE_SCHEMA = """{
  "market_summary": "2-sentence character read of this neighborhood — who lives here, what they spend money on",
  "top_opportunities": [
    {
      "niche": "niche_name",
      "score": 0,
      "why_here": "One sentence: what specific demographic or gap makes this niche work HERE",
      "monthly_revenue_estimate": 12000,
      "net_margin_pct": 35,
      "monthly_net_income": 4200,
      "startup_cost_minimum": 30000,
      "payback_months": 7,
      "first_customer_in_days": 14,
      "automation_stack": ["Calendly for booking", "Square POS", "Twilio review requests"],
      "staff_needed": "1 owner-operator, no employees year 1",
      "biggest_risk": "One sentence: the #1 thing that kills this business here"
    }
  ],
  "immediate_action": "The ONE thing to do in the next 7 days to validate the top opportunity before spending any money",
  "asset_needed_for_top": "The single most important asset/license/skill to acquire first",
  "neighborhood_insider_edge": "What cultural or community knowledge gives an insider a 2x advantage here"
}"""


def _call_groq(prompt: str) -> str | None:
    try:
        import groq  # type: ignore[import]
        client = groq.Groq(api_key=os.environ["GROQ_API_KEY"])
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        return resp.choices[0].message.content
    except Exception as exc:
        log.warning("Groq failed: %s", exc)
        return None


def _call_anthropic(prompt: str) -> str | None:
    try:
        import anthropic  # type: ignore[import]
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except Exception as exc:
        log.warning("Anthropic failed: %s", exc)
        return None


def _extract_json(raw: str) -> dict | None:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError as exc:
        log.warning("JSON parse error: %s", exc)
        return None


def _template_fallback(demographics: dict, top_opportunities: list[dict]) -> dict:
    pop = demographics.get("population", 0)
    income = demographics.get("median_income", 0)
    top3 = top_opportunities[:3]

    def _opp_to_template(o: dict) -> dict:
        niche = o.get("niche", "unknown")
        score = o.get("opportunity_score", o.get("score", 0))
        capital = o.get("typical_capital_req", 80_000)
        demand = o.get("demand_score", 50)
        sat = o.get("saturation_ratio", 1.0)
        gap_label = "undersupplied" if sat < 0.8 else ("at capacity" if sat < 1.5 else "oversupplied")
        return {
            "niche": niche,
            "score": score,
            "why_here": (
                f"Data model shows {gap_label} supply (ratio {sat:.2f}x benchmark) "
                f"with demand score {demand}/100 for {niche.replace('_', ' ')} in this zip."
            ),
            "monthly_revenue_estimate": max(8_000, int(income * 0.15)),
            "net_margin_pct": 28,
            "monthly_net_income": max(2_000, int(income * 0.04)),
            "startup_cost_minimum": capital,
            "payback_months": max(6, capital // max(1, int(income * 0.04))),
            "first_customer_in_days": 21,
            "automation_stack": ["Square POS (free)", "Calendly free tier", "Google Business Profile"],
            "staff_needed": "1 owner-operator, no employees year 1",
            "biggest_risk": "Insufficient foot traffic — validate location with 30-day pop-up before signing lease.",
        }

    return {
        "market_summary": (
            f"Neighborhood with {pop:,} residents and median income ${income:,}. "
            "Data model identifies supply-demand gaps — LLM analysis unavailable, using computed fallback."
        ),
        "top_opportunities": [_opp_to_template(o) for o in top3],
        "immediate_action": (
            "Spend 2 hours walking the zip code at 10am and 6pm on a weekday. "
            "Count foot traffic at the top-scored niche's closest competitor."
        ),
        "asset_needed_for_top": "Local business license + $500 deposit on a shared/sublease space to test demand.",
        "neighborhood_insider_edge": (
            "Know the dominant community language and cultural buying patterns — "
            "insider referrals from a community anchor (mosque, church, community center) cut CAC to near zero."
        ),
        "source": "template_fallback",
    }


def evaluate_neighborhood(
    zip_code: str,
    demographics: dict,
    top_opportunities: list[dict],
    businesses: list[dict] | None = None,
    city: str = "",
) -> dict:
    """
    Returns dict with keys:
        market_summary, top_opportunities, critical_risks, entry_strategy, source
    """
    pop = demographics.get("population", 0)
    income = demographics.get("median_income", 0)
    age = demographics.get("age_median", 0)
    biz_list: list[dict] = businesses or []

    # Build competitor snapshot: top 5 rated + bottom 5 rated per top niche
    top_niche = top_opportunities[0].get("niche", "") if top_opportunities else ""
    niche_biz = [b for b in biz_list if b.get("niche") == top_niche][:10]
    competitor_lines = [
        f"{b.get('name','?')} ⭐{b.get('rating', 0):.1f} ({b.get('review_count', 0)} reviews)"
        for b in sorted(niche_biz, key=lambda x: x.get("rating", 0), reverse=True)[:5]
    ]
    competitor_str = "\n".join(competitor_lines) if competitor_lines else "No competitors found in DB"

    # Saturation signal for top opportunity
    if top_opportunities:
        top = top_opportunities[0]
        sat_ratio = top.get("saturation_ratio", 1.0)
        count = top.get("competitor_count", 0)
        sat_signal = f"{count} {top_niche.replace('_',' ')}s for {pop:,} residents = {sat_ratio:.2f}x national benchmark"
    else:
        sat_signal = "No saturation data available"

    prompt = f"""Analyze this neighborhood and identify the BEST specific business to open here. Give EXACT dollar figures — no ranges, no "varies".

ZIP Code: {zip_code}
City/State: {demographics.get('city', '')} {demographics.get('state', '')}

Demographics:
- Population: {pop:,}
- Median Household Income: ${income:,}/yr
- Median Age: {age}
- Growth Rate (5yr): {demographics.get('growth_rate_5yr', 0):.1f}%

Market Gap Signal (top niche):
{sat_signal}

Top Existing Competitors in top niche:
{competitor_str}

Top Scored Opportunities (by supply/demand/sentiment model):
{json.dumps(top_opportunities[:5], indent=2)}

Total businesses scraped in this zip: {len(biz_list)}

Respond with ONLY this JSON structure:
{_RESPONSE_SCHEMA}"""

    source = "template_fallback"
    raw: str | None = None

    groq_result = _call_groq(prompt)
    if groq_result:
        raw = groq_result
        source = "groq"
    else:
        anthropic_result = _call_anthropic(prompt)
        if anthropic_result:
            raw = anthropic_result
            source = "anthropic"

    if raw:
        parsed = _extract_json(raw)
        if parsed:
            parsed["source"] = source
            return parsed
        log.warning("LLM returned unparseable JSON from %s; falling back to template", source)

    return _template_fallback(demographics, top_opportunities)
