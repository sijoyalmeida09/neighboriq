"""biz_profile.py — Comprehensive business asset profile for any domain."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__all__ = ["RevenueStream", "BizProfile", "from_yaml", "from_dict", "to_yaml_template"]


@dataclass(frozen=True)
class RevenueStream:
    name: str            # "consulting retainer", "product sales", "SaaS MRR"
    monthly_usd: int
    pct_of_total: float  # 0.0–1.0
    recurring: bool


@dataclass(frozen=True)
class BizProfile:
    # ── Identity ──────────────────────────────────────────────────────────────
    name: str
    description: str            # plain language; used for domain auto-detect
    naics_code: str | None      # e.g. "484110" (trucking); None if unknown
    year_founded: int | None
    website: str | None

    # ── Physical ──────────────────────────────────────────────────────────────
    equipment: tuple[tuple[str, int], ...]  # (("forklift", 45000), ...)
    inventory_value: int        # $ current value
    vehicles: int
    sqft_owned: int
    sqft_leased: int
    real_estate_value: int      # $ market value of owned property

    # ── Digital ───────────────────────────────────────────────────────────────
    monthly_web_traffic: int
    email_list_size: int
    social_followers: tuple[tuple[str, int], ...]  # (("instagram", 4200), ...)
    software_tools: tuple[str, ...]
    data_assets: tuple[str, ...]    # ("customer purchase history", "route telemetry")
    ip_patents: tuple[str, ...]

    # ── Human ─────────────────────────────────────────────────────────────────
    headcount: int
    roles: tuple[tuple[str, int], ...]  # (("driver", 8), ("dispatcher", 2))
    owner_certifications: tuple[str, ...]
    owner_network_size: int     # estimated relationship count

    # ── Financial ─────────────────────────────────────────────────────────────
    monthly_revenue: int
    monthly_expenses: int
    cash_on_hand: int
    credit_line: int
    monthly_debt_service: int

    # ── Brand ─────────────────────────────────────────────────────────────────
    years_in_market: int
    avg_rating: float           # 1.0–5.0
    review_count: int
    recognition: str            # "neighborhood" | "city" | "regional" | "national"

    # ── Operational ───────────────────────────────────────────────────────────
    licenses: tuple[str, ...]
    certifications: tuple[str, ...]
    exclusive_supplier_contracts: tuple[str, ...]
    proprietary_processes: tuple[str, ...]

    # ── Revenue ───────────────────────────────────────────────────────────────
    revenue_streams: tuple[RevenueStream, ...]

    @property
    def monthly_profit(self) -> int:
        return self.monthly_revenue - self.monthly_expenses - self.monthly_debt_service

    @property
    def total_asset_value(self) -> int:
        equip_val = sum(v for _, v in self.equipment)
        return equip_val + self.inventory_value + self.real_estate_value

    @property
    def total_social_followers(self) -> int:
        return sum(count for _, count in self.social_followers)

    @property
    def profit_margin(self) -> float:
        if self.monthly_revenue == 0:
            return 0.0
        return self.monthly_profit / self.monthly_revenue


# ── Loaders ───────────────────────────────────────────────────────────────────

def _to_pair_tuple(items: list | None, key_cast=str, val_cast=int) -> tuple[tuple, ...]:
    """Convert [[k, v], ...] or [{"k": v}, ...] to tuple of (k, v) tuples."""
    if not items:
        return ()
    result = []
    for item in items:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            result.append((key_cast(item[0]), val_cast(item[1])))
        elif isinstance(item, dict):
            k, v = list(item.items())[0]
            result.append((key_cast(k), val_cast(v)))
    return tuple(result)


def _to_str_tuple(items: list | None) -> tuple[str, ...]:
    if not items:
        return ()
    return tuple(str(i) for i in items)


def from_dict(data: dict[str, Any]) -> BizProfile:
    """Build BizProfile from a flat or nested dict (YAML/JSON source)."""
    biz = data.get("business", data)
    phys = data.get("physical", {})
    dig = data.get("digital", {})
    human = data.get("human", {})
    fin = data.get("financial", {})
    brand = data.get("brand", {})
    ops = data.get("operational", {})
    rev = data.get("revenue", {})

    raw_streams = rev.get("streams", data.get("revenue_streams", []))
    streams: list[RevenueStream] = []
    for s in raw_streams:
        if isinstance(s, dict):
            streams.append(RevenueStream(
                name=str(s.get("name", "")),
                monthly_usd=int(s.get("monthly_usd", 0)),
                pct_of_total=float(s.get("pct_of_total", 0.0)),
                recurring=bool(s.get("recurring", False)),
            ))
        elif isinstance(s, (list, tuple)) and len(s) >= 4:
            streams.append(RevenueStream(
                name=str(s[0]), monthly_usd=int(s[1]),
                pct_of_total=float(s[2]), recurring=bool(s[3]),
            ))

    return BizProfile(
        name=str(biz.get("name", "")),
        description=str(biz.get("description", "")),
        naics_code=biz.get("naics_code") or None,
        year_founded=int(biz["year_founded"]) if biz.get("year_founded") else None,
        website=biz.get("website") or None,
        equipment=_to_pair_tuple(phys.get("equipment", data.get("equipment", []))),
        inventory_value=int(phys.get("inventory_value", data.get("inventory_value", 0))),
        vehicles=int(phys.get("vehicles", data.get("vehicles", 0))),
        sqft_owned=int(phys.get("sqft_owned", data.get("sqft_owned", 0))),
        sqft_leased=int(phys.get("sqft_leased", data.get("sqft_leased", 0))),
        real_estate_value=int(phys.get("real_estate_value", data.get("real_estate_value", 0))),
        monthly_web_traffic=int(dig.get("monthly_web_traffic", data.get("monthly_web_traffic", 0))),
        email_list_size=int(dig.get("email_list_size", data.get("email_list_size", 0))),
        social_followers=_to_pair_tuple(dig.get("social_followers", data.get("social_followers", []))),
        software_tools=_to_str_tuple(dig.get("software_tools", data.get("software_tools", []))),
        data_assets=_to_str_tuple(dig.get("data_assets", data.get("data_assets", []))),
        ip_patents=_to_str_tuple(dig.get("ip_patents", data.get("ip_patents", []))),
        headcount=int(human.get("headcount", data.get("headcount", 0))),
        roles=_to_pair_tuple(human.get("roles", data.get("roles", []))),
        owner_certifications=_to_str_tuple(
            human.get("owner_certifications", data.get("owner_certifications", []))
        ),
        owner_network_size=int(human.get("owner_network_size", data.get("owner_network_size", 0))),
        monthly_revenue=int(fin.get("monthly_revenue", data.get("monthly_revenue", 0))),
        monthly_expenses=int(fin.get("monthly_expenses", data.get("monthly_expenses", 0))),
        cash_on_hand=int(fin.get("cash_on_hand", data.get("cash_on_hand", 0))),
        credit_line=int(fin.get("credit_line", data.get("credit_line", 0))),
        monthly_debt_service=int(fin.get("monthly_debt_service", data.get("monthly_debt_service", 0))),
        years_in_market=int(brand.get("years_in_market", data.get("years_in_market", 0))),
        avg_rating=float(brand.get("avg_rating", data.get("avg_rating", 0.0))),
        review_count=int(brand.get("review_count", data.get("review_count", 0))),
        recognition=str(brand.get("recognition", data.get("recognition", "neighborhood"))),
        licenses=_to_str_tuple(ops.get("licenses", data.get("licenses", []))),
        certifications=_to_str_tuple(ops.get("certifications", data.get("certifications", []))),
        exclusive_supplier_contracts=_to_str_tuple(
            ops.get("exclusive_supplier_contracts", data.get("exclusive_supplier_contracts", []))
        ),
        proprietary_processes=_to_str_tuple(
            ops.get("proprietary_processes", data.get("proprietary_processes", []))
        ),
        revenue_streams=tuple(streams),
    )


def from_yaml(path: str) -> BizProfile:
    """Load BizProfile from a YAML (.yaml/.yml) or JSON (.json) file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Profile not found: {path}")

    if p.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore[import-untyped]
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
        except ImportError as exc:
            raise ImportError(
                "PyYAML is required to load .yaml profiles.\n"
                "Install it: pip install pyyaml\n"
                "Or save your profile as .json instead."
            ) from exc
    else:
        data = json.loads(p.read_text(encoding="utf-8"))

    return from_dict(data or {})


