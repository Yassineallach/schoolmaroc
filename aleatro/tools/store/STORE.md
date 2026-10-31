# Play Console: finishing Aleatro's setup

This covers everything left in Play Console for `com.mardev.Aleatro`, in the
order of the dashboard's **Set up your app** list. Every value to type is
here. Every file to upload is in **`Aleatro-PlayConsole-kit.zip`** (rebuilt
by the steps at the end).

Already covered elsewhere:
- Play Games Services (sign-in, achievements, leaderboards): `tools/play_games/README.md`.
- AdMob and the consent message: `tools/ads/ADS.md`.

---

## 1. Store settings

**Grow users > Store presence > Store settings**

| Field | Value |
|---|---|
| App or game | **Game** |
| Category | **Card** |
| Tags | Pick up to 5 from Play's list. Choose the ones closest to *Card*, *Poker*, *Roguelike*, *Deck building*, *Strategy*, *Single player* and *Offline*. |
| Email address | **mardevlopm@gmail.com** |
| Website | **https://mar-devl.github.io/** (needed for app-ads.txt) |
| Phone | Optional. Leave it empty. |
| External marketing | On |

## 2. Main store listing: the default language (English)

**Grow users > Store presence > Store listings > Main store listing**

Default language: **English (United States) – en-US**.

| Field | Where to copy it from | Limit |
|---|---|---|
| App name | `listing/en-US.txt`, `#title`: **Aleatro: Poker Roguelike** | 30 |
| Short description | `listing/en-US.txt`, `#short` | 80 |
| Full description | `listing/en-US.txt`, `#full` | 4000 |

The same text is also in the kit, laid out per field:
- `metadata/android/en-US/title.txt`
- `metadata/android/en-US/short_description.txt`
- `metadata/android/en-US/full_description.txt`

**Graphics** (all in the kit, under `metadata/android/<locale>/images/`):

| Asset | File | Spec |
|---|---|---|
| App icon | `icon.png` | 512×512, 32-bit PNG with alpha, under 1 MB |
| Feature graphic | `featureGraphic.png` | 1024×500, 24-bit PNG with no alpha |
| Phone screenshots | `phoneScreenshots/1…6` | 1920×1080 (16:9 landscape), 6 per language |
| 7-inch tablet screenshots | `sevenInchScreenshots/1…6` | 1920×1080 |
| 10-inch tablet screenshots | `tenInchScreenshots/1…6` | 2560×1440 |
| Chromebook (optional) | Reuse the 10-inch set | 16:9, 1080 to 7680 px |
| Video (optional) | A YouTube link. It must be public or unlisted, with ads off. | |

The screenshots are JPEGs (quality 92), which keeps the kit small; Play accepts JPEG.

These sizes meet Google's game rule for recommendations (at least three
16:9 landscape screenshots of 1920×1080 or more) and the large-screen rule
(at least 4 at 1080 px or more). Every screenshot shows real gameplay under
a one-line caption that takes less than 15% of the image.

The screenshots, in order:
1. Scoring a Flush: Chips × Mult with charms firing
2. The shop: charms, vouchers and packs
3. Opening a Mega Rune Pack
4. Choosing a blind: Small, Big and Boss Blind with tags
5. The charm collection
6. Picking a deck and a stake

## 3. Translations: 9 more languages

Play Console has no file import for the store listing text, so each language
is pasted in. It's three fields per language, about 20 minutes in all.

1. **Store listings > Main store listing > Manage translations > Add your own
   translations**. Tick the languages below, then **Apply**.
2. Pick each language from the language selector at the top of the listing.
   Paste its three fields from `listing/<locale>.txt` (or from the per-field
   files in `metadata/android/<locale>/`).
3. In that same language, scroll to **Graphics** and upload that language's
   screenshots: phone, 7-inch and 10-inch, from
   `metadata/android/<locale>/images/`. The icon and feature graphic are the
   same in every language, so skip them there.
4. **Save** and move on to the next language.

