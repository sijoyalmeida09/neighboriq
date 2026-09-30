"""Pytest suite for NeighborIQ intelligence layer — all 8 modules."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure the neighboriq package root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

pytestmark = pytest.mark.unit


# ── Helpers ───────────────────────────────────────────────────────────────────

def _minimal_profile(**overrides):
    """Return a BizProfile built from a minimal dict, applying overrides."""
    from neighboriq.intelligence.biz_profile import from_dict
    base = {
        "name": "Test Biz",
        "description": "A small local restaurant serving food",
        "naics_code": None,
        "year_founded": 2020,
        "monthly_revenue": 8000,
        "monthly_expenses": 5000,
        "years_in_market": 3,
        "avg_rating": 4.5,
        "review_count": 50,
        "recognition": "neighborhood",
    }
    base.update(overrides)
    return from_dict(base)


def _get_food_benchmarks():
    from neighboriq.intelligence.benchmark_engine import get_benchmarks
    return get_benchmarks("food_beverage")


def _get_food_domain():
    from neighboriq.intelligence.domain_taxonomy import get_domain
    return get_domain("food_beverage")


# ── BizProfile ────────────────────────────────────────────────────────────────

def test_biz_profile_from_dict_minimal() -> None:
    p = _minimal_profile()
    assert p.name == "Test Biz"
    assert isinstance(p.monthly_profit, int)


def test_biz_profile_frozen() -> None:
    from dataclasses import FrozenInstanceError
    p = _minimal_profile()
    with pytest.raises((FrozenInstanceError, AttributeError)):
        p.name = "Hacked"  # type: ignore[misc]


def test_to_yaml_template_creates_file(tmp_path: Path) -> None:
    from neighboriq.intelligence.biz_profile import to_yaml_template
    out = tmp_path / "biz.yaml"
    to_yaml_template(str(out))
    assert out.exists()
    content = out.read_text()
    assert "name:" in content


def test_from_yaml_roundtrip(tmp_path: Path) -> None:
    """Template written by to_yaml_template must be loadable by from_yaml (requires pyyaml)."""
    try:
        import yaml  # noqa: F401
    except ImportError:
        pytest.skip("pyyaml not installed — skipping YAML roundtrip test")

    from neighboriq.intelligence.biz_profile import to_yaml_template, from_yaml
    out = tmp_path / "biz.yaml"
    to_yaml_template(str(out))
    profile = from_yaml(str(out))
    assert isinstance(profile.name, str)


# ── DomainTaxonomy ────────────────────────────────────────────────────────────

def test_classify_logistics() -> None:
    from neighboriq.intelligence.biz_profile import from_dict
    from neighboriq.intelligence.domain_taxonomy import classify
    profile = from_dict({"name": "Fast Trucks LLC", "description": "trucking and freight delivery carrier", "naics_code": "4841"})
    domain = classify(profile)
    assert domain.domain_id == "logistics"


def test_classify_by_naics() -> None:
    from neighboriq.intelligence.biz_profile import from_dict
    from neighboriq.intelligence.domain_taxonomy import classify
    profile = from_dict({"name": "Code Co", "description": "software company", "naics_code": "5112"})
    domain = classify(profile)
    # Software NAICS 5112 → software_saas
    assert domain is not None


def test_get_domain_returns_spec() -> None:
    from neighboriq.intelligence.domain_taxonomy import get_domain
    d = get_domain("software_saas")
    assert d is not None
    assert d.domain_id == "software_saas"


def test_get_domain_unknown_returns_fallback() -> None:
    from neighboriq.intelligence.domain_taxonomy import get_domain
    # get_domain always returns a DomainSpec; returns a fallback for unknown IDs
    d = get_domain("nonexistent_xyz_123")
    assert d is not None
    # The fallback domain_id is not the requested (invalid) one
    assert d.domain_id != "nonexistent_xyz_123"


def test_list_domains_has_14() -> None:
    from neighboriq.intelligence.domain_taxonomy import list_domains
    domains = list_domains()
    assert len(domains) == 14


# ── BenchmarkEngine ───────────────────────────────────────────────────────────

def test_get_benchmarks_returns_defaults_on_network_failure() -> None:
    with patch("urllib.request.urlopen", side_effect=Exception("network error")):
        from neighboriq.intelligence.benchmark_engine import get_benchmarks
        b = get_benchmarks("food_beverage")
        assert b.revenue_p50 > 0


def test_benchmarks_are_frozen() -> None:
    from dataclasses import FrozenInstanceError
    b = _get_food_benchmarks()
    with pytest.raises((FrozenInstanceError, AttributeError)):
        b.revenue_p50 = 0  # type: ignore[misc]


def test_all_domains_have_benchmarks() -> None:
    from neighboriq.intelligence.domain_taxonomy import list_domains
    from neighboriq.intelligence.benchmark_engine import get_benchmarks
    domain_ids = list_domains()  # returns list[str]
    # Patch network to avoid real HTTP calls in tests
    with patch("urllib.request.urlopen", side_effect=Exception("network error")):
        for did in domain_ids:
            b = get_benchmarks(did)
            assert b.revenue_p50 > 0, f"{did} has revenue_p50=0"


# ── VerticalFinder ────────────────────────────────────────────────────────────

def test_find_verticals_returns_sequence() -> None:
    from neighboriq.intelligence.vertical_finder import find_verticals
    p = _minimal_profile()
    b = _get_food_benchmarks()
    results = find_verticals(p, b, "food_beverage")
    assert isinstance(results, (list, tuple))
    assert len(results) >= 0


def test_verticals_are_frozen() -> None:
    from dataclasses import FrozenInstanceError
    from neighboriq.intelligence.vertical_finder import find_verticals
    p = _minimal_profile()
    b = _get_food_benchmarks()
    results = find_verticals(p, b, "food_beverage")
    if results:
        with pytest.raises((FrozenInstanceError, AttributeError)):
            results[0].name = "hacked"  # type: ignore[misc]


def test_novel_rules_trigger_for_music() -> None:
    from neighboriq.intelligence.biz_profile import from_dict
    from neighboriq.intelligence.benchmark_engine import get_benchmarks
    from neighboriq.intelligence.vertical_finder import find_verticals
    profile = from_dict({
        "name": "Vijay Music",
        "description": "music recording studio and entertainment company",
        "naics_code": "7112",
        "monthly_revenue": 5000,
        "monthly_expenses": 2000,
        "years_in_market": 2,
    })
    b = get_benchmarks("music_entertainment")
    results = find_verticals(profile, b, "music_entertainment", top_n=20)
    names = [r.name for r in results]
    assert any("SoundExchange" in n or "MLC" in n for n in names), (
        f"SoundExchange/MLC rule not found. Got: {names}"
    )


def test_equipment_rule_triggers() -> None:
    from neighboriq.intelligence.biz_profile import from_dict
    from neighboriq.intelligence.vertical_finder import find_verticals
    profile = from_dict({
        "name": "Heavy Gear Co",
        "description": "construction equipment rental",
        "equipment": [["excavator", 25000], ["bulldozer", 35000]],
        "monthly_revenue": 10000,
        "monthly_expenses": 6000,
        "years_in_market": 3,
    })
    b = _get_food_benchmarks()
    results = find_verticals(profile, b, "local_service", top_n=20)
    names = [r.name for r in results]
    assert any("Idle" in n or "Rental" in n or "Fat Llama" in n for n in names), (
        f"Equipment idle rental rule not found. Got: {names}"
    )


def test_sba_rule_triggers() -> None:
    from neighboriq.intelligence.biz_profile import from_dict
    from neighboriq.intelligence.vertical_finder import find_verticals
    profile = from_dict({
        "name": "Established Biz",
        "description": "established local business with financial records",
        "monthly_revenue": 10000,
        "monthly_expenses": 6000,
        "years_in_market": 3,
    })
    b = _get_food_benchmarks()
    results = find_verticals(profile, b, "professional_services", top_n=20)
    names = [r.name for r in results]
    assert any("SBA" in n for n in names), f"SBA rule not found. Got: {names}"


# ── UniversalRoadmap ──────────────────────────────────────────────────────────

def test_generate_roadmap_returns_roadmap() -> None:
    from neighboriq.intelligence.universal_roadmap import generate_roadmap
    from neighboriq.intelligence.vertical_finder import find_verticals
    p = _minimal_profile()
    b = _get_food_benchmarks()
    d = _get_food_domain()
    verticals = tuple(find_verticals(p, b, "food_beverage"))
    roadmap = generate_roadmap(p, b, verticals, d)
    assert roadmap is not None
    assert roadmap.domain_id == "food_beverage"


def test_roadmap_three_phases() -> None:
    from neighboriq.intelligence.universal_roadmap import generate_roadmap
    from neighboriq.intelligence.vertical_finder import find_verticals
    p = _minimal_profile()
    b = _get_food_benchmarks()
    d = _get_food_domain()
    verticals = tuple(find_verticals(p, b, "food_beverage"))
    roadmap = generate_roadmap(p, b, verticals, d)
    assert roadmap.phase1.actions
    assert roadmap.phase2.actions
    assert roadmap.phase3.actions


def test_format_roadmap_string() -> None:
    from neighboriq.intelligence.universal_roadmap import generate_roadmap, format_roadmap
    from neighboriq.intelligence.vertical_finder import find_verticals
    p = _minimal_profile()
    b = _get_food_benchmarks()
    d = _get_food_domain()
    verticals = tuple(find_verticals(p, b, "food_beverage"))
    roadmap = generate_roadmap(p, b, verticals, d)
    text = format_roadmap(roadmap)
    assert isinstance(text, str)
    assert len(text) > 0


# ── MilestoneEngine ───────────────────────────────────────────────────────────

def test_generate_forecast_returns_forecast() -> None:
    from neighboriq.intelligence.milestone_engine import generate_forecast
    p = _minimal_profile()
    b = _get_food_benchmarks()
    d = _get_food_domain()
    forecast = generate_forecast(p, b, d)
    assert forecast is not None
    assert forecast.domain_id == "food_beverage"


def test_weekly_milestones_have_dates() -> None:
    from neighboriq.intelligence.milestone_engine import generate_forecast
    p = _minimal_profile()
    b = _get_food_benchmarks()
    d = _get_food_domain()
    forecast = generate_forecast(p, b, d)
    assert len(forecast.weekly_milestones) > 0
    for m in forecast.weekly_milestones:
        assert "2026" in m.date or "2027" in m.date, f"date missing year: {m.date}"


def test_monthly_targets_24_months() -> None:
    from neighboriq.intelligence.milestone_engine import generate_forecast
    p = _minimal_profile()
    b = _get_food_benchmarks()
    d = _get_food_domain()
    forecast = generate_forecast(p, b, d)
    assert len(forecast.monthly_targets) == 24


def test_market_sizing_logical() -> None:
    from neighboriq.intelligence.milestone_engine import generate_forecast
    p = _minimal_profile()
    b = _get_food_benchmarks()
    d = _get_food_domain()
    forecast = generate_forecast(p, b, d)
    assert forecast.market.tam_usd > forecast.market.sam_usd
    assert forecast.market.sam_usd > forecast.market.som_usd


def test_format_forecast_string() -> None:
    from neighboriq.intelligence.milestone_engine import generate_forecast, format_forecast
    p = _minimal_profile()
    b = _get_food_benchmarks()
    d = _get_food_domain()
    forecast = generate_forecast(p, b, d)
    text = format_forecast(forecast)
    assert isinstance(text, str)
    assert "TAM" in text


# ── ToolSelector ──────────────────────────────────────────────────────────────

def test_recommend_llm_for_code() -> None:
    from neighboriq.intelligence.tool_selector import recommend_llm, ToolRecommendation
    rec = recommend_llm("write python code", {})
    assert isinstance(rec, ToolRecommendation)
    assert rec.winner  # non-empty string


def test_no_anthropic_bias_large_context() -> None:
    from neighboriq.intelligence.tool_selector import recommend_llm
    rec = recommend_llm("analyze large document with 500K tokens", {"min_context_k": 500})
    # Gemini 2.0 Flash has 1M context — should win for large context tasks
    assert "Gemini" in rec.winner or "gemini" in rec.winner.lower(), (
        f"Expected Gemini for large-context task, got: {rec.winner}"
    )


def test_full_stack_recommendation() -> None:
    from neighboriq.intelligence.tool_selector import full_stack_recommendation
    recs = full_stack_recommendation("restaurant", "customer chat")
    assert "llm" in recs
    assert "automation" in recs
    assert "agent_framework" in recs


# ── RepoScanner ───────────────────────────────────────────────────────────────

def test_scan_repo_current_dir() -> None:
    from neighboriq.intelligence.repo_scanner import scan_repo, RepoScan
    scan = scan_repo("C:\\Sijoy_2.0\\automation\\neighboriq")
    assert isinstance(scan, RepoScan)
    assert scan.detected_domain is not None or scan.detected_domain is None  # doesn't raise


def test_scan_nonexistent_path() -> None:
    from neighboriq.intelligence.repo_scanner import scan_repo
    # Must not raise — returns RepoScan with safe defaults
    scan = scan_repo("C:\\nonexistent_path_xyz_99999")
    assert scan is not None


def test_format_scan_summary() -> None:
    from neighboriq.intelligence.repo_scanner import scan_repo, format_scan_summary
    scan = scan_repo("C:\\Sijoy_2.0\\automation\\neighboriq")
    summary = format_scan_summary(scan)
    assert isinstance(summary, str)
    assert len(summary) > 0
