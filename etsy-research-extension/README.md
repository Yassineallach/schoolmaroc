# Shoplens Research: Etsy research workspace for Opera (and Chrome)

A browser extension for Etsy sellers that covers product research, sales and revenue estimates, keyword research, SEO checks, competitor monitoring, trends and exports.

- **No AI.** Everything is statistics, rules and your own history.
- **No APIs or servers.** The extension makes no network requests of its own.
- **Local only.** Data stays in your browser's storage. No account and no subscription.
- **Honest numbers.** Every figure is labelled **Verified** (Etsy shows it), **Observed** (the difference between your own visits) or **≈ Estimated** (a documented model with a range and a confidence grade).

> The term "Etsy" is a trademark of Etsy, Inc. Shoplens Research is not endorsed by, certified by or affiliated with Etsy, Inc.

---

## 1. Installation

### Opera (prebuilt)
1. Download `release/shoplens-research-opera-0.1.0.zip` and unzip it to a folder you will keep.
2. Open `opera://extensions`.
3. Turn on **Developer mode** (top right).
4. Click **Load unpacked** and select the unzipped folder (the one that contains `manifest.json`).
5. The welcome page opens. Tick **Read the Etsy pages I open** and click **Continue**.
6. Optional: pin the toolbar button. To use the sidebar panel, open Opera's sidebar settings (the ⋯ / gear at the bottom of the sidebar) and enable **Shoplens Research** under extensions.

### Chrome / Edge / Brave
Use `release/shoplens-research-chrome-0.1.0.zip` and follow the same steps at `chrome://extensions`. The Chrome build also registers a side panel.

### Build from source
```bash
cd etsy-research-extension
npm install
npm run build        # outputs dist/opera, dist/chrome and the two zip files in dist/
npm test             # 53 unit tests
npm run test:e2e     # end-to-end test (needs Playwright + Chromium), run after a build
```

---

## 2. How data is collected

| Source | Used for | How |
|---|---|---|
| Etsy **search / market / category** pages you open | Keyword indicators, price distribution, title phrases, ads and badge shares, product discovery | Reads the result cards already on screen |
| Etsy **listing** pages you open | Price, currency, reviews, rating, favourites, "in baskets", shop sales counter, "Listed on", category, variations, images, description, related search terms, shipping origin | JSON-LD structured data first, then page text |
| Etsy **shop** pages you open | Sales counter, reviews, rating, "On Etsy since", admirers, listing count, sections, visible listings | Page text and listing cards |
| Etsy **autocomplete** dropdown | "Seen in autocomplete" demand signal and suggestions | Reads the suggestions Etsy already shows while you type |
| Your **own history** | Trends, velocity, change logs | Snapshots of each visit, kept in IndexedDB |

Page reading is **off until you turn it on**. It is passive: it never loads Etsy pages in the background, never crawls, scrolls, clicks or paginates, and never handles CAPTCHAs or logins. It reads no buyer or private data; review text and reviewer names are not collected. Turning it off in Settings removes the panel from Etsy straight away.

**Legal note.** Etsy's developer terms forbid screen-scraping by API applications, and Etsy's terms of use restrict automated data collection. Shoplens does not use the API and does no automated collection, but reading pages you view is a grey area. Popular Etsy research extensions work the same way. You decide whether to enable it; see `docs/01-research-and-architecture.md` §6.

---

## 3. Features

### Product research
- **Products table** of every listing you have seen. Filters: keyword, shop, category, physical/digital, price range, minimum estimated sales/month, minimum estimated revenue/month, minimum reviews, minimum rating, maximum days since listed, competition level (difficulty of the search where you found the product), and full-data only. Every column is sortable: estimated sales, revenue, popularity (favourites), reviews, recency, price and velocity.
- **Product detail**: verified fields; a **sales and revenue table** (day, week, month, year, lifetime) with 90% ranges; editable price and discount assumptions; currency conversion with your own rates; method steps; confidence grade with its reasons; performance indicators; charts of price, reviews and favourites over time; change log; variations; related search terms; and an SEO summary.
- **Performance indicators**: reviews-per-sale (shop), favourites per review, days since "Listed on", first seen, velocity, price percentile within its search, baskets and badges. **Favourites-to-views** and **conversion rate** are shown as *Not available* with the reason, because Etsy hides views.

