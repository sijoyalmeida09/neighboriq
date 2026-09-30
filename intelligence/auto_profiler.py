"""auto_profiler.py — Convert RepoScan + user answers into a complete BizProfile."""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from neighboriq.intelligence.repo_scanner import RepoScan

from neighboriq.intelligence.biz_profile import BizProfile, RevenueStream, from_dict

__all__ = [
    "build_profile_from_scan",
    "profile_to_yaml",
    "quick_profile",
]


# ── Inference helpers ─────────────────────────────────────────────────────────

def _infer_data_assets(scan: "RepoScan") -> tuple[str, ...]:
    assets: list[str] = []
    if "stripe" in scan.payment_integrations:
        assets.append("customer payment history")
    if "supabase" in scan.key_integrations or "firebase" in scan.key_integrations:
        assets.append("user database")
    if "openai" in scan.key_integrations or "anthropic" in scan.key_integrations:
        assets.append("AI conversation logs")
    if scan.has_admin_panel:
        assets.append("business operations data")
    if scan.commit_velocity_90d > 20:
        assets.append("product usage telemetry")
    if "google-maps" in scan.key_integrations or "googlemaps" in scan.key_integrations:
        assets.append("location and route data")
    if "twilio" in scan.key_integrations:
        assets.append("customer communication history")
    if "quickbooks" in scan.key_integrations:
        assets.append("financial transaction history")
    return tuple(assets)


def _infer_digital_assets(scan: "RepoScan") -> tuple[str, ...]:
    assets: list[str] = ["source code / GitHub repository"]
    if scan.is_deployed:
        assets.append("live web application")
    if scan.has_admin_panel:
        assets.append("admin dashboard / back office")
    if scan.has_ci:
        assets.append("automated CI/CD pipeline")
    if "stripe" in scan.payment_integrations:
        assets.append("payment processing integration")
    if "supabase" in scan.key_integrations:
        assets.append("cloud database (Supabase)")
    if "openai" in scan.key_integrations or "anthropic" in scan.key_integrations:
        assets.append("AI/LLM integration")
    if scan.has_docker:
        assets.append("containerized deployment")
    return tuple(assets)


