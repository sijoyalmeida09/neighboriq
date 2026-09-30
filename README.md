# NeighborIQ

**Neighborhood business intelligence engine — find underserved niches from real-time data.**

> "There are 47 restaurants in Dorchester. Zero Vietnamese. Zero Ethiopian. The data says someone is leaving $500K/yr on the table."

NeighborIQ scrapes every real business in a zip code, compares supply vs national demand benchmarks, analyzes historical patterns, and ranks the exact niches most likely to succeed — before you sign a lease.

## What it does

```
$ python -m neighboriq analyze --zip 02122

NeighborIQ — 02122 (Dorchester, MA)
Population: 38,000  |  Median Income: $52,000

TOP OPPORTUNITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#1 [A] indian_restaurant       Score: 82  Gap: 8x
     6 existing • avg rating 3.4 • demand 71/100
     Entry capital: ~$150,000
     → 47 restaurants total. Only 6 Indian. National avg = 0.3/10k.
       Competitor quality is poor (3.4 avg rating). High search demand.

#2 [A] florist                  Score: 78  Gap: ∞
     0 existing • n/a • demand 68/100
     Entry capital: ~$50,000
```

## How it works

```
zip code
   ↓
[Google Maps scraper] → 200+ businesses, ratings, reviews
[US Census ACS]       → population, income, age, growth rate
[Google Trends]       → search demand per niche, last 12 months
[Yelp Fusion]         → supplemental reviews + sentiment
   ↓
[Saturation Analyzer] → businesses/10k vs national benchmarks
[Gap Detector]        → demand × (1/saturation) = gap score
[Sentiment Analyzer]  → VADER on reviews → competition quality
[Pattern Analyzer]    → historical success rates in similar markets
   ↓
[Opportunity Scorer]  → weighted multi-factor score (0–100)
   ↓
Ranked opportunity list + YouTube script + PDF report
```

## Installation

```bash
git clone https://github.com/joshoit/neighboriq
cd neighboriq

pip install -e ".[dev]"
playwright install chromium

cp .env.example .env
# Fill in your keys (only CENSUS_API_KEY is required for full data)
```

## Quick start

```bash
# Analyze a zip code
python -m neighboriq analyze --zip 02122

# Skip LLM analysis (faster)
python -m neighboriq analyze --zip 02122 --no-llm

# Compare two neighborhoods
python -m neighboriq compare --zips 02122,02124

# Generate YouTube script for top niche
python -m neighboriq content --zip 02122 --niche indian_restaurant

# Full run: analyze + generate content
python -m neighboriq run --zip 02122

# Database stats
python -m neighboriq stats

# One-liner via Makefile
make analyze ZIP=02122
```

## API keys

| Key | Required | Free tier | Get it |
|-----|----------|-----------|--------|
| `CENSUS_API_KEY` | Yes (for demographics) | Unlimited | [census.gov/data/key_signup.html](https://api.census.gov/data/key_signup.html) |
| `YELP_API_KEY` | No | 500 calls/day | [yelp.com/developers](https://www.yelp.com/developers/v3/manage_app) |
| `GROQ_API_KEY` | No (LLM eval) | Free tier | [console.groq.com](https://console.groq.com) |
| `ANTHROPIC_API_KEY` | No (LLM fallback) | — | [console.anthropic.com](https://console.anthropic.com) |

Google Maps and Google Trends are scraped (no key needed). Census and Yelp use official APIs.

## Scoring model

```
score = 50 (base)
      + demand_score × 0.30        # Google Trends signal (max +30)
      + supply_points               # 0–25 based on saturation ratio
      + competition_points          # 0–20 based on competitor avg rating
      + pattern_points              # 0–15 from historical success data
      + demographics_alignment      # 0–10 income vs typical capital match

Tier A = score ≥ 70 (act now)
Tier B = score 50–69 (monitor)
Tier C = score < 50 (skip)
```

## Data sources

| Source | Method | Data |
|--------|--------|------|
| Google Maps | Playwright headless | Business name, rating, reviews, address |
| US Census ACS 5-year | Official API (free key) | Population, income, age, growth |
| Google Trends | pytrends scraper | Search interest 0–100 per niche |
| Yelp Fusion | REST API | Reviews, price tier, sentiment |
| OpenStreetMap | Overpass API | Category cross-reference |

All data is cached locally in SQLite. Re-runs use cached data (no re-scraping).

## Project structure

```
neighboriq/
├── collectors/          # Data ingestion (Maps, Census, Trends, Yelp, OSM)
├── analyzers/           # Saturation, gap, sentiment, pattern analysis
├── scoring/             # Niche classifier, opportunity scorer, LLM eval
├── storage/             # SQLite ORM + artifact cache
├── content/             # YouTube script, PDF report, thumbnail generator
├── api/                 # FastAPI server (GET /analyze/{zip})
├── tests/               # Unit tests (pytest)
└── cli.py               # Entry point
```

## Run tests

```bash
pytest tests/ -v
# 11 passed in 0.02s
```

## API server

```bash
uvicorn neighboriq.api.server:app --reload --port 8000

# Endpoints
GET /analyze/{zip_code}      # opportunity scores JSON
GET /businesses/{zip_code}   # all businesses in DB
GET /content/{zip_code}      # YouTube script + LinkedIn post
```

## Known limitations

- **Google Trends rate-limiting**: pytrends gets throttled by Google (~429). Falls back to neutral score 50/100 for all niches. Use SERP API for production demand signals.
- **Census key required**: Without `CENSUS_API_KEY`, population defaults to 10,000 (scores work but are less precise).
- **Google Maps deduplication**: Businesses found across multiple category searches are deduplicated by (name, address); some category overlaps collapse into "restaurant" vs "pizza_restaurant".
- **Radius is approximate**: Google Maps search is geographic, not a strict radius filter.

## Content generation

Each analysis auto-generates a YouTube script in the "neighborhood opportunity" format:

```json
{
  "title": "The HIDDEN $500K/yr Business in Dorchester Nobody's Opened (Data Proof)",
  "hook": "47 restaurants in this zip. Zero Vietnamese. Here's what the numbers say.",
  "sections": {
    "the_data": "Saturation analysis...",
    "the_pattern": "Where this worked before...",
    "the_entry": "What you'd need to open this...",
    "the_cta": "Next week: [next zip]"
  },
  "thumbnail_text": "8x DEMAND. ZERO SUPPLY.",
  "short_script": "60-second Shorts version"
}
```

## License

MIT — use freely, attribution appreciated.

Built by Sijoy Almeida
