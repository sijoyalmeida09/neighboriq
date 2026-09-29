"""pattern_analyzer.py — extracts lessons from historical market patterns."""
from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class DemographicProfile:
    income_bracket: str   # "low" | "moderate" | "high" | "affluent"
    population_tier: str  # "micro" | "small" | "medium" | "large"
    age_group: str        # "young" | "mixed" | "mature"


@dataclass(frozen=True)
class PatternLesson:
    niche: str
    success_rate: float
    pattern_count: int
    avg_years_to_profit: float
    avg_entry_capital: int
    summary: str


def compute_profile(demographics: dict) -> DemographicProfile:
    income = demographics.get("median_income", 60_000)
    if income < 40_000:
        income_bracket = "low"
    elif income < 80_000:
        income_bracket = "moderate"
    elif income < 120_000:
        income_bracket = "high"
    else:
        income_bracket = "affluent"

    population = demographics.get("population", 20_000)
    if population < 5_000:
        population_tier = "micro"
    elif population < 20_000:
        population_tier = "small"
    elif population < 50_000:
        population_tier = "medium"
    else:
        population_tier = "large"

    age = demographics.get("age_median", 36)
    if age < 32:
        age_group = "young"
    elif age < 42:
        age_group = "mixed"
    else:
        age_group = "mature"

    return DemographicProfile(
        income_bracket=income_bracket,
        population_tier=population_tier,
        age_group=age_group,
    )


def profile_hash(profile: DemographicProfile) -> str:
    key = f"{profile.income_bracket}|{profile.population_tier}|{profile.age_group}"
    return hashlib.sha1(key.encode()).hexdigest()[:12]


def get_lessons(
    patterns: list[dict],
    niche: str | None = None,
) -> list[PatternLesson]:
    """
    Aggregates pattern records into lessons.
    Each record must have: niche, outcome ("succeeded"|"failed"),
    years_to_profit (float), entry_capital_usd (int).
    """
    if niche is not None:
        patterns = [p for p in patterns if p.get("niche") == niche]

    by_niche: dict[str, list[dict]] = defaultdict(list)
    for p in patterns:
        by_niche[p["niche"]].append(p)

    lessons: list[PatternLesson] = []
    for n, records in by_niche.items():
        succeeded = [r for r in records if r.get("outcome") == "succeeded"]
        success_rate = len(succeeded) / len(records) if records else 0.0
        profit_years = [
            float(r["years_to_profit"])
            for r in succeeded
            if r.get("years_to_profit") is not None
        ]
        capitals = [
            int(r["entry_capital_usd"])
            for r in records
            if r.get("entry_capital_usd") is not None
        ]
        avg_years = sum(profit_years) / len(profit_years) if profit_years else 0.0
        avg_capital = int(sum(capitals) / len(capitals)) if capitals else 0

        summary = (
            f"{n}: {success_rate:.0%} success rate across {len(records)} markets, "
            f"avg {avg_years:.1f} yrs to profit, ~${avg_capital:,} entry capital"
        )
        lessons.append(
            PatternLesson(
                niche=n,
                success_rate=round(success_rate, 3),
                pattern_count=len(records),
                avg_years_to_profit=round(avg_years, 2),
                avg_entry_capital=avg_capital,
                summary=summary,
            )
        )

    lessons.sort(key=lambda l: l.success_rate, reverse=True)
    return lessons


# ---------------------------------------------------------------------------
# Seed data: ~20 realistic historical patterns
# Keys: demographic_profile_hash, niche, outcome, years_to_profit,
#       entry_capital_usd, source
# ---------------------------------------------------------------------------

def _h(income: str, pop: str, age: str) -> str:
    return profile_hash(DemographicProfile(income, pop, age))


