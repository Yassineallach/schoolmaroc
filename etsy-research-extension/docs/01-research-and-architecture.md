# Etsy Research Workspace — Phase 1 Research Report & Proposed Architecture

Status: **draft for approval. No code has been written yet.**
Date: 2026-11-27

---

## 0. Summary

1. **Etsy does not publish search volume or per-listing sales.** Every tool that shows these numbers is estimating them. The tools say their sales estimates are about 80% accurate. No one has checked that claim independently, and reviewers say the estimates drift on low-volume listings. Several tools use the same estimate for keyword volume, and two tools disagree with each other on accuracy (82% vs 64% in one hands-on test).
2. **The only official public sales number is the shop's lifetime sales counter.** It appears on shop pages and in the API (`transaction_sold_count`). Reviews, favourites, listing dates, tags and prices are public too.
3. **The biggest gap we can fill honestly is *measured* change over time.** Snapshot a shop's public sales counter on day A and day B, and the difference is a real sales count for that shop over that period. It is not an estimate. Almost no tool separates this observed figure from modelled figures. Our extension will make that split the core of its design.
4. **Etsy's developer rules say "Screen-scraping is not allowed"** and require apps to use the API. So the legitimate main data path is the **official Etsy Open API v3 with the user's own free API key**. Reading the page the user already has open (no crawling, no background fetching of Etsy HTML) is a secondary, opt-in path. That path is a grey area, and Section 6 explains why.
5. Everything is deterministic: statistics, rules and the user's own collected history. No AI anywhere.

---

## 1. Competitor research

Sources were official sites, Chrome Web Store listings, help centres and independent reviews. Prices change often and the sources disagree. The figures below are the most consistent ones and should be checked again before publishing any comparison.

### 1.1 Platforms reviewed

| Platform | Type | Pricing (as found) | Core strength | Main weakness |
|---|---|---|---|---|
| **eRank** | Web app + extension | Free (5 keyword lookups/day, 1 shop, 50 listings); Basic $5.99, Pro $9.99, Expert $29.99/mo; annual ~25% off | Keyword tool (volume, clicks, competition, trend), listing audits, top-100 listing analysis, competitor tracking, Trend Buzz, multi-marketplace | Volume is its own model; daily quotas; dense UI |
| **EverBee** | Extension + web app | Free "Hobby" hides sales/revenue; Growth ~$19.99 and Business ~$69/mo annual (other sources say $29/$99) | Sales and revenue overlay on search results, listing age, tags, keyword score | Estimate method is a black box; key data paywalled; billing complaints |
| **Alura** | Web app + extension | Free (5 searches/day, 10 listings to optimise); paid from ~$7.99–$13.99/mo | Keyword Finder, Product Seeker, Shop Analyzer, estimated sales in search results | Heavy AI features (which we exclude); same estimate black box |
| **EHunt (EtsyHunt)** | Extension + web app | Free plan; Basic $9.99, Pro $19.99, Elite $59.99, Team $79.99 | Sales, weekly sales and favourites overlay; product and shop databases | Reports of zero-stat results; ~80% accuracy claim not verified |
| **Marmalead** | Web app | ~$15.83–19/mo; no free plan | Keyword engagement and competition, seasonality, listing grades | No product or sales research; paid only |
| **Sale Samurai** | Web app + extension | ~$8.30–10/mo; 3-day trial | Keyword ideas, volume estimates, tag tools | Volume accuracy questioned; AI tag generator |
| **Koalanda** | Web app | Freemium | Long-tail keyword tool, listing editor | Little public documentation |
| **Keywords Everywhere** | Extension | Credits | Shows Google volume on Etsy | Openly says no tool has real Etsy volume, and Google intent differs from Etsy |
| **InsightAgent, Listadum, EtsiMator, others** | Calculators | Free / freemium | Review × multiplier calculators | Fixed multipliers ranging from ×3 to ×20, with nothing to back them |

### 1.2 Feature comparison matrix

