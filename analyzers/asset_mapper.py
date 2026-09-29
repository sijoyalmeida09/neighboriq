"""asset_mapper.py — Filter and re-rank NeighborIQ opportunities by operator assets.

Given what a person already has (capital, space, skills, licenses), produces
a ranked list of business opportunities sorted by feasibility + opportunity.
"""
from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "AssetProfile",
    "FeasibilityResult",
    "build_asset_profile",
    "parse_asset_profile_from_dict",
    "filter_by_assets",
    "format_feasibility_results",
]

# ---------------------------------------------------------------------------
# Capital tiers per niche (home_based, small, full) — all USD
# home_based=0 means not viable as home-based
# ---------------------------------------------------------------------------
_CAPITAL_TIERS: dict[str, tuple[int, int, int]] = {
    "barbershop":         (5_000,   30_000,  60_000),
    "hair_salon":         (5_000,   60_000, 120_000),
    "nail_salon":         (3_000,   50_000, 100_000),
    "laundromat":         (0,      200_000, 500_000),
    "dry_cleaning":       (0,       80_000, 200_000),
    "check_cashing":      (0,       80_000, 150_000),
    "tutoring_center":    (500,     30_000,  80_000),
    "real_estate":        (5_000,   30_000,  50_000),
    "convenience_store":  (0,      100_000, 250_000),
    "grocery_store":      (0,      500_000,1_000_000),
    "coffee_shop":        (2_000,   80_000, 200_000),
    "cafe":               (2_000,   60_000, 150_000),
    "yoga_studio":        (1_000,   50_000, 100_000),
    "gym":                (0,      200_000, 500_000),
    "accounting":         (1_000,   30_000,  80_000),
    "insurance":          (1_000,   30_000,  60_000),
    "law_office":         (2_000,   50_000, 150_000),
    "auto_repair":        (0,      200_000, 400_000),
    "daycare":            (0,      150_000, 300_000),
    "dentist":            (0,      500_000,1_000_000),
    "doctor":             (0,      300_000, 800_000),
    "pharmacy":           (0,    1_000_000,2_000_000),
    "liquor_store":       (0,      150_000, 350_000),
    "florist":            (2_000,   50_000, 100_000),
    "gift_shop":          (1_000,   80_000, 150_000),
    "bakery":             (3_000,   70_000, 150_000),
    "pizza_restaurant":   (0,      100_000, 250_000),
    "restaurant":         (0,      250_000, 600_000),
    "halal_restaurant":   (0,      130_000, 300_000),
    "indian_restaurant":  (0,      150_000, 350_000),
    "chinese_restaurant": (0,      120_000, 280_000),
    "mexican_restaurant": (0,      130_000, 280_000),
    "sushi_restaurant":   (0,      180_000, 400_000),
    "thai_restaurant":    (0,      140_000, 300_000),
    "ethiopian_restaurant":(0,     120_000, 280_000),
    "vietnamese_restaurant":(0,    110_000, 260_000),
    "mediterranean_restaurant":(0, 160_000, 350_000),
    "bar":                (0,      200_000, 500_000),
    "bookstore":          (2_000,  100_000, 200_000),
    "shoe_store":         (0,      100_000, 200_000),
    "clothing_store":     (0,      150_000, 300_000),
    "electronics_store":  (0,      200_000, 400_000),
    "furniture_store":    (0,      300_000, 600_000),
    "jewelry_store":      (0,      150_000, 400_000),
    "pet_store":          (0,      200_000, 400_000),
    "hardware_store":     (0,      500_000,1_000_000),
    "gas_station":        (0,    1_000_000,3_000_000),
}

