// Context menu: send selected text or the current page to Claude.
// The chat page picks the request up from storage.session when it opens.

chrome.runtime.onInstalled.addListener((details) => {
  chrome.contextMenus.create({
    id: "ask-selection",
    title: "Ask Claude about \"%s\"",
    contexts: ["selection"],
  });
  chrome.contextMenus.create({
    id: "summarize-page",
    title: "Summarize this page with Claude",
    contexts: ["page"],
  });
  if (details.reason === "install") chrome.runtime.openOptionsPage();
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  let pending;
  if (info.menuItemId === "ask-selection") {
    pending = {
      kind: "selection",
      text: info.selectionText,
      url: tab?.url || "",
      title: tab?.title || "",
    };
  } else if (info.menuItemId === "summarize-page") {
    pending = { kind: "page", tabId: tab?.id };
  }
  if (!pending) return;

  await chrome.storage.session.set({ pending });
  // Opening the popup from a context-menu click is allowed in recent Chromium;
  // if it fails, the request waits until the user opens the popup or sidebar.
  try {
    await chrome.action.openPopup();
  } catch {
    chrome.action.setBadgeText({ text: "1" });
    chrome.action.setBadgeBackgroundColor({ color: "#d97757" });
  }
});
