import { getSettings, streamMessage, MODELS } from "./api.js";
import { renderMarkdown } from "./markdown.js";
import { extractEtsyPage, toCSV, toPromptText, LISTING_COLUMNS } from "./etsy.js";

const $ = (id) => document.getElementById(id);
const messagesEl = $("messages");
const emptyEl = $("empty");
const input = $("input");
const sendBtn = $("send");
const stopBtn = $("stop");
const modelSel = $("model");

const MAX_PAGE_CHARS = 120000;
let history = []; // [{role, content}] — content is a string
let controller = null;
let settings;

if (new URLSearchParams(location.search).has("sidebar")) {
  document.body.classList.add("sidebar");
}

// ---------- init ----------
(async function init() {
  settings = await getSettings();
  for (const m of MODELS) {
    const opt = new Option(m.label, m.id);
    modelSel.add(opt);
  }
  modelSel.value = settings.model;
  $("noKey").hidden = !!settings.apiKey;

  const saved = await chrome.storage.local.get("history");
  history = saved.history || [];
  history.forEach((m) => addBubble(m.role, m.display || m.content));
  updateEmpty();

  chrome.action.setBadgeText({ text: "" });
  const { pending } = await chrome.storage.session.get("pending");
  if (pending) {
    await chrome.storage.session.remove("pending");
    handlePending(pending);
  }
  input.focus();
})();

chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && changes.settings) {
    getSettings().then((s) => {
      settings = s;
      modelSel.value = s.model;
      $("noKey").hidden = !!s.apiKey;
    });
  }
  if (area === "session" && changes.pending?.newValue) {
    chrome.storage.session.remove("pending");
    handlePending(changes.pending.newValue);
  }
});

// ---------- UI events ----------
modelSel.addEventListener("change", async () => {
  settings.model = modelSel.value;
  const stored = await chrome.storage.local.get("settings");
  await chrome.storage.local.set({ settings: { ...(stored.settings || {}), model: modelSel.value } });
});

$("openSettings").addEventListener("click", () => chrome.runtime.openOptionsPage());
$("settingsLink").addEventListener("click", (e) => {
  e.preventDefault();
  chrome.runtime.openOptionsPage();
});

$("newChat").addEventListener("click", async () => {
  controller?.abort();
  history = [];
  await chrome.storage.local.remove("history");
  messagesEl.querySelectorAll(".msg").forEach((n) => n.remove());
  updateEmpty();
  input.focus();
});

input.addEventListener("input", autoGrow);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    $("composer").requestSubmit();
  }
});

$("composer").addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text || controller) return;
  input.value = "";
  autoGrow();
  let pageContext = null;
  if ($("includePage").checked) pageContext = await getPageText();
  send(text, pageContext);
});

stopBtn.addEventListener("click", () => controller?.abort());

document.querySelectorAll(".chip").forEach((chip) =>
  chip.addEventListener("click", async () => {
    const prompts = {
      summarize: "Summarize this page.",
      keypoints: "List the key points of this page as bullets.",
      explain: "Explain what this page is about in simple terms.",
    };
    const page = await getPageText();
    if (page) send(prompts[chip.dataset.action], page);
  })
);

messagesEl.addEventListener("click", (e) => {
  const btn = e.target.closest(".copy-code, .copy-msg");
  if (!btn) return;
  const text = btn.classList.contains("copy-code")
    ? btn.parentElement.querySelector("code").textContent
    : btn.closest(".msg").dataset.raw;
  navigator.clipboard.writeText(text);
  const old = btn.textContent;
  btn.textContent = "Copied";
  setTimeout(() => (btn.textContent = old), 1200);
});

// ---------- core ----------
async function handlePending(p) {
  if (p.kind === "selection") {
    send(`Explain or answer this:\n\n"${p.text}"`, null, `From: ${p.title}`);
  } else if (p.kind === "page") {
    const page = await getPageText(p.tabId);
    if (page) send("Summarize this page.", page);
  }
}

