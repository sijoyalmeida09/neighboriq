"""census_collector.py — US Census ACS 5-year demographic data retrieval.

Requires free Census API key: https://api.census.gov/data/key_signup.html
Set env var CENSUS_API_KEY before running.

Variables:
  B01003_001E — total population
  B19013_001E — median household income
  B01002_001E  — median age
  B11001_001E  — total households
"""
from __future__ import annotations

import logging
import os

import requests

log = logging.getLogger("neighboriq.collectors.census")

_BASE_URL = "https://api.census.gov/data/2022/acs/acs5"
_VARS = "B01003_001E,B19013_001E,B01002_001E,B11001_001E"
_TIMEOUT = 10
_API_KEY = os.environ.get("CENSUS_API_KEY", "")

_DEFAULTS: dict = {
    "population": 0,
    "median_income": 0,
    "age_median": 0.0,
    "growth_rate_5yr": 0.0,
    "households": 0,
    "source": "census_acs",
}


def _safe_int(val: str | None) -> int:
    try:
        v = int(val or 0)
        return max(v, 0)
    except (ValueError, TypeError):
        return 0


def _safe_float(val: str | None) -> float:
    try:
        v = float(val or 0)
        return max(v, 0.0)
    except (ValueError, TypeError):
        return 0.0


def get_demographics(zip_code: str) -> dict:
    """Fetch ACS 5-year demographic data for a US zip code.

    Returns a dict with population, median_income, age_median, growth_rate_5yr,
    households, and source. All numeric fields default to 0 on API failure.
    """
    if not _API_KEY:
        log.warning(
            "CENSUS_API_KEY not set — demographics will be zero. "
            "Get a free key at https://api.census.gov/data/key_signup.html"
        )
        return {"zip_code": zip_code, **_DEFAULTS}

    try:
        params: dict = {
            "get": _VARS,
            "for": f"zip code tabulation area:{zip_code}",
            "key": _API_KEY,
        }
        resp = requests.get(_BASE_URL, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        rows = resp.json()
        if len(rows) < 2:
            log.warning("No Census data returned for zip %s", zip_code)
            return {"zip_code": zip_code, **_DEFAULTS}

        # rows[0] = header, rows[1] = data
        header = rows[0]
        data = rows[1]
        row = dict(zip(header, data))

        population = _safe_int(row.get("B01003_001E"))
        median_income = _safe_int(row.get("B19013_001E"))
        age_median = _safe_float(row.get("B01002_001E"))
        households = _safe_int(row.get("B11001_001E"))

        # growth_rate_5yr: Census doesn't give a direct growth rate in ACS5.
        # We use households as a proxy — stored for future enrichment via
        # comparison against 2017 ACS data. Default 0.0 until enriched.
        growth_rate_5yr = 0.0

        log.info(
            "Census data for zip %s: pop=%d, income=%d, age=%.1f, households=%d",
            zip_code, population, median_income, age_median, households,
        )
        return {
            "zip_code": zip_code,
            "population": population,
            "median_income": median_income,
            "age_median": age_median,
            "growth_rate_5yr": growth_rate_5yr,
            "households": households,
            "source": "census_acs",
        }

    except requests.RequestException as exc:
        log.error("Census API request failed for zip %s: %s", zip_code, exc)
    except Exception as exc:
        log.error("Unexpected error fetching Census data for zip %s: %s", zip_code, exc)

    return {"zip_code": zip_code, **_DEFAULTS}


def get_demographics_batch(zip_codes: list[str]) -> dict[str, dict]:
    """Fetch demographics for multiple zip codes.

    Returns a dict keyed by zip_code. Failed zips get zero-filled defaults.
    """
    return {z: get_demographics(z) for z in zip_codes}
