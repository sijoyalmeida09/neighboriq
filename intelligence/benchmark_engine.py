"""benchmark_engine.py — Real benchmark data from free government and academic sources.

Sources (all free, no mandatory API keys):
  1. Damodaran (NYU Stern) — net/gross/EBITDA margins for 100+ industries, annual XLS
  2. Census SUSB — revenue and payroll per establishment by NAICS code
  3. BLS OES — average hourly wages by industry sector
  4. FRED — sector-level growth rates and economic indicators

All fetchers return empty dict / fallback values on any error — never raise.
Results are cached as JSON in data/benchmarks/ with a 30-day TTL.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

__all__ = ["DomainBenchmarks", "get_benchmarks"]

# ── Cache directory ───────────────────────────────────────────────────────────
_CACHE_DIR = Path(__file__).parent.parent / "data" / "benchmarks"
_CACHE_TTL_DAYS = 30


def _warn(msg: str) -> None:
    if os.environ.get("NEIGHBORIQ_DEBUG") == "1":
        print(f"[benchmark_engine] {msg}", file=sys.stderr)


def _cache_path(key: str) -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / f"{key}.json"


def _load_cache(key: str) -> dict | None:
    p = _cache_path(key)
    try:
        if p.exists():
            age_days = (time.time() - p.stat().st_mtime) / 86400
            if age_days < _CACHE_TTL_DAYS:
                return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        _warn(f"cache read failed for {key}: {exc}")
    return None


def _save_cache(key: str, data: dict) -> None:
    try:
        _cache_path(key).write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as exc:
        _warn(f"cache write failed for {key}: {exc}")


# ── Main output dataclass ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class DomainBenchmarks:
    domain_id: str
    industry_label: str

    # Revenue percentiles — single location / solo operator ($/mo)
    revenue_p25: int
    revenue_p50: int
    revenue_p75: int

    # Profitability (Damodaran)
    net_margin_typical: float
    gross_margin_typical: float
    ebitda_margin: float

    # Labor (BLS OES)
    avg_hourly_wage: float
    employee_revenue_ratio: int     # $/employee/year

    # Customer metrics (derived)
    customer_ltv_typical: int
    churn_annual: float | None      # None for non-subscription businesses

    # Growth (FRED)
    growth_rate_industry: float     # % YoY

    # Cost breakdown
    top_costs_pct: dict[str, float]

    # Metadata
    data_sources: tuple[str, ...]
    vintage_year: int
    confidence: str                 # "HIGH" | "MEDIUM" | "LOW"


# ── Domain defaults (fallback when all APIs fail) ─────────────────────────────

_DOMAIN_DEFAULTS: dict[str, dict] = {
    "local_service":        {"net_margin": 0.15, "gross_margin": 0.65, "revenue_p50_monthly": 8_000,   "growth": 2.5},
    "food_beverage":        {"net_margin": 0.05, "gross_margin": 0.65, "revenue_p50_monthly": 35_000,  "growth": 3.0},
    "healthcare":           {"net_margin": 0.08, "gross_margin": 0.45, "revenue_p50_monthly": 45_000,  "growth": 5.5},
    "logistics":            {"net_margin": 0.06, "gross_margin": 0.35, "revenue_p50_monthly": 85_000,  "growth": 4.0},
    "distribution":         {"net_margin": 0.04, "gross_margin": 0.28, "revenue_p50_monthly": 120_000, "growth": 3.5},
    "manufacturing":        {"net_margin": 0.08, "gross_margin": 0.35, "revenue_p50_monthly": 75_000,  "growth": 2.8},
    "software_saas":        {"net_margin": 0.18, "gross_margin": 0.72, "revenue_p50_monthly": 25_000,  "growth": 15.0},
    "agency_services":      {"net_margin": 0.20, "gross_margin": 0.55, "revenue_p50_monthly": 30_000,  "growth": 5.0},
    "music_entertainment":  {"net_margin": 0.12, "gross_margin": 0.55, "revenue_p50_monthly": 15_000,  "growth": 6.0},
    "retail":               {"net_margin": 0.04, "gross_margin": 0.40, "revenue_p50_monthly": 50_000,  "growth": 3.0},
    "real_estate":          {"net_margin": 0.25, "gross_margin": 0.60, "revenue_p50_monthly": 20_000,  "growth": 4.5},
    "education":            {"net_margin": 0.15, "gross_margin": 0.60, "revenue_p50_monthly": 18_000,  "growth": 4.0},
    "creative_media":       {"net_margin": 0.18, "gross_margin": 0.65, "revenue_p50_monthly": 12_000,  "growth": 7.0},
    "professional_services":{"net_margin": 0.22, "gross_margin": 0.60, "revenue_p50_monthly": 35_000,  "growth": 4.0},
}

# NAICS-prefix overrides — more accurate than broad domain defaults for specific industries
# Sources: Census SUSB 2022 NAICS 812210 (funeral directors), NFDA industry data
_NAICS_DEFAULTS: dict[str, dict] = {
    "8122": {"net_margin": 0.18, "gross_margin": 0.65, "revenue_p50_monthly": 65_000, "growth": 2.0,
             "revenue_p25_monthly": 35_000, "revenue_p75_monthly": 110_000, "avg_wage": 28.0,
             "employee_revenue_ratio": 175_000},  # funeral services
    "6211": {"net_margin": 0.12, "gross_margin": 0.55, "revenue_p50_monthly": 55_000, "growth": 5.0,
             "revenue_p25_monthly": 30_000, "revenue_p75_monthly": 90_000, "avg_wage": 35.0},  # physician offices
    "4841": {"net_margin": 0.07, "gross_margin": 0.38, "revenue_p50_monthly": 95_000, "growth": 4.5,
             "revenue_p25_monthly": 52_000, "revenue_p75_monthly": 180_000, "avg_wage": 24.0},  # general freight trucking
}

# Customer LTV and churn estimates per domain (not available from free APIs — domain knowledge)
_DOMAIN_LTV: dict[str, tuple[int, float | None]] = {
    # (ltv_usd, annual_churn or None)
    "local_service":        (3_500,   None),
    "food_beverage":        (2_200,   None),
    "healthcare":           (6_000,   None),
    "logistics":            (45_000,  0.12),
    "distribution":         (80_000,  0.08),
    "manufacturing":        (120_000, 0.10),
    "software_saas":        (8_000,   0.15),
    "agency_services":      (18_000,  0.20),
    "music_entertainment":  (1_200,   None),
    "retail":               (1_800,   None),
    "real_estate":          (15_000,  None),
    "education":            (7_500,   None),
    "creative_media":       (5_000,   0.25),
    "professional_services":(12_000,  0.10),
}


# ── Source 1: Damodaran ───────────────────────────────────────────────────────

_DAMODARAN_URL = "http://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/margin.html"

_DAMODARAN_KEYWORDS: dict[str, list[str]] = {
    "local_service":         ["personal services", "laundry", "personal"],
    "food_beverage":         ["restaurant", "food service", "hotels"],
    "healthcare":            ["healthcare", "health information", "medical"],
    "logistics":             ["trucking", "transportation"],
    "distribution":          ["wholesale", "distribution"],
    "manufacturing":         ["manufacturing", "industrial", "machinery"],
    "software_saas":         ["software (internet & cloud)", "software", "information technology"],
    "agency_services":       ["advertising", "consulting", "business services"],
    "music_entertainment":   ["entertainment", "recreation", "broadcasting"],
    "retail":                ["retail (online)", "retail (general)", "retail"],
    "real_estate":           ["real estate", "reits"],
    "education":             ["education", "schools"],
    "creative_media":        ["publishing", "broadcasting", "media"],
    "professional_services": ["legal", "accounting", "financial services"],
}


class _MarginTableParser(HTMLParser):
    """Extracts rows from Damodaran's margin HTML table."""

    def __init__(self) -> None:
        super().__init__()
        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._current_row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "table":
            self._in_table = True
        elif tag == "tr" and self._in_table:
            self._in_row = True
            self._current_row = []
        elif tag in ("td", "th") and self._in_row:
            self._in_cell = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "table":
            self._in_table = False
        elif tag == "tr" and self._in_row:
            self._in_row = False
            if self._current_row:
                self.rows.append(self._current_row)
        elif tag in ("td", "th"):
            self._in_cell = False

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._current_row.append(data.strip())


