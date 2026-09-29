"""automation_matrix.py — Automation blueprint per business niche.

Maps each niche to: which tasks can be automated, which must stay human,
recommended free/low-cost tools, estimated monthly savings, and top-3
priority automations to implement first.
"""
from __future__ import annotations

from dataclasses import dataclass

__all__ = ["AutomationBlueprint", "get_automation_blueprint", "format_automation_blueprint"]


# NOTE: frozen=True + tuple[dict, ...] fields are not hashable at runtime.
# Instances are safe to create and access but should not be used as dict keys.
@dataclass(frozen=True)
class AutomationBlueprint:
    niche: str
    automation_score: int                          # 0-100
    automated_tasks: tuple[str, ...]
    human_tasks: tuple[str, ...]
    recommended_tools: tuple[dict, ...]            # {"tool", "use", "cost_mo"}
    staff_with_automation: str
    monthly_savings_usd: int
    automation_pct: float                          # 0.0–1.0
    priority_automations: tuple[str, ...]          # top-3 to implement first


_BLUEPRINTS: dict[str, AutomationBlueprint] = {}


def _reg(
    niche: str,
    *,
    automation_score: int,
    automated_tasks: tuple[str, ...],
    human_tasks: tuple[str, ...],
    recommended_tools: tuple[dict, ...],
    staff_with_automation: str,
    monthly_savings_usd: int,
    automation_pct: float,
    priority_automations: tuple[str, ...],
) -> AutomationBlueprint:
    bp = AutomationBlueprint(
        niche=niche,
        automation_score=automation_score,
        automated_tasks=automated_tasks,
        human_tasks=human_tasks,
        recommended_tools=recommended_tools,
        staff_with_automation=staff_with_automation,
        monthly_savings_usd=monthly_savings_usd,
        automation_pct=automation_pct,
        priority_automations=priority_automations,
    )
    _BLUEPRINTS[niche] = bp
    return bp


# ── blueprints ────────────────────────────────────────────────────────────────

_reg(
    "barbershop",
    automation_score=55,
    automated_tasks=(
        "Online appointment booking",
        "SMS/email appointment reminders (24hr + 1hr before)",
        "Post-visit review request SMS",
        "Automated no-show follow-up",
        "Square POS payment + receipts",
        "Weekly social media post from template",
        "Supply reorder alerts when below threshold",
        "Birthday discount SMS to loyal clients",
    ),
    human_tasks=(
        "Haircuts and styling",
        "Client consultation and preference tracking",
        "Cash and sensitive payments",
        "Walk-in queue management",
        "Product recommendation",
        "Staff performance reviews",
    ),
    recommended_tools=(
        {"tool": "Calendly", "use": "Online booking (replaces phone calls)", "cost_mo": 0},
        {"tool": "Square POS", "use": "Payment, tips, sales reporting", "cost_mo": 0},
        {"tool": "Twilio SMS", "use": "Reminders + review requests (~150 msgs/mo)", "cost_mo": 2},
        {"tool": "n8n (self-hosted)", "use": "Automate reminder + review flows", "cost_mo": 0},
        {"tool": "Mailchimp free", "use": "Monthly loyalty email blast", "cost_mo": 0},
        {"tool": "When I Work free", "use": "Staff scheduling if multi-barber", "cost_mo": 0},
    ),
    staff_with_automation="1 owner-barber + 0 employees",
    monthly_savings_usd=700,
    automation_pct=0.45,
    priority_automations=(
        "Calendly booking — eliminates 1-2 hrs/day of phone tag",
        "Twilio reminder SMS — reduces no-shows by 30-50%",
        "Post-visit review request SMS — builds Google rating passively",
    ),
)

_reg(
    "nail_salon",
    automation_score=50,
    automated_tasks=(
        "Online booking via Calendly or Fresha",
        "Automated appointment reminders",
        "Review requests after each appointment",
        "Loyalty points tracking (Square Loyalty)",
        "Instagram posting from content template",
        "Supply inventory alerts",
        "Client birthday offers",
        "Payment via Square",
    ),
    human_tasks=(
        "All nail services (manicure, pedicure, gel, acrylic)",
        "Client color and design consultation",
        "Upselling add-on services",
        "Allergy and sanitation checks",
        "Cash handling for tips",
    ),
    recommended_tools=(
        {"tool": "Fresha", "use": "Booking + client management (beauty-specific)", "cost_mo": 0},
        {"tool": "Square POS", "use": "Payment + loyalty program", "cost_mo": 0},
        {"tool": "Square Loyalty", "use": "Stamp card replacement — earns 30% more repeat visits", "cost_mo": 45},
        {"tool": "Twilio", "use": "Reminder + review SMS", "cost_mo": 2},
        {"tool": "Later free", "use": "Instagram scheduling", "cost_mo": 0},
    ),
    staff_with_automation="1 owner-tech + 0 employees",
    monthly_savings_usd=500,
    automation_pct=0.40,
    priority_automations=(
        "Fresha booking — online bookings convert 2× vs phone",
        "Square Loyalty — repeat visit rate increases by 30%",
        "Twilio review SMS — 4.5+ Google rating within 90 days",
    ),
)