### Sales estimation method
1. `k = shop sales ÷ shop reviews`, the shop's own sales per review, both verified. If the shop has fewer reviews than the threshold, the median `k` of other recorded shops is used, then your default.
2. Lifetime sales ≈ listing reviews × k, with a 90% Poisson range on the review count.
3. Velocity, using the best method available:
   1. **review-delta**: new listing reviews between your visits × k
   2. **shop-delta**: shop sales counter growth × the listing's share of shop reviews
   3. **shop-lifetime**: shop sales ÷ shop age × review share
   4. **listed-on**: lifetime ÷ days since "Listed on". This is an upper bound and caps the grade at C.
4. Confidence grade A–D, based on review sample size, calibration source and velocity method.

Revenue is always labelled **estimated gross revenue** (sales × price × (1 − discount)). It does not deduct fees, costs or taxes.

### Keyword research
- Etsy does **not** publish search volume, and Shoplens never invents it. Indicators per keyword: result count (verified), share of "Bestseller" and "Popular now" badges, ad share, median and IQR price, distinct shops, shop concentration (Herfindahl index), median card review count, and presence in autocomplete.
- **Difficulty** = 100 × (0.45 supply + 0.35 established competitors + 0.10 ads + 0.10 shop dominance). Each part is shown.
- **Opportunity** = 100 × data quality × Σ(weight × component) ÷ Σ weights, with components demand, low competition, trend and specificity. **Weights are sliders.**
- **Related phrases**: document-frequency n-grams from the result titles you opened, plus autocomplete. Grouped as broad, long-tail, buyer-intent, seasonal or autocomplete.
- **Comparison** of 2–6 keywords side by side, **folders**, notes, saved lists, a history chart (7 d to 24 m; periods without data are disabled), a price histogram, and a Google Trends link-out that you open yourself.

### Competitor research
- Shop list with verified counters and **observed sales/day** between visits.
- **Track** shops. Each visit to a shop page is compared with the previous one: new listings, listings no longer visible, price changes, title changes, and changes in sales, reviews and listing count.
- Shop detail: KPIs, sales-counter and review charts, price distribution, categories and sections, change log, recorded products.
- **Shop comparison** (2–6): sales, observed velocity, reviews, rating, age, listings, sales per review, sales per listing, prices, diversity, new listings in the last 30 days, top terms.
- **Keyword overlap matrix** (Jaccard) across tracked shops, and **term gaps**: terms competitors use that your shop doesn't.

### SEO toolkit (deterministic rules)
- **Listing audit** with rule IDs (T1–T6, G1–G5, K1, D1–D6, I1–I2, L1), severities and explanations, plus a score.
- **Title analyser**: live character counter (140), words, repeated words, ALL CAPS, special characters, phrases, the first 40 characters, and keyword positions.
- **Tag analyser**: 13 inputs with a 20-character check, duplicates, words repeated across tags, overlap with the title, keyword coverage, saved keywords as targets, a **competitor term comparison** (click to fill a slot), saved tag sets, and copy.
- **Description analyser**: length, paragraphs, bullets, Flesch readability, opening 160 characters, keyword placement, repeated phrases, and a product-information checklist.
- **Listing comparison** of 2–4 listings side by side.

### Trends and calendar
- Rising and declining keywords **in your own data**, a keyword history chart, recently emerging products (reviews per day since "Listed on"), products with popularity badges, and categories in your research.
- A **shopping calendar** computed for US, UK, EU, CA or AU: Valentine's Day, Easter (Gregorian computus), Mother's and Father's Day by region, Back to School, Halloween, Thanksgiving, Black Friday, Cyber Monday and Christmas. Each has a "list by" lead time and links to your matching saved keywords.

### Organisation and data
- Collections of products, tag sets and keyword folders, plus research history and a change log.
- **CSV and Excel (.xlsx)** exports for products, keywords, shops, collections, history and changes, and a printable report for any page.
- **JSON backup and restore** (merge or replace), and delete-all.
- Global search, light, dark and system themes, display currency with manual exchange rates, and adjustable estimate assumptions.
- **Page diagnostics** shows which fields were found on each open Etsy tab, which helps when Etsy changes its layout.

### Inside Etsy
- A small **SL** button opens a panel. It sits in an isolated shadow root, so it never touches Etsy's styles or layout. It summarises the current search, listing or shop page.
- Search cards of listings you already analysed show a small "≈ N sales/mo (est.)" chip.
- The toolbar popup and the Opera sidebar or Chrome side panel show the same summary.

---

## 4. Architecture

