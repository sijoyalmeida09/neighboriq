"""niche_roadmap.py — 3-phase scaling roadmap, Delta 4 moat, and repeat customer mechanics.

Delta 4 Theory (Kunal Shah, CRED):
    Score old behavior 1-10. Score new behavior (done right) 1-10.
    Delta >= 4 = irreversible switching, word-of-mouth, premium pricing moat.
    Example: cash payment = 4, UPI = 9 -> delta = 5 -> nobody goes back to cash.
"""
from __future__ import annotations

from dataclasses import dataclass

__all__ = ["NicheRoadmap", "get_niche_roadmap", "format_roadmap", "list_roadmap_niches"]


@dataclass(frozen=True)
class NicheRoadmap:
    niche: str

    # Phase 1: Boring -- just get operational
    phase1_name: str
    phase1_timeline: str
    phase1_actions: tuple[str, ...]
    phase1_revenue_target: int
    phase1_exit_criteria: str

    # Phase 2: High engagement -- community anchor
    phase2_name: str
    phase2_timeline: str
    phase2_actions: tuple[str, ...]
    phase2_revenue_target: int
    phase2_exit_criteria: str

    # Phase 3: Hard to execute -- institutional moat
    phase3_name: str
    phase3_timeline: str
    phase3_actions: tuple[str, ...]
    phase3_revenue_target: int
    phase3_exit_criteria: str

    # Delta 4 Analysis
    old_experience_score: float
    new_experience_score: float
    delta: float
    delta4_what_changes: str
    irreversibility_trigger: str
    delta4_enabled: bool

    # Repeat Customer Mechanics
    visit_frequency_days: int
    customer_ltv_usd: int
    loyalty_mechanic: str
    referral_trigger: str
    repeat_revenue_pct: float

    # NSE Score + Moat
    nse_score: int
    moat_type: str
    hardest_thing: str


_ROADMAPS: dict[str, NicheRoadmap] = {}


def _reg(**kwargs: object) -> NicheRoadmap:
    r = NicheRoadmap(**kwargs)  # type: ignore[arg-type]
    _ROADMAPS[r.niche] = r
    return r


# ---------------------------------------------------------------------------
# Niche library
# ---------------------------------------------------------------------------

_reg(
    niche="barbershop",
    phase1_name="Neighborhood Standard",
    phase1_timeline="Months 1-6",
    phase1_actions=(
        "Fully optimize Google Business Profile with 10+ photos; get 10 five-star reviews in first 30 days",
        "Install Square POS + Booksy online booking — eliminate phone calls entirely",
        "Develop 3 signature cuts nobody local offers (fade styles, line art, cultural cuts)",
        "Hand-write thank-you card to first 50 customers with a $5 next-visit discount",
        "Track every client's name, preferred style, and last visit in a spreadsheet",
    ),
    phase1_revenue_target=8000,
    phase1_exit_criteria="Booked 80%+ of available slots for 4 consecutive weeks; Google rating 4.7+",
    phase2_name="The Spot",
    phase2_timeline="Months 7-18",
    phase2_actions=(
        "Post before/after Instagram Reels 3x/week — each one tags the client (free reach)",
        "Launch $50/mo loyalty membership: 10th cut free + priority booking + product discount",
        "Host one neighborhood event quarterly (sports watch party, cultural holiday, charity drive)",
        "Add 2nd chair and rent it to a barber at $800-$1,200/mo — zero extra labor for you",
        "Introduce Father & Son packages ($45 vs $60 separately) — drives Saturday morning traffic",
    ),
    phase2_revenue_target=15000,
    phase2_exit_criteria="Second chair fully rented; 40%+ of clients on standing weekly/biweekly appointments",
    phase3_name="Institution",
    phase3_timeline="Months 19-36+",
    phase3_actions=(
        "Scale to 3+ chairs all booth-rented at $800-$1,200/chair/mo — revenue without cutting hair",
        "Build barbering school pipeline: mentor 2 students/yr, first right of refusal on hiring",
        "Launch private-label pomade/edge control product at $18/unit, 70% margin, sold in-shop",
        "Document franchise playbook: training manual, POS setup, social template, supplier list",
        "Use demographic data (age, gender, income by block) to inform chair count and service pricing",
    ),
    phase3_revenue_target=30000,
    phase3_exit_criteria="Booth rent covers rent + utilities; you work by choice, not necessity",
    old_experience_score=3.0,
    new_experience_score=8.0,
    delta=5.0,
    delta4_what_changes=(
        "Appointment-based + same barber every time + culturally fluent + remembers your style "
        "eliminates the anxiety of 'will it look right?' that every walk-in experience carries"
    ),
    irreversibility_trigger=(
        "Visit 3: barber greets you by name, starts your regular fade without being asked, "
        "asks about your kid by name. Customer realizes no chain can replicate this."
    ),
    delta4_enabled=True,
    visit_frequency_days=21,
    customer_ltv_usd=3500,
    loyalty_mechanic="Standing biweekly appointment on Booksy — same slot, same barber, auto-reminded",
    referral_trigger="First time a coworker compliments the cut and asks 'who does your hair?'",
    repeat_revenue_pct=75.0,
    nse_score=72,
    moat_type="trust",
    hardest_thing=(
        "Delivering the same quality cut consistently across 3+ chairs — one bad barber "
        "destroys the reputation you spent 18 months building"
    ),
)

