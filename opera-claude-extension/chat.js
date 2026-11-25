import { getSettings, streamMessage, MODELS } from "./api.js";
import { renderMarkdown } from "./markdown.js";

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
  if (!settings.apiKey) {
    $("noKey").hidden = false;
    updateEmpty(true);
    return;
  }

  // The page text is attached to the API message but only the short prompt is shown.
  const apiContent = page
    ? `<page title="${attr(page.title)}" url="${attr(page.url)}">\n${page.text}\n</page>\n\n${text}`
    : text;
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