def _infer_roles(scan: "RepoScan") -> tuple[tuple[str, int], ...]:
    count = scan.contributor_count
    if count <= 1:
        return (("founder/developer", 1),)
    if count <= 3:
        return (("founder", 1), ("developer", count - 1))
    if count <= 8:
        return (
            ("founder", 1),
            ("developer", max(1, count - 3)),
            ("operations", min(2, count - 2)),
        )
    return (
        ("founder", 1),
        ("developer", count // 2),
        ("operations", count // 4),
        ("sales", max(1, count // 4)),
    )


def _infer_revenue_streams(scan: "RepoScan", monthly_revenue: int) -> tuple[RevenueStream, ...]:
    if "stripe" in scan.payment_integrations:
        return (
            RevenueStream(
                name="subscription / SaaS revenue",
                monthly_usd=int(monthly_revenue * 0.80),
                pct_of_total=0.80,
                recurring=True,
            ),
        )
    if "square" in scan.payment_integrations:
        return (
            RevenueStream(
                name="point-of-sale / retail revenue",
                monthly_usd=int(monthly_revenue * 0.90),
                pct_of_total=0.90,
                recurring=False,
            ),
        )
    if "shopify" in scan.payment_integrations:
        return (
            RevenueStream(
                name="e-commerce product sales",
                monthly_usd=int(monthly_revenue * 0.85),
                pct_of_total=0.85,
                recurring=False,
            ),
        )
    # Fallback — generic service revenue
    return (
        RevenueStream(
            name="service revenue",
            monthly_usd=monthly_revenue,
            pct_of_total=1.0,
            recurring=False,
        ),
    )


def _infer_recognition(scan: "RepoScan") -> str:
    followers = sum(c for _, c in scan.inferred_digital_assets if False)  # placeholder
    if scan.contributor_count >= 10 or scan.commit_velocity_90d >= 100:
        return "regional"
    if scan.is_deployed and scan.has_ci:
        return "city"
    return "neighborhood"


# ── Main builder ──────────────────────────────────────────────────────────────

def build_profile_from_scan(
    scan: "RepoScan",
    topup: dict[str, Any],
    biz_name: str | None = None,
) -> BizProfile:
    """Merge scan-inferred fields + user-provided topup into a complete BizProfile."""
    monthly_revenue = int(topup.get("monthly_revenue", 0))
    headcount = max(scan.inferred_headcount_min, 1)

    data: dict[str, Any] = {
        # ── Identity ──────────────────────────────────────────────────────────
        "name": biz_name or topup.get("name", scan.readme_excerpt[:40].strip() or "My Business"),
        "description": scan.readme_excerpt or topup.get("description", ""),
        "naics_code": topup.get("naics_code", None),
        "year_founded": topup.get(
            "year_founded",
            max(2000, 2025 - max(0, int(scan.repo_age_years))) if scan.repo_age_years else None,
        ),
        "website": topup.get("website", None),

        # ── Physical ──────────────────────────────────────────────────────────
        "equipment": [],
        "inventory_value": int(topup.get("inventory_value", 0)),
        "vehicles": int(topup.get("vehicles", 0)),
        "sqft_owned": int(topup.get("sqft_owned", 0)),
        "sqft_leased": int(topup.get("sqft_leased", 0)),
        "real_estate_value": int(topup.get("real_estate_value", 0)),

        # ── Digital ───────────────────────────────────────────────────────────
        "monthly_web_traffic": int(topup.get("monthly_web_traffic", 0)),
        "email_list_size": int(topup.get("email_list_size", 0)),
        "social_followers": topup.get("social_followers", []),
        "software_tools": list(scan.inferred_software_tools),
        "data_assets": list(_infer_data_assets(scan)),
        "ip_patents": list(topup.get("ip_patents", [])),

        # ── Human ─────────────────────────────────────────────────────────────
        "headcount": headcount,
        "roles": [list(r) for r in _infer_roles(scan)],
        "owner_certifications": list(topup.get("owner_certifications", [])),
        "owner_network_size": headcount * 50,

        # ── Financial ─────────────────────────────────────────────────────────
        "monthly_revenue": monthly_revenue,
        "monthly_expenses": int(topup.get("monthly_expenses", int(monthly_revenue * 0.70))),
        "cash_on_hand": int(topup.get("cash_on_hand", 0)),
        "credit_line": int(topup.get("credit_line", 0)),
        "monthly_debt_service": int(topup.get("monthly_debt_service", 0)),

        # ── Brand ─────────────────────────────────────────────────────────────
        "years_in_market": scan.inferred_years_in_market,
        "avg_rating": float(topup.get("avg_rating", 4.0)),
        "review_count": int(topup.get("review_count", 0)),
        "recognition": topup.get("recognition", _infer_recognition(scan)),

        # ── Operational ───────────────────────────────────────────────────────
        "licenses": list(topup.get("licenses", [])),
        "certifications": list(topup.get("certifications", [])),
        "exclusive_supplier_contracts": [],
        "proprietary_processes": (
            ["automated CI/CD pipeline", "containerized deployment"]
            if scan.has_ci and scan.has_docker
            else []
        ),

        # ── Revenue streams ───────────────────────────────────────────────────
        "revenue_streams": [
            {
                "name": rs.name,
                "monthly_usd": rs.monthly_usd,
                "pct_of_total": rs.pct_of_total,
                "recurring": rs.recurring,
            }
            for rs in _infer_revenue_streams(scan, monthly_revenue)
        ],

        # Inject inferred digital assets into the data dict via a side-channel
        # (from_dict will ignore unknown keys, so we store separately)
    }

    # Override digital assets list with inferred version by injecting into
    # the digital section — from_dict maps "digital_assets" key
    data["digital_assets"] = list(_infer_digital_assets(scan))

    return from_dict(data)


# ── YAML serialiser (stdlib, no pyyaml needed) ────────────────────────────────

def _yaml_str(value: str) -> str:
    """Quote a string for YAML if it contains special characters."""
    if any(c in value for c in ':#{}[]|>&*!,'):
        return f'"{value}"'
    return value


def profile_to_yaml(profile: BizProfile, path: str) -> None:
    """Serialize BizProfile to a human-readable YAML file (no pyyaml required)."""
    lines: list[str] = [
        "# NeighborIQ Business Profile — auto-generated",
        "# Edit values then re-run: neighboriq biz-audit --profile this_file.yaml",
        "",
        "business:",
        f"  name: {_yaml_str(profile.name)}",
        f"  description: {_yaml_str(profile.description[:120] if profile.description else '')}",
        f"  naics_code: {profile.naics_code or 'null'}",
        f"  year_founded: {profile.year_founded or 'null'}",
        f"  website: {profile.website or 'null'}",
        "",
        "physical:",
        f"  inventory_value: {profile.inventory_value}",
        f"  vehicles: {profile.vehicles}",
        f"  sqft_owned: {profile.sqft_owned}",
        f"  sqft_leased: {profile.sqft_leased}",
        f"  real_estate_value: {profile.real_estate_value}",
        "  equipment: []",
        "",
        "digital:",
        f"  monthly_web_traffic: {profile.monthly_web_traffic}",
        f"  email_list_size: {profile.email_list_size}",
        "  social_followers: []",
    ]

    for tool in profile.software_tools:
        lines.append(f"  # tool: {tool}")

    lines += [
        "",
        "human:",
        f"  headcount: {profile.headcount}",
        f"  owner_network_size: {profile.owner_network_size}",
        "  owner_certifications: []",
        "  roles:",
    ]
    for role, count in profile.roles:
        lines.append(f"    - [{_yaml_str(role)}, {count}]")

    lines += [
        "",
        "financial:",
        f"  monthly_revenue: {profile.monthly_revenue}",
        f"  monthly_expenses: {profile.monthly_expenses}",
        f"  cash_on_hand: {profile.cash_on_hand}",
        f"  credit_line: {profile.credit_line}",
        f"  monthly_debt_service: {profile.monthly_debt_service}",
        "",
        "brand:",
        f"  years_in_market: {profile.years_in_market}",
        f"  avg_rating: {profile.avg_rating}",
        f"  review_count: {profile.review_count}",
        f"  recognition: {profile.recognition}",
        "",
        "operational:",
        "  licenses: []",
        "  certifications: []",
        "  exclusive_supplier_contracts: []",
        "  proprietary_processes:",
    ]
    for pp in profile.proprietary_processes:
        lines.append(f"    - {_yaml_str(pp)}")

    lines += ["", "revenue_streams:"]
    for rs in profile.revenue_streams:
        lines += [
            f"  - name: {_yaml_str(rs.name)}",
            f"    monthly_usd: {rs.monthly_usd}",
            f"    pct_of_total: {rs.pct_of_total}",
            f"    recurring: {'true' if rs.recurring else 'false'}",
        ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ── One-call convenience ──────────────────────────────────────────────────────

def quick_profile(root_path: str | None = None) -> tuple["BizProfile", "RepoScan"]:
    """scan_repo() + interactive_topup() + build_profile_from_scan() in one call."""
    from neighboriq.intelligence.repo_scanner import scan_repo, interactive_topup, format_scan_summary

    print("Scanning repository...")
    scan = scan_repo(root_path)
    print(format_scan_summary(scan))

    topup = interactive_topup(scan)
    profile = build_profile_from_scan(scan, topup)

    return profile, scan
