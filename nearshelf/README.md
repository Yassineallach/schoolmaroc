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

## Build

Needs JDK 17+ and an Android SDK with platform 37 (`sdk.dir` in `local.properties`).

```
./gradlew :core:test                 # unit tests (fixtures, offline)
./gradlew :app:assembleDebug         # debug APK
./gradlew :core:test -Pnearshelf.live=true --tests '*LiveTest'   # hits real endpoints
```

## Verified endpoints

| Provider | Endpoint | Verified |
|---|---|---|
| OverDrive library lookup | `GET https://locate.libbyapp.com/autocomplete/{query}` → `branches[].systems[].fulfillmentId` | 2026-11-17 |
| OverDrive availability | `GET https://thunder.api.overdrive.com/v2/libraries/{key}/media?query=…&perPage=24` (title text or ISBN) | 2026-11-17 |
| Libby title deep link | `https://libbyapp.com/library/{key}/title/{id}` (Libby router's `title-redirect-controller`; libbyapp.com `assetlinks.json` delegates to `com.overdrive.mobile.android.libby`) | 2026-11-17 |

## Milestones

1. [x] Spike: skeleton, `CatalogProvider`, OverDrive provider, fixtures, parser tests, debug screen
2. [ ] Core: library management, search, `BookMatcher`, streaming Results, Libby deep links
3. [ ] Share sheet, barcode scanner, Open Library ISBN expansion
4. [ ] Hoopla
5. [ ] Library registry, URL auto-detection, registry build script, home branch
6. [ ] BiblioCommons, Koha
7. [ ] Evergreen, Aspen, Polaris, Sierra
8. [ ] Location sorting, watchlist, notifications, caching, rate limiting, provider health
9. [ ] Widget, history, offline, filters
10. [ ] AdMob + UMP, settings, about, privacy, French/Arabic + RTL
11. [ ] Release polish
