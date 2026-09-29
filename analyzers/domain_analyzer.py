"""domain_analyzer.py — Analyze a business website to find revenue gaps and automation opportunities.

Given a URL, fetches the page, profiles the business (niche, services, location, online features),
cross-references with NeighborIQ market data, and returns actionable revenue-add recommendations.

Usage:
    from neighboriq.analyzers.domain_analyzer import analyze_domain, format_domain_analysis
    analysis = analyze_domain("https://tonybarbershop.com")
    print(format_domain_analysis(analysis))
"""
from __future__ import annotations

import html as html_module
import logging
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

log = logging.getLogger("domain_analyzer")

__all__ = [
    "DomainProfile",
    "DomainAnalysis",
    "fetch_domain_text",
    "extract_zip_from_text",
    "extract_phone",
    "detect_niche_from_text",
    "detect_services",
    "detect_online_features",
    "analyze_domain",
    "format_domain_analysis",
]

# ── constants ─────────────────────────────────────────────────────────────────

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
_MAX_BYTES = 50_000

# keyword → niche (longer/more specific first to win on first match)
_NICHE_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("manicure", "pedicure", "nail salon", "nail spa"), "nail_salon"),
    (("barbershop", "barber shop", "fade", "beard trim", "men's cut"), "barbershop"),
    (("hair salon", "hair studio", "highlights", "balayage", "coloring"), "hair_salon"),
    (("espresso", "latte", "cappuccino", "coffee shop", "cold brew"), "coffee_shop"),
    (("café", "cafe", "brunch", "pastry", "croissant"), "cafe"),
    (("bakery", "bread", "cakes", "muffins", "sourdough"), "bakery"),
    (("laundromat", "coin laundry", "washer", "dryer", "dry clean"), "laundromat"),
    (("grocery", "supermarket", "produce", "deli counter"), "grocery_store"),
    (("convenience store", "c-store", "snacks", "cigarettes", "lottery"), "convenience_store"),
    (("liquor", "beer", "wine", "spirits", "alcohol"), "liquor_store"),
    (("tutor", "tutoring", "homework help", "math class", "sat prep"), "tutoring_center"),
    (("daycare", "childcare", "preschool", "after school", "child care"), "daycare"),
    (("yoga", "pilates", "meditation", "vinyasa", "hot yoga"), "yoga_studio"),
    (("gym", "fitness", "workout", "personal training", "crossfit"), "gym"),
    (("check cashing", "money order", "wire transfer", "western union", "payday"), "check_cashing"),
    (("real estate", "homes for sale", "property listing", "realtor", "mls"), "real_estate"),
    (("insurance", "policy", "coverage", "claims", "auto insurance"), "insurance"),
    (("accounting", "bookkeeping", "tax preparation", "cpa", "payroll"), "accounting"),
    (("auto repair", "mechanic", "oil change", "brake", "tire"), "auto_repair"),
    (("dentist", "dental", "teeth whitening", "orthodontics", "cavity"), "dentist"),
    (("sushi", "japanese", "ramen", "teriyaki"), "sushi_restaurant"),
    (("indian", "curry", "tandoori", "biryani", "masala"), "indian_restaurant"),
    (("halal", "shawarma", "kebab", "falafel"), "halal_restaurant"),
    (("chinese", "dim sum", "wonton", "fried rice", "noodles"), "chinese_restaurant"),
    (("mexican", "taco", "burrito", "enchilada", "guacamole"), "mexican_restaurant"),
    (("pizza", "pizzeria", "calzone", "stromboli"), "pizza_restaurant"),
    (("thai", "pad thai", "green curry", "tom yum"), "thai_restaurant"),
    (("mediterranean", "hummus", "pita", "gyro", "falafel"), "mediterranean_restaurant"),
    (("ethiopian", "injera", "wat", "tibs"), "ethiopian_restaurant"),
    (("vietnamese", "pho", "banh mi", "spring roll", "boba"), "vietnamese_restaurant"),
    (("restaurant", "menu", "dine", "reservations", "entrée"), "restaurant"),
    (("florist", "flowers", "bouquet", "arrangement", "wedding flowers"), "florist"),
    (("gift shop", "souvenirs", "greeting cards", "novelty"), "gift_shop"),
]

