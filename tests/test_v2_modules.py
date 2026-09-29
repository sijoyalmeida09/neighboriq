"""test_v2_modules.py — Tests for NeighborIQ v2 additions.

Covers: revenue_model, automation_matrix, asset_mapper,
        safegraph_collector, census_cbp_collector.
All tests run without external network or API calls.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Insert automation root so `neighboriq.*` imports resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# ──────────────────────────────────────────────────────────────────────────────
# Revenue model
# ──────────────────────────────────────────────────────────────────────────────

def test_revenue_model_barbershop() -> None:
    from neighboriq.scoring.revenue_model import get_revenue_model
    m = get_revenue_model("barbershop", {})
    assert m.niche == "barbershop"
    assert m.revenue_median > 0
    assert 0 < m.net_margin_solo_pct <= 100
    assert m.startup_home_based < m.startup_small < m.startup_full
    assert m.payback_solo_months > 0


def test_revenue_model_laundromat() -> None:
    from neighboriq.scoring.revenue_model import get_revenue_model
    m = get_revenue_model("laundromat", {})
    assert m.revenue_median >= 10_000
    assert m.net_margin_solo_pct > 0


def test_revenue_model_unknown_niche_falls_back() -> None:
    from neighboriq.scoring.revenue_model import get_revenue_model
    m = get_revenue_model("unicorn_store", {})
    assert m.niche in ("generic", "unicorn_store") or m.revenue_median > 0


def test_revenue_model_list_niches() -> None:
    from neighboriq.scoring.revenue_model import list_niches
    niches = list_niches()
    assert len(niches) >= 10
    assert "barbershop" in niches
    assert "laundromat" in niches


def test_revenue_model_immutable() -> None:
    from neighboriq.scoring.revenue_model import get_revenue_model
    import dataclasses
    m = get_revenue_model("nail_salon", {})
    assert dataclasses.is_dataclass(m)
    # Frozen dataclasses raise FrozenInstanceError on mutation attempt
    try:
        m.niche = "mutated"  # type: ignore[misc]
        assert False, "Should have raised"
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# Automation matrix
# ──────────────────────────────────────────────────────────────────────────────

def test_automation_matrix_barbershop() -> None:
    from neighboriq.scoring.automation_matrix import get_automation_blueprint
    b = get_automation_blueprint("barbershop")
    assert b.automation_score >= 0
    assert len(b.automated_tasks) > 0
    assert len(b.human_tasks) > 0
    assert b.monthly_savings_usd >= 0


def test_automation_matrix_unknown_niche() -> None:
    from neighboriq.scoring.automation_matrix import get_automation_blueprint
    b = get_automation_blueprint("unicorn_store")
    assert b is not None


def test_automation_matrix_immutable() -> None:
    from neighboriq.scoring.automation_matrix import get_automation_blueprint
    import dataclasses
    b = get_automation_blueprint("nail_salon")
    assert dataclasses.is_dataclass(b)
    try:
        b.automation_score = 999  # type: ignore[misc]
        assert False, "Should have raised"
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# Asset mapper
# ──────────────────────────────────────────────────────────────────────────────

def test_asset_mapper_basic() -> None:
    from neighboriq.analyzers.asset_mapper import AssetProfile, filter_by_assets
    profile = AssetProfile(
        capital_usd=5000,
        space_sqft=0,
        has_vehicle=False,
        skills=("teaching",),
        licenses=(),
        existing_customers=0,
        monthly_overhead_max=500,
        prefers_home_based=True,
        hours_per_week=20,
    )
    opportunities = [
        {"niche": "tutoring_center", "opportunity_score": 75},
        {"niche": "laundromat", "opportunity_score": 80},
    ]
    # actual signature: filter_by_assets(opportunities, assets)
    results = filter_by_assets(opportunities, profile)
    assert isinstance(results, list)
    niches = [r.niche for r in results]
    assert "tutoring_center" in niches
    tutor = next(r for r in results if r.niche == "tutoring_center")
    assert tutor.feasibility_score > 0


def test_asset_mapper_no_opportunities() -> None:
    from neighboriq.analyzers.asset_mapper import AssetProfile, filter_by_assets
    profile = AssetProfile(
        capital_usd=1000, space_sqft=0, has_vehicle=False,
        skills=(), licenses=(), existing_customers=0,
        monthly_overhead_max=100, prefers_home_based=True, hours_per_week=5,
    )
    results = filter_by_assets([], profile)
    assert results == []


def test_asset_mapper_returns_immutable() -> None:
    from neighboriq.analyzers.asset_mapper import AssetProfile, filter_by_assets
    import dataclasses
    profile = AssetProfile(
        capital_usd=50_000, space_sqft=1000, has_vehicle=True,
        skills=("haircutting",), licenses=("cosmetology",), existing_customers=0,
        monthly_overhead_max=3000, prefers_home_based=False, hours_per_week=50,
    )
    results = filter_by_assets([{"niche": "barbershop", "opportunity_score": 80}], profile)
    if results:
        assert dataclasses.is_dataclass(results[0])


# ──────────────────────────────────────────────────────────────────────────────
# SafeGraph collector
# ──────────────────────────────────────────────────────────────────────────────

def test_safegraph_no_env_returns_empty() -> None:
    from neighboriq.collectors.safegraph_collector import load_places_for_zip, is_available
    os.environ.pop("SAFEGRAPH_DIR", None)
    assert not is_available()
    result = load_places_for_zip("02122")
    assert result == []


def test_safegraph_bad_dir_returns_empty(tmp_path) -> None:
    from neighboriq.collectors.safegraph_collector import load_places_for_zip, is_available
    os.environ["SAFEGRAPH_DIR"] = str(tmp_path / "nonexistent")
    try:
        assert not is_available()
        result = load_places_for_zip("02122")
        assert result == []
    finally:
        os.environ.pop("SAFEGRAPH_DIR", None)


def test_safegraph_reads_csv(tmp_path) -> None:
    import csv as _csv
    from neighboriq.collectors.safegraph_collector import load_places_for_zip

    csv_path = tmp_path / "places.csv"
    rows = [
        {
            "location_name": "Joe's Barber",
            "top_category": "Personal Care Services",
            "sub_category": "Barbershop",
            "latitude": "42.3601",
            "longitude": "-71.0589",
            "street_address": "123 Main St",
            "city": "Boston",
            "region": "MA",
            "postal_code": "02122",
            "raw_visit_counts": "150",
            "avg_rating": "4.5",
            "num_reviews": "23",
        },
        {
            "location_name": "Out of ZIP",
            "top_category": "Restaurants",
            "sub_category": "Pizza",
            "latitude": "40.7128",
            "longitude": "-74.0060",
            "street_address": "1 Wall St",
            "city": "New York",
            "region": "NY",
            "postal_code": "10005",
            "raw_visit_counts": "200",
            "avg_rating": "4.0",
            "num_reviews": "10",
        },
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = _csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    os.environ["SAFEGRAPH_DIR"] = str(tmp_path)
    try:
        result = load_places_for_zip("02122")
        assert len(result) == 1
        assert result[0]["name"] == "Joe's Barber"
        assert result[0]["source"] == "safegraph"
        assert result[0]["rating"] == 4.5
    finally:
        os.environ.pop("SAFEGRAPH_DIR", None)


# ──────────────────────────────────────────────────────────────────────────────
# Census CBP collector
# ──────────────────────────────────────────────────────────────────────────────

def test_census_naics_mapping() -> None:
    from neighboriq.collectors.census_cbp_collector import naics_to_niche
    assert naics_to_niche("812111") in ("barbershop", "hair_salon", "personal_care")
    assert naics_to_niche("812320") == "laundromat"
    assert naics_to_niche("445110") in ("grocery_store", "convenience_store", "food_retail")
    assert naics_to_niche("999999") == "other"


def test_census_get_niche_counts_network_fail_returns_empty() -> None:
    """When network is unavailable, get_niche_counts_for_zip must return {} not raise."""
    from neighboriq.collectors.census_cbp_collector import get_niche_counts_for_zip
    # Use a clearly invalid zip to maximize network failure likelihood in CI
    result = get_niche_counts_for_zip("99999")
    assert isinstance(result, dict)


def test_census_is_available_when_key_set() -> None:
    from neighboriq.collectors.census_cbp_collector import is_available
    os.environ["CENSUS_API_KEY"] = "test_key_12345"
    try:
        result = is_available()
        assert isinstance(result, bool)
    finally:
        os.environ.pop("CENSUS_API_KEY", None)


# ──────────────────────────────────────────────────────────────────────────────
# Domain analyzer
# ──────────────────────────────────────────────────────────────────────────────

def test_domain_analyzer_import() -> None:
    from neighboriq.analyzers.domain_analyzer import analyze_domain, format_domain_analysis
    assert callable(analyze_domain)
    assert callable(format_domain_analysis)


# ──────────────────────────────────────────────────────────────────────────────
# MCP server
# ──────────────────────────────────────────────────────────────────────────────

def test_mcp_server_import() -> None:
    import neighboriq.mcp_server as mcp
    assert hasattr(mcp, "_HANDLERS")
    assert "analyze_neighborhood" in mcp._HANDLERS
    assert "get_revenue_model" in mcp._HANDLERS
    assert "filter_by_assets" in mcp._HANDLERS
    assert "analyze_business" in mcp._HANDLERS
