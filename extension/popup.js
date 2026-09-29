// popup.js — NeighborIQ Chrome Extension popup logic
"use strict";

const API_BASE = "http://localhost:8000";

const zipInput = document.getElementById("zipInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const dashboardBtn = document.getElementById("dashboardBtn");
const metaRow = document.getElementById("metaRow");
const contentEl = document.getElementById("content");

// ── helpers ────────────────────────────────────────────────────────────────

function showSpinner(msg = "Analyzing neighborhood...") {
  contentEl.innerHTML = `<div class="spinner">${msg}</div>`;
  metaRow.style.display = "none";
}

function showError(msg) {
  contentEl.innerHTML = `
    <div class="error">
      ${msg}
      <code>Start API: uvicorn neighboriq.api.server:app --port 8000</code>
    </div>`;
}

function showEmpty() {
  contentEl.innerHTML = `<div class="empty">No opportunities found for this ZIP.</div>`;
}

function tierClass(tier) {
  if (tier === "A") return "tier-A";
  if (tier === "B") return "tier-B";
  return "tier-C";
}

function fmtCapital(n) {
  if (!n) return "—";
  if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
  return `$${n}`;
}

function fmtGap(satRatio) {
  if (!satRatio) return "—";
  const gap = (1 / Math.max(satRatio, 0.01)).toFixed(1);
  return `${gap}x gap`;
}

function renderOpportunities(opportunities, meta) {
  if (!opportunities || opportunities.length === 0) {
    showEmpty();
    return;
  }

  if (meta) {
    const pop = meta.population ? `Pop ${meta.population.toLocaleString()}` : "";
    const city = meta.city || "";
    metaRow.textContent = [city, pop].filter(Boolean).join(" · ");
    metaRow.style.display = "block";
  }

  const top5 = opportunities.slice(0, 5);
  const cards = top5.map((opp) => {
    const score = opp.opportunity_score || 0;
    const niche = (opp.niche || "unknown").replace(/_/g, " ");
    const nicheTitle = niche.charAt(0).toUpperCase() + niche.slice(1);
    const tier = opp.tier || "C";
    const capital = fmtCapital(opp.typical_capital_req);
    const gap = fmtGap(opp.saturation_ratio);

    return `
      <div class="opp-card">
        <div class="opp-top">
          <span class="tier-badge ${tierClass(tier)}">${tier}</span>
          <span class="opp-name">${nicheTitle}</span>
          <span class="opp-score">${score}</span>
        </div>
        <div class="score-bar-wrap">
          <div class="score-bar" style="width:${score}%"></div>
        </div>
        <div class="opp-meta">
          <span>💰 ${capital} entry</span>
          <span>📊 ${gap}</span>
        </div>
      </div>`;
  });

  contentEl.innerHTML = `<div class="opp-list">${cards.join("")}</div>`;
}

// ── API calls ──────────────────────────────────────────────────────────────

async function fetchOpportunities(zip) {
  // Try cached endpoint first
  const cached = await fetch(`${API_BASE}/opportunities/${zip}`).catch(() => null);
  if (cached && cached.ok) {
    const data = await cached.json();
    if (Array.isArray(data) && data.length > 0) return { opportunities: data, meta: null };
  }

  // Run full analysis (no LLM for speed)
  const resp = await fetch(`${API_BASE}/analyze/${zip}?run_llm=false`);
  if (!resp.ok) throw new Error(`API returned ${resp.status}`);
  const data = await resp.json();
  return {
    opportunities: data.opportunities || [],
    meta: data.demographics || null,
  };
}

async function analyze() {
  const zip = (zipInput.value || "").trim().replace(/\D/g, "").slice(0, 5);
  if (!zip || zip.length !== 5) {
    showError("Please enter a valid 5-digit ZIP code.");
    return;
  }

  chrome.storage.local.set({ lastZip: zip });
  showSpinner(`Analyzing ${zip}...`);
  analyzeBtn.disabled = true;

  try {
    const { opportunities, meta } = await fetchOpportunities(zip);
    renderOpportunities(opportunities, meta);
  } catch (err) {
    showError(`Could not reach NeighborIQ API: ${err.message}`);
  } finally {
    analyzeBtn.disabled = false;
  }
}

// ── init ───────────────────────────────────────────────────────────────────

analyzeBtn.addEventListener("click", analyze);
zipInput.addEventListener("keydown", (e) => { if (e.key === "Enter") analyze(); });
dashboardBtn.addEventListener("click", () => {
  chrome.tabs.create({ url: API_BASE });
});

// On popup open: restore last zip or use Maps-detected zip
chrome.storage.local.get(["detectedZip", "lastZip"], ({ detectedZip, lastZip }) => {
  const zip = detectedZip || lastZip || "";
  if (zip) {
    zipInput.value = zip;
    analyze();
  }
});
