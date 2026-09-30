"""intelligence — Universal Business Intelligence layer.

Extends NeighborIQ from neighborhood analysis to any business domain.

Usage:
    from neighboriq.intelligence.biz_profile import BizProfile, from_yaml
    from neighboriq.intelligence.domain_taxonomy import classify, get_domain
    from neighboriq.intelligence.benchmark_engine import get_benchmarks
    from neighboriq.intelligence.vertical_finder import find_verticals
    from neighboriq.intelligence.universal_roadmap import generate_roadmap, format_roadmap
    from neighboriq.intelligence.tool_selector import recommend_llm, full_stack_recommendation
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
from neighboriq.intelligence.repo_scanner import (
    RepoScan,
    scan_repo,
    format_scan_summary,
)
from neighboriq.intelligence.auto_profiler import (
    build_profile_from_scan,
    quick_profile,
    profile_to_yaml,
)
from neighboriq.intelligence.analysis_queue import (
    run_analysis,
    get_report,
    reset_analysis,
)
from neighboriq.intelligence.tool_selector import (
    LLMSpec,
    AutomationToolSpec,
    AgentFrameworkSpec,
    VectorDBSpec,
    ToolRecommendation,
    recommend_llm,
    recommend_automation,
    recommend_agent_framework,
    recommend_vector_db,
    full_stack_recommendation,
    format_recommendation,
    list_llms,
    list_automation_tools,
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
    "RepoScan",
    "scan_repo",
    "format_scan_summary",
    "build_profile_from_scan",
    "quick_profile",
    "profile_to_yaml",
    "run_analysis",
    "get_report",
    "reset_analysis",
    # Tool selector
    "LLMSpec",
    "AutomationToolSpec",
    "AgentFrameworkSpec",
    "VectorDBSpec",
    "ToolRecommendation",
    "recommend_llm",
    "recommend_automation",
    "recommend_agent_framework",
    "recommend_vector_db",
    "full_stack_recommendation",
    "format_recommendation",
    "list_llms",
    "list_automation_tools",
]
