"""intelligence — Universal Business Intelligence layer.

Extends NeighborIQ from neighborhood analysis to any business domain.

Usage:
    from neighboriq.intelligence.biz_profile import BizProfile, from_yaml
    from neighboriq.intelligence.domain_taxonomy import classify, get_domain
    from neighboriq.intelligence.benchmark_engine import get_benchmarks
    from neighboriq.intelligence.vertical_finder import find_verticals
    from neighboriq.intelligence.universal_roadmap import generate_roadmap, format_roadmap
"""
from __future__ import annotations

from neighboriq.intelligence.biz_profile import (
    BizProfile,
    RevenueStream,
    from_dict,
    from_yaml,
    to_yaml_template,
)
from neighboriq.intelligence.domain_taxonomy import (
    DomainSpec,
    classify,
    get_domain,
    list_domains,
)

__all__ = [
    "BizProfile",
    "RevenueStream",
    "from_yaml",
    "from_dict",
    "to_yaml_template",
    "DomainSpec",
    "classify",
    "get_domain",
    "list_domains",
]
