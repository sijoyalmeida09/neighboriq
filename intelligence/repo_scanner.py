"""repo_scanner.py — Auto-detect business domain and profile from any codebase.

Run `neighboriq init` inside any repo to get a partial BizProfile without filling
any YAML — this module reads the codebase like a business analyst.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

__all__ = ["RepoScan", "scan_repo", "format_scan_summary", "interactive_topup"]

_DEBUG = os.environ.get("NEIGHBORIQ_DEBUG", "") == "1"


def _dbg(msg: str) -> None:
    if _DEBUG:
        import sys
        print(f"[repo_scanner] {msg}", file=sys.stderr)


# ── Domain keyword taxonomy ───────────────────────────────────────────────────

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "software_saas": ["saas", "subscription", "api", "platform", "dashboard", "analytics", "crm", "b2b", "tenant"],
    "logistics": ["logistics", "trucking", "freight", "delivery", "shipping", "fleet", "dispatch", "route", "carrier"],
    "distribution": ["distributor", "wholesale", "supply chain", "fulfillment", "warehouse", "inventory", "sku"],
    "food_beverage": ["restaurant", "food", "beverage", "kitchen", "menu", "dining", "catering", "recipe", "cafe"],
    "retail": ["store", "shop", "retail", "inventory", "pos", "point of sale", "ecommerce", "cart", "checkout"],
    "healthcare": ["health", "medical", "patient", "clinic", "telehealth", "ehr", "hipaa", "care", "provider"],
    "music_entertainment": ["music", "artist", "booking", "venue", "event", "entertainment", "streaming", "royalt"],
    "agency_services": ["agency", "marketing", "consulting", "design", "seo", "advertising", "client", "campaign"],
    "real_estate": ["real estate", "property", "rent", "lease", "landlord", "tenant", "mortgage", "listing"],
    "education": ["education", "learning", "course", "student", "tutor", "school", "curriculum", "lesson", "lms"],
    "professional_services": ["legal", "accounting", "law", "cpa", "tax", "finance", "insurance", "audit", "compliance"],
    "local_service": ["local", "neighborhood", "salon", "barbershop", "repair", "laundry", "cleaning", "plumb"],
    "manufacturing": ["manufacturing", "production", "factory", "fabrication", "assembly", "machining", "cnc"],
    "creative_media": ["media", "content", "video", "photo", "studio", "podcast", "creative", "broadcast", "film"],
}

# Package name → (payment_integration_label, business_model_signal, domain_hint)
_PAYMENT_SIGNALS: dict[str, tuple[str, str, str]] = {
    "stripe": ("stripe", "subscription", "software_saas"),
    "@stripe/stripe-js": ("stripe", "subscription", "software_saas"),
    "square": ("square", "point_of_sale", "retail"),
    "squareup": ("square", "point_of_sale", "retail"),
    "shopify": ("shopify", "e_commerce", "retail"),
    "@shopify/shopify-api": ("shopify", "e_commerce", "retail"),
    "paypal": ("paypal", "marketplace", "retail"),
    "paypalrestsdk": ("paypal", "marketplace", "retail"),
    "plaid": ("plaid", "fintech", "professional_services"),
    "razorpay": ("razorpay", "india_payments", "software_saas"),
    "cashfree": ("cashfree", "india_payments", "software_saas"),
    "twilio": ("twilio", "communications", "logistics"),
    "sendgrid": ("sendgrid", "email_marketing", "agency_services"),
    "@sendgrid/mail": ("sendgrid", "email_marketing", "agency_services"),
    "mailchimp": ("mailchimp", "email_marketing", "agency_services"),
}

# Package name → (integration_label, domain_hint)
_INTEGRATION_SIGNALS: dict[str, tuple[str, str]] = {
    "supabase": ("supabase", "software_saas"),
    "@supabase/supabase-js": ("supabase", "software_saas"),
    "firebase": ("firebase", "software_saas"),
    "firebase-admin": ("firebase", "software_saas"),
    "openai": ("openai", "software_saas"),
    "@anthropic-ai/sdk": ("anthropic", "software_saas"),
    "anthropic": ("anthropic", "software_saas"),
    "aws-sdk": ("aws", "software_saas"),
    "@aws-sdk/client-s3": ("aws", "software_saas"),
    "boto3": ("aws", "software_saas"),
    "googlemaps": ("google_maps", "logistics"),
    "@googlemaps/js-api-loader": ("google_maps", "logistics"),
    "google-maps": ("google_maps", "local_service"),
    "playwright": ("playwright", "agency_services"),
    "puppeteer": ("puppeteer", "agency_services"),
    "quickbooks": ("quickbooks", "professional_services"),
    "node-quickbooks": ("quickbooks", "professional_services"),
    "xero-node": ("xero", "professional_services"),
    "redis": ("redis", "software_saas"),
    "ioredis": ("redis", "software_saas"),
    "fastapi": ("fastapi", "software_saas"),
    "django": ("django", "software_saas"),
    "flask": ("flask", "software_saas"),
    "next": ("nextjs", "software_saas"),
    "react": ("react", "software_saas"),
    "vue": ("vue", "software_saas"),
    "nuxt": ("nuxt", "software_saas"),
    "express": ("express", "software_saas"),
    "uvicorn": ("fastapi", "software_saas"),
}

# Framework detection from package names
_FRAMEWORK_MAP: dict[str, str] = {
    "next": "nextjs", "react": "react", "vue": "vue", "nuxt": "nuxt",
    "svelte": "svelte", "angular": "angular", "express": "express",
    "fastapi": "fastapi", "django": "django", "flask": "flask",
    "fastify": "fastify", "nestjs": "nestjs", "hono": "hono",
    "rails": "rails", "laravel": "laravel", "spring": "spring",
    "tauri": "tauri", "electron": "electron", "flutter": "flutter",
}

_ALWAYS_MISSING = (
    "monthly_revenue", "monthly_expenses", "cash_on_hand",
    "credit_line", "monthly_debt_service", "avg_rating", "review_count",
)

# ── Output dataclass ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RepoScan:
    languages: tuple[str, ...]
    frameworks: tuple[str, ...]
    payment_integrations: tuple[str, ...]
    key_integrations: tuple[str, ...]

    detected_domain: str | None
    domain_confidence: float
    business_model_signals: tuple[str, ...]

    contributor_count: int
    repo_age_years: float
    commit_velocity_90d: int
    has_tests: bool
    has_ci: bool
    has_docker: bool
    has_admin_panel: bool
    is_deployed: bool

    readme_excerpt: str
    env_var_names: tuple[str, ...]

    inferred_headcount_min: int
    inferred_headcount_max: int
    inferred_years_in_market: int
    inferred_digital_assets: tuple[str, ...]
    inferred_software_tools: tuple[str, ...]

    missing_fields: tuple[str, ...]
    summary: str


# ── Sub-scanners ──────────────────────────────────────────────────────────────

def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}


def _detect_stack(root: Path) -> tuple[list[str], list[str], list[str], list[str]]:
    languages: list[str] = []
    frameworks: list[str] = []
    payments: list[str] = []
    integrations: list[str] = []
    domain_votes: dict[str, int] = {}

    all_deps: set[str] = set()

    # package.json
    pkg = _read_json(root / "package.json")
    if pkg:
        languages.append("javascript")
        if "typescript" in pkg.get("devDependencies", {}):
            languages.append("typescript")
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        all_deps.update(k.lower() for k in deps)
        _dbg(f"package.json deps: {list(deps)[:10]}")

    # pyproject.toml / requirements.txt / setup.py
    for pyfile in ["pyproject.toml", "requirements.txt", "setup.py"]:
        if (root / pyfile).exists():
            languages.append("python")
            try:
                text = (root / pyfile).read_text(encoding="utf-8", errors="ignore").lower()
                for line in text.splitlines():
                    m = re.match(r"^\s*([a-z][a-z0-9_\-]+)", line)
                    if m:
                        all_deps.add(m.group(1))
            except Exception:
                pass
            break

    if (root / "go.mod").exists():
        languages.append("go")
    if (root / "Cargo.toml").exists():
        languages.append("rust")
    if (root / "pom.xml").exists() or list(root.glob("build.gradle*")):
        languages.append("java")
    if (root / "pubspec.yaml").exists():
        languages.append("dart")
    if (root / "composer.json").exists():
        languages.append("php")
    if (root / "Gemfile").exists():
        languages.append("ruby")
    if list(root.rglob("*.csproj")):
        languages.append("csharp")

    # Map deps to signals
    for dep in all_deps:
        dep_lower = dep.lower().lstrip("@").split("/")[-1]

        if dep in _PAYMENT_SIGNALS or dep_lower in _PAYMENT_SIGNALS:
            label, biz_model, domain = _PAYMENT_SIGNALS.get(dep) or _PAYMENT_SIGNALS.get(dep_lower, ("", "", ""))
            if label and label not in payments:
                payments.append(label)
            if domain:
                domain_votes[domain] = domain_votes.get(domain, 0) + 2

        if dep in _INTEGRATION_SIGNALS or dep_lower in _INTEGRATION_SIGNALS:
            label, domain = _INTEGRATION_SIGNALS.get(dep) or _INTEGRATION_SIGNALS.get(dep_lower, ("", ""))
            if label and label not in integrations:
                integrations.append(label)
            if domain:
                domain_votes[domain] = domain_votes.get(domain, 0) + 1

        fw = _FRAMEWORK_MAP.get(dep_lower)
        if fw and fw not in frameworks:
            frameworks.append(fw)

    return (
        list(dict.fromkeys(languages)),
        list(dict.fromkeys(frameworks)),
        payments,
        integrations,
    )


def _detect_domain(
    stack_signals: list[str],
    readme_text: str,
    env_vars: list[str],
    domain_votes: dict[str, int] | None = None,
) -> tuple[str | None, float]:
    votes: dict[str, int] = dict(domain_votes or {})
    text = (readme_text + " " + " ".join(env_vars) + " " + " ".join(stack_signals)).lower()

    for domain, keywords in _DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                votes[domain] = votes.get(domain, 0) + 1

    if not votes:
        return None, 0.0

    total = sum(votes.values())
    best = max(votes, key=lambda d: votes[d])
    confidence = votes[best] / total if total > 0 else 0.0

    if confidence < 0.30:
        return None, confidence

    return best, round(confidence, 2)


def _run_git_signals(root: Path) -> tuple[int, float, int]:
    def _run(cmd: list[str]) -> str:
        try:
            result = subprocess.run(
                cmd, cwd=str(root), capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return ""

    # Contributor count
    contributors_raw = _run(["git", "shortlog", "-s", "-n", "HEAD", "--no-merges"])
    contributor_count = len([l for l in contributors_raw.splitlines() if l.strip()]) or 1

    # Repo age
    first_year_raw = _run(["git", "log", "--reverse", "--format=%ad", "--date=format:%Y"])
    first_year = 0
    for line in first_year_raw.splitlines():
        try:
            first_year = int(line.strip())
            break
        except ValueError:
            continue
    repo_age = round((datetime.now().year - first_year) + 0.5, 1) if first_year else 0.5

    # Commit velocity
    velocity_raw = _run(["git", "log", "--since=90 days ago", "--oneline"])
    velocity = len([l for l in velocity_raw.splitlines() if l.strip()])

    return contributor_count, repo_age, velocity


def _scan_filesystem(root: Path) -> tuple[bool, bool, bool, bool, bool]:
    def exists(*parts: str) -> bool:
        return any((root / p).exists() for p in parts)

    has_tests = exists("tests", "test", "__tests__", "spec", "e2e")
    has_ci = exists(".github/workflows", ".gitlab-ci.yml", ".circleci", "Jenkinsfile")
    has_docker = exists("Dockerfile", "docker-compose.yml", "docker-compose.yaml")
    has_admin = exists("admin", "apps/admin", "src/admin", "dashboard", "back-office")
    has_webhook = any(root.rglob("webhook*")) or any(root.rglob("*/webhooks*"))
    is_deployed = has_ci and has_docker

    return has_tests, has_ci, has_docker, has_admin, is_deployed


def _extract_readme(root: Path) -> str:
    for name in ("README.md", "README.rst", "README.txt", "readme.md"):
        p = root / name
        if p.exists():
            try:
                return p.read_text(encoding="utf-8", errors="ignore")[:300]
            except Exception:
                pass
    return ""


def _extract_env_var_names(root: Path) -> list[str]:
    for name in (".env.example", ".env.template", ".env.sample", ".env.local.example"):
        p = root / name
        if p.exists():
            try:
                lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
                names = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        names.append(line.split("=")[0].strip())
                return names
            except Exception:
                pass
    return []


def _infer_digital_assets(
    has_ci: bool,
    has_docker: bool,
    has_admin: bool,
    is_deployed: bool,
    frameworks: list[str],
    integrations: list[str],
) -> list[str]:
    assets = ["GitHub repository"]
    if "nextjs" in frameworks or "react" in frameworks or "vue" in frameworks:
        assets.append("Web application")
    if "fastapi" in frameworks or "django" in frameworks or "flask" in frameworks or "express" in frameworks:
        assets.append("API / backend service")
    if has_admin:
        assets.append("Admin dashboard")
    if has_ci:
        assets.append("CI/CD pipeline")
    if has_docker:
        assets.append("Containerised deployment")
    if is_deployed:
        assets.append("Live production system")
    if "supabase" in integrations or "firebase" in integrations:
        assets.append("Managed database + auth")
    if "openai" in integrations or "anthropic" in integrations:
        assets.append("AI integration")
    return assets


def _build_missing_fields(has_physical: bool = False) -> list[str]:
    fields = list(_ALWAYS_MISSING)
    if not has_physical:
        fields += ["vehicles", "sqft_owned", "sqft_leased", "real_estate_value"]
    fields += ["email_list_size", "monthly_web_traffic", "years_in_market"]
    return fields


# ── Main entry point ──────────────────────────────────────────────────────────

def scan_repo(root_path: str | None = None) -> RepoScan:
    """Scan the repo at root_path (default: cwd) and return a RepoScan.
    Never raises — all sub-scanners fail gracefully.
    """
    root = Path(root_path or os.getcwd()).resolve()
    _dbg(f"scanning {root}")

    # Stack
    languages, frameworks, payments, integrations = _detect_stack(root)

    # Env vars
    env_vars = _extract_env_var_names(root)

    # Business model signals from env var names
    biz_signals: list[str] = []
    for var in env_vars:
        v = var.upper()
        if "STRIPE" in v:
            biz_signals.append("subscription")
        if "SQUARE" in v:
            biz_signals.append("point_of_sale")
        if "SHOPIFY" in v:
            biz_signals.append("e_commerce")
        if "RAZORPAY" in v or "CASHFREE" in v:
            biz_signals.append("india_payments")

    # Domain detection
    readme = _extract_readme(root)
    all_text_signals = payments + integrations + frameworks + languages
    domain, confidence = _detect_domain(all_text_signals, readme, env_vars)

    # Git signals
    contributors, age_years, velocity = _run_git_signals(root)

    # Filesystem signals
    has_tests, has_ci, has_docker, has_admin, is_deployed = _scan_filesystem(root)

    # Inferred assets
    digital_assets = _infer_digital_assets(has_ci, has_docker, has_admin, is_deployed, frameworks, integrations)
    tools = list(dict.fromkeys(frameworks + [i for i in integrations if i not in frameworks]))

    # Headcount estimate from contributors
    hc_min = max(1, contributors)
    hc_max = max(hc_min, contributors * 2)  # contributors are often a fraction of actual team

    years_in_market = max(0, int(age_years))

    missing = _build_missing_fields()

    summary_parts = []
    if languages:
        summary_parts.append(f"{' + '.join(languages[:3]).title()} project")
    if domain:
        summary_parts.append(f"detected as {domain.replace('_', ' ')} ({int(confidence * 100)}% confidence)")
    if is_deployed:
        summary_parts.append("appears to be live in production")
    summary = "; ".join(summary_parts) or "repository scanned — domain unclear, manual profile recommended"

    return RepoScan(
        languages=tuple(dict.fromkeys(languages)),
        frameworks=tuple(dict.fromkeys(frameworks)),
        payment_integrations=tuple(payments),
        key_integrations=tuple(integrations),
        detected_domain=domain,
        domain_confidence=confidence,
        business_model_signals=tuple(dict.fromkeys(biz_signals)),
        contributor_count=contributors,
        repo_age_years=age_years,
        commit_velocity_90d=velocity,
        has_tests=has_tests,
        has_ci=has_ci,
        has_docker=has_docker,
        has_admin_panel=has_admin,
        is_deployed=is_deployed,
        readme_excerpt=readme[:300],
        env_var_names=tuple(env_vars),
        inferred_headcount_min=hc_min,
        inferred_headcount_max=hc_max,
        inferred_years_in_market=years_in_market,
        inferred_digital_assets=tuple(digital_assets),
        inferred_software_tools=tuple(tools[:15]),
        missing_fields=tuple(missing),
        summary=summary,
    )


# ── Formatting ────────────────────────────────────────────────────────────────

def format_scan_summary(scan: RepoScan) -> str:
    W = 52
    SEP = "─" * W

    lang_str = " + ".join(scan.languages[:4]).title() or "Unknown"
    fw_str = ", ".join(scan.frameworks[:4]) or "—"
    pay_str = ", ".join(scan.payment_integrations) or "None detected"
    domain_str = (
        f"{scan.detected_domain.replace('_', ' ')} ({int(scan.domain_confidence * 100)}% confidence)"
        if scan.detected_domain else "Unknown — answer questions below to detect"
    )
    age_str = f"{scan.repo_age_years:.1f} years"
    deploy_str = "Yes" if scan.is_deployed else "No"
    assets_str = "\n            ".join(scan.inferred_digital_assets) or "—"
    tools_str = ", ".join(scan.inferred_software_tools[:8]) or "—"
    missing_q = [
        ("Monthly revenue", "monthly_revenue", "$"),
        ("Monthly expenses", "monthly_expenses", "$"),
        ("Cash on hand", "cash_on_hand", "$"),
        ("Physical assets?", "physical_assets", "y/n"),
        ("Approx customers", "customer_count", "#"),
    ]

    lines = [
        f"── REPO SCAN COMPLETE {'─' * (W - 21)}",
        f"Stack:      {lang_str} ({fw_str})",
        f"Payments:   {pay_str}",
        f"Domain:     {domain_str}",
        f"Age:        {age_str} | Contributors: {scan.contributor_count} | Velocity: {scan.commit_velocity_90d} commits/90d",
        f"Deployed:   {deploy_str} (CI={scan.has_ci} Docker={scan.has_docker} Tests={scan.has_tests})",
        "",
        f"── INFERRED BUSINESS PROFILE {'─' * (W - 28)}",
        f"Team size:  {scan.inferred_headcount_min}–{scan.inferred_headcount_max} people (from git contributors)",
        f"Market age: {scan.inferred_years_in_market}+ years",
        f"Assets:     {assets_str}",
        f"Tools:      {tools_str}",
        "",
        f"── WHAT I NEED FROM YOU ({len(missing_q)} questions) {'─' * max(0, W - 34)}",
    ]
    for i, (label, _, unit) in enumerate(missing_q, 1):
        lines.append(f"  {i}. {label}: {unit}___")

    return "\n".join(lines)


# ── Interactive top-up ────────────────────────────────────────────────────────

def _parse_money(raw: str) -> int:
    """Parse '$8,000/mo', '8K', '8000' → int dollars."""
    raw = raw.strip().lower().replace(",", "").replace("$", "").replace("/mo", "").replace("/month", "")
    try:
        if raw.endswith("k"):
            return int(float(raw[:-1]) * 1000)
        if raw.endswith("m"):
            return int(float(raw[:-1]) * 1_000_000)
        return int(float(raw))
    except ValueError:
        return 0


def _parse_bool(raw: str) -> bool:
    return raw.strip().lower() in ("y", "yes", "true", "1")


_TOPUP_QUESTIONS: list[tuple[str, str, str]] = [
    ("Monthly revenue", "monthly_revenue", "money"),
    ("Monthly expenses (rent + payroll + all costs)", "monthly_expenses", "money"),
    ("Cash on hand right now", "cash_on_hand", "money"),
    ("Credit line available", "credit_line", "money"),
    ("Do you have physical assets (equipment, vehicles, real estate)?", "has_physical", "bool"),
    ("Approx number of active customers", "customer_count", "int"),
    ("Average customer rating (1-5, or press Enter to skip)", "avg_rating", "float_opt"),
    ("Email list size (0 if none)", "email_list_size", "int"),
]


def interactive_topup(scan: RepoScan) -> dict[str, object]:
    """Prompt the user for fields we couldn't infer. Returns dict of field→value."""
    print("\n── QUICK PROFILE QUESTIONS ─────────────────────────────")
    print("   (Press Enter to skip any field)\n")

    answers: dict[str, object] = {}
    for label, key, kind in _TOPUP_QUESTIONS:
        try:
            raw = input(f"  {label}: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw:
            continue
        if kind == "money":
            answers[key] = _parse_money(raw)
        elif kind == "bool":
            answers[key] = _parse_bool(raw)
        elif kind == "int":
            try:
                answers[key] = int(raw.replace(",", ""))
            except ValueError:
                pass
        elif kind == "float_opt":
            try:
                answers[key] = float(raw)
            except ValueError:
                pass
        else:
            answers[key] = raw

    return answers
