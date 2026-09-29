// content.js — Runs on Google Maps pages
// Extracts zip code from URL params, page title, or visible text
// Sends detected zip to background service worker for storage

(function () {
  "use strict";

  const US_ZIP_RE = /\b(\d{5})(?:-\d{4})?\b/;

  function extractZipFromUrl(url) {
    try {
      const u = new URL(url);
      // Check query params: ?q=02122 or ?query=Boston+02122
      for (const [, val] of u.searchParams) {
        const m = val.match(US_ZIP_RE);
        if (m) return m[1];
      }
      // Check hash fragment
      const m = u.hash.match(US_ZIP_RE);
      if (m) return m[1];
    } catch (_) {}
    return null;
  }

  function extractZipFromTitle() {
    const title = document.title || "";
    const m = title.match(US_ZIP_RE);
    return m ? m[1] : null;
  }

  function extractZipFromPage() {
    // Look in address chips, sidebar text
    const candidates = [
      document.querySelector('[data-item-id="address"]'),
      document.querySelector('.rogA2c'),
      document.querySelector('[aria-label*="zip"]'),
    ].filter(Boolean);

    for (const el of candidates) {
      const m = (el.textContent || "").match(US_ZIP_RE);
      if (m) return m[1];
    }
    // Broader scan — last resort
    const bodySnippet = document.body.innerText.slice(0, 5000);
    const m = bodySnippet.match(US_ZIP_RE);
    return m ? m[1] : null;
  }

  function detectZip() {
    return (
      extractZipFromUrl(window.location.href) ||
      extractZipFromTitle() ||
      extractZipFromPage()
    );
  }

  function sendZip(zip) {
    chrome.runtime.sendMessage({ type: "ZIP_DETECTED", zip }, (resp) => {
      if (chrome.runtime.lastError) return; // extension reloaded
    });
  }

  // Initial detection
  const zip = detectZip();
  if (zip) sendZip(zip);

  // Watch for navigation within Maps SPA
  let lastUrl = location.href;
  new MutationObserver(() => {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      const newZip = detectZip();
      if (newZip) sendZip(newZip);
    }
  }).observe(document.body, { subtree: true, childList: true });
})();
