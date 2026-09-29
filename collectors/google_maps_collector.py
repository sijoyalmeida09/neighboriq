"""google_maps_collector.py — Google Maps business scraper via Playwright headless.

Adapted from sohaya_supply/turbo_scraper.py's scrape_google_maps() pattern,
generalized to any coordinates + category list.
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any

import requests

log = logging.getLogger("neighboriq.collectors.google_maps")

DEFAULT_CATEGORIES: list[str] = [
    "restaurant", "indian restaurant", "chinese restaurant", "mexican restaurant",
    "pizza restaurant", "coffee shop", "cafe", "bakery", "bar", "grocery store",
    "pharmacy", "nail salon", "hair salon", "barbershop", "laundromat",
    "dry cleaning", "gym", "yoga studio", "dentist", "doctor",
    "auto repair", "gas station", "convenience store", "liquor store",
    "pet store", "bookstore", "clothing store", "shoe store",
    "hardware store", "electronics store", "furniture store",
    "real estate", "law office", "accounting", "insurance",
    "bank", "credit union", "pawn shop", "check cashing",
    "hotel", "motel", "hostel",
    "daycare", "preschool", "tutoring center",
    "movie theater", "bowling alley", "arcade", "escape room",
    "florist", "jewelry store", "gift shop",
    "delivery service", "moving company", "storage facility",
]

_ZIPPOPOTAM_URL = "https://api.zippopotam.us/us/{zip}"


def _geocode_zip(zip_code: str) -> tuple[float, float]:
    """Geocode a US zip code to (lat, lng) via zippopotam.us. Returns (0.0, 0.0) on failure."""
    try:
        resp = requests.get(
            _ZIPPOPOTAM_URL.format(zip=zip_code),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        places = data.get("places", [])
        if places:
            return float(places[0]["latitude"]), float(places[0]["longitude"])
    except Exception as exc:
        log.warning("Geocoding failed for zip %s: %s", zip_code, exc)
    return 0.0, 0.0


def _dedup(businesses: list[dict]) -> list[dict]:
    """Deduplicate by (name, address) pair."""
    seen: set[tuple[str, str]] = set()
    result: list[dict] = []
    for biz in businesses:
        key = (biz.get("name", "").lower().strip(), biz.get("address", "").lower().strip())
        if key not in seen:
            seen.add(key)
            result.append(biz)
    return result


async def _scrape_category(page: Any, lat: float, lng: float, category: str) -> list[dict]:
    """Scrape one category from Google Maps at given coordinates using JS extraction."""
    query = f"{category} near {lat},{lng}"
    url = f"https://www.google.com/maps/search/{requests.utils.quote(query)}"

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)

        # Scroll results panel to load more listings
        for _ in range(3):
            await page.keyboard.press("PageDown")
            await asyncio.sleep(1)

        # JS extraction adapted from turbo_scraper.py — handles Google Maps DOM variants
        results: list[dict] = await page.evaluate(r"""
            () => {
                const out = [];
                const seen = new Set();

                document.querySelectorAll('[role="article"]').forEach(el => {
                    const nameEl = el.querySelector(
                        '[class*="fontHeadlineSmall"], [class*="qBF1Pd"], [class*="NrDZNb"]'
                    );
                    if (!nameEl) return;
                    const name = nameEl.textContent.trim();
                    if (!name || name.length < 2 || seen.has(name)) return;
                    seen.add(name);

                    const ratingEl = el.querySelector('[role="img"][aria-label*="star"]');
                    const ratingText = ratingEl ? ratingEl.getAttribute('aria-label') : '';
                    const ratingMatch = ratingText.match(/([\d.]+)/);
                    const rating = ratingMatch ? parseFloat(ratingMatch[1]) : 0;

                    const reviewEl = el.querySelector('[aria-label*="review"]');
                    const reviewText = reviewEl ? reviewEl.getAttribute('aria-label') : '';
                    const reviewMatch = reviewText.match(/(\d[\d,]*)/);
                    const reviews = reviewMatch ? parseInt(reviewMatch[1].replace(/,/g, '')) : 0;

                    const addrSpans = el.querySelectorAll('[class*="W4Efsd"] span');
                    const addr = addrSpans.length > 0 ? addrSpans[addrSpans.length - 1].textContent.trim() : '';

                    out.push({name, rating, review_count: reviews, address: addr});
                });
                return out;
            }
        """)

        businesses: list[dict] = []
        for r in results:
            if r.get("name"):
                businesses.append({
                    "name": r["name"],
                    "raw_category": category,
                    "rating": float(r.get("rating", 0)),
                    "review_count": int(r.get("review_count", 0)),
                    "address": r.get("address", ""),
                    "phone": "",
                    "lat": lat,
                    "lng": lng,
                    "source": "google_maps",
                })

        log.debug("  %s → %d businesses found", category, len(businesses))

    except Exception as exc:
        log.warning("Failed scraping category '%s': %s", category, exc)
        businesses = []

    return businesses


async def _collect_async(
    lat: float,
    lng: float,
    radius_mi: float,  # noqa: ARG001 — stored in DB but Maps search is approximate
    categories: list[str],
) -> list[dict]:
    try:
        from playwright.async_api import async_playwright  # type: ignore[import]
    except ImportError:
        log.error("playwright not installed — run: pip install playwright && playwright install chromium")
        return []

    all_businesses: list[dict] = []
    capped = categories[:30]

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        for cat in capped:
            log.info("Scraping Google Maps: %s @ (%.4f, %.4f)", cat, lat, lng)
            results = await _scrape_category(page, lat, lng, cat)
            all_businesses.extend(results)
            log.debug("  → %d results", len(results))
            await asyncio.sleep(3)

        await browser.close()

    return _dedup(all_businesses)


def collect(
    lat: float,
    lng: float,
    radius_mi: float,
    categories: list[str],
) -> list[dict]:
    """Scrape Google Maps businesses near (lat, lng) for each category.

    Args:
        lat: Latitude of search center
        lng: Longitude of search center
        radius_mi: Approximate search radius in miles (passed to storage; Maps search is geographic)
        categories: List of business category search terms

    Returns:
        Deduplicated list of business dicts.
    """
    return asyncio.run(_collect_async(lat, lng, radius_mi, categories))


def collect_by_zip(
    zip_code: str,
    radius_mi: float = 1.0,
    categories: list[str] | None = None,
) -> list[dict]:
    """Geocode a zip code then collect businesses nearby.

    Args:
        zip_code: US 5-digit zip code
        radius_mi: Search radius in miles
        categories: Categories to search (defaults to DEFAULT_CATEGORIES)

    Returns:
        Deduplicated list of business dicts.
    """
    lat, lng = _geocode_zip(zip_code)
    if lat == 0.0 and lng == 0.0:
        log.error("Could not geocode zip %s — returning empty list", zip_code)
        return []
    return collect(lat, lng, radius_mi, categories or DEFAULT_CATEGORIES)