| Play language | File |
|---|---|
| Chinese (Simplified) – zh-CN | `listing/zh-CN.txt` |
| Japanese – ja-JP | `listing/ja-JP.txt` |
| Korean (South Korea) – ko-KR | `listing/ko-KR.txt` |
| German – de-DE | `listing/de-DE.txt` |
| French – fr-FR | `listing/fr-FR.txt` |
| Spanish (Spain) – es-ES | `listing/es-ES.txt` |
| Portuguese (Brazil) – pt-BR | `listing/pt-BR.txt` |
| Italian – it-IT | `listing/it-IT.txt` |
| Arabic – ar | `listing/ar.txt` |

Optional: add **Spanish (Latin America) – es-419** with the es-ES text and
screenshots. The game's Spanish is neutral enough for both.

Do **not** use **Translations > Store listings and products > Create order**
for these languages. A machine-translation order overwrites the text you
pasted.

Two more files in the kit hold the same text:
- `listings.csv`: all 10 languages in one sheet, to proofread or to keep as a record.
- `metadata/android/`: fastlane `supply`'s folder layout. If you later set up
  a Play Developer API service account, `fastlane supply
  --metadata_path metadata/android --skip_upload_apk --skip_upload_aab`
  uploads every language's text and screenshots in one go.

## 4. App content (Policy > App content)

### Privacy policy
**https://mar-devl.github.io/aleatro-legal/**

### App access
**All functionality is available without special access.** No login is
needed; Play Games sign-in is optional.

### Ads
**Yes, my app contains ads.**

### Content rating (IARC questionnaire)
- Email: mardevlopm@gmail.com. Category: **Game** (not a social, communication
  or reference app).
- **Violence, fear, sexuality, language, controlled substances, crude humour:
  No** to every one. The art is cartoon playing cards and jesters.
- **Gambling.** This answer is yours to make; here is the reasoning.
  - The questionnaire asks whether the game has **simulated gambling**: games
    of chance where you bet a currency on an outcome (slots, blackjack, poker
    with chips at stake).
  - In Aleatro you never place a bet. Poker hands are only a scoring system;
    the "$" is shop money; and "stakes" are difficulty levels. Nothing can be
    bought with real money, and nothing can be cashed out.
  - So **No** to simulated gambling is a defensible answer.
  - If the form also asks about **gambling themes or references**, answer
    **Yes** (poker hands and casino-style terms). That usually gives a low age
    rating with a "gambling themes" descriptor.
  - Answering accurately matters more than the rating: a wrong answer can
    get the rating corrected or the app pulled later.
- **Users can interact or exchange content: No.** Leaderboards and
  achievements are Play Games features with no chat or sharing.