# per-niche service keywords
_SERVICE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "barbershop": ("fade", "taper", "line-up", "beard trim", "hot towel shave", "kids cut", "shape-up"),
    "hair_salon": ("highlights", "balayage", "color", "blowout", "keratin", "cut", "trim", "extensions"),
    "nail_salon": ("manicure", "pedicure", "gel", "acrylic", "dip powder", "nail art", "waxing"),
    "coffee_shop": ("espresso", "latte", "cold brew", "pour over", "pour-over", "pastry", "sandwich"),
    "cafe": ("brunch", "avocado toast", "omelette", "smoothie", "salad", "wrap"),
    "bakery": ("custom cakes", "cupcakes", "sourdough", "croissant", "gluten free", "wedding cake"),
    "restaurant": ("delivery", "takeout", "catering", "dine-in", "reservations", "private events"),
    "tutoring_center": ("math", "reading", "sat", "act", "homework help", "stem", "english"),
    "daycare": ("infant care", "toddler", "after school", "summer camp", "preschool", "drop-in"),
    "yoga_studio": ("vinyasa", "hot yoga", "meditation", "pilates", "barre", "restorative"),
    "gym": ("personal training", "group classes", "crossfit", "weights", "cardio", "nutrition"),
    "laundromat": ("drop-off", "wash and fold", "dry cleaning", "alterations", "pickup"),
    "auto_repair": ("oil change", "brake", "tire rotation", "inspection", "transmission", "ac repair"),
    "convenience_store": ("atm", "lottery", "tobacco", "money order", "hot food", "beer"),
}

# booking/ecommerce/loyalty detection signals
_BOOKING_SIGNALS = (
    "book now", "book an appointment", "schedule", "calendly", "booksy", "vagaro",
    "fresha", "reserve", "appointment", "online booking", "book online",
)
_ECOMMERCE_SIGNALS = (
    "add to cart", "buy now", "shop now", "checkout", "shopify", "woocommerce",
    "product", "order online", "purchase",
)
_LOYALTY_SIGNALS = (
    "loyalty", "rewards", "points", "membership", "punch card", "stamp",
    "frequent", "member", "vip",
)