# Estimated monthly rent/overhead per tier (small, full) — USD
_MONTHLY_OVERHEAD: dict[str, tuple[int, int]] = {
    "barbershop":         (1_500,  3_500),
    "hair_salon":         (2_000,  5_000),
    "nail_salon":         (1_500,  4_000),
    "laundromat":         (3_000,  8_000),
    "check_cashing":      (2_500,  6_000),
    "tutoring_center":    (1_000,  3_000),
    "real_estate":        (800,    2_500),
    "convenience_store":  (3_000,  8_000),
    "coffee_shop":        (3_000,  7_000),
    "yoga_studio":        (2_000,  5_000),
    "accounting":         (500,    2_000),
    "auto_repair":        (3_000,  8_000),
    "daycare":            (3_500,  9_000),
    "restaurant":         (5_000, 15_000),
    "bar":                (5_000, 12_000),
}
_DEFAULT_OVERHEAD = (2_000, 6_000)

# ---------------------------------------------------------------------------
# Skill requirements per niche
# ---------------------------------------------------------------------------
_SKILL_REQUIREMENTS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    # (required, helpful)
    "barbershop":           (("hair_cutting", "barbering"),       ("customer_service",)),
    "hair_salon":           (("hair_cutting", "cosmetology"),     ("customer_service",)),
    "nail_salon":           (("cosmetology", "nail_tech"),        ()),
    "laundromat":           ((),                                   ()),
    "dry_cleaning":         ((),                                   ("chemistry",)),
    "check_cashing":        ((),                                   ("finance", "accounting")),
    "tutoring_center":      (("teaching", "education"),           ("math", "english")),
    "real_estate":          (("real_estate",),                    ("sales",)),
    "convenience_store":    ((),                                   ("retail",)),
    "grocery_store":        ((),                                   ("retail",)),
    "coffee_shop":          (("barista",),                        ("cooking", "customer_service")),
    "cafe":                 (("barista",),                        ("cooking",)),
    "yoga_studio":          (("yoga",),                           ("fitness",)),
    "gym":                  ((),                                   ("fitness",)),
    "accounting":           (("accounting", "finance"),           ("cpa",)),
    "insurance":            (("insurance",),                      ("finance", "sales")),
    "law_office":           (("law", "legal"),                    ()),
    "auto_repair":          (("mechanics",),                      ("auto_repair",)),
    "daycare":              (("childcare", "teaching"),           ("education",)),
    "dentist":              (("dentistry",),                      ()),
    "doctor":               (("medicine", "healthcare"),          ()),
    "florist":              (("floristry",),                      ("design",)),
    "bakery":               (("baking", "cooking"),               ("food_handler",)),
    "pizza_restaurant":     (("cooking",),                        ("food_handler",)),
    "restaurant":           (("cooking",),                        ("food_handler", "management")),
    "halal_restaurant":     (("cooking",),                        ("food_handler",)),
    "indian_restaurant":    (("cooking",),                        ("food_handler",)),
    "chinese_restaurant":   (("cooking",),                        ("food_handler",)),
    "mexican_restaurant":   (("cooking",),                        ("food_handler",)),
    "sushi_restaurant":     (("cooking", "sushi"),                ("food_handler",)),
    "thai_restaurant":      (("cooking",),                        ("food_handler",)),
    "ethiopian_restaurant": (("cooking",),                        ("food_handler",)),
    "vietnamese_restaurant":(("cooking",),                        ("food_handler",)),
    "mediterranean_restaurant":(("cooking",),                     ("food_handler",)),
    "bar":                  (("bartending",),                     ("customer_service",)),
}
_DEFAULT_SKILLS: tuple[tuple[str, ...], tuple[str, ...]] = ((), ())

# Niches that are high-ops (not suitable for < 25 hrs/week)
_HIGH_OPS_NICHES = {
    "restaurant", "halal_restaurant", "indian_restaurant", "chinese_restaurant",
    "mexican_restaurant", "sushi_restaurant", "thai_restaurant", "ethiopian_restaurant",
    "vietnamese_restaurant", "mediterranean_restaurant", "pizza_restaurant",
    "bar", "daycare", "convenience_store", "grocery_store", "laundromat",
    "gas_station", "pharmacy",
}