_reg(
    niche="nail_salon",
    phase1_name="Clean & Reliable",
    phase1_timeline="Months 1-6",
    phase1_actions=(
        "Appointment-only from day 1 — no walk-ins creates scarcity signal and respects client time",
        "Post cleanliness photos weekly: autoclave equipment, fresh files, UV sterilizer open on counter",
        "Master 5 trending nail art designs (jelly nails, chrome, 3D florals) that nearby salons don't offer",
        "Publish standard pricing clearly on Instagram bio — no 'starting at' bait-and-switch",
        "Respond to every DM within 1 hour, 7 days a week, for the first 6 months",
    ),
    phase1_revenue_target=10000,
    phase1_exit_criteria="Booked 3+ weeks out consistently; 15+ five-star reviews mentioning cleanliness",
    phase2_name="The Go-To",
    phase2_timeline="Months 7-18",
    phase2_actions=(
        "Add lash extension services: $80-$150/set, 80% margin, books independently of nails",
        "Launch nail membership: $120/mo prepaid = 2 gel manis — locks in revenue, fills slow weeks",
        "Post before/after Reels for every nail set — tag client, use neighborhood hashtags",
        "Host bridal shower nail parties on Sundays ($350-500/hr, 4-6 guests = premium revenue block)",
        "Referral program: $20 credit for both referrer and new client on first visit",
    ),
    phase2_revenue_target=21000,
    phase2_exit_criteria="50+ active memberships generating $6,000+ guaranteed monthly recurring",
    phase3_name="Beauty Hub",
    phase3_timeline="Months 19-36+",
    phase3_actions=(
        "Sublease 2-3 beauty stations to esthetician/lash artist at $600-$800/mo each — passive income",
        "Add licensed esthetician for facials ($80-$150/session, 65% margin)",
        "Launch private-label nail products (cuticle oil, base coat) at $14-$22/unit, sold in-shop and online",
        "Build beauty school referral pipeline: mentor 1 student/semester, first hire right",
        "Use peak-hour booking data to implement dynamic pricing: $10 surcharge on Fri/Sat",
    ),
    phase3_revenue_target=37000,
    phase3_exit_criteria="Station rental covers base overhead; 3 revenue streams operating independently",
    old_experience_score=3.5,
    new_experience_score=7.5,
    delta=4.0,
    delta4_what_changes=(
        "Hygiene visibility + scarcity signal (booked 2 weeks out) + app history of your preferred "
        "styles + membership pricing transforms a commodity into a personalized luxury routine"
    ),
    irreversibility_trigger=(
        "First time the salon posts their nail photo to Instagram and 40 people like it — "
        "the client becomes a brand ambassador before they realize it"
    ),
    delta4_enabled=True,
    visit_frequency_days=21,
    customer_ltv_usd=4200,
    loyalty_mechanic="$120/mo membership auto-billed — canceling feels like losing money already paid",
    referral_trigger="Instagram FOMO: friend sees the post and DMs 'who did your nails?'",
    repeat_revenue_pct=80.0,
    nse_score=68,
    moat_type="switching_cost",
    hardest_thing=(
        "Maintaining identical quality standards as you add technicians — "
        "one inconsistent tech poaches your best clients to a competitor"
    ),
)

_reg(
    niche="laundromat",
    phase1_name="Clean Machine",
    phase1_timeline="Months 1-12",
    phase1_actions=(
        "24/7 operation with visible security cameras — the #1 differentiator vs. competitors",
        "Contactless payment only (no coins): install Laundry Boss or PayRange on every machine",
        "Keep interior at 72F year-round with AC — people linger, spend more, tell friends",
        "Free WiFi with a branded SSID (NeighborhoodWash_Free) + phone charging stations at every row",
        "Google Business Profile with interior photos updated monthly — 'clean' keyword in every post",
    ),
    phase1_revenue_target=10000,
    phase1_exit_criteria="$10K/mo revenue with <5% machine downtime; 4.5+ Google rating",
    phase2_name="Neighborhood Utility",
    phase2_timeline="Months 13-24",
    phase2_actions=(
        "Launch wash-dry-fold at $1.50/lb — targets 60% of revenue with zero owner labor",
        "Sign 3 commercial laundry contracts: gym towels, salon capes, restaurant linens ($500-$2K/mo each)",
        "Loyalty app (LaundryCard or custom): 10th wash free — drives repeat at 88% rate",
        "Text notification when machine cycle ends — one feature that eliminates the #1 complaint",
        "Monthly neighborhood coupon newsletter (print, distributed in 3-block radius) = 200+ reach for $40",
    ),
    phase2_revenue_target=16000,
    phase2_exit_criteria="Commercial contracts cover rent; wash-fold is 40%+ of revenue",
    phase3_name="Infrastructure",
    phase3_timeline="Months 25-48+",
    phase3_actions=(
        "Second location in adjacent zip: use cash flow from Location 1, no bank required",
        "Install vending machines: snacks + detergent pods at 40% margin, $800-$1,200/mo passive",
        "Launch pickup/delivery route at $3/lb (vs $1.50 in-store) — targets working professionals",
        "Negotiate coin-op vending with neighboring businesses (barber, nail salon = referral flywheel)",
        "Sell Location 1 on owner financing at 4-5x EBITDA ($250K-$400K deal) — fund Location 3",
    ),
    phase3_revenue_target=25000,
    phase3_exit_criteria="2+ locations; pickup/delivery generating $3K+/mo; owner works <10 hrs/week",
    old_experience_score=3.0,
    new_experience_score=7.0,
    delta=4.0,
    delta4_what_changes=(
        "App-controlled machines + text-when-done + air conditioning + fold service "
        "converts 2 hours of laundry anxiety into a 5-minute drop-off — time is irreversible"
    ),
    irreversibility_trigger=(
        "First wash-fold pickup: customer realizes they reclaimed 2 hours of their Sunday. "
        "They will never hand-fold their own laundry again."
    ),
    delta4_enabled=True,
    visit_frequency_days=9,
    customer_ltv_usd=2400,
    loyalty_mechanic="Proximity + habit — closest clean laundromat with wash-fold wins permanently",
    referral_trigger="'I just drop it off and pick it up clean' — every working parent tells 3 friends",
    repeat_revenue_pct=88.0,
    nse_score=55,
    moat_type="convenience",
    hardest_thing=(
        "Machine downtime: one broken washer on a Saturday morning costs $200+ in lost revenue "
        "and triggers 3 one-star reviews — preventive maintenance schedule is non-negotiable"
    ),
)

