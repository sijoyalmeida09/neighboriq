"""video_generator.py — YouTube video script generator for NeighborIQ.

Generates a complete video package (title, hook, 4 sections, Shorts script,
thumbnail text, description, tags) for a neighborhood business opportunity.

Uses Groq LLM when GROQ_API_KEY is set; falls back to deterministic templates.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

log = logging.getLogger("video_generator")

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "data" / "content"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

_NICHE_DISPLAY = {
    "indian_restaurant": "Indian Restaurant",
    "chinese_restaurant": "Chinese Restaurant",
    "mexican_restaurant": "Mexican Restaurant",
    "pizza_restaurant": "Pizza Restaurant",
    "coffee_shop": "Coffee Shop",
    "cafe": "Café",
    "bakery": "Bakery",
    "bar": "Bar",
    "nail_salon": "Nail Salon",
    "hair_salon": "Hair Salon",
    "barbershop": "Barbershop",
    "laundromat": "Laundromat",
    "gym": "Gym / Fitness Center",
    "yoga_studio": "Yoga Studio",
    "daycare": "Daycare Center",
    "tutoring_center": "Tutoring Center",
    "convenience_store": "Convenience Store",
    "liquor_store": "Liquor Store",
    "auto_repair": "Auto Repair Shop",
    "dentist": "Dental Clinic",
}


def _display_niche(niche: str) -> str:
    return _NICHE_DISPLAY.get(niche, niche.replace("_", " ").title())


def _revenue_estimate(niche: str, demographics: dict) -> int:
    try:
        from neighboriq.scoring.revenue_model import get_revenue_model
        m = get_revenue_model(niche, demographics)
        return m.revenue_median * 12
    except Exception:
        population = demographics.get("population", 20000)
        median_income = demographics.get("median_income", 60000)
        return int(median_income * 0.02 * population / 10000)


def _build_entry_section(
    zip_code: str, niche: str, niche_display: str,
    opportunity_data: dict, llm_analysis: dict,
) -> str:
    try:
        from neighboriq.scoring.revenue_model import get_revenue_model
        from neighboriq.scoring.automation_matrix import get_automation_blueprint
        m = get_revenue_model(niche, {})
        b = get_automation_blueprint(niche)
        return (
            f"So how do you actually open a {niche_display} here? "
            f"Three entry tiers. "
            f"Home-based: ${m.startup_home_based:,} — {m.model_solo_description} "
            f"Small footprint: ${m.startup_small:,} — payback in {m.payback_solo_months} months solo "
            f"or {m.payback_1staff_months} months with one employee. "
            f"Full storefront: ${m.startup_full:,} — the institutional play. "
            f"At median revenue of ${m.revenue_median:,}/month, your net solo is "
            f"{m.net_margin_solo_pct:.0f}% — that's ${int(m.revenue_median * m.net_margin_solo_pct / 100):,}/month. "
            f"Now here's the automation play: {b.staff_with_automation}. "
            f"Automate {', '.join(list(b.automated_tasks)[:3])} — saves ${b.monthly_savings_usd:,}/month. "
            f"Tools: {', '.join(t['tool'] for t in list(b.recommended_tools)[:3])}. "
            f"Most of them are free or under $50/month. "
            f"Low-to-high margin path: {m.escalation_path[:200]}. "
            f"{llm_analysis.get('entry_strategy', '')}"
        )
    except Exception:
        capital = opportunity_data.get("typical_capital_req", 150000)
        return (
            f"So how do you actually open a {niche_display} here? "
            f"Startup capital: ${capital:,}. "
            f"Days 1-30: secure the space and permits. "
            f"Days 31-60: build out and hire 1-2 staff. "
            f"Days 61-90: soft launch, focus on {zip_code} delivery radius first. "
            f"{llm_analysis.get('entry_strategy', '')}"
        )


def _build_template_script(
    zip_code: str,
    city: str,
    niche: str,
    opportunity_data: dict,
    demographics: dict,
    competitor_analysis: dict,
    llm_analysis: dict,
) -> dict:
    niche_display = _display_niche(niche)
    competitor_count = opportunity_data.get("competitor_count", 0)
    opportunity_score = opportunity_data.get("opportunity_score", 70)
    saturation_ratio = opportunity_data.get("saturation_ratio", 0.2)
    demand_score = opportunity_data.get("demand_score", 65)
    avg_rating = competitor_analysis.get("avg_rating", 3.5)
    population = demographics.get("population", 20000)
    median_income = demographics.get("median_income", 60000)
    revenue_est = _revenue_estimate(niche, demographics)

    total_restaurants = competitor_analysis.get("total_businesses_nearby", competitor_count * 8)
    title = (
        f"The HIDDEN {niche_display} Opportunity in {city} — The Data Proves It"
    )

    hook_script = (
        f"There are {total_restaurants} restaurants within a mile of {zip_code}. "
        f"I found exactly {competitor_count} {niche_display}{'s' if competitor_count != 1 else ''}. "
        f"But Google Trends shows demand at {demand_score}/100 — and climbing. "
        f"Here's why the first person to open a {niche_display} here could pull "
        f"${revenue_est:,}/year, according to the data."
    )

    sections = [
        {
            "title": "Section 1 — The Data (0:30–3:00)",
            "script": (
                f"Let me show you exactly what I found. I scraped every business "
                f"in {zip_code} — {total_restaurants} total in the food category alone. "
                f"Of those, only {competitor_count} are {niche_display}s. "
                f"That's a saturation ratio of {saturation_ratio:.2f}x the national average. "
                f"Meaning: this neighborhood is running at {int(saturation_ratio * 100)}% of "
                f"the capacity it should have. "
                f"And when I pulled the Google Trends data for '{niche_display.lower()} near me' "
                f"in this area, demand scored {demand_score} out of 100. "
                f"The existing competitors? Average rating of {avg_rating:.1f} stars. "
                f"Customers are under-served AND unhappy with what's there."
            ),
            "visuals": [
                f"Bar chart: {niche_display} count vs national average",
                f"Google Trends screenshot showing {demand_score}/100 demand",
                f"Map view of {zip_code} with business pins",
                f"Star rating distribution of existing {niche_display}s",
            ],
        },
        {
            "title": "Section 2 — The Pattern (3:00–5:00)",
            "script": (
                f"This isn't guesswork. I've seen this exact demographic profile before. "
                f"A neighborhood with {population:,} people, median income of ${median_income:,}, "
                f"and zero {niche_display}s — that's a pattern. "
                f"In neighborhoods with the same profile, when someone opened the first "
                f"{niche_display}, they hit break-even within 18 months on average. "
                f"The first-mover advantage in a neighborhood like this is massive — "
                f"you become the default choice before anyone else shows up."
            ),
            "visuals": [
                "Graph showing success rates in analogous neighborhoods",
                "Timeline: typical first-mover profitability curve",
                "Map of comparable neighborhoods that followed this pattern",
            ],
        },
        {
            "title": "Section 3 — The Entry (5:00–8:00)",
            "script": _build_entry_section(zip_code, niche, niche_display, opportunity_data, llm_analysis),
            "visuals": [
                "90-day Gantt chart",
                "Startup cost breakdown table",
                "Map of vacant commercial spaces in area",
                "Sample menu/service offering",
            ],
        },
        {
            "title": "Section 4 — The CTA (8:00–9:00)",
            "script": (
                f"Every week I run this same analysis on a new neighborhood. "
                f"Next week I'm analyzing the zip code right next to {zip_code}. "
                f"Subscribe and hit the bell — because these windows don't stay open forever. "
                f"The moment someone opens the first {niche_display} in {city}, "
                f"this opportunity disappears. "
                f"If you want the full data report for {zip_code} — the competitor breakdown, "
                f"the demand curves, the entry cost model — link's in the description."
            ),
            "visuals": [
                "Subscribe animation",
                "Preview of next neighborhood analysis",
                "Report download CTA card",
            ],
        },
    ]

    short_script = (
        f"POV: You find a neighborhood with {total_restaurants} restaurants and zero {niche_display}s. "
        f"Demand score? {demand_score} out of 100. "
        f"Competitors? Only {competitor_count}, averaging {avg_rating:.1f} stars. "
        f"Revenue potential? ${revenue_est:,} a year. "
        f"This is {city}, {zip_code}. The data found the gap. "
        f"Now someone just has to open it. "
        f"Follow for weekly neighborhood opportunity analysis."
    )

    thumbnail_text = f"ZERO {niche_display.upper()}S"
    demand_line = f"${revenue_est:,}/yr DEMAND SIGNAL"

    description = (
        f"I analyzed every business in {city} {zip_code} and found a major gap: "
        f"only {competitor_count} {niche_display}{'s' if competitor_count != 1 else ''} "
        f"for a population of {population:,}. "
        f"Demand score: {demand_score}/100. Opportunity score: {opportunity_score}/100.\n\n"
        f"In this video I break down:\n"
        f"- The exact saturation data for {zip_code}\n"
        f"- Why the existing competitors are losing customers\n"
        f"- Historical patterns from similar neighborhoods\n"
        f"- A realistic 90-day entry plan\n\n"
        f"Get the full data report (free): github.com/sijoy/neighboriq\n\n"
        f"#BusinessOpportunity #{city.replace(' ', '')} #SmallBusiness "
        f"#Entrepreneurship #DataDriven #NeighborIQ"
    )

    tags = [
        f"business opportunity {city.lower()}",
        f"{niche_display.lower()} opportunity",
        f"small business {city.lower()}",
        "neighborhood analysis",
        "data-driven business",
        "entrepreneurship",
        "business intelligence",
        f"{zip_code} business",
        "hidden opportunity",
        "market gap analysis",
    ]

    chapter_timestamps = [
        "0:00 — The shocking gap in the data",
        "0:30 — Breaking down the numbers",
        "3:00 — Historical pattern analysis",
        "5:00 — The 90-day entry plan",
        "8:00 — What's next",
    ]

    return {
        "zip_code": zip_code,
        "city": city,
        "niche": niche,
        "title": title,
        "hook_script": hook_script,
        "sections": sections,
        "short_script": short_script,
        "thumbnail_text": thumbnail_text,
        "demand_line": demand_line,
        "description": description,
        "tags": tags,
        "chapter_timestamps": chapter_timestamps,
        "opportunity_score": opportunity_score,
        "revenue_estimate": revenue_est,
    }


def _build_llm_script(
    zip_code: str,
    city: str,
    niche: str,
    opportunity_data: dict,
    demographics: dict,
    competitor_analysis: dict,
    llm_analysis: dict,
) -> dict | None:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        import requests  # type: ignore

        niche_display = _display_niche(niche)
        revenue_est = _revenue_estimate(niche, demographics)

        prompt = {
            "role": "user",
            "content": (
                f"You are a YouTube scriptwriter for a data-driven business channel called NeighborIQ. "
                f"Write a complete 8–9 minute YouTube video script about a hidden business opportunity.\n\n"
                f"CONTEXT:\n"
                f"- Neighborhood: {city}, {zip_code}\n"
                f"- Opportunity: {niche_display}\n"
                f"- Opportunity score: {opportunity_data.get('opportunity_score', 70)}/100\n"
                f"- Existing competitor count: {opportunity_data.get('competitor_count', 0)}\n"
                f"- Competitor avg rating: {competitor_analysis.get('avg_rating', 3.5)}\n"
                f"- Demand score: {opportunity_data.get('demand_score', 65)}/100\n"
                f"- Population: {demographics.get('population', 20000):,}\n"
                f"- Median income: ${demographics.get('median_income', 60000):,}\n"
                f"- Estimated annual revenue opportunity: ${revenue_est:,}\n"
                f"- LLM market analysis: {json.dumps(llm_analysis)}\n\n"
                f"OUTPUT FORMAT (strict JSON, no markdown):\n"
                f'{{"title": "...", "hook_script": "...", '
                f'"sections": [{{"title": "...", "script": "...", "visuals": ["..."]}}], '
                f'"short_script": "...", "thumbnail_text": "...", "demand_line": "...", '
                f'"description": "...", "tags": ["..."], "chapter_timestamps": ["..."]}}'
            ),
        }

        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [prompt],
                "temperature": 0.7,
                "max_tokens": 2000,
            },
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        parsed: dict[str, Any] = json.loads(content)
        parsed.update({
            "zip_code": zip_code,
            "city": city,
            "niche": niche,
            "opportunity_score": opportunity_data.get("opportunity_score", 70),
            "revenue_estimate": revenue_est,
        })
        return parsed
    except Exception as exc:
        log.warning("Groq script generation failed (%s), falling back to template", exc)
        return None


def generate_script(
    zip_code: str,
    city: str,
    niche: str,
    opportunity_data: dict,
    demographics: dict,
    competitor_analysis: dict,
    llm_analysis: dict,
) -> dict:
    """Generate a complete YouTube video package for a neighborhood opportunity."""
    result = _build_llm_script(
        zip_code, city, niche,
        opportunity_data, demographics, competitor_analysis, llm_analysis,
    )
    if result is None:
        result = _build_template_script(
            zip_code, city, niche,
            opportunity_data, demographics, competitor_analysis, llm_analysis,
        )
    log.info("Generated script for %s / %s: %s", zip_code, niche, result["title"])
    return result


def generate_video_script(zip_code: str, niche: str, opportunity_data: dict) -> dict:
    """Compatibility wrapper used by cli.py run/content commands."""
    demographics = opportunity_data.get("demographics", {})
    competitor_analysis = {
        "avg_rating": opportunity_data.get("competitor_avg_rating", 3.5),
        "total_businesses_nearby": opportunity_data.get("competitor_count", 0) * 8,
    }
    city = opportunity_data.get("city", zip_code)
    llm_analysis = opportunity_data.get("llm_analysis", {})
    return generate_script(zip_code, city, niche, opportunity_data, demographics, competitor_analysis, llm_analysis)


def save_script(zip_code: str, niche: str, script: dict) -> Path:
    """Saves script JSON to data/content/{zip_code}_{niche}.json. Returns path."""
    path = OUTPUT_DIR / f"{zip_code}_{niche}.json"
    path.write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Saved script → %s", path)
    return path


def load_script(zip_code: str, niche: str) -> dict | None:
    """Loads script from data/content/ if it exists."""
    path = OUTPUT_DIR / f"{zip_code}_{niche}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        log.warning("Failed to load script %s: %s", path, exc)
        return None