# ---------------------------------------------------------------------------
# Low → high margin escalation paths
# ---------------------------------------------------------------------------
_ESCALATION_PATHS: dict[str, str] = {
    "convenience_store": (
        "Start: grab-and-go food + ATM (30% margin) → "
        "Add lottery terminal (+10% commission) → "
        "Add tobacco/alcohol (higher margin) → "
        "Add money orders/Western Union (fee income) → "
        "Add micro-lending/check cashing (highest margin, ~40%)"
    ),
    "barbershop": (
        "Start: basic cuts at $20 (60% margin) → "
        "Add beard/fade specialty at $30-35 → "
        "Add hair products retail (60% margin) → "
        "Add membership plan ($80/mo unlimited, locked revenue) → "
        "Add 1 chair rental to another barber ($400/mo fully passive)"
    ),
    "hair_salon": (
        "Start: basic cuts/color at $40 → "
        "Add premium treatments (keratin, extensions) at $200+ → "
        "Add retail product sales (60% margin) → "
        "Add booth rentals ($600-900/mo passive per chair) → "
        "Add bridal/event packages at 3× regular pricing"
    ),
    "nail_salon": (
        "Start: basic manicure/pedicure ($25-40) → "
        "Add nail art and gel sets ($60-80) → "
        "Add lash extensions upsell ($80-120) → "
        "Add waxing services → "
        "Add spa packages (2-3× margin on bundled services)"
    ),
    "tutoring_center": (
        "Start: 1-on-1 sessions at $30/hr (high margin, low overhead) → "
        "Add group classes at $15/student (same time, 3× revenue) → "
        "Add test prep (SAT/ACT) at $60/hr premium → "
        "Add online async courses ($200-500 one-time, zero marginal cost) → "
        "License curriculum to other tutors (pure royalty income)"
    ),
    "coffee_shop": (
        "Start: drip coffee + pastries (65% margin) → "
        "Add specialty drinks (lattes, cold brew) at $6-8 (70%+ margin) → "
        "Add retail beans/merch (75% margin) → "
        "Add catering/office delivery (higher volume, lower overhead) → "
        "Add loyalty subscription ($30/mo, predictable MRR)"
    ),
    "laundromat": (
        "Start: coin-op washers/dryers (passive, 40% margin) → "
        "Add wash-dry-fold service ($1.50/lb, 60% margin) → "
        "Add dry cleaning drop-off (referral fee, zero capital) → "
        "Add commercial laundry contracts (hotels, restaurants) → "
        "Add vending machines (snacks/detergent, 50%+ margin)"
    ),
    "check_cashing": (
        "Start: check cashing at 2-3% fee (pure margin) → "
        "Add money orders ($1-3 fee per, zero risk) → "
        "Add Western Union/remittance (per-transaction fee) → "
        "Add prepaid debit cards (activation + reload fees) → "
        "Add small personal loans if licensed (highest margin, highest risk)"
    ),
    "real_estate": (
        "Start: buyer's agent (2.5-3% commission, low capital) → "
        "Add property management ($100-200/mo per unit, recurring) → "
        "Add rental arbitrage (sublease furnished units at 2×) → "
        "Add wholesaling (assign contracts, $5-20K fee per deal) → "
        "Add fix-and-flip once capital accumulates (30-50% ROI per deal)"
    ),
    "accounting": (
        "Start: bookkeeping at $50-75/hr (80% margin) → "
        "Add monthly retainer packages ($500-1500/mo recurring) → "
        "Add tax preparation at $300-800/return (seasonal spike) → "
        "Add CFO-as-a-service for SMBs ($2,000-5,000/mo) → "
        "Add payroll processing (software leverage, near-zero marginal cost)"
    ),
    "yoga_studio": (
        "Start: park/outdoor classes (near-zero overhead, $15/class) → "
        "Add drop-in studio classes ($18-25/class) → "
        "Add unlimited monthly memberships ($80-120/mo MRR) → "
        "Add 200-hr teacher training ($2,000-3,000/student, 80% margin) → "
        "Add online on-demand library ($20/mo, zero marginal cost per subscriber)"
    ),
    "bakery": (
        "Start: home-based custom orders (cakes, events) at 60%+ margin → "
        "Add farmers market booth (volume + visibility) → "
        "Add wholesale to coffee shops (consistent orders, lower margin but reliable) → "
        "Add subscription boxes ($60-100/mo, predictable) → "
        "Open storefront only when wholesale revenue covers rent"
    ),
    "auto_repair": (
        "Start: mobile oil changes/tire rotation ($80-150/visit, low overhead) → "
        "Add pre-purchase inspections ($100, pure labor) → "
        "Add small repairs (brakes, batteries) → "
        "Open bay shop for full diagnostics → "
        "Add fleet maintenance contracts with local businesses (recurring, negotiated rates)"
    ),
    "florist": (
        "Start: event/wedding flowers from home (60%+ margin, no storefront) → "
        "Add weekly office subscriptions ($150-300/mo per client, recurring) → "
        "Add online orders + local delivery ($12-15 delivery fee) → "
        "Add grief/sympathy arrangements (year-round demand) → "
        "Add DIY floral workshops ($75-100/person, 80% margin)"
    ),
}
_DEFAULT_ESCALATION = (
    "Start with lowest-capital entry point to validate demand → "
    "Reinvest first 3 months of profit into automation/equipment → "
    "Add premium tier service at 2× price → "
    "Build recurring revenue layer (subscriptions, retainers, contracts) → "
    "Hire 1 staff member to handle operations while you focus on sales/growth"
)