_reg(
    "hair_salon",
    automation_score=52,
    automated_tasks=(
        "Online booking (Fresha or Vagaro)",
        "Appointment reminders",
        "Cancellation and rebooking flows",
        "Review requests",
        "Product retail order tracking",
        "Monthly newsletter with promotions",
        "Square payment + tip handling",
    ),
    human_tasks=(
        "All hair services: cuts, color, treatment",
        "Color formula consultation",
        "Scalp health assessment",
        "In-person upselling of retail products",
    ),
    recommended_tools=(
        {"tool": "Vagaro", "use": "Salon-specific booking, POS, client notes", "cost_mo": 25},
        {"tool": "Square POS", "use": "Payments backup and retail tracking", "cost_mo": 0},
        {"tool": "Twilio", "use": "Reminder + rebooking SMS", "cost_mo": 3},
        {"tool": "Mailchimp free", "use": "Monthly promotion email", "cost_mo": 0},
    ),
    staff_with_automation="1 owner-stylist + 0 employees",
    monthly_savings_usd=500,
    automation_pct=0.42,
    priority_automations=(
        "Vagaro booking — tracks color formulas + client history automatically",
        "Automated rebooking SMS 4 weeks after last visit",
        "Review request 1hr after checkout",
    ),
)

_reg(
    "coffee_shop",
    automation_score=62,
    automated_tasks=(
        "Mobile order ahead (Square Online)",
        "Loyalty punch card (Square Loyalty)",
        "Automatic social post 3×/week from template",
        "Daily sales report to owner phone",
        "Low-inventory alert for beans and supplies",
        "Automated email for online orders",
        "Gift card program",
        "Wholesale subscription billing (Stripe recurring)",
    ),
    human_tasks=(
        "Espresso preparation and latte art",
        "Customer interaction and recommendations",
        "Food prep",
        "Cash register for walk-ins",
        "Equipment cleaning and maintenance",
    ),
    recommended_tools=(
        {"tool": "Square Online", "use": "Mobile ordering and pickup scheduling", "cost_mo": 0},
        {"tool": "Square POS + Loyalty", "use": "POS + loyalty stamps", "cost_mo": 45},
        {"tool": "n8n (self-hosted)", "use": "Low-stock alerts → reorder Slack/SMS", "cost_mo": 0},
        {"tool": "Buffer free", "use": "3 social posts/week scheduled", "cost_mo": 0},
        {"tool": "Stripe", "use": "Wholesale subscription billing", "cost_mo": 0},
    ),
    staff_with_automation="1 owner-barista + 1 part-time barista",
    monthly_savings_usd=700,
    automation_pct=0.55,
    priority_automations=(
        "Mobile order ahead — reduces peak-rush bottleneck, increases throughput 20%",
        "Low-inventory alert — prevents stock-outs that close the shop",
        "Loyalty program — 5× more likely to retain a customer than acquire a new one",
    ),
)

_reg(
    "cafe",
    automation_score=55,
    automated_tasks=(
        "Online ordering via Square or Toast",
        "Order confirmation + pickup SMS",
        "Review requests",
        "Catering inquiry auto-reply with menu + pricing PDF",
        "Loyalty rewards",
        "Social media scheduling",
        "Supplier reorder alerts",
    ),
    human_tasks=(
        "Food preparation",
        "Customer service and upselling",
        "Special dietary accommodation",
        "Cash handling",
        "Daily prep and cleaning",
    ),
    recommended_tools=(
        {"tool": "Square Online", "use": "Takeout ordering", "cost_mo": 0},
        {"tool": "Toast POS", "use": "Full-service cafe POS with kitchen display", "cost_mo": 0},
        {"tool": "Twilio", "use": "Order-ready SMS notification", "cost_mo": 3},
        {"tool": "n8n", "use": "Catering auto-reply workflow", "cost_mo": 0},
        {"tool": "Buffer free", "use": "Social scheduling", "cost_mo": 0},
    ),
    staff_with_automation="1 owner + 1 part-time counter person",
    monthly_savings_usd=600,
    automation_pct=0.48,
    priority_automations=(
        "Online ordering — captures off-peak orders from workers who pre-order lunch",
        "Catering auto-reply — no missed leads during service hours",
        "Review request SMS 2hrs after visit",
    ),
)

_reg(
    "bakery",
    automation_score=45,
    automated_tasks=(
        "Online pre-orders for pickup (Square Online)",
        "Custom cake inquiry form → auto-response with price guide",
        "Order-ready SMS notification",
        "Review requests",
        "Farmers market schedule auto-post to Instagram",
        "Ingredient reorder alerts",
        "Subscription box billing (Stripe)",
    ),
    human_tasks=(
        "All baking and production",
        "Custom cake design consultation",
        "Decorating and finishing",
        "Quality control",
        "Farmers market setup and sales",
    ),
    recommended_tools=(
        {"tool": "Square Online", "use": "Pre-order + special order form", "cost_mo": 0},
        {"tool": "Stripe", "use": "Subscription box recurring billing", "cost_mo": 0},
        {"tool": "Twilio", "use": "Order-ready + review SMS", "cost_mo": 2},
        {"tool": "Canva Pro + Buffer", "use": "Social content from product photos", "cost_mo": 13},
        {"tool": "Google Forms + n8n", "use": "Custom cake intake + auto-quote email", "cost_mo": 0},
    ),
    staff_with_automation="1 owner-baker + 0 employees",
    monthly_savings_usd=400,
    automation_pct=0.35,
    priority_automations=(
        "Pre-order system — bake to order reduces waste by 30-40%",
        "Custom cake inquiry auto-responder — captures leads at 2 AM",
        "Subscription box billing — recurring revenue with zero re-selling effort",
    ),
)

