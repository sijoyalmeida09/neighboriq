"""revenue_model.py — Full P&L model per business niche.

Provides startup capital tiers, monthly revenue ranges, cost structure,
net margins at each staffing level, payback periods, and escalation paths.
All figures use real US small-business benchmarks (2024).
"""
from __future__ import annotations

from dataclasses import dataclass

__all__ = ["RevenueModel", "get_revenue_model", "format_revenue_model", "list_niches"]


@dataclass(frozen=True)
class RevenueModel:
    niche: str

    # ── Startup capital tiers ────────────────────────────────────────────────
    startup_home_based: int   # home / mobile / online-only launch
    startup_small: int        # kiosk, chair sublease, sub-1000 sqft
    startup_full: int         # full storefront build-out

    # ── Monthly revenue range ─────────────────────────────────────────────────
    revenue_conservative: int
    revenue_median: int
    revenue_optimistic: int

    # ── Cost structure ────────────────────────────────────────────────────────
    cogs_pct: float           # direct cost as % of revenue
    rent_monthly_low: int
    rent_monthly_mid: int
    utilities_monthly: int    # separate from COGS

    # ── Staff cost estimates (monthly) ────────────────────────────────────────
    staff_solo_monthly: int   # owner draw / total if working alone
    staff_1_monthly: int      # cost of 1 part-time employee
    staff_2_monthly: int      # cost of 2 employees

    # ── Derived margins (computed at median revenue, mid rent, 1-staff) ───────
    gross_margin_pct: float
    net_margin_solo_pct: float
    net_margin_1staff_pct: float

    # ── Payback on startup_small investment ───────────────────────────────────
    payback_solo_months: int
    payback_1staff_months: int

    # ── Automation impact ────────────────────────────────────────────────────
    automation_monthly_savings: int

    # ── Business model descriptions ──────────────────────────────────────────
    model_solo_description: str
    model_1staff_description: str
    model_2staff_description: str

    # ── Margin classification & growth path ───────────────────────────────────
    margin_tier: str       # "low" <15% | "medium" 15–30% | "high" >30%
    escalation_path: str


# ── helpers ──────────────────────────────────────────────────────────────────

def _tier(pct: float) -> str:
    if pct >= 30:
        return "high"
    if pct >= 15:
        return "medium"
    return "low"


def _payback(startup_small: int, monthly_net: float) -> int:
    if monthly_net <= 0:
        return 999
    return max(1, round(startup_small / monthly_net))


_MODELS: dict[str, RevenueModel] = {}


def _reg(
    niche: str,
    *,
    startup_home_based: int,
    startup_small: int,
    startup_full: int,
    revenue_conservative: int,
    revenue_median: int,
    revenue_optimistic: int,
    cogs_pct: float,
    rent_monthly_low: int,
    rent_monthly_mid: int,
    utilities_monthly: int,
    staff_solo_monthly: int,
    staff_1_monthly: int,
    staff_2_monthly: int,
    automation_monthly_savings: int,
    model_solo_description: str,
    model_1staff_description: str,
    model_2staff_description: str,
    escalation_path: str,
) -> RevenueModel:
    rev = revenue_median
    cogs = rev * cogs_pct / 100.0
    gross = round(100.0 - cogs_pct, 1)
    net_solo_raw = rev - cogs - rent_monthly_mid - utilities_monthly
    net_1_raw = net_solo_raw - staff_1_monthly
    net_solo_pct = round(net_solo_raw / rev * 100, 1) if rev else 0.0
    net_1_pct = round(net_1_raw / rev * 100, 1) if rev else 0.0

    m = RevenueModel(
        niche=niche,
        startup_home_based=startup_home_based,
        startup_small=startup_small,
        startup_full=startup_full,
        revenue_conservative=revenue_conservative,
        revenue_median=revenue_median,
        revenue_optimistic=revenue_optimistic,
        cogs_pct=cogs_pct,
        rent_monthly_low=rent_monthly_low,
        rent_monthly_mid=rent_monthly_mid,
        utilities_monthly=utilities_monthly,
        staff_solo_monthly=staff_solo_monthly,
        staff_1_monthly=staff_1_monthly,
        staff_2_monthly=staff_2_monthly,
        gross_margin_pct=gross,
        net_margin_solo_pct=net_solo_pct,
        net_margin_1staff_pct=net_1_pct,
        payback_solo_months=_payback(startup_small, net_solo_raw),
        payback_1staff_months=_payback(startup_small, net_1_raw),
        automation_monthly_savings=automation_monthly_savings,
        model_solo_description=model_solo_description,
        model_1staff_description=model_1staff_description,
        model_2staff_description=model_2staff_description,
        margin_tier=_tier(net_solo_pct),
        escalation_path=escalation_path,
    )
    _MODELS[niche] = m
    return m


# ── niche library ─────────────────────────────────────────────────────────────