_reg(
    niche="convenience_store",
    phase1_name="Essential Stop",
    phase1_timeline="Months 1-12",
    phase1_actions=(
        "Stock top 80 SKUs covering 90% of impulse needs — don't try to be a supermarket",
        "Accept EBT/SNAP from day 1: 20-40% of neighborhood spend in underserved areas is SNAP",
        "Google Business Profile lists exact hours (open late) — 'open now' filter drives foot traffic",
        "Learn the first and last name of your top 20 customers by week 4 — say it every visit",
        "Clean bathroom with a visible inspection log — customers tell their friends about clean bathrooms",
    ),
    phase1_revenue_target=25000,
    phase1_exit_criteria="$25K/mo revenue; 30+ customers per day; Google rating 4.4+",
    phase2_name="Neighborhood Fridge",
    phase2_timeline="Months 13-24",
    phase2_actions=(
        "Add fresh deli counter: hot food at 65% margin vs 22% on packaged goods",
        "Ethnic grocery section matched to demographics — Haitian, Dominican, West African at 60% premium",
        "Money services: Western Union + bill pay = $300-$500/mo guaranteed foot traffic fee income",
        "Loyalty card with coffee subscription: $25/mo = unlimited 12oz coffee, drives daily visits",
        "Stock 3 items nobody else carries locally — become the only source for those SKUs",
    ),
    phase2_revenue_target=42000,
    phase2_exit_criteria="Deli + ethnic section = 35%+ of gross margin; 3 money service terminals active",
    phase3_name="Community Hub",
    phase3_timeline="Months 25-48+",
    phase3_actions=(
        "In-store ATM: $2.50-$3.50 surcharge per transaction = $500-$800/mo completely passive",
        "Lottery terminal: state license = guaranteed footfall regardless of other factors",
        "Hot food expansion: pizza slice + hot dogs at 65% margin = $2K-$5K/mo on existing space",
        "Second location 1-2 miles away — use same supplier relationships, halve per-unit cost",
        "SKU velocity data: negotiate direct terms with top 10 suppliers — bypass distributor markup",
    ),
    phase3_revenue_target=75000,
    phase3_exit_criteria="ATM + lottery + deli = 50%+ of profit; supplier direct terms locked in",
    old_experience_score=4.0,
    new_experience_score=8.0,
    delta=4.0,
    delta4_what_changes=(
        "Owner knows your name + stocks your cultural foods + accepts EBT without judgment + "
        "open when you need it = feels like a neighbor, not a transaction"
    ),
    irreversibility_trigger=(
        "First time customer finds the exact product they've searched for everywhere "
        "(specific brand of hot sauce, specific phone card, specific snack from home country). "
        "Every store that doesn't have it feels like a failure after that."
    ),
    delta4_enabled=True,
    visit_frequency_days=2,
    customer_ltv_usd=3000,
    loyalty_mechanic="Proximity + cultural alignment + EBT acceptance — switching requires relearning a new store",
    referral_trigger="'They have [specific product]' — spreads through WhatsApp groups and word-of-mouth",
    repeat_revenue_pct=91.0,
    nse_score=62,
    moat_type="community",
    hardest_thing=(
        "Fresh inventory management: spoilage on deli and produce destroys margin — "
        "requires daily ordering discipline and waste tracking from day 1"
    ),
)

_reg(
    niche="tutoring_center",
    phase1_name="Pass the Test",
    phase1_timeline="Months 1-6",
    phase1_actions=(
        "Identify the ONE high-stakes test in your zip (SAT, MCAS, AP Calc) — own that niche entirely",
        "Guarantee: score improvement or full refund — removes every objection, builds immediate trust",
        "First 5 students at 50% off in exchange for video testimonials and 3 referrals each",
        "Partner with 2 middle/high school counselors — they see every struggling student first",
        "Google Classroom + Zoom = zero space cost until $8K/mo, then lease a small room",
    ),
    phase1_revenue_target=6000,
    phase1_exit_criteria="10+ paying students; 3 testimonials with score improvements documented",
    phase2_name="College Pipeline",
    phase2_timeline="Months 7-18",
    phase2_actions=(
        "Add college admissions consulting at $2,500-$5,000/application — 70% margin, high trust purchase",
        "Group classes: 6 students x $150/hr = $900 for 1 tutor's time — scale without hiring",
        "After-school program at 5 feeder schools: $200/student/mo, school handles marketing",
        "Summer intensive camp: $1,500/student/week x 20 students = $30K in 4 weeks",
        "Build '100 families' list with monthly progress email — position as the neighborhood expert",
    ),
    phase2_revenue_target=14000,
    phase2_exit_criteria="3+ group classes running; college consulting = 25%+ of revenue",
    phase3_name="Education Institution",
    phase3_timeline="Months 19-36+",
    phase3_actions=(
        "Franchise curriculum to tutors in 3 other cities at $10K/yr licensing fee",
        "Publish proprietary pass rate statistics publicly — '94% of our students improved by 200+ SAT points'",
        "Online course sales: $199/course x 500 students = $100K/yr passively on existing content",
        "School district partnership: become the official enrichment provider for 2+ districts",
        "Hire part-time tutors at $40/hr, charge clients $80/hr — scales headcount without capital",
    ),
    phase3_revenue_target=37000,
    phase3_exit_criteria="Franchise revenue + online courses = 30%+ of total; proprietory data published",
    old_experience_score=3.0,
    new_experience_score=8.0,
    delta=5.0,
    delta4_what_changes=(
        "Score improvement guarantee + structured curriculum + weekly progress tracking + "
        "college counselor included transforms tutoring from a last resort into a proven system"
    ),
    irreversibility_trigger=(
        "First score report above target: parent screenshots it, sends to every parent group chat. "
        "The data does the marketing permanently."
    ),
    delta4_enabled=True,
    visit_frequency_days=7,
    customer_ltv_usd=8000,
    loyalty_mechanic="Results compound: sibling referrals + college success stories = multi-year family engagement",
    referral_trigger="College acceptance letter — parent tells every family they know who their tutor was",
    repeat_revenue_pct=65.0,
    nse_score=78,
    moat_type="data",
    hardest_thing=(
        "Maintaining guaranteed outcomes while scaling teacher quality — "
        "one underperforming tutor breaks the guarantee promise and destroys the brand"
    ),
)