# ---------------------------------------------------------------------------
# First 30 days per niche + entry tier
# ---------------------------------------------------------------------------
_FIRST_30_DAYS: dict[str, dict[str, str]] = {
    "barbershop": {
        "home_based": (
            "Week 1: Get mobile barber license + buy $2K kit (clippers, cape, chair). "
            "Week 2: Text 50 contacts, offer $15 introductory cuts at-home. "
            "Week 3: Set up Square reader + Calendly booking link. "
            "Week 4: Post 4 transformation videos on Instagram/TikTok."
        ),
        "small": (
            "Week 1: Sign lease, order 2 barber chairs + mirrors ($8K). "
            "Week 2: Hire 1 barber on booth-rent model ($400/mo). "
            "Week 3: Grand opening — free fades for first 20 customers. "
            "Week 4: Set up Google Business profile + ask for 10 reviews."
        ),
        "full": (
            "Week 1-2: Full buildout + 3 chairs. "
            "Week 3: Hire 2 experienced barbers + 1 receptionist. "
            "Week 4: Launch Instagram + run $200 geo-targeted ad to 3-mile radius."
        ),
    },
    "tutoring_center": {
        "home_based": (
            "Week 1: Post on Nextdoor, local Facebook groups, and school bulletin boards. "
            "Week 2: Set up Calendly + Venmo/Zelle + a simple rate card ($30-50/hr). "
            "Week 3: Teach 5 trial sessions at $20 introductory rate. "
            "Week 4: Ask each student family for 2 referrals."
        ),
        "small": (
            "Week 1: Set up 3-room tutoring center + whiteboard/desks. "
            "Week 2: Partner with 2 local schools to hand out flyers. "
            "Week 3: Run free diagnostic assessment weekend (builds list). "
            "Week 4: Launch group SAT/ACT prep class at $15/session."
        ),
        "full": (
            "Week 1-2: Full center open, hire 3 subject tutors at $20/hr. "
            "Week 3: Contact 10 school counselors directly. "
            "Week 4: Launch summer intensive programs + online booking."
        ),
    },
    "real_estate": {
        "home_based": (
            "Week 1: Complete pre-licensing course online ($150-300). "
            "Week 2: Choose a brokerage to hang license under (no desk fee options exist). "
            "Week 3: Tell every contact you are now a licensed agent. "
            "Week 4: Show your first 5 listings and aim for 1 under-contract."
        ),
        "small": (
            "Week 1: License + join local MLS board ($500). "
            "Week 2: Set up small office + hire 1 buyer's agent on commission-only. "
            "Week 3: Door-knock 200 homes in target neighborhood. "
            "Week 4: Run $100 Facebook lead-gen ad to renters in your zip."
        ),
    },
    "accounting": {
        "home_based": (
            "Week 1: Set up LLC + get EIN + open business bank account. "
            "Week 2: Create a simple one-page website + LinkedIn update. "
            "Week 3: Offer free 30-min bookkeeping review to 10 small businesses. "
            "Week 4: Convert 3 of those to $500/mo retainer clients."
        ),
        "small": (
            "Week 1: Rent small office, subscribe to QuickBooks Accountant + Drake Tax. "
            "Week 2: Hire 1 bookkeeper ($18/hr part-time). "
            "Week 3: Cold-call 50 local small businesses. "
            "Week 4: Send 'tax season offer' email to every contact."
        ),
    },
    "coffee_shop": {
        "home_based": (
            "Week 1: Get food handler permit + buy $500 espresso setup. "
            "Week 2: Book a farmers market booth ($50-100/day). "
            "Week 3: Sell for 3 weekends, track best sellers. "
            "Week 4: Add pre-orders via Instagram DM."
        ),
        "small": (
            "Week 1: Sign lease + order espresso machine + POS ($15K all-in). "
            "Week 2: Hire 1 experienced barista. "
            "Week 3: Soft open — invite neighborhood + offer free drink. "
            "Week 4: Set up Google Business + loyalty stamp card."
        ),
    },
    "yoga_studio": {
        "home_based": (
            "Week 1: Find a local park or community center to teach in. "
            "Week 2: Post flyers + Instagram — 'Free outdoor yoga this Saturday.' "
            "Week 3: Run 4 free classes, collect emails + feedback. "
            "Week 4: Launch $60/mo unlimited pass to your first 20 regulars."
        ),
        "small": (
            "Week 1: Sign studio lease + buy 20 mats + mirror + sound system. "
            "Week 2: Set up Mindbody or Vagaro scheduling software. "
            "Week 3: Host free community class, collect 50 emails. "
            "Week 4: Launch founding member deal: $80/mo for first 30 sign-ups."
        ),
    },
    "nail_salon": {
        "home_based": (
            "Week 1: Get cosmetology/nail tech license if not already held. "
            "Week 2: Set up home nail station ($1K supplies). "
            "Week 3: Offer $20 intro sets to 10 friends/family for photos. "
            "Week 4: Post before/after on Instagram, add booking link."
        ),
        "small": (
            "Week 1: Lease 400 sqft + buy 3 nail stations ($15K buildout). "
            "Week 2: Hire 1 licensed nail tech on commission (50%). "
            "Week 3: Offer $25 intro manicures opening week. "
            "Week 4: Google Business setup + ask every client for a review."
        ),
    },
    "laundromat": {
        "small": (
            "Week 1: Due diligence on existing laundromat for sale (faster than build). "
            "Week 2: Secure SBA loan pre-approval. "
            "Week 3: Hire 1 attendant for wash-dry-fold service. "
            "Week 4: Add vending machines + post pricing on Google."
        ),
        "full": (
            "Week 1-2: Equipment install (20 washers, 20 dryers). "
            "Week 3: Hire 2 attendants + set up app-based payment. "
            "Week 4: Launch commercial contracts pitch to 5 local hotels."
        ),
    },
    "florist": {
        "home_based": (
            "Week 1: Set up flower wholesale account (Sam's Club or local market). "
            "Week 2: Post 10 arrangement photos on Instagram. "
            "Week 3: Offer free consultation + bouquet for 5 upcoming events in your network. "
            "Week 4: Book 2 paid events ($300-600 each)."
        ),
        "small": (
            "Week 1: Lease 200 sqft storefront + refrigerated case ($3K). "
            "Week 2: Order opening week inventory ($2K wholesale). "
            "Week 3: Partner with 3 local event venues. "
            "Week 4: Launch weekly office subscription ($150/mo)."
        ),
    },
    "bakery": {
        "home_based": (
            "Week 1: Get cottage food license (most states allow $25-50 fee). "
            "Week 2: Post 5 product photos + launch Instagram page. "
            "Week 3: Take 10 custom cake orders at $80-150 each. "
            "Week 4: Book a farmers market booth for next month."
        ),
        "small": (
            "Week 1: Commercial kitchen rental ($300-600/mo shared kitchen). "
            "Week 2: List on Goldbelly + DoorDash + Instagram shop. "
            "Week 3: Wholesale pitch to 5 coffee shops. "
            "Week 4: Launch subscription box ($60/mo, 20 subscribers = $1,200 MRR)."
        ),
    },
}