_reg(
    "tutoring_center",
    automation_score=65,
    automated_tasks=(
        "Online session booking (Calendly or Acuity)",
        "Session reminders (SMS + email)",
        "Monthly invoice + Stripe auto-charge",
        "Progress report email template (weekly auto-send)",
        "Student attendance tracking (Google Sheets + n8n)",
        "Review request after first month",
        "Waitlist management",
        "Homework assignment delivery via email",
    ),
    human_tasks=(
        "All tutoring and teaching sessions",
        "Student assessment and diagnostic",
        "Parent communication on progress",
        "Curriculum customization per student",
        "Motivating struggling students",
    ),
    recommended_tools=(
        {"tool": "Calendly", "use": "Session booking + buffer time enforcement", "cost_mo": 0},
        {"tool": "Stripe", "use": "Monthly retainer auto-charge", "cost_mo": 0},
        {"tool": "Twilio", "use": "Session reminders + last-minute reschedule alerts", "cost_mo": 2},
        {"tool": "Google Sheets + n8n", "use": "Attendance and progress tracking automation", "cost_mo": 0},
        {"tool": "Notion", "use": "Curriculum library and student notes", "cost_mo": 0},
    ),
    staff_with_automation="1 owner-tutor + 0 employees (up to 30 students)",
    monthly_savings_usd=400,
    automation_pct=0.60,
    priority_automations=(
        "Stripe recurring billing — eliminates monthly invoice chasing entirely",
        "Calendly booking — no back-and-forth scheduling texts",
        "Weekly progress report auto-email — parents feel informed without extra calls",
    ),
)

_reg(
    "daycare",
    automation_score=22,
    automated_tasks=(
        "Automated billing and tuition collection (Brightwheel)",
        "Daily attendance log app",
        "Parent pickup notification SMS",
        "Incident report digital form",
        "Enrollment inquiry auto-reply with tour booking",
        "State compliance document reminders",
        "Payroll processing (Gusto)",
    ),
    human_tasks=(
        "All child care and supervision",
        "Age-appropriate activities and education",
        "Meal preparation and feeding",
        "Nap and rest supervision",
        "Health checks and medication",
        "Parent relationship management",
        "Emergency response",
    ),
    recommended_tools=(
        {"tool": "Brightwheel", "use": "Childcare management: billing, attendance, parent app", "cost_mo": 150},
        {"tool": "Gusto", "use": "Payroll for licensed staff", "cost_mo": 40},
        {"tool": "Calendly", "use": "Tour booking for prospective parents", "cost_mo": 0},
        {"tool": "Twilio", "use": "Pickup arrival SMS notification", "cost_mo": 2},
        {"tool": "Google Forms", "use": "Digital incident and daily report forms", "cost_mo": 0},
    ),
    staff_with_automation="Owner + 1 licensed assistant (state-mandated ratio)",
    monthly_savings_usd=500,
    automation_pct=0.20,
    priority_automations=(
        "Brightwheel billing — eliminates check-chasing, parents auto-pay monthly",
        "Brightwheel parent app — replaces 20+ daily text messages to parents",
        "Calendly tour booking — no missed enrollment leads during care hours",
    ),
)

_reg(
    "laundromat",
    automation_score=88,
    automated_tasks=(
        "Card + app payment (no cash needed)",
        "Machine availability status on app (LaundryView or custom)",
        "Dryer-done SMS notification to customers",
        "Low-soap-dispenser alert to owner",
        "Machine maintenance schedule alerts",
        "Loyalty points via app (earn free dry cycles)",
        "Daily revenue report to owner phone",
        "Security camera monitoring (cloud DVR)",
    ),
    human_tasks=(
        "Machine repair and maintenance",
        "Weekly cash collection (if cash-only backup)",
        "Restocking soap dispensers and supplies",
        "Customer issue resolution",
        "Wash-dry-fold service (if offered)",
    ),
    recommended_tools=(
        {"tool": "CoinOp Solutions / PayRange", "use": "Card + mobile payment for machines", "cost_mo": 30},
        {"tool": "LaundryView or ShinePOS", "use": "Machine monitoring + customer-facing app", "cost_mo": 50},
        {"tool": "Twilio", "use": "Dryer-done SMS and maintenance alerts", "cost_mo": 5},
        {"tool": "n8n", "use": "Revenue report and alert automation", "cost_mo": 0},
        {"tool": "Hikvision NVR (Sijoy's inventory)", "use": "On-site security monitoring", "cost_mo": 0},
    ),
    staff_with_automation="1 owner visiting 2×/week (~8 hrs/month)",
    monthly_savings_usd=2_000,
    automation_pct=0.85,
    priority_automations=(
        "Card/mobile payment — replaces coin collection, eliminates theft risk",
        "Dryer-done SMS — customers leave faster, faster machine turnover = more revenue",
        "Maintenance alert → owner SMS — catch small issues before costly repair",
    ),
)

_reg(
    "check_cashing",
    automation_score=50,
    automated_tasks=(
        "Bill payment kiosk (MoneyGram, Western Union terminal)",
        "ID verification scan (reduces fraud)",
        "Digital transaction log (no paper ledger)",
        "Daily cash position report",
        "Compliance report auto-generation",
        "Prepaid card reload automation",
        "SMS receipt to customer",
    ),
    human_tasks=(
        "Check authentication and approval decisions",
        "Customer identity verification",
        "Cash disbursement",
        "Suspicious activity judgment",
        "Regulatory compliance monitoring",
        "Customer service for disputes",
    ),
    recommended_tools=(
        {"tool": "MoneyGram terminal", "use": "Bill pay + money transfer, earns commission", "cost_mo": 0},
        {"tool": "Idscan.net", "use": "ID scan and fraud check ($0.10/scan)", "cost_mo": 20},
        {"tool": "Square or custom POS", "use": "Transaction logging and reporting", "cost_mo": 0},
        {"tool": "Twilio", "use": "SMS receipt and pickup notifications", "cost_mo": 3},
    ),
    staff_with_automation="1 owner + 1 counter employee",
    monthly_savings_usd=600,
    automation_pct=0.45,
    priority_automations=(
        "ID scan — fraud detection pays for itself on first prevented loss",
        "MoneyGram terminal — earns $2-5/transaction with no extra staff time",
        "Digital transaction log — compliance reports in minutes vs hours",
    ),
)