_reg(
    niche="daycare",
    phase1_name="Safe & Licensed",
    phase1_timeline="Months 1-12",
    phase1_actions=(
        "Obtain full state childcare license before any marketing — this takes 6-12 months, start immediately",
        "Maintain 1:4 infant ratio even when regulations allow 1:7 — trust is built on visible overcaution",
        "Start a waitlist 3 months before opening — waitlist = social proof before you have a single child",
        "Install HiMama or Brightwheel app: parents get real-time photos every 2 hours",
        "First 10 families = founding members at $50/mo discount in exchange for 5-star reviews and referrals",
    ),
    phase1_revenue_target=12000,
    phase1_exit_criteria="Licensed, full enrollment (12+ children), 4.8+ Google rating, waitlist active",
    phase2_name="Community's Daycare",
    phase2_timeline="Months 13-24",
    phase2_actions=(
        "After-school program 3pm-6pm using same staff and space — adds $800/child/mo with no new overhead",
        "Summer camp at $400/week premium — same children, higher rate, parents already trust you",
        "Enroll in USDA Child & Adult Care Food Program — free meal reimbursements, $300-$600/mo",
        "Daycare ambassador program: refer 3 families = 1 month free tuition — word-of-mouth flywheel",
        "Hire bilingual staff matching neighborhood's top 2 languages — non-negotiable differentiator",
    ),
    phase2_revenue_target=23000,
    phase2_exit_criteria="After-school + summer camp running; USDA enrolled; waitlist 6+ families",
    phase3_name="Childcare Franchise",
    phase3_timeline="Months 25-48+",
    phase3_actions=(
        "Open second location — use waitlist data to identify the right zip; same brand standards",
        "Develop proprietary curriculum (Montessori-adjacent) — increases per-child rate $200-$400/mo",
        "Master subsidy programs: CCAP, DTA, childcare vouchers — fills every slot with guaranteed state payment",
        "Train and certify 2 caregivers/yr in your method — licensing fee + talent pipeline",
        "Publish waitlist length publicly ('currently 47 families waiting') — most powerful social proof in childcare",
    ),
    phase3_revenue_target=45000,
    phase3_exit_criteria="2 locations; 80%+ subsidy-funded slots; proprietary curriculum launched",
    old_experience_score=3.5,
    new_experience_score=8.0,
    delta=4.5,
    delta4_what_changes=(
        "Licensed + curriculum-based + real-time photo updates + language-matched staff + "
        "visible waitlist signal eliminates the daily anxiety every parent feels dropping off their child"
    ),
    irreversibility_trigger=(
        "First midday photo notification: parent sees their child laughing during lunch. "
        "Every daycare without this app feels dangerous by comparison."
    ),
    delta4_enabled=True,
    visit_frequency_days=1,
    customer_ltv_usd=60000,
    loyalty_mechanic="5 years per child x siblings = 8-12 year family relationship; switching costs are emotionally enormous",
    referral_trigger="'We have a spot opening' — parents tell every pregnant coworker immediately",
    repeat_revenue_pct=95.0,
    nse_score=85,
    moat_type="trust",
    hardest_thing=(
        "Staff retention: one caregiver incident or negative review can destroy a "
        "business built over 3 years — staff vetting and culture are the only moat"
    ),
)

_reg(
    niche="auto_repair",
    phase1_name="Honest Mechanic",
    phase1_timeline="Months 1-12",
    phase1_actions=(
        "Before/after photo documentation on every repair: texted to customer before work begins",
        "Text written estimate BEFORE touching the car — no surprise invoices, ever",
        "Free diagnostic for any check-engine light — removes the barrier that sends people to chains",
        "First oil change free ($40 cost, $800+ average LTV per car-owning household over 5 years)",
        "Google Business Profile lists 'brakes,' 'AC,' 'check engine,' 'tires' as services — high search intent",
    ),
    phase1_revenue_target=20000,
    phase1_exit_criteria="$20K/mo; 50+ returning customers; Google rating 4.7+ with 30+ reviews",
    phase2_name="Fleet Anchor",
    phase2_timeline="Months 13-24",
    phase2_actions=(
        "Sign 3 fleet accounts: local businesses with 3+ vehicles = $2K-$5K/mo guaranteed recurring",
        "Towing partnership: local tow company sends you every breakdown in your zip = reciprocal referrals",
        "State inspection certification: legal requirement = guaranteed monthly foot traffic you didn't earn",
        "One loaner car: costs $8K-$15K used, eliminates the #1 reason customers go elsewhere",
        "Maintenance reminder texts at 3/6/12 month intervals = 40% return rate with zero ad spend",
    ),
    phase2_revenue_target=34000,
    phase2_exit_criteria="3 fleet accounts; inspection certified; loaner car operational",
    phase3_name="Multi-Bay Empire",
    phase3_timeline="Months 25-48+",
    phase3_actions=(
        "Add second bay, then second location: use fleet account revenue as down payment",
        "Proprietary diagnostic database: every vehicle's full history = switching cost data moat",
        "ADAS calibration certification: advanced driver assistance systems = new revenue, few local competitors",
        "Buy the building when possible — landlord risk is the #1 existential threat to this business",
        "Apprenticeship program: 2 apprentices/yr at lower labor cost + talent pipeline",
    ),
    phase3_revenue_target=65000,
    phase3_exit_criteria="2 bays minimum; ADAS certified; vehicle history database = 500+ records",
    old_experience_score=2.5,
    new_experience_score=7.0,
    delta=4.5,
    delta4_what_changes=(
        "Photo documentation + upfront written estimate + honest explanation eliminates "
        "the fear and distrust that every car owner carries into every repair shop"
    ),
    irreversibility_trigger=(
        "First time the final bill matches the estimate exactly. "
        "Customer realizes this has never happened at any other shop. They tell everyone."
    ),
    delta4_enabled=True,
    visit_frequency_days=150,
    customer_ltv_usd=12000,
    loyalty_mechanic="Trust is structurally irreplaceable — once established, customer never risks a new mechanic",
    referral_trigger="'Go see my mechanic, he's honest' — the rarest sentence in auto repair",
    repeat_revenue_pct=70.0,
    nse_score=82,
    moat_type="trust",
    hardest_thing=(
        "Finding mechanics who share your honesty values — one dishonest hire "
        "destroys the reputation you spent 18 months building, permanently"
    ),
)