def _parse_pct(value: str) -> float | None:
    """Parse '12.34%' → 0.1234, or return None for 'N/A' / empty."""
    value = value.strip().rstrip("%")
    try:
        return float(value) / 100.0
    except ValueError:
        return None


def _fetch_damodaran_margins() -> dict[str, dict[str, float]]:
    """Returns {industry_name: {net_margin, ebit_margin, ebitda_margin}}."""
    cached = _load_cache("damodaran_margins")
    if cached is not None:
        return cached

    try:
        req = urllib.request.Request(
            _DAMODARAN_URL,
            headers={"User-Agent": "NeighborIQ/2.0 (business intelligence research)"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        _warn(f"Damodaran fetch failed: {exc}")
        return {}

    parser = _MarginTableParser()
    parser.feed(html)

    result: dict[str, dict[str, float]] = {}
    for row in parser.rows:
        if len(row) < 4:
            continue
        industry = row[0].strip()
        if not industry or industry.lower() in ("industry name", "industry", ""):
            continue
        # Columns vary; try positions 2,3,4 for net/ebit/ebitda
        net = _parse_pct(row[2]) if len(row) > 2 else None
        ebit = _parse_pct(row[3]) if len(row) > 3 else None
        ebitda = _parse_pct(row[4]) if len(row) > 4 else None
        if net is not None:
            result[industry.lower()] = {
                "net_margin": net,
                "ebit_margin": ebit if ebit is not None else net * 1.3,
                "ebitda_margin": ebitda if ebitda is not None else net * 1.6,
            }

    if result:
        _save_cache("damodaran_margins", result)
        _warn(f"Damodaran: loaded {len(result)} industries")
    return result


def _find_damodaran_industry(
    domain_id: str, margins: dict[str, dict[str, float]]
) -> dict[str, float] | None:
    """Keyword match domain_id → best Damodaran industry entry."""
    keywords = _DAMODARAN_KEYWORDS.get(domain_id, [domain_id.replace("_", " ")])
    for keyword in keywords:
        kw = keyword.lower()
        # Exact match first
        if kw in margins:
            return margins[kw]
        # Substring match
        for name, data in margins.items():
            if kw in name:
                return data
    return None


# ── Source 2: Census SUSB ─────────────────────────────────────────────────────

_SUSB_BASE = "https://api.census.gov/data/2022/susb"

# Domain → primary NAICS prefix (3–4 digits)
_DOMAIN_NAICS: dict[str, str] = {
    "local_service":         "812",
    "food_beverage":         "722",
    "healthcare":            "621",
    "logistics":             "484",
    "distribution":          "423",
    "manufacturing":         "311",
    "software_saas":         "5112",
    "agency_services":       "5418",
    "music_entertainment":   "711",
    "retail":                "441",
    "real_estate":           "531",
    "education":             "611",
    "creative_media":        "5121",
    "professional_services": "5411",
}


def _fetch_census_susb(naics_prefix: str) -> dict[str, int]:
    """Returns {receipts_total, emp_total, payroll_total, estab_count} or {}."""
    cache_key = f"susb_{naics_prefix}"
    cached = _load_cache(cache_key)
    if cached is not None:
        return cached

    params = urllib.parse.urlencode({
        "get": "NAICS2022,RCPTOT,EMP,PAYANN,ESTAB",
        "NAICS2022": naics_prefix,
        "EMPSZES": "1",
    })
    url = f"{_SUSB_BASE}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as exc:
        _warn(f"Census SUSB fetch failed for NAICS {naics_prefix}: {exc}")
        return {}

    if not isinstance(data, list) or len(data) < 2:
        return {}

    headers = data[0]
    try:
        idx = {h: i for i, h in enumerate(headers)}
        totals: dict[str, int] = {
            "receipts_total": 0,
            "emp_total": 0,
            "payroll_total": 0,
            "estab_count": 0,
        }
        for row in data[1:]:
            def _int(col: str) -> int:
                try:
                    return int(row[idx[col]]) if col in idx else 0
                except (ValueError, TypeError):
                    return 0

            totals["receipts_total"] += _int("RCPTOT")
            totals["emp_total"] += _int("EMP")
            totals["payroll_total"] += _int("PAYANN")
            totals["estab_count"] += _int("ESTAB")

        _save_cache(cache_key, totals)
        _warn(f"SUSB NAICS {naics_prefix}: {totals['estab_count']} establishments")
        return totals
    except Exception as exc:
        _warn(f"SUSB parse failed: {exc}")
        return {}


def _estimate_revenue_percentiles(
    susb_data: dict[str, int], p50_fallback: int
) -> tuple[int, int, int]:
    """Derive p25/p50/p75 monthly revenue from SUSB establishment averages."""
    estab = susb_data.get("estab_count", 0)
    receipts = susb_data.get("receipts_total", 0)

    if estab > 0 and receipts > 0:
        # SUSB receipts are in $1000s
        avg_annual = (receipts * 1000) / estab
        avg_monthly = int(avg_annual / 12)
        return (
            int(avg_monthly * 0.55),
            int(avg_monthly * 0.85),
            int(avg_monthly * 1.30),
        )

    return (
        int(p50_fallback * 0.60),
        p50_fallback,
        int(p50_fallback * 1.55),
    )


# ── Source 3: BLS OES ─────────────────────────────────────────────────────────

_BLS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

_BLS_SERIES: dict[str, str] = {
    "food_beverage":         "CEU0800000008",
    "retail":                "CEU4300000008",
    "logistics":             "CEU4900000008",
    "distribution":          "CEU4300000008",
    "healthcare":            "CEU6500000008",
    "professional_services": "CEU5500000008",
    "software_saas":         "CEU5500000008",
    "agency_services":       "CEU5500000008",
    "manufacturing":         "CEU3000000008",
    "local_service":         "CEU0700000008",
    "music_entertainment":   "CEU0800000008",
    "real_estate":           "CEU5500000008",
    "education":             "CEU6500000008",
    "creative_media":        "CEU5500000008",
}
_BLS_FALLBACK_WAGE = 18.0  # US median service worker 2024


def _fetch_bls_avg_hourly_wage(domain_id: str) -> float:
    """Returns average hourly wage ($/hr) for the domain's typical worker."""
    cache_key = f"bls_wage_{domain_id}"
    cached = _load_cache(cache_key)
    if cached is not None:
        return float(cached.get("hourly_wage", _BLS_FALLBACK_WAGE))

    series_id = _BLS_SERIES.get(domain_id, "CEU0500000008")
    payload = json.dumps({
        "seriesid": [series_id],
        "startyear": "2023",
        "endyear": "2024",
    }).encode()

    try:
        req = urllib.request.Request(
            _BLS_API,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())

        series_list = result.get("Results", {}).get("series", [])
        if not series_list:
            return _BLS_FALLBACK_WAGE

        data_points = series_list[0].get("data", [])
        if not data_points:
            return _BLS_FALLBACK_WAGE

        # data is sorted desc by time; take first (most recent) annual average
        for point in data_points:
            if point.get("period") == "M13":  # annual average
                wage = float(point["value"])
                _save_cache(cache_key, {"hourly_wage": wage})
                _warn(f"BLS {series_id}: ${wage}/hr")
                return wage

        # Fallback: take most recent monthly value
        wage = float(data_points[0]["value"])
        _save_cache(cache_key, {"hourly_wage": wage})
        return wage

    except Exception as exc:
        _warn(f"BLS fetch failed for {domain_id}: {exc}")
        return _BLS_FALLBACK_WAGE


# ── Source 4: FRED ────────────────────────────────────────────────────────────

_FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

_FRED_GROWTH_SERIES: dict[str, str] = {
    "logistics":        "TRFVOLUSM227NFWA",
    "real_estate":      "RRVRUSQ156N",
    "food_beverage":    "RSFSDP",
    "retail":           "RSCCAS",
    "manufacturing":    "IPMAN",
    "healthcare":       "HLTHSCPCHCSA",
    "software_saas":    "DGORDER",
}
_FRED_DEFAULT_SERIES = "GDP"


def _fetch_fred_growth_rate(domain_id: str) -> float:
    """Returns YoY % growth rate for the domain's sector proxy. Fallback = 3.0."""
    cache_key = f"fred_growth_{domain_id}"
    cached = _load_cache(cache_key)
    if cached is not None:
        return float(cached.get("growth_rate", 3.0))

    series_id = _FRED_GROWTH_SERIES.get(domain_id, _FRED_DEFAULT_SERIES)
    api_key = os.environ.get("FRED_API_KEY", "")
    params: dict[str, str] = {
        "series_id": series_id,
        "file_type": "json",
        "sort_order": "desc",
        "limit": "13",
    }
    if api_key:
        params["api_key"] = api_key

    url = f"{_FRED_BASE}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())

        observations = data.get("observations", [])
        valid = [o for o in observations if o.get("value") not in (".", "", None)]
        if len(valid) < 2:
            return 3.0

        latest = float(valid[0]["value"])
        year_ago = float(valid[-1]["value"])
        if year_ago == 0:
            return 3.0

        growth = (latest - year_ago) / abs(year_ago) * 100.0
        # Cap at reasonable range
        growth = max(-20.0, min(50.0, growth))
        _save_cache(cache_key, {"growth_rate": growth})
        _warn(f"FRED {series_id}: {growth:.1f}% YoY")
        return growth

    except Exception as exc:
        _warn(f"FRED fetch failed for {domain_id}: {exc}")
        return 3.0


# ── Cost estimation ───────────────────────────────────────────────────────────

_SERVICE_DOMAINS = {
    "local_service", "food_beverage", "healthcare", "agency_services",
    "music_entertainment", "education", "creative_media", "professional_services",
    "real_estate", "software_saas",
}


def _estimate_costs(
    net_margin: float, gross_margin: float, domain_id: str
) -> dict[str, float]:
    """Estimate cost breakdown from margins and domain type."""
    cogs = round(1.0 - gross_margin, 3)
    remaining = round(gross_margin - net_margin, 3)

    is_service = domain_id in _SERVICE_DOMAINS
    labor_of_remaining = 0.50 if is_service else 0.30
    rent_of_remaining = 0.18 if domain_id in {"food_beverage", "retail", "local_service"} else 0.10
    marketing_of_remaining = 0.12

    labor = round(remaining * labor_of_remaining, 3)
    rent = round(remaining * rent_of_remaining, 3)
    marketing = round(remaining * marketing_of_remaining, 3)
    overhead = round(remaining - labor - rent - marketing, 3)

    costs: dict[str, float] = {}
    if cogs > 0.01:
        costs["cogs"] = cogs
    costs["labor"] = labor
    if rent > 0.005:
        costs["rent"] = rent
    costs["marketing"] = marketing
    if overhead > 0.005:
        costs["overhead"] = overhead

    return costs


# ── Main public function ──────────────────────────────────────────────────────

def get_benchmarks(
    domain_id: str,
    naics_prefix: str | None = None,
    force_refresh: bool = False,
) -> DomainBenchmarks:
    """Fetch and combine real benchmark data for a business domain.

    Data sources tried in order:
      1. Damodaran NYU → margin benchmarks
      2. Census SUSB → revenue per establishment
      3. BLS OES → avg hourly wage
      4. FRED → industry growth rate
    Falls back to hardcoded defaults when sources are unavailable.
    Results cached 30 days in data/benchmarks/.
    """
    cache_key = f"combined_{domain_id}"
    if not force_refresh:
        cached = _load_cache(cache_key)
        if cached is not None:
            costs = cached.pop("top_costs_pct_json", {})
            sources_list = cached.pop("data_sources_list", ["cache"])
            return DomainBenchmarks(
                **cached,
                top_costs_pct=costs,
                data_sources=tuple(sources_list),
            )

    defaults = _DOMAIN_DEFAULTS.get(domain_id, _DOMAIN_DEFAULTS["professional_services"])
    ltv, churn = _DOMAIN_LTV.get(domain_id, (5_000, None))
    sources_used: list[str] = []
    current_year = 2026

    # Apply NAICS-prefix override when a more accurate baseline exists
    _naics_key = (naics_prefix or "")[:4]
    if _naics_key in _NAICS_DEFAULTS:
        defaults = {**defaults, **_NAICS_DEFAULTS[_naics_key]}
        sources_used.append(f"NAICS-{_naics_key} industry baseline")

    # 1. Damodaran margins
    raw_damodaran = _fetch_damodaran_margins()
    margin_data = _find_damodaran_industry(domain_id, raw_damodaran)
    if margin_data:
        net_margin = margin_data["net_margin"]
        gross_margin = margin_data.get("ebit_margin", net_margin * 1.3)
        ebitda_margin = margin_data.get("ebitda_margin", net_margin * 1.6)
        industry_label = domain_id.replace("_", " ").title()
        confidence = "HIGH"
        sources_used.append("Damodaran NYU Stern Industry Margins 2026")
    else:
        net_margin = defaults["net_margin"]
        gross_margin = defaults["gross_margin"]
        ebitda_margin = net_margin * 1.6
        industry_label = domain_id.replace("_", " ").title()
        confidence = "LOW"
        sources_used.append("hardcoded_defaults")

    # 2. Census SUSB
    naics = naics_prefix or _DOMAIN_NAICS.get(domain_id, "")
    susb = _fetch_census_susb(naics) if naics else {}
    p50_fallback = defaults["revenue_p50_monthly"]
    p25, p50, p75 = _estimate_revenue_percentiles(susb, p50_fallback)
    # Override p25/p75 with NAICS-specific values when available (more accurate than derived ratios)
    if "revenue_p25_monthly" in defaults:
        p25 = defaults["revenue_p25_monthly"]
    if "revenue_p75_monthly" in defaults:
        p75 = defaults["revenue_p75_monthly"]
    if susb:
        sources_used.append("Census SUSB 2022")
        confidence = "HIGH" if confidence == "HIGH" else "MEDIUM"
        emp = susb.get("emp_total", 0)
        estab = susb.get("estab_count", 0)
        payroll = susb.get("payroll_total", 0)
        # payroll in $1000s, emp = total employees across all establishments
        employee_revenue_ratio = int((p50 * 12) / max(emp / max(estab, 1), 1)) if emp > 0 else int(p50 * 4)
    else:
        employee_revenue_ratio = int(p50 * 4)  # rough: 1 employee per $4K/mo revenue

    # 3. BLS hourly wage
    avg_wage = _fetch_bls_avg_hourly_wage(domain_id)
    if avg_wage != _BLS_FALLBACK_WAGE:
        sources_used.append("BLS OES 2024")

    # 4. FRED growth
    growth_rate = _fetch_fred_growth_rate(domain_id)
    fred_series = _FRED_GROWTH_SERIES.get(domain_id)
    if fred_series:
        sources_used.append(f"FRED {fred_series}")

    # Derive costs
    top_costs = _estimate_costs(net_margin, gross_margin, domain_id)

    benchmarks = DomainBenchmarks(
        domain_id=domain_id,
        industry_label=industry_label,
        revenue_p25=p25,
        revenue_p50=p50,
        revenue_p75=p75,
        net_margin_typical=round(net_margin, 4),
        gross_margin_typical=round(gross_margin, 4),
        ebitda_margin=round(ebitda_margin, 4),
        avg_hourly_wage=avg_wage,
        employee_revenue_ratio=employee_revenue_ratio,
        customer_ltv_typical=ltv,
        churn_annual=churn,
        growth_rate_industry=round(growth_rate, 2),
        top_costs_pct=top_costs,
        data_sources=tuple(sources_used) if sources_used else ("hardcoded_defaults",),
        vintage_year=current_year,
        confidence=confidence,
    )

    # Cache the combined result (serialize dict/tuple for JSON)
    cache_payload = {
        "domain_id": benchmarks.domain_id,
        "industry_label": benchmarks.industry_label,
        "revenue_p25": benchmarks.revenue_p25,
        "revenue_p50": benchmarks.revenue_p50,
        "revenue_p75": benchmarks.revenue_p75,
        "net_margin_typical": benchmarks.net_margin_typical,
        "gross_margin_typical": benchmarks.gross_margin_typical,
        "ebitda_margin": benchmarks.ebitda_margin,
        "avg_hourly_wage": benchmarks.avg_hourly_wage,
        "employee_revenue_ratio": benchmarks.employee_revenue_ratio,
        "customer_ltv_typical": benchmarks.customer_ltv_typical,
        "churn_annual": benchmarks.churn_annual,
        "growth_rate_industry": benchmarks.growth_rate_industry,
        "vintage_year": benchmarks.vintage_year,
        "confidence": benchmarks.confidence,
        "top_costs_pct_json": top_costs,
        "data_sources_list": list(benchmarks.data_sources),
    }
    _save_cache(cache_key, cache_payload)

    return benchmarks
