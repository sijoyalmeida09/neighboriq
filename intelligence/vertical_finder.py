"""vertical_finder.py — Find new revenue verticals from existing business assets."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from neighboriq.intelligence.biz_profile import BizProfile
    from neighboriq.intelligence.benchmark_engine import DomainBenchmarks

__all__ = ["VerticalOpportunity", "find_verticals"]


@dataclass(frozen=True)
class VerticalOpportunity:
    name: str
    rationale: str
    assets_leveraged: tuple[str, ...]
    capital_required: int
    months_to_first_revenue: int
    monthly_revenue_at_maturity: int
    risk_level: str                     # "LOW" | "MEDIUM" | "HIGH"
    skills_overlap_pct: float           # 0.0–1.0
    requires_new_license: bool
    license_name: str | None
    domain_fit: str                     # comma-separated domain ids or "any"


# ── Adjacency rule type ──────────────────────────────────────────────────────
# Each rule: (condition_fn(profile, domain_id) -> bool, VerticalOpportunity)
_AdjacencyRule = tuple[Callable[["BizProfile", str], bool], VerticalOpportunity]


def _rule(
    cond: Callable[["BizProfile", str], bool],
    name: str,
    rationale: str,
    assets_leveraged: tuple[str, ...],
    capital_required: int,
    months_to_first_revenue: int,
    monthly_revenue_at_maturity: int,
    risk_level: str = "MEDIUM",
    skills_overlap_pct: float = 0.70,
    requires_new_license: bool = False,
    license_name: str | None = None,
    domain_fit: str = "any",
) -> _AdjacencyRule:
    v = VerticalOpportunity(
        name=name,
        rationale=rationale,
        assets_leveraged=assets_leveraged,
        capital_required=capital_required,
        months_to_first_revenue=months_to_first_revenue,
        monthly_revenue_at_maturity=monthly_revenue_at_maturity,
        risk_level=risk_level,
        skills_overlap_pct=skills_overlap_pct,
        requires_new_license=requires_new_license,
        license_name=license_name,
        domain_fit=domain_fit,
    )
    return (cond, v)


def _has_license(profile: "BizProfile", lic: str) -> bool:
    return any(lic.lower() in l.lower() for l in profile.licenses)


def _has_tool(profile: "BizProfile", tool: str) -> bool:
    return any(tool.lower() in t.lower() for t in profile.software_tools)


def _total_followers(profile: "BizProfile") -> int:
    return sum(c for _, c in profile.social_followers)


# ── 20 adjacency rules ───────────────────────────────────────────────────────
_RULES: list[_AdjacencyRule] = [

    _rule(
        lambda p, d: p.vehicles >= 2 and _has_license(p, "DOT") and d in ("logistics", "distribution"),
        name="Freight Brokerage",
        rationale="You already have DOT authority and carrier relationships — brokering loads for other shippers requires zero additional assets. Pure margin play at 10-20% of load value.",
        assets_leveraged=("DOT license", "carrier relationships", "vehicles"),
        capital_required=0,
        months_to_first_revenue=1,
        monthly_revenue_at_maturity=11000,
        risk_level="LOW",
        skills_overlap_pct=0.90,
        domain_fit="logistics,distribution",
    ),

    _rule(
        lambda p, d: p.sqft_owned > 500 and p.monthly_profit > 0,
        name="Space Sublease / Booth Rental",
        rationale="Owned square footage earns passive income through booth rental, pop-ups, or storage sublease without owner involvement.",
        assets_leveraged=("owned real estate", "existing foot traffic"),
        capital_required=2000,
        months_to_first_revenue=2,
        monthly_revenue_at_maturity=2800,
        risk_level="LOW",
        skills_overlap_pct=0.60,
        domain_fit="any",
    ),

    _rule(
        lambda p, d: _has_tool(p, "Shopify") or _has_tool(p, "WooCommerce") or p.email_list_size >= 500,
        name="E-Commerce Product Line",
        rationale="Existing e-commerce infrastructure or email audience lets you launch a product line without rebuilding a customer acquisition channel.",
        assets_leveraged=("e-commerce platform", "email list", "existing brand"),
        capital_required=3000,
        months_to_first_revenue=3,
        monthly_revenue_at_maturity=5000,
        risk_level="MEDIUM",
        skills_overlap_pct=0.65,
        domain_fit="any",
    ),

    _rule(
        lambda p, d: d == "food_beverage" and p.headcount >= 2,
        name="Catering / B2B Delivery",
        rationale="Your kitchen and staff are already provisioned — corporate catering fills off-peak hours with high-margin guaranteed revenue.",
        assets_leveraged=("kitchen equipment", "culinary staff", "food handler license"),
        capital_required=1500,
        months_to_first_revenue=2,
        monthly_revenue_at_maturity=8000,
        risk_level="LOW",
        skills_overlap_pct=0.85,
        domain_fit="food_beverage",
    ),

    _rule(
        lambda p, d: p.headcount >= 3 and (len(p.owner_certifications) > 0 or p.years_in_market >= 5),
        name="Training / Certification Program",
        rationale="Your operational knowledge and team depth can be monetized as a training program — other operators will pay $500-2,000 per person to learn your system.",
        assets_leveraged=("operational expertise", "certifications", "team depth"),
        capital_required=500,
        months_to_first_revenue=3,
        monthly_revenue_at_maturity=5000,
        risk_level="LOW",
        skills_overlap_pct=0.80,
        domain_fit="any",
    ),

    _rule(
        lambda p, d: len(p.proprietary_processes) > 0 and p.years_in_market >= 3,
        name="Licensing / White-Label",
        rationale="Your documented proprietary process is an asset that other operators in non-competing markets will pay to license rather than build from scratch.",
        assets_leveraged=("proprietary processes", "brand reputation", "documented systems"),
        capital_required=0,
        months_to_first_revenue=4,
        monthly_revenue_at_maturity=9000,
        risk_level="MEDIUM",
        skills_overlap_pct=0.70,
        domain_fit="any",
    ),

    _rule(
        lambda p, d: _total_followers(p) >= 2000,
        name="Brand Ambassador / Influencer Revenue",
        rationale="Your existing social audience is a paid media channel — brands in adjacent categories will pay $500-5,000/month for authentic promotion to your engaged followers.",
        assets_leveraged=("social media audience", "brand credibility"),
        capital_required=200,
        months_to_first_revenue=1,
        monthly_revenue_at_maturity=3000,
        risk_level="MEDIUM",
        skills_overlap_pct=0.55,
        domain_fit="any",
    ),

    _rule(
        lambda p, d: p.vehicles >= 1 and d in ("logistics", "distribution", "retail", "food_beverage"),
        name="Last-Mile Delivery for Local Retailers",
        rationale="Your vehicle capacity has idle hours — local retailers will pay $8-15/delivery for same-day delivery without the complexity of FedEx/UPS accounts.",
        assets_leveraged=("vehicles", "local route knowledge", "DOT familiarity"),
        capital_required=500,
        months_to_first_revenue=1,
        monthly_revenue_at_maturity=6000,
        risk_level="LOW",
        skills_overlap_pct=0.80,
        domain_fit="logistics,distribution,retail,food_beverage",
    ),

    _rule(
        lambda p, d: d == "food_beverage" and p.monthly_revenue >= 15000,
        name="Wholesale / Bulk Product Line",
        rationale="At your revenue level your production is systematic enough to supply local restaurants, hotels, or specialty retailers with a signature product at wholesale margin.",
        assets_leveraged=("production capacity", "existing recipes/products", "supplier relationships"),
        capital_required=5000,
        months_to_first_revenue=4,
        monthly_revenue_at_maturity=6500,
        risk_level="MEDIUM",
        skills_overlap_pct=0.80,
        domain_fit="food_beverage",
    ),

    _rule(
        lambda p, d: d == "music_entertainment" and _total_followers(p) >= 1000,
        name="Sync Licensing / Music Placement",
        rationale="Your catalog can earn passive income through sync licensing (film, TV, ads, YouTube) — each placement earns $500-25,000 with no additional work after delivery.",
        assets_leveraged=("music catalog", "social proof", "streaming presence"),
        capital_required=0,
        months_to_first_revenue=2,
        monthly_revenue_at_maturity=2750,
        risk_level="MEDIUM",
        skills_overlap_pct=0.75,
        domain_fit="music_entertainment",
    ),

    _rule(
        lambda p, d: p.review_count >= 20 and p.avg_rating >= 4.2 and p.monthly_revenue >= 5000,
        name="Subscription / Membership Tier",
        rationale="Your review volume and rating signal a loyal customer base ready to pre-pay for guaranteed access or exclusive benefits — converting 10% to members creates predictable MRR.",
        assets_leveraged=("customer loyalty", "brand reputation", "existing service"),
        capital_required=500,
        months_to_first_revenue=2,
        monthly_revenue_at_maturity=6000,
        risk_level="LOW",
        skills_overlap_pct=0.75,
        domain_fit="any",
    ),

    _rule(
        lambda p, d: d in ("healthcare", "gym", "local_service") and p.headcount >= 2,
        name="Corporate Wellness / B2B Contract",
        rationale="Local employers actively seek wellness vendors for employee benefits — a $500-2,000/month B2B contract fills capacity without marketing spend.",
        assets_leveraged=("service capacity", "health expertise", "scheduling infrastructure"),
        capital_required=1000,
        months_to_first_revenue=3,
        monthly_revenue_at_maturity=5000,
        risk_level="LOW",
        skills_overlap_pct=0.80,
        domain_fit="healthcare,gym,local_service",
    ),

    _rule(
        lambda p, d: d in ("real_estate", "professional_services", "check_cashing") and p.owner_network_size >= 100,
        name="Insurance / Financial Product Referral",
        rationale="Your trusted professional relationships make insurance referrals a natural fit — every client conversation is a warm intro opportunity at $200-800/policy commission.",
        assets_leveraged=("client trust relationships", "professional network", "existing client base"),
        capital_required=200,
        months_to_first_revenue=3,
        monthly_revenue_at_maturity=3750,
        risk_level="LOW",
        skills_overlap_pct=0.65,
        requires_new_license=True,
        license_name="Insurance Producer License",
        domain_fit="real_estate,professional_services,check_cashing",
    ),

    _rule(
        lambda p, d: len(p.social_followers) > 0 and p.monthly_web_traffic > 0,
        name="YouTube / Content Channel",
        rationale="Your business operations contain educational content that others search for — a how-to channel monetizes your expertise passively through AdSense + sponsorships.",
        assets_leveraged=("operational expertise", "existing brand", "web presence"),
        capital_required=800,
        months_to_first_revenue=6,
        monthly_revenue_at_maturity=2750,
        risk_level="MEDIUM",
        skills_overlap_pct=0.50,
        domain_fit="any",
    ),

    _rule(
        lambda p, d: (p.sqft_owned > 0 or p.sqft_leased > 200),
        name="ATM / Vending Placement",
        rationale="Any foot-traffic location can host an ATM ($400-800/mo passive) or vending machines (30-40% margin) — pure passive income on unused floor space.",
        assets_leveraged=("physical location", "foot traffic", "existing lease/ownership"),
        capital_required=5000,
        months_to_first_revenue=1,
        monthly_revenue_at_maturity=800,
        risk_level="LOW",
        skills_overlap_pct=0.40,
        domain_fit="any",
    ),

    _rule(
        lambda p, d: p.headcount >= 5 and p.years_in_market >= 3 and d in ("logistics", "manufacturing", "distribution"),
        name="Staffing / Temp Placement",
        rationale="You know what a good worker in your industry looks like — staffing other operators in your space earns 15-25% of placed worker wages with no additional overhead.",
        assets_leveraged=("hiring expertise", "industry network", "operational credibility"),
        capital_required=500,
        months_to_first_revenue=2,
        monthly_revenue_at_maturity=7500,
        risk_level="MEDIUM",
        skills_overlap_pct=0.75,
        domain_fit="logistics,manufacturing,distribution",
    ),

    _rule(
        lambda p, d: d == "check_cashing" or (_has_tool(p, "QuickBooks") and p.headcount >= 1),
        name="Tax Prep / Financial Services",
        rationale="Tax prep earns $150-400 per return from January through April — your existing client trust and bookkeeping familiarity make this a natural 4-month revenue spike.",
        assets_leveraged=("financial trust", "client base", "accounting software"),
        capital_required=300,
        months_to_first_revenue=1,
        monthly_revenue_at_maturity=5000,
        risk_level="LOW",
        skills_overlap_pct=0.70,
        domain_fit="check_cashing,professional_services",
    ),

    _rule(
        lambda p, d: p.real_estate_value > 0 or d == "real_estate",
        name="Property Management Services",
        rationale="Owning property gives you the operational knowledge to manage other people's properties — charging 8-12% of rents for management scales without capital.",
        assets_leveraged=("real estate experience", "contractor relationships", "local market knowledge"),
        capital_required=1000,
        months_to_first_revenue=2,
        monthly_revenue_at_maturity=7500,
        risk_level="LOW",
        skills_overlap_pct=0.80,
        domain_fit="real_estate,any",
    ),

    _rule(
        lambda p, d: d in ("education", "tutoring_center", "professional_services") and p.email_list_size >= 200,
        name="Online Course / Cohort Program",
        rationale="Your email list contains warm learners who trust your expertise — a $299-999 online course or 8-week cohort at $500/seat scales revenue without adding labor.",
        assets_leveraged=("email list", "domain expertise", "content credibility"),
        capital_required=500,
        months_to_first_revenue=3,
        monthly_revenue_at_maturity=6000,
        risk_level="LOW",
        skills_overlap_pct=0.80,
        domain_fit="education,tutoring_center,professional_services",
    ),

    _rule(
        lambda p, d: p.recognition in ("city", "regional", "national") and p.avg_rating >= 4.5,
        name="Community Partnership / Grant Revenue",
        rationale="Your reputation and community standing make you a compelling partner for government and foundation grants — $5K-50K grants require no equity and no debt.",
        assets_leveraged=("community recognition", "brand credibility", "local impact"),
        capital_required=0,
        months_to_first_revenue=3,
        monthly_revenue_at_maturity=2750,
        risk_level="LOW",
        skills_overlap_pct=0.55,
        domain_fit="any",
    ),
]


# ── Main function ────────────────────────────────────────────────────────────

def find_verticals(
    profile: "BizProfile",
    benchmarks: "DomainBenchmarks",
    domain_id: str,
    top_n: int = 5,
) -> tuple[VerticalOpportunity, ...]:
    """Return top vertical opportunities ranked by ROI score."""
    _RISK_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

    def _score(v: VerticalOpportunity) -> tuple[float, int]:
        rev_score = v.monthly_revenue_at_maturity / (v.capital_required + 1) / v.months_to_first_revenue
        return (rev_score, -_RISK_RANK[v.risk_level])

    def _passes(v: VerticalOpportunity, cash_limit_pct: float) -> bool:
        if v.capital_required > profile.cash_on_hand * cash_limit_pct:
            return False
        if v.skills_overlap_pct < 0.50:
            return False
        return True

    # Evaluate all rules
    candidates: list[VerticalOpportunity] = []
    for cond_fn, vertical in _RULES:
        try:
            if cond_fn(profile, domain_id):
                candidates.append(vertical)
        except Exception:
            continue

    # Try strict cash filter first (50%), then relax to 75%
    for limit in (0.50, 0.75, 1.00):
        filtered = [v for v in candidates if _passes(v, limit)]
        if len(filtered) >= min(3, top_n):
            break
    else:
        filtered = candidates  # include everything if still sparse

    # Deduplicate by name
    seen: set[str] = set()
    unique: list[VerticalOpportunity] = []
    for v in sorted(filtered, key=_score, reverse=True):
        if v.name not in seen:
            seen.add(v.name)
            unique.append(v)

    return tuple(unique[:top_n])