_reg(
    niche="coffee_shop",
    phase1_name="The Third Place",
    phase1_timeline="Months 1-8",
    phase1_actions=(
        "One signature drink NOT available anywhere else — name it after the neighborhood or a local story",
        "Open 6am-2pm only: best margin hours, avoids evening labor cost, creates consistent experience",
        "Source coffee with a story: specific farm, single origin, roast date on bag — transparency builds loyalty",
        "Know regulars by first name by week 3 — this is the single most important operational task",
        "Zero delivery apps for the first 12 months: protects 30% margin AND forces in-person experience",
    ),
    phase1_revenue_target=15000,
    phase1_exit_criteria="$15K/mo; 40+ daily regulars; Instagram following 500+ local followers",
    phase2_name="Neighborhood Living Room",
    phase2_timeline="Months 9-20",
    phase2_actions=(
        "Weekly events: open mic, study night, cultural night — zero cost, drives 30-50 new visitors each",
        "Wholesale whole-bean bags to 3 local restaurants at $18/lb — 60% margin, zero retail overhead",
        "Coffee subscription box: $45/mo x 100 subscribers = $4,500 guaranteed recurring monthly",
        "Sell merchandise: sticker, tote, mug at $8-$35 — identity purchase, free walking advertisement",
        "Local artist gallery wall: rotating monthly — artist promotes it, brings their audience in",
    ),
    phase2_revenue_target=25000,
    phase2_exit_criteria="100+ subscribers; wholesale to 3 restaurants active; events fill the space",
    phase3_name="Brand & Beans",
    phase3_timeline="Months 21-36+",
    phase3_actions=(
        "Second location in office district: different customer, different daypart, zero cannibalization",
        "Roasting license: roast your own beans at 70% margin vs buying roasted at 45% margin",
        "License signature drink to 2 hotels or corporate offices: $500-$1,500/mo per account, passive",
        "Off-hours ghost kitchen rental: 2pm-5pm kitchen to local food businesses at $20/hr",
        "Wholesale = 50% of revenue target — B2B is low labor, predictable, scalable without foot traffic",
    ),
    phase3_revenue_target=45000,
    phase3_exit_criteria="Roasting license active; 2nd location profitable; wholesale 40%+ of revenue",
    old_experience_score=5.0,
    new_experience_score=9.0,
    delta=4.0,
    delta4_what_changes=(
        "Barista knows your name, your drink, and your Monday mood — "
        "Starbucks can never replicate this at scale, making every chain feel cold by comparison"
    ),
    irreversibility_trigger=(
        "First time the barista starts making your order before you reach the counter. "
        "You realize you've never felt this recognized anywhere else."
    ),
    delta4_enabled=True,
    visit_frequency_days=2,
    customer_ltv_usd=3200,
    loyalty_mechanic="Habit + identity — being 'a regular at [shop name]' is a personality trait, not a transaction",
    referral_trigger="Instagram photo of the space or drink: the aesthetic does the marketing",
    repeat_revenue_pct=72.0,
    nse_score=70,
    moat_type="community",
    hardest_thing=(
        "Preserving the 'small and special' feeling as you scale — "
        "the moment it feels like a chain, the regulars leave and never explain why"
    ),
)

_reg(
    niche="gym",
    phase1_name="Consistent & Clean",
    phase1_timeline="Months 1-12",
    phase1_actions=(
        "24/7 key fob access: members value flexibility above all, reduces staff cost by 60%",
        "Free 14-day trial, no credit card required: removes every barrier, converts 40% to paid",
        "One free group class per week: builds community before memberships, creates FOMO",
        "Fix the one thing every other local gym fails at: choose cleanliness, equipment, or parking and dominate it",
        "6-month prepaid membership at 15% discount — improves cash flow and locks retention",
    ),
    phase1_revenue_target=11000,
    phase1_exit_criteria="80+ active members; equipment uptime 99%; Google rating 4.6+",
    phase2_name="Fitness Community",
    phase2_timeline="Months 13-24",
    phase2_actions=(
        "Personal training: hire 2 trainers at 50/50 revenue split — zero cost to gym, adds $3K-$8K/mo",
        "Nutrition coaching add-on at $200/mo: pairs with training, 65% margin on a 30-min/week service",
        "6-week transformation challenge: $200 entry fee, before/after photos = organic marketing content",
        "Corporate wellness contracts: $500-$2,000/mo per company for employee memberships",
        "Referral month: 'Bring a Friend February' — refer 1 member, get 1 month free",
    ),
    phase2_revenue_target=23000,
    phase2_exit_criteria="2 trainers active; 1 corporate contract signed; 150+ members",
    phase3_name="Health Platform",
    phase3_timeline="Months 25-48+",
    phase3_actions=(
        "Franchise the model: $15K licensing fee + 8% monthly royalty — sells the playbook, not the gym",
        "Physical therapy co-location partnership: PT pays rent, refers members post-injury = premium positioning",
        "Proprietary tracking app: workout logs + progress photos = data switching cost, members can't leave easily",
        "Private-label supplement line: protein, pre-workout at 40% margin, sold at front desk",
        "Second location: same brand standards, same culture — culture doesn't travel without documentation",
    ),
    phase3_revenue_target=48000,
    phase3_exit_criteria="Franchise agreement signed; PT partnership active; proprietary app launched",
    old_experience_score=3.0,
    new_experience_score=7.5,
    delta=4.5,
    delta4_what_changes=(
        "Community feel + coach knows your name + accountability texts + 24/7 access "
        "removes the intimidation and anonymity that kills motivation at big box gyms"
    ),
    irreversibility_trigger=(
        "First time a member hits a personal record and has 10 people cheering for them. "
        "No Planet Fitness can replicate that moment."
    ),
    delta4_enabled=True,
    visit_frequency_days=2,
    customer_ltv_usd=4800,
    loyalty_mechanic="Community — leaving the gym means leaving the friends, the coach, and the routine simultaneously",
    referral_trigger="'How did you lose the weight?' — the referral writes itself",
    repeat_revenue_pct=68.0,
    nse_score=74,
    moat_type="community",
    hardest_thing=(
        "Retaining members past the 90-day motivation cliff — "
        "requires proactive community management, not just equipment, which most gym owners don't know how to do"
    ),
)