# revenue-add opportunities per niche (what's MISSING → what to add)
_REVENUE_ADDS: dict[str, list[dict]] = {
    "barbershop": [
        {"add": "Monthly membership plan ($80/mo unlimited cuts)", "monthly_add": 2000, "cost": "$0", "why": "25 members = $2K predictable MRR, zero ad spend"},
        {"add": "Retail hair products (pomade, beard oil)", "monthly_add": 600, "cost": "$300 initial inventory", "why": "60% margin, zero extra labor"},
        {"add": "Online booking (Booksy — free)", "monthly_add": 800, "cost": "free", "why": "Reduces no-shows by 30%, captures after-hours bookings"},
        {"add": "Loyalty SMS (Stamp Me — free)", "monthly_add": 400, "cost": "free", "why": "30% repeat visit increase"},
    ],
    "hair_salon": [
        {"add": "Online booking (Vagaro — $25/mo)", "monthly_add": 1200, "cost": "$25/mo", "why": "Captures after-hours bookings, reduces no-shows 30%"},
        {"add": "Retail product line (shampoo, conditioner)", "monthly_add": 800, "cost": "$500 initial inventory", "why": "50-60% margin"},
        {"add": "Membership plan ($120/mo 2 services)", "monthly_add": 3000, "cost": "$0", "why": "25 members = $3K predictable MRR"},
        {"add": "Loyalty SMS (Stamp Me)", "monthly_add": 500, "cost": "free", "why": "30% repeat visit lift"},
    ],
    "nail_salon": [
        {"add": "Online booking (Fresha — free)", "monthly_add": 700, "cost": "free", "why": "15% revenue lift from online discoverability"},
        {"add": "Gel/dip upsell menu", "monthly_add": 900, "cost": "$200 supplies", "why": "$15-25 upsell per visit at 70% margin"},
        {"add": "Loyalty punch card digital (Stamp Me)", "monthly_add": 400, "cost": "free", "why": "Every 10th visit free = 30% retention lift"},
        {"add": "Waxing service add-on", "monthly_add": 600, "cost": "$100 supplies", "why": "High margin, existing client base"},
    ],
    "coffee_shop": [
        {"add": "Online ordering (Square Online — free)", "monthly_add": 1500, "cost": "free + 2.9% transaction", "why": "Pre-orders reduce rush-hour chaos, 20% AOV lift"},
        {"add": "Loyalty app (Square Loyalty — $45/mo)", "monthly_add": 1000, "cost": "$45/mo", "why": "Average 28% visit frequency increase"},
        {"add": "Catering menu for offices", "monthly_add": 2000, "cost": "$0", "why": "1-2 office accounts = $1-2K/mo recurring"},
        {"add": "Merchandise (branded mugs, beans)", "monthly_add": 500, "cost": "$300 initial", "why": "60% margin, passive revenue"},
    ],
    "restaurant": [
        {"add": "DoorDash / UberEats listing", "monthly_add": 3000, "cost": "25-30% commission", "why": "Average 30-40% revenue lift for restaurants"},
        {"add": "Online ordering direct (Square Online)", "monthly_add": 1500, "cost": "free + fees", "why": "0% commission vs 30% from platforms"},
        {"add": "Catering packages", "monthly_add": 2500, "cost": "$0", "why": "1 catering event/week = $500-800 each"},
        {"add": "Email/SMS loyalty list", "monthly_add": 800, "cost": "free (Mailchimp)", "why": "1 email per week = 10-15% repeat visit lift"},
    ],
    "laundromat": [
        {"add": "Drop-off wash & fold service", "monthly_add": 3000, "cost": "$0 (use existing machines)", "why": "$2-3/lb at 80% margin vs self-service 30%"},
        {"add": "Delivery pickup (partner with Dolly/TaskRabbit)", "monthly_add": 1500, "cost": "20% driver cut", "why": "Capture busy households who can't come in"},
        {"add": "Dry cleaning drop-off (subcontract)", "monthly_add": 800, "cost": "$0 (send to wholesale cleaner)", "why": "Pure arbitrage — collect, send out, mark up 40%"},
        {"add": "Loyalty SMS card", "monthly_add": 400, "cost": "free", "why": "Every 10th wash free = 25% retention lift"},
    ],
    "convenience_store": [
        {"add": "Hot food / deli counter", "monthly_add": 4000, "cost": "$2,000 equipment", "why": "Highest margin category in c-stores (50-60%)"},
        {"add": "ATM (own unit)", "monthly_add": 600, "cost": "$2,500 machine", "why": "$1.50-2.50 per transaction, zero labor"},
        {"add": "Money orders / Western Union", "monthly_add": 500, "cost": "$0 (agent program)", "why": "Pure fee income, zero inventory"},
        {"add": "Lottery terminal", "monthly_add": 300, "cost": "$0 (state issued)", "why": "5-8% commission on ticket sales"},
    ],
    "tutoring_center": [
        {"add": "Online tutoring (Zoom sessions)", "monthly_add": 2000, "cost": "free (Zoom basic)", "why": "Serve 3x more students without space cost"},
        {"add": "Group classes (5 students × $30)", "monthly_add": 1500, "cost": "$0", "why": "Same hour, 5x revenue vs 1-on-1"},
        {"add": "Test prep packages (SAT/ACT)", "monthly_add": 1800, "cost": "$100 materials", "why": "$500-800 per student premium package"},
        {"add": "School break intensives", "monthly_add": 2000, "cost": "$0", "why": "Fill dead weeks with week-long boot camps"},
    ],
    "check_cashing": [
        {"add": "Money orders (USPS agent)", "monthly_add": 800, "cost": "$0 (agent signup)", "why": "Pure fee income per transaction"},
        {"add": "Bill payment service", "monthly_add": 600, "cost": "$0 (PayNearMe/CheckFree agent)", "why": "$1-3 per transaction, high volume"},
        {"add": "Prepaid debit cards (NetSpend)", "monthly_add": 500, "cost": "$0 (agent program)", "why": "Commission per activation + reload"},
        {"add": "Notary service", "monthly_add": 400, "cost": "$50 certification", "why": "$10-15 per notarization, zero overhead"},
    ],
    "yoga_studio": [
        {"add": "Online classes (Zoom / YouTube members)", "monthly_add": 2000, "cost": "free", "why": "Unlimited capacity, zero overhead"},
        {"add": "Membership / class packs", "monthly_add": 3000, "cost": "$0", "why": "Predictable MRR, 40% retention lift"},
        {"add": "Retail (yoga mats, blocks, apparel)", "monthly_add": 800, "cost": "$500 initial", "why": "50-60% margin from existing customers"},
        {"add": "Corporate wellness contracts", "monthly_add": 2000, "cost": "$0", "why": "1 company = $500-1K/mo for weekly classes"},
    ],
    "real_estate": [
        {"add": "Property management services", "monthly_add": 3000, "cost": "$0 licensing (state varies)", "why": "8-12% of monthly rent per unit, passive"},
        {"add": "Rental listings (Zillow Premier Agent)", "monthly_add": 1500, "cost": "$200-500/mo", "why": "Renter leads → buyer pipeline"},
        {"add": "Home staging consultation", "monthly_add": 800, "cost": "$0", "why": "$500-1500 per staging consult"},
        {"add": "Social media lead gen (Instagram listings)", "monthly_add": 2000, "cost": "free", "why": "Instagram drives 20%+ of agent inquiries"},
    ],
}