_reg(
    "barbershop",
    startup_home_based=5_000,
    startup_small=15_000,
    startup_full=30_000,
    revenue_conservative=5_000,
    revenue_median=8_000,
    revenue_optimistic=16_000,
    cogs_pct=12.0,
    rent_monthly_low=1_200,
    rent_monthly_mid=1_800,
    utilities_monthly=200,
    staff_solo_monthly=3_500,
    staff_1_monthly=2_500,
    staff_2_monthly=5_000,
    automation_monthly_savings=700,
    model_solo_description=(
        "Owner cuts hair 6 days/week. Online booking via Calendly eliminates phone tag. "
        "Square POS handles payment + tips. Runs on ~8 hrs/day."
    ),
    model_1staff_description=(
        "Owner + 1 barber. Owner takes premium/loyal clients, staff handles walk-ins. "
        "Owner shifts 20% of time to management and marketing."
    ),
    model_2staff_description=(
        "2 barbers + owner as manager. Owner focuses on supplier deals, social media, "
        "booth-rental revenue. Target: $2,500/chair/month in booth rent."
    ),
    escalation_path=(
        "Solo chair → 2 chairs → booth rental model ($1K-2K/chair/month passive) → "
        "franchise or second location. Each chair adds ~$5K-8K revenue with minimal overhead."
    ),
)

_reg(
    "nail_salon",
    startup_home_based=8_000,
    startup_small=25_000,
    startup_full=50_000,
    revenue_conservative=8_000,
    revenue_median=15_000,
    revenue_optimistic=28_000,
    cogs_pct=20.0,
    rent_monthly_low=1_500,
    rent_monthly_mid=2_200,
    utilities_monthly=300,
    staff_solo_monthly=4_000,
    staff_1_monthly=3_000,
    staff_2_monthly=6_000,
    automation_monthly_savings=500,
    model_solo_description=(
        "Owner does all nail services. Appointment-only via booking app. "
        "Handles supply orders, marketing via Instagram. ~45 hrs/week."
    ),
    model_1staff_description=(
        "Owner + 1 nail tech. Owner takes specialty services (gel, acrylic art). "
        "Staff handles basics. Double throughput, minor management overhead."
    ),
    model_2staff_description=(
        "2 nail techs + owner as manager/lead artist. Owner focuses on training, "
        "social content, supply negotiation. Targets $25K/mo revenue."
    ),
    escalation_path=(
        "Solo → add 1 tech when consistently booked 2 weeks out → add lash services "
        "(high-margin add-on at $80-150/set) → beauty suite model with subleased stations."
    ),
)

_reg(
    "hair_salon",
    startup_home_based=5_000,
    startup_small=20_000,
    startup_full=60_000,
    revenue_conservative=6_000,
    revenue_median=12_000,
    revenue_optimistic=22_000,
    cogs_pct=25.0,
    rent_monthly_low=1_500,
    rent_monthly_mid=2_500,
    utilities_monthly=300,
    staff_solo_monthly=4_000,
    staff_1_monthly=3_200,
    staff_2_monthly=6_400,
    automation_monthly_savings=500,
    model_solo_description=(
        "Stylist-owner sees clients by appointment. Retail product sales pad revenue by 10-15%. "
        "Instagram-driven client acquisition."
    ),
    model_1staff_description=(
        "Owner + 1 stylist. Booth rental model keeps costs predictable. "
        "Owner handles color work (highest margin), staff handles cuts."
    ),
    model_2staff_description=(
        "2+ stylists + owner as lead. Suite-based model: each stylist rents a suite at "
        "$700-1,200/mo, owner keeps retail and owns the lease."
    ),
    escalation_path=(
        "Solo stylist → booth rental ($700-1,200/booth/month) → multi-suite building → "
        "product line (house-brand retail at 60% margin vs 30% on brands)."
    ),
)

_reg(
    "coffee_shop",
    startup_home_based=3_000,
    startup_small=30_000,
    startup_full=80_000,
    revenue_conservative=8_000,
    revenue_median=18_000,
    revenue_optimistic=40_000,
    cogs_pct=30.0,
    rent_monthly_low=2_000,
    rent_monthly_mid=3_500,
    utilities_monthly=600,
    staff_solo_monthly=4_000,
    staff_1_monthly=3_000,
    staff_2_monthly=6_000,
    automation_monthly_savings=700,
    model_solo_description=(
        "Owner-barista works opening shift. Automated espresso machine reduces skill barrier. "
        "Mobile order app reduces counter time. Kiosk model keeps overhead minimal."
    ),
    model_1staff_description=(
        "Owner + 1 barista covers AM and PM peaks. Owner handles back-of-house: "
        "ordering, books, social. Revenue target: $600/day."
    ),
    model_2staff_description=(
        "2 baristas + owner. Owner opens and closes, mid-day freedom. "
        "Add wholesale bean sales to local offices for $3K-5K/mo passive revenue."
    ),
    escalation_path=(
        "Kiosk → storefront → wholesale coffee subscriptions ($50-100/mo recurring) → "
        "second location or coffee cart at events ($2K-5K/event day)."
    ),
)

_reg(
    "cafe",
    startup_home_based=5_000,
    startup_small=25_000,
    startup_full=60_000,
    revenue_conservative=6_000,
    revenue_median=14_000,
    revenue_optimistic=28_000,
    cogs_pct=35.0,
    rent_monthly_low=1_800,
    rent_monthly_mid=3_000,
    utilities_monthly=500,
    staff_solo_monthly=3_500,
    staff_1_monthly=3_000,
    staff_2_monthly=6_000,
    automation_monthly_savings=600,
    model_solo_description=(
        "Owner cooks and serves. Limited menu reduces waste. "
        "Online pre-orders cut rush-hour chaos. Closed 2 days/week."
    ),
    model_1staff_description=(
        "Owner cooks, staff serves and handles register. Doubles throughput. "
        "Staff frees owner to prep specials and manage social content."
    ),
    model_2staff_description=(
        "Kitchen + counter covered by staff. Owner becomes operator: purchasing, "
        "hiring, catering side business ($500-1,500/event)."
    ),
    escalation_path=(
        "Dine-in → catering add-on (35-45% margin) → meal prep subscription kits → "
        "ghost kitchen model renting kitchen to other chefs at $20-40/hr."
    ),
)

