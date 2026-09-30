"""NeighborIQ — Neighborhood Business Intelligence Engine.

Quickstart:
    from neighboriq.scoring.revenue_model import get_revenue_model, list_niches
    from neighboriq.analyzers.asset_mapper import AssetProfile, filter_by_assets
    from neighboriq.analyzers.domain_analyzer import analyze_domain

CLI:
    neighboriq init                              # auto-detect from current repo
    neighboriq biz-audit --profile my.yaml      # audit from profile file
    neighboriq biz-audit --interactive           # scan + questions
    neighboriq analyze --zip 02122
    neighboriq analyze --zip 02122 --depth full
    neighboriq analyze-business --url https://example.com

API:
    uvicorn neighboriq.api.server:app --port 8000
"""
from __future__ import annotations

__version__ = "0.2.0"
__author__ = "Sijoy Almeida"
__license__ = "MIT"

# Stable public API — safe to import directly from `neighboriq`
from neighboriq.scoring.revenue_model import (  # noqa: F401
    RevenueModel,
    get_revenue_model,
    list_niches,
)
from neighboriq.scoring.automation_matrix import (  # noqa: F401
    AutomationBlueprint,
    get_automation_blueprint,
)
from neighboriq.analyzers.asset_mapper import (  # noqa: F401
    AssetProfile,
    FeasibilityResult,
    filter_by_assets,
)
from neighboriq.scoring.niche_roadmap import (  # noqa: F401
    NicheRoadmap,
    get_niche_roadmap,
    format_roadmap,
    list_roadmap_niches,
)

__all__ = [
    "__version__",
    # Revenue model
    "RevenueModel",
    "get_revenue_model",
    "list_niches",
    # Automation
    "AutomationBlueprint",
    "get_automation_blueprint",
    # Asset filtering
    "AssetProfile",
    "FeasibilityResult",
    "filter_by_assets",
    # Niche roadmaps
    "NicheRoadmap",
    "get_niche_roadmap",
    "format_roadmap",
    "list_roadmap_niches",
]
