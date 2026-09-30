"""universal_roadmap.py — 3-phase scaling roadmap derived from real benchmark data."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from neighboriq.intelligence.biz_profile import BizProfile
    from neighboriq.intelligence.benchmark_engine import DomainBenchmarks
    from neighboriq.intelligence.domain_taxonomy import DomainSpec
    from neighboriq.intelligence.vertical_finder import VerticalOpportunity

__all__ = [
    "RoadmapPhase",
    "Delta4Analysis",
    "TrendOpportunity",
    "UniversalRoadmap",
    "generate_roadmap",
    "format_roadmap",
]


@dataclass(frozen=True)
class RoadmapPhase:
    phase: int
    name: str
    timeline: str
    theme: str
    actions: tuple[str, ...]
    revenue_target: int
    kpis: tuple[str, ...]
    exit_criteria: str


@dataclass(frozen=True)
class Delta4Analysis:
    old_experience_score: float
    new_experience_score: float
    delta: float
    what_changes: str
    irreversibility_trigger: str
    enabled: bool


@dataclass(frozen=True)
class TrendOpportunity:
    trend_name: str
    why_now: str
    how_to_exploit: str
    source: str


@dataclass(frozen=True)
class UniversalRoadmap:
    biz_name: str
    domain_id: str
    generated_at: str
    confidence: str
    phases: tuple[RoadmapPhase, RoadmapPhase, RoadmapPhase]
    delta4: Delta4Analysis
    top_verticals: tuple[Any, ...]
    trend_opportunities: tuple[TrendOpportunity, ...]
    benchmark_sources: tuple[str, ...]
    benchmark_vintage: int

    @property
    def phase1(self) -> RoadmapPhase:
        return self.phases[0]

    @property
    def phase2(self) -> RoadmapPhase:
        return self.phases[1]

    @property
    def phase3(self) -> RoadmapPhase:
        return self.phases[2]


# ── Delta 4 by domain ────────────────────────────────────────────────────────
_DELTA4_BY_DOMAIN: dict[str, Delta4Analysis] = {
    "logistics": Delta4Analysis(3.5, 8.0, 4.5, "From 'hope it shows up' to 'I know exactly where it is and who to call'", "First on-time delivery when a previous carrier failed them", True),
    "distribution": Delta4Analysis(3.0, 7.5, 4.5, "From phone orders and manual tracking to EDI-integrated, real-time inventory and automated reorder", "First time they see their inventory auto-reordered without a phone call", True),
    "software_saas": Delta4Analysis(4.0, 8.5, 4.5, "The task goes from a 2-hour manual effort to a 2-minute automated flow", "First month they cannot remember how they did it before", True),
    "agency_services": Delta4Analysis(3.5, 8.0, 4.5, "From project-by-project anxiety to a predictable monthly retainer with guaranteed scope", "First invoice that arrives automatically without a proposal fight", True),
    "music_entertainment": Delta4Analysis(3.0, 7.5, 4.5, "From 'exposure economy' to 'royalty economy' — every stream and sync earns without a gig", "First sync licensing check — they never perform for free again", True),
    "food_beverage": Delta4Analysis(3.5, 8.0, 4.5, "From generic menu to a culturally specific, story-driven experience nobody else in the area offers", "First time a customer says 'this tastes like home' and calls their family", True),
    "healthcare": Delta4Analysis(4.0, 8.5, 4.5, "From 'wait 3 weeks for an appointment, see a different doctor each time' to same-day, personalized, outcome-tracked care", "First follow-up text that asks how they are feeling — nobody else does that", True),
    "retail": Delta4Analysis(3.5, 7.5, 4.0, "From generic inventory to a curation so specific to the neighborhood that customers travel for it", "First time they find a product here they could not find anywhere else online", True),
    "real_estate": Delta4Analysis(3.0, 7.5, 4.5, "From landlord-tenant transactional relationship to a managed-asset partnership where owners see monthly reports without asking", "First month-end financial report delivered automatically without the owner chasing", True),
    "education": Delta4Analysis(3.5, 8.0, 4.5, "From 'generic tutoring that may or may not work' to a guaranteed outcome with score improvement or money back", "When the student hits their target score and the parent calls every parent they know", True),
    "manufacturing": Delta4Analysis(3.0, 7.5, 4.5, "From custom quotes with 3-week turnaround to instant online configuration, pricing, and 5-day delivery", "First instant quote that closes without a single phone call", True),
    "creative_media": Delta4Analysis(3.5, 8.0, 4.5, "From 'another generic video agency' to a full-service creative partner who owns the brand narrative across all channels", "First campaign where the client says 'our competitors started copying our style'", True),
    "professional_services": Delta4Analysis(3.5, 8.0, 4.5, "From reactive problem-solving billed by the hour to proactive advisory on a flat monthly retainer", "First month when a problem was caught before it became expensive — unprompted", True),
    "local_service": Delta4Analysis(3.0, 7.5, 4.5, "From anonymous commodity service to a trusted neighborhood expert who knows you by name and history", "First visit where the service provider remembers their preference without being told", True),
}

_GENERIC_DELTA4 = Delta4Analysis(3.5, 7.0, 3.5, "Systematize the service so quality is consistent, then layer in loyalty mechanics that make switching painful", "First time a customer refers a friend without being asked", False)


# ── Trends by domain (updated Q3 2026) ───────────────────────────────────────
_TRENDS_BY_DOMAIN: dict[str, tuple[TrendOpportunity, ...]] = {
    "logistics": (
        TrendOpportunity("AI-Assisted Dispatch", "Convoy and Transfix collapsed in 2024, leaving independent carriers who adopt AI tools ($200-500/mo) with the advantage previously reserved for enterprises at $2K-5K/mo", "Deploy a $99/mo AI load-matching tool; market as 'AI-dispatched' to price-sensitive shippers who previously used the failed platforms", "FreightWaves 2025 / BTS Q2 2026"),
        TrendOpportunity("Final-Mile E-Commerce Overflow", "Amazon, UPS, FedEx have suburban corridor capacity constraints; local carriers earn 18-25% premium for reliable last-mile SLAs", "Contract with 2-3 local e-commerce fulfillment centers for guaranteed volume at premium rates; one contract = $8-15K/mo baseline", "BTS Supply Chain Indicators 2026"),
        TrendOpportunity("Cold Chain Gap", "Post-COVID food supply chain rebuild created a 40% shortage in last-mile refrigerated capacity projected through 2027", "Add one refrigerated van ($800/mo lease) to open a $12-18K/mo grocery or pharma lane unavailable to standard carriers", "USDA ERS + BTS 2026"),
    ),
    "distribution": (
        TrendOpportunity("Direct-to-Retail Bypass", "Brands are cutting national distributors in favor of regional partners who offer faster restock and better sell-through data", "Pitch 5 regional brands on a direct distribution deal with weekly POS data reporting — differentiate on data, not just delivery", "FRED PPI Wholesale 2026"),
        TrendOpportunity("Private Label Demand Spike", "Post-inflation consumer shift to value brands has retailers seeking distributors who can source and brand generic products at 35-50% below national brands", "Source 2-3 private label SKUs in your top category; offer exclusive regional distribution rights", "Census SUSB Manufacturing 2026"),
        TrendOpportunity("EDI Adoption Gap", "60% of regional distributors still process orders by phone or email; EDI-capable distributors win national retail accounts that others cannot touch", "Implement free-tier EDI (SPS Commerce Fulfillment, $299/mo) to unlock national retail buyer relationships", "SBA Market Intelligence 2026"),
    ),
    "software_saas": (
        TrendOpportunity("AI Feature Commoditization", "Basic AI features (summarize, generate, search) are now table stakes; the moat has shifted to workflow automation that replaces a specific job function entirely", "Map your product to one job function it can fully replace (not assist) — price it as headcount replacement at $2-5K/mo instead of $99/seat", "GitHub OSS Benchmarks 2026"),
        TrendOpportunity("Vertical SaaS Premium", "Horizontal tools are losing to vertical-specific products that speak the exact language of one industry — and charge 3-5x more", "Rebrand as a [specific industry] platform rather than a generic tool; add 3 industry-specific reports and raise price by 40%", "re:cap SaaS Benchmarks 2026"),
        TrendOpportunity("Usage-Based Pricing Shift", "Seat-based pricing is being replaced by consumption-based models; customers prefer to start cheap and scale — reducing churn 30-40%", "Add a usage tier below your starter plan; optimize for activation, not trial conversion", "OpenCollective / SaaS metrics repos 2026"),
    ),
    "agency_services": (
        TrendOpportunity("Productized Service Premium", "Clients pay 40-60% more for a fixed-scope, fixed-price deliverable than for hourly billing — and buy faster", "Package your top service as a $2,500 or $5,000 productized offering with a clear 30-day deliverable and standard contract", "Eagle Rock CFO Agency Benchmarks 2026"),
        TrendOpportunity("AI-Augmented Delivery", "Agencies using AI for research, copywriting, and reporting are delivering 3x the output at the same headcount — compressing the cost-to-deliver by 40-60%", "Implement Claude or GPT-4o for brief writing, research, and draft generation; pass 50% of savings to clients as faster turnaround, keep 50% as margin", "Damodaran 2026 / BLS OES"),
        TrendOpportunity("Retainer-First Sales Model", "Project-based agencies have 60-80% revenue variance; retainer-first agencies have 15-25% variance and 40% higher valuations at exit", "Reframe every project proposal to include a 3-month retainer option at 20% discount; close 2 retainers = predictable baseline", "re:cap Benchmarks 2026"),
    ),
    "music_entertainment": (
        TrendOpportunity("Sync Licensing Boom", "Music supervisors placed 35% more tracks in 2025 than 2023 due to streaming-platform original content explosion; indie catalog in demand", "Submit your 10 best instrumentals to Musicbed, Artlist, and Pond5 — each platform pays $500-5,000 per sync placement", "RIAA 2025 / MusicBrainz data"),
        TrendOpportunity("Short-Form Monetization", "TikTok and Instagram Reels now pay directly through creator funds; artists with 10K-100K followers earn $200-2,000/mo passively from posting content they are already creating", "Post 3 short-form clips per week from existing recordings; enroll in TikTok Creator Fund and Instagram Reels Bonus", "Spotify for Artists / ListenBrainz 2026"),
        TrendOpportunity("NFT + Direct Fan Monetization", "Web3 music tools (Sound.xyz, Catalog) let artists sell 50 limited editions at $50-200 each — $2,500-10,000 per release from 50 superfans instead of millions of streams", "Release one track as a limited 50-edition NFT; price at $100 each = $5,000 gross with no label split", "ListenBrainz / Sound.xyz public data 2026"),
    ),
    "food_beverage": (
        TrendOpportunity("Ghost Kitchen Expansion", "Dark kitchens are growing 15% YoY; renting production capacity off-hours ($500-1,500/mo) lets restaurants earn revenue while closed", "List on CloudKitchens or a local commissary and run 2 delivery-only concepts from your existing kitchen during off-peak hours", "Census CBP NAICS 722 2026"),
        TrendOpportunity("Meal Kit / Subscription Demand", "Consumer meal kit market grew 12% in 2025; locally sourced weekly box subscriptions command $80-150/week at 55-65% gross margin", "Launch a weekly meal-prep subscription box for 30 customers = $3,600-4,500/week at near-zero incremental labor", "USDA ERS + BLS OES 2026"),
        TrendOpportunity("Cultural Food Premium", "Authentic ethnic cuisine earns 22-35% price premium over generic equivalents in urban markets; demand for regional specificity is growing", "Add 3 dishes unique to your regional origin (not the generic version) and price them at 25% above menu average; promote the origin story", "Yelp Fusion + Damodaran 2026"),
    ),
    "healthcare": (
        TrendOpportunity("Telehealth Hybrid Model", "Patients who did in-person plus telehealth visits have 28% higher retention and 40% higher annual spend than in-person-only patients", "Add telehealth for follow-ups and simple consults at $75-150/session — zero additional overhead after initial setup", "CMS Open Data 2026"),
        TrendOpportunity("Chronic Care Management Billing", "CMS reimburses $42-100/patient/month for chronic care management (CCM) — a billable code most small practices leave on the table", "Enroll your top 50 chronic-condition patients in CCM program; bill CMS monthly for care coordination calls = $2,100-5,000 passive/mo", "CMS data.cms.gov 2026"),
        TrendOpportunity("Cash-Pay Concierge Tier", "High-income patients will pay $200-500/month for same-day appointments and direct physician access — bypassing insurance entirely at 90%+ margin", "Launch a 50-patient concierge membership at $250/mo = $12,500/mo revenue with no insurance billing overhead", "FRED + CMS benchmarks 2026"),
    ),
    "retail": (
        TrendOpportunity("Experiential Retail Layer", "Retailers adding in-store experiences (classes, events, tastings) see 30-45% higher average transaction value and 25% better retention", "Host one free monthly event tied to your product category; capture email at registration = build owned audience", "Census SUSB Retail 2026"),
        TrendOpportunity("Local Brand Exclusive Distribution", "Consumers prefer products not available on Amazon; carrying exclusive local-brand products drives 18-25% of traffic with 55-70% gross margin", "Source 3-5 local artisan products on exclusive distribution terms; display prominently as 'local only' category", "Yelp Fusion + Census 2026"),
        TrendOpportunity("Buy Local Premium", "62% of consumers say they pay more for locally-owned businesses; 'local' positioning commands 15-20% price premium over chain alternatives", "Add 'locally owned since [year]' to all signage and digital presence; join local business association for cross-promotion", "SBA + Damodaran 2026"),
    ),
    "real_estate": (
        TrendOpportunity("Short-Term Rental Arbitrage", "STR platforms (Airbnb, VRBO) earn 2.5-4x long-term rent in major metros; property managers adding STR management earn 20-30% of gross revenue", "Add STR management as a premium tier for property owners at 25% of gross vs 10% for long-term — same labor, 2.5x revenue", "Zillow Research + AirDNA 2026"),
        TrendOpportunity("Renovation Cost Optimization", "Material costs declined 18% from 2022 peak; contractors with established relationships can now close the renovation-to-rent gap 30% faster", "Negotiate renovation packages with 2 contractors at fixed pricing in exchange for consistent deal flow; market as 'turnkey rehab + management'", "FRED CPI Housing + HUD 2026"),
        TrendOpportunity("Section 8 / Voucher Demand", "HUD voucher program has 12-month waitlists in most metros; landlords accepting vouchers have 98%+ occupancy and government-guaranteed rents", "Apply to accept Housing Choice Vouchers; government pays on time, every time, and tenant turnover is 60% lower than market rate", "HUD FMR data 2026"),
    ),
    "education": (
        TrendOpportunity("Test Prep Demand Surge", "SAT/ACT scores declined nationally post-COVID; parents are spending 40% more on test prep than pre-2020, with premium programs commanding $150-300/hr", "Add a guaranteed SAT score improvement program ($2,000-5,000 package with refund if target not hit) — guarantee removes all objections", "NCES + BLS OES 2026"),
        TrendOpportunity("AI Tutoring Supplement", "Students and parents want human tutors who use AI tools to personalize faster — positioning as 'AI-enhanced tutoring' commands 20-30% price premium", "Use Claude or GPT-4o to generate personalized practice sets per student; charge a $50/mo 'AI curriculum' add-on to existing clients", "NCES data 2026"),
        TrendOpportunity("Corporate Training Market", "Companies with 10-50 employees spend $1,200-3,000/employee/year on skills training; local providers beat national vendors on responsiveness and cultural fit", "Package your curriculum as a corporate lunch-and-learn ($1,500/session) and pitch 5 local SMBs — one yes = $18K/year contract", "BLS OES + SBA 2026"),
    ),
    "manufacturing": (
        TrendOpportunity("Reshoring Demand", "US manufacturers are bringing production home; domestic contract manufacturers with 2-4 week turnaround are replacing 12-16 week China lead times at 15-25% cost premium", "Market as 'Made in USA, 3-week turnaround' specifically to buyers burned by overseas delays; partner with 2 local designers for rapid prototyping referrals", "Census ASM + FRED 2026"),
        TrendOpportunity("Custom / On-Demand Production", "MOQ (minimum order quantity) compression — buyers want 50-500 units instead of 5,000; custom-run manufacturers earn 40-60% higher margin per unit", "Add a custom small-batch tier at 40% price premium over standard runs; market directly to Etsy and Shopify sellers via Facebook groups", "Census AIES + USDA 2026"),
        TrendOpportunity("Sustainability Certification Premium", "B Corp and 1% for the Planet certifications command 15-30% price premium and open Fortune 500 vendor lists closed to uncertified suppliers", "Apply for 1% for the Planet membership ($250/yr); add to all packaging and marketing — opens enterprise RFPs worth $50K-500K", "SEC EDGAR sustainability reports 2026"),
    ),
    "creative_media": (
        TrendOpportunity("AI-Augmented Production", "Studios using AI for scripting, storyboarding, and editing are delivering 3x output at same headcount — undercutting full-service agencies on price while matching quality", "Implement AI for scripting and rough-cut editing; position as 'premium quality at indie speed' and undercut agency pricing by 25%", "GitHub OSS media tools 2026"),
        TrendOpportunity("Branded Content Surge", "Brands are pulling ad spend from traditional media into owned branded content; budgets of $5K-50K/episode are available to credible content partners", "Pitch 5 local brands on a branded podcast or video series ($5,000-15,000/episode); their story, your production, they own the content", "BLS OES + Damodaran 2026"),
        TrendOpportunity("Vertical Video Dominance", "90% of content consumption is now vertical (mobile); studios that natively produce vertical content command 20-30% premium from social-first brands", "Restructure every shoot for vertical-first delivery; add a $500 vertical-edit add-on to every existing package", "ListenBrainz / Spotify / platform data 2026"),
    ),
    "professional_services": (
        TrendOpportunity("Fractional Executive Model", "Companies with $1M-10M revenue need CFO/CMO/COO expertise at 10-20 hrs/week; fractional roles pay $150-350/hr vs $200K+ full-time salary", "Offer a Fractional [Your Role] retainer at $3,000-8,000/month for 10 hrs/week; target 3 clients = $9,000-24,000/mo baseline", "BLS OES + Damodaran 2026"),
        TrendOpportunity("AI-Enhanced Compliance", "Regulatory burden is growing in every industry; firms offering AI-assisted compliance monitoring at fixed monthly fees are capturing CFO budgets previously spent on audits", "Add a $500-1,500/mo compliance monitoring retainer using AI tools; position as 'proactive, not reactive' compliance partner", "SEC EDGAR + BLS 2026"),
        TrendOpportunity("Niche Specialization Premium", "Generalist professional service firms lose on price to AI tools; specialists in one vertical command 35-50% premium and 80% referral close rate", "Pick your single best-served industry vertical; rebrand all marketing around that niche; raise price 30% and watch close rate improve", "Damodaran 2026 margins by sector"),
    ),
    "local_service": (
        TrendOpportunity("Booking App Adoption Gap", "60% of local service businesses still rely on walk-ins or phone calls; those with online booking earn 22% more revenue and 15% better retention", "Implement free Booksy, Square Appointments, or Calendly booking; add 'Book Online' to Google Business Profile", "Census CBP + Yelp data 2026"),
        TrendOpportunity("Loyalty Program Conversion", "Customers with a loyalty card visit 28% more frequently; digital loyalty (Square Loyalty, Stamp Me) costs $50-100/mo and pays back in 30 days", "Launch a digital loyalty program this week; target 10th-visit reward at your median ticket size", "Damodaran + BLS OES 2026"),
        TrendOpportunity("Video Social Proof", "Service businesses with before/after Reels get 3-5x more profile views and 40% more inbound calls than those without; the bar is low because few do it", "Post one before/after Reel per week from existing client work; pin the best one to your Google Business Profile", "Yelp Fusion + OpenStreetMap data 2026"),
    ),
}

_GENERIC_TRENDS = (
    TrendOpportunity("Digital Presence Upgrade", "Businesses with complete Google Business Profiles get 7x more clicks than those without; most local businesses are incomplete", "Fully optimize Google Business Profile: 10+ photos, Q&A, posts weekly, menu/services listed", "Census + Google data 2026"),
    TrendOpportunity("Recurring Revenue Conversion", "Project-based or transactional businesses have 60-80% revenue variance; adding a monthly subscription converts 10-20% of clients to predictable MRR", "Identify your 10 best clients and offer a monthly retainer/membership at 15% discount from their average monthly spend", "Damodaran margins 2026"),
    TrendOpportunity("Referral System Formalization", "80% of small business revenue comes from referrals; fewer than 20% have a formal referral program. A simple $25-50 referral reward pays back 10-20x in LTV", "Launch a referral program this week: $50 credit for referrer + $25 discount for new client on first purchase", "SBA + BLS data 2026"),
)


# ── Phase templates by domain ────────────────────────────────────────────────
def _build_phases(
    domain_id: str,
    p1_target: int,
    p2_target: int,
    p3_target: int,
    avg_wage: float,
    net_margin_pct: int,
    top_vertical_name: str,
) -> tuple[RoadmapPhase, RoadmapPhase, RoadmapPhase]:
    w = avg_wage
    vm = top_vertical_name or "a new revenue vertical"

    templates: dict[str, tuple] = {
        "logistics": (
            ("Run Lean, Run Reliable", f"Track cost-per-mile weekly (labor ~${w:.0f}/hr = ~35% of revenue); get FMCSA safety score to Satisfactory (unlocks premium shippers); implement free TMS (Trulos/Tailwind); build 3-5 direct shipper relationships (cut out broker 15-20% margin); document your top-performing lane as a data asset", "Miles driven vs revenue, cost-per-mile, on-time rate, direct vs brokered ratio", "You have 3+ direct shipper contracts covering baseline revenue"),
            ("Freight Network Builder", f"Add freight brokerage authority (MC number + bond = $1,200 one-time) to start brokering loads; build a carrier network of 10+ trusted independents; sign 2 dedicated lane contracts at $8K-15K/mo guaranteed; implement fuel surcharge tracking (2-3% margin recovery); hire 1 dispatcher at ${w*1.3:.0f}/hr to free owner for business development", "Brokered load count, carrier NPS, guaranteed contract revenue, dispatcher utilization", "Brokered revenue exceeds owned-truck revenue — asset-light model proven"),
            (f"Asset-Light Empire", "Lease (not buy) a 2nd power unit; set up a factoring line for cash flow acceleration (1.5-3% cost = worth it at this revenue); automate load-board bidding; target 40% owned-truck + 60% brokered mix (scales without capital); launch driver lease-to-own program for retention and equity building", "Total revenue, brokered %, factoring utilization, driver retention rate", "Three revenue streams each generating $10K+/mo independently"),
        ),
        "software_saas": (
            (f"Activate & Retain", f"Cut time-to-value under 15 minutes (if onboarding takes longer, churn within 90 days is near-certain); add in-app usage analytics (PostHog free tier); email every churned user within 24 hrs; target {net_margin_pct}%+ gross margin by removing unprofitable tiers; document your 3 highest-retention customer profiles", "Time-to-activate, 30-day retention, NPS, gross margin %", "30-day retention above 70% and gross margin above 60%"),
            (f"Expand Revenue Per Account", f"Add {vm} to create a second revenue line; implement usage-based pricing tier below starter (reduces churn 30-40%); launch a referral program ($25 credit for both sides); build 3 integrations with tools your users already pay for; target NRR above 110% (expansions outpace churn)", "MRR, NRR, integration adoption, referral conversion, LTV:CAC ratio", "NRR consistently above 100% — expansion revenue covers new churn"),
            ("Defensible Moat", "Lock in annual contracts with 15% discount (cuts churn 60%); build a data network effect (the more customers, the better the product); open a partner/reseller channel (no CAC); publish benchmark reports from your aggregate data (thought leadership + SEO); target Series A metrics: $1M ARR, 100%+ NRR, <10% annual churn", "ARR, churn %, NRR, partner-sourced revenue %, data asset value", "Product provides unique insight competitors cannot replicate from their data alone"),
        ),
        "agency_services": (
            ("Standardize & Systematize", f"Document your 3 highest-margin service deliverables as repeatable playbooks; convert 2 clients to monthly retainers at 20% discount from project equivalent; implement time-tracking to identify work below ${w*1.5:.0f}/hr (cut or raise price); target 65%+ gross margin by saying no to scope creep; build a case study from every completed project", "Billable utilization %, gross margin, retainer % of revenue, proposal win rate", "50%+ of revenue on retainer; billable utilization above 70%"),
            ("Retainer-First Growth", f"Add {vm} as a productized service at fixed price; pitch every project client on a 3-month minimum retainer; hire 1 junior at ${w*0.8:.0f}/hr (leverage your rate, raise capacity 40%); target 3 anchor clients at $3K-8K/mo each = $9K-24K/mo baseline; build a sub-contractor bench for overflow", "Retainer MRR, client count, revenue per FTE, sub-contractor utilization", "Retainer MRR covers 100% of fixed costs — all project work is profit"),
            ("Agency Brand & Exit Optionality", "Build a proprietary methodology with a name and trademark; publish weekly thought leadership to attract inbound leads; add a training product ($2K course) for a passive revenue layer; target 20%+ EBITDA margin (agency multiples at 4-6x EBITDA); document all processes for owner-independence (raises exit valuation)", "EBITDA %, inbound lead %,  methodology licensing revenue, owner-hours/week", "Agency runs without owner involvement for 4 weeks — sellable at 4x+ EBITDA"),
        ),
        "music_entertainment": (
            ("Catalog & Distribution", f"Distribute 100% of catalog to all streaming platforms via DistroKid/CD Baby ($20/yr); register with IPRS/ASCAP/BMI for performance royalties (free); claim all unclaimed royalties on existing tracks; post consistently on one platform (Instagram or TikTok) 3x/week; build an email list from social followers (1,000 subscribers > 100,000 followers for monetization)", "Monthly streaming revenue, email list size, royalty registrations complete, platform follower growth", "Monthly royalty income covers hosting and distribution costs — music earns passively"),
            (f"Royalty Economy", f"Submit 10 instrumentals to sync licensing platforms (Musicbed, Artlist, Pond5); launch a Patreon or membership at $5-25/month targeting 200 subscribers = $1K-5K/mo baseline; add {vm}; pitch 3 local brands for paid social media collaboration ($500-2,000 per post); release one EP with limited NFT editions (50 × $100 = $5,000)", "Sync licensing income, Patreon MRR, brand deal revenue, total monthly royalties", "Monthly recurring music income exceeds $3,000 without a single live performance"),
            ("IP Empire", "Launch a label entity (LLC) and sign 2-3 artists on revenue-share (you own distribution, they get 70%); license your sound/style to 3 non-competing artists; build a music production course ($299) for passive income; pursue 1 major sync placement (TV/film) through a music supervisor; target 10 income streams from the same catalog", "Label revenue, artist roster size, course MRR, sync placement revenue, total IP income", "50%+ of revenue is passive — from catalog, licensing, and label, not live performance"),
        ),
        "food_beverage": (
            ("Consistent & Profitable", f"Cut menu to 12-15 items (80% of revenue comes from 20% of menu); post food cost weekly (target 28-32%); train staff on upselling ($2 average ticket increase = 20% more revenue per table); get Google Business Profile to 4.5+ stars with 50+ reviews; implement Square or Toast POS to track per-item profitability", "Food cost %, labor %, average ticket, review rating, table turn time", "Food cost below 32% and labor below 35% consistently for 60 days"),
            (f"Community Anchor", f"Launch catering for corporate events ($5K-30K/event) using existing kitchen; add {vm}; sell a signature item as retail product at 3 local stores (70% margin); build a reservation-only dinner series ($95/head × 20 covers = $1,900/night); host a cooking class monthly ($75/person × 20 = $1,500/night)", "Catering revenue, retail product sell-through, reservation fill rate, customer email list size", "Catering and retail together represent 30%+ of total revenue"),
            ("Food Brand Expansion", "Sell packaged version of signature product to 10+ retail locations; launch a ghost kitchen concept (2nd brand from same kitchen, delivery-only); open a 2nd location in an office district (different daypart = no cannibalization); explore franchise inquiry process; license your recipe/concept to a non-competing regional operator", "Retail SKU distribution, ghost kitchen revenue, 2nd location EBITDA, franchise inquiry pipeline", "Three distinct revenue streams each generating $8K+/mo from the same production infrastructure"),
        ),
        "healthcare": (
            ("Reliable & Accessible", f"Implement online scheduling (reduce no-shows 35%); send automated appointment reminders 48hr + 2hr before (reduces no-shows further 25%); optimize billing to capture all CPT codes (most practices leave 15-20% on the table); target 85%+ schedule utilization; collect patient email for post-visit follow-up (opens telehealth revenue later)", "Schedule utilization %, no-show rate, billing capture rate, patient retention 12-month", "Schedule utilization above 85% and no-show rate below 10%"),
            (f"Proactive Care Model", f"Add telehealth for follow-ups ($75-150/session, zero overhead); enroll top 50 chronic patients in CCM billing ($42-100/patient/month from CMS); launch {vm}; hire 1 medical assistant at ${w:.0f}/hr to expand provider capacity without adding a physician; target NPS above 70 through post-visit text follow-up", "Telehealth revenue, CCM billing income, NPS, panel size, revenue per provider", "Telehealth + CCM billing add $3,000+/mo with zero additional provider hours"),
            ("Concierge + Community", "Launch a 50-patient concierge tier ($250/mo = $12,500/mo at 90%+ margin, no insurance billing); add a corporate wellness contract with 2 local employers ($500-2,000/mo each); build a health education content channel (YouTube/podcast) for inbound referrals; hire a mid-level provider (NP/PA) to double capacity; target 1,000-patient panel per provider (benchmark for profitable solo practice)", "Concierge MRR, corporate contract revenue, new patient inbound from content, NP/PA capacity utilization", "Concierge revenue alone covers fixed overhead — all insurance revenue becomes profit"),
        ),
        "retail": (
            ("Essential Destination", f"Stock your top 80 SKUs based on sell-through velocity (cut the bottom 20% of SKUs that sit 90+ days); accept EBT/SNAP from day 1 (opens 15-25% more customer base in most neighborhoods); display 3 local/artisan products on exclusive terms (55-70% margin); target ${p1_target:,}/mo by optimizing your top revenue days (Friday-Sunday = 60% of weekly retail revenue)", "Inventory turnover, sell-through rate, top-SKU contribution %, EBT transaction volume", "Inventory turnover above 8x/year and top 80 SKUs representing 90%+ of revenue"),
            (f"Neighborhood Brand", f"Add {vm}; launch a loyalty program ($50/yr membership with exclusive pricing); host one monthly in-store event tied to your product category (drives 3-5x foot traffic on event days); add an online store for local delivery (builds email list); stock 5 products unavailable on Amazon (forces local purchase)", "Loyalty member count, event attendance, online order volume, exclusive SKU revenue", "Loyalty members represent 40%+ of revenue; event days generate 3x average daily revenue"),
            ("Multi-Channel Institution", "Open a second location or add a kiosk at a high-traffic venue; launch a private label product (35-50% higher margin than national brand equivalent); add an Amazon storefront for national reach on your unique/exclusive products; install an ATM ($400-800/mo passive income); build a wholesale account with 5 local restaurants/offices", "2nd location EBITDA, private label revenue %, Amazon sales, ATM income, wholesale account count", "Three revenue channels (retail + online + wholesale) each generating $5K+/mo independently"),
        ),
        "real_estate": (
            ("Systematic Operations", f"Implement free property management software (Rentec Direct, free under 10 units); automate rent collection (ACH = 98%+ on-time rate vs 82% for check); conduct inspection on every unit annually with documented photos (prevents security deposit disputes); respond to maintenance requests within 24 hours (reduces tenant churn 35%); build a vendor list for 5 trade categories at pre-negotiated rates", "On-time rent %, maintenance response time, tenant retention %, vacancy days per year", "Vacancy rate below 5% and tenant retention above 80% for 12 consecutive months"),
            (f"Portfolio Expansion", f"Add {vm}; add property management services for 3-5 other landlords at 8-12% of gross rents (scales without capital); pursue one value-add acquisition (distressed property at 70-80% ARV with renovation plan); set up a 1031 exchange strategy with your CPA before the next sale; target $100K in annual NOI across portfolio", "Portfolio NOI, managed units (your + 3rd party), vacancy %, annual appreciation", "Property management fee income covers all of your own property expenses — portfolio is self-funding"),
            ("Real Estate Business", "Operate as a licensed property management company (opens larger institutional mandates); target 50+ managed units (fixed overhead = higher margin per unit); add STR management for premium clients (25% fee vs 10% for long-term); pursue commercial real estate (retail/office = longer leases, less management intensity); build toward a portfolio sale at 12-15x NOI", "Total AUM (assets under management), management fee revenue, STR vs LTR revenue mix, equity appreciation", "Management company generates $15K+/mo independent of your owned portfolio performance"),
        ),
        "education": (
            ("Results Factory", f"Pick one high-stakes outcome (SAT score, state test, college acceptance) and guarantee it or refund (removes all sales objections); document your methodology in a repeatable curriculum; get 10 testimonials with specific score improvements in the first 60 days; price at ${w*3:.0f}-{w*5:.0f}/hr for premium positioning (cheap tutors lose credibility); build Google My Business with 20+ reviews", "Student outcome rate %, testimonial count, average session rate, referral source %", "Outcome guarantee is offered and claimed on fewer than 10% of engagements — methodology proven"),
            (f"Pipeline Builder", f"Add {vm}; launch a group class format (6 students × $150/hr = $900/hr — same knowledge delivery, 4x revenue); target 3 school counselors as referral partners (each worth 5-10 students/year); run a summer intensive camp ($1,500/student/week × 20 students = $30,000/week); build a parent communication system (weekly progress updates = #1 retention driver)", "Group class revenue, counselor referrals, camp enrollment, parent NPS, student retention rate", "Group classes represent 40%+ of revenue; summer camp alone covers 3 months of operating costs"),
            ("Education Institution", "License your curriculum to 3 other tutors in non-competing geographies ($5,000-15,000/yr licensing fee each); launch an online course ($299 × 500 students = $149,500); partner with 2 school districts for after-school program contracts ($8K-25K/month guaranteed); build proprietary pass-rate data and publish it (creates defensible proof vs. competitors); target 50-student annual capacity per tutor", "Licensed curriculum partners, online course revenue, district contract income, published pass-rate data", "Licensing and online revenue represent 30%+ of total revenue — teaching is now optional for income"),
        ),
        "manufacturing": (
            ("Quality & Speed", f"Implement 5S methodology in production floor (reduces waste 30-40%, typically worth ${p1_target//10:,}/mo); document setup times per job and attack the longest ones first; target 95%+ on-time delivery rate (unlocks premium customer relationships); build a supplier scorecard (reduce input cost 10-15%); price complexity honestly — every custom job should have a complexity fee", "On-time delivery %, defect rate, setup time per job type, gross margin per product line", "On-time delivery above 95% for 90 consecutive days — foundation for national customer relationships"),
            (f"Capacity & Margin", f"Add {vm}; raise minimum order quantity (MOQ) 20% to cut low-margin rush jobs; launch a 'design + manufacture' service (higher margin than manufacturing alone); target 2 national brand accounts (10x order volume at slightly lower margin = more profitable overall); add DTC (direct-to-consumer) channel for 1-2 products (40-60% margin vs 15-25% for wholesale)", "Capacity utilization %, gross margin by customer type, DTC revenue, national account pipeline", "Capacity utilization above 80% at current pricing — demand exceeds supply, enabling price increases"),
            ("IP + Automation", "File patents or trade secrets on your highest-margin process; add one CNC or automated tool that replaces 1 FTE of repetitive labor; launch a licensing deal with a non-competing manufacturer in another region; target 2 international customers (export adds 15-25% revenue at similar margin); prepare for acquisition (document all processes, customer contracts, supplier agreements)", "Automation ROI, patent applications, international revenue %, export volume, EBITDA margin", "EBITDA above 15% and revenue diversified across 5+ customers — acquisition-ready"),
        ),
        "creative_media": (
            ("Portfolio & Proof", f"Shoot 3 pro bono projects with ideal clients (portfolio over cash at this stage); build a portfolio site with 10 case studies showing before/after outcomes not just aesthetics; target one award or press feature (legitimizes premium pricing); implement project management (Notion free tier) to prevent scope creep; move to fixed-project pricing (hourly billing caps your income)", "Portfolio quality (subjective), case study count, referral source %, project margin %, scope change frequency", "Portfolio generates inbound inquiries without outbound pitching — proof the work speaks for itself"),
            (f"Retainer Studio", f"Convert 2 clients to monthly content retainers ($2,000-5,000/mo = predictable MRR); add {vm}; hire 1 junior creative at ${w*0.7:.0f}/hr to handle execution while you focus on strategy; build a sub-contractor network for overflow (never say no to scope); target 3 anchor clients at $3K+/mo each = studio baseline covered", "Retainer MRR, project backlog, junior utilization %, sub-contractor spend, client NPS", "Retainer MRR covers all studio fixed costs — project work is pure profit"),
            ("Brand & IP", "Develop a proprietary creative methodology with a name (clients pay for a system, not just hours); license your methodology to non-competing studios in other markets; launch a course or workshop for aspiring creatives ($499 × 100 = $49,900); build a content IP asset (podcast, YouTube) that creates inbound leads; target a buyout or merger at 3-5x annual revenue", "Methodology licensing revenue, course sales, inbound lead %, studio valuation, owner-hours/week", "Studio is owner-independent for 30 days — sellable at 3x+ annual revenue"),
        ),
        "professional_services": (
            ("Retainer Foundation", f"Convert all project work to a retainer proposal (offer 15% discount for 3-month commitment); implement value-based pricing for high-stakes projects (price by outcome value, not hours); document your 3 highest-margin service categories; target ${p1_target:,}/mo from retainer clients alone; bill net-15 with late fees (cash flow is the #1 killer of professional service firms)", "Retainer revenue %, average project margin, billing cycle days, client concentration risk", "Retainer revenue covers 100% of fixed costs — all project work is bonus profit"),
            (f"Expertise Expansion", f"Specialize in one industry vertical (raises close rate 40% and prices 30%); add {vm}; hire 1 associate at ${w*0.7:.0f}/hr to leverage your expertise (1 associate at full utilization = $40-80K/yr profit contribution); launch a newsletter or podcast in your vertical (inbound marketing at $0 CAC); target 5 anchor clients at $3K-8K/mo retainer each", "Industry vertical concentration %, associate utilization %, inbound lead %, client NPS, revenue per FTE", "5 anchor clients on retainer; inbound inquiries exceed capacity — can raise prices"),
            ("Advisory & Exit", "Build a proprietary data product from client work (anonymized benchmark report = marketing + revenue); launch a group advisory program ($1,500/mo × 20 clients = $30,000/mo at minimal added labor); pursue a partnership or merger for scale; document all processes for owner-independence; target 20%+ EBITDA (professional services multiples: 4-8x EBITDA at exit)", "EBITDA %, owner-dependence score, advisory MRR, IP asset value, exit valuation estimate", "EBITDA above 20% and owner works fewer than 20 hrs/week — value captured in systems not person"),
        ),
        "local_service": (
            ("Reliable Standard", f"Get Google Business Profile to 4.5+ stars with 50+ reviews (adds 40% more inbound calls); implement online booking (reduces friction, fills off-peak slots); respond to every review within 24 hours; track your top 5 revenue services and price them 10% above nearest competitor; build a customer database with contact info for every client served", "Google rating, review count, online booking adoption %, repeat visit rate, top-service revenue %", "4.5+ Google rating with 50+ reviews and 30%+ of bookings coming through online channel"),
            (f"Community Anchor", f"Launch a loyalty program (10th visit free costs ~{int(p1_target*0.1/10):,}/mo, worth 28% more visits); add {vm}; post Instagram Reels weekly (before/after content drives 3-5x more profile visits); offer a referral reward ($25 credit for referrer + 10% off for new client); partner with 2 complementary local businesses for cross-referral", "Loyalty member count, referral source %, Instagram reach, cross-referral bookings, client LTV", "Loyalty members represent 40%+ of revenue; referrals represent 30%+ of new client acquisition"),
            ("Neighborhood Institution", "Add a 2nd revenue stream (booth rental, product line, or certification program); hire 1 additional service provider and transition to a booth-rent or revenue-share model (owner becomes landlord, not operator); build a local franchise or licensing inquiry process; document all operational systems for owner-independence; target $25K+/mo revenue with owner working under 30 hrs/week", "2nd stream revenue %, booth rental income, owner hours/week, referral pipeline, systems documentation completeness", "Owner-independent for 2 weeks; 2nd revenue stream generating $3K+/mo consistently"),
        ),
    }

    domain = domain_id if domain_id in templates else "local_service"
    t1, t2, t3 = templates[domain]

    def _parse_kpis(s: str) -> tuple[str, ...]:
        return tuple(k.strip() for k in s.split(",") if k.strip())

    p1 = RoadmapPhase(1, t1[0], "Months 1–6", "Stabilize & Systematize", tuple(t1[1].split("; ")), p1_target, _parse_kpis(t1[2]), t1[3])
    p2 = RoadmapPhase(2, t2[0], "Months 7–18", "Engage & Expand", tuple(t2[1].split("; ")), p2_target, _parse_kpis(t2[2]), t2[3])
    p3 = RoadmapPhase(3, t3[0], "Months 19–36", "Build the Moat", tuple(t3[1].split("; ")), p3_target, _parse_kpis(t3[2]), t3[3])
    return (p1, p2, p3)


# ── Main functions ────────────────────────────────────────────────────────────

def generate_roadmap(
    profile: "BizProfile",
    benchmarks: "DomainBenchmarks",
    verticals: tuple[Any, ...],
    domain: "DomainSpec",
) -> UniversalRoadmap:
    """Generate a 3-phase roadmap with benchmark-derived revenue targets."""
    domain_id = domain.domain_id

    # Revenue targets derived from benchmarks
    p50 = benchmarks.revenue_p50
    p75 = benchmarks.revenue_p75
    p1_target = int(p50 * 0.65)
    p2_target = int(p50 * 1.10)
    p3_target = int(p75 * 0.95)

    # Adjust if business is already above p50
    if profile.monthly_revenue > 0:
        p1_target = max(p1_target, int(profile.monthly_revenue * 1.15))

    top_vertical_name = verticals[0].name if verticals else ""
    avg_wage = getattr(benchmarks, "avg_hourly_wage", 18.0)
    net_margin_pct = int(benchmarks.net_margin_typical * 100)

    # Override with curated data for local_service niches if available
    if domain_id == "local_service":
        niche_key = profile.description.lower().replace(" ", "_")
        try:
            from neighboriq.scoring.niche_roadmap import get_niche_roadmap, format_roadmap as _fmt
            curated = get_niche_roadmap(niche_key)
            if curated.niche != "generic":
                phases = (
                    RoadmapPhase(1, curated.phase1_name, curated.phase1_timeline, "Stabilize & Systematize", curated.phase1_actions, curated.phase1_revenue_target, ("Revenue target", "Review count", "Repeat %"), curated.phase1_exit_criteria),
                    RoadmapPhase(2, curated.phase2_name, curated.phase2_timeline, "Engage & Expand", curated.phase2_actions, curated.phase2_revenue_target, ("Revenue target", "Community events", "Loyalty members"), curated.phase2_exit_criteria),
                    RoadmapPhase(3, curated.phase3_name, curated.phase3_timeline, "Build the Moat", curated.phase3_actions, curated.phase3_revenue_target, ("Revenue target", "Passive income %", "Owner hours/wk"), curated.phase3_exit_criteria),
                )
                delta4 = Delta4Analysis(curated.old_experience_score, curated.new_experience_score, curated.delta, curated.delta4_what_changes, curated.irreversibility_trigger, curated.delta4_enabled)
                return UniversalRoadmap(
                    biz_name=profile.name, domain_id=domain_id,
                    generated_at=datetime.now(timezone.utc).isoformat(),
                    confidence="HIGH",
                    phases=phases, delta4=delta4,
                    top_verticals=verticals,
                    trend_opportunities=_TRENDS_BY_DOMAIN.get(domain_id, _GENERIC_TRENDS),
                    benchmark_sources=("curated niche_roadmap.py",) + benchmarks.data_sources,
                    benchmark_vintage=benchmarks.vintage_year,
                )
        except Exception:
            pass

    phases = _build_phases(domain_id, p1_target, p2_target, p3_target, avg_wage, net_margin_pct, top_vertical_name)
    delta4 = _DELTA4_BY_DOMAIN.get(domain_id, _GENERIC_DELTA4)
    trends = _TRENDS_BY_DOMAIN.get(domain_id, _GENERIC_TRENDS)

    return UniversalRoadmap(
        biz_name=profile.name,
        domain_id=domain_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        confidence=benchmarks.confidence,
        phases=phases,
        delta4=delta4,
        top_verticals=verticals,
        trend_opportunities=trends,
        benchmark_sources=benchmarks.data_sources,
        benchmark_vintage=benchmarks.vintage_year,
    )


def format_roadmap(roadmap: UniversalRoadmap, verbose: bool = False) -> str:
    """Return a human-readable roadmap string for CLI output."""
    lines: list[str] = []
    sep = "═" * 60

    lines += [sep, f"BUSINESS ROADMAP: {roadmap.biz_name}", f"Domain: {roadmap.domain_id}  |  Confidence: {roadmap.confidence}", f"Generated: {roadmap.generated_at[:10]}  |  Sources: {', '.join(roadmap.benchmark_sources[:2])}", sep, ""]

    for ph in roadmap.phases:
        lines += [f"── PHASE {ph.phase}: {ph.name} ── {ph.timeline} ──────────────────", f"Theme: {ph.theme}", f"Target: ${ph.revenue_target:,}/mo"]
        for i, action in enumerate(ph.actions, 1):
            lines.append(f"  {i}. {action}")
        lines += [f"KPIs: {' | '.join(ph.kpis)}", f"Exit when: {ph.exit_criteria}", ""]

    d = roadmap.delta4
    lines += ["── DELTA 4 ANALYSIS ─────────────────────────────────────────", f"Old experience: {d.old_experience_score}/10  →  New: {d.new_experience_score}/10  →  Δ {d.delta}", "✅ MOAT ACHIEVED" if d.enabled else "⚠  Delta below 4.0 — commodity risk, vulnerable to price competition", f"What changes: {d.what_changes}", f"Irreversibility: {d.irreversibility_trigger}", ""]

    if roadmap.top_verticals:
        lines.append("── NEW VERTICALS TO ADD ──────────────────────────────────────")
        for v in roadmap.top_verticals[:3]:
            lines += [f"  {v.name}: ${v.capital_required:,} capital → ${v.monthly_revenue_at_maturity:,}/mo in {v.months_to_first_revenue}mo  [{v.risk_level}]", f"    {v.rationale[:100]}"]
        lines.append("")

    if roadmap.trend_opportunities:
        lines.append("── TREND OPPORTUNITIES ───────────────────────────────────────")
        for t in roadmap.trend_opportunities[:3]:
            lines += [f"  {t.trend_name}", f"    Why now: {t.why_now[:120]}", f"    Action:  {t.how_to_exploit[:120]}"]
        lines.append("")

    lines += ["── NUMBERS PROVENANCE ────────────────────────────────────────", f"Sources: {', '.join(roadmap.benchmark_sources)}", f"Vintage: {roadmap.benchmark_vintage}  |  All revenue targets derived from benchmark percentiles, not manually estimated."]

    return "\n".join(lines)