_DEFAULT_30_DAYS = {
    "home_based": (
        "Week 1: Register business name + set up free Google Business profile. "
        "Week 2: Tell your entire network via WhatsApp/text. "
        "Week 3: Deliver service to 5 customers at introductory price. "
        "Week 4: Collect reviews + ask each for 2 referrals."
    ),
    "small": (
        "Week 1: Sign lease + order essential equipment. "
        "Week 2: Hire 1 part-time staff member. "
        "Week 3: Soft open with word-of-mouth only. "
        "Week 4: Google Business + first paid social ad ($100 test)."
    ),
    "full": (
        "Week 1-2: Full buildout + staffing. "
        "Week 3: Grand opening event + press outreach. "
        "Week 4: Launch loyalty program + geo-targeted advertising."
    ),
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AssetProfile:
    capital_usd: int = 50_000
    space_sqft: int = 0
    has_vehicle: bool = False
    skills: tuple[str, ...] = ()
    licenses: tuple[str, ...] = ()
    existing_customers: int = 0
    monthly_overhead_max: int = 5_000
    prefers_home_based: bool = False
    hours_per_week: int = 40


@dataclass(frozen=True)
class FeasibilityResult:
    niche: str
    opportunity_score: int
    feasibility_score: int
    combined_score: int
    capital_fit: str
    skill_match: float
    what_you_have: tuple[str, ...]
    what_you_need: tuple[str, ...]
    recommended_entry_tier: str
    first_30_days: str
    low_to_high_path: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_capital_tiers(niche: str) -> tuple[int, int, int]:
    return _CAPITAL_TIERS.get(niche, (0, 100_000, 250_000))


def _get_skill_reqs(niche: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return _SKILL_REQUIREMENTS.get(niche, _DEFAULT_SKILLS)


def _calc_skill_match(niche: str, skills: tuple[str, ...]) -> tuple[float, list[str], list[str]]:
    required, helpful = _get_skill_reqs(niche)
    skills_lower = {s.lower() for s in skills}
    have: list[str] = []
    need: list[str] = []

    for req in required:
        if req in skills_lower:
            have.append(req)
        else:
            need.append(req)

    for hlp in helpful:
        if hlp in skills_lower:
            have.append(hlp)

    if not required:
        match = 1.0
    else:
        match = len([r for r in required if r in skills_lower]) / len(required)

    return round(match, 2), have, need


def _recommend_entry_tier(
    niche: str,
    assets: AssetProfile,
) -> str:
    home_cap, small_cap, _ = _get_capital_tiers(niche)
    if home_cap > 0 and assets.capital_usd >= home_cap and assets.prefers_home_based:
        return "home_based"
    if home_cap > 0 and assets.capital_usd >= home_cap and assets.capital_usd < small_cap:
        return "home_based"
    if assets.capital_usd >= small_cap:
        return "small" if assets.capital_usd < small_cap * 2 else "full"
    if home_cap > 0 and assets.capital_usd >= home_cap:
        return "home_based"
    return "home_based" if home_cap > 0 else "small"


def _capital_fit_label(capital: int, small_cap: int) -> str:
    if small_cap == 0:
        return "perfect"
    if capital >= small_cap:
        return "perfect"
    if capital >= small_cap * 0.5:
        return "tight"
    if capital >= small_cap * 0.25:
        return "stretch"
    return "impossible"


def _score_feasibility(
    niche: str,
    assets: AssetProfile,
) -> tuple[int, str, float, list[str], list[str]]:
    home_cap, small_cap, _ = _get_capital_tiers(niche)
    overhead_small, overhead_full = _MONTHLY_OVERHEAD.get(niche, _DEFAULT_OVERHEAD)

    # Capital scoring (0-40 pts)
    if home_cap > 0 and assets.capital_usd >= home_cap:
        capital_pts = 40
    elif small_cap > 0 and assets.capital_usd >= small_cap:
        capital_pts = 35
    elif small_cap > 0 and assets.capital_usd >= small_cap * 0.5:
        capital_pts = 20
    elif small_cap > 0 and assets.capital_usd >= small_cap * 0.25:
        capital_pts = 8
    else:
        capital_pts = 0

    cap_fit = _capital_fit_label(assets.capital_usd, home_cap if home_cap > 0 else small_cap)

    # Skill scoring (0-30 pts)
    skill_match, have, need = _calc_skill_match(niche, assets.skills)
    skill_pts = round(skill_match * 30)

    # Home-based preference scoring (0-10 pts)
    home_pts = 0
    if assets.prefers_home_based:
        if home_cap > 0:
            home_pts = 10
        else:
            home_pts = -10  # penalty for storefront-only niche

    # Hours scoring (0-10 pts)
    hours_pts = 0
    if assets.hours_per_week < 25 and niche in _HIGH_OPS_NICHES:
        hours_pts = -15
    elif assets.hours_per_week >= 40:
        hours_pts = 10
    else:
        hours_pts = 5

    # Overhead alignment (0-10 pts)
    overhead_pts = 0
    if assets.monthly_overhead_max >= overhead_full:
        overhead_pts = 10
    elif assets.monthly_overhead_max >= overhead_small:
        overhead_pts = 7
    elif assets.monthly_overhead_max >= overhead_small * 0.5:
        overhead_pts = 3
    else:
        overhead_pts = 0

    # Vehicle bonus for mobile niches
    vehicle_pts = 0
    mobile_niches = {"auto_repair", "florist", "barbershop"}
    if assets.has_vehicle and niche in mobile_niches:
        vehicle_pts = 5

    # Existing customers bonus
    cust_pts = min(5, assets.existing_customers // 20)

    total = capital_pts + skill_pts + home_pts + hours_pts + overhead_pts + vehicle_pts + cust_pts
    total = int(min(100, max(0, total)))

    return total, cap_fit, skill_match, have, need


def _get_first_30_days(niche: str, tier: str) -> str:
    niche_plans = _FIRST_30_DAYS.get(niche, {})
    if tier in niche_plans:
        return niche_plans[tier]
    # fallback: try adjacent tier
    for t in ("home_based", "small", "full"):
        if t in niche_plans:
            return niche_plans[t]
    return _DEFAULT_30_DAYS.get(tier, _DEFAULT_30_DAYS["home_based"])


def _get_escalation(niche: str) -> str:
    return _ESCALATION_PATHS.get(niche, _DEFAULT_ESCALATION)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_asset_profile(**kwargs: object) -> AssetProfile:
    """Build an AssetProfile with sensible defaults for any missing fields."""
    skills = kwargs.get("skills", ())
    if isinstance(skills, list):
        skills = tuple(skills)
    licenses = kwargs.get("licenses", ())
    if isinstance(licenses, list):
        licenses = tuple(licenses)
    return AssetProfile(
        capital_usd=int(kwargs.get("capital_usd", 50_000)),
        space_sqft=int(kwargs.get("space_sqft", 0)),
        has_vehicle=bool(kwargs.get("has_vehicle", False)),
        skills=tuple(s.lower() for s in skills),
        licenses=tuple(lic.lower() for lic in licenses),
        existing_customers=int(kwargs.get("existing_customers", 0)),
        monthly_overhead_max=int(kwargs.get("monthly_overhead_max", 5_000)),
        prefers_home_based=bool(kwargs.get("prefers_home_based", False)),
        hours_per_week=int(kwargs.get("hours_per_week", 40)),
    )


def parse_asset_profile_from_dict(d: dict) -> AssetProfile:
    """Parse an AssetProfile from a JSON-compatible dict."""
    return build_asset_profile(**d)


def filter_by_assets(
    opportunities: list[dict],
    assets: AssetProfile,
    top_n: int = 10,
) -> list[FeasibilityResult]:
    """
    Filter and re-rank NeighborIQ opportunities by operator asset feasibility.

    Args:
        opportunities: list of opportunity dicts from the NeighborIQ pipeline.
                       Each must have at least 'niche' and 'opportunity_score'.
        assets: operator's available assets.
        top_n: max results to return.

    Returns:
        List of FeasibilityResult sorted by combined_score descending.
    """
    results: list[FeasibilityResult] = []

    for opp in opportunities:
        niche = opp.get("niche", "")
        if not niche or niche == "other":
            continue

        opp_score = int(opp.get("opportunity_score", opp.get("score", 50)))

        feasibility, cap_fit, skill_match, have, need = _score_feasibility(niche, assets)

        # Skip impossible capital situations unless there's a home-based path
        home_cap, _, _ = _get_capital_tiers(niche)
        if cap_fit == "impossible" and home_cap == 0:
            continue

        tier = _recommend_entry_tier(niche, assets)
        combined = int(opp_score * 0.45 + feasibility * 0.55)

        what_you_have: list[str] = list(have)
        if assets.has_vehicle and niche in {"auto_repair", "florist", "barbershop"}:
            what_you_have.append("vehicle (mobile ops)")
        if assets.space_sqft > 0:
            what_you_have.append(f"{assets.space_sqft} sqft space")
        if assets.existing_customers > 0:
            what_you_have.append(f"{assets.existing_customers} existing customers")

        results.append(FeasibilityResult(
            niche=niche,
            opportunity_score=opp_score,
            feasibility_score=feasibility,
            combined_score=combined,
            capital_fit=cap_fit,
            skill_match=skill_match,
            what_you_have=tuple(what_you_have),
            what_you_need=tuple(need),
            recommended_entry_tier=tier,
            first_30_days=_get_first_30_days(niche, tier),
            low_to_high_path=_get_escalation(niche),
        ))

    results.sort(key=lambda r: r.combined_score, reverse=True)
    return results[:top_n]


def format_feasibility_results(results: list[FeasibilityResult]) -> str:
    """Return a formatted multi-line string of asset-filtered opportunities."""
    if not results:
        return "No feasible opportunities found for your current asset profile.\n"

    lines: list[str] = ["ASSET-FILTERED OPPORTUNITIES", "━" * 60]
    for i, r in enumerate(results, 1):
        cap_icon = {"perfect": "✓", "tight": "~", "stretch": "!", "impossible": "✗"}.get(
            r.capital_fit, "?"
        )
        lines.append(
            f"\n#{i} {r.niche.replace('_', ' ').title()}"
            f"  [Opp:{r.opportunity_score}  Feasibility:{r.feasibility_score}  Combined:{r.combined_score}]"
        )
        lines.append(
            f"   Capital fit: {cap_icon} {r.capital_fit}  |  "
            f"Skill match: {int(r.skill_match * 100)}%  |  "
            f"Entry: {r.recommended_entry_tier}"
        )
        if r.what_you_have:
            lines.append(f"   Have: {', '.join(r.what_you_have)}")
        if r.what_you_need:
            lines.append(f"   Need: {', '.join(r.what_you_need)}")
        lines.append(f"   Path: {r.low_to_high_path[:120]}...")
        lines.append(f"   First 30 days: {r.first_30_days[:120]}...")

    lines.append("")
    return "\n".join(lines)