_reg(
    "convenience_store",
    automation_score=65,
    automated_tasks=(
        "POS with inventory tracking (Square or Lightspeed)",
        "Low-stock reorder alerts to owner phone",
        "Lottery terminal self-service",
        "Surveillance camera AI motion alerts",
        "EBT/SNAP payment processing",
        "Daily sales + shrinkage report",
        "Vendor invoice scanning (auto-log to books)",
        "ATM cash-level alert",
    ),
    human_tasks=(
        "Customer service and checkout",
        "Stocking shelves and receiving deliveries",
        "Age verification for alcohol and tobacco",
        "Loss prevention judgment calls",
        "Cash register reconciliation",
        "Vendor relationship management",
    ),
    recommended_tools=(
        {"tool": "Lightspeed Retail", "use": "POS + inventory tracking + reports", "cost_mo": 69},
        {"tool": "n8n + Twilio", "use": "Low-stock SMS alert to owner", "cost_mo": 3},
        {"tool": "Hikvision NVR", "use": "AI motion alert for theft detection", "cost_mo": 0},
        {"tool": "QuickBooks Simple Start", "use": "P&L auto-sync from POS", "cost_mo": 15},
        {"tool": "When I Work free", "use": "Staff scheduling app", "cost_mo": 0},
    ),
    staff_with_automation="1 owner + 1 cashier (covers AM or PM shift)",
    monthly_savings_usd=2_000,
    automation_pct=0.58,
    priority_automations=(
        "POS inventory tracking — know what's shrinking before you lose $500/week",
        "Reorder alert — never run out of top-20 SKUs (top 20 SKUs = 60% of revenue)",
        "Surveillance AI alert — reduces shoplifting by 30-50%",
    ),
)

_reg(
    "liquor_store",
    automation_score=58,
    automated_tasks=(
        "POS with age verification prompt",
        "Inventory tracking and low-stock alerts",
        "Daily sales report",
        "Drizly / Minibar / direct delivery order management",
        "Loyalty program (Square Loyalty)",
        "Event tasting registration (Eventbrite free)",
        "Vendor invoice auto-scanning",
        "Surveillance + motion alerts",
    ),
    human_tasks=(
        "Age verification and ID check",
        "Customer craft beer / wine recommendations",
        "Receiving and stocking deliveries",
        "Tasting event hosting",
        "Loss prevention",
        "License compliance",
    ),
    recommended_tools=(
        {"tool": "Lightspeed Retail", "use": "Liquor-specific POS with age prompt", "cost_mo": 69},
        {"tool": "Drizly / Minibar", "use": "Delivery marketplace integration", "cost_mo": 0},
        {"tool": "Square Loyalty", "use": "Repeat customer rewards", "cost_mo": 45},
        {"tool": "Eventbrite free", "use": "Tasting event registration", "cost_mo": 0},
        {"tool": "n8n", "use": "Low-stock and daily report automation", "cost_mo": 0},
    ),
    staff_with_automation="1 owner + 1 part-time employee",
    monthly_savings_usd=800,
    automation_pct=0.50,
    priority_automations=(
        "Inventory POS — track craft vs national margin by SKU, cut low-margin shelf space",
        "Delivery app integration — captures $2K-5K/mo with no extra staff",
        "Tasting event registration — zero-cost event marketing that fills the calendar",
    ),
)

_reg(
    "indian_restaurant",
    automation_score=60,
    automated_tasks=(
        "Online ordering (own website via Square Online or ChowNow)",
        "DoorDash / Uber Eats / Grubhub order tablet",
        "Reservation management (OpenTable or Resy)",
        "Automated review request after dine-in visit",
        "Catering inquiry auto-reply with PDF menu",
        "Loyalty punch card (Square)",
        "Inventory recipe costing alerts",
        "Social post from food photo template",
    ),
    human_tasks=(
        "All cooking and food preparation",
        "Table service and customer interaction",
        "Menu item recommendation",
        "Catering event execution",
        "Cash handling",
        "Quality control and plating",
    ),
    recommended_tools=(
        {"tool": "ChowNow", "use": "Commission-free online ordering (vs 30% Doordash)", "cost_mo": 149},
        {"tool": "OpenTable", "use": "Reservation + guest management", "cost_mo": 0},
        {"tool": "Twilio", "use": "Review request SMS 2hrs after checkout", "cost_mo": 3},
        {"tool": "n8n", "use": "Catering auto-reply + social post scheduler", "cost_mo": 0},
        {"tool": "MarketMan", "use": "Recipe costing + waste tracking", "cost_mo": 199},
    ),
    staff_with_automation="1 owner-chef + 1 FOH staff",
    monthly_savings_usd=800,
    automation_pct=0.52,
    priority_automations=(
        "ChowNow direct ordering — saves 25-30% commission vs Doordash on every order",
        "OpenTable reservations — fills PM peaks without phone interruptions",
        "Review request SMS — 4.5+ Google rating is the #1 new-customer driver",
    ),
)

_reg(
    "halal_restaurant",
    automation_score=58,
    automated_tasks=(
        "Delivery app order management (tablet aggregator)",
        "Online catering inquiry form + auto-reply",
        "Reservation system",
        "Review request SMS",
        "Social post scheduling (Ramadan specials calendar)",
        "Loyalty stamps",
        "Inventory alerts for halal-certified proteins",
    ),
    human_tasks=(
        "All cooking",
        "Halal sourcing verification",
        "Customer service",
        "Prayer-time schedule accommodation",
        "Catering setup and service",
    ),
    recommended_tools=(
        {"tool": "Otter.ai (restaurant)", "use": "Aggregates Doordash/Uber/Grubhub into 1 tablet", "cost_mo": 49},
        {"tool": "Square POS", "use": "In-store payment + loyalty", "cost_mo": 0},
        {"tool": "Twilio", "use": "Order-ready + review SMS", "cost_mo": 3},
        {"tool": "n8n", "use": "Catering auto-reply + social scheduler", "cost_mo": 0},
        {"tool": "Google Forms", "use": "Catering order intake form", "cost_mo": 0},
    ),
    staff_with_automation="1 owner-chef + 1 counter/delivery staff",
    monthly_savings_usd=700,
    automation_pct=0.50,
    priority_automations=(
        "Delivery aggregator (Otter) — one tablet vs three, halves order error rate",
        "Catering intake form — captures community events automatically (Eid, weddings)",
        "Review SMS — Muslim community is highly referral-driven; ratings matter enormously",
    ),
)