_YAML_TEMPLATE = """\
# NeighborIQ Business Profile
# Fill in your business details, then run:
#   neighboriq biz-audit --profile this_file.yaml
# Leave unknown numeric fields as 0; leave unknown text fields as null.

business:
  name: "My Business Name"
  description: "One sentence describing what your business does and who it serves"
  naics_code: null        # e.g. "484110" trucking | "722511" restaurant | null if unknown
  year_founded: null      # e.g. 2019
  website: null           # e.g. "https://mybusiness.com"

physical:
  equipment: []           # [[name, value_usd], ...] e.g. [["truck", 45000], ["forklift", 8000]]
  inventory_value: 0      # current inventory value in $
  vehicles: 0             # vehicles owned or leased
  sqft_owned: 0           # square feet owned outright
  sqft_leased: 0          # square feet leased/rented
  real_estate_value: 0    # market value of owned real estate in $

digital:
  monthly_web_traffic: 0
  email_list_size: 0
  social_followers:       # [[platform, count], ...]
    - ["instagram", 0]
    - ["facebook", 0]
    - ["linkedin", 0]
    - ["tiktok", 0]
    - ["youtube", 0]
  software_tools: []      # e.g. ["QuickBooks", "Shopify", "Salesforce", "HubSpot"]
  data_assets: []         # e.g. ["customer purchase history", "route telemetry", "3 years POS data"]
  ip_patents: []          # e.g. ["proprietary sauce recipe", "patented process", "custom software"]

human:
  headcount: 0
  roles: []  # [[role_title, count], ...] e.g. [["driver", 4], ["dispatcher", 1]]
  owner_certifications: []  # e.g. ["DOT authority", "ServSafe", "General Contractor"]
  owner_network_size: 0  # estimated professional contacts/relationships

financial:
  monthly_revenue: 0
  monthly_expenses: 0
  cash_on_hand: 0
  credit_line: 0       # total available credit line in $
  monthly_debt_service: 0  # monthly loan/lease payments

brand:
  years_in_market: 0
  avg_rating: 0.0      # Google/Yelp rating 1.0-5.0
  review_count: 0
  recognition: neighborhood  # neighborhood | city | regional | national

operational:
  licenses: []         # e.g. ["DOT authority MC-123456", "food handler permit", "contractor license"]
  certifications: []   # e.g. ["ISO 9001", "HACCP", "ServSafe Manager"]
  exclusive_supplier_contracts: []  # e.g. ["Sysco regional exclusivity"]
  proprietary_processes: []  # e.g. ["24hr fulfillment SLA", "secret blend formula"]

revenue:
  streams:             # list of revenue streams
    - name: Primary Revenue
      monthly_usd: 0
      pct_of_total: 1.0
      recurring: false
    # Add more streams below:
    # - name: Maintenance contracts
    #   monthly_usd: 0
    #   pct_of_total: 0.0
    #   recurring: true
"""


def to_yaml_template(path: str) -> None:
    """Write a blank business profile YAML template to path."""
    Path(path).write_text(_YAML_TEMPLATE, encoding="utf-8")