_reg(
    "bakery",
    startup_home_based=5_000,
    startup_small=30_000,
    startup_full=70_000,
    revenue_conservative=5_000,
    revenue_median=12_000,
    revenue_optimistic=24_000,
    cogs_pct=35.0,
    rent_monthly_low=1_500,
    rent_monthly_mid=2_800,
    utilities_monthly=600,
    staff_solo_monthly=3_500,
    staff_1_monthly=2_800,
    staff_2_monthly=5_600,
    automation_monthly_savings=400,
    model_solo_description=(
        "Owner bakes 4 AM-noon, sells noon-6 PM. Cottage food license covers home start. "
        "Farmers markets add $800-1,500/weekend with no rent."
    ),
    model_1staff_description=(
        "Owner bakes, assistant handles counter + packaging. Owner gains time for "
        "custom cake orders (high margin: $150-500/cake)."
    ),
    model_2staff_description=(
        "Production baker + counter staff + owner as head baker / business lead. "
        "Wholesale to local cafes adds $3K-8K/mo at lower margin but no retail overhead."
    ),
    escalation_path=(
        "Home cottage → farmers market → storefront → wholesale accounts → "
        "custom cake studio (premium tier: $400-1,200 per wedding cake at 65% margin)."
    ),
)

_reg(
    "tutoring_center",
    startup_home_based=2_000,
    startup_small=15_000,
    startup_full=30_000,
    revenue_conservative=4_000,
    revenue_median=9_000,
    revenue_optimistic=20_000,
    cogs_pct=10.0,
    rent_monthly_low=800,
    rent_monthly_mid=1_500,
    utilities_monthly=150,
    staff_solo_monthly=3_500,
    staff_1_monthly=3_000,
    staff_2_monthly=6_000,
    automation_monthly_savings=400,
    model_solo_description=(
        "Owner tutors 25-30 hrs/week. Online sessions reduce commute, expand market. "
        "Packages ($400-800/mo per student) create stable recurring revenue."
    ),
    model_1staff_description=(
        "Owner + 1 tutor (part-time, often a grad student at $20-25/hr). "
        "Owner handles STEM + test prep; staff covers humanities. Doubles capacity."
    ),
    model_2staff_description=(
        "2 tutors + owner as director. Owner handles intake, curriculum, and marketing. "
        "Group sessions ($50-80/hr split across 4-6 students) boost revenue/hour 3x."
    ),
    escalation_path=(
        "Solo → group classes → recorded course library (sell at $197-497, zero marginal cost) → "
        "franchise curriculum or school district contracts ($5K-50K/year B2B)."
    ),
)

_reg(
    "daycare",
    startup_home_based=15_000,
    startup_small=80_000,
    startup_full=150_000,
    revenue_conservative=8_000,
    revenue_median=22_000,
    revenue_optimistic=45_000,
    cogs_pct=20.0,
    rent_monthly_low=2_000,
    rent_monthly_mid=4_000,
    utilities_monthly=500,
    staff_solo_monthly=4_000,
    staff_1_monthly=4_500,
    staff_2_monthly=9_000,
    automation_monthly_savings=500,
    model_solo_description=(
        "Licensed home daycare: 6-8 children, owner is lead caregiver. "
        "Revenue: $1,200-2,000/child/month. Waitlists common in underserved areas."
    ),
    model_1staff_description=(
        "Owner + 1 licensed assistant. State ratio allows 10-12 children. "
        "Revenue $14K-24K/mo. Staff enables breaks and compliance headroom."
    ),
    model_2staff_description=(
        "2 staff + owner as director. Capacity 15-20 children. Owner handles "
        "enrollment, billing, state compliance, parent communication."
    ),
    escalation_path=(
        "Home daycare → licensed center → after-school program add-on → "
        "summer camp ($500-800/child/week) → second location. State subsidies (CCAP) "
        "guarantee revenue floor."
    ),
)

_reg(
    "laundromat",
    startup_home_based=0,
    startup_small=80_000,
    startup_full=200_000,
    revenue_conservative=5_000,
    revenue_median=10_000,
    revenue_optimistic=18_000,
    cogs_pct=8.0,
    rent_monthly_low=2_000,
    rent_monthly_mid=3_500,
    utilities_monthly=3_200,
    staff_solo_monthly=1_000,
    staff_1_monthly=2_200,
    staff_2_monthly=4_400,
    automation_monthly_savings=2_000,
    model_solo_description=(
        "Owner visits 2-3×/week for machine maintenance, money collection, restocking. "
        "~10 hrs/week total. Payment kiosks eliminate cash handling. Highly passive."
    ),
    model_1staff_description=(
        "Attendant on-site full-time. Adds wash-dry-fold service ($2-3/lb) raising "
        "revenue 30-40%. Owner visits once/week."
    ),
    model_2staff_description=(
        "Full staffing: wash-dry-fold + drop-off + pickup/delivery. "
        "Delivery route adds $3K-8K/mo. Owner is fully absentee."
    ),
    escalation_path=(
        "Coin-op only → wash-dry-fold service → pickup/delivery subscription → "
        "commercial laundry accounts (gyms, hotels, restaurants at $500-5K/account/month)."
    ),
)

