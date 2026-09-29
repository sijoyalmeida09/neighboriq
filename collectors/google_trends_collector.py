"""google_trends_collector.py — Google Trends demand signals via pytrends.

Batches 5 categories per request (pytrends limit), sleeps between batches,
and falls back gracefully to neutral (50) score if the API is unavailable.
"""
from __future__ import annotations

import logging
import time
from typing import Any

log = logging.getLogger("neighboriq.collectors.google_trends")

# In-process memory cache: (frozenset(categories), location, timeframe) → scores dict
_CACHE: dict[tuple, dict[str, int]] = {}

_BATCH_SIZE = 5
_SLEEP_BETWEEN_BATCHES = 2.0  # seconds


def _normalize_batch(interest_df: Any) -> dict[str, int]:
    """Normalize a pytrends interest_over_time DataFrame to 0-100 per keyword."""
    if interest_df is None or interest_df.empty:
        return {}
    scores: dict[str, int] = {}
    for col in interest_df.columns:
        if col == "isPartial":
            continue
        series = interest_df[col]
        max_val = series.max()
        if max_val > 0:
            scores[col] = int(round(series.mean() / max_val * 100))
        else:
            scores[col] = 0
    return scores


def get_demand_signals(
    categories: list[str],
    location: str,
    timeframe: str = "today 12-m",
) -> dict[str, int]:
    """Return Google Trends demand score (0-100) per business category.

    Args:
        categories: Business category names to query.
        location: Location string passed to pytrends (e.g. "Boston" or geo code "US-MA").
        timeframe: pytrends timeframe string.

    Returns:
        Dict mapping category → score (0-100). Missing categories default to 50.
    """
    cache_key = (frozenset(categories), location, timeframe)
    if cache_key in _CACHE:
        log.debug("Trends cache hit for location=%s", location)
        return dict(_CACHE[cache_key])

    try:
        from pytrends.request import TrendReq  # type: ignore[import]
    except ImportError:
        log.error("pytrends not installed — run: pip install pytrends")
        return {cat: 50 for cat in categories}

    # urllib3 2.x renamed method_whitelist → allowed_methods; patch for pytrends compatibility
    try:
        from urllib3.util.retry import Retry as _Retry
        _orig_retry_init = _Retry.__init__
        def _compat_retry_init(self, *a, method_whitelist=None, allowed_methods=None, **kw):
            if method_whitelist is not None and allowed_methods is None:
                allowed_methods = method_whitelist
            _orig_retry_init(self, *a, allowed_methods=allowed_methods, **kw)
        _Retry.__init__ = _compat_retry_init
    except Exception:
        pass

    result: dict[str, int] = {}
    pytrends = TrendReq(hl="en-US", tz=360, retries=2, backoff_factor=1.0)

    batches = [categories[i:i + _BATCH_SIZE] for i in range(0, len(categories), _BATCH_SIZE)]
    for idx, batch in enumerate(batches):
        try:
            pytrends.build_payload(batch, timeframe=timeframe, geo=location)
            df = pytrends.interest_over_time()
            scores = _normalize_batch(df)
            for cat in batch:
                result[cat] = scores.get(cat, 50)
            log.info("Trends batch %d/%d for location=%s: %s", idx + 1, len(batches), location, scores)
        except Exception as exc:
            log.warning("Trends batch %d failed (%s) — using neutral score 50 for: %s", idx + 1, exc, batch)
            for cat in batch:
                result[cat] = 50

        if idx < len(batches) - 1:
            time.sleep(_SLEEP_BETWEEN_BATCHES)

    _CACHE[cache_key] = result
    return dict(result)


def get_top_rising(location: str) -> list[str]:
    """Return up to 5 rising business-related search queries in a location.

    Falls back to empty list if pytrends is unavailable or rate-limited.
    """
    try:
        from pytrends.request import TrendReq  # type: ignore[import]
    except ImportError:
        log.error("pytrends not installed")
        return []

    try:
        from urllib3.util.retry import Retry as _Retry2
        _orig2 = _Retry2.__init__
        def _compat2(self, *a, method_whitelist=None, allowed_methods=None, **kw):
            if method_whitelist is not None and allowed_methods is None:
                allowed_methods = method_whitelist
            _orig2(self, *a, allowed_methods=allowed_methods, **kw)
        _Retry2.__init__ = _compat2
    except Exception:
        pass

    try:
        pytrends = TrendReq(hl="en-US", tz=360, retries=1, backoff_factor=1.0)
        # Use "restaurant near me" as a seed to get related rising queries
        pytrends.build_payload(["restaurant near me"], timeframe="today 3-m", geo=location)
        related = pytrends.related_queries()
        rising = related.get("restaurant near me", {}).get("rising")
        if rising is not None and not rising.empty:
            return list(rising["query"].head(5))
    except Exception as exc:
        log.warning("get_top_rising failed for location=%s: %s", location, exc)

    return []