# automation gaps per niche
_AUTOMATION_GAPS: dict[str, tuple[str, ...]] = {
    "barbershop": (
        "Appointment reminders (losing ~15% to no-shows without SMS reminders)",
        "Review request automation (manually asking = 5% response vs 20% automated)",
        "Social media posting (missed new-customer discovery)",
    ),
    "hair_salon": (
        "Automated rebooking reminders at 4-6 weeks (prevents client drift)",
        "Review request SMS after each appointment",
        "Birthday discount automation (high open rate)",
    ),
    "nail_salon": (
        "Appointment reminder SMS 24 hours before (reduce no-shows)",
        "Post-visit review request",
        "Seasonal promotion broadcasts",
    ),
    "restaurant": (
        "Order confirmation & pickup-ready SMS",
        "Review request 30 min after pickup",
        "Weekly specials email blast (Mailchimp free)",
    ),
    "laundromat": (
        "Machine-ready SMS alerts (customer waiting = lost time)",
        "Drop-off ready notification",
        "Monthly loyalty credit reminders",
    ),
    "coffee_shop": (
        "Pre-order reminders (reduce morning rush chaos)",
        "Loyalty points balance SMS",
        "Weekly new menu / special announcement",
    ),
    "tutoring_center": (
        "Session reminder 24h before (reduce parent no-shows)",
        "Progress report automated email monthly",
        "Enrollment renewal reminder at session-end",
    ),
    "convenience_store": (
        "Low-inventory reorder alerts (avoid stockouts on top 20 SKUs)",
        "Loyalty points balance SMS",
        "Weekly promotion blast to loyalty list",
    ),
    "yoga_studio": (
        "Class reminder 2h before (reduce late no-shows)",
        "Membership renewal reminder 7 days before expiry",
        "New class announcement to lapsed students",
    ),
    "real_estate": (
        "New listing alert emails to buyer list",
        "Price drop notifications (automated via MLS webhook)",
        "Post-closing review request automation",
    ),
}

_DEFAULT_AUTOMATION_GAPS = (
    "Appointment/order reminder automation (SMS reduces no-shows 15-30%)",
    "Review request automation (post-service SMS vs manually asking)",
    "Social media scheduling (batch post weekly vs daily manual)",
)


# ── dataclasses ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DomainProfile:
    url: str
    business_name: str
    detected_zip: str
    detected_city: str
    detected_niche: str
    detected_services: tuple[str, ...]
    has_online_booking: bool
    has_ecommerce: bool
    has_loyalty_program: bool
    price_signals: tuple[str, ...]
    phone: str
    address: str


@dataclass(frozen=True)
class DomainAnalysis:
    profile: DomainProfile
    current_strengths: tuple[str, ...]
    neighborhood_gaps: tuple[str, ...]
    revenue_add_opportunities: tuple[dict, ...]
    automation_gaps: tuple[str, ...]
    market_position: str
    neighborhood_opportunity_score: int
    summary: str


