# NeighborIQ v2

**Neighborhood business intelligence engine — find underserved niches from real-time data.**

> "There are 47 restaurants in Dorchester. Zero Vietnamese. Zero Ethiopian. The data says someone is leaving $500K/yr on the table."

NeighborIQ scrapes every real business in a zip code, compares supply vs national demand benchmarks, models the full P&L before you sign a lease, and generates YouTube video scripts for each opportunity.

---

## What it does

```
$ python -m neighboriq analyze --zip 02122 --depth full

NeighborIQ — 02122 (Dorchester, MA)
Population: 38,000  |  Median Income: $52,000

TOP OPPORTUNITIES (full P&L)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#1 [A] barbershop      Score: 82  Gap: 4x
     Startup:  $5K (home) → $15K (small) → $30K (full)
     Revenue:  $5K–$8K–$16K/mo (conservative/median/optimistic)
     Net solo: 63%  →  $5,040/mo   Payback: 3 months
     1 staff:  38%  →  $3,040/mo   Payback: 5 months
     Automate: online booking + POS + inventory  saves $700/mo
     Path:     chair → booth rental ($1K-2K/chair passive) → 2nd location
```

---

## v2 Feature Map

| Feature | Command / Endpoint |
|---|---|
| Analyze a zip | `python -m neighboriq analyze --zip 02122` |
| Full P&L depth | `--depth full` |
| Asset-based filter | `--assets '{"capital_usd":5000,"skills":["teaching"]}'` |
| Analyze a business URL | `python -m neighboriq analyze-business --url https://example.com` |
| Content pipeline (scripts) | `python -m neighboriq.content.pipeline --zip 02122 --top 3` |
| Web dashboard | `.\neighboriq-start.ps1` → http://localhost:8000 |
| REST API | `GET /analyze/{zip}`, `GET /revenue-model/{niche}`, `POST /asset-filter` |
| MCP server | Registered in `.mcp.json` — 6 Claude Code tools |
| Chrome extension | Load `extension/` as unpacked → auto-detects zip on Google Maps |
| PM2 | `.\neighboriq-start.ps1 -Pm2` |

---

## Quickstart

```powershell
# Install deps
pip install playwright fastapi uvicorn rich requests
python -m playwright install chromium

# Run analysis
cd C:\Sijoy_2.0\automation
$env:PYTHONPATH = "C:\Sijoy_2.0\automation"
python -m neighboriq analyze --zip 02122

# Start web dashboard (foreground)
.\neighboriq\neighboriq-start.ps1

# Run tests (30 passing)
python -m pytest neighboriq/tests/ -v
```

---

## How it works

```
zip code
  → Google Maps scraper (Playwright)   — every business + category
  → [optional] SafeGraph Places CSV    — 8M+ US POIs, set SAFEGRAPH_DIR
  → [optional] Census CBP API          — exact establishment counts by NAICS
  → Niche classifier                   — assigns each business to 1 of 50+ niches
  → Saturation analyzer                — actual density vs national benchmark
  → Demand scorer                      — Google Trends + demographics
  → Revenue model                      — startup tiers, margins, payback (25 niches)
  → Automation matrix                  — automation savings per niche
  → LLM evaluator                      — Groq → Anthropic → template fallback
  → Gap detector                       — tiers A / B / C
  → Display / API / MCP / Extension    — multiple output surfaces
```

---

## Data Sources