_reg(
    "check_cashing",
    startup_home_based=0,
    startup_small=50_000,
    startup_full=80_000,
    revenue_conservative=8_000,
    revenue_median=15_000,
    revenue_optimistic=28_000,
    cogs_pct=15.0,
    rent_monthly_low=1_500,
    rent_monthly_mid=2_500,
    utilities_monthly=300,
    staff_solo_monthly=3_500,
    staff_1_monthly=3_000,
    staff_2_monthly=6_000,
    automation_monthly_savings=600,
    model_solo_description=(
        "Owner operates counter in high-foot-traffic location. Fees: 1-5% per check. "
        "Bill pay, money orders, and prepaid cards add $2K-5K/mo."
    ),
    model_1staff_description=(
        "Owner + 1 counter staff. Owner handles compliance/compliance training, "
        "cash management, and banking relationships. Staff runs the counter."
    ),
    model_2staff_description=(
        "2 counter staff + owner as manager. Multiple windows increase throughput "
        "during peak (1st/15th of month, tax season = 3× normal volume)."
    ),
    escalation_path=(
        "Check cashing → bill pay hub → wire transfers → prepaid debit → "
        "small-dollar loans (where licensed) → become a neighborhood financial hub. "
        "Each service adds 15-25% revenue with minimal incremental cost."
    ),
)

_reg(
    "convenience_store",
    startup_home_based=0,
    startup_small=50_000,
    startup_full=100_000,
    revenue_conservative=20_000,
    revenue_median=45_000,
    revenue_optimistic=90_000,
    cogs_pct=72.0,
    rent_monthly_low=2_500,
    rent_monthly_mid=4_000,
    utilities_monthly=800,
    staff_solo_monthly=4_000,
    staff_1_monthly=3_500,
    staff_2_monthly=7_000,
    automation_monthly_savings=2_000,
    model_solo_description=(
        "Owner works the counter. High volume, low margin per item. "
        "Revenue per sq ft is key metric. Lottery commission adds 5-7% pure margin."
    ),
    model_1staff_description=(
        "Owner + 1 cashier. Owner handles ordering, receiving, loss prevention. "
        "Staff frees owner to negotiate better vendor terms (key profit lever)."
    ),
    model_2staff_description=(
        "2 staff cover AM/PM shifts. Owner manages from off-site. "
        "Hot food program ($1.50 cost → $4.99 sell price) boosts gross margin to 35%."
    ),
    escalation_path=(
        "Commodity goods (7% margin) → hot food program (70% margin) → "
        "ATM income ($150-300/mo/machine) → lottery terminal → "
        "money services (MoneyGram, utility payments) — each adds margin without inventory."
    ),
)

_reg(
    "liquor_store",
    startup_home_based=0,
    startup_small=80_000,
    startup_full=150_000,
    revenue_conservative=20_000,
    revenue_median=45_000,
    revenue_optimistic=80_000,
    cogs_pct=65.0,
    rent_monthly_low=2_500,
    rent_monthly_mid=4_000,
    utilities_monthly=600,
    staff_solo_monthly=4_000,
    staff_1_monthly=3_500,
    staff_2_monthly=7_000,
    automation_monthly_savings=800,
    model_solo_description=(
        "Owner-operator. License is the moat — new licenses are hard to get. "
        "Craft beer and local spirits carry 35-40% margin vs national brands at 20%."
    ),
    model_1staff_description=(
        "Owner + 1 staff. Owner curates premium selection (margin lever). "
        "Regular tasting events drive $3K-8K/event in sales."
    ),
    model_2staff_description=(
        "2 staff + owner as buyer/manager. Delivery service (Drizly/direct) adds "
        "15-20% volume. Private-label spirits possible at 50%+ margin."
    ),
    escalation_path=(
        "National brands (low margin) → craft/local curation (high margin) → "
        "tasting events → private label spirits → delivery subscription → "
        "second license location (10× harder to get but 10× the moat)."
    ),
)

_reg(
    "indian_restaurant",
    startup_home_based=5_000,
    startup_small=50_000,
    startup_full=150_000,
    revenue_conservative=12_000,
    revenue_median=32_000,
    revenue_optimistic=70_000,
    cogs_pct=35.0,
    rent_monthly_low=2_500,
    rent_monthly_mid=4_500,
    utilities_monthly=1_200,
    staff_solo_monthly=5_000,
    staff_1_monthly=4_000,
    staff_2_monthly=8_000,
    automation_monthly_savings=800,
    model_solo_description=(
        "Chef-owner cooks, handles delivery apps (DoorDash/Uber Eats/Grubhub). "
        "Ghost kitchen start eliminates front-of-house cost. "
        "Catering for Indian events (weddings, pujas) = $1K-8K/event."
    ),
    model_1staff_description=(
        "Owner cooks, 1 front-of-house / delivery coordinator. "
        "Lunch buffet ($14.99/person) drives 40-60 covers with minimal labor. "
        "Catering deposits fund cash flow."
    ),
    model_2staff_description=(
        "Full kitchen + front-of-house team. Owner as executive chef/manager. "
        "Private dining room rentals add $500-2,000/event. "
        "Franchise model viable with proven recipes."
    ),
    escalation_path=(
        "Ghost kitchen delivery → add dine-in → catering arm → "
        "meal kit subscription (Indian cooking kits ship nationwide at 60% margin) → "
        "second location or franchise."
    ),
)

