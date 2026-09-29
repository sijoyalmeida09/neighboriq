// background.js — Service worker for NeighborIQ extension
// Receives zip codes detected by content.js and stores them in chrome.storage.local

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "ZIP_DETECTED" && message.zip) {
    chrome.storage.local.set({ detectedZip: message.zip }, () => {
      console.log("[NeighborIQ] Stored detected zip:", message.zip);
      sendResponse({ ok: true });
    });
    return true; // keep channel open for async sendResponse
  }
});