| Source | Type | Setup |
|---|---|---|
| Google Maps | Playwright scraper | Built-in (no key needed) |
| SafeGraph Places | CSV (8M+ POIs) | Set `SAFEGRAPH_DIR` → [free academic](https://www.safegraph.com/free-data/places-data) |
| US Census CBP | API | Free ≤500/day; `CENSUS_API_KEY` → [signup](https://api.census.gov/data/key_signup.html) |
| Overpass (OSM) | API | Built-in fallback |
| Yelp Fusion | API | Set `YELP_API_KEY` |

**Best Kaggle datasets to pair with NeighborIQ:**
- `safegraph-core-places` — 8M POI visits + hours
- `uscensusbureau/acs5` — income, race, age by zip (American Community Survey)
- `deptofed/bls-quarterly-census-employment-wages` — employer count by NAICS
- `thedevastator/us-homeprice-index-by-zip` — rent proxy (CoreLogic)
- `zillow/zillow-rent-index` — median gross rent by zip

---

## Revenue Model (25 niches)

```python
from neighboriq.scoring.revenue_model import get_revenue_model, list_niches

m = get_revenue_model("barbershop", {})
print(m.revenue_median)          # 8000  ($/mo)
print(m.net_margin_solo_pct)     # 63.0  (%)
print(m.payback_solo_months)     # 3
print(m.startup_home_based)      # 5000  ($)
print(m.escalation_path)         # "chair → booth rental → 2nd location"

print(list_niches())             # all 25 supported niches
```

---

## Asset-Based Filtering

```python
from neighboriq.analyzers.asset_mapper import AssetProfile, filter_by_assets

profile = AssetProfile(
    capital_usd=5000,
    skills=("teaching", "math"),
    licenses=(),
    space_sqft=0,
    has_vehicle=False,
    existing_customers=0,
    monthly_overhead_max=500,
    prefers_home_based=True,
    hours_per_week=20,
)
results = filter_by_assets(opportunities, profile)
# → tutoring_center first (home-based, $500 entry, skill match)
```

CLI: `--assets '{"capital_usd":5000,"skills":["teaching"]}'`

---

## MCP Tools (Claude Code)

| Tool | Description |
|---|---|
| `analyze_neighborhood` | Analyze a zip code |
| `get_revenue_model` | Full P&L for a niche |
| `filter_by_assets` | Filter by capital/skills/space |
| `compare_neighborhoods` | Compare two zips |
| `get_neighborhood_stats` | DB stats |
| `analyze_business` | URL → revenue gaps |

---

## Chrome Extension

1. Chrome → `chrome://extensions` → Enable Developer Mode
2. "Load unpacked" → select `automation/neighboriq/extension/`
3. Navigate to Google Maps → extension auto-detects zip
4. Click the NeighborIQ icon → top opportunities instantly

Requires API running on `localhost:8000`.

---

## Environment Variables

```bash
GROQ_API_KEY=gsk_...           # Free tier LLM (llama-3.3-70b)
ANTHROPIC_API_KEY=sk-ant-...   # Fallback LLM

SAFEGRAPH_DIR=/path/to/csv/    # SafeGraph Places CSV folder
CENSUS_API_KEY=...             # census.gov (free, <500 calls/day without key)
YELP_API_KEY=...               # Yelp Fusion

TELEGRAM_BOT_TOKEN=...         # Content pipeline Telegram preview
TELEGRAM_CHAT_ID=...
```

---

## Directory Structure

```
automation/neighboriq/
├── cli.py                       # Entry point
├── mcp_server.py                # JSON-RPC 2.0 stdio MCP server
├── ecosystem.config.js          # PM2 config
├── neighboriq-start.ps1         # Windows startup script
├── analyzers/
│   ├── asset_mapper.py          # Filter by capital/skills/space
│   └── domain_analyzer.py      # URL → revenue gap analysis
├── collectors/
│   ├── google_maps_collector.py # Playwright scraper
│   ├── safegraph_collector.py   # SafeGraph CSV loader (optional)
│   └── census_cbp_collector.py  # US Census CBP API (optional)
├── content/
│   ├── pipeline.py              # Auto-generate scripts for top opportunities
│   └── video_generator.py      # YouTube script engine
├── scoring/
│   ├── revenue_model.py         # Full P&L (25 niches, frozen dataclasses)
│   └── automation_matrix.py    # Automation blueprint per niche
├── api/server.py                # FastAPI: dashboard + REST
├── dashboard/index.html         # Dark-theme SPA
├── extension/                   # Chrome Manifest v3 extension
└── tests/
    ├── test_scoring.py          # Original unit tests
    └── test_v2_modules.py       # v2 tests (30 passing)
```

---

Built by [Sijoy Almeida](https://github.com/sijoy) · NeighborIQ is part of the Sijoy 2.0 autonomous OS.
