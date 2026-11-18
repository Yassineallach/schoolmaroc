# Nearshelf

"Your next book, on a shelf near you." An Android app that shows a book's ebook,
audiobook and print availability across every library you belong to, and hands
off to the official app or catalog page to borrow or place a hold.

Not affiliated with OverDrive, Hoopla, or any library or catalog vendor.

## Layout

| Module | What lives there |
|---|---|
| `core/` | Pure Kotlin/JVM: domain model, `CatalogProvider` and each provider's HTTP + parsing. No Android types, so every parser is unit-tested on the JVM against recorded responses in `core/src/test/resources/fixtures/`. |
| `app/` | Android app: Compose UI, Hilt wiring, later Room/WorkManager/Glance. Never calls an endpoint directly. |

## Design sources

- Design system from [ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill): "book brown + page amber" palette on paper, Cormorant Garamond display type (OFL, bundled), its Jetpack Compose guidelines (stateless composables, `collectAsStateWithLifecycle`, keyed lazy lists, typed routes).
- Components ported from [Lightswind UI](https://github.com/codewithMUHILAN/Lightswind-UI-Library) (MIT) to Compose: `Skeleton`, `CountUp`, `Badge`, `TopLoader` in `app/.../ui/components/lightswind/`.
- Icons: [Phosphor](https://phosphoricons.com) (MIT), converted with `tools/phosphor_to_vector.py`.
- Licence texts ship in `app/src/main/assets/licenses/` for the in-app licences screen (milestone 10).

## Ads

Native AdMob ads only, inside content (never banners, never at the bottom, never interstitials,
never in notifications or the widget): after the first library card on Results, after the 2nd
book on Watchlist, after the 3rd entry on History. Google UMP consent runs at every launch.
Test IDs are used unless `local.properties` contains:

```
admob.appId=ca-app-pub-XXXXXXXXXXXXXXXX~YYYYYYYYYY
admob.nativeUnitId=ca-app-pub-XXXXXXXXXXXXXXXX/ZZZZZZZZZZ
```

## Build

Needs JDK 17+ and an Android SDK with platform 37 (`sdk.dir` in `local.properties`).

```
./gradlew :core:test                 # unit tests (fixtures, offline)
./gradlew :app:assembleDebug         # debug APK
./gradlew :core:test -Pnearshelf.live=true --tests '*LiveTest'   # hits real endpoints
```

## Library registry

`app/src/main/assets/libraries.json` maps libraries to their catalog systems, Libby key,
Hoopla id and branches. Rebuild and check it with:

```
python3 tools/registry/build_registry.py          # ~15 min, one request per second; writes report.md
python3 tools/registry/build_registry.py --update "Seattle"   # redo matching rows only
python3 tools/registry/validate_registry.py
```

Add libraries in `tools/registry/seed.csv`. A catalog candidate is kept only if its software
is recognised and its page title names the library; prefix a URL with `!` only after checking
by hand that it belongs to that library (generic titles like "Vega Discover").

**Weekly updates:** publish `libraries.json` in a public repo and set its raw URL in
`gradle.properties` as `nearshelf.registryUrl=https://raw.githubusercontent.com/<you>/<repo>/main/libraries.json`.
The app downloads it at most once a week and falls back to the bundled copy.

## Verified endpoints

| Provider | Endpoint | Verified |
|---|---|---|
| OverDrive library lookup | `GET https://locate.libbyapp.com/autocomplete/{query}` → `branches[].systems[].fulfillmentId` | 2026-11-17 |
| OverDrive availability | `GET https://thunder.api.overdrive.com/v2/libraries/{key}/media?query=…&perPage=24` (title text or ISBN) | 2026-11-17 |
| Open Library edition | `GET https://openlibrary.org/isbn/{isbn}.json` (title, `languages`, `works`, `covers`; 404 if unknown) | 2026-11-18 |
| Open Library work + all ISBNs | `GET https://openlibrary.org/search.json?isbn={isbn}&fields=key,title,author_name,isbn,language,cover_i` (55 ISBNs → 28 unique ISBN-13s for Project Hail Mary, ebook ISBN included) | 2026-11-18 |
| Goodreads share pages | `goodreads.com/book/show/{id}` serves JSON-LD `Book` with `isbn`, `name`, `author`, `inLanguage` | 2026-11-18 |
| Amazon product pages | `/dp/{ASIN}`; ISBN-10 ASINs are ISBNs; page `<title>` is `Title: Last, First: ISBN: Amazon.com: Books` | 2026-11-18 |
| StoryGraph | Pages answer 403 with a Cloudflare challenge; not fetched, share text used instead | 2026-11-18 |
| Hoopla libraries | `GET https://patron-api-gateway.hoopladigital.com/core/libraries/autocomplete?query=…` (headers `app: WWW`, `ws-api: 2.1`) | 2026-11-18 |
| Hoopla search | `POST https://patron-api-gateway.hoopladigital.com/graphql` `search(criteria:{q, pagination})`, whole catalog, no login | 2026-11-18 |
| Hoopla deep link / covers | `https://www.hoopladigital.com/title/{id}` (App Link to `com.hoopladigital.android`); `https://cover.hoopladigital.com/{artKey}_270.jpeg` | 2026-11-18 |
| Libby branches | `GET https://locate.libbyapp.com/branches/{websiteId}`: every branch with address and coordinates (Toronto: 103) | 2026-11-18 |
| BiblioCommons | `gateway.bibliocommons.com/v2/libraries/{code}/bibs/search?query=…&searchType=smart`, `/bibs/{id}/availability` (per copy); record page `{code}.bibliocommons.com/v2/record/{id}` | 2026-11-18 |
| Koha | `/cgi-bin/koha/opac-search.pl?q=…&format=rss`; `/api/v1/public/biblios/{id}/items`, `/api/v1/public/libraries`. Many hosts put bot checks in front (Cloudflare 429, JS challenge) | 2026-11-18 |
| Evergreen | `/opac/extras/opensearch/1.1/-/atom-full/keyword/?searchTerms=title:… author:{surname}` (copies inline); record `/eg/opac/record/{id}` | 2026-11-18 |
| Polaris | session: `search/searchresults.aspx`, then `search/components/ajaxResults.aspx?page=1`, `ajaxavailability.aspx?pos=…&bibid=…`; permalink `view.aspx?cn=` | 2026-11-18 |
| Vega | `POST https://{region}.iiivega.com/api/search-result/search/format-groups` (header `iii-customer-domain`), `drawer/format-groups/{id}/locations?tab=`; card `search/card?id=…&entityType=FormatGroup` | 2026-11-18 |
| Sierra WebPAC | `/search~S1/?searchtype=X&searcharg=…`, record `/record={b…}~S1` | 2026-11-18 |
| Aspen | API IP-restricted; catalogs behind Cloudflare or JS challenge: link to `/Search/Results?lookfor=…` only | 2026-11-18 |
| Libby title deep link | `https://libbyapp.com/library/{key}/title/{id}` (Libby router's `title-redirect-controller`; libbyapp.com `assetlinks.json` delegates to `com.overdrive.mobile.android.libby`) | 2026-11-17 |

## Milestones

1. [x] Spike: skeleton, `CatalogProvider`, OverDrive provider, fixtures, parser tests, debug screen
2. [x] Core: library management, search, `BookMatcher`, streaming Results, Libby deep links
3. [x] Share sheet, barcode scanner, Open Library ISBN expansion
4. [x] Hoopla (see docs/providers/hoopla.md)
5. [x] Library registry, URL auto-detection, registry build script, home branch
6. [x] BiblioCommons, Koha
7. [x] Evergreen, Polaris, Sierra (WebPAC, Vega); Aspen link-only
8. [x] Location sorting, watchlist, notifications, caching, rate limiting, provider health
9. [x] Widget, history, offline, filters
10. [x] AdMob native ads (in content) + UMP, settings, about, privacy policy, licences (no translations: English only, by decision)
11. [x] Release polish: onboarding, icon, accessibility, empty/error states, signing, baseline profile module, Play listing and Data Safety (docs/play-store.md)

## Screenshot tests

`./gradlew :app:testDebugUnitTest -Pnearshelf.screenshots=true` renders Results, empty state, onboarding and About on a phone, a small phone, landscape, 2× font and dark mode (Roborazzi + Robolectric, no device). PNGs land in `app/build/outputs/roborazzi/`.

## Release

1. Add to `local.properties` (never committed): `admob.appId`, `admob.nativeUnitId`, `release.storeFile`, `release.storePassword`, `release.keyAlias`, `release.keyPassword`.
2. `./gradlew test :app:lintRelease :app:bundleRelease`, which produces `app/build/outputs/bundle/release/app-release.aab`.
3. Optional, with a phone connected: `./gradlew :app:generateReleaseBaselineProfile` (faster cold start).
4. Listing text, screenshots plan, Data Safety answers and the pre-release checklist: docs/play-store.md.
