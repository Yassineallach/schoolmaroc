# Google Play listing: everything to enter in Play Console

Images are in `docs/play-listing/` (regenerate: see the end). Text below is ready to paste;
character counts are checked against Play's limits.

---

## 1. Main store listing (Grow › Store presence › Main store listing)

**App name** (30 max, this is 30):
```
Nearshelf: Library Book Finder
```

**Short description** (80 max, this is 76):
```
Check ebooks, audiobooks and print copies across all your libraries at once.
```

**Full description** (4000 max):
```
Your next book, on a shelf near you.

Nearshelf searches every library you belong to in one go and shows where a book is available: as an ebook, an audiobook, or a print copy on a branch shelf near you.

ONE SEARCH, ALL YOUR LIBRARIES
Add the libraries you have a card for. Nearshelf checks their Libby/OverDrive collections, hoopla, and their catalogs (BiblioCommons, Polaris, Evergreen, Koha, Sierra, Vega) at the same time.

THE QUICKEST WAY TO EACH BOOK FIRST
eBook, audiobook and print each have their own tab. The option you can borrow soonest is at the top, with copies, holds and days to wait at a glance.

PRINT COPIES NEAR YOU
See which branches have the book on the shelf, nearest first, and set a home branch. Your location is used on your phone only and never leaves it.

THE RIGHT BOOK, EVERY TIME
Several books share a title? Pick yours, and results show only that book.

WATCH A BOOK
Choose the formats and libraries you care about. Nearshelf checks once a day and sends a notification when the book becomes available, lands on a shelf, or the wait drops.

AND MORE
• Scan a barcode in a bookshop to see if your library has it
• Share a book from your browser or a reading site and Nearshelf finds it
• Home-screen widget, recent searches and offline results
• Light and dark theme

BORROW IN ONE TAP
When you find a copy, Nearshelf opens the library's own app or website so you can borrow it or place a hold.

PRIVATE BY DESIGN
No account. Nearshelf never asks for your library card or PIN, and everything you save stays on your phone.

Nearshelf is free and shows a few ads, never in notifications.

Nearshelf is not affiliated with OverDrive, hoopla, or any library or catalog vendor. Libby, OverDrive and hoopla are trademarks of their respective owners.
```

**Graphics**

| Asset | File | Play's requirement |
|---|---|---|
| App icon | `docs/play-listing/app_icon_512.png` | 512 × 512 PNG, full square (Play rounds the corners) |
| Feature graphic | `docs/play-listing/feature_graphic_1024x500.png` | 1024 × 500 PNG/JPEG |
| Phone screenshots | `docs/play-listing/phone_01_home.png` … `phone_08_home_dark.png` (upload in this order) | 2–8 images, 9:16, 1080 × 1920 |
| Tablet screenshots | optional; skip for now | needed only to be featured for tablets |
| Video | optional; leave empty | YouTube URL |

The screenshots use fictional libraries and public-domain books and show no ads (Play forbids
test ads in store images).

---

## 2. Store settings (Grow › Store presence › Store settings)

- **App or game:** App
- **Category:** Books & Reference
- **Tags** (pick up to 5 that Play offers): Library, Books, eBooks, Audiobooks, Reading
- **Email:** mardevlopm@gmail.com
- **Website:** https://mar-devl.github.io/Nearshelf-legal/
- **Phone:** leave empty

---

## 3. App content (Policy › App content)

**Privacy policy:** `https://mar-devl.github.io/Nearshelf-legal/`

**App access:** "All functionality in my app is available without any access restrictions"
(no login; reviewers add a library from the built-in list).

**Ads:** "Yes, my app contains ads."

**Content rating** (IARC questionnaire):
- Email: mardevlopm@gmail.com · Category: **All other app types** (reference, utility)
- Violence, fear, sexuality, language, controlled substances, crude humour: **No** to all
- Users can interact or exchange content with each other: **No**
- Shares the user's current physical location with other users: **No**
- Allows users to purchase digital goods: **No**
- Unrestricted internet access / web browser: **No** (it opens specific library sites only)
- Gambling or simulated gambling: **No**
- Expected rating: Everyone / PEGI 3 / IARC 3+