_reg(
    niche="indian_restaurant",
    phase1_name="Authentic & Consistent",
    phase1_timeline="Months 1-8",
    phase1_actions=(
        "12-item menu maximum — NOT 100 items; limits waste, forces mastery, speeds kitchen",
        "One hero dish that earns Yelp mentions: a grandma's recipe nobody else makes in the area",
        "Lunch thali at $12 fixed price — consistent, profitable, easy to execute under pressure",
        "GrubHub/DoorDash for lunch only: delivery at dinner damages the experience and margin",
        "Family recipe story printed on menu card — the story justifies premium pricing",
    ),
    phase1_revenue_target=18000,
    phase1_exit_criteria="$18K/mo; hero dish mentioned in 5+ reviews by name; 4.5+ Google rating",
    phase2_name="The Destination",
    phase2_timeline="Months 9-20",
    phase2_actions=(
        "Catering for South Asian events: weddings $5K-$30K/event, corporate $500-$5K — highest single transactions",
        "Cooking class at $75/person x 20 = $1,500/night: empty restaurant on Monday night becomes revenue",
        "Weekend brunch buffet at $25/head: high throughput, low labor, premium price for off-hours slot",
        "Frozen meal subscription at $150/mo x 50 subscribers = $7,500 guaranteed monthly recurring",
        "Brand ambassador in local South Asian community: one influential family = 50 referred customers",
    ),
    phase2_revenue_target=32000,
    phase2_exit_criteria="Catering at 2+ events/mo; 50 frozen meal subscribers; cooking class waitlist",
    phase3_name="Cuisine Empire",
    phase3_timeline="Months 21-36+",
    phase3_actions=(
        "Ghost kitchen franchise: license your tiffin model to operators in 3 cities at $15K/yr",
        "Retail packaging: curry paste + spice blend sold at Whole Foods / Indian grocery chains",
        "YouTube cooking channel: 50K subscribers → drives 20%+ of restaurant bookings organically",
        "Franchise in adjacent city: $50K franchise fee + 6% royalty on $40K/mo = $2,400/mo passive",
        "Catering fleet: refrigerated van + commercial equipment = $8K-$25K/event capability",
    ),
    phase3_revenue_target=65000,
    phase3_exit_criteria="Retail product in 2+ stores; franchise agreement signed; YouTube monetized",
    old_experience_score=3.0,
    new_experience_score=8.0,
    delta=5.0,
    delta4_what_changes=(
        "Grandmother's recipe from a specific Indian state + server who explains regional context + "
        "feeling like a guest in someone's home, not a diner in a generic 'Indian restaurant'"
    ),
    irreversibility_trigger=(
        "First time a customer says 'this tastes exactly like home' and calls their mother to describe it. "
        "No other restaurant can manufacture that emotional memory."
    ),
    delta4_enabled=True,
    visit_frequency_days=12,
    customer_ltv_usd=5200,
    loyalty_mechanic="Nostalgia is the most irreplaceable loyalty mechanic — no loyalty card can replicate an emotional anchor",
    referral_trigger="South Asian community network effect: one family tells 10 others, WhatsApp groups do the rest",
    repeat_revenue_pct=74.0,
    nse_score=76,
    moat_type="trust",
    hardest_thing=(
        "Recipe consistency when the original cook is unavailable — "
        "must document every recipe to gram-level precision before scaling or hiring"
    ),
)

_reg(
    niche="check_cashing",
    phase1_name="Fast & Fair",
    phase1_timeline="Months 1-12",
    phase1_actions=(
        "Post fee schedule on exterior signage: 0.5% lower than nearest competitor, visible from sidewalk",
        "Western Union terminal from day 1 — drives footfall regardless of anything else you offer",
        "Open Sundays 10am-4pm: 99% of competitors are closed, you earn the entire underbanked Sunday market",
        "Multilingual staff matching neighborhood's top 2-3 languages — non-negotiable",
        "Fee schedule laminated on counter: full transparency vs. competitors who hide fees in fine print",
    ),
    phase1_revenue_target=11000,
    phase1_exit_criteria="$11K/mo; Western Union processing active; Google rating 4.4+",
    phase2_name="Community Bank",
    phase2_timeline="Months 13-24",
    phase2_actions=(
        "Prepaid debit card program: $7.95/mo card fee x 200 cardholders = $1,590 recurring monthly",
        "Tax preparation Jan-April: $150-$400/return, highest margin service per hour in the business",
        "Money order at $1.50/unit: high margin, drives foot traffic from utility bill payers",
        "Notary services at $10-$25/document: zero overhead addition if owner is licensed",
        "Bill pay terminal for 10+ utility companies: every utility company's customers = your customers",
    ),
    phase2_revenue_target=23000,
    phase2_exit_criteria="200+ prepaid cardholders; tax prep running first season; 5 bill pay companies",
    phase3_name="Financial Hub",
    phase3_timeline="Months 25-48+",
    phase3_actions=(
        "Small business lending referral partnership: $200-$500/loan referral fee, zero capital required",
        "Insurance license (auto + renters): recurring commission on existing customers at no acquisition cost",
        "Cryptocurrency ATM: 15-20% fee per transaction = $3K-$6K/mo passive on a $8K machine",
        "Second location in adjacent underbanked zip: same playbook, lower startup risk",
        "Proprietary prepaid card with neighborhood loyalty points: gas, groceries, utilities = closed loop",
    ),
    phase3_revenue_target=45000,
    phase3_exit_criteria="Crypto ATM installed; insurance license active; 2nd location open",
    old_experience_score=2.0,
    new_experience_score=7.0,
    delta=5.0,
    delta4_what_changes=(
        "Dignified service + transparent fees + multilingual staff + no-judgment environment "
        "transforms a shame transaction (payday loan) into a trusted community financial partner"
    ),
    irreversibility_trigger=(
        "First tax refund deposited to their prepaid card at your counter — "
        "you now hold their financial relationship across 4 services simultaneously"
    ),
    delta4_enabled=True,
    visit_frequency_days=14,
    customer_ltv_usd=2800,
    loyalty_mechanic="Trust + convenience + language — switching requires finding another staff member who speaks your language",
    referral_trigger="Immigrant community trust network: person-to-person, never online",
    repeat_revenue_pct=85.0,
    nse_score=65,
    moat_type="trust",
    hardest_thing=(
        "Money transmission license: $50K+ application cost, 12-18 months per state — "
        "must be completed before operating, non-negotiable, cannot be skipped"
    ),
)