```
src/
  background/sw.ts            message router; stores extractions; no network access
  content/
    main.ts                   page detection, panel (closed shadow DOM), badges, autocomplete capture
    extractors/               pure DOM readers: common.ts, cards.ts, pages.ts (search/listing/shop)
  core/                       pure logic, no browser APIs (unit-tested)
    stats.ts text.ts          quantiles, HHI, Jaccard, Poisson CI, OLS slope, histogram; n-grams, Flesch
    sales.ts                  calibration, lifetime, velocity, periods, revenue, observed shop velocity
    keywords.ts               indicators, difficulty, opportunity, suggestions
    seo.ts                    title/tag/description analysis + rule audit
    competitors.ts            snapshot diffs, comparison, overlap, term gaps
    trends.ts                 series, periods, movements, holiday calendar
    export.ts                 CSV + dependency-free XLSX writer (stored ZIP + SpreadsheetML)
    storage/db.ts repo.ts     IndexedDB wrapper; ingestion, snapshots (merged within 1 h), backup
    summaries.ts              joins storage and engines for the UI
  ui/
    components.ts             tables (sortable), SVG line/histogram charts, badges, KPIs
    summary-view.ts           panel/sidebar renderer
    dashboard/                hash router + views (overview, products, keywords, competitors, seo, trends, saved, history, settings, diagnostics)
    popup/                    popup + sidebar
    styles/                   design tokens (light/dark), dashboard, popup
static/                       HTML pages, icons
build.mjs                     esbuild bundles + per-target manifest (Opera: sidebar_action; Chrome: side_panel) + zip
```

**Data model (IndexedDB `shoplens`)**: `listings`, `listingSnapshots`, `shops`, `shopSnapshots`, `keywords`, `keywordSnapshots`, `changes`, `collections`, `history` and `meta`. Settings live in `chrome.storage.local`. Snapshots taken within one hour of each other are merged, so reloading a page doesn't create fake history.

**Permissions**: `storage`, `unlimitedStorage`, host access to `etsy.com` only, and `sidePanel` in the Chrome build. There is no `tabs`, `cookies`, `webRequest`, `<all_urls>` or remote code.

**Dependencies**: none at runtime. Development uses TypeScript, esbuild, Vitest, jsdom and fake-indexeddb, all MIT or Apache-2.0.

---

## 5. Testing report

| Suite | Result |
|---|---|
| Type check (`tsc --noEmit`, strict) | passes |
| Unit tests (Vitest): extractors, number/price/date parsing, stats, text, sales, keywords, SEO, competitors, trends/calendar, currency, CSV/XLSX (XLSX re-read with openpyxl), IndexedDB ingestion, snapshot merge, diffs, backup/restore | **53/53 pass** |
| End-to-end (Playwright, Chromium with the built extension, synthetic Etsy fixtures served at `www.etsy.com` URLs): onboarding; panel on search, listing and shop pages; estimate chips; all 17 dashboard routes; estimate labelling; diagnostics; CSV and Excel downloads; filtering; sorting; backup; popup; sidebar; no horizontal overflow at 375 px and 768 px on 8 views; dark theme; panel removed when reading is turned off; **zero console errors** | **66/66 checks pass, for both the Opera and Chrome builds** |

Screenshots from the end-to-end run are written to `test-results/<target>/`.

**Not tested here:**
- **Real Opera.** Opera is not available in this environment. The Opera build was loaded in Chromium, which Opera is based on. `sidebar_action` is Opera-specific and is ignored by Chromium.
- **Live Etsy pages.** Etsy blocks automated access from the build environment (HTTP 403). The page readers were built from Etsy's known page structure with several fallbacks, and tested on synthetic pages modelled on that structure. **Use Page diagnostics on real pages after installing**; it shows which fields are found.

---

## 6. Known limitations

- **Page layout changes.** Etsy can change its HTML at any time. Structured data (JSON-LD) is used where possible, and text patterns are English-first. Other Etsy languages may miss some text-based fields (sales, favourites, "Listed on"); Page diagnostics shows exactly which ones.
- **No search volume.** Etsy doesn't publish it. Demand is shown through indicators instead.
- **Card review counts** on search results usually belong to the **shop**, not the listing. They are only used as a measure of competitor strength.
- **"Listed on"** is the latest renewal date, not the original creation date. Velocity based on it is an upper bound.
- **Tags.** Etsy no longer shows a listing's tags. The related search terms it links from the listing page are used instead and labelled as such. For your own listings, paste your exact tags into the SEO tools.
- **Trends and history** exist only from the day you start collecting, and only for the pages you visit. Nothing is backfilled, and nothing represents all of Etsy.
- **Monitoring** happens when you visit a page. There is no background checking, by design.
- **Shop diffs** compare the listings visible on the captured shop page (usually the first page). A "no longer visible" listing may only have moved to another page.
- **Exchange rates** are entered by you. Values without a rate stay in their original currency.
- **Views, conversion rates and costs** are never shown, because Etsy doesn't publish them for other sellers.