**Target audience and content:**
- Age groups: **13–15, 16–17, 18 and over** (not under 13: the ads are not set up for children)
- "Could your store listing unintentionally appeal to children?": **No**

**Data safety:**

| Question | Answer |
|---|---|
| Does your app collect or share any of the required user data types? | **Yes** (through the Google Mobile Ads SDK) |
| Is all user data encrypted in transit? | **Yes** (HTTPS only) |
| Do you provide a way for users to request that their data is deleted? | **No** (no accounts; everything is on the phone and uninstalling removes it) |

Data types to tick (all from the Ads SDK, per Google's
[SDK data disclosure](https://developers.google.com/admob/android/privacy/play-data-disclosure)):

| Data type | Collected | Shared | Processed ephemerally | Required or optional | Purposes |
|---|---|---|---|---|---|
| Location › Approximate location | Yes | Yes | No | Required | Advertising or marketing, Analytics, Fraud prevention, security and compliance |
| App activity › App interactions | Yes | Yes | No | Required | Advertising or marketing, Analytics |
| App info and performance › Crash logs | Yes | Yes | No | Required | Analytics, Fraud prevention, security and compliance |
| App info and performance › Diagnostics | Yes | Yes | No | Required | Analytics, Fraud prevention, security and compliance |
| Device or other IDs | Yes | Yes | No | Required | Advertising or marketing, Analytics, Fraud prevention, security and compliance |

Not declared, and why (so you can answer a reviewer):
- **Location from the app itself:** used on the phone only, to sort branches; never sent anywhere.
- **Camera:** barcode frames are read on the phone by ML Kit and discarded.
- **Search terms:** sent only to the library service being searched, when the user searches
  (a user-initiated transfer); the developer receives nothing. If a reviewer disagrees, add
  "App activity › In-app search history: shared, not collected, app functionality".
- **Library cards / passwords:** never asked for.

**Advertising ID:** "Yes, my app uses advertising ID" · Purposes: Advertising or marketing,
Analytics, Fraud prevention, security and compliance.

**Government app:** No · **Financial features:** none · **Health:** none ·
**News app:** No · **Actions / foreground service declarations:** none needed (the only
foreground-service permission comes from WorkManager, with no typed service).

**Permissions the app requests** (no Play declaration needed for any of them): Internet,
network state, camera (barcode scan), approximate location (nearest branch, on the phone only),
notifications (watchlist alerts), Ads SDK permissions.

---

## 4. Closed test (Test and release › Testing › Closed testing)

1. Create a track, add testers (an email list or a Google Group). New personal developer
   accounts need at least 12 testers opted in for 14 days in a row before production can be
   requested; the Dashboard shows the current rule and your progress.
2. **Feedback URL or email:** mardevlopm@gmail.com
3. Upload `app-release.aab` from the GitHub build (Actions › Build release, test ads **off**).
4. Accept **Play App Signing** when asked (Google keeps the app-signing key; your upload key
   stays yours).
5. **Release name:** `1.0.0 (1)` · **Release notes:**
```
<en-US>
First test release. Add your libraries, search for a book, and tell us what Nearshelf finds (or misses) at mardevlopm@gmail.com.
</en-US>
```
6. Send testers the opt-in link from the track's Testers tab.

After the test: **Promote release › Production** reuses the same bundle. A new build needs a
higher `versionCode` (app/build.gradle.kts).

---

## 5. AdMob and app-ads.txt

- AdMob › Apps › Nearshelf › **App settings › Link to app store** once the listing is live.
- AdMob › Privacy & messaging › **GDPR message**: create and publish it (EU/UK/CH consent).
- Put the line AdMob gives you (Apps › View all apps › app-ads.txt) in a file `app-ads.txt` at
  the root of the developer website: create a repository named `mar-devl.github.io` so it is
  served at `https://mar-devl.github.io/app-ads.txt`. AdMob looks for it on the host of the
  Store settings website (`mar-devl.github.io`), so the website above works as it is.

---

## Regenerating the images

```
./gradlew :app:testDebugUnitTest --tests '*StoreScreenshotTest*' -Pnearshelf.store=true
python3 tools/store/make_store_images.py
```
Captions live in `tools/store/make_store_images.py`; the demo data in
`app/src/test/.../screenshots/StoreScreenshotTest.kt`.
