"""gap_detector.py — detects supply/demand gaps from saturation + trend data."""
from __future__ import annotations

from dataclasses import dataclass

from .saturation_analyzer import SaturationResult


@dataclass(frozen=True)
class GapResult:
    niche: str
    saturation_ratio: float
    demand_score: int       # 0–100 from Google Trends
    gap_score: float        # demand × (1 / saturation_ratio) × 10
    tier: str               # "A" | "B" | "C"
    reason: str


def detect_gaps(
    saturation_results: list[SaturationResult],
    demand_signals: dict[str, int],
    min_demand_score: int = 20,
) -> list[GapResult]:
    """
    Args:
        saturation_results: output of saturation_analyzer.compute_density()
        demand_signals: {niche: trend_score 0-100} from google_trends_collector
        min_demand_score: niches with demand below this threshold are skipped
    Returns:
        List of GapResult sorted by gap_score descending.
    """
    gaps: list[GapResult] = []
    for sat in saturation_results:
        demand = demand_signals.get(sat.niche, 50)
        if demand < min_demand_score:
            continue

        ratio = sat.saturation_ratio
        if ratio == 0:
            gap_score = float(demand) * 3.0
        else:
            gap_score = demand * (1.0 / ratio) * 10

        if gap_score >= 150:
            tier = "A"
        elif gap_score >= 80:
            tier = "B"
        else:
            tier = "C"

        reason = (
            f"{sat.niche}: {sat.actual_count} existing "
            f"({ratio:.2f}x benchmark), demand score {demand}/100"
        )

        gaps.append(
            GapResult(
                niche=sat.niche,
                saturation_ratio=ratio,
                demand_score=demand,
                gap_score=round(gap_score, 2),
                tier=tier,
                reason=reason,
            )
        )

    gaps.sort(key=lambda g: g.gap_score, reverse=True)
    return gaps
