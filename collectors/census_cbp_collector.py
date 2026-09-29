"""census_cbp_collector.py — Census County Business Patterns (CBP) data for a zip code.

Provides exact business-establishment counts by NAICS code from the US Census Bureau.
No API key required for <500 calls/day. Set CENSUS_API_KEY for higher rate limits.

API docs: https://www.census.gov/data/developers/data-sets/cbp-nonemp-zbp/cbp.html
Endpoint:  https://api.census.gov/data/2021/cbp
Vintage 2021 is the latest available as of 2024.

Returns [] on any error — never blocks the pipeline.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

__all__ = [
    "get_business_counts_by_zip",
    "naics_to_niche",
    "get_niche_counts_for_zip",
    "is_available",
]

log = logging.getLogger("census_cbp_collector")

_CBP_BASE = "https://api.census.gov/data/2021/cbp"
_TIMEOUT = 12  # seconds

# NAICS 2017 prefix → NeighborIQ niche label (first match wins)
_NAICS_MAP: list[tuple[str, str]] = [
    # Food & Beverage
    ("7225",  "bar"),                   # Drinking places (no food)
    ("72251", "bar"),
    ("72232", "bakery"),               # Retail bakeries
    ("7223",  "bakery"),
    ("72231", "coffee_shop"),          # Mobile food services (coffee carts etc)
    ("72241", "bar"),                  # Drinking places (alcoholic)
    ("722513","fast_food"),
    ("722515","fast_food"),
    ("722511","full_service_restaurant"),
    ("7224",  "bar"),
    ("7221",  "full_service_restaurant"),
    ("7222",  "fast_food"),
    ("722",   "full_service_restaurant"),  # Broad food services fallback
    # Retail
    ("4453",  "convenience_store"),    # Fruit & veg / specialty food stores
    ("44511", "grocery_store"),
    ("4451",  "grocery_store"),
    ("4453",  "specialty_food_store"),
    ("44521", "liquor_store"),
    ("4452",  "liquor_store"),
    ("4461",  "pharmacy"),
    ("446",   "pharmacy"),
    ("4471",  "gas_station"),          # Gasoline stations
    ("447",   "gas_station"),
    ("4481",  "clothing_store"),
    ("448",   "clothing_store"),
    ("4511",  "sporting_goods"),
    ("452",   "general_merchandise"),
    ("453",   "general_merchandise"),
    # Personal Services
    ("81211", "barbershop"),
    ("81219", "nail_salon"),
    ("8121",  "hair_salon"),
    ("812",   "hair_salon"),
    ("81231", "dry_cleaning"),
    ("8123",  "laundromat"),
    # Health & Fitness
    ("71394", "gym"),
    ("713940","gym"),
    ("7139",  "gym"),
    ("621",   "healthcare"),
    ("6211",  "doctor_office"),
    ("6212",  "dentist"),
    ("6213",  "dentist"),
    # Education
    ("6116",  "tutoring_center"),
    ("611",   "education"),
    # Child Care
    ("6244",  "daycare"),
    ("624",   "daycare"),
    # Auto
    ("4411",  "auto_dealer"),
    ("441",   "auto_dealer"),
    ("4413",  "auto_parts"),
    ("8111",  "auto_repair"),
    ("811",   "auto_repair"),
    # Professional Services
    ("541",   "professional_services"),
    ("5411",  "legal"),
    ("5412",  "accounting"),
    ("5415",  "it_services"),
    ("5416",  "consulting"),
    # Real Estate
    ("531",   "real_estate"),
    # Construction
    ("236",   "construction"),
    ("238",   "construction"),
]


def naics_to_niche(naics_code: str) -> str:
    """Map a NAICS code string to a NeighborIQ niche label.

    Tries longest prefix first so 722513 (fast_food) wins over 722 (restaurant).
    Returns 'other' if no match.
    """
    code = naics_code.strip()
    # Sort by length descending to get most-specific match first
    for prefix, niche in sorted(_NAICS_MAP, key=lambda x: -len(x[0])):
        if code.startswith(prefix):
            return niche
    return "other"


def _build_url(zip_code: str, api_key: Optional[str] = None) -> str:
    params: dict[str, str] = {
        "get": "NAICS2017,NAICS2017_LABEL,ESTAB,EMP",
        "for": f"zipcode:{zip_code.zfill(5)}",
    }
    if api_key:
        params["key"] = api_key
    return f"{_CBP_BASE}?{urllib.parse.urlencode(params)}"


def get_business_counts_by_zip(zip_code: str) -> list[dict]:
    """
    Fetch business establishment counts from Census CBP for a zip code.

    Returns list of dicts with keys:
      naics_code, naics_label, establishments, employees, niche
    Returns [] on any error or if data is unavailable.
    """
    api_key = os.environ.get("CENSUS_API_KEY", "").strip() or None
    url = _build_url(zip_code, api_key)

    log.info("Census CBP: fetching zip %s", zip_code.zfill(5))
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "NeighborIQ/0.2 (research; contact via GitHub)"},
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 204:
            log.info("Census CBP: no data for zip %s (204 No Content)", zip_code)
        else:
            log.warning("Census CBP HTTP %s for zip %s: %s", exc.code, zip_code, exc.reason)
        return []
    except Exception as exc:
        log.warning("Census CBP fetch failed for zip %s: %s", zip_code, exc)
        return []

    try:
        rows: list[list[str]] = json.loads(raw)
    except Exception as exc:
        log.warning("Census CBP: JSON parse failed for zip %s: %s", zip_code, exc)
        return []

    if not rows or len(rows) < 2:
        log.info("Census CBP: empty result for zip %s", zip_code)
        return []

    header = rows[0]
    try:
        idx_naics = header.index("NAICS2017")
        idx_label = header.index("NAICS2017_LABEL")
        idx_estab = header.index("ESTAB")
        idx_emp   = header.index("EMP")
    except ValueError:
        log.warning("Census CBP: unexpected column names: %s", header)
        return []

    results: list[dict] = []
    for row in rows[1:]:
        if len(row) <= max(idx_naics, idx_label, idx_estab, idx_emp):
            continue
        naics_code = (row[idx_naics] or "").strip()
        if not naics_code or naics_code == "00":
            continue  # skip totals row

        try:
            establishments = int(row[idx_estab] or "0")
        except ValueError:
            establishments = 0

        try:
            employees = int(row[idx_emp] or "0")
        except ValueError:
            employees = 0

        results.append({
            "naics_code":     naics_code,
            "naics_label":    (row[idx_label] or "").strip(),
            "establishments": establishments,
            "employees":      employees,
            "niche":          naics_to_niche(naics_code),
        })

    log.info(
        "Census CBP: %d NAICS rows loaded for zip %s",
        len(results), zip_code.zfill(5),
    )
    return results


def get_niche_counts_for_zip(zip_code: str) -> dict[str, int]:
    """
    Aggregate Census CBP establishment counts into NeighborIQ niche buckets.

    Returns dict mapping niche → total establishment count.
    Returns {} on any error.
    """
    rows = get_business_counts_by_zip(zip_code)
    counts: dict[str, int] = {}
    for row in rows:
        niche = row["niche"]
        if niche == "other":
            continue
        counts[niche] = counts.get(niche, 0) + row["establishments"]
    return counts


def is_available() -> bool:
    """Always True — CBP API is free and has no local dependency."""
    return True
