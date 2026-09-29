"""safegraph_collector.py — Load SafeGraph Places CSV data for a zip code.

SafeGraph Places: 8M+ US POIs with category, visit counts, hours.
Free academic/OSS access: https://www.safegraph.com/free-data/places-data

Setup:
    1. Download SafeGraph Places CSV from their free-data portal
    2. Extract to a directory
    3. Set SAFEGRAPH_DIR=<path> in your .env

If SAFEGRAPH_DIR is not set or the files don't exist, this collector
returns an empty list and logs a warning — it never blocks the pipeline.
"""
from __future__ import annotations

import csv
import glob
import logging
import os
from pathlib import Path

__all__ = ["load_places_for_zip", "is_available"]

log = logging.getLogger("safegraph_collector")

# SafeGraph column name variations across schema versions
_COL_ALIASES: dict[str, list[str]] = {
    "name":         ["location_name", "LOCATION_NAME", "safegraph_place_id"],
    "top_category": ["top_category", "TOP_CATEGORY", "naics_code"],
    "sub_category": ["sub_category", "SUB_CATEGORY", "category_tags"],
    "lat":          ["latitude", "LATITUDE", "lat"],
    "lng":          ["longitude", "LONGITUDE", "lon", "lng"],
    "address":      ["street_address", "STREET_ADDRESS", "address"],
    "city":         ["city", "CITY"],
    "region":       ["region", "REGION", "state"],
    "postal_code":  ["postal_code", "POSTAL_CODE", "zip", "zip_code"],
    "visit_counts": ["raw_visit_counts", "RAW_VISIT_COUNTS", "visits"],
    "avg_rating":   ["avg_rating", "AVG_RATING", "rating"],
    "num_reviews":  ["num_reviews", "NUM_REVIEWS", "review_count"],
}


def _resolve(row: dict, key: str, default: str = "") -> str:
    for alias in _COL_ALIASES.get(key, [key]):
        if alias in row:
            return row[alias] or default
    return default


def _find_csv_files(sg_dir: str) -> list[Path]:
    candidates = [
        Path(sg_dir) / "places.csv",
        Path(sg_dir) / "core_poi.csv",
    ]
    glob_matches = [
        Path(p)
        for p in glob.glob(str(Path(sg_dir) / "core-poi-*.csv"))
    ]
    return [p for p in candidates + glob_matches if p.exists()]


def is_available() -> bool:
    """Returns True if SAFEGRAPH_DIR is set and contains at least one usable CSV."""
    sg_dir = os.environ.get("SAFEGRAPH_DIR", "").strip()
    if not sg_dir:
        return False
    return bool(_find_csv_files(sg_dir))


def load_places_for_zip(zip_code: str) -> list[dict]:
    """
    Load POIs from SafeGraph Places CSV files for a zip code.

    Returns list of dicts matching NeighborIQ business schema:
      name, raw_category, rating, review_count, address, lat, lng, source
    Returns [] if SAFEGRAPH_DIR is not set or no files found.
    """
    sg_dir = os.environ.get("SAFEGRAPH_DIR", "").strip()
    if not sg_dir:
        log.debug("SAFEGRAPH_DIR not set — skipping SafeGraph enrichment")
        return []

    csv_files = _find_csv_files(sg_dir)
    if not csv_files:
        log.warning(
            "SAFEGRAPH_DIR=%s set but no CSV files found (places.csv / core_poi.csv / core-poi-*.csv)",
            sg_dir,
        )
        return []

    results: list[dict] = []
    zip_code = zip_code.strip().lstrip("0") if zip_code.startswith("0") else zip_code.strip()
    # Normalise: SafeGraph stores as 5-char string, sometimes without leading zero
    zip_padded = zip_code.zfill(5)

    for csv_path in csv_files:
        log.info("Loading SafeGraph data from %s for zip %s", csv_path.name, zip_padded)
        try:
            with csv_path.open(newline="", encoding="utf-8-sig") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    postal = _resolve(row, "postal_code").strip().zfill(5)
                    if postal != zip_padded:
                        continue

                    top_cat = _resolve(row, "top_category")
                    sub_cat = _resolve(row, "sub_category")
                    raw_category = sub_cat if sub_cat else top_cat

                    try:
                        lat = float(_resolve(row, "lat", "0") or "0")
                        lng = float(_resolve(row, "lng", "0") or "0")
                    except ValueError:
                        lat, lng = 0.0, 0.0

                    try:
                        rating = float(_resolve(row, "avg_rating", "0") or "0")
                    except ValueError:
                        rating = 0.0

                    try:
                        review_count = int(_resolve(row, "num_reviews", "0") or "0")
                    except ValueError:
                        review_count = 0

                    address = ", ".join(
                        part for part in [
                            _resolve(row, "address"),
                            _resolve(row, "city"),
                            _resolve(row, "region"),
                            zip_padded,
                        ]
                        if part
                    )

                    results.append({
                        "name":          _resolve(row, "name", "Unknown"),
                        "raw_category":  raw_category,
                        "niche":         "",   # filled by classify_businesses in pipeline
                        "rating":        rating,
                        "review_count":  review_count,
                        "address":       address,
                        "lat":           lat,
                        "lng":           lng,
                        "source":        "safegraph",
                    })
        except Exception as exc:
            log.warning("Failed to read %s: %s", csv_path, exc)
            continue

    log.info("SafeGraph: loaded %d POIs for zip %s", len(results), zip_padded)
    return results