_reg(
    niche="florist",
    phase1_name="Reliable & Beautiful",
    phase1_timeline="Months 1-8",
    phase1_actions=(
        "Valentine's Day + Mother's Day = 40% of annual revenue — plan for these 2 dates like they're war",
        "Pre-order system with 50% deposit: cash flow management and demand signal before you buy inventory",
        "Develop one signature wrap style that photographs perfectly — this is your Instagram currency",
        "Same-day delivery for $15 premium: 30% of customers will pay it, zero extra effort to offer",
        "Funeral home relationship: 3 funeral homes = 6-12 guaranteed arrangements/mo at $80-$250 each",
    ),
    phase1_revenue_target=8000,
    phase1_exit_criteria="$8K/mo; 3 funeral home accounts; 200 Instagram followers with 4%+ engagement",
    phase2_name="Event Florist",
    phase2_timeline="Months 9-20",
    phase2_actions=(
        "Wedding florals: $3,500-$15,000/wedding at 55% margin — one wedding = 2 weeks of retail revenue",
        "Corporate subscription: weekly office flowers at $200-$500/mo per client = recurring revenue",
        "Monthly floral arrangement class at $65/person x 20 = $1,300 on a Tuesday night",
        "Subscription box: $75/mo x 80 subscribers = $6,000 guaranteed recurring monthly",
        "Wedding venue content partnership: provide venue florals for photoshoots in exchange for referrals",
    ),
    phase2_revenue_target=18000,
    phase2_exit_criteria="2 weddings/mo booked; 60 subscription box customers; 3 corporate accounts",
    phase3_name="Floral Brand",
    phase3_timeline="Months 21-36+",
    phase3_actions=(
        "Wholesale to 5+ restaurants and hotels: consistent volume = predictable baseline revenue",
        "Online floral design course at $299: existing knowledge monetized, zero marginal cost per student",
        "Event styling expansion: florals + full decor = 3x revenue per event, no new customer acquisition",
        "Franchise your design system to florists in 3 other cities at $8K/yr licensing",
        "Branded packaging at weddings: 150-person event = 150 people photographing your branded arrangements",
    ),
    phase3_revenue_target=32000,
    phase3_exit_criteria="Wholesale to 5 businesses; online course launched; 2 event styling contracts/mo",
    old_experience_score=3.0,
    new_experience_score=7.5,
    delta=4.5,
    delta4_what_changes=(
        "Fresh-sourced + custom color palette matched to the occasion + hand-delivered with personalized note "
        "transforms a transactional purchase into an emotional experience the recipient photographs and shares"
    ),
    irreversibility_trigger=(
        "First time the recipient cries at the delivery. "
        "The sender will never buy flowers from a grocery store again — ever."
    ),
    delta4_enabled=True,
    visit_frequency_days=25,
    customer_ltv_usd=3800,
    loyalty_mechanic="Emotional anchor: they got a positive response from the recipient, and they'll chase that feeling every time",
    referral_trigger="Recipient asks 'where did those flowers come from?' — every beautiful delivery is a referral",
    repeat_revenue_pct=60.0,
    nse_score=66,
    moat_type="switching_cost",
    hardest_thing=(
        "Perishable inventory management: wrong demand forecast = thousands in waste — "
        "requires daily ordering discipline and ruthless pre-order incentivization"
    ),
)


