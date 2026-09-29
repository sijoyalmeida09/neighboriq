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

_SYSTEM = """You are a top business analyst specializing in neighborhood market intelligence.
You analyze demographic data, competitor density, and demand signals to identify underserved business niches.
Your goal: find the ONE specific type of business that has the highest probability of success in this neighborhood.
Always respond in valid JSON only."""

_RESPONSE_SCHEMA = """{
  "market_summary": "2-sentence description of this neighborhood's character and opportunity",
  "top_opportunities": [
    {"niche": "niche_name", "score": 0-100, "reasoning": "Why this niche will succeed here in 1 sentence"},
    {"niche": "niche_name", "score": 0-100, "reasoning": "..."},
    {"niche": "niche_name", "score": 0-100, "reasoning": "..."}
  ],
  "critical_risks": ["Risk 1", "Risk 2", "Risk 3"],
  "entry_strategy": "Specific 90-day entry plan: what to open, how much capital, first 3 actions"
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
    return {
        "market_summary": (
            f"Neighborhood with {pop:,} residents and median income ${income:,}. "
            "Data-driven analysis identifies supply-demand gaps in key business categories."
        ),
        "top_opportunities": [
            {
                "niche": o.get("niche", ""),
                "score": o.get("score", 0),
                "reasoning": "Data model detected undersupply relative to demand and national benchmarks.",
            }
            for o in top3
        ],
        "critical_risks": [
            "Market data may be incomplete or stale.",
            "Local zoning and permit requirements not analyzed.",
            "Competitor landscape may have changed since scrape.",
        ],
        "entry_strategy": (
            "Validate the top-scored niche with a soft launch or pop-up before committing capital. "
            "Survey 20 residents in the zip code, then lease a small footprint for 6 months."
        ),
        "source": "template_fallback",
    }


def evaluate_neighborhood(
    zip_code: str,
    city: str,
    demographics: dict,
    top_opportunities: list[dict],
    businesses: list[dict],
) -> dict:
    """
    Returns dict with keys:
        market_summary, top_opportunities, critical_risks, entry_strategy, source
    """
    pop = demographics.get("population", 0)
    income = demographics.get("median_income", 0)
    age = demographics.get("age_median", 0)

    niche_sample = [b.get("niche", "unknown") for b in businesses[:30]]

    prompt = f"""Analyze this neighborhood and identify the best business opportunity:

ZIP Code: {zip_code}
City: {city}

Demographics:
- Population: {pop:,}
- Median Income: ${income:,}
- Median Age: {age}

Top Scored Opportunities (by our data model):
{json.dumps(top_opportunities[:5], indent=2)}

Existing Business Sample ({len(businesses)} total scraped):
{json.dumps(niche_sample, indent=2)}

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