- **Shares the user's current physical location: No.**
- **Allows digital purchases: No.** (Remove ads can't be sold from Morocco; see section 5.)
- **Unrestricted internet access** (web browser or search engine): **No**.

### Target audience and content
- Ages: **13–15, 16–17 and 18+**. Leave 12 and under unticked: AdMob is set up
  for a general audience, and the Families policy would require other ad
  settings.
- **Could the app unintentionally appeal to children?** **No.** It's a
  strategy card game with text-heavy rules; say so in the box if asked.

### News app
**No.**

### Data safety
Answer the questionnaire like this:

**Does your app collect or share any of the required user data types?** Yes.
**Is all of the user data collected by your app encrypted in transit?** Yes.
**Do you provide a way for users to request that their data is deleted?** Not
required. The game has no accounts of its own; the privacy policy explains how
to reset the advertising ID and how to manage Google data. Answer **No**, or
**Yes** with a link to the privacy policy.

| Data type | Collected | Shared | Ephemeral | Required? | Purposes | Why |
|---|---|---|---|---|---|---|
| **Location > Approximate location** | Yes | Yes | No | Required | Advertising or marketing, Analytics, Fraud prevention, security and compliance | AdMob reads the IP address, which estimates a rough location |
| **App activity > App interactions** | Yes | Yes | No | Required | Advertising or marketing, Analytics, Fraud prevention, security and compliance | AdMob: app launches, taps, ad views |
| **App activity > Other actions** | Yes | No | No | Optional | App functionality | Play Games: achievements unlocked and leaderboard scores, when signed in |
| **App info and performance > Diagnostics** | Yes | Yes | No | Required | Advertising or marketing, Analytics, Fraud prevention, security and compliance | AdMob: launch time, hang rate, energy use |
| **Device or other IDs** | Yes | Yes | No | Required | Advertising or marketing, Analytics, Fraud prevention, security and compliance | AdMob: advertising ID and app set ID |
| **Personal info > User IDs** | Yes | No | No | Optional | App functionality | Play Games player ID, only when signed in |

Everything else: **not collected**.
- Name, email, contacts, photos, files, messages, health, precise location,
  web history and so on are not collected.
- Crash logs aren't collected either: the game has no crash reporter.

The AdMob rows follow Google's own disclosure for the Mobile Ads SDK
([developers.google.com/admob/android/privacy/play-data-disclosure](https://developers.google.com/admob/android/privacy/play-data-disclosure)).

The Play Games and Billing rows are the cautious reading: Google handles that
data, but the game's code sends it. If Play Console's own help for those
SDKs says they don't need declaring, you can drop them.

### Advertising ID
**Yes**, the app uses an advertising ID, for **Advertising or marketing**,
**Analytics** and **Fraud prevention, security and compliance**. The AdMob SDK
adds the `AD_ID` permission itself.

### Government apps, Financial features, Health
**No**, **My app doesn't provide any financial features**, and **No health
features**.

## 5. Remove ads: not available from Morocco

Google Play only lets developers sell paid apps and in-app products from
locations that support **merchant registration**, and Morocco is not one of
them ([supported locations](https://support.google.com/googleplay/android-developer/answer/9306917)).
So the `remove_ads` product can't be created, and the game earns through
AdMob only, which pays to Morocco separately from Play.

- **Nothing to do in the game.** The "Remove ads" button only appears once
  Google Play returns a price for `remove_ads`. With no product it never
  shows, and the ads work as usual.
- **Play Console:** don't create any one-time product. In the content rating
  answer **No** to digital purchases, and in Data safety leave out
  *Purchase history*.
- **If merchant registration ever reaches Morocco,** or you publish through a
  company in a supported country, create a one-time product with the ID
  `remove_ads` (Buy option, USD 3.99) and activate it. The game picks it up
  with no update. Its name and description in the 10 languages are in this
  file's git history (the commit before this section changed).

## 6. Pricing and countries

- **Monetise with Play > App pricing: Free.** A free app can never become
  paid later.
- **Production > Countries / regions: Add all.** The game is translated into
  10 languages and plays offline.

## 7. Testing, then production

- **Test and release > Testing > Internal testing**: upload `Aleatro.aab`,
  add yourself as a tester, and install from the opt-in link. That's how to
  test Play Games, the purchase and the ads.
- **New personal developer account?** Google requires a **closed test with at
  least 12 testers who stay opted in for 14 days in a row** before you can
  apply for production. Start it as early as possible, under
  **Testing > Closed testing > Create track**.
- After that, go to **Production > Create new release**, upload the newest
  `.aab`, and send it for review.
- After the first upload, copy the **App signing key certificate SHA-1**
  (**Test and release > App integrity**) into the Play Games credentials.
  See step 1 of `tools/play_games/README.md`.

## Rebuilding the kit

From the project folder:

```sh
# 1. Raw screenshots, one run per language (2560×1440)
for l in en zh_CN ja ko de fr es pt_BR it ar; do
  LANG_SHOT=$l STORE_OUT=/abs/raw xvfb-run -a -s "-screen 0 2600x1500x24" \
    godot --rendering-driver opengl3 --resolution 2560x1440 -s tools/store/capture.gd
done
# 2. Captions over them: the phone set at 1920×1080, the tablet set at 2560×1440
#    FONT_DIR holds the full Noto Sans SC/JP/KR/Arabic fonts
for r in phone:1920x1080 tablet:2560x1440; do
  STORE_RAW=/abs/raw STORE_OUT=/abs/shots STORE_SET=${r%%:*} FONT_DIR=/abs/fonts \
    xvfb-run -a -s "-screen 0 2600x1500x24" godot --rendering-driver opengl3 \
    --resolution ${r#*:} -s tools/store/compose.gd
done
# 3. Text checks, the CSV and the fastlane folders
python3 tools/store/make_listing.py /abs/kit /abs/shots
```

- Captions: `tools/store/captions.json`.
- Listing text: `tools/store/listing/<locale>.txt`. The script checks the
  30/80/4000 limits and flags words Play rejects ("best", "#1", "download
  now" and so on).
