# Claude for Opera

A browser extension for using Claude from Opera's sidebar or toolbar, with an Etsy data extractor.

## Two ways to run it

| | **Claude Pro plan ($20/month)** | **API key** |
|---|---|---|
| Setup | Nothing. Leave the API key empty. | Paste a key from console.anthropic.com |
| How answers arrive | Your question (plus page or Etsy data) is copied, and Claude.ai opens. Press **Ctrl+V** and send. | Answers stream right inside the extension |
| Cost | Included in your Pro plan | Pay per use, billed separately from Pro |

Anthropic doesn't let other apps or extensions use a Claude.ai subscription directly. The Pro option works by handing your prompt to Claude.ai in your browser, where you're already signed in.

## Etsy tab
1. Open any Etsy page: search results, a category, a shop, or a single listing.
2. Open the extension, switch to **Etsy**, and click **Extract Etsy data**.
   - **This tab** reads the page you're on. **All open Etsy tabs** reads every Etsy tab at once.
   - To collect more, go to the next results page and extract again. Duplicates are skipped.
3. You get a table of listings with title, price, sale price, rating, review count, shop, ad, free shipping, bestseller, Star Seller, link and image. A listing page also gives the full product details and reviews.
4. **Download CSV** (opens in Excel or Google Sheets) or **Copy JSON**.
5. Type any question about the data, then click **Ask on Claude.ai (Pro)** or **Ask here (API key)**.

It reads only pages you open yourself. It doesn't crawl Etsy in the background, which would break Etsy's terms of use and get blocked by Etsy's bot protection. For large-scale data, use Etsy's official Open API.

## Chat tab
- Chat with Claude, with Markdown rendering and copy buttons
- **Summarize / Key points / Explain** buttons for the current page, and an "Include current page" toggle
- Right-click selected text → **Ask Claude about "…"**; right-click a page → **Summarize this page**
- Model and effort choice (these apply to API-key mode only; on Claude.ai you pick the model there)

## Install in Opera
1. Unzip `opera-claude-extension.zip` (or use this folder).
2. Open `opera://extensions` and turn on **Developer mode**.
3. Click **Load unpacked** and select the folder.
4. Settings open automatically. For the Pro plan, just close them. For an API key, paste it and click **Test key**.
5. For the sidebar: right-click Opera's sidebar → **Sidebar setup** → enable **Claude**. Or click the toolbar icon (**Alt+Shift+C**).
6. Make sure you're signed in at claude.ai in Opera.

## Notes
- An API key stays in this browser profile and is sent only to api.anthropic.com.
- Etsy changes its page layout from time to time. If extraction finds no listings, Claude still gets the page text, so questions keep working.
- Pages like `opera://…` and the add-ons store can't be read by extensions.