_reg(
    "restaurant",
    automation_score=55,
    automated_tasks=(
        "Online reservation system (OpenTable / Resy)",
        "Delivery app management",
        "POS with table tracking",
        "Kitchen display system (replaces paper tickets)",
        "Review request SMS",
        "Staff scheduling (7shifts or When I Work)",
        "Inventory and recipe costing",
        "Gift card program",
    ),
    human_tasks=(
        "All cooking and food prep",
        "Table service and hospitality",
        "Menu creation and specials",
        "Wine and beverage service",
        "Customer complaint resolution",
    ),
    recommended_tools=(
        {"tool": "Toast POS", "use": "Restaurant POS + kitchen display + online ordering", "cost_mo": 0},
        {"tool": "OpenTable", "use": "Reservations + guest profiles", "cost_mo": 0},
        {"tool": "7shifts", "use": "Staff scheduling + labor cost tracking", "cost_mo": 0},
        {"tool": "MarketMan", "use": "Inventory + recipe costing", "cost_mo": 199},
        {"tool": "Twilio", "use": "Table-ready SMS for waitlist", "cost_mo": 3},
    ),
    staff_with_automation="1 owner + 2-4 kitchen + 1-2 FOH",
    monthly_savings_usd=900,
    automation_pct=0.48,
    priority_automations=(
        "Kitchen display system — eliminates lost tickets, speeds service by 15-20%",
        "Staff scheduling app — reduces labor overspend (labor is 30-35% of revenue)",
        "Recipe costing — know exact food cost per dish, price menu accordingly",
    ),
)

_reg(
    "pizza_restaurant",
    automation_score=70,
    automated_tasks=(
        "Online ordering with real-time ETA (Slice or own site)",
        "Delivery route optimization (Onfleet or Circuit)",
        "Order-ready SMS to customer",
        "Loyalty program (punch card digital)",
        "Review requests",
        "Catering order form",
        "Inventory alerts for dough and toppings",
        "Social post from weekly special",
    ),
    human_tasks=(
        "Dough making and pizza assembly",
        "Oven monitoring and timing",
        "Delivery driving",
        "Phone orders (declining)",
        "Quality control",
    ),
    recommended_tools=(
        {"tool": "Slice", "use": "Pizza-specific ordering platform + marketing", "cost_mo": 0},
        {"tool": "Toast POS", "use": "POS + online ordering + kitchen display", "cost_mo": 0},
        {"tool": "Circuit (routing)", "use": "Delivery route optimization", "cost_mo": 20},
        {"tool": "Twilio", "use": "Order-ready + delivery-arrived SMS", "cost_mo": 3},
        {"tool": "n8n", "use": "Inventory alert + review request automation", "cost_mo": 0},
    ),
    staff_with_automation="1 owner-chef + 1 delivery driver",
    monthly_savings_usd=1_000,
    automation_pct=0.65,
    priority_automations=(
        "Online ordering system — 70% of pizza orders already online; catch them or lose them",
        "Delivery route optimization — saves 1-2 hrs/day for solo driver operation",
        "Order-ready SMS — reduces arrived-early/left-early customer churn",
    ),
)

_reg(
    "real_estate",
    automation_score=72,
    automated_tasks=(
        "CRM lead follow-up sequences (HubSpot free)",
        "Listing auto-syndication to Zillow/Realtor.com/MLS",
        "Automated showing schedule via Calendly",
        "Client drip emails post-showing",
        "Review request after closing",
        "Market report auto-email to prospect list",
        "Contract e-signature (DocuSign or HelloSign)",
        "Social post from listing photos",
    ),
    human_tasks=(
        "Showing homes and reading client reactions",
        "Negotiation strategy",
        "Offer structuring and presentation",
        "Relationship building and trust",
        "Inspection and appraisal navigation",
        "Local market expertise",
    ),
    recommended_tools=(
        {"tool": "HubSpot CRM free", "use": "Lead pipeline + automated follow-up sequences", "cost_mo": 0},
        {"tool": "Calendly", "use": "Showing scheduler — no back-and-forth texts", "cost_mo": 0},
        {"tool": "HelloSign (3 free/mo)", "use": "E-signature for disclosure forms", "cost_mo": 0},
        {"tool": "Canva + Buffer", "use": "Listing social posts + open-house promotion", "cost_mo": 13},
        {"tool": "Mailchimp", "use": "Monthly market update to past clients and leads", "cost_mo": 0},
    ),
    staff_with_automation="1 solo agent (handles 4-6 active clients)",
    monthly_savings_usd=600,
    automation_pct=0.65,
    priority_automations=(
        "CRM lead sequences — follow-up is 80% of real estate; automate all of it",
        "Calendly showing scheduler — removes friction that kills deals",
        "Monthly market report email — keeps you top-of-mind when they're ready to buy/sell",
    ),
)

