import { getSettings, streamMessage, MODELS, DEFAULT_SETTINGS } from "./api.js";

const $ = (id) => document.getElementById(id);
const status = $("status");

for (const m of MODELS) $("model").add(new Option(m.label, m.id));

const s = await getSettings();
$("apiKey").value = s.apiKey;
$("model").value = s.model;
$("effort").value = s.effort;
$("system").value = s.system;

function read() {
  return {
    apiKey: $("apiKey").value.trim(),
    model: $("model").value,
    effort: $("effort").value,
    system: $("system").value.trim() || DEFAULT_SETTINGS.system,
  };
}

function show(msg, ok) {
  status.textContent = msg;
  status.className = ok ? "ok" : "bad";
}

$("save").addEventListener("click", async () => {
  await chrome.storage.local.set({ settings: read() });
  show("Saved.", true);
});

$("test").addEventListener("click", async () => {
  const settings = { ...read(), effort: "low" };
  if (!settings.apiKey) return show("Enter a key first.", false);
  show("Testing…", true);
  try {
    await streamMessage({
      settings,
      messages: [{ role: "user", content: "Reply with the single word: ok" }],
      onText: () => {},
    });
    await chrome.storage.local.set({ settings: read() });
    show("Key works — saved.", true);
  } catch (e) {
    show(e.message, false);
  }
});
