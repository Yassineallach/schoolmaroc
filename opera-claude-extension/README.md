# Claude for Opera

A browser extension that lets you chat with Claude from Opera's sidebar or toolbar.

## Features
- Chat with streamed replies, rendered as Markdown with copy buttons
- Opera sidebar panel, plus a toolbar popup (shortcut: **Alt+Shift+C**)
- One-click **Summarize / Key points / Explain** for the current page
- "Include current page" toggle to ask questions about what you're reading
- Right-click a selection → **Ask Claude about "…"**; right-click a page → **Summarize this page**
- Choose a model (Opus 5.5, Sonnet 5.5, Haiku 5.5, Fable 5.2) and an effort level
- Conversation is saved between openings; **＋** starts a new chat
- Light and dark mode

## Install in Opera
1. Download or clone this folder (`opera-claude-extension`).
2. Open `opera://extensions`.
3. Turn on **Developer mode** (top right).
4. Click **Load unpacked** and select the `opera-claude-extension` folder.
5. The settings page opens: paste your Anthropic API key (from console.anthropic.com → API Keys), then click **Test key**.
6. To use the sidebar: right-click Opera's sidebar → **Sidebar setup**, then enable **Claude**. Or click the toolbar icon.

## Notes
- You need an Anthropic API key, and usage is billed to that account. This is separate from a claude.ai subscription.
- The key is stored in this browser profile only (`chrome.storage.local`) and sent only to `api.anthropic.com`.
- Pages like `opera://…` and the add-ons store can't be read by extensions.
- Long pages are cut to about 120,000 characters before they're sent.
- For Opus 5.5, Sonnet 5.5 and Fable 5.2, the extension turns on Anthropic's server-side refusal fallback. If a safety check declines a request, the API retries it on a fallback model. Remove `fallbacks` in `api.js` to turn this off.