async function send(text, page, note) {
  // The page text is attached to the API message but only the short prompt is shown.
  const apiContent = page
    ? `<page title="${attr(page.title)}" url="${attr(page.url)}">\n${page.text}\n</page>\n\n${text}`
    : text;

  // No API key: hand the prompt to Claude.ai so it runs on the user's Pro plan.
  if (!settings.apiKey) {
    await askOnClaudeAi(apiContent);
    return;
  }
  const shown = page ? `${text}\n\n📄 ${page.title}` : note ? `${text}\n\n${note}` : text;

  history.push({ role: "user", content: apiContent, display: shown });
  addBubble("user", shown);
  updateEmpty();

  const bubble = addBubble("assistant", "");
  bubble.classList.add("streaming");
  const body = bubble.querySelector(".body");
  let acc = "";

  controller = new AbortController();
  setBusy(true);
  try {
    const { stopReason } = await streamMessage({
      settings,
      messages: history.map(({ role, content }) => ({ role, content })),
      signal: controller.signal,
      onText: (d) => {
        acc += d;
        body.innerHTML = renderMarkdown(acc);
        scrollDown();
      },
    });
    if (stopReason === "refusal") {
      acc += "\n\n*Claude declined to answer this request.*";
    } else if (stopReason === "max_tokens") {
      acc += "\n\n*Response was cut off (max length reached).*";
    }
  } catch (err) {
    if (err.name === "AbortError") {
      acc += acc ? "\n\n*Stopped.*" : "*Stopped.*";
    } else {
      bubble.classList.add("error");
      acc = `**Error:** ${err.message}`;
      history.pop(); // drop the failed user turn so the conversation stays valid
      body.innerHTML = renderMarkdown(acc);
      finish(bubble);
      return;
    }
  }

  body.innerHTML = renderMarkdown(acc || "*(no response)*");
  bubble.dataset.raw = acc;
  if (acc.trim()) {
    history.push({ role: "assistant", content: acc });
  } else {
    history.pop();
  }
  await chrome.storage.local.set({ history });
  finish(bubble);
}

function finish(bubble) {
  bubble.classList.remove("streaming");
  controller = null;
  setBusy(false);
  input.focus();
}

async function getPageText(tabId) {
  try {
    if (!tabId) {
      const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
      tabId = tab?.id;
    }
    const [res] = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => ({
        title: document.title,
        url: location.href,
        text: (document.body?.innerText || "").replace(/\n{3,}/g, "\n\n"),
      }),
    });
    const page = res.result;
    if (page.text.length > MAX_PAGE_CHARS) {
      page.text = page.text.slice(0, MAX_PAGE_CHARS) + "\n[…page truncated…]";
    }
    return page;
  } catch (e) {
    showSystem("Can't read this page (browser pages like opera:// and the extension store are blocked).");
    return null;
  }
}

// ---------- rendering helpers ----------
const attr = (v) => String(v).replace(/"/g, "&quot;");

function addBubble(role, text) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.dataset.raw = text;
  div.innerHTML = `<div class="body"></div>${
    role === "assistant" ? '<button class="copy-msg" type="button">Copy</button>' : ""
  }`;
  div.querySelector(".body").innerHTML =
    role === "user" ? renderMarkdown(text).replace(/<\/?h\d>/g, "") : renderMarkdown(text);
  messagesEl.appendChild(div);
  scrollDown();
  return div;
}

function showSystem(text) {
  const div = document.createElement("div");
  div.className = "msg system";
  div.textContent = text;
  messagesEl.appendChild(div);
  scrollDown();
}

function updateEmpty(force) {
  emptyEl.hidden = !force && history.length > 0;
}

function setBusy(b) {
  sendBtn.hidden = b;
  stopBtn.hidden = !b;
}

function scrollDown() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function autoGrow() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 160) + "px";
}

// ---------- Claude.ai handoff (Pro plan, no API key) ----------
async function askOnClaudeAi(prompt) {
  try {
    await navigator.clipboard.writeText(prompt);
  } catch {
    // Fallback for contexts where the async clipboard API is blocked.
    const ta = document.createElement("textarea");
    ta.value = prompt;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
  }
  await chrome.tabs.create({ url: "https://claude.ai/new" });
}

// ---------- view switching ----------
document.querySelectorAll(".tab").forEach((tab) =>
  tab.addEventListener("click", () => showView(tab.dataset.view))
);
function showView(id) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.view === id));
  document.querySelectorAll(".view").forEach((v) => (v.hidden = v.id !== id));
  modelSel.hidden = $("newChat").hidden = id !== "chatView";
  chrome.storage.local.set({ lastView: id });
}
chrome.storage.local.get("lastView").then(({ lastView }) => lastView && showView(lastView));

// ---------- Etsy ----------
let etsyPages = []; // results of extractEtsyPage(), newest last

chrome.storage.local.get("etsyPages").then(({ etsyPages: saved }) => {
  if (saved?.length) {
    etsyPages = saved;
    renderEtsy();
  }
});

function allListings() {
  const seen = new Set();
  const out = [];
  for (const p of etsyPages) {
    for (const l of p.listings) {
      if (seen.has(l.id)) continue;
      seen.add(l.id);
      out.push(l);
    }
  }
  return out;
}

function etsyStatus(msg, bad) {
  const el = $("etsyStatus");
  el.textContent = msg;
  el.className = bad ? "bad" : "";
}

