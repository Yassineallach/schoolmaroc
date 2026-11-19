# Play Store submission

## Listing

**App name (30 max):** Nearshelf: Library Book Finder

**Short description (80 max):**
Check ebooks, audiobooks and print copies across all your libraries at once.

**Full description:**

Your next book, on a shelf near you.

Nearshelf searches every library you belong to in one go and shows where a book is available: as an ebook, an audiobook, or a print copy on a branch shelf.

• One search, all your libraries: Libby/OverDrive collections, hoopla, and library catalogs (BiblioCommons, Polaris, Evergreen, Koha, Sierra, Vega)
• eBook, audiobook and print in their own tabs, the quickest way to each first: copies, holds and days to wait at a glance
• Many books share a title? Pick yours, and results show only that book
• Nearest branch first: print copies are sorted by distance (your location never leaves your phone)
• Share from anywhere: share a book from a browser or a reading site and Nearshelf finds it
• Scan a barcode in a bookshop to check if your library has it
• Watchlist: choose the formats and libraries to watch, and get a notification when the book becomes available, lands on a shelf, or the wait drops
• Home-screen widget and offline results

When you find a copy, Nearshelf opens the library's own app or website so you can borrow it or place a hold. No account needed. Nearshelf never asks for your library card or PIN.

Nearshelf is not affiliated with OverDrive, hoopla, or any library or catalog vendor. Libby, OverDrive and hoopla are trademarks of their owners.

**Category:** Books & Reference. **Tags:** library, ebooks, audiobooks.
**Contact email:** mardevlopm@gmail.com · **Developer:** MAR Dev
**Privacy policy URL:** https://yassineallach.github.io/schoolmaroc/privacy/ (publish docs/privacy/index.html with GitHub Pages first)

## Screenshots (phone, 1080×2400, 4–8)

1. Results for a popular title on the Audiobook tab: cards from 3 libraries, fastest first (caption: "Every library, one search")
2. Branch list sorted by distance with "On shelf" badges ("Find the nearest copy")
3. Share sheet from a browser into Nearshelf ("Share a book from anywhere")
4. Barcode scanner ("Scan in the bookshop")
5. Watchlist with a "Now available" notification ("Know when it's your turn")
6. Libraries screen with home branch ("All your library cards' libraries")
7. Widget on the home screen

Take them on a phone with the release build and test ads turned off, or crop the ad card out: Play forbids showing test ads. Feature graphic: 1024×500, brown #7C3A10 background, icon + "Your next book, on a shelf near you."

## Content rating

Questionnaire category: Reference/utility. No violence, sexual content, gambling, or user interaction/chat. Ads: yes.
Target audience: 13+ (not designed for children; the ads are not in Families mode).

## Data Safety form

Answers match PRIVACY.md and the merged manifest. The app has no server. Data only "leaves" through (a) user-requested searches to library services, and (b) the AdMob SDK.

| Question | Answer |
|---|---|
| Does the app collect or share required user data types? | Yes (because of the AdMob SDK) |
| Is all data encrypted in transit? | Yes (HTTPS only; cleartext is blocked by default at targetSdk 28+) |
| Can users request deletion? | Data stays on the device; uninstalling deletes it. AdMob: advertising ID is reset by the user in Android settings |

Declared types (all from the Google Mobile Ads SDK, per Google's [SDK data disclosure](https://developers.google.com/admob/android/privacy/play-data-disclosure)):

| Data type | Collected | Shared | Optional | Purpose |
|---|---|---|---|---|
| Location › Approximate location (IP-derived) | Yes | Yes | No | Advertising, analytics, fraud prevention |
| App activity › App interactions | Yes | Yes | No | Advertising, analytics |
| App info and performance › Diagnostics, crash logs | Yes | Yes | No | Analytics, fraud prevention |
| Device or other IDs › Advertising ID | Yes | Yes | No | Advertising, analytics, fraud prevention |

Not declared, and why:
- **Precise or coarse location from the app itself:** used on-device only to sort branches; never transmitted.
- **Photos/camera:** barcode frames are processed on-device by ML Kit and discarded.
- **Search terms:** sent only to the library service the user is searching, when they search, to perform that search (a user-initiated transfer); the developer receives nothing. If a reviewer disagrees, declare "App activity › In-app search history: shared, not stored, app functionality".
- **Library cards/credentials:** never requested.

Ads declaration: "Contains ads" = Yes. Advertising ID permission (`AD_ID`) is present through the Ads SDK, purpose: advertising.

## Before release (checklist)

- [x] Contact email in PRIVACY.md and `app/src/main/assets/privacy.md` (the test keeps them identical)
- [ ] Publish `docs/privacy/index.html` with GitHub Pages (Settings › Pages › Deploy from a branch › `/docs`) and put the URL in Play Console
- [ ] AdMob app + native ad unit; put `admob.appId` and `admob.nativeUnitId` in `local.properties`, and add `app-ads.txt` on your developer website
- [ ] Upload keystore; `release.storeFile/storePassword/keyAlias/keyPassword` in `local.properties`; enrol in Play App Signing
- [ ] Optional: `nearshelf.registryUrl` pointing to the hosted `libraries.json` for weekly updates
- [ ] Optional: generate the baseline profile on a device: `./gradlew :app:generateReleaseBaselineProfile`
- [ ] `./gradlew test :app:lintRelease :app:bundleRelease` and upload `app/build/outputs/bundle/release/app-release.aab` to internal testing first