_reg(
    "halal_restaurant",
    startup_home_based=5_000,
    startup_small=50_000,
    startup_full=130_000,
    revenue_conservative=10_000,
    revenue_median=28_000,
    revenue_optimistic=60_000,
    cogs_pct=38.0,
    rent_monthly_low=2_000,
    rent_monthly_mid=4_000,
    utilities_monthly=1_000,
    staff_solo_monthly=4_500,
    staff_1_monthly=3_800,
    staff_2_monthly=7_600,
    automation_monthly_savings=700,
    model_solo_description=(
        "Chef-owner. Halal certification is a trust moat in Muslim communities. "
        "Delivery-first via apps minimizes front-of-house cost. "
        "Community catering (Eid, Ramadan iftars) drives seasonal spikes."
    ),
    model_1staff_description=(
        "Owner + 1 server/cashier. Owner cooks, staff manages orders and customers. "
        "Combo meal pricing simplifies operations and boosts average ticket."
    ),
    model_2staff_description=(
        "2 staff + owner. Owner manages kitchen and quality control. "
        "Wholesale halal meal prep to offices, mosques, and schools adds stable B2B revenue."
    ),
    escalation_path=(
        "Restaurant → catering → meal prep subscription → wholesale to institutions → "
        "halal food distribution (supply other halal restaurants at 15-20% distributor margin)."
    ),
)

_reg(
    "restaurant",
    startup_home_based=10_000,
    startup_small=80_000,
    startup_full=250_000,
    revenue_conservative=20_000,
    revenue_median=55_000,
    revenue_optimistic=110_000,
    cogs_pct=38.0,
    rent_monthly_low=3_500,
    rent_monthly_mid=6_000,
    utilities_monthly=1_500,
    staff_solo_monthly=6_000,
    staff_1_monthly=4_500,
    staff_2_monthly=9_000,
    automation_monthly_savings=900,
    model_solo_description=(
        "Chef-owner, limited menu, high quality. 50-seat max. Reservations-only "
        "reduces staffing pressure. Strong online presence drives repeat business."
    ),
    model_1staff_description=(
        "Owner + 1 key employee (sous chef or FOH manager). Owner shifts from "
        "line work to management. Private dining and catering arm added."
    ),
    model_2staff_description=(
        "Full team: kitchen + FOH + manager. Owner as executive chef and business "
        "developer. Multiple revenue streams: dine-in, catering, delivery, merch."
    ),
    escalation_path=(
        "Single location → catering → ghost kitchen for delivery-only menu → "
        "second location or franchise → food brand / CPG product line."
    ),
)

_reg(
    "pizza_restaurant",
    startup_home_based=5_000,
    startup_small=40_000,
    startup_full=100_000,
    revenue_conservative=12_000,
    revenue_median=30_000,
    revenue_optimistic=65_000,
    cogs_pct=30.0,
    rent_monthly_low=2_000,
    rent_monthly_mid=3_500,
    utilities_monthly=1_000,
    staff_solo_monthly=4_500,
    staff_1_monthly=3_500,
    staff_2_monthly=7_000,
    automation_monthly_savings=1_000,
    model_solo_description=(
        "Owner makes dough, manages online orders. Delivery-only ghost kitchen "
        "eliminates dining room cost. Average ticket $25-35."
    ),
    model_1staff_description=(
        "Owner + 1 cook/driver. Online ordering system handles 80% of order taking. "
        "Slice delivery route optimized by routing app."
    ),
    model_2staff_description=(
        "Kitchen + delivery staff + owner as manager. Catering (office lunch boxes, "
        "party orders) adds $5K-15K/mo at 55% margin."
    ),
    escalation_path=(
        "Delivery ghost kitchen → add pickup window → add dine-in → "
        "catering school events and offices → slice wholesale to bodegas ($2/slice cost, "
        "$4/slice price = 50% margin, zero additional marketing)."
    ),
)

_reg(
    "real_estate",
    startup_home_based=2_000,
    startup_small=10_000,
    startup_full=30_000,
    revenue_conservative=5_000,
    revenue_median=15_000,
    revenue_optimistic=45_000,
    cogs_pct=30.0,
    rent_monthly_low=0,
    rent_monthly_mid=1_500,
    utilities_monthly=100,
    staff_solo_monthly=4_000,
    staff_1_monthly=0,
    staff_2_monthly=0,
    automation_monthly_savings=600,
    model_solo_description=(
        "Agent-owner works from home or shared office. Commission splits with broker: "
        "typically 70/30 to 90/10 once volume proves out. 2-4 closed deals/month target."
    ),
    model_1staff_description=(
        "Owner + buyer's agent (commission-only, no base salary risk). "
        "Owner takes listings, agent takes buyers. Doubles transaction volume."
    ),
    model_2staff_description=(
        "Small team brokerage. 3-5 agents generating $30K-100K gross commission/month. "
        "Owner takes 10-30% split from agents plus personal transactions."
    ),
    escalation_path=(
        "Individual agent → team lead → small brokerage → property management arm "
        "($100-150/unit/month, pure recurring) → own investment properties."
    ),
)

