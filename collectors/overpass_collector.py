"""overpass_collector.py — OpenStreetMap Overpass API business counter.

Free, no API key required. Groups OSM amenity/shop/leisure tags into
normalized business buckets for saturation analysis.
"""
from __future__ import annotations

import logging

import requests

log = logging.getLogger("neighboriq.collectors.overpass")

_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_TIMEOUT = 30

# OSM tag value → normalized bucket mapping
_AMENITY_MAP: dict[str, str] = {
    "restaurant": "food_beverage",
    "fast_food": "food_beverage",
    "cafe": "food_beverage",
    "bar": "food_beverage",
    "pub": "food_beverage",
    "food_court": "food_beverage",
    "pharmacy": "pharmacy",
    "hospital": "healthcare",
    "clinic": "healthcare",
    "doctors": "healthcare",
    "dentist": "healthcare",
    "bank": "financial",
    "atm": "financial",
    "bureau_de_change": "financial",
    "fuel": "gas_station",
    "car_wash": "auto_services",
    "car_repair": "auto_services",
    "place_of_worship": "community",
    "school": "education",
    "university": "education",
    "college": "education",
    "kindergarten": "childcare",
    "childcare": "childcare",
    "cinema": "entertainment",
    "theatre": "entertainment",
    "nightclub": "entertainment",
    "gym": "fitness",
    "laundry": "laundry",
    "dry_cleaning": "laundry",
    "post_office": "services",
    "police": "services",
    "library": "community",
    "community_centre": "community",
}

_SHOP_MAP: dict[str, str] = {
    "supermarket": "grocery",
    "convenience": "grocery",
    "greengrocer": "grocery",
    "bakery": "food_beverage",
    "butcher": "food_beverage",
    "deli": "food_beverage",
    "confectionery": "food_beverage",
    "alcohol": "liquor",
    "beverages": "liquor",
    "hairdresser": "beauty",
    "beauty": "beauty",
    "cosmetics": "beauty",
    "massage": "beauty",
    "optician": "healthcare",
    "shoes": "retail_clothing",
    "clothes": "retail_clothing",
    "boutique": "retail_clothing",
    "jewelry": "retail_specialty",
    "florist": "retail_specialty",
    "gift": "retail_specialty",
    "toys": "retail_specialty",
    "books": "retail_specialty",
    "electronics": "retail_electronics",
    "mobile_phone": "retail_electronics",
    "computer": "retail_electronics",
    "hardware": "retail_home",
    "furniture": "retail_home",
    "doityourself": "retail_home",
    "pet": "retail_specialty",
    "sports": "fitness",
    "outdoor": "retail_specialty",
    "car": "auto_services",
    "car_parts": "auto_services",
    "travel_agency": "services",
    "insurance": "financial",
    "real_estate": "financial",
    "laundry": "laundry",
    "dry_cleaning": "laundry",
    "copyshop": "services",
    "tattoo": "beauty",
}

_LEISURE_MAP: dict[str, str] = {
    "fitness_centre": "fitness",
    "gym": "fitness",
    "sports_centre": "fitness",
    "swimming_pool": "fitness",
    "bowling_alley": "entertainment",
    "miniature_golf": "entertainment",
    "escape_game": "entertainment",
    "dance": "entertainment",
}


def _build_query(lat: float, lng: float, radius_meters: int) -> str:
    return f"""[out:json][timeout:25];
(
  node["amenity"](around:{radius_meters},{lat},{lng});
  node["shop"](around:{radius_meters},{lat},{lng});
  node["leisure"](around:{radius_meters},{lat},{lng});
);
out body;"""


def _tag_to_bucket(tags: dict) -> str | None:
    """Map an OSM element's tags to a normalized bucket name."""
    amenity = tags.get("amenity", "")
    if amenity and amenity in _AMENITY_MAP:
        return _AMENITY_MAP[amenity]

    shop = tags.get("shop", "")
    if shop and shop in _SHOP_MAP:
        return _SHOP_MAP[shop]

    leisure = tags.get("leisure", "")
    if leisure and leisure in _LEISURE_MAP:
        return _LEISURE_MAP[leisure]

    # Catch-all: return amenity/shop/leisure raw value prefixed with "other_"
    for tag in (amenity, shop, leisure):
        if tag:
            return f"other_{tag}"

    return None


def count_businesses_by_category(
    lat: float,
    lng: float,
    radius_meters: int = 2000,
) -> dict[str, int]:
    """Count OSM-mapped businesses by normalized category bucket.

    Args:
        lat: Center latitude.
        lng: Center longitude.
        radius_meters: Search radius in meters.

    Returns:
        Dict mapping bucket name → count. Returns empty dict on API failure.
    """
    query = _build_query(lat, lng, radius_meters)
    try:
        resp = requests.post(_OVERPASS_URL, data={"data": query}, timeout=_TIMEOUT)
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
    except requests.RequestException as exc:
        log.error("Overpass API request failed: %s", exc)
        return {}
    except Exception as exc:
        log.error("Unexpected error in Overpass collector: %s", exc)
        return {}

    counts: dict[str, int] = {}
    for el in elements:
        tags = el.get("tags", {})
        bucket = _tag_to_bucket(tags)
        if bucket:
            counts[bucket] = counts.get(bucket, 0) + 1

    log.info(
        "Overpass: %d elements → %d buckets for (%.4f, %.4f) r=%dm",
        len(elements), len(counts), lat, lng, radius_meters,
    )
    return dict(counts)