Legend: E = eRank, EB = EverBee, A = Alura, EH = EHunt, M = Marmalead, S = Sale Samurai. F = free, P = premium, F/P = limited free.
"Implement" values: **Yes** = build it; **Better** = build an improved version; **Limited** = build it with its data limits clearly shown; **No** = leave it out.

| Feature | Who has it | What it does / how it works | Tier | Limitation in competitors | Implement | How we improve it |
|---|---|---|---|---|---|---|
| Sales overlay on search results | EB, A, EH | Shows estimated sales and revenue on each card | F/P | Black-box estimate; paywalled | **Better** | Shows the method, confidence grade and range; observed figure kept apart from modelled figure |
| Listing sales estimate | EB, A, EH | Est. monthly and total sales | P | One number, no range | **Better** | Uses the shop's own sales-to-review ratio, gives a low/high band, and lets the user override assumptions |
| Revenue estimate | EB, A, EH | Sales × price | P | Ignores discounts and currency | **Yes** | Configurable price, discount and currency; labelled "estimated gross" |
| Listing age | EB, EH | Days since created | F | Shows only one date | **Yes** | Uses both `original_creation` and `last_modified`, with "renewed" flagged |
| Tags of any listing | E, EB, A | Reads public tags | F/P | Quotas | **Yes** | Unlimited, local, comparable |
| Keyword search volume | E, M, S, A, EB | Estimated searches/month | F/P | All modelled; no method published | **Limited** | No made-up volume. We show demand *indicators* and say what each one is (Section 3.2) |
| Keyword competition | All | Listing count for the term | F | Mostly the raw count | **Better** | Count plus the strength of the top results (reviews, shop age, sales) |
| Keyword trend | E, M | Monthly trend chart | P | Data from the vendor | **Limited** | Built only from the user's own snapshots, plus a link-out to Google Trends that the user opens themselves |
| Related / long-tail keywords | All | Suggestions | F/P | Often AI-generated | **Yes** | N-gram extraction from top-result titles and tags, plus autocomplete the user has seen; deterministic |
| Keyword score | EB, A, M | Composite score | P | Opaque | **Better** | Open formula with weights the user can adjust |
| Keyword lists | E, A | Save lists | F/P | Capped | **Yes** | Folders, tags, history, CSV/XLSX |
| Listing SEO audit | E, A, M | Rule-based grade | F/P | Some rules are AI-based | **Yes** | Every rule documented and deterministic |
| Title / tag / description tools | E, S, A | Analyse fields | F/P | Mixed with AI generation | **Yes** | Analysis only; nothing generated |
| Shop analyzer | A, E, EH | Shop stats, best sellers | F/P | Best sellers are estimated | **Better** | Best sellers ranked by reviews, with the method shown; real sales counter |
| Competitor tracking | E, EH | Monitor shops | P | Limited to N shops | **Better** | Unlimited local monitoring; diff log for new/removed listings, price, tags, title, counters |
| Product database | EH, A (Product Seeker) | Search the vendor's crawled DB | P | Relies on the vendor's crawling | **Limited** | Built from API search results the user runs; no hidden crawling |
| Trend Buzz / trending lists | E, EH | Vendor's trending terms | P | Vendor data | **Limited** | "Rising in *your* tracked data" only; never shown as Etsy-wide |
| Seasonal calendar | E, M | Holiday calendar | F | Static | **Better** | Dates computed per country (Easter algorithm, regional Mother's Day), lead-time windows, linked to the user's keywords |
| Data export | E, EB, A | CSV | P | Paywalled | **Yes** | CSV, XLSX and JSON backup, all free |
| Multi-marketplace | E | Amazon, eBay and others | P | — | **No** | Out of scope |
| AI title/tag/description writers, chat | A, S, EB | LLM output | P | — | **No** | Excluded by project rules |

### 1.3 Gaps in the market (our differentiators)

1. **Verified-vs-estimated split** on every number, through a badge system: *Verified* (Etsy shows it), *Observed* (difference between our own snapshots), *Estimated* (modelled).
2. **Observed shop sales velocity**: lifetime-counter differences between snapshots give real sales per day for a shop. No competitor highlights this.
3. **Per-shop sales/review calibration** instead of a fixed multiplier of ×3–×20.
4. **Confidence grades and ranges** (A–D) based on data quality: review count, shop size and snapshot age.
5. **Transparent, editable scoring**: every score opens a "how was this calculated" panel showing the inputs.
6. **Listing change history**: a diff of title, tags, price, images and variations between snapshots (competitors' versions are shallow).
7. **Price-distribution analysis** for any search: histogram, quartiles and the user's own position.
8. **Keyword overlap matrix** across competitor shops, using tag set intersection and Jaccard similarity.
9. **Saturation index**: results count against the review depth of the top N.
10. **Fully local and free**: no account and no quotas. Backup and restore runs on JSON files.

---

## 2. Data sources and what each one can support

| Source | Data | Legitimacy | Notes |
|---|---|---|---|
| **Etsy Open API v3 (user's own API key)** | Active listings search (keywords, sort, price filter, taxonomy), listing details (title, tags, price, currency, `num_favorers`, `views`*, creation/modified timestamps, taxonomy, digital flag, images, variations/inventory), shop (`transaction_sold_count`, `review_count`, `review_average`, `create_date`, active listing count), reviews by shop/listing | **Official.** Needs a free developer app; the user keeps their own key; rate limit about 10 req/s and 10k/day by default | Primary path. *Some field availability must be checked against the live reference during Stage 2, because the reference page did not render for our fetcher. |
| **Etsy OAuth (user's own shop)** | The user's own listings, private fields | Official | Optional. Used to audit the user's own listings |
| **Current page DOM (the tab the user opened)** | Same visible fields as above | **Grey area** (see 6.2) | Opt-in, read-only, passive; no requests made to Etsy |
| **Etsy autocomplete** | Suggestion strings | Unofficial endpoint; terms unclear | **Off.** We only record suggestions the user sees in the search box, if they opt in |
| **Google Trends** | Relative interest | No official API | User-initiated link-out only; we never fetch it |
| **Local snapshot history** | Everything above over time | User's own data | The basis for all trend and velocity features |
| **Exchange rates** | FX | Free public APIs (e.g. ECB reference rates) | Optional; the user can enter rates by hand |

---

## 3. Methodology (deterministic, no AI)

### 3.1 Sales estimation

Inputs:
- `S_shop`: shop lifetime sales (Verified)
- `R_shop`: shop review count (Verified)
- `R_listing`: listing review count (Verified, from reviews-by-listing)
- `age`: listing age in days

Steps:
1. **Shop calibration ratio** `k = S_shop / R_shop`. This is the shop's own sales per review. If `R_shop < 20`, fall back to the median `k` across the shops the user has tracked, or to a user-set default. Confidence drops one grade.
2. **Listing lifetime sales (est.)** `= R_listing × k`. The band uses `k` computed with a ±√R Poisson interval on review counts.
3. **Velocity.** If the listing's review count has been observed at two snapshots: `(ΔR_listing × k) / Δdays`. Otherwise use lifetime / age, flagged "age-averaged, assumes even sales over time".
4. **Daily/weekly/monthly/yearly** = velocity × 1 / 7 / 30.44 / 365.
5. **Shop-level observed velocity**: `ΔS_shop / Δdays` from snapshots. **Observed**, not estimated.
6. **Confidence grade (A–D)** from review count, shop size, snapshot count and how fresh the data is.

What the user sees: estimates show a range and an "≈" badge. The tooltip names the formula and its inputs. Estimates are never shown without the "Estimated" label.

Known limitations, stated in the UI: review rates differ by category (gifts get fewer reviews); multi-item orders; listings that were deleted or renewed; digital products.

### 3.2 Keyword research without inventing search volume

We will **not** show a "searches per month" number. Instead we show:

| Indicator | Source | What it measures | Limitation |
|---|---|---|---|
| **Supply**: active results | API `count` | Competition | Broad-match count |
| **Market depth**: Σ reviews and median reviews of the top 48 | API | Proven demand in the results | Lagging; review rate varies |
| **Engagement**: median favourites of the top 48 | API | Interest | Favourites ≠ purchases |
| **Top-result velocity**: median est. sales/month of the top 48 | §3.1 | Demand proxy | Inherits the estimate's uncertainty |
| **Freshness**: share of the top 48 created in the last 90 days | API | How easy it is to enter | Small sample |
| **Shop concentration**: Herfindahl index across shops in the top 48 | API | Dominance | — |
| **Own-history trend** | Snapshots | Direction of change | Only after repeated checks |

**Keyword difficulty (0–100)** = 100 × weighted mean of normalised log(supply), the median review depth of the top 48, and shop concentration.

**Opportunity score (0–100)** = weighted sum of: demand proxy (+), difficulty (−), trend slope (+), specificity (word count / long-tail bonus) (+), multiplied by a data-quality factor. The weights are sliders, and the formula is shown in the UI.

**Suggestions**: n-grams (2–4 words) from titles and tags of the top results, ranked by document frequency, then split into broad (1–2 words), long-tail (3+ words), buyer-intent (a lexicon of words such as "personalized", "gift for", "custom", "set") and seasonal (a holiday lexicon). All of it is lexical, with no models.

### 3.3 SEO audit rules (examples)

Current Etsy limits are a 140-character title, 13 tags of 20 characters each, and 1–20 images (to be checked again in Stage 2).

The audit checks: title length band; duplicate words; whether the primary keyword is in the first 40 characters; the number of tags used; tag lengths; duplicate tags; tag words already covered in the title; multi-word tag usage; overlap with the user's researched keywords; description length; whether the first 160 characters contain the keyword; Flesch reading ease; repeated phrases (3-gram duplicates); and checklists for materials, size and shipping. Each rule has an ID, a severity, an explanation and a pass/fail result.

### 3.4 Trends and history

Charts show only periods we have data for (7d, 30d, 90d, 6m, 12m, 24m). Periods without data are greyed out and labelled "collected since <date>". The holiday calendar is computed (Easter uses the Anonymous Gregorian algorithm, US/UK Mother's Day, Black Friday = the 4th Thursday of November + 1, and so on), with configurable lead-time windows.

---

## 4. Technical feasibility

| Category | Features |
|---|---|
| **Fully implementable** | SEO audit, title/tag/description analysers, listing comparison, keyword lists/folders, collections, research history, CSV/XLSX/JSON export, backup/restore, seasonal calendar, price distribution, keyword overlap, scoring engine, themes, currency conversion with manual rates |
| **Implementable with limits** | Sales and revenue estimates (modelled, with confidence); keyword demand indicators (no true volume); trend charts (only from collected history); competitor monitoring (only while the browser runs, using `chrome.alarms` and API quota); product discovery (only from the user's API searches); views and favourites (only if the API exposes them) |
| **Requires an external API** | Etsy Open API v3 (free key, user-supplied); optional FX rates |
| **Not feasible / excluded** | True Etsy search volume; Etsy-wide trending lists; verified per-listing sales; competitors' private stats; anything that needs crawling, CAPTCHA handling or logged-in scraping; AI features |

---

## 5. Proposed architecture

### 5.1 Stack
- Manifest V3, **TypeScript**, built with **Vite** (one build gives Chrome and Opera).
- UI uses plain TS with **Preact** (MIT, ~4 kB) for the dashboard; no heavy framework.
- Charts use **uPlot** (MIT, small, fast) for time series and hand-written SVG for histograms.
- XLSX export uses **SheetJS CE** (Apache-2.0), bundled locally; MV3 does not allow remote code.
- Storage uses **IndexedDB** (via `idb`, ISC) for snapshots and history, and `chrome.storage.local` for settings.
- Tests use **Vitest** for the engines and **Playwright** for loading the extension and checking pages against saved Etsy HTML fixtures.

### 5.2 Opera compatibility
- Opera runs Chromium MV3 extensions. Opera does **not** reliably support Chrome's `sidePanel` API; it has its own `sidebar_action` key.
- Plan:
  1. A full-tab **dashboard** (`dashboard.html`) is the main workspace.
  2. An **in-page panel** inside a Shadow DOM on Etsy pages, so Etsy's CSS is isolated in both directions.
  3. A `sidebar_action` entry for Opera and `side_panel` for Chrome, both pointing to the same compact view.
- Installation for development: `opera://extensions`, then Developer mode, then "Load unpacked". Publishing goes to addons.opera.com.

### 5.3 Modules
```
src/
  manifest.ts               # generates manifest for chrome/opera targets
  background/               # service worker: API client, rate limiter, alarms (monitoring), message router
  content/                  # Etsy page integration (search / listing / shop), Shadow-DOM panel, badges
    extractors/             # passive, read-only page parsers (opt-in) with versioned selectors
  ui/
    popup/                  # quick lookup + open dashboard
    dashboard/              # routes: products, keywords, competitors, seo, trends, saved, history, settings
    sidebar/                # compact view (Opera sidebar_action / Chrome side_panel)
    components/             # table, chart, badge(Verified/Observed/Estimated), score explainer
  core/
    api/etsy.ts             # typed Etsy v3 client, quota accounting, caching TTL
    storage/                # IndexedDB schema, migrations, backup/restore
    engines/
      sales.ts              # §3.1
      keywords.ts           # §3.2 indicators, difficulty, opportunity, n-grams
      seo.ts                # §3.3 rule set
      competitors.ts        # diffing, overlap, comparison
      trends.ts             # time series from snapshots, holiday calendar
      stats.ts              # quantiles, HHI, Jaccard, Poisson CI, Flesch
    export/                 # CSV, XLSX, JSON, printable HTML report
  shared/                   # types, currency, i18n strings
```
Engines are pure functions with no browser APIs, which makes them fully unit-testable.

### 5.4 Data model (IndexedDB stores)
- `listings` {listingId, title, url, shopId, price, currency, tags[], taxonomyId, isDigital, createdAt, modifiedAt, imageUrls[], variations, source, fetchedAt}
- `listingSnapshots` {listingId, ts, price, reviews, favourites, views?, title, tagsHash, imagesHash}
- `shops` {shopId, name, url, createdAt, ...}
- `shopSnapshots` {shopId, ts, salesCount, reviewCount, rating, activeListings, listingIds[]}
- `keywords` {term, folderId, notes, createdAt}
- `keywordSnapshots` {term, ts, resultCount, top48Stats{...}, indicators{...}}
- `collections`, `folders`, `history` {type, query, ts}, `changeLog` {entity, id, ts, field, old, new}
- `settings` {apiKey (stored locally, never synced), theme, currency, fxRates, scoringWeights, estimateDefaults, pageReadingOptIn}

### 5.5 Permissions (minimal)
`storage`, `alarms`, `unlimitedStorage`; host permissions `https://openapi.etsy.com/*` and `https://www.etsy.com/*` (content script only). No `tabs`, no `<all_urls>`, no `cookies`, no `webRequest`.

### 5.6 UI structure
The dashboard has a left nav with the sections Products · Keywords · Competitors · SEO · Trends · Saved · History · Settings. There is a top bar with a global search, a currency switch and a theme toggle. Cards hold the KPIs and dense tables handle sorting and filtering. Every metric has a provenance badge and an ⓘ "how calculated" popover. Light and dark themes use CSS tokens, and the layout works down to 360 px.

---

## 6. Legal and compliance design

### 6.1 Rules we follow
- Etsy developer criteria: *"Applications must not sidestep the API to retrieve or post Etsy data. Screen-scraping is not allowed."* We therefore use the **API as the primary source**.
- Required notice, shown prominently: *"The term 'Etsy' is a trademark of Etsy, Inc. This application uses the Etsy API but is not endorsed or certified by Etsy, Inc."*
- The product name must not contain "Etsy" as a brand (trademark policy), so we use a neutral name.
- We respect rate limits (a token bucket at ≤5 req/s, daily quota tracking, exponential backoff on 429 errors); there is no key rotation to get around limits.
- Caching: we keep snapshots because the user asked to track them; the Section 1 caching rules must be checked once the terms page can be read (it returned 403 to our fetcher).
- We store no buyer names or other personal data from reviews; we keep counts and ratings only.

### 6.2 Grey area: reading the open page
Reading the DOM of a page the user is already looking at is how EverBee, Alura and EHunt work. Third-party summaries say Etsy's API Terms (reportedly updated June 2025) restrict browser extensions from accessing Etsy data without permission. **We could not read the official terms page to confirm this.**

Proposal: page reading is **off by default** and turned on in Settings with a plain-language notice. When it is on, it only parses the current page. It makes no requests to Etsy, does no crawling and does no background tab loading. Everything works with API data alone.

---

## 7. Development roadmap

| Stage | Output |
|---|---|
| 2 Feasibility | Check API fields (`views`, `num_favorers`, reviews-by-listing, taxonomy) against the live reference with a test key; confirm Etsy's title/tag limits |
| 3 Spec | Freeze scoring formulas, rule IDs and the data schema |
| 4 UI | Dashboard shell, design tokens, components, themes |
| 5 Engines | stats → sales → keywords → seo → competitors → trends; unit tests |
| 6 Integration | API client, monitoring alarms, content-script badges and panel, optional page reader |
| 7 Testing | Vitest suites, Playwright extension tests on saved Etsy page fixtures, screen sizes, permissions audit |
| 8 Delivery | Build zip for Opera, README, feature docs, architecture, test report, limitations |

---

## 8. Decisions needed from the user

1. **Data access:** API-key-first, with page reading as an opt-in (recommended). The alternatives are API only, or page reading by default as the competitors do.
2. **Repository location:** this branch lives in `schoolmaroc`. Keep the project in `etsy-research-extension/`, or move it to a dedicated repository?
3. **Extension name:** it must not use "Etsy" as a brand. Proposal: "Shoplens Research" (placeholder).

---

## Sources
- eRank plans: https://erank.com/plans · help: https://help.erank.com/blog/choosing-the-right-erank-plan-for-you/
- EverBee: https://chromewebstore.google.com/detail/everbee/oeicpkgdngoghobnbjngekclpcmpgpij · review: https://ehunt.ai/blog/everbee-review · https://revenuegeeks.com/software/everbee
- Alura: https://www.alura.io/features/chrome-extension · https://www.alura.io/comparison · https://www.nichepursuits.com/alura-review/
- EHunt: https://chromewebstore.google.com/detail/ehunt-etsy-rank-tool/pmpgnefoilpinnblccjddomajohmbpko · https://revenuegeeks.com/software/etsyhunt/pricing · https://www.nichepursuits.com/etsyhunt-review/
- Marmalead / Sale Samurai / Koalanda: https://salesamurai.io/sale-samurai-vs-marmalead · https://craftybase.com/blog/best-etsy-seo-tools · https://contentmavericks.com/best-etsy-seo-tools/
- Search volume: https://keywordseverywhere.com/etsy-search-volume.html · https://apify.com/maximedupre/etsy-keywords-research-tool
- Sales-estimate heuristics: https://sellertoolshq.com/guides/etsy-shop-revenue-estimator/ · https://apify.com/marielise.dev/etsy-sales-intelligence
- Etsy API: https://developer.etsy.com/documentation/ · https://developer.etsy.com/documentation/essentials/rate-limits/ · https://www.etsy.com/legal/api