_reg(
    "accounting",
    startup_home_based=2_000,
    startup_small=10_000,
    startup_full=30_000,
    revenue_conservative=5_000,
    revenue_median=14_000,
    revenue_optimistic=35_000,
    cogs_pct=10.0,
    rent_monthly_low=500,
    rent_monthly_mid=1_500,
    utilities_monthly=100,
    staff_solo_monthly=5_000,
    staff_1_monthly=4_000,
    staff_2_monthly=8_000,
    automation_monthly_savings=800,
    model_solo_description=(
        "CPA-owner works from home. Monthly bookkeeping retainers ($300-800/client/month) "
        "provide predictable revenue. Tax season spikes to 3× normal monthly."
    ),
    model_1staff_description=(
        "Owner + junior accountant/bookkeeper. Owner handles tax strategy and advisory, "
        "staff handles data entry and basic bookkeeping. Scales to 60-80 clients."
    ),
    model_2staff_description=(
        "Small firm: 2 accountants + owner as managing partner. CFO-as-a-service for "
        "SMBs at $2K-5K/month is the premium tier. B2B recurring revenue is the moat."
    ),
    escalation_path=(
        "Bookkeeping ($300/mo) → tax prep ($500-2,000/year) → advisory retainer "
        "($2,000-5,000/mo) → CFO-as-a-Service → fractional CFO for funded startups "
        "($5,000-15,000/mo, fewer clients, much higher value)."
    ),
)

_reg(
    "insurance",
    startup_home_based=2_000,
    startup_small=10_000,
    startup_full=30_000,
    revenue_conservative=4_000,
    revenue_median=12_000,
    revenue_optimistic=30_000,
    cogs_pct=20.0,
    rent_monthly_low=500,
    rent_monthly_mid=1_500,
    utilities_monthly=100,
    staff_solo_monthly=4_000,
    staff_1_monthly=3_500,
    staff_2_monthly=7_000,
    automation_monthly_savings=500,
    model_solo_description=(
        "Licensed agent earns 10-20% commission on premiums. Auto, home, life = recurring "
        "renewals. Book of business builds compounding passive income over years."
    ),
    model_1staff_description=(
        "Owner + 1 licensed agent (commission-split or salary). Owner focuses on "
        "commercial accounts (higher premium = higher commission)."
    ),
    model_2staff_description=(
        "Agency with 2-3 agents + owner. Owner earns override on agent production. "
        "Commercial lines (workers comp, general liability) = 3-5× premium of personal lines."
    ),
    escalation_path=(
        "Personal lines → commercial lines → specialty lines (cyber, E&O) → "
        "captive agency → independent MGA (wholesaler) with override on all bound premium. "
        "Renewals compound: year 5 book generates $8K-15K/mo with no new sales."
    ),
)

_reg(
    "yoga_studio",
    startup_home_based=3_000,
    startup_small=20_000,
    startup_full=50_000,
    revenue_conservative=4_000,
    revenue_median=10_000,
    revenue_optimistic=22_000,
    cogs_pct=10.0,
    rent_monthly_low=1_000,
    rent_monthly_mid=2_000,
    utilities_monthly=300,
    staff_solo_monthly=3_500,
    staff_1_monthly=3_000,
    staff_2_monthly=6_000,
    automation_monthly_savings=400,
    model_solo_description=(
        "Teacher-owner leads all classes. Memberships ($80-150/mo) build recurring base. "
        "Online classes extend reach beyond local zip code with zero marginal cost."
    ),
    model_1staff_description=(
        "Owner + 1 sub-instructor (often revenue-share at $30-50/class). "
        "Owner focuses on premium workshops and teacher trainings ($1,500-3,000/student)."
    ),
    model_2staff_description=(
        "2 instructors + owner as studio director. Owner monetizes expertise: "
        "online courses, teacher training programs (200-hr YTT at $2,500-4,000/student)."
    ),
    escalation_path=(
        "In-person classes → online membership ($29-79/mo, no rent) → "
        "yoga teacher training ($2,500-4,000/student, 20 students = $50K) → "
        "wellness retreat weekends → licensing curriculum to other studios."
    ),
)

_reg(
    "gym",
    startup_home_based=5_000,
    startup_small=50_000,
    startup_full=200_000,
    revenue_conservative=8_000,
    revenue_median=22_000,
    revenue_optimistic=55_000,
    cogs_pct=15.0,
    rent_monthly_low=3_000,
    rent_monthly_mid=6_000,
    utilities_monthly=1_500,
    staff_solo_monthly=4_500,
    staff_1_monthly=4_000,
    staff_2_monthly=8_000,
    automation_monthly_savings=600,
    model_solo_description=(
        "Owner-trainer: personal training + group classes + gym membership access. "
        "Membership recurring revenue covers fixed costs; training is profit."
    ),
    model_1staff_description=(
        "Owner + 1 trainer. Owner handles business ops and premium clients. "
        "Staff covers group classes. Target: 150-200 members at $50-80/mo."
    ),
    model_2staff_description=(
        "2 trainers + owner as business lead. Add nutrition coaching, supplement sales "
        "(60-70% margin), and online programs for non-local revenue."
    ),
    escalation_path=(
        "Personal training → gym memberships → group fitness → "
        "online coaching ($100-300/mo recurring, zero rent) → "
        "supplement line → franchise or licensing your system."
    ),
)