_reg(
    niche="funeral_home",
    phase1_name="Dignified Standard",
    phase1_timeline="Months 1-6",
    phase1_actions=(
        "Register with Massachusetts Funeral Directors Association (MFDA) — referral pipeline + legal protection",
        "Get all Google Business reviews responded to within 24hr — funeral families research 4+ providers before choosing",
        "Create a pre-need funeral planning brochure (Massachusetts allows pre-need contracts) — $3K-8K per family upfront",
        "Partner with local Haitian churches and community centers for referral exchange",
        "Document all repatriation logistics into a repeatable SOP — cost basis, airline contacts, Haiti consulate process",
    ),
    phase1_revenue_target=35000,
    phase1_exit_criteria="Pre-need program launched; 2+ church referral partnerships active; SOP documented",
    phase2_name="Diaspora Network Hub",
    phase2_timeline="Months 7-18",
    phase2_actions=(
        "Launch grief support group in Creole — monthly meetings, $50-100/family/mo subscription, 20-40 families = $1K-4K/mo recurring",
        "Expand repatriation service to Haitian diaspora in Providence RI + New Haven CT + Hartford CT — same network, new geography",
        "Offer Haitian death certificate authentication + translation services ($150-300/document) — families need this anyway",
        "Partner with burial insurance agent (Massachusetts Mutual, Foresters) — earn $500-1500 per policy referred",
        "Host annual Fet Gede (Haitian Day of the Dead) community event — 200+ attendees, $25-50 ticket, cultural anchor",
    ),
    phase2_revenue_target=55000,
    phase2_exit_criteria="Grief group has 25+ paying families; repatriation expanded to 2+ cities; insurance partnership active",
    phase3_name="New England Haitian Death-Care Institution",
    phase3_timeline="Months 19-36",
    phase3_actions=(
        "Open satellite arrangement office in Providence RI or Hartford CT (no embalming needed — just arrangement desk + transport)",
        "Launch Haitian pre-need trust fund — partner with a MA-licensed funeral insurance provider for guaranteed-price plans",
        "License your repatriation SOP to 3 non-competing Haitian funeral homes in Miami/NYC/Montreal for $500-1500/mo each",
        "Build an estate services partnership — probate attorneys, Haitian community banks, immigrant financial advisors",
        "Target 25+ repatriations/yr to Haiti — position as the New England specialist, charge 30% premium over generic providers",
    ),
    phase3_revenue_target=90000,
    phase3_exit_criteria="2+ arrangement offices; licensed SOP to 2+ out-of-state homes; regional brand recognized in Haitian press",
    old_experience_score=4.0,
    new_experience_score=9.0,
    delta=5.0,
    delta4_what_changes="From generic American funeral home with language barrier to Haitian family's trusted community institution — one call, they never switch",
    irreversibility_trigger="First family that experiences a repatriation handled in 48hr with Creole support — they refer every single person in their network",
    delta4_enabled=True,
    visit_frequency_days=730,
    customer_ltv_usd=18000,
    loyalty_mechanic="Pre-need funeral contract — family locks in today's prices for guaranteed future service; creates 100% retention",
    referral_trigger="Repatriation handled in 48hr — family posts on Facebook Haitian groups (each has 5,000-30,000 members) before even leaving the airport",
    repeat_revenue_pct=35.0,
    nse_score=87,
    moat_type="cultural_language_trust",
    hardest_thing="Building the Haiti air cargo + morgue network and Haitian consulate relationships — takes 2+ years and can't be copied quickly",
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_GENERIC_FALLBACK = NicheRoadmap(
    niche="generic",
    phase1_name="Get Operational",
    phase1_timeline="Months 1-6",
    phase1_actions=(
        "Claim and fully optimize Google Business Profile — photos, hours, services",
        "Get 10 five-star reviews in first 30 days from real customers",
        "Build a simple appointment or order system to eliminate phone tag",
        "Learn the first name of every repeat customer in the first 30 days",
    ),
    phase1_revenue_target=8000,
    phase1_exit_criteria="Consistent revenue; positive reviews; repeat customers returning",
    phase2_name="Community Anchor",
    phase2_timeline="Months 7-18",
    phase2_actions=(
        "Launch a loyalty program that rewards repeat visits",
        "Host one community event quarterly — the neighborhood should know your name",
        "Add a second revenue stream that uses existing space or skills",
        "Build a referral system: existing customers bring new ones",
    ),
    phase2_revenue_target=18000,
    phase2_exit_criteria="30%+ of revenue from repeat customers; recognizable brand in neighborhood",
    phase3_name="Neighborhood Institution",
    phase3_timeline="Months 19-36+",
    phase3_actions=(
        "Add passive revenue: rental income, subscriptions, or wholesale",
        "Document your playbook well enough to franchise or license it",
        "Build a data asset: customer history, preferences, purchase patterns",
        "Expand to second location or second market",
    ),
    phase3_revenue_target=35000,
    phase3_exit_criteria="Passive income covers overhead; data asset creates switching cost",
    old_experience_score=4.0,
    new_experience_score=7.0,
    delta=3.0,
    delta4_what_changes="Personalization and reliability above what any chain can deliver at scale",
    irreversibility_trigger="First time a customer says 'I can't imagine going anywhere else'",
    delta4_enabled=False,
    visit_frequency_days=30,
    customer_ltv_usd=2000,
    loyalty_mechanic="Consistency + recognition + proximity",
    referral_trigger="A friend asks for a recommendation in the category",
    repeat_revenue_pct=55.0,
    nse_score=50,
    moat_type="community",
    hardest_thing="Maintaining quality and culture while scaling beyond the owner's direct involvement",
)


def get_niche_roadmap(niche: str) -> NicheRoadmap:
    """Return the roadmap for a niche. Falls back to generic if unknown."""
    return _ROADMAPS.get(niche, _GENERIC_FALLBACK)


def list_roadmap_niches() -> list[str]:
    """Return sorted list of niches with a defined roadmap."""
    return sorted(_ROADMAPS.keys())


def format_roadmap(roadmap: NicheRoadmap) -> str:
    """Human-readable roadmap string showing all phases, Delta 4, and repeat mechanics."""
    delta_flag = "DELTA 4 MOAT ACHIEVED" if roadmap.delta4_enabled else f"delta={roadmap.delta:.1f} (below threshold)"
    lines = [
        f"NICHE ROADMAP: {roadmap.niche.upper().replace('_', ' ')}",
        "=" * 60,
        "",
        f"PHASE 1 — {roadmap.phase1_name} ({roadmap.phase1_timeline})",
        f"  Target: ${roadmap.phase1_revenue_target:,}/mo",
    ]
    for action in roadmap.phase1_actions:
        lines.append(f"  • {action}")
    lines += [
        f"  Exit when: {roadmap.phase1_exit_criteria}",
        "",
        f"PHASE 2 — {roadmap.phase2_name} ({roadmap.phase2_timeline})",
        f"  Target: ${roadmap.phase2_revenue_target:,}/mo",
    ]
    for action in roadmap.phase2_actions:
        lines.append(f"  • {action}")
    lines += [
        f"  Exit when: {roadmap.phase2_exit_criteria}",
        "",
        f"PHASE 3 — {roadmap.phase3_name} ({roadmap.phase3_timeline})",
        f"  Target: ${roadmap.phase3_revenue_target:,}/mo",
    ]
    for action in roadmap.phase3_actions:
        lines.append(f"  • {action}")
    lines += [
        f"  Exit when: {roadmap.phase3_exit_criteria}",
        "",
        f"DELTA 4 ANALYSIS  [{delta_flag}]",
        f"  Old experience score : {roadmap.old_experience_score}/10",
        f"  New experience score : {roadmap.new_experience_score}/10",
        f"  Delta                : {roadmap.delta:.1f}",
        f"  What changes         : {roadmap.delta4_what_changes}",
        f"  Irreversibility      : {roadmap.irreversibility_trigger}",
        "",
        "REPEAT CUSTOMER MECHANICS",
        f"  Visit frequency  : every {roadmap.visit_frequency_days} days",
        f"  Lifetime value   : ${roadmap.customer_ltv_usd:,}/yr per loyal customer",
        f"  Loyalty mechanic : {roadmap.loyalty_mechanic}",
        f"  Referral trigger : {roadmap.referral_trigger}",
        f"  Repeat revenue   : {roadmap.repeat_revenue_pct:.0f}% of total",
        "",
        f"MOAT: {roadmap.moat_type.upper()}  |  NSE Score: {roadmap.nse_score}/100",
        f"HARDEST THING: {roadmap.hardest_thing}",
    ]
    return "\n".join(lines)