_reg(
    "accounting",
    automation_score=75,
    automated_tasks=(
        "Bank feed auto-sync to QuickBooks/Xero",
        "Monthly bookkeeping reconciliation (near-automated for standard clients)",
        "Invoice and billing via QuickBooks",
        "Tax deadline reminder emails to clients",
        "Stripe recurring retainer billing",
        "Client document collection portal (TaxDome)",
        "Financial report auto-generation",
        "E-signature for engagement letters",
    ),
    human_tasks=(
        "Tax strategy and planning",
        "Audit representation",
        "Advisory conversations with clients",
        "Complex transaction classification",
        "Client relationship and retention",
        "Regulatory change monitoring",
    ),
    recommended_tools=(
        {"tool": "QuickBooks Online", "use": "Bookkeeping + bank feeds + reports", "cost_mo": 30},
        {"tool": "TaxDome", "use": "Client portal + document collection + e-sign", "cost_mo": 50},
        {"tool": "Stripe", "use": "Monthly retainer auto-billing", "cost_mo": 0},
        {"tool": "Calendly", "use": "Tax consultation scheduling", "cost_mo": 0},
        {"tool": "Loom", "use": "Async client video updates (saves 1hr of calls/week)", "cost_mo": 0},
    ),
    staff_with_automation="1 owner-CPA (handles 40-60 bookkeeping clients solo)",
    monthly_savings_usd=800,
    automation_pct=0.70,
    priority_automations=(
        "Stripe recurring billing — never chase a retainer payment again",
        "TaxDome client portal — document collection that used to take 2 weeks takes 2 days",
        "Bank feed auto-sync — cuts bookkeeping time per client from 3 hrs to 45 min",
    ),
)

_reg(
    "insurance",
    automation_score=68,
    automated_tasks=(
        "CRM pipeline with renewal alerts 90/60/30 days out",
        "Automated renewal reminder emails to clients",
        "Policy document delivery via email",
        "Quote request auto-reply with intake form",
        "E-signature for applications (DocuSign)",
        "Commission tracking dashboard",
        "Review request after policy bind",
        "Birthday and anniversary check-in email",
    ),
    human_tasks=(
        "Coverage needs analysis and consultation",
        "Claims navigation and advocacy",
        "Complex risk placement",
        "Relationship maintenance for commercial clients",
        "Underwriter negotiations",
    ),
    recommended_tools=(
        {"tool": "HubSpot CRM free", "use": "Renewal pipeline + drip email sequences", "cost_mo": 0},
        {"tool": "DocuSign", "use": "Application e-signature", "cost_mo": 10},
        {"tool": "Calendly", "use": "Annual review scheduling", "cost_mo": 0},
        {"tool": "Mailchimp", "use": "Annual renewal campaign + birthday emails", "cost_mo": 0},
        {"tool": "Google Forms", "use": "New client risk intake form", "cost_mo": 0},
    ),
    staff_with_automation="1 solo agent (manages 200-400 policies)",
    monthly_savings_usd=500,
    automation_pct=0.62,
    priority_automations=(
        "Renewal alert CRM — missing a renewal is a $500-5,000 commission loss",
        "Quote intake form — captures leads at midnight when clients are researching",
        "Birthday/anniversary email — top retention tool in insurance with zero effort",
    ),
)

_reg(
    "yoga_studio",
    automation_score=68,
    automated_tasks=(
        "Class booking + waitlist (Mindbody or Pike13)",
        "Automated class reminders",
        "Membership billing (Stripe recurring)",
        "Trial-to-membership conversion email sequence",
        "Class recording delivery to online members",
        "Review requests",
        "Teacher-training inquiry auto-reply with brochure",
        "Social media class schedule post",
    ),
    human_tasks=(
        "Teaching yoga classes and adjusting students",
        "New student orientation",
        "Injury modification consultation",
        "Community building and culture",
        "Teacher training program delivery",
    ),
    recommended_tools=(
        {"tool": "Pike13 (studio mgmt)", "use": "Class booking + memberships + attendance", "cost_mo": 79},
        {"tool": "Stripe", "use": "Membership recurring billing", "cost_mo": 0},
        {"tool": "Mailchimp", "use": "Trial nurture + teacher training funnel", "cost_mo": 0},
        {"tool": "Zoom", "use": "Online class delivery for hybrid memberships", "cost_mo": 15},
        {"tool": "Twilio", "use": "Class reminder + cancellation SMS", "cost_mo": 3},
    ),
    staff_with_automation="1 owner-teacher + occasional sub-instructors (revenue share)",
    monthly_savings_usd=400,
    automation_pct=0.60,
    priority_automations=(
        "Membership auto-billing — replaces manual monthly invoicing for every member",
        "Trial-to-member email sequence — 30-day nurture converts 40-60% of trials",
        "Class reminder SMS — reduces no-shows by 35%, improves per-class revenue",
    ),
)

_reg(
    "gym",
    automation_score=60,
    automated_tasks=(
        "Membership billing (ABC Fitness or Stripe)",
        "Key fob / app door access control (24/7 unstaffed hours)",
        "Class booking system",
        "Member check-in tracking",
        "Automated non-payment suspension",
        "Review requests for new members",
        "Monthly challenge emails",
        "Lead nurture from free trial → paid membership",
    ),
    human_tasks=(
        "Personal training sessions",
        "Fitness assessments and program design",
        "Group class instruction",
        "Equipment maintenance",
        "Member motivation and retention",
        "Sales consultations for new members",
    ),
    recommended_tools=(
        {"tool": "ABC Fitness (gym mgmt)", "use": "Member billing + access control + reports", "cost_mo": 99},
        {"tool": "Kisi or Openpath", "use": "App-based door access (24/7 unmanned hours)", "cost_mo": 60},
        {"tool": "Mindbody", "use": "Class and personal training booking", "cost_mo": 79},
        {"tool": "Mailchimp", "use": "Member retention + challenge campaigns", "cost_mo": 0},
        {"tool": "Twilio", "use": "Payment failure + class reminder SMS", "cost_mo": 3},
    ),
    staff_with_automation="1 owner + 1 part-time trainer (enables 24/7 unstaffed access)",
    monthly_savings_usd=600,
    automation_pct=0.55,
    priority_automations=(
        "App door access — enables 24/7 operation without overnight staff ($2K/mo savings)",
        "Automated non-payment suspension — reduces receivables from 15% to 3%",
        "Lead nurture sequence — trial → member conversion from 20% to 45%",
    ),
)

