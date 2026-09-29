"""report_generator.py — Professional HTML/PDF business opportunity report generator.

Produces a self-contained HTML report (and optionally PDF via weasyprint) for a
neighborhood's top business opportunities.
"""
from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

log = logging.getLogger("report_generator")

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "data" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

_CSS = """
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #1a1a2e; color: #e8e8f0; line-height: 1.6;
  }
  .wrapper { max-width: 800px; margin: 0 auto; padding: 24px 16px; }
  /* ── Header ── */
  .header {
    background: #0f3460; border-radius: 12px;
    padding: 32px; margin-bottom: 24px; text-align: center;
  }
  .header h1 { font-size: 1.8rem; color: #fff; margin-bottom: 8px; }
  .header .subtitle { color: #a0aec0; font-size: 0.95rem; }
  .badge {
    display: inline-block; background: #e94560; color: #fff;
    border-radius: 20px; padding: 4px 16px; font-size: 0.8rem;
    font-weight: 600; margin-top: 12px; letter-spacing: 0.5px;
  }
  /* ── Cards ── */
  .card {
    background: #16213e; border-radius: 10px;
    padding: 24px; margin-bottom: 20px;
  }
  .card h2 { font-size: 1.1rem; color: #e94560; margin-bottom: 16px;
              text-transform: uppercase; letter-spacing: 1px; font-size: 0.85rem; }
  /* ── Demographic table ── */
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #0f3460; }
  th { color: #a0aec0; font-weight: 500; font-size: 0.85rem; }
  td { color: #e8e8f0; font-size: 0.95rem; }
  /* ── Opportunity cards ── */
  .opp-card { border: 1px solid #0f3460; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
  .opp-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
  .opp-name { font-size: 1.1rem; font-weight: 600; color: #fff; }
  .score-badge {
    background: #e94560; color: #fff; border-radius: 6px;
    padding: 4px 12px; font-weight: 700; font-size: 1rem;
  }
  .score-badge.tier-a { background: #38a169; }
  .score-badge.tier-b { background: #d69e2e; }
  .score-badge.tier-c { background: #718096; }
  .score-bar-bg { background: #0f3460; border-radius: 4px; height: 6px; margin: 8px 0; }
  .score-bar { background: #e94560; border-radius: 4px; height: 6px; }
  .score-bar.tier-a { background: #38a169; }
  .score-bar.tier-b { background: #d69e2e; }
  .opp-meta { color: #a0aec0; font-size: 0.85rem; }
  /* ── Risk / strategy text ── */
  .prose { color: #cbd5e0; font-size: 0.95rem; line-height: 1.7; }
  .prose p { margin-bottom: 10px; }
  ul.risk-list { padding-left: 20px; color: #cbd5e0; font-size: 0.95rem; }
  ul.risk-list li { margin-bottom: 6px; }
  /* ── Footer ── */
  .footer { text-align: center; color: #4a5568; font-size: 0.8rem; margin-top: 32px; padding-top: 16px;
            border-top: 1px solid #2d3748; }
  .footer a { color: #e94560; text-decoration: none; }
</style>
"""


def _score_bar(score: int, tier: str) -> str:
    tier_class = f"tier-{tier.lower()}"
    return (
        f'<div class="score-bar-bg">'
        f'<div class="score-bar {tier_class}" style="width:{score}%"></div>'
        f"</div>"
    )


def _format_currency(value: int | float) -> str:
    return f"${int(value):,}"


def _safe_text(value: object) -> str:
    return str(value) if value else "—"


