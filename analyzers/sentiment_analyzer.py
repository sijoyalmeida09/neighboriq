"""sentiment_analyzer.py — rates competition quality via review scores and VADER."""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass

log = logging.getLogger("sentiment_analyzer")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _VADER = SentimentIntensityAnalyzer()
    _VADER_AVAILABLE = True
except ImportError:
    _VADER = None  # type: ignore[assignment]
    _VADER_AVAILABLE = False
    log.debug("vaderSentiment not installed; sentiment_score will be 0.0")

_LOW_RATING_THRESHOLD = 3.8


@dataclass(frozen=True)
class SentimentResult:
    niche: str
    avg_rating: float
    review_count_total: int
    pct_low_rated: float    # fraction of businesses in niche with rating < 3.8
    sentiment_score: float  # VADER compound -1 to 1 (0.0 if unavailable)
    is_opportunity: bool    # unhappy existing customers = entry opportunity


def analyze_competition_quality(
    businesses: list[dict],
    reviews_by_niche: dict[str, list[str]] | None = None,
) -> list[SentimentResult]:
    """
    Args:
        businesses: list of dicts with "niche", "rating" (float), "review_count" (int)
        reviews_by_niche: optional {niche: [review_text, ...]} for VADER scoring
    Returns:
        List of SentimentResult sorted by avg_rating ascending
        (worst-rated niches first = highest opportunity).
    """
    by_niche: dict[str, list[dict]] = defaultdict(list)
    for biz in businesses:
        niche = biz.get("niche", "other")
        if niche and niche != "other":
            by_niche[niche].append(biz)

    results: list[SentimentResult] = []
    for niche, biz_list in by_niche.items():
        ratings = [
            float(b["rating"])
            for b in biz_list
            if b.get("rating") is not None and float(b.get("rating", 0)) > 0
        ]
        if not ratings:
            continue

        avg_rating = sum(ratings) / len(ratings)
        review_count_total = sum(
            int(b.get("review_count", 0)) for b in biz_list
        )
        pct_low_rated = sum(1 for r in ratings if r < _LOW_RATING_THRESHOLD) / len(ratings)

        sentiment_score = 0.0
        if _VADER_AVAILABLE and reviews_by_niche:
            texts = reviews_by_niche.get(niche, [])
            if texts:
                scores = [_VADER.polarity_scores(t)["compound"] for t in texts]  # type: ignore[union-attr]
                sentiment_score = sum(scores) / len(scores)

        is_opportunity = (
            (avg_rating < _LOW_RATING_THRESHOLD and review_count_total >= 20)
            or (avg_rating < 4.0 and pct_low_rated > 0.3)
        )

        results.append(
            SentimentResult(
                niche=niche,
                avg_rating=round(avg_rating, 2),
                review_count_total=review_count_total,
                pct_low_rated=round(pct_low_rated, 3),
                sentiment_score=round(sentiment_score, 3),
                is_opportunity=is_opportunity,
            )
        )

    results.sort(key=lambda r: r.avg_rating)
    return results
