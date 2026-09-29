"""Unit tests for NeighborIQ scoring logic — no external dependencies."""
from __future__ import annotations

import sys
from pathlib import Path

# Allow imports from the neighboriq root when running pytest from tests/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzers.saturation_analyzer import SaturationResult, compute_density
from analyzers.gap_detector import detect_gaps
from scoring.niche_classifier import classify


def test_niche_classify_indian() -> None:
    result = classify("Indian Restaurant")
    assert result.niche == "indian_restaurant"
    assert result.parent_category == "food_beverage"


def test_niche_classify_coffee() -> None:
    result = classify("Starbucks Coffee")
    assert result.niche == "coffee_shop"


def test_niche_classify_unknown() -> None:
    result = classify("ZZZZUNKNOWN_XYZ")
    assert result.niche == "other"


def test_niche_classify_barbershop() -> None:
    result = classify("Joe's Barber Shop")
    assert result.niche == "barbershop"
    assert result.typical_capital_req > 0


def test_saturation_undersupplied() -> None:
    businesses = [{"niche": "indian_restaurant"} for _ in range(1)]
    results = compute_density(businesses, population=50000)
    indian = next((r for r in results if r.niche == "indian_restaurant"), None)
    assert indian is not None
    # 1 Indian restaurant per 50k residents → 0.2/10k vs benchmark 0.3/10k = undersupplied
    assert indian.saturation_ratio < 1.0


def test_saturation_oversupplied() -> None:
    businesses = [{"niche": "hair_salon"} for _ in range(50)]
    results = compute_density(businesses, population=10000)
    hair = next((r for r in results if r.niche == "hair_salon"), None)
    assert hair is not None
    # 50 salons per 10k residents → 50/10k vs benchmark 2.8/10k = massively oversupplied
    assert hair.saturation_ratio > 1.0


def test_saturation_zero_population_does_not_crash() -> None:
    businesses = [{"niche": "coffee_shop"}]
    results = compute_density(businesses, population=0)
    # Should return results without dividing by zero
    assert isinstance(results, list)


def test_gap_high_demand_zero_supply() -> None:
    sat = SaturationResult(
        niche="indian_restaurant",
        actual_count=0,
        actual_density=0.0,
        benchmark_density=0.3,
        saturation_ratio=0.0,
        population=50000,
    )
    demand = {"indian_restaurant": 80}
    gaps = detect_gaps([sat], demand)
    assert len(gaps) == 1
    assert gaps[0].tier == "A"
    assert gaps[0].gap_score > 100


def test_gap_low_demand_filters_out() -> None:
    sat = SaturationResult(
        niche="bookstore",
        actual_count=0,
        actual_density=0.0,
        benchmark_density=0.2,
        saturation_ratio=0.0,
        population=10000,
    )
    demand = {"bookstore": 5}  # very low demand
    gaps = detect_gaps([sat], demand, min_demand_score=20)
    assert len(gaps) == 0  # filtered out


def test_gap_oversupplied_scores_low() -> None:
    sat = SaturationResult(
        niche="hair_salon",
        actual_count=30,
        actual_density=30.0,
        benchmark_density=2.8,
        saturation_ratio=10.7,  # massively oversupplied
        population=10000,
    )
    demand = {"hair_salon": 60}
    gaps = detect_gaps([sat], demand)
    if gaps:
        assert gaps[0].tier in ("B", "C")  # should not be Tier A


def test_gap_sorts_by_score_descending() -> None:
    sats = [
        SaturationResult("indian_restaurant", 0, 0.0, 0.3, 0.0, 50000),
        SaturationResult("coffee_shop", 10, 2.0, 2.1, 0.95, 50000),
    ]
    demand = {"indian_restaurant": 80, "coffee_shop": 70}
    gaps = detect_gaps(sats, demand)
    if len(gaps) >= 2:
        assert gaps[0].gap_score >= gaps[1].gap_score
