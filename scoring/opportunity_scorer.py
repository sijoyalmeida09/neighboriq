"""opportunity_scorer.py — Multi-factor business opportunity scorer.

Additive scoring model (base 50) adapted from the legitimacy_checker.py pattern.
Each factor contributes bounded points; final score is capped at [0, 100].
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from analyzers.gap_detector import GapResult
    from analyzers.pattern_analyzer import PatternLesson
    from analyzers.saturation_analyzer import SaturationResult
    from analyzers.sentiment_analyzer import SentimentResult

from .niche_classifier import NICHE_MAP

log = logging.getLogger("opportunity_scorer")

# Income bracket thresholds (median household income)
_LOW_INCOME = 40_000
_MODERATE_INCOME = 80_000
_HIGH_INCOME = 120_000

# Capital tiers for demographic alignment
_AFFORDABLE_CAP = 100_000   # nail salon, barbershop, tutoring
_PREMIUM_CAP = 300_000      # gym, bar, ethnic restaurant


@dataclass(frozen=True)
class OpportunityScore:
    niche: str
    score: int
    tier: str                    # "A" | "B" | "C"
    saturation_ratio: float
    demand_score: int
    competitor_avg_rating: float
    pattern_success_rate: float
    income_alignment: float      # 0.0–1.0
    score_breakdown: dict        # {"demand": N, "supply": N, "competition": N, "pattern": N, "demographics": N}
    recommendation: str


def _demand_points(demand_score: int) -> float:
    return demand_score * 0.30  # max +30


def _supply_points(saturation_ratio: float) -> float:
    if saturation_ratio == 0:
        return 25.0
    if saturation_ratio < 0.5:
        return 20.0
    if saturation_ratio < 1.0:
        return 12.0
    if saturation_ratio < 2.0:
        return 5.0
    return 0.0


def _competition_points(avg_rating: float) -> float:
    if avg_rating <= 0:
        return 5.0  # no data → slight positive (no competition signal)
    if avg_rating < 3.5:
        return 20.0
    if avg_rating < 3.8:
        return 14.0
    if avg_rating < 4.0:
        return 8.0
    if avg_rating < 4.2:
        return 3.0
    return 0.0


def _pattern_points(lessons: list[PatternLesson]) -> tuple[float, float]:
    """Returns (points, success_rate). Points capped at 15."""
    if not lessons:
        return 0.0, 0.0
    best = max(lessons, key=lambda l: l.success_rate)
    return best.success_rate * 15.0, best.success_rate


def _demographics_points(niche: str, median_income: int) -> tuple[float, float]:
    """Returns (points, income_alignment 0-1)."""
    entry = NICHE_MAP.get(niche)
    typical_cap = entry[2] if entry else 150_000

    if median_income >= _HIGH_INCOME:
        # affluent: premium niches fit well
        if typical_cap >= _PREMIUM_CAP:
            return 10.0, 1.0
        if typical_cap >= _AFFORDABLE_CAP:
            return 6.0, 0.7
        return 4.0, 0.5
    elif median_income >= _MODERATE_INCOME:
        # moderate: affordable niches fit best
        if typical_cap <= _AFFORDABLE_CAP:
            return 8.0, 0.9
        if typical_cap <= _PREMIUM_CAP:
            return 5.0, 0.7
        return 2.0, 0.4
    else:
        # low income: very affordable niches only
        if typical_cap <= _AFFORDABLE_CAP:
            return 6.0, 0.8
        if typical_cap <= _PREMIUM_CAP:
            return 0.0, 0.3
        return -5.0, 0.1  # mismatch penalty


def _build_recommendation(niche: str, score: int, tier: str, sat: float, demand: int, rating: float) -> str:
    supply_word = "no" if sat == 0 else ("low" if sat < 0.5 else ("moderate" if sat < 1.0 else "high"))
    demand_word = "strong" if demand >= 70 else ("moderate" if demand >= 40 else "weak")
    comp_word = "poor" if rating < 3.8 else ("average" if rating < 4.2 else "strong")
    return (
        f"Tier {tier} (score {score}): {niche.replace('_', ' ').title()} — "
        f"{supply_word} supply, {demand_word} demand, {comp_word} competition quality."
    )


def score_opportunity(
    niche: str,
    saturation_result: SaturationResult | None,
    gap_result: GapResult | None,
    sentiment_result: SentimentResult | None,
    pattern_lessons: list[PatternLesson],
    demographics: dict,
) -> OpportunityScore:
    sat_ratio = saturation_result.saturation_ratio if saturation_result else 1.0
    demand = gap_result.demand_score if gap_result else 50
    avg_rating = sentiment_result.avg_rating if sentiment_result else 0.0
    median_income = demographics.get("median_income", 60_000)

    d_pts = _demand_points(demand)
    s_pts = _supply_points(sat_ratio)
    c_pts = _competition_points(avg_rating)
    p_pts, success_rate = _pattern_points(pattern_lessons)
    demo_pts, income_align = _demographics_points(niche, median_income)

    raw = 50 + d_pts + s_pts + c_pts + p_pts + demo_pts
    final = int(min(100, max(0, raw)))

    tier = "A" if final >= 70 else ("B" if final >= 50 else "C")

    breakdown = {
        "demand": round(d_pts, 1),
        "supply": round(s_pts, 1),
        "competition": round(c_pts, 1),
        "pattern": round(p_pts, 1),
        "demographics": round(demo_pts, 1),
    }

    return OpportunityScore(
        niche=niche,
        score=final,
        tier=tier,
        saturation_ratio=sat_ratio,
        demand_score=demand,
        competitor_avg_rating=avg_rating,
        pattern_success_rate=round(success_rate, 3),
        income_alignment=round(income_align, 2),
        score_breakdown=breakdown,
        recommendation=_build_recommendation(niche, final, tier, sat_ratio, demand, avg_rating),
    )


def score_all_opportunities(
    saturation_results: list[SaturationResult],
    gap_results: list[GapResult],
    sentiment_results: list[SentimentResult],
    pattern_lessons_by_niche: dict[str, list[PatternLesson]],
    demographics: dict,
) -> list[OpportunityScore]:
    """Joins all analyzer outputs by niche and scores each. Returns sorted by score desc."""
    sat_by_niche = {r.niche: r for r in saturation_results}
    gap_by_niche = {r.niche: r for r in gap_results}
    sent_by_niche = {r.niche: r for r in sentiment_results}

    all_niches: set[str] = (
        set(sat_by_niche) | set(gap_by_niche) | set(sent_by_niche)
    )

    scores: list[OpportunityScore] = []
    for niche in all_niches:
        try:
            opp = score_opportunity(
                niche=niche,
                saturation_result=sat_by_niche.get(niche),
                gap_result=gap_by_niche.get(niche),
                sentiment_result=sent_by_niche.get(niche),
                pattern_lessons=pattern_lessons_by_niche.get(niche, []),
                demographics=demographics,
            )
            scores.append(opp)
        except Exception:
            log.exception("Scoring failed for niche=%s", niche)

    return sorted(scores, key=lambda o: o.score, reverse=True)