_reg(
    "auto_repair",
    startup_home_based=10_000,
    startup_small=50_000,
    startup_full=200_000,
    revenue_conservative=8_000,
    revenue_median=22_000,
    revenue_optimistic=55_000,
    cogs_pct=35.0,
    rent_monthly_low=2_000,
    rent_monthly_mid=3_500,
    utilities_monthly=500,
    staff_solo_monthly=5_000,
    staff_1_monthly=5_500,
    staff_2_monthly=11_000,
    automation_monthly_savings=400,
    model_solo_description=(
        "Mobile mechanic-owner does oil changes, brakes, diagnostics on-site. "
        "No shop rent. $80-150/hr labor rate. Repeat customers = high LTV."
    ),
    model_1staff_description=(
        "Shop owner + 1 mechanic. Owner handles diagnostics and customer interaction "
        "(highest value). Staff handles routine maintenance. Target: 8-12 cars/day."
    ),
    model_2staff_description=(
        "2 mechanics + service advisor (owner). Owner upsells maintenance packages "
        "and manages parts inventory. Fleet accounts ($500-5K/month recurring) "
        "are the key margin lever."
    ),
    escalation_path=(
        "Mobile mechanic → fixed shop → fleet maintenance contracts → "
        "specialty (EV repair, which has lower competition and higher hourly rates) → "
        "auto repair franchise or specialty brand."
    ),
)

_reg(
    "florist",
    startup_home_based=3_000,
    startup_small=20_000,
    startup_full=50_000,
    revenue_conservative=4_000,
    revenue_median=11_000,
    revenue_optimistic=25_000,
    cogs_pct=40.0,
    rent_monthly_low=1_200,
    rent_monthly_mid=2_000,
    utilities_monthly=400,
    staff_solo_monthly=3_500,
    staff_1_monthly=2_800,
    staff_2_monthly=5_600,
    automation_monthly_savings=300,
    model_solo_description=(
        "Owner-florist: daily arrangements, wedding consultation, event flowers. "
        "Subscription boxes ($60-150/mo per customer) provide recurring revenue."
    ),
    model_1staff_description=(
        "Owner + 1 assistant. Owner handles design and client relationships; "
        "staff handles assembly, delivery coordination, shop front."
    ),
    model_2staff_description=(
        "2 staff + owner as lead designer. Owner focuses on weddings and corporate "
        "accounts ($500-5K/event). Corporate weekly arrangements = reliable B2B revenue."
    ),
    escalation_path=(
        "Retail walk-ins → subscription arrangements → wedding/event specialty → "
        "corporate weekly accounts ($200-500/account/week) → "
        "dried flower and preserved arrangements (no perishability risk, 65% margin)."
    ),
)

_reg(
    "bookstore",
    startup_home_based=5_000,
    startup_small=30_000,
    startup_full=100_000,
    revenue_conservative=4_000,
    revenue_median=10_000,
    revenue_optimistic=22_000,
    cogs_pct=55.0,
    rent_monthly_low=1_500,
    rent_monthly_mid=2_500,
    utilities_monthly=300,
    staff_solo_monthly=3_500,
    staff_1_monthly=2_800,
    staff_2_monthly=5_600,
    automation_monthly_savings=300,
    model_solo_description=(
        "Curated indie bookstore. Used books (buy at $1-2, sell at $5-8) "
        "carry 80% margin and offset new book thin margins. "
        "Events (author readings, book clubs) drive foot traffic."
    ),
    model_1staff_description=(
        "Owner + 1 staff. Owner handles curation, events, social. "
        "Staff handles customers and daily ops. Events become $500-2K revenue nights."
    ),
    model_2staff_description=(
        "2 staff + owner as curator/community builder. Add: café corner, "
        "local art sales, subscription boxes ($35-75/mo). Diversification is survival."
      ),
    escalation_path=(
        "New books (thin margin) → used books (high margin) → "
        "events + memberships → gift/stationery (40-60% margin) → "
        "subscription book box (no rent, ships nationwide) → "
        "online used book marketplace (no physical constraints)."
    ),
)

_reg(
    "gift_shop",
    startup_home_based=5_000,
    startup_small=30_000,
    startup_full=80_000,
    revenue_conservative=5_000,
    revenue_median=13_000,
    revenue_optimistic=30_000,
    cogs_pct=50.0,
    rent_monthly_low=1_500,
    rent_monthly_mid=2_500,
    utilities_monthly=200,
    staff_solo_monthly=3_500,
    staff_1_monthly=2_800,
    staff_2_monthly=5_600,
    automation_monthly_savings=400,
    model_solo_description=(
        "Owner curates, buys, and sells. Etsy/Shopify extends to national market. "
        "Local artisan consignment (owner keeps 30-40%) reduces buying risk."
    ),
    model_1staff_description=(
        "Owner + part-time staff for peak hours. Owner handles buying and social media. "
        "Staff manages counter, wrapping, inventory."
    ),
    model_2staff_description=(
        "2 staff + owner as buyer/brand. Corporate gifting arm "
        "($500-5K/order, custom branding) is the high-margin lever. B2B sales."
    ),
    escalation_path=(
        "Retail → online store → corporate gifting → "
        "private label items (branded mugs, totes at 65% margin) → "
        "subscription gift box ($35-75/month recurring, ships nationwide)."
    ),
)

