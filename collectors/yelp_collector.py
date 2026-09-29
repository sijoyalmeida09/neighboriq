"""yelp_collector.py — Yelp Fusion API business data collector.

Requires YELP_API_KEY in environment. Returns empty list gracefully if key absent.
Free tier: 500 calls/day.
"""
from __future__ import annotations

import logging
import os
import time

import requests

log = logging.getLogger("neighboriq.collectors.yelp")

_SEARCH_URL = "https://api.yelp.com/v3/businesses/search"
_REVIEWS_URL = "https://api.yelp.com/v3/businesses/{id}/reviews"
_TIMEOUT = 10
_PAGE_SIZE = 50
_MAX_RESULTS = 200
_PAGE_SLEEP = 0.5


def _price_tier(price_str: str | None) -> int:
    """Convert Yelp price string (e.g. '$$') to integer 1-4."""
    if not price_str:
        return 0
    return min(len(price_str.strip()), 4)


def _get_headers() -> dict[str, str] | None:
    key = os.environ.get("YELP_API_KEY", "")
    if not key:
        return None
    return {"Authorization": f"Bearer {key}"}


def collect(
    zip_code: str,
    categories: list[str] | None = None,
    radius_meters: int = 2400,
) -> list[dict]:
    """Collect businesses from Yelp Fusion API for a zip code.

    Args:
        zip_code: US zip code to search in.
        categories: Yelp category aliases to filter by (None = all categories).
        radius_meters: Search radius in meters (max 40000).

    Returns:
        List of business dicts. Empty if YELP_API_KEY not set.
    """
    headers = _get_headers()
    if not headers:
        log.warning("YELP_API_KEY not set — skipping Yelp collection")
        return []

    params: dict = {
        "location": zip_code,
        "radius": min(radius_meters, 40000),
        "limit": _PAGE_SIZE,
        "sort_by": "rating",
    }
    if categories:
        params["categories"] = ",".join(categories)

    all_businesses: list[dict] = []
    offset = 0

    while offset < _MAX_RESULTS:
        params["offset"] = offset
        try:
            resp = requests.get(_SEARCH_URL, headers=headers, params=params, timeout=_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            log.error("Yelp API request failed (offset=%d): %s", offset, exc)
            break

        businesses = data.get("businesses", [])
        if not businesses:
            break

        for biz in businesses:
            location = biz.get("location", {})
            coords = biz.get("coordinates", {})
            cats = biz.get("categories", [])
            raw_category = cats[0]["title"] if cats else ""

            all_businesses.append({
                "name": biz.get("name", ""),
                "raw_category": raw_category,
                "rating": float(biz.get("rating", 0.0)),
                "review_count": int(biz.get("review_count", 0)),
                "price_tier": _price_tier(biz.get("price")),
                "address": " ".join(filter(None, [
                    location.get("address1", ""),
                    location.get("city", ""),
                    location.get("state", ""),
                ])),
                "phone": biz.get("display_phone", ""),
                "lat": float(coords.get("latitude", 0.0)),
                "lng": float(coords.get("longitude", 0.0)),
                "yelp_id": biz.get("id", ""),
                "source": "yelp",
            })

        log.info("Yelp: fetched %d businesses (offset=%d)", len(businesses), offset)

        if len(businesses) < _PAGE_SIZE:
            break

        offset += _PAGE_SIZE
        time.sleep(_PAGE_SLEEP)

    log.info("Yelp: total %d businesses for zip=%s", len(all_businesses), zip_code)
    return all_businesses


def get_reviews(business_id: str, count: int = 3) -> list[str]:
    """Fetch review texts for a Yelp business (up to count reviews).

    Args:
        business_id: Yelp business ID (yelp_id field from collect()).
        count: Maximum reviews to return.

    Returns:
        List of review text strings. Empty on error or missing key.
    """
    headers = _get_headers()
    if not headers:
        return []

    try:
        url = _REVIEWS_URL.format(id=business_id)
        resp = requests.get(url, headers=headers, params={"limit": count}, timeout=_TIMEOUT)
        resp.raise_for_status()
        reviews = resp.json().get("reviews", [])
        return [r.get("text", "") for r in reviews if r.get("text")]
    except requests.RequestException as exc:
        log.warning("Failed to fetch reviews for %s: %s", business_id, exc)
        return []
