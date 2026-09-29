# Contributing to NeighborIQ

Thanks for wanting to improve NeighborIQ. Here's how to get started.

## Setup

```bash
git clone https://github.com/sijoyalmeida09/neighboriq
cd neighboriq
pip install -e ".[dev,scrape,api]"
python -m playwright install chromium
```

## Running tests

```bash
pytest tests/ -v
```

All 30 tests must pass before a PR is merged. No new code ships without a test.

## Areas where contributions are welcome

| Area | What's needed |
|---|---|
| **More niches** | Add to `scoring/revenue_model.py` and `scoring/automation_matrix.py` — follow the `_reg(...)` pattern. Add a test in `tests/test_v2_modules.py`. |
| **Better data** | Improve `collectors/census_cbp_collector.py` NAICS→niche mappings, or add a new collector (Yelp, Foursquare, OpenStreetMap). |
| **Dashboard** | Improve `dashboard/index.html` — dark SPA, no build step, vanilla JS only. |
| **CLI** | Add flags to `cli.py` — follow the existing argparse pattern in `_parse_args()`. |
| **Extension** | Improve `extension/popup.html` and `extension/popup.js` — vanilla JS, no npm. |
| **Docs** | Add real-world case studies to README. |

## Code conventions

- All model dataclasses must be `frozen=True` — immutability is non-negotiable
- New collectors must return `[]` on any error, never raise
- New API handlers must return human-readable text, not raw dicts
- Functions under 50 lines; files under 800 lines
- No external dependencies added without a discussion in an Issue first

## Pull Request checklist

- [ ] `pytest tests/ -v` all pass locally
- [ ] New niche/collector/feature has a corresponding test
- [ ] No secrets or API keys committed
- [ ] `data/` directory contents not committed (see `.gitignore`)

## Adding a new niche

Copy the pattern from `scoring/revenue_model.py`:

```python
_reg(
    "your_niche",
    startup_home_based=...,   # $ to start from home
    startup_small=...,        # $ for small footprint
    startup_full=...,         # $ for full storefront
    revenue_conservative=..., # $/mo low end
    revenue_median=...,       # $/mo typical
    revenue_optimistic=...,   # $/mo high end
    cogs_pct=...,             # cost of goods as % of revenue
    rent_monthly_low=...,
    rent_monthly_mid=...,
    utilities_monthly=...,
    staff_solo_monthly=...,
    staff_1_monthly=...,
    staff_2_monthly=...,
    automation_monthly_savings=...,
    model_solo_description="...",
    model_1staff_description="...",
    model_2staff_description="...",
    escalation_path="low margin entry → ... → high margin exit",
)
```

Then add the corresponding entry in `scoring/automation_matrix.py` and a keyword mapping in `scoring/niche_classifier.py`.

## Reporting bugs

Open a GitHub Issue with:
- The zip code you analyzed
- The command you ran
- The full error output
- Your Python version (`python --version`)