SEED_PATTERNS: list[dict] = [
    # ── Indian / ethnic restaurants ──────────────────────────────────────────
    {"demographic_profile_hash": _h("moderate", "medium", "young"), "niche": "indian_restaurant",
     "outcome": "succeeded", "years_to_profit": 1.5, "entry_capital_usd": 150_000, "source": "sba_data"},
    {"demographic_profile_hash": _h("moderate", "medium", "young"), "niche": "indian_restaurant",
     "outcome": "succeeded", "years_to_profit": 2.0, "entry_capital_usd": 180_000, "source": "sba_data"},
    {"demographic_profile_hash": _h("moderate", "small", "young"), "niche": "indian_restaurant",
     "outcome": "succeeded", "years_to_profit": 1.8, "entry_capital_usd": 140_000, "source": "yelp_historical"},
    {"demographic_profile_hash": _h("low", "medium", "young"), "niche": "indian_restaurant",
     "outcome": "failed", "years_to_profit": 0.0, "entry_capital_usd": 120_000, "source": "sba_data"},
    {"demographic_profile_hash": _h("high", "medium", "mixed"), "niche": "indian_restaurant",
     "outcome": "succeeded", "years_to_profit": 1.2, "entry_capital_usd": 200_000, "source": "yelp_historical"},
    # ── Halal restaurant ─────────────────────────────────────────────────────
    {"demographic_profile_hash": _h("moderate", "medium", "young"), "niche": "halal_restaurant",
     "outcome": "succeeded", "years_to_profit": 1.3, "entry_capital_usd": 130_000, "source": "sba_data"},
    {"demographic_profile_hash": _h("moderate", "large", "mixed"), "niche": "halal_restaurant",
     "outcome": "succeeded", "years_to_profit": 1.0, "entry_capital_usd": 125_000, "source": "sba_data"},
    # ── Coffee shop ──────────────────────────────────────────────────────────
    {"demographic_profile_hash": _h("affluent", "medium", "young"), "niche": "coffee_shop",
     "outcome": "succeeded", "years_to_profit": 1.0, "entry_capital_usd": 80_000, "source": "sba_data"},
    {"demographic_profile_hash": _h("affluent", "medium", "mixed"), "niche": "coffee_shop",
     "outcome": "succeeded", "years_to_profit": 1.5, "entry_capital_usd": 90_000, "source": "sba_data"},
    {"demographic_profile_hash": _h("high", "small", "young"), "niche": "coffee_shop",
     "outcome": "succeeded", "years_to_profit": 2.0, "entry_capital_usd": 75_000, "source": "yelp_historical"},
    {"demographic_profile_hash": _h("low", "medium", "mature"), "niche": "coffee_shop",
     "outcome": "failed", "years_to_profit": 0.0, "entry_capital_usd": 70_000, "source": "sba_data"},
    # ── Laundromat ───────────────────────────────────────────────────────────
    {"demographic_profile_hash": _h("moderate", "medium", "mixed"), "niche": "laundromat",
     "outcome": "succeeded", "years_to_profit": 2.5, "entry_capital_usd": 200_000, "source": "sba_data"},
    {"demographic_profile_hash": _h("low", "medium", "mixed"), "niche": "laundromat",
     "outcome": "succeeded", "years_to_profit": 2.0, "entry_capital_usd": 180_000, "source": "sba_data"},
    {"demographic_profile_hash": _h("low", "large", "young"), "niche": "laundromat",
     "outcome": "succeeded", "years_to_profit": 1.8, "entry_capital_usd": 220_000, "source": "yelp_historical"},
    # ── Gym ──────────────────────────────────────────────────────────────────
    {"demographic_profile_hash": _h("affluent", "medium", "young"), "niche": "gym",
     "outcome": "succeeded", "years_to_profit": 1.5, "entry_capital_usd": 200_000, "source": "sba_data"},
    {"demographic_profile_hash": _h("high", "medium", "young"), "niche": "gym",
     "outcome": "succeeded", "years_to_profit": 2.0, "entry_capital_usd": 250_000, "source": "sba_data"},
    {"demographic_profile_hash": _h("moderate", "medium", "young"), "niche": "gym",
     "outcome": "failed", "years_to_profit": 0.0, "entry_capital_usd": 180_000, "source": "sba_data"},
    # ── Nail salon ───────────────────────────────────────────────────────────
    {"demographic_profile_hash": _h("moderate", "medium", "mixed"), "niche": "nail_salon",
     "outcome": "succeeded", "years_to_profit": 1.0, "entry_capital_usd": 50_000, "source": "sba_data"},
    {"demographic_profile_hash": _h("high", "small", "mixed"), "niche": "nail_salon",
     "outcome": "succeeded", "years_to_profit": 0.8, "entry_capital_usd": 60_000, "source": "yelp_historical"},
    {"demographic_profile_hash": _h("low", "micro", "mature"), "niche": "nail_salon",
     "outcome": "failed", "years_to_profit": 0.0, "entry_capital_usd": 45_000, "source": "sba_data"},
]