_reg(
    "auto_repair",
    automation_score=45,
    automated_tasks=(
        "Online appointment booking (Tekmetric or Shopify booking)",
        "Automated service reminder at 3,000 miles / 3 months",
        "Digital vehicle inspection report to customer phone",
        "Parts reorder alert when below par level",
        "Invoice + Stripe payment link via SMS",
        "Review request after service completion",
        "Fleet account monthly billing (Stripe recurring)",
    ),
    human_tasks=(
        "All mechanical diagnosis and repair",
        "Parts selection and technical judgment",
        "Test drives",
        "Customer explanation of repairs",
        "Warranty and liability decisions",
        "Hazardous waste disposal compliance",
    ),
    recommended_tools=(
        {"tool": "Tekmetric", "use": "Shop management: RO, digital inspection, parts, billing", "cost_mo": 99},
        {"tool": "Stripe", "use": "SMS payment link (pay without coming in)", "cost_mo": 0},
        {"tool": "Twilio", "use": "Service reminder + review request", "cost_mo": 3},
        {"tool": "PartsTech", "use": "Parts sourcing across multiple suppliers with 1 search", "cost_mo": 0},
        {"tool": "Google Forms", "use": "Fleet account maintenance request form", "cost_mo": 0},
    ),
    staff_with_automation="1 owner-mechanic + 0-1 technician",
    monthly_savings_usd=400,
    automation_pct=0.40,
    priority_automations=(
        "Digital inspection reports — photos sent to customer phone, upsell approval rate +40%",
        "Service reminder SMS at 3 months — brings back 60% of one-time customers",
        "SMS payment link — gets paid 2 days faster than paper invoice",
    ),
)

_reg(
    "florist",
    automation_score=50,
    automated_tasks=(
        "Online ordering (own site via Shopify or Square)",
        "1-800-Flowers / FTD marketplace integration",
        "Order-ready pickup SMS",
        "Delivery route optimization",
        "Subscription arrangement billing (Stripe)",
        "Review request after delivery",
        "Valentine's / Mother's Day pre-order campaign automation",
        "Corporate account weekly order reminder",
    ),
    human_tasks=(
        "All floral design and arrangement",
        "Sourcing and selecting fresh stock",
        "Wedding consultation and design",
        "Delivery driving",
        "Perishable inventory judgment",
    ),
    recommended_tools=(
        {"tool": "Shopify Lite", "use": "Online store + POS in one", "cost_mo": 9},
        {"tool": "Circuit", "use": "Delivery route optimization", "cost_mo": 20},
        {"tool": "Stripe", "use": "Subscription weekly/monthly arrangement billing", "cost_mo": 0},
        {"tool": "Twilio", "use": "Order-ready + delivery SMS", "cost_mo": 2},
        {"tool": "Mailchimp", "use": "Holiday pre-order campaigns", "cost_mo": 0},
    ),
    staff_with_automation="1 owner + 0-1 part-time assistant",
    monthly_savings_usd=300,
    automation_pct=0.45,
    priority_automations=(
        "Online ordering — holiday online orders are 3× walk-in; capture them",
        "Subscription billing — $60-150/mo per corporate account with zero reselling",
        "Holiday campaign automation — Valentine's and Mother's Day = 40% of annual revenue",
    ),
)

_reg(
    "bookstore",
    automation_score=50,
    automated_tasks=(
        "Shopify online store (new + used books)",
        "eBay / AbeBooks marketplace listing for used books",
        "Inventory barcode scan system",
        "Event registration (Eventbrite)",
        "Email newsletter (Mailchimp)",
        "Subscription box billing (Stripe)",
        "Social media post scheduler",
        "Review request after purchase",
    ),
    human_tasks=(
        "Book curation and buying decisions",
        "Customer recommendations",
        "Author event hosting",
        "Community programming",
        "Book-buying from estate sales and donations",
    ),
    recommended_tools=(
        {"tool": "Shopify", "use": "Online storefront — critical survival tool for bookstores", "cost_mo": 29},
        {"tool": "AbeBooks Pro", "use": "Used book marketplace — free listing, 8% commission", "cost_mo": 0},
        {"tool": "Eventbrite free", "use": "Author events, book clubs, kids storytime", "cost_mo": 0},
        {"tool": "Mailchimp", "use": "Weekly newsletter — #1 retention tool for indie bookstores", "cost_mo": 0},
        {"tool": "Stripe", "use": "Subscription box recurring billing", "cost_mo": 0},
    ),
    staff_with_automation="1 owner + 0-1 part-time staff (volunteer programs work here)",
    monthly_savings_usd=300,
    automation_pct=0.48,
    priority_automations=(
        "Online store — 30-50% of indie bookstore survival now depends on online used-book sales",
        "Mailchimp newsletter — customers who receive it buy 2.3× more than those who don't",
        "Eventbrite events — free events become the acquisition channel for paid regulars",
    ),
)

