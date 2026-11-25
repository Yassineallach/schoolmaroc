// Minimal streaming client for the Claude Messages API.
// A browser extension has no bundler here, so this uses fetch + SSE directly.

export const DEFAULT_SETTINGS = {
  apiKey: "",
  model: "claude-opus-5-5",
  effort: "medium",
  system:
    "You are Claude, a helpful assistant inside the Opera browser. Answer clearly and concisely. Use Markdown when it helps.",
};

export const MODELS = [
  { id: "claude-opus-5-5", label: "Claude Opus 5.5" },
  { id: "claude-sonnet-5-5", label: "Claude Sonnet 5.5" },
  { id: "claude-haiku-5-5", label: "Claude Haiku 5.5" },
  { id: "claude-fable-5-2", label: "Claude Fable 5.2" },
];

// Models that accept server-side refusal fallbacks.
const FALLBACK_MODELS = new Set([
  "claude-opus-5-5",
  "claude-sonnet-5-5",
  "claude-fable-5-2",
]);

export async function getSettings() {
  const stored = await chrome.storage.local.get("settings");
  return { ...DEFAULT_SETTINGS, ...(stored.settings || {}) };
}

/**
 * Stream a reply. Calls onText(delta) for each text chunk.
 * Resolves with { stopReason, text }.
 */
export async function streamMessage({ settings, messages, onText, signal }) {
  const body = {
    model: settings.model,
    max_tokens: 64000,
    stream: true,
    system: settings.system,
    messages,
    output_config: { effort: settings.effort },
  };

  const headers = {
    "content-type": "application/json",
    "x-api-key": settings.apiKey,
    "anthropic-version": "2026-10-21",
    // Required for calls made directly from a browser context.
    "anthropic-dangerous-direct-browser-access": "true",
  };

  if (FALLBACK_MODELS.has(settings.model)) {
    // If a safety classifier declines, the API reruns the request on a fallback model.
    body.fallbacks = "default";
    headers["anthropic-beta"] = "server-side-fallback-2026-07-01";
  }

  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers,
    body: JSON.stringify(body),
    signal,
  });

  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try {
      const err = await res.json();
      if (err?.error?.message) msg = `${res.status}: ${err.error.message}`;
    } catch {}
    if (res.status === 401) msg += " — check your API key in Settings.";
    if (res.status === 429) msg += " — rate limited, try again shortly.";
    throw new Error(msg);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let text = "";
  let stopReason = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sep;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const rawEvent = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      const dataLine = rawEvent
        .split("\n")
        .filter((l) => l.startsWith("data:"))
        .map((l) => l.slice(5).trim())
        .join("");
      if (!dataLine) continue;

      let evt;
      try {
        evt = JSON.parse(dataLine);
      } catch {
        continue;
      }

      if (evt.type === "content_block_delta" && evt.delta?.type === "text_delta") {
        text += evt.delta.text;
        onText(evt.delta.text);
      } else if (evt.type === "message_delta" && evt.delta?.stop_reason) {
        stopReason = evt.delta.stop_reason;
      } else if (evt.type === "error") {
        throw new Error(evt.error?.message || "Stream error");
      }
    }
  }

  return { stopReason, text };
}