# ── helpers ───────────────────────────────────────────────────────────────────

def fetch_domain_text(url: str, timeout: int = 10) -> tuple[str, str]:
    """Returns (plain_text, raw_html). Strips tags, limits to 50KB."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(_MAX_BYTES).decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc

    # unescape HTML entities
    raw_unescaped = html_module.unescape(raw)
    # strip tags
    text = re.sub(r"<[^>]+>", " ", raw_unescaped)
    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text, raw


def extract_zip_from_text(text: str) -> str:
    """Find first 5-digit US zip code in text."""
    m = re.search(r"\b(\d{5})(?:-\d{4})?\b", text)
    return m.group(1) if m else ""


def extract_phone(text: str) -> str:
    """Find first US phone number pattern."""
    m = re.search(
        r"(\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4})",
        text,
    )
    return m.group(1).strip() if m else ""


def extract_business_name(text: str, url: str) -> str:
    """Try og:site_name, <title>, or domain name fallback."""
    title_m = re.search(r"<title[^>]*>([^<]{1,80})</title>", text, re.IGNORECASE)
    if title_m:
        name = title_m.group(1).strip()
        # strip common suffixes
        name = re.sub(r"\s*[|\-–—]\s*.{0,40}$", "", name).strip()
        if name:
            return name
    # domain fallback
    domain_m = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if domain_m:
        return domain_m.group(1).split(".")[0].replace("-", " ").title()
    return "Unknown Business"


def extract_city_from_text(text: str) -> str:
    """Try to find city name near a zip code pattern."""
    m = re.search(
        r"([A-Za-z ]{2,25}),\s*[A-Z]{2}\s+\d{5}",
        text,
    )
    return m.group(1).strip() if m else ""


def extract_address(text: str) -> str:
    """Find a street address pattern."""
    m = re.search(
        r"\d{1,5}\s+[A-Z][a-zA-Z\s]{3,40}(?:St(?:reet)?|Ave(?:nue)?|Rd|Road|Blvd|Ln|Dr|Way|Ct)\b",
        text,
    )
    return m.group(0).strip() if m else ""


def extract_price_signals(text: str) -> tuple[str, ...]:
    """Find price mentions like '$15', '$120/mo'."""
    prices = re.findall(r"\$\d+(?:\.\d{2})?(?:/\w+)?", text)
    return tuple(dict.fromkeys(prices[:10]))  # dedup, max 10


def detect_niche_from_text(text: str) -> str:
    """Map page text to nearest NeighborIQ niche."""
    lower = text.lower()
    for keywords, niche in _NICHE_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return niche
    return "other"


def detect_services(text: str, niche: str) -> tuple[str, ...]:
    """Extract specific services mentioned for this niche."""
    keywords = _SERVICE_KEYWORDS.get(niche, ())
    lower = text.lower()
    found = [kw for kw in keywords if kw in lower]
    return tuple(found)


def detect_online_features(html: str) -> tuple[bool, bool, bool]:
    """Returns (has_booking, has_ecommerce, has_loyalty)."""
    lower = html.lower()
    has_booking = any(s in lower for s in _BOOKING_SIGNALS)
    has_ecommerce = any(s in lower for s in _ECOMMERCE_SIGNALS)
    has_loyalty = any(s in lower for s in _LOYALTY_SIGNALS)
    return has_booking, has_ecommerce, has_loyalty


def _build_strengths(profile: DomainProfile) -> tuple[str, ...]:
    out: list[str] = []
    if profile.address:
        out.append("Physical storefront (detected address)")
    if profile.phone:
        out.append("Phone number listed")
    if profile.has_online_booking:
        out.append("Online booking system active")
    if profile.has_ecommerce:
        out.append("E-commerce / online store active")
    if profile.has_loyalty_program:
        out.append("Loyalty program active")
    if profile.detected_services:
        out.append(f"Services listed: {', '.join(profile.detected_services[:5])}")
    if profile.price_signals:
        out.append(f"Pricing published: {', '.join(profile.price_signals[:3])}")
    if not out:
        out.append("Website presence established")
    return tuple(out)


def _build_revenue_adds(profile: DomainProfile) -> tuple[dict, ...]:
    base = list(_REVENUE_ADDS.get(profile.detected_niche, []))
    # Always add Google Business Profile if no address/phone found
    if not profile.address and not profile.phone:
        base.insert(0, {
            "add": "Google Business Profile (verified)",
            "monthly_add": 500,
            "cost": "free",
            "why": "#1 driver of local foot traffic — invisible without it",
        })
    # Filter out already-present features
    filtered: list[dict] = []
    for item in base:
        add_lower = item["add"].lower()
        if "booking" in add_lower and profile.has_online_booking:
            continue
        if any(w in add_lower for w in ("loyalty", "stamp", "membership")) and profile.has_loyalty_program:
            continue
        if any(w in add_lower for w in ("shop", "store", "ecommerce", "shopify")) and profile.has_ecommerce:
            continue
        filtered.append(item)
    return tuple(filtered[:6])


def _get_neighborhood_data(zip_code: str, niche: str) -> tuple[int, str, tuple[str, ...]]:
    """Returns (opportunity_score, market_position, neighborhood_gaps)."""
    try:
        from neighboriq.storage.market_db import MarketDB
        db = MarketDB()
        opps = db.get_opportunities(zip_code, min_tier="C")
        if not opps:
            return 0, "unknown — no data (run: neighboriq analyze --zip {})".format(zip_code), ()

        # Find this niche's opportunity score
        this_opp = next((o for o in opps if o.get("niche") == niche), None)
        score = this_opp["opportunity_score"] if this_opp else 0
        avg_rating = this_opp.get("competitor_avg_rating", 0.0) if this_opp else 0.0
        competitor_count = this_opp.get("competitor_count", 0) if this_opp else 0

        # Market position
        if score >= 70 and competitor_count <= 2:
            position = "first mover — major undersupply in neighborhood"
        elif 0 < avg_rating < 3.8:
            position = f"weak competitor field (avg rating {avg_rating:.1f}/5 — room to be the best)"
        elif competitor_count >= 5 and avg_rating >= 4.2:
            position = "saturated — differentiation required"
        elif score >= 50:
            position = "moderate competition — opportunity exists"
        else:
            position = "competitive — quality and marketing will decide"

        # Gaps: top niches in neighborhood that this business DOESN'T offer
        top_niches = [o["niche"] for o in opps[:5] if o["niche"] != niche]
        gaps = tuple(f"{n.replace('_', ' ').title()} gap (score {next((o['opportunity_score'] for o in opps if o['niche']==n), 0)})" for n in top_niches[:3])

        return score, position, gaps
    except Exception as exc:
        log.debug("Neighborhood lookup failed: %s", exc)
        return 0, "unknown — no neighborhood data", ()


# ── main API ──────────────────────────────────────────────────────────────────

def analyze_domain(url: str) -> DomainAnalysis:
    """
    Main entry point. Fetch URL, profile the business, cross-reference
    with NeighborIQ market data, return full DomainAnalysis.
    """
    try:
        text, raw_html = fetch_domain_text(url)
    except RuntimeError as exc:
        empty_profile = DomainProfile(
            url=url, business_name="Unknown", detected_zip="", detected_city="",
            detected_niche="other", detected_services=(), has_online_booking=False,
            has_ecommerce=False, has_loyalty_program=False, price_signals=(),
            phone="", address="",
        )
        return DomainAnalysis(
            profile=empty_profile, current_strengths=(), neighborhood_gaps=(),
            revenue_add_opportunities=(), automation_gaps=(),
            market_position="unknown", neighborhood_opportunity_score=0,
            summary=f"Could not fetch {url}: {exc}. Check the URL and try again.",
        )

    niche = detect_niche_from_text(text)
    has_booking, has_ecommerce, has_loyalty = detect_online_features(raw_html)

    profile = DomainProfile(
        url=url,
        business_name=extract_business_name(raw_html, url),
        detected_zip=extract_zip_from_text(text),
        detected_city=extract_city_from_text(text),
        detected_niche=niche,
        detected_services=detect_services(text, niche),
        has_online_booking=has_booking,
        has_ecommerce=has_ecommerce,
        has_loyalty_program=has_loyalty,
        price_signals=extract_price_signals(text),
        phone=extract_phone(text),
        address=extract_address(text),
    )

    opp_score, market_position, neighborhood_gaps = (
        _get_neighborhood_data(profile.detected_zip, niche)
        if profile.detected_zip else (0, "no zip detected", ())
    )

    strengths = _build_strengths(profile)
    revenue_adds = _build_revenue_adds(profile)
    auto_gaps = _AUTOMATION_GAPS.get(niche, _DEFAULT_AUTOMATION_GAPS)

    # Build summary
    total_upside = sum(r.get("monthly_add", 0) for r in revenue_adds)
    top_add = revenue_adds[0]["add"] if revenue_adds else "online booking"
    location_str = f"{profile.detected_city} {profile.detected_zip}".strip() or "detected location"
    summary = (
        f"{profile.business_name} has a {niche.replace('_', ' ')} in {location_str}. "
        f"Market position: {market_position}. "
        f"Leaving ~${total_upside:,}/month on the table across {len(revenue_adds)} revenue gaps. "
        f"Highest-ROI action: {top_add} — implement in under 30 minutes."
    )

    return DomainAnalysis(
        profile=profile,
        current_strengths=strengths,
        neighborhood_gaps=neighborhood_gaps,
        revenue_add_opportunities=revenue_adds,
        automation_gaps=auto_gaps,
        market_position=market_position,
        neighborhood_opportunity_score=opp_score,
        summary=summary,
    )


def format_domain_analysis(analysis: DomainAnalysis) -> str:
    p = analysis.profile
    lines: list[str] = []
    lines.append("BUSINESS DOMAIN ANALYSIS")
    lines.append("━" * 54)
    lines.append(f"Business:  {p.business_name}")
    lines.append(f"URL:       {p.url}")
    lines.append(f"Niche:     {p.detected_niche.replace('_', ' ').title()}")
    loc = f"{p.detected_city} {p.detected_zip}".strip()
    lines.append(f"Location:  {loc or 'not detected'}")
    if p.detected_services:
        lines.append(f"Services:  {', '.join(p.detected_services)}")
    if p.price_signals:
        lines.append(f"Prices:    {', '.join(p.price_signals[:5])}")

    lines.append("")
    lines.append("WHAT YOU HAVE")
    for s in analysis.current_strengths:
        lines.append(f"  ✓ {s}")
    if not p.has_online_booking:
        lines.append("  ✗ No online booking")
    if not p.has_loyalty_program:
        lines.append("  ✗ No loyalty program")
    if not p.has_ecommerce:
        lines.append("  ✗ No online store / ecommerce")
    if not p.phone:
        lines.append("  ✗ Phone not detected on page")
    if not p.address:
        lines.append("  ✗ Address not detected on page")

    lines.append("")
    lines.append(f"NEIGHBORHOOD POSITION ({p.detected_zip or 'zip not detected'})")
    lines.append(f"  Market position:       {analysis.market_position}")
    if analysis.neighborhood_opportunity_score:
        lines.append(f"  Opportunity score:     {analysis.neighborhood_opportunity_score}/100")
    if analysis.neighborhood_gaps:
        lines.append("  Other neighborhood gaps you could expand into:")
        for gap in analysis.neighborhood_gaps:
            lines.append(f"    → {gap}")

    lines.append("")
    lines.append("REVENUE ADD OPPORTUNITIES")
    total_upside = sum(r.get("monthly_add", 0) for r in analysis.revenue_add_opportunities)
    for r in analysis.revenue_add_opportunities:
        monthly = r.get("monthly_add", 0)
        cost = r.get("cost", "?")
        why = r.get("why", "")
        lines.append(f"  +${monthly:,}/mo  {r['add']}  [{cost}]")
        lines.append(f"             Why: {why}")
    lines.append("")
    lines.append(f"  TOTAL UPSIDE: +${total_upside:,}/mo without changing your core service")

    lines.append("")
    lines.append("AUTOMATION GAPS")
    for ag in analysis.automation_gaps:
        lines.append(f"  → {ag}")

    lines.append("")
    lines.append("SUMMARY")
    lines.append(analysis.summary)

    return "\n".join(lines)