$("extract").addEventListener("click", async () => {
  const scope = document.querySelector('input[name="scope"]:checked').value;
  let tabs;
  if (scope === "all") {
    tabs = await chrome.tabs.query({ url: ["https://*.etsy.com/*"] });
  } else {
    const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
    tabs = tab ? [tab] : [];
    if (tab && !/^https:\/\/([a-z0-9-]+\.)?etsy\.com\//i.test(tab.url || "")) {
      return etsyStatus("This tab isn't an Etsy page. Open etsy.com first.", true);
    }
  }
  if (!tabs.length) return etsyStatus("No open Etsy tabs found.", true);

  etsyStatus(`Reading ${tabs.length} tab${tabs.length > 1 ? "s" : ""}…`);
  const before = allListings().length;
  let ok = 0;
  for (const tab of tabs) {
    try {
      const [res] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, func: extractEtsyPage });
      const page = res.result;
      // Replace an earlier extraction of the same URL instead of duplicating it.
      etsyPages = etsyPages.filter((p) => p.url !== page.url);
      etsyPages.push(page);
      ok++;
    } catch (e) {
      console.warn("Etsy extraction failed", tab.url, e);
    }
  }
  if (!ok) return etsyStatus("Couldn't read the page. Reload the Etsy tab and try again.", true);

  // Keep storage small: page text is only kept for the last few pages.
  etsyPages = etsyPages.slice(-30).map((p, i, arr) => (i < arr.length - 5 ? { ...p, pageText: "" } : p));
  await chrome.storage.local.set({ etsyPages });
  const added = allListings().length - before;
  etsyStatus(`Read ${ok} page${ok > 1 ? "s" : ""}. ${added} new listing${added === 1 ? "" : "s"} added.`);
  renderEtsy();
});

$("clearData").addEventListener("click", async () => {
  etsyPages = [];
  await chrome.storage.local.remove("etsyPages");
  $("etsyResults").hidden = true;
  etsyStatus("Cleared.");
});

function renderEtsy() {
  const listings = allListings();
  const products = etsyPages.filter((p) => p.product);
  const reviews = etsyPages.reduce((n, p) => n + p.reviews.length, 0);
  const shops = etsyPages.filter((p) => p.shop);
  $("etsyResults").hidden = false;

  const parts = [`<strong>${etsyPages.length}</strong> page${etsyPages.length === 1 ? "" : "s"}`];
  parts.push(`<strong>${listings.length}</strong> listings`);
  if (products.length) parts.push(`<strong>${products.length}</strong> product page${products.length === 1 ? "" : "s"}`);
  if (reviews) parts.push(`<strong>${reviews}</strong> reviews`);
  if (shops.length) parts.push(`<strong>${shops.length}</strong> shop${shops.length === 1 ? "" : "s"}`);
  $("etsySummary").innerHTML = parts.join(" · ");

  const table = $("etsyTable");
  table.replaceChildren();
  const rows = [
    ...products.map((p) => ({ ...p.product, _kind: "Product" })),
    ...listings,
  ];
  const head = table.createTHead().insertRow();
  for (const h of ["Title", "Price", "Rating", "Reviews", "Shop"]) {
    const th = document.createElement("th");
    th.textContent = h;
    head.appendChild(th);
  }
  const tbody = table.createTBody();
  for (const r of rows.slice(0, 200)) {
    const tr = tbody.insertRow();
    const tdTitle = tr.insertCell();
    const a = document.createElement("a");
    a.href = r.url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = r.title;
    tdTitle.appendChild(a);
    tr.insertCell().textContent = [r.currency, r.price].filter(Boolean).join(" ");
    tr.insertCell().textContent = r.rating;
    tr.insertCell().textContent = r.reviewCount;
    tr.insertCell().textContent = r.shop;
  }
  if (!rows.length) {
    const td = tbody.insertRow().insertCell();
    td.colSpan = 5;
    td.textContent = "No listings found on these pages; Claude will use the page text instead.";
  }
}

$("downloadCsv").addEventListener("click", () => {
  const products = etsyPages.filter((p) => p.product).map((p) => p.product);
  const rows = [...products, ...allListings()];
  const blob = new Blob([toCSV(rows, LISTING_COLUMNS)], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `etsy-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
});

$("copyJson").addEventListener("click", async (e) => {
  const data = etsyPages.map(({ pageText, ...p }) => p);
  await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
  e.target.textContent = "Copied";
  setTimeout(() => (e.target.textContent = "Copy JSON"), 1200);
});

function etsyPrompt() {
  const q = $("etsyQuestion").value.trim();
  if (!q) {
    $("etsyQuestion").focus();
    etsyStatus("Type a question first.", true);
    return null;
  }
  return { q, data: toPromptText(etsyPages) };
}

$("askClaudeAi").addEventListener("click", async () => {
  const p = etsyPrompt();
  if (!p) return;
  await askOnClaudeAi(
    `Here is data I extracted from Etsy pages I was browsing.\n\n<etsy_data>\n${p.data}\n</etsy_data>\n\n${p.q}`
  );
});

$("askApi").addEventListener("click", () => {
  const p = etsyPrompt();
  if (!p) return;
  if (!settings.apiKey) {
    etsyStatus("No API key set. Use \"Ask on Claude.ai (Pro)\" or add a key in Settings.", true);
    return;
  }
  showView("chatView");
  send(p.q, { title: `Etsy data (${allListings().length} listings)`, url: "etsy.com", text: p.data });
});
