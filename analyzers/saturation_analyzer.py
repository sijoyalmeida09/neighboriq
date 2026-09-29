"""saturation_analyzer.py — measures how crowded each business category is."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

# US national averages: businesses per 10,000 residents
# Source: US Census County Business Patterns + SBA data
NATIONAL_BENCHMARKS: dict[str, float] = {
    "restaurant": 7.2,
    "indian_restaurant": 0.3,
    "chinese_restaurant": 0.8,
    "mexican_restaurant": 0.9,
    "pizza_restaurant": 1.2,
    "coffee_shop": 2.1,
    "cafe": 1.8,
    "bakery": 0.6,
    "bar": 2.4,
    "grocery_store": 1.4,
    "pharmacy": 0.9,
    "nail_salon": 1.1,
    "hair_salon": 2.8,
    "barbershop": 1.6,
    "laundromat": 0.4,
    "dry_cleaning": 0.3,
    "gym": 0.8,
    "yoga_studio": 0.4,
    "dentist": 1.7,
    "doctor": 2.3,
    "auto_repair": 1.2,
    "gas_station": 0.8,
    "convenience_store": 0.9,
    "liquor_store": 0.6,
    "pet_store": 0.4,
    "bookstore": 0.2,
    "clothing_store": 1.8,
    "shoe_store": 0.6,
    "hardware_store": 0.5,
    "electronics_store": 0.7,
    "furniture_store": 0.4,
    "real_estate": 1.4,
    "law_office": 2.1,
    "accounting": 1.2,
    "insurance": 1.1,
    "bank": 0.8,
    "credit_union": 0.3,
    "daycare": 0.9,
    "tutoring_center": 0.5,
    "florist": 0.4,
    "jewelry_store": 0.5,
    "gift_shop": 0.3,
    "sushi_restaurant": 0.4,
    "thai_restaurant": 0.3,
    "mediterranean_restaurant": 0.2,
    "ethiopian_restaurant": 0.1,
    "vietnamese_restaurant": 0.3,
    "halal_restaurant": 0.2,
    "check_cashing": 0.3,
    "real_estate_office": 1.4,
}


@dataclass(frozen=True)
class SaturationResult:
    niche: str
    actual_count: int
    actual_density: float       # per 10k residents
    benchmark_density: float    # national average per 10k
    saturation_ratio: float     # actual / benchmark; < 1.0 = undersupplied
    population: int


def compute_density(
    businesses: list[dict],
    population: int,
    niche_counts: dict[str, int] | None = None,
) -> list[SaturationResult]:
    """
    Args:
        businesses: list of dicts each with a "niche" key
        population: neighborhood population (must be > 0)
        niche_counts: optional override counts per niche (skips counting businesses)
    Returns:
        List of SaturationResult for niches present in NATIONAL_BENCHMARKS,
        sorted by saturation_ratio ascending (most undersupplied first).
    """
    if population <= 0:
        population = 1

    counts: dict[str, int]
    if niche_counts is not None:
        counts = dict(niche_counts)
    else:
        raw_counts: Counter[str] = Counter(
            b.get("niche", "other") for b in businesses
        )
        counts = dict(raw_counts)

    results: list[SaturationResult] = []
    for niche, benchmark in NATIONAL_BENCHMARKS.items():
        actual_count = counts.get(niche, 0)
        actual_density = (actual_count / population) * 10_000
        if benchmark > 0:
            saturation_ratio = actual_density / benchmark
        else:
            saturation_ratio = 0.0
        results.append(
            SaturationResult(
                niche=niche,
                actual_count=actual_count,
                actual_density=round(actual_density, 4),
                benchmark_density=benchmark,
                saturation_ratio=round(saturation_ratio, 4),
                population=population,
            )
        )

    results.sort(key=lambda r: r.saturation_ratio)
    return results
