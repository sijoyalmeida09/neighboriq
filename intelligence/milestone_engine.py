"""milestone_engine.py — Date-stamped growth forecasts with TAM/SAM/SOM market sizing.

Replaces vague "Phase 1: months 0-6" with exact calendar dates, weekly actions,
go/no-go signals, and market sizing math derived from real benchmark data.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neighboriq.intelligence.biz_profile import BizProfile
    from neighboriq.intelligence.benchmark_engine import DomainBenchmarks
    from neighboriq.intelligence.domain_taxonomy import DomainSpec

__all__ = [
    "WeeklyMilestone",
    "MonthlyTarget",
    "MarketSizing",
    "GrowthForecast",
    "generate_forecast",
    "format_forecast",
]

_US_POPULATION = 335_000_000

_TAM_USD: dict[str, int] = {
    "food_beverage":          890_000_000_000,
    "healthcare":           4_500_000_000_000,
    "logistics":            1_640_000_000_000,
    "distribution":         8_000_000_000_000,
    "software_saas":          700_000_000_000,
    "agency_services":        455_000_000_000,
    "music_entertainment":     26_000_000_000,
    "retail":               7_500_000_000_000,
    "real_estate":          3_800_000_000_000,
    "education":            1_800_000_000_000,
    "local_service":          500_000_000_000,
    "manufacturing":        2_300_000_000_000,
    "creative_media":         120_000_000_000,
    "professional_services":2_100_000_000_000,
}

_MARKET_PHASE: dict[str, str] = {
    "software_saas":       "growing",
    "logistics":           "disrupted",
    "music_entertainment": "disrupted",
    "healthcare":          "growing",
    "real_estate":         "mature",
    "food_beverage":       "mature",
    "retail":              "disrupted",
    "education":           "growing",
    "agency_services":     "growing",
    "local_service":       "mature",
    "distribution":        "mature",
    "manufacturing":       "mature",
    "creative_media":      "growing",
    "professional_services":"mature",
}

_KEY_METRIC_LABEL: dict[str, str] = {
    "software_saas":       "MRR ($)",
    "logistics":           "loads/mo",
    "food_beverage":       "covers/day",
    "music_entertainment": "streams/mo",
    "healthcare":          "patients/mo",
    "real_estate":         "listings/mo",
    "retail":              "transactions/mo",
    "education":           "students/mo",
    "agency_services":     "active clients",
    "local_service":       "clients/mo",
    "distribution":        "orders/mo",
    "manufacturing":       "units/mo",
    "creative_media":      "subscribers",
    "professional_services":"active engagements",
}

_NOVEL_OPPORTUNITIES: dict[str, tuple[str, ...]] = {
    "logistics": (
        "Freight brokerage authority (MC+bond $1,200) — earn $800-2,000/load margin with zero truck cost",
        "SBA Express Loan packaging for owner-operators — 1-3% referral fee on $50K-350K loans",
        "DOT compliance consulting for small fleets — $200-500/mo retainer, sell to drivers you know",
        "Dead-mile sublease — sell empty backhaul space via uShip or Direct Freight ($150-400/load)",
    ),
    "software_saas": (
        "LLM API reselling — mark up DeepSeek/Gemini calls 3x for non-technical clients via proxy",
        "White-label your product for agency resell — 30% revenue share, zero new sales effort",
        "Usage-based upgrade upsell at limit — deploy in-app prompt, 3-8% upgrade rate documented",
        "AI agent wrapper — add Claude/GPT-4o to existing tool, charge 2x for 'AI tier'",
    ),
    "music_entertainment": (
        "SoundExchange + MLC royalty claim — average artist has $500-5,000 unclaimed from 2020-2024",
        "Sync licensing via Musicbed/Artlist — one placement = $500-5,000 passive income",
        "YouTube Content ID — monetize your catalog on 500M+ videos using others' music",
        "Suno/Udio AI production at $10/track cost, sell via CD Baby → IPRS → ₹117K ceiling proven",
    ),
    "food_beverage": (
        "Ghost kitchen brand — run 2nd brand from same kitchen via Uber Eats/DoorDash with zero rent",
        "B2B catering account with 1 office building — $500-2,000/mo guaranteed, zero marketing",
        "VIP loyalty membership $45/mo — 20 members = $900/mo pure recurring revenue",
        "ATM placement — net $200-400/mo passive per machine, bank supplies equipment",
    ),
    "healthcare": (
        "Medicare CCM billing — chronic care management pays $42-100/patient/mo for 20-min calls",
        "R&D Tax Credit — healthcare software/process improvements qualify; 6-8% of qualifying spend",
        "Telemedicine add-on — existing patients, new revenue stream, no real estate cost",
        "Medical billing audit — 30% of claims underpaid; recover on contingency 15-25% of recoveries",
    ),
    "retail": (
        "ATM placement — $200-400/mo net passive per machine, supplier installs free",
        "5G small cell leasing — $1,000-3,000/mo to carriers for roof/wall mount on your building",
        "Amazon FBA from your existing inventory — reach 200M Prime customers overnight",
        "Unclaimed property recovery service for vendors — 10-15% of recovered funds as fee",
    ),
    "local_service": (
        "AI scheduling agent ($200-500/mo) — replace manual booking, sell to peers in same trade",
        "Equipment idle-time rental — rent tools/equipment during off-hours via Fat Llama",
        "Insurance referral program — $50-200/referral for auto/home policies from your client base",
        "Branded app with loyalty rewards — reduce Yelp/Google dependency, own the relationship",
    ),
    "real_estate": (
        "Property management SaaS — build once, sell to 50 landlords at $99/mo = $5K MRR",
        "Unclaimed security deposit recovery — help tenants; 20% contingency fee",
        "Short-term rental arbitrage — master lease + Airbnb sub-lease, owner's permission required",
        "1031 exchange coordination — refer investors to qualified intermediaries, $500-1,000/referral",
    ),
    "education": (
        "Online course repackaging — convert 1:1 tutoring into async Udemy/Teachable course",
        "School district contract — B2B beats B2C; 1 contract = 500 students, stable revenue",
        "AI tutoring agent — deploy Khan Academy-style AI, charge $25/mo vs $80/hr human tutor",
        "Corporate L&D contract — companies pay $5K-50K for employee training cohorts",
    ),
    "agency_services": (
        "White-label productized service — package one repeatable service, sell to 10 agencies",
        "Retainer-first pricing — stop project work; 5 clients × $3K/mo = $15K predictable MRR",
        "AI content factory — Suno + Claude + CapCut pipeline; sell output not labor",
        "Performance-based fee tier — charge base + % of results; attracts higher-value clients",
    ),
    "distribution": (
        "Freight brokerage add-on — broker loads you don't carry yourself; 15-20% margin",
        "Vendor financing arbitrage — net-60 from suppliers + net-30 from buyers = float profit",
        "Private-label product line — distribute others' goods + your own brand at 2x margin",
        "SBA loan packaging for small retailers — 1-3% referral on $50K-500K loans",
    ),
    "manufacturing": (
        "Equipment idle-time rental — CNC/laser time at $80-200/hr to local makers",
        "R&D Tax Credit — 6-8% of qualifying manufacturing process improvements",
        "Contract manufacturing for e-commerce brands — DTC brands need production but not factories",
        "ISO certification consulting — certify others in your specialty; $500-2,000/client",
    ),
    "creative_media": (
        "Sync licensing — one TV/ad placement = $500-50,000 one-time",
        "YouTube Content ID — passive royalties on user-generated content using your IP",
        "Brand ambassador retainer — $500-3,000/mo for consistent creator partnerships",
        "Course/template productization — sell what you already know, not just what you create",
    ),
    "professional_services": (
        "Retainer productization — convert project fees to $3K-8K/mo recurring advisory",
        "R&D Tax Credit recovery — audit clients' past 3 years; 1-3% contingency fee on refunds",
        "SBA/grant application packaging — 1-3% of loan amount for preparation services",
        "White-label your expertise — other firms resell your specialty under their brand",
    ),
}


# ── Weekly milestone templates ────────────────────────────────────────────────

_WEEKLY_TEMPLATES: dict[str, list[dict]] = {
    "logistics": [
        {"theme": "Foundation", "actions": ("Register FMCSA portal, pull your Safety Rating report", "Map your top 5 lanes by volume and calculate cost-per-mile for each"), "rev": 0, "go": "Safety rating pulled, lanes mapped", "nogo": "Outstanding violations → resolve before any marketing", "cost": 0},
        {"theme": "First Revenue", "actions": ("Cold email 5 shippers on your best lane: 'guaranteed 24hr response, $X/mile'", "Post on DAT/TruckStop free boards for that lane"), "rev": 3000, "go": "1 shipper callback received", "nogo": "0 callbacks → rewrite subject line, lower minimum commitment", "cost": 50},
        {"theme": "Foundation", "actions": ("Install Trulos or Tailwind TMS free tier, enter all existing loads", "Set up Quickbooks Self-Employed or Wave free for P&L tracking"), "rev": 800, "go": "First load entered in TMS", "nogo": "Skip if already have TMS — spend week on direct shipper outreach instead", "cost": 0},
        {"theme": "Optimization", "actions": ("Calculate exact cost-per-mile on last 30 loads from TMS data", "Flag any lane priced under your break-even CPM — those get a price increase this week"), "rev": 1500, "go": "Spreadsheet complete with break-even per lane", "nogo": "Missing data for >50% of loads → fix data entry first", "cost": 0},
        {"theme": "Vertical Unlock", "actions": ("Apply for FMCSA Broker Authority (MC + $75K bond = ~$1,200 one-time)", "Open dedicated broker operating bank account"), "rev": 0, "go": "Application submitted", "nogo": "Defer to Week 8 if cash is tight — use week for direct shipper calls", "cost": 1200},
        {"theme": "Scale", "actions": ("Get 3 direct shipper contracts (vs spot market) at fixed rate + guaranteed volume", "Offer net-30 invoicing as incentive for first-time direct shippers"), "rev": 5500, "go": "1 signed direct shipper contract", "nogo": "0 signed → lower volume minimum, offer 1 free load trial", "cost": 0},
        {"theme": "Leverage", "actions": ("Hire 1 remote dispatcher ($15-18/hr) to take 80% of load coordination", "Write 1-page dispatcher SOP so you can be in sales mode"), "rev": 2000, "go": "First load dispatched by them without your input", "nogo": "Quality issues → 1 additional training week before next hire", "cost": 2600},
        {"theme": "Brokerage", "actions": ("Make first brokered load (if broker authority landed from Week 5)", "If authority still pending: book 2 additional direct shipper contracts"), "rev": 1200, "go": "First broker invoice sent OR 2 new direct contracts signed", "nogo": "Authority pending → spot load instead, bank the cash", "cost": 0},
        {"theme": "Network", "actions": ("Build 'preferred carrier' relationships with 5 independents — get W-9s in TMS", "Offer preferred carriers guaranteed weekly load in exchange for rate lock"), "rev": 1800, "go": "5 carriers in TMS with W-9s on file", "nogo": "< 5 carriers → spend extra day on Facebook trucking groups", "cost": 0},
        {"theme": "Margin", "actions": ("Implement fuel surcharge matrix tied to weekly DOE diesel index", "Invoice all existing shippers with FSC starting this week"), "rev": 1200, "go": "First FSC line-item invoiced and paid", "nogo": "Shipper pushback → reduce to 50% pass-through as concession", "cost": 0},
        {"theme": "Review", "actions": ("Pull 90-day P&L: if broker margin > 15% of gross revenue → double brokerage this month", "Calculate revenue per truck per week — must be ≥ $4,000 to justify each unit"), "rev": 0, "go": "Decision made: scale brokerage vs. scale assets", "nogo": "Revenue/truck < $4K → sell/park worst performer, redeploy capital", "cost": 0},
        {"theme": "Scale Decision", "actions": ("Month 3 checkpoint: review gross vs benchmark target", "Hire/don't hire decision: if MoM growth > 20% last 2 months → hire second dispatcher"), "rev": 0, "go": "Written plan for next 90 days", "nogo": "< 10% MoM growth → revisit lane strategy before adding headcount", "cost": 0},
    ],
    "software_saas": [
        {"theme": "Foundation", "actions": ("Set up MRR/ARR tracking in ChartMogul free tier or Baremetrics free", "Tag all customers by plan tier and signup date in your database"), "rev": 0, "go": "First invoice shows in MRR dashboard", "nogo": "No invoicing system yet → set up Stripe + ChartMogul this week", "cost": 0},
        {"theme": "Analytics", "actions": ("Install PostHog (free, open-source) for product analytics — 5 core events", "Identify top 3 features by usage and map them to paid vs free tier users"), "rev": 0, "go": "10+ events tracked, retention cohort visible", "nogo": "< 10 events → add tracking before any UX changes", "cost": 0},
        {"theme": "Customer Intel", "actions": ("Email all users who logged in 3+ times: offer 15-min call, ask about top pain point", "Document verbatim answers from every call — quote mine for landing page copy"), "rev": 500, "go": "3 customer calls completed with notes", "nogo": "0 responses → personalize subject line with their company name", "cost": 0},
        {"theme": "Hero Feature", "actions": ("Identify the 1 feature that 80% of paying users use weekly", "Rebuild landing page hero section around that feature with real customer quote"), "rev": 800, "go": "Landing page updated with feature-led messaging", "nogo": "No clear hero feature → run 2-week feature flag experiment", "cost": 0},
        {"theme": "Cash Flow", "actions": ("Add annual plan at 20% discount (2 months free framing)", "Email all monthly subscribers personally about annual option"), "rev": 2000, "go": "1 annual upgrade received", "nogo": "0 upgrades → add countdown timer or limit annual slots to 10", "cost": 0},
        {"theme": "Pipeline", "actions": ("Cold outreach to 20 ICP companies via Apollo free (50 exports/mo) + LinkedIn", "Personalize each email with 1 sentence about their specific use case"), "rev": 3500, "go": "2 demo calls booked", "nogo": "0 demos → shorten email to 3 sentences max, A/B test subject lines", "cost": 0},
        {"theme": "Expansion", "actions": ("Deploy in-app upgrade prompt when user hits 80% of free tier limit", "A/B test 2 CTA variations: 'Upgrade' vs 'Unlock [Feature]'"), "rev": 1200, "go": "Prompt live; upgrade rate > 0% in first 7 days", "nogo": "0 upgrades → check if limit is too high — lower trigger to 60%", "cost": 0},
        {"theme": "Referral", "actions": ("Set up Rewardful ($49/mo) with 30% lifetime referral commission", "Email top 10 power users with personal referral link and ask"), "rev": 1000, "go": "1 referral signup received", "nogo": "0 referrals → raise commission to 40% for first 30 days", "cost": 49},
        {"theme": "SEO", "actions": ("Write 1 SEO article: 'How [ICP job title] does [top pain point]' — 1,500+ words", "Publish to your domain + submit to 3 newsletters in your niche"), "rev": 0, "go": "Article live, submitted, and indexed by Google", "nogo": "No time → hire a writer at $100-200 on Contra — still your best long-term bet", "cost": 200},
        {"theme": "Retention", "actions": ("Integrate with top 3 tools your customers use (Zapier webhooks + Slack + HubSpot)", "Send email to all users about new integrations — drives re-engagement"), "rev": 800, "go": "3 integrations live; 1 customer uses each", "nogo": "Integrations too complex → use Zapier app instead of native", "cost": 0},
        {"theme": "Pricing", "actions": ("Raise prices 20% for new customers ONLY (grandfather existing)", "Update pricing page with new prices + 'current customers locked in' note"), "rev": 1500, "go": "New price live; no customer churn in 30 days", "nogo": "Churn spike > 5% → revert for new customers, keep existing raise", "cost": 0},
        {"theme": "Scale Decision", "actions": ("Calculate LTV:CAC — must be > 3:1 to scale paid ads", "If > 3:1: set $500/mo Google Ads budget targeting your ICP search terms"), "rev": 0, "go": "LTV:CAC documented, ad decision made", "nogo": "< 3:1 → fix churn before adding fuel to a leaky bucket", "cost": 500},
    ],
    "music_entertainment": [
        {"theme": "Royalty Unlock", "actions": ("Register on SoundExchange.com + TheMLC.com — both free, takes 30 min each", "Claim your artist profile on every streaming platform DSP portal"), "rev": 400, "go": "Both registrations complete", "nogo": "Name conflict on SoundExchange → submit correction form before proceeding", "cost": 0},
        {"theme": "PRO Registration", "actions": ("Register all works on ASCAP or BMI (pick one; cost $0-150)", "If India connection: register on IPRS.org same week"), "rev": 300, "go": "All existing works registered with at least 1 PRO", "nogo": "Catalog > 100 tracks → bulk register, do 20/day", "cost": 150},
        {"theme": "Distribution", "actions": ("Upload entire catalog to DistroKid ($22/yr) or TuneCore if not live", "Claim artist profiles on Spotify for Artists + Apple Music for Artists"), "rev": 200, "go": "All tracks live on Spotify, Apple, YouTube Music", "nogo": "Cover songs need licensing first — use DistroKid's cover song license ($0.25/track/yr)", "cost": 22},
        {"theme": "Sync Pitch", "actions": ("Pitch top 5 tracks to Musicbed.com, Artlist.io, and Musicvine — free submission", "Create 60-second 'sync reel' audio preview for each pitched track"), "rev": 1500, "go": "2 pitches submitted with assets", "nogo": "Rejected → improve production quality first (EQ/master via LANDR free tier)", "cost": 0},
        {"theme": "Recurring Revenue", "actions": ("Launch Patreon or Substack at $5/mo tier with exclusive content offer", "Email + DM top 50 fans personally with launch message"), "rev": 250, "go": "10 paid subscribers in first week", "nogo": "< 5 subscribers → switch to $2/mo, lower barrier, focus on volume", "cost": 0},
        {"theme": "Content Engine", "actions": ("Identify top-performing track → create 5 short-form Reels/TikToks from it", "Post 1/day for 5 days — test hooks: lyric quote vs performance vs backstory"), "rev": 0, "go": "1 post reaches 500+ organic views", "nogo": "All under 200 views → switch format (talking head beats performance for discovery)", "cost": 0},
        {"theme": "Brand Sync", "actions": ("Reach out to 10 local brands for paid sync/background music deal ($500-2,000)", "Target: restaurants, gyms, retail stores — pitch 'custom playlist for your brand'"), "rev": 750, "go": "1 brand responds for follow-up call", "nogo": "0 responses → pivot to online brands in your genre niche", "cost": 0},
        {"theme": "Legal", "actions": ("File USCO copyright registration for all works ($65 per group of songs)", "Create master rights document listing co-writer splits for every track"), "rev": 0, "go": "Registration receipt received from Copyright Office", "nogo": "Budget tight → prioritize top 20 tracks, register rest later", "cost": 65},
        {"theme": "Merch", "actions": ("Set up Printful + free Shopify trial — 5 designs, phone-free production", "Add merch link to all bio/link-in-bio platforms"), "rev": 300, "go": "Store live; first sale within 14 days", "nogo": "No sales in 14 days → run 48hr '10% off' promo to email list", "cost": 0},
        {"theme": "Live Revenue", "actions": ("Book 2 paid live events at $500-2,000 performance fee each", "Target: local festivals, cultural events, corporate parties — use LinkedIn outreach"), "rev": 1500, "go": "1 event booked and deposit received", "nogo": "0 bookings → lower to $250 for first 2 events as portfolio builders", "cost": 0},
        {"theme": "Playlist", "actions": ("Pitch top track to 3 Spotify playlist curators via SubmitHub ($0.50-2/submission)", "Also pitch to Apple Music + YouTube Music editorial via their free submission portals"), "rev": 200, "go": "Track added to 1 playlist with 5,000+ followers", "nogo": "All rejected → improve artwork and re-pitch — first impression is visual", "cost": 10},
        {"theme": "Royalty Audit", "actions": ("Pull all royalty dashboards — SoundExchange, PRO, DistroKid, Patreon", "Calculate total passive royalty run-rate → target $1,000/mo by end of Year 1"), "rev": 0, "go": "All income sources documented in one spreadsheet", "nogo": "< $200/mo royalties → focus next 60 days on sync licensing pitches", "cost": 0},
    ],
    "food_beverage": [
        {"theme": "Foundation", "actions": ("Install Square POS (free) or Toast Free tier to capture real-time sales data", "Pull last 30 days of sales if possible — find your top-10 selling items"), "rev": 0, "go": "First sale rung through POS", "nogo": "Cash-only operation → POS is Week 1 foundation, non-negotiable", "cost": 0},
        {"theme": "Menu Margin", "actions": ("Calculate food cost % on top-10 items — target < 30% food cost per item", "Feature top 3 highest-margin items prominently on menu (reprint if needed)"), "rev": 800, "go": "Menu reprinted with margin-optimized layout", "nogo": "No cost data → estimate via supplier invoices, refine over 2 weeks", "cost": 50},
        {"theme": "Email List", "actions": ("Launch 'text/email for 10% off next visit' at POS counter", "Set up Mailchimp free (500 contacts) or Google Form → Google Sheet"), "rev": 0, "go": "50 emails/numbers collected in first week", "nogo": "< 20 collected → add verbal prompt from every cashier at checkout", "cost": 0},
        {"theme": "Reviews", "actions": ("Respond to every Google/Yelp review within 24hr — personal reply, not template", "Ask every satisfied customer: 'Would you mind leaving us a Google review?'"), "rev": 600, "go": "All existing reviews responded to; 3 new reviews this week", "nogo": "Negative reviews dominating → address each personally before marketing spend", "cost": 0},
        {"theme": "Online Ordering", "actions": ("Set up Toast Free online ordering or Square Online free tier", "Add online order link to Google Business Profile and Instagram bio"), "rev": 2000, "go": "First online order received", "nogo": "Order quality issues online → add 'call if confused' note + simpler online menu", "cost": 0},
        {"theme": "Catering B2B", "actions": ("Call 5 local businesses within 1 mile for catering accounts", "Offer 10% off first order + 'staff meal' standing weekly order"), "rev": 1500, "go": "1 recurring catering account signed", "nogo": "0 bites → lower to 'one-time lunch for your team, free delivery'", "cost": 0},
        {"theme": "Office Deal", "actions": ("Create 'office meal plan' — $12/person/day, minimum 5 people, weekly prepay", "Target 1 office building within walking distance via LinkedIn or cold visit"), "rev": 1200, "go": "1 office deal signed with deposit", "nogo": "No offices nearby → pivot to construction site meal delivery ($14-18/person)", "cost": 0},
        {"theme": "Cash Flow", "actions": ("Call top-2 food suppliers to negotiate net-30 payment terms", "In exchange: commit to ordering 20% more volume from them each month"), "rev": 0, "go": "Net-30 terms confirmed in writing", "nogo": "Supplier refuses → ask for 50% upfront, 50% net-15 as middle ground", "cost": 0},
        {"theme": "Loyalty", "actions": ("Launch $45/mo VIP membership: unlimited coffee/tea + 15% off + priority seating", "Announce via email list and Instagram — limit to first 25 members for urgency"), "rev": 900, "go": "5 VIP memberships sold in first week", "nogo": "< 3 sold → lower to $29/mo or add more tangible benefit", "cost": 0},
        {"theme": "Content", "actions": ("Post 3 Reels/TikToks this week: kitchen process, best dish, customer reaction", "Use trending audio — DM 5 local food bloggers/influencers for free meal exchange"), "rev": 400, "go": "1 post gets 500+ organic views", "nogo": "All under 100 views → reshoot with better lighting, post at 12pm or 6pm", "cost": 0},
        {"theme": "Staffing", "actions": ("If monthly revenue > $15,000: hire 1 part-time (20hr/wk) at $18-20/hr", "Owner shifts to front-of-house management + sales — stops working the line"), "rev": 0, "go": "Revenue threshold met → post job on Indeed free today", "nogo": "Revenue < $15K → skip hire, focus on online ordering and catering volume", "cost": 0},
        {"theme": "P&L Review", "actions": ("Pull full 3-month P&L: COGS must be under 35% of gross to be scalable", "If COGS > 35%: identify top 3 waste items and implement par levels this week"), "rev": 0, "go": "COGS % calculated and documented", "nogo": "No clear P&L data → this is the non-negotiable fix before Month 4", "cost": 0},
    ],
}

_GENERIC_TEMPLATE: list[dict] = [
    {"theme": "Foundation", "actions": ("Audit all current revenue streams — document exact $/mo each", "Identify your single highest-margin product/service"), "rev": 0, "go": "Revenue audit in spreadsheet", "nogo": "No financial records → build basic bookkeeping this week first", "cost": 0},
    {"theme": "Customer Intel", "actions": ("Interview 5 best customers: what do they buy, why, what else do they need", "Document verbatim responses — look for patterns"), "rev": 500, "go": "5 interviews complete", "nogo": "Can't reach 5 → send 1-question email survey to email list", "cost": 0},
    {"theme": "Quick Win", "actions": ("Raise prices 10% on lowest-volume highest-margin service", "Announce price increase in 30 days to existing clients — close 'now' deals"), "rev": 800, "go": "Prices updated; 0 client complaints", "nogo": "Pushback > 20% → revert, add value bundle instead", "cost": 0},
    {"theme": "Digital Foundation", "actions": ("Set up Google Business Profile if missing (free)", "Respond to all reviews within 24hr for 30 days straight"), "rev": 400, "go": "Profile complete with photos + hours", "nogo": "No reviews yet → ask 10 best customers this week", "cost": 0},
    {"theme": "Recurring Revenue", "actions": ("Design a $X/mo retainer or subscription tier", "Offer to top 10 clients first with 20% founding-member discount"), "rev": 1500, "go": "1 recurring client signed", "nogo": "0 sign-ups → lower price, add more deliverables", "cost": 0},
    {"theme": "Partnership", "actions": ("Identify 3 non-competing businesses serving your customer", "Propose referral exchange: you send them clients, they send you clients"), "rev": 800, "go": "1 active referral partnership", "nogo": "No responses → offer cash referral fee instead of exchange", "cost": 0},
    {"theme": "Content", "actions": ("Post 1 piece of value content per day for 14 days on your best platform", "Document the result: followers gained, DMs received, leads generated"), "rev": 300, "go": "14 posts live; at least 1 DM from a potential client", "nogo": "0 DMs → switch platform or format after 7 days", "cost": 0},
    {"theme": "Vertical Test", "actions": ("Identify the top vertical opportunity from your NeighborIQ analysis", "Run minimum viable test: offer it to 3 existing customers at discounted rate"), "rev": 1000, "go": "1 customer buys the new offer", "nogo": "0 buys → reframe offer, not the product", "cost": 0},
    {"theme": "Automation", "actions": ("Identify top 3 manual tasks taking > 2 hrs/week", "Automate with n8n (free self-hosted) or Zapier free tier"), "rev": 0, "go": "2+ hours/week saved", "nogo": "Can't automate → hire VA at $5-15/hr for these specific tasks", "cost": 0},
    {"theme": "Review", "actions": ("Pull 90-day P&L and compare to benchmark targets", "Identify top leak: customer acquisition cost, churn, or margin compression"), "rev": 0, "go": "P&L reviewed, top leak identified", "nogo": "No P&L data → this is the only priority this week", "cost": 0},
    {"theme": "Scale", "actions": ("If revenue hit month-3 target: hire or outsource your lowest-leverage task", "Document the exact process before delegating"), "rev": 0, "go": "Process documented + delegated", "nogo": "Revenue < target → no new hires, focus on lead generation", "cost": 0},
    {"theme": "Checkpoint", "actions": ("Review all 12 milestones: what worked, what didn't", "Write 90-day plan for next quarter based on actual results"), "rev": 0, "go": "Written plan for next quarter", "nogo": "No plan → treat this as the most important hour of the quarter", "cost": 0},
]


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class WeeklyMilestone:
    week_number: int
    date: str
    theme: str
    actions: tuple[str, ...]
    revenue_impact_monthly: int
    go_signal: str
    no_go_signal: str
    cost_to_execute: int


@dataclass(frozen=True)
class MonthlyTarget:
    month_number: int
    date: str
    revenue_target: int
    profit_target: int
    key_metric: str
    key_metric_target: str
    what_unlocks_next: str
    risk_if_missed: str


@dataclass(frozen=True)
class MarketSizing:
    domain_id: str
    geography: str
    tam_usd: int
    tam_description: str
    sam_usd: int
    sam_description: str
    som_usd: int
    som_description: str
    market_growth_rate: float
    market_phase: str
    year1_target_pct: float
    year1_revenue: int
    year3_revenue: int


@dataclass(frozen=True)
class GrowthForecast:
    biz_name: str
    domain_id: str
    start_date: str
    market: MarketSizing
    weekly_milestones: tuple[WeeklyMilestone, ...]
    monthly_targets: tuple[MonthlyTarget, ...]
    recommended_llm: str
    recommended_automation: str
    recommended_agent_framework: str
    llm_cost_monthly: str
    novel_opportunities: tuple[str, ...]
    total_investment_needed: int
    break_even_week: int
    year1_roi_pct: float


# ── Internal helpers ──────────────────────────────────────────────────────────

def _fmt_date(d: date) -> str:
    return d.strftime("%b %-d, %Y") if hasattr(d, "strftime") else str(d)


def _fmt_date_long(d: date) -> str:
    return d.strftime("%B %-d, %Y") if hasattr(d, "strftime") else str(d)


def _fmt_usd(n: int) -> str:
    if n >= 1_000_000_000_000:
        return f"${n / 1_000_000_000_000:.1f}T"
    if n >= 1_000_000_000:
        return f"${n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"${n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"${n / 1_000:.0f}K"
    return f"${n}"


def _calculate_market_sizing(
    domain_id: str,
    benchmarks: "DomainBenchmarks",
    city_population: int,
) -> MarketSizing:
    tam = _TAM_USD.get(domain_id, 100_000_000_000)
    tam_desc = f"US total {domain_id.replace('_', ' ')} market (industry data)"

    metro_share = city_population / _US_POPULATION
    sam_raw = int(tam * metro_share * 0.15)
    sam_cap = benchmarks.revenue_p75 * 12 * 200
    sam = min(sam_raw, sam_cap)
    sam_desc = (
        f"Metro addressable market ({city_population:,} pop, 15% local capture ceiling, "
        f"capped at {_fmt_usd(sam_cap)} = 200 top-quartile businesses)"
    )

    som_raw = int(sam * 0.02)
    som_floor = benchmarks.revenue_p50 * 12 * 3
    som_ceil = benchmarks.revenue_p75 * 12 * 5
    som = max(som_floor, min(som_raw, som_ceil))
    som_desc = f"3-year attainable (2% of SAM, floor={_fmt_usd(som_floor)}, ceil={_fmt_usd(som_ceil)})"

    year1_revenue = int(benchmarks.revenue_p50 * 10)  # ~10 months ramp to median
    year3_revenue = int(benchmarks.revenue_p75 * 12 * 1.2)  # 20% above top quartile after 3 yrs
    year1_pct = (year1_revenue / som * 100) if som > 0 else 0.0

    return MarketSizing(
        domain_id=domain_id,
        geography=f"Metro area ({city_population:,} pop)",
        tam_usd=tam,
        tam_description=tam_desc,
        sam_usd=sam,
        sam_description=sam_desc,
        som_usd=som,
        som_description=som_desc,
        market_growth_rate=benchmarks.growth_rate_industry,
        market_phase=_MARKET_PHASE.get(domain_id, "mature"),
        year1_target_pct=round(year1_pct, 1),
        year1_revenue=year1_revenue,
        year3_revenue=year3_revenue,
    )


def _generate_weekly_milestones(
    domain_id: str,
    benchmarks: "DomainBenchmarks",
    start_date: date,
) -> tuple[WeeklyMilestone, ...]:
    templates = _WEEKLY_TEMPLATES.get(domain_id, _GENERIC_TEMPLATE)
    milestones: list[WeeklyMilestone] = []
    for i, t in enumerate(templates[:12]):
        week_num = i + 1
        wdate = start_date + timedelta(weeks=i)
        milestones.append(WeeklyMilestone(
            week_number=week_num,
            date=_fmt_date(wdate),
            theme=t["theme"],
            actions=tuple(t["actions"]),
            revenue_impact_monthly=t["rev"],
            go_signal=t["go"],
            no_go_signal=t["nogo"],
            cost_to_execute=t["cost"],
        ))
    return tuple(milestones)


def _generate_monthly_targets(
    benchmarks: "DomainBenchmarks",
    profile: "BizProfile",
    domain_id: str,
    start_date: date,
    months: int = 24,
) -> tuple[MonthlyTarget, ...]:
    p25 = benchmarks.revenue_p25
    p50 = benchmarks.revenue_p50
    p75 = benchmarks.revenue_p75
    current = getattr(profile, "monthly_revenue", 0) or 0
    margin = max(0.01, benchmarks.net_margin_typical)
    key_metric = _KEY_METRIC_LABEL.get(domain_id, "revenue ($)")

    # Phase boundaries
    phases = [
        (1, 3, current, p25, "Build systems and first recurring clients"),
        (4, 6, p25, p50, "Hit benchmark median — proof of scalability"),
        (7, 12, p50, p75, "Outperform benchmark — employer-grade operation"),
        (13, 24, p75, int(p75 * 1.4), "Sustain excellence + vertical expansion"),
    ]

    targets: list[MonthlyTarget] = []
    for phase_start, phase_end, rev_start, rev_end, _ in phases:
        for mo in range(phase_start, min(phase_end + 1, months + 1)):
            t = (mo - phase_start) / max(1, phase_end - phase_start)
            rev = int(rev_start + (rev_end - rev_start) * t)
            rev = max(rev, current)
            profit = int(rev * margin)
            target_num = int(rev / max(1, rev // max(1, _key_metric_target_divisor(domain_id))))
            mdate = _add_months(start_date, mo)
            targets.append(MonthlyTarget(
                month_number=mo,
                date=_fmt_date_long(mdate),
                revenue_target=rev,
                profit_target=profit,
                key_metric=key_metric,
                key_metric_target=_fmt_metric_target(domain_id, rev, mo),
                what_unlocks_next=_unlock_text(domain_id, mo),
                risk_if_missed=_risk_text(domain_id, mo),
            ))
            if mo >= months:
                break

    return tuple(targets[:months])


def _key_metric_target_divisor(domain_id: str) -> int:
    divisors = {
        "software_saas": 100, "logistics": 5000, "food_beverage": 100,
        "music_entertainment": 1, "healthcare": 200, "real_estate": 3000,
        "retail": 50, "education": 300, "agency_services": 5000,
        "local_service": 150, "distribution": 2000, "manufacturing": 500,
        "creative_media": 1, "professional_services": 5000,
    }
    return divisors.get(domain_id, 1000)


def _fmt_metric_target(domain_id: str, rev: int, month: int) -> str:
    templates = {
        "software_saas":       f"${rev:,} MRR",
        "logistics":           f"{max(1, rev // 5000)} loads/mo",
        "food_beverage":       f"{max(10, rev // 100)} covers/day",
        "music_entertainment": f"{rev * 100:,} streams + ${rev // 10:,} royalties",
        "healthcare":          f"{max(1, rev // 200)} patient visits",
        "real_estate":         f"{max(1, rev // 3000)} closed transactions",
        "retail":              f"{max(10, rev // 50)} transactions/mo",
        "education":           f"{max(1, rev // 300)} enrolled students",
        "agency_services":     f"{max(1, rev // 5000)} active client retainers",
        "local_service":       f"{max(5, rev // 150)} clients/mo",
        "distribution":        f"{max(1, rev // 2000)} orders/mo",
        "manufacturing":       f"{max(1, rev // 500)} units/mo",
        "creative_media":      f"{max(100, rev * 10):,} subscribers",
        "professional_services": f"{max(1, rev // 5000)} active engagements",
    }
    return templates.get(domain_id, f"${rev:,}/mo gross")


def _unlock_text(domain_id: str, month: int) -> str:
    if month <= 3:
        return "Proof of concept → qualify for SBA microloan ($5K-50K) if needed"
    if month <= 6:
        return "Benchmark median → justifies hiring first part-time employee"
    if month <= 12:
        return "Top-quartile operation → credible for investor conversations or franchise model"
    return "Vertical expansion → add second revenue stream without touching core"


def _risk_text(domain_id: str, month: int) -> str:
    risks = {
        1: "No foundation built → month 2-3 ramp becomes much steeper",
        3: "Still at zero baseline → core assumptions need revisiting before spending more",
        6: "Below median benchmark → may need to revisit positioning or pricing",
        12: "< top quartile → scale plan needs revision; don't add headcount yet",
        24: "< 1.4x top quartile → vertical expansion delayed; focus on core optimization",
    }
    closest = min(risks.keys(), key=lambda k: abs(k - month))
    return risks[closest]


def _add_months(d: date, months: int) -> date:
    month = d.month + months
    year = d.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    last_day = [0, 31, 28 + (1 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 0),
                31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month]
    return date(year, month, min(d.day, last_day))


def _tool_recommendations(domain_id: str) -> tuple[str, str, str, str]:
    llm_map = {
        "software_saas":       ("Claude Sonnet 4.6", "$3-15/M tokens — best function calling reliability", "LangGraph", "n8n self-hosted"),
        "logistics":           ("Gemini 2.0 Flash", "$0.10/$0.40/M — large doc analysis, RFP parsing", "CrewAI", "n8n self-hosted"),
        "music_entertainment": ("DeepSeek V3", "$0.14/$0.28/M — cheapest frontier for lyric/sync copy", "smolagents", "n8n self-hosted"),
        "food_beverage":       ("Gemini 2.0 Flash", "$0.10/$0.40/M — menu analysis, review sentiment", "AutoGen", "n8n self-hosted"),
        "healthcare":          ("Claude Sonnet 4.6", "$3-15/M — HIPAA-sensitive, best structured output", "LangGraph", "Temporal"),
        "real_estate":         ("GPT-4o", "$5/$15/M — best for long-form listing copy generation", "AutoGen", "n8n self-hosted"),
        "education":           ("Claude Haiku 4.5", "$0.25/$1.25/M — high-volume student interactions", "smolagents", "n8n self-hosted"),
        "agency_services":     ("Claude Sonnet 4.6", "$3-15/M — client-facing copy quality", "LangGraph", "n8n self-hosted"),
        "local_service":       ("Gemini 2.0 Flash", "$0.10/$0.40/M — cheapest for scheduling/review tasks", "smolagents", "n8n self-hosted"),
        "retail":              ("Gemini 2.0 Flash", "$0.10/$0.40/M — inventory and pricing analysis", "AutoGen", "n8n self-hosted"),
        "distribution":        ("DeepSeek V3", "$0.14/$0.28/M — cheapest for PO/invoice parsing", "CrewAI", "n8n self-hosted"),
        "manufacturing":       ("GPT-4o", "$5/$15/M — technical spec understanding", "LangGraph", "Temporal"),
        "creative_media":      ("DeepSeek V3", "$0.14/$0.28/M — cheapest for bulk content generation", "smolagents", "n8n self-hosted"),
        "professional_services":("Claude Sonnet 4.6", "$3-15/M — reasoning + report quality", "LangGraph", "n8n self-hosted"),
    }
    rec = llm_map.get(domain_id, ("Gemini 2.0 Flash", "$0.10/$0.40/M — cost-effective general use", "AutoGen", "n8n self-hosted"))
    return rec[0], rec[1], rec[2], rec[3]


def _calculate_break_even(
    milestones: tuple[WeeklyMilestone, ...],
    profile: "BizProfile",
) -> int:
    current_monthly_profit = getattr(profile, "monthly_revenue", 0) - getattr(profile, "monthly_expenses", 0)
    total_investment = sum(m.cost_to_execute for m in milestones)
    cumulative_added_revenue = 0
    for m in milestones:
        cumulative_added_revenue += m.revenue_impact_monthly
        if cumulative_added_revenue >= total_investment:
            return m.week_number
    return 16  # fallback if investment not recovered in 12 weeks


# ── Public API ────────────────────────────────────────────────────────────────

def generate_forecast(
    profile: "BizProfile",
    benchmarks: "DomainBenchmarks",
    domain: "DomainSpec",
    city_population: int = 700_000,
    start_date: date | None = None,
) -> GrowthForecast:
    if start_date is None:
        start_date = date.today()

    market = _calculate_market_sizing(domain.domain_id, benchmarks, city_population)
    weekly = _generate_weekly_milestones(domain.domain_id, benchmarks, start_date)
    monthly = _generate_monthly_targets(benchmarks, profile, domain.domain_id, start_date)
    llm, llm_cost, framework, automation = _tool_recommendations(domain.domain_id)
    novel = tuple(_NOVEL_OPPORTUNITIES.get(domain.domain_id, (
        "Equipment idle-time rental — monetize downtime with zero new capital",
        "Google Business optimization — most businesses have < 10 photos and no Q&A answered",
        "Referral program — 20% of new clients from existing clients if you ask systematically",
        "Annual prepay offer — discount 15%, collect 12 months upfront to fund growth",
    )))
    total_invest = sum(m.cost_to_execute for m in weekly)
    break_even = _calculate_break_even(weekly, profile)
    year1_added = sum(m.revenue_impact_monthly for m in weekly)
    roi = ((year1_added * 12 - total_invest) / max(1, total_invest) * 100) if total_invest > 0 else 999.0

    return GrowthForecast(
        biz_name=profile.name,
        domain_id=domain.domain_id,
        start_date=start_date.strftime("%B %-d, %Y"),
        market=market,
        weekly_milestones=weekly,
        monthly_targets=monthly,
        recommended_llm=llm,
        recommended_automation=automation,
        recommended_agent_framework=framework,
        llm_cost_monthly=llm_cost,
        novel_opportunities=novel,
        total_investment_needed=total_invest,
        break_even_week=break_even,
        year1_roi_pct=round(roi, 1),
    )


def format_forecast(forecast: GrowthForecast, weeks: int = 12) -> str:
    w = 60
    sep = "═" * w
    thin = "─" * w
    lines: list[str] = []

    lines += [
        sep,
        f"GROWTH FORECAST: {forecast.biz_name}",
        f"Domain: {forecast.domain_id.replace('_', ' ').title()}  |  Start: {forecast.start_date}",
        f"Break-even: Week {forecast.break_even_week}  |  Year-1 ROI: {forecast.year1_roi_pct:.0f}%",
        sep,
        "",
    ]

    m = forecast.market
    lines += [
        "MARKET SIZING",
        thin,
        f"TAM  {_fmt_usd(m.tam_usd):>10}  {m.tam_description}",
        f"SAM  {_fmt_usd(m.sam_usd):>10}  {m.sam_description[:55]}",
        f"SOM  {_fmt_usd(m.som_usd):>10}  {m.som_description[:55]}",
        f"",
        f"Year 1 target : {_fmt_usd(m.year1_revenue)} ({m.year1_target_pct:.1f}% of SOM)",
        f"Year 3 target : {_fmt_usd(m.year3_revenue)}",
        f"Market phase  : {m.market_phase}  |  Growth: {m.market_growth_rate:.1f}%/yr",
        f"",
    ]

    lines += [
        "RECOMMENDED TECH STACK  (cost-optimized, no vendor bias)",
        thin,
        f"LLM:        {forecast.recommended_llm} — {forecast.llm_cost_monthly}",
        f"Automation: {forecast.recommended_automation} — $0/mo self-hosted vs $20-50/mo cloud alternatives",
        f"Framework:  {forecast.recommended_agent_framework}",
        "",
    ]

    lines += ["WEEK-BY-WEEK ACTION PLAN", thin]
    for ms in forecast.weekly_milestones[:weeks]:
        cost_str = f"${ms.cost_to_execute:,}" if ms.cost_to_execute > 0 else "free"
        lines.append(f"── Week {ms.week_number:>2}  ({ms.date})  [{ms.theme.upper()}]  cost: {cost_str}")
        for action in ms.actions:
            lines.append(f"   □  {action}")
        if ms.revenue_impact_monthly > 0:
            lines.append(f"   Revenue impact: +${ms.revenue_impact_monthly:,}/mo when complete")
        lines.append(f"   ✓ Go: {ms.go_signal}")
        lines.append(f"   ✗ No-Go: {ms.no_go_signal}")
        lines.append("")

    # Monthly targets — show months 1, 3, 6, 12, 18, 24
    show_months = {1, 3, 6, 12, 18, 24}
    monthly_shown = [t for t in forecast.monthly_targets if t.month_number in show_months]
    if monthly_shown:
        lines += ["MONTHLY REVENUE TARGETS", thin]
        for t in monthly_shown:
            lines.append(
                f"Month {t.month_number:>2}  ({t.date[:12]}):  "
                f"${t.revenue_target:>8,} gross  |  ${t.profit_target:>7,} net"
            )
            lines.append(f"          Key: {t.key_metric_target}")
            lines.append(f"          Unlocks: {t.what_unlocks_next}")
            lines.append("")

    lines += ["NOVEL INCOME STREAMS  (underexploited in your domain)", thin]
    for i, opp in enumerate(forecast.novel_opportunities, 1):
        lines.append(f"  {i}. {opp}")

    lines += [
        "",
        thin,
        f"Total 12-week investment needed: ${forecast.total_investment_needed:,}",
        f"Break-even week: {forecast.break_even_week}  |  Projected Year-1 ROI: {forecast.year1_roi_pct:.0f}%",
        sep,
    ]

    return "\n".join(lines)
