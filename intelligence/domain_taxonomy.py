"""domain_taxonomy.py — Maps any business to one of 14 standardised domain categories."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neighboriq.intelligence.biz_profile import BizProfile

__all__ = ["DomainSpec", "classify", "get_domain", "list_domains"]


@dataclass(frozen=True)
class DomainSpec:
    domain_id: str
    label: str
    naics_prefixes: tuple[str, ...]     # matched against BizProfile.naics_code
    keywords: tuple[str, ...]           # matched against BizProfile.description (lowercase)
    key_metrics: tuple[str, ...]        # what to benchmark: margins, churn, utilization…
    benchmark_sources: tuple[str, ...]  # human-readable source names
    benchmark_api_ids: tuple[str, ...]  # machine-readable source keys for benchmark_engine


_DOMAINS: dict[str, DomainSpec] = {}


def _reg(domain_id: str, **kw: object) -> None:
    _DOMAINS[domain_id] = DomainSpec(domain_id=domain_id, **kw)  # type: ignore[arg-type]


# ── 14 Domain Registrations ───────────────────────────────────────────────────

_reg(
    "local_service",
    label="Local Services",
    naics_prefixes=("8121", "8122", "8123", "8129", "8111", "8112", "8113"),
    keywords=(
        "barbershop", "barber", "nail salon", "nail", "laundromat", "dry clean",
        "auto repair", "mechanic", "car wash", "pet grooming", "tailoring",
        "alterations", "shoe repair", "locksmith", "cleaning service",
        "pool service", "lawn care", "landscaping",
    ),
    key_metrics=("net_margin", "revenue_per_sqft", "customer_ltv", "repeat_rate"),
    benchmark_sources=("Census CBP", "SBA Size Standards", "NeighborIQ curated (HIGH)"),
    benchmark_api_ids=("census_cbp", "sba_size_standards", "neighboriq_niche_roadmap"),
)

_reg(
    "food_beverage",
    label="Food & Beverage",
    naics_prefixes=("7225", "7224", "3111", "3112", "3113", "3114", "3115", "3116"),
    keywords=(
        "restaurant", "cafe", "coffee", "bakery", "food truck", "catering",
        "bar", "brewery", "winery", "distillery", "deli", "sandwich", "pizza",
        "sushi", "taco", "burger", "food production", "meal prep", "ghost kitchen",
    ),
    key_metrics=("food_cost_pct", "labor_cost_pct", "revenue_per_seat", "table_turn_rate"),
    benchmark_sources=("Census CBP", "BLS OES (kitchen labor)", "NRA State of the Industry"),
    benchmark_api_ids=("census_cbp", "bls_oes", "damodaran"),
)

_reg(
    "healthcare",
    label="Healthcare & Wellness",
    naics_prefixes=("621", "622", "623", "8011", "8021", "8031", "8041", "8049"),
    keywords=(
        "clinic", "medical", "dental", "dentist", "physical therapy", "chiropractic",
        "optometry", "dermatology", "mental health", "therapy", "counseling",
        "wellness", "spa", "massage", "acupuncture", "telehealth", "urgent care",
        "pharmacy", "home health", "hospice",
    ),
    key_metrics=("revenue_per_provider", "payer_mix", "collections_rate", "no_show_rate"),
    benchmark_sources=("CMS Open Data", "BLS OES", "Census CBP"),
    benchmark_api_ids=("cms_open_data", "bls_oes", "census_cbp"),
)

_reg(
    "logistics",
    label="Logistics & Transportation",
    naics_prefixes=("484", "485", "488", "492", "493"),
    keywords=(
        "trucking", "freight", "logistics", "shipping", "delivery", "courier",
        "last mile", "3pl", "third party logistics", "warehouse", "warehousing",
        "transportation", "carrier", "dispatch", "fleet", "drayage", "ltl", "ftl",
        "freight broker", "brokerage",
    ),
    key_metrics=("revenue_per_mile", "empty_mile_pct", "driver_utilization", "fuel_cost_pct"),
    benchmark_sources=("BTS Supply Chain Data", "FRED Freight Index", "Census SUSB"),
    benchmark_api_ids=("bts_open_data", "fred", "census_susb"),
)

_reg(
    "distribution",
    label="Wholesale Distribution",
    naics_prefixes=("423", "424", "425"),
    keywords=(
        "distribution", "distributor", "wholesale", "wholesaler", "supply chain",
        "import", "export", "trading company", "commodity", "regional distributor",
        "tobacco distributor", "food distributor", "beverage distributor",
        "medical supply", "industrial supply",
    ),
    key_metrics=("gross_margin", "inventory_turns", "fill_rate", "revenue_per_employee"),
    benchmark_sources=("Census SUSB", "FRED PPI Wholesale", "Damodaran"),
    benchmark_api_ids=("census_susb", "fred", "damodaran"),
)

_reg(
    "manufacturing",
    label="Manufacturing",
    naics_prefixes=("31", "32", "33"),
    keywords=(
        "manufacturing", "manufacturer", "production", "fabrication", "assembly",
        "factory", "plant", "machining", "welding", "printing", "packaging",
        "food processing", "woodworking", "metalworking", "plastics", "textiles",
        "custom manufacturing", "contract manufacturing",
    ),
    key_metrics=("oee", "scrap_rate", "revenue_per_employee", "inventory_turns"),
    benchmark_sources=("Census Annual Survey of Manufactures", "FRED", "Damodaran"),
    benchmark_api_ids=("census_aies", "fred", "damodaran"),
)

_reg(
    "software_saas",
    label="Software & SaaS",
    naics_prefixes=("5112", "5415", "5182"),
    keywords=(
        "saas", "software", "app", "application", "platform", "crm", "erp",
        "api", "developer tools", "b2b software", "subscription software",
        "mobile app", "web app", "marketplace", "fintech", "edtech", "healthtech",
        "proptech", "legaltech", "no-code", "low-code",
    ),
    key_metrics=("mrr", "arr", "churn", "ltv_cac_ratio", "ndr", "rule_of_40"),
    benchmark_sources=("re:cap SaaS Benchmarks", "OpenCollective", "Damodaran"),
    benchmark_api_ids=("recap_saas", "opencollective", "damodaran"),
)

_reg(
    "agency_services",
    label="Agency & Professional Services",
    naics_prefixes=("5411", "5412", "5413", "5414", "5416", "5417", "5418", "5419", "7389"),
    keywords=(
        "agency", "marketing agency", "design agency", "consulting", "consultant",
        "accounting", "bookkeeping", "cpa", "law firm", "legal", "architecture",
        "engineering firm", "recruiting", "staffing", "hr consulting",
        "management consulting", "pr agency", "advertising",
    ),
    key_metrics=("billable_utilization", "revenue_per_fte", "gross_margin", "client_retention"),
    benchmark_sources=("BLS OES", "Census SUSB", "SBA Size Standards"),
    benchmark_api_ids=("bls_oes", "census_susb", "damodaran"),
)

_reg(
    "music_entertainment",
    label="Music & Entertainment",
    naics_prefixes=("7111", "7112", "7113", "7114", "7115", "5121", "5122"),
    keywords=(
        "music", "musician", "artist", "band", "label", "record label", "studio",
        "recording studio", "concert", "venue", "live music", "event production",
        "entertainment", "performer", "dj", "producer", "sync licensing",
        "music distribution", "streaming", "royalty",
    ),
    key_metrics=("royalty_revenue", "streaming_income", "live_revenue_split", "catalog_value"),
    benchmark_sources=("MusicBrainz", "ListenBrainz", "Spotify API", "RIAA public data"),
    benchmark_api_ids=("musicbrainz", "listenbrainz", "spotify_api", "damodaran"),
)

_reg(
    "retail",
    label="Retail",
    naics_prefixes=("44", "45"),
    keywords=(
        "retail", "store", "shop", "boutique", "ecommerce", "e-commerce", "online store",
        "amazon seller", "fba", "etsy", "shopify", "convenience store", "c-store",
        "clothing store", "shoe store", "electronics store", "bookstore",
        "gift shop", "toy store", "sporting goods",
    ),
    key_metrics=("gross_margin", "inventory_turns", "revenue_per_sqft", "conversion_rate"),
    benchmark_sources=("Census Monthly Retail Trade", "BLS", "Damodaran"),
    benchmark_api_ids=("census_susb", "bls_oes", "damodaran"),
)

_reg(
    "real_estate",
    label="Real Estate & Property",
    naics_prefixes=("531",),
    keywords=(
        "real estate", "property management", "landlord", "rental", "apartment",
        "commercial real estate", "cre", "short-term rental", "airbnb", "vrbo",
        "brokerage", "realtor", "developer", "reit", "multifamily",
    ),
    key_metrics=("cap_rate", "noi", "vacancy_rate", "revenue_per_unit"),
    benchmark_sources=("Zillow Research", "HUD FMR API", "FRED Real Estate"),
    benchmark_api_ids=("zillow_research", "hud_api", "fred"),
)

_reg(
    "education",
    label="Education & Training",
    naics_prefixes=("611", "6111", "6112", "6113", "6114", "6115", "6116", "6117"),
    keywords=(
        "tutoring", "tutor", "learning center", "education", "school", "training",
        "e-learning", "online course", "bootcamp", "coding school", "daycare",
        "preschool", "after-school", "test prep", "sat", "gre", "professional training",
        "certification program", "workshop",
    ),
    key_metrics=("revenue_per_student", "enrollment", "student_ltv", "completion_rate"),
    benchmark_sources=("NCES Public Datasets", "BLS OES", "Census SUSB"),
    benchmark_api_ids=("nces_ipeds", "bls_oes", "census_susb"),
)

_reg(
    "creative_media",
    label="Creative & Media",
    naics_prefixes=("5121", "5122", "5151", "5152", "7115", "5418"),
    keywords=(
        "photography", "videography", "video production", "content creator",
        "podcast", "youtube", "streaming", "graphic design", "animation",
        "filmmaking", "documentary", "media company", "content studio",
        "social media", "influencer", "creator economy",
    ),
    key_metrics=("revenue_per_project", "audience_size", "sponsorship_rate", "licensing_income"),
    benchmark_sources=("BLS OES", "Census SUSB", "ListenBrainz/Spotify"),
    benchmark_api_ids=("bls_oes", "census_susb", "damodaran"),
)

_reg(
    "professional_services",
    label="Professional Services",
    naics_prefixes=("5411", "5412", "5241", "5242", "5231", "5232", "5239"),
    keywords=(
        "financial advisor", "wealth management", "insurance", "insurance agency",
        "tax preparer", "estate planning", "financial planning", "mortgage broker",
        "accountant", "auditor", "actuary",
    ),
    key_metrics=("revenue_per_advisor", "aum", "client_retention", "compliance_cost"),
    benchmark_sources=("BLS OES", "Census SUSB", "SBA Size Standards"),
    benchmark_api_ids=("bls_oes", "census_susb", "damodaran"),
)


# ── Public API ────────────────────────────────────────────────────────────────

_FALLBACK = DomainSpec(
    domain_id="unknown",
    label="Unknown Domain",
    naics_prefixes=(),
    keywords=(),
    key_metrics=("revenue", "net_margin", "headcount"),
    benchmark_sources=("Census SUSB", "Damodaran", "BLS OES"),
    benchmark_api_ids=("census_susb", "damodaran", "bls_oes"),
)


def classify(profile: "BizProfile") -> DomainSpec:
    """Map a BizProfile to a DomainSpec via NAICS code first, then keyword match."""
    naics = (profile.naics_code or "").strip()
    if naics:
        for spec in _DOMAINS.values():
            for prefix in spec.naics_prefixes:
                if naics.startswith(prefix):
                    return spec

    desc_lower = profile.description.lower()
    best: DomainSpec | None = None
    best_hits = 0
    for spec in _DOMAINS.values():
        hits = sum(1 for kw in spec.keywords if kw in desc_lower)
        if hits > best_hits:
            best_hits = hits
            best = spec

    return best if best and best_hits > 0 else _FALLBACK


def get_domain(domain_id: str) -> DomainSpec:
    """Return DomainSpec by ID, or the fallback spec if not found."""
    return _DOMAINS.get(domain_id, _FALLBACK)


def list_domains() -> list[str]:
    """Return all registered domain IDs, sorted."""
    return sorted(_DOMAINS.keys())