def generate_html_report(
    zip_code: str,
    city: str,
    state: str,
    demographics: dict,
    opportunities: list[dict],
    businesses: list[dict],
    llm_analysis: dict,
) -> str:
    today = date.today().strftime("%B %d, %Y")
    top_5 = sorted(opportunities, key=lambda x: x.get("opportunity_score", 0), reverse=True)[:5]

    # Competitor landscape: worst-rated first (most opportunity)
    sorted_businesses = sorted(
        [b for b in businesses if b.get("rating", 0) > 0],
        key=lambda x: x.get("rating", 5.0),
    )[:10]

    # ── opportunity cards ─────────────────────────────────────────────────────
    opp_cards_html = ""
    for opp in top_5:
        niche = opp.get("niche", "").replace("_", " ").title()
        score = opp.get("opportunity_score", 0)
        tier = opp.get("tier", "C")
        saturation = opp.get("saturation_ratio", 0.0)
        demand = opp.get("demand_score", 0)
        count = opp.get("competitor_count", 0)
        capital = opp.get("typical_capital_req", 0)
        tier_class = f"tier-{tier.lower()}"
        opp_cards_html += f"""
        <div class="opp-card">
          <div class="opp-header">
            <span class="opp-name">{niche}</span>
            <span class="score-badge {tier_class}">Score: {score} &nbsp;|&nbsp; Tier {tier}</span>
          </div>
          {_score_bar(score, tier)}
          <div class="opp-meta">
            {count} existing competitors &nbsp;·&nbsp;
            {saturation:.2f}× national average &nbsp;·&nbsp;
            Demand: {demand}/100 &nbsp;·&nbsp;
            Est. capital: {_format_currency(capital)}
          </div>
        </div>
        """

    # ── competitor table ──────────────────────────────────────────────────────
    comp_rows = ""
    for b in sorted_businesses:
        rating = b.get("rating", 0)
        reviews = b.get("review_count", 0)
        niche = b.get("niche", b.get("raw_category", "")).replace("_", " ").title()
        comp_rows += (
            f"<tr>"
            f"<td>{b.get('name', '—')}</td>"
            f"<td>{niche}</td>"
            f'<td style="color:#e94560">{"★" * int(rating)}{"☆" * (5 - int(rating))} {rating:.1f}</td>'
            f"<td>{reviews:,}</td>"
            f"</tr>"
        )

    # ── risks as list ─────────────────────────────────────────────────────────
    risks = llm_analysis.get("critical_risks", "No specific risks identified.")
    if isinstance(risks, list):
        risk_items = "".join(f"<li>{r}</li>" for r in risks)
        risks_html = f"<ul class='risk-list'>{risk_items}</ul>"
    else:
        risks_html = f"<p class='prose'>{risks}</p>"

    entry_strategy = llm_analysis.get("entry_strategy", "Focus on quality and local delivery radius.")
    market_summary = llm_analysis.get(
        "market_summary",
        f"{city}, {zip_code} shows strong opportunity signals with undersupplied niches "
        f"and growing demand from its population of {demographics.get('population', 0):,}.",
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NeighborIQ Report — {city}, {state} {zip_code}</title>
  {_CSS}
</head>
<body>
<div class="wrapper">

  <div class="header">
    <h1>NeighborIQ Intelligence Report</h1>
    <div class="subtitle">{city}, {state} &nbsp;·&nbsp; ZIP {zip_code} &nbsp;·&nbsp; {today}</div>
    <span class="badge">NEIGHBORHOOD OPPORTUNITY ANALYSIS</span>
  </div>

  <div class="card">
    <h2>Executive Summary</h2>
    <p class="prose">{market_summary}</p>
  </div>

  <div class="card">
    <h2>Demographic Overview</h2>
    <table>
      <thead><tr><th>Metric</th><th>Value</th></tr></thead>
      <tbody>
        <tr><td>Population</td><td>{demographics.get("population", 0):,}</td></tr>
        <tr><td>Median Household Income</td><td>{_format_currency(demographics.get("median_income", 0))}</td></tr>
        <tr><td>Median Age</td><td>{demographics.get("age_median", 0):.1f} years</td></tr>
        <tr><td>Total Households</td><td>{demographics.get("households", 0):,}</td></tr>
        <tr><td>5-Year Growth Rate</td><td>{demographics.get("growth_rate_5yr", 0):.1f}%</td></tr>
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Top Business Opportunities</h2>
    {opp_cards_html if opp_cards_html else '<p class="prose">No Tier A/B opportunities detected. Try expanding radius.</p>'}
  </div>

  <div class="card">
    <h2>Competitor Landscape — Worst Rated First</h2>
    <table>
      <thead>
        <tr><th>Business</th><th>Category</th><th>Rating</th><th>Reviews</th></tr>
      </thead>
      <tbody>
        {comp_rows if comp_rows else '<tr><td colspan="4">No competitor data available</td></tr>'}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Entry Strategy</h2>
    <p class="prose">{entry_strategy}</p>
  </div>

  <div class="card">
    <h2>Critical Risks</h2>
    {risks_html}
  </div>

  <div class="footer">
    Generated by <a href="https://github.com/sijoy/neighboriq">NeighborIQ</a>
    &nbsp;·&nbsp; Data sourced from Google Maps, Yelp, US Census, Google Trends
    &nbsp;·&nbsp; For informational purposes only
  </div>

</div>
</body>
</html>"""

    return html


def save_html_report(zip_code: str, html: str) -> Path:
    """Saves to data/reports/{zip_code}_{date}.html. Returns path."""
    filename = f"{zip_code}_{date.today().isoformat()}.html"
    path = REPORTS_DIR / filename
    path.write_text(html, encoding="utf-8")
    log.info("Saved HTML report → %s", path)
    return path


def save_pdf_report(zip_code: str, html: str) -> Path | None:
    """
    Tries to convert HTML to PDF using weasyprint.
    If weasyprint not installed, saves HTML only and returns None.
    """
    try:
        from weasyprint import HTML as WeasyHTML  # type: ignore

        filename = f"{zip_code}_{date.today().isoformat()}.pdf"
        path = REPORTS_DIR / filename
        WeasyHTML(string=html).write_pdf(str(path))
        log.info("Saved PDF report → %s", path)
        return path
    except ImportError:
        log.info("weasyprint not installed — skipping PDF generation")
        return None
    except Exception as exc:
        log.warning("PDF generation failed: %s", exc)
        return None