_reg(
    "electronics_store",
    startup_home_based=10_000,
    startup_small=50_000,
    startup_full=200_000,
    revenue_conservative=15_000,
    revenue_median=38_000,
    revenue_optimistic=80_000,
    cogs_pct=70.0,
    rent_monthly_low=2_000,
    rent_monthly_mid=3_500,
    utilities_monthly=400,
    staff_solo_monthly=4_500,
    staff_1_monthly=3_500,
    staff_2_monthly=7_000,
    automation_monthly_savings=600,
    model_solo_description=(
        "Owner specializes in repair + refurbished sales. Repair margin is 60-80% "
        "vs 15-25% on new retail. Used/refurb sales carry 30-40% margin."
    ),
    model_1staff_description=(
        "Owner + 1 repair tech. Owner handles sales and customer intake; "
        "tech handles repairs. Trade-in program builds used inventory at zero cost."
    ),
    model_2staff_description=(
        "2 techs + owner as manager/buyer. B2B repair contracts with local "
        "schools, offices, and clinics provide $2K-10K/month recurring revenue."
    ),
    escalation_path=(
        "New retail (7% margin) → repair services (70% margin) → "
        "refurbished sales → B2B repair contracts → "
        "device buyback/resale marketplace → e-waste recycling (EPA certified = premium)."
    ),
)


# ── public API ────────────────────────────────────────────────────────────────

def get_revenue_model(niche: str, demographics: dict | None = None) -> RevenueModel:
    """Return a RevenueModel for the given niche. Falls back to a generic model."""
    if niche in _MODELS:
        return _MODELS[niche]

    # Generic fallback — rough defaults for uncatalogued niches
    rev = 12_000
    cogs = 40.0
    rent_mid = 2_500
    util = 400
    staff1 = 3_200
    startup_small = 40_000
    cogs_amt = rev * cogs / 100
    gross = round(100.0 - cogs, 1)
    net_s = rev - cogs_amt - rent_mid - util
    net_1 = net_s - staff1
    net_s_pct = round(net_s / rev * 100, 1)
    net_1_pct = round(net_1 / rev * 100, 1)

    return RevenueModel(
        niche=niche,
        startup_home_based=10_000,
        startup_small=startup_small,
        startup_full=100_000,
        revenue_conservative=6_000,
        revenue_median=rev,
        revenue_optimistic=25_000,
        cogs_pct=cogs,
        rent_monthly_low=1_500,
        rent_monthly_mid=rent_mid,
        utilities_monthly=util,
        staff_solo_monthly=3_500,
        staff_1_monthly=staff1,
        staff_2_monthly=6_400,
        gross_margin_pct=gross,
        net_margin_solo_pct=net_s_pct,
        net_margin_1staff_pct=net_1_pct,
        payback_solo_months=_payback(startup_small, net_s),
        payback_1staff_months=_payback(startup_small, net_1),
        automation_monthly_savings=400,
        model_solo_description="Owner-operator manages all functions. Online booking and payment reduce admin overhead.",
        model_1staff_description="Owner + 1 employee. Owner shifts to management and sales, staff handles operations.",
        model_2staff_description="2 employees + owner as manager. Automation and SOPs enable part-time owner involvement.",
        margin_tier=_tier(net_s_pct),
        escalation_path="Start lean → systemize with SOPs and automation → add staff when revenue consistently exceeds costs → add B2B or recurring revenue streams.",
    )


def format_revenue_model(model: RevenueModel) -> str:
    """Return a human-readable P&L breakdown."""
    lines = [
        f"{'━'*60}",
        f"REVENUE MODEL — {model.niche.replace('_', ' ').upper()}",
        f"{'━'*60}",
        "",
        "STARTUP CAPITAL",
        f"  Home/Mobile start : ${model.startup_home_based:>10,}",
        f"  Small footprint   : ${model.startup_small:>10,}",
        f"  Full storefront   : ${model.startup_full:>10,}",
        "",
        "MONTHLY REVENUE RANGE",
        f"  Conservative : ${model.revenue_conservative:>10,}/mo",
        f"  Median       : ${model.revenue_median:>10,}/mo",
        f"  Optimistic   : ${model.revenue_optimistic:>10,}/mo",
        "",
        "COST STRUCTURE (at median revenue)",
        f"  COGS / direct costs : {model.cogs_pct:.0f}%  (${int(model.revenue_median * model.cogs_pct / 100):,}/mo)",
        f"  Rent (mid estimate) : ${model.rent_monthly_mid:,}/mo",
        f"  Utilities           : ${model.utilities_monthly:,}/mo",
        f"  Gross margin        : {model.gross_margin_pct:.1f}%",
        "",
        "NET MARGIN",
        f"  Solo (owner-operator)  : {model.net_margin_solo_pct:.1f}%  = ${int(model.revenue_median * model.net_margin_solo_pct / 100):,}/mo",
        f"  With 1 employee        : {model.net_margin_1staff_pct:.1f}%  = ${int(model.revenue_median * model.net_margin_1staff_pct / 100):,}/mo",
        f"  Margin tier            : {model.margin_tier.upper()}",
        "",
        "PAYBACK (on small-footprint startup cost)",
        f"  Solo    : {model.payback_solo_months} months",
        f"  1 staff : {'N/A' if model.payback_1staff_months >= 999 else str(model.payback_1staff_months) + ' months'}",
        "",
        f"AUTOMATION SAVINGS : ~${model.automation_monthly_savings:,}/mo",
        "",
        "BUSINESS MODELS",
        f"  Solo     : {model.model_solo_description}",
        f"  1 staff  : {model.model_1staff_description}",
        f"  2 staff  : {model.model_2staff_description}",
        "",
        "ESCALATION PATH",
        f"  {model.escalation_path}",
        "",
    ]
    return "\n".join(lines)


def list_niches() -> list[str]:
    """Return sorted list of all niche keys with registered revenue models."""
    return sorted(_MODELS.keys())


def list_niches() -> list[str]:
    """Return all niche keys that have a defined revenue model."""
    return sorted(_MODELS.keys())