_reg(
    "gift_shop",
    automation_score=55,
    automated_tasks=(
        "Shopify online store + local pickup",
        "Etsy marketplace listing (handmade/local items)",
        "Inventory sync across channels",
        "Holiday promotion email campaign",
        "Corporate gifting inquiry auto-reply with catalog",
        "Review request after purchase",
        "Subscription gift box billing (Stripe)",
        "Social post from product photo",
    ),
    human_tasks=(
        "Product curation and buying",
        "Gift wrapping and custom packaging",
        "Corporate account relationship management",
        "In-store merchandising",
        "Customer gift recommendation",
    ),
    recommended_tools=(
        {"tool": "Shopify", "use": "Online store + POS unified inventory", "cost_mo": 29},
        {"tool": "Etsy", "use": "Handmade/local product marketplace", "cost_mo": 0},
        {"tool": "Mailchimp", "use": "Holiday campaigns + corporate outreach", "cost_mo": 0},
        {"tool": "Stripe", "use": "Subscription gift box billing", "cost_mo": 0},
        {"tool": "Google Forms", "use": "Corporate gifting intake with logo upload", "cost_mo": 0},
    ),
    staff_with_automation="1 owner + 0-1 part-time (holiday season bump)",
    monthly_savings_usd=400,
    automation_pct=0.50,
    priority_automations=(
        "Shopify online store — extends reach from local to regional/national",
        "Holiday campaign automation — Q4 = 40-60% of annual gift shop revenue",
        "Corporate gifting form — $500-5,000 orders with zero additional floor time",
    ),
)

_reg(
    "electronics_store",
    automation_score=60,
    automated_tasks=(
        "Shopify / WooCommerce online store for refurb sales",
        "eBay / Swappa marketplace listing",
        "Repair ticket status SMS to customer",
        "Parts reorder alerts",
        "B2B repair contract monthly billing (Stripe)",
        "Review request after repair pickup",
        "Device buyback price calculator (web tool)",
        "Surveillance alert for after-hours",
    ),
    human_tasks=(
        "All hardware repair and diagnostics",
        "Device assessment and pricing",
        "Data backup and transfer",
        "B2B client site visits",
        "Component soldering and micro-repair",
    ),
    recommended_tools=(
        {"tool": "RepairDesk", "use": "Repair shop POS + ticket system + customer SMS", "cost_mo": 49},
        {"tool": "Shopify", "use": "Refurbished device online store", "cost_mo": 29},
        {"tool": "Swappa / eBay", "use": "Used device marketplace — zero listing fee (Swappa)", "cost_mo": 0},
        {"tool": "Stripe", "use": "B2B contract monthly billing", "cost_mo": 0},
        {"tool": "Twilio", "use": "Repair-ready SMS + pickup reminder", "cost_mo": 3},
    ),
    staff_with_automation="1 owner-tech + 0-1 part-time repair tech",
    monthly_savings_usd=600,
    automation_pct=0.55,
    priority_automations=(
        "RepairDesk ticket system — repair status SMS eliminates 10+ daily 'is it ready?' calls",
        "Refurb online store — $200-800 margin per device, no walk-in required",
        "B2B Stripe billing — school/office contracts pay on time automatically",
    ),
)


# ── public API ────────────────────────────────────────────────────────────────

def get_automation_blueprint(niche: str) -> AutomationBlueprint:
    """Return an AutomationBlueprint for the given niche. Falls back to generic."""
    if niche in _BLUEPRINTS:
        return _BLUEPRINTS[niche]

    return AutomationBlueprint(
        niche=niche,
        automation_score=45,
        automated_tasks=(
            "Online booking or order intake",
            "Payment processing (Square or Stripe)",
            "Automated appointment or order reminders via SMS",
            "Review request after service",
            "Social media post scheduling",
            "Low-stock or low-capacity alerts",
        ),
        human_tasks=(
            "Core product or service delivery",
            "Customer consultation and relationship",
            "Quality control",
            "Cash handling and sensitive transactions",
        ),
        recommended_tools=(
            {"tool": "Calendly or Square", "use": "Booking or order intake", "cost_mo": 0},
            {"tool": "Stripe or Square", "use": "Payment processing", "cost_mo": 0},
            {"tool": "Twilio", "use": "SMS reminders and review requests", "cost_mo": 3},
            {"tool": "n8n (self-hosted)", "use": "Workflow automation hub", "cost_mo": 0},
            {"tool": "Buffer free", "use": "Social media scheduling", "cost_mo": 0},
        ),
        staff_with_automation="1 owner + 0-1 part-time employee",
        monthly_savings_usd=400,
        automation_pct=0.40,
        priority_automations=(
            "Online booking or ordering — eliminates phone tag and captures off-hours leads",
            "Automated reminders — reduces no-shows and late payments by 30-50%",
            "Review request SMS — builds Google rating passively over time",
        ),
    )


def format_automation_blueprint(bp: AutomationBlueprint) -> str:
    """Return a human-readable automation summary."""
    lines = [
        f"{'━'*60}",
        f"AUTOMATION BLUEPRINT — {bp.niche.replace('_', ' ').upper()}",
        f"{'━'*60}",
        "",
        f"Automation Score   : {bp.automation_score}/100",
        f"Automation %       : {int(bp.automation_pct * 100)}% of operational tasks",
        f"Monthly Savings    : ~${bp.monthly_savings_usd:,}/mo vs fully manual operation",
        f"Staffing Model     : {bp.staff_with_automation}",
        "",
        "TOP 3 AUTOMATIONS (implement these first)",
        *[f"  {i+1}. {p}" for i, p in enumerate(bp.priority_automations)],
        "",
        "AUTOMATED TASKS",
        *[f"  ✓ {t}" for t in bp.automated_tasks],
        "",
        "MUST-REMAIN HUMAN",
        *[f"  ✗ {t}" for t in bp.human_tasks],
        "",
        "RECOMMENDED TOOLS",
        *[
            f"  {tool['tool']:<25} ${tool['cost_mo']:>4}/mo  — {tool['use']}"
            for tool in bp.recommended_tools
        ],
        "",
        f"TOTAL TOOL COST: ~${sum(t['cost_mo'] for t in bp.recommended_tools):,}/mo",
        "",
    ]
    return "\n".join(lines)
