# Few true Android gaps survive verification

The app that people ask for most often and in the most places, and that no one has yet brought to market in a satisfying form, is **a crowdsourced "where is it cheapest" grocery price comparer that shows real shelf prices, not flyer deals**. Shoppers in the US and Germany, and on Hacker News, have asked for it from 2023 to 2026: at least **8 independent requesters across several communities**, with replies such as "I wish! I just want to upload my shopping list and see what store has it cheapest!" ([r/Frugal](https://www.reddit.com/r/Frugal/comments/142ycig/please_tell_me_there_is_an_app_that_takes/)). The demand is the broadest in the study, but the commercial case is weak. Willingness to pay is low, and established deal apps already hold most of the audience. The clearest technical gap of the "exists only on iOS" kind is an **Android walk/don't-walk pedestrian-signal detector for blind users**. Both leading apps, Oko and WalkAssist, are iPhone-only, and blind users have asked for Android versions in writing ([AppleVis](https://www.applevis.com/comment/145382)). Overall, the research found far fewer strong gaps than hoped. Of roughly 80 ideas examined, only about **7 combine a verified Android gap with more than one independent request**. Another 11 are plausible but thin, and the rest are either weak leads or already-served ideas that should not be built. Most niches on Google Play in 2026 are crowded with small, often AI-assisted apps, so a new app will usually win on polish, privacy or price, not on being first. Live Reddit was blocked during this research, so every request count below is a lower bound.

## Methodology and limits: archives, forums and Play search, not live Reddit

Six research tracks covered accessibility and health; education and hobbies; everyday life and family; finance, shopping and travel; social, entertainment and work; and tech and AI. **Live reddit.com was unreachable**: JSON endpoints, old.reddit and web search to Reddit were all refused. Reddit evidence therefore comes from the **Arctic Shift Reddit archive API**. It returns real post and comment text with dates, but its scores are captured early and understate live upvotes. Comment full-text searches for phrases like "wish there was an app" timed out, so the sample is biased toward posts with "app" in the title. Non-Reddit evidence came from Hacker News (Algolia API), AppleVis (the largest blind-user forum), the HearingTracker forum, the F-Droid forum's 895-post "missing apps" megathread, the Privacy Guides forum, Lemmy, NFB articles, and direct Google Play and App Store searches. Existence checks on Google Play mostly used **search-result titles, not opened listings**, so some "lacks the function" claims need a feature check before anyone builds. The Alzheimer's Society forum was behind Cloudflare, and its content is known only from search summaries. This version of the report deliberately leaves out region-specific ideas and evidence.

Two patterns shaped the results. First, idea subreddits such as r/SomebodyMakeThis and r/AppIdeas are now **dominated by developers fishing for ideas**, and several communities actively push back. r/CaregiverSupport bans market research, and one member wrote "Ugh people that try to make money off us are gross" ([r/CaregiverSupport](https://reddit.com/r/CaregiverSupport/comments/1tyq9zz/are_you_using_an_app_to_organize_your_tasks_how/)). r/AgingParents members wrote "There must be four thousand apps that do this exact thing" ([r/AgingParents](https://reddit.com/r/AgingParents/comments/1vr130f/is_there_any_app_in_particular_you_like_for_yours/)). The real signals came from plain "Is there an app that…?" posts in topic communities, from users of apps that died (App in the Air, TV Time), and from Android users who discover that the app they read about is iOS-only. Second, **many 2023–2024 gaps had closed by 2026**: Android Flighty-style trackers, AI notification summaries, Pixel Screenshots clones and fabric-stash apps.

Each idea below is classified as **doesn't exist**, **similar apps lack the function**, **exists but not on Android**, **abandoned**, or **only in expensive platform**. The **market opportunity score (out of 10)** is a judgement that combines the sourced evidence with feasibility for a solo developer. It is an inference, not a measured figure. No idea scored above 6. Ideas are grouped into three tiers. **Strong** means a verified Android gap plus two or more independent people asking. **Plausible** means a real gap with thin or indirect demand, or real demand with an incomplete gap check. **Weak lead** means a single request, a crowded field, or a structural barrier.

## Thirty candidates, honestly tiered

"Requests" counts the independent people seen directly asking, not upvotes. The Android features and monetization lines are design suggestions, built from the notes' assessments.

### Strong tier: verified gap and repeated demand (7)

#### 1. Crowdsourced shelf-price grocery comparer — 3/10 commercially, but the strongest demand in the study

| Field | Detail |
|---|---|
| Concept / what it does | Users photograph receipts or shelf tags. On-device OCR extracts item, price and store into a shared database. The app then shows the cheapest nearby store for each item or a whole shopping list, plus price history. |
| Who wants it, and why | Budget shoppers who cannot tell where an item is cheapest. Existing apps cover weekly deals, not everyday shelf prices, and prices vary from store to store even within one chain. |
| Original requests | "Please tell me there is an app that takes crowdsourced/user created data and helps us compare products between stores and allows for sorting by unit price… Or if someone wants to take that idea and make an app, go for it. If it exists, I must know" ([r/Frugal 2023](https://www.reddit.com/r/Frugal/comments/142ycig/please_tell_me_there_is_an_app_that_takes/)). "Is there an app in Germany that actually compares prices across supermarkets (not just deals)?… The apps I have so far focus on weekly flyers or promotions, not full real-time prices" ([r/germany 2025](https://www.reddit.com/r/germany/comments/1o8y709/is_there_an_app_in_germany_that_actually_compares/)). "is there an app where you can search what costs what at local stores / Supermarkt?" ([r/germany 2024](https://www.reddit.com/r/germany/comments/1hbxnv8/is_there_an_app_where_you_can_search_what_costs/)). |
| More links | [r/povertyfinance](https://www.reddit.com/r/povertyfinance/comments/1i7rxhy/), [r/Frugal 2024](https://www.reddit.com/r/Frugal/comments/1aywc87/), [r/Frugal eggs](https://www.reddit.com/r/Frugal/comments/1067lrx/), [r/Frugal USA item](https://www.reddit.com/r/Frugal/comments/1e6m4fi/), [r/Frugal real-time](https://www.reddit.com/r/Frugal/comments/1igr5iu/), [Ask HN mirror](https://hn.svelte.dev/item/43195604) |
| Independent requests | At least 8, across r/Frugal, r/povertyfinance, r/germany and Ask HN, 2023–2026. This is the most repeated cluster in the whole study. |
| Positive reactions | The 2023 thread scored 60 with 50 comments. Replies included "I wish! I just want to upload my shopping list and see what store has it cheapest!" (+7) and "This is my dream come true and I've thought many times of doing it myself" (+6). |
| Existing alternatives | Flipp (US/CA flyers); Trolley (UK); kaufDA, marktguru, smhaggle and KassenCheck (Germany); Open Prices from Open Food Facts, a crowdsourced, ODbL-licensed database with 125,000+ prices as of August 2025 ([GitHub](https://github.com/openfoodfacts/open-prices)); GrocSnap and Price Book, personal price books that are mostly iOS ([GrocSnap](https://apps.apple.com/app/id6760315590), [Price Book](https://apps.apple.com/us/app/-/id6760607131)). |
| Why they fall short | **Similar apps lack the function.** KaufDA "won't otherwise give you a real-time price for items that aren't on sale", and "I have two Edekas within walking distance and they have different owners and different prices" ([r/germany](https://www.reddit.com/r/germany/comments/1hbxnv8/is_there_an_app_where_you_can_search_what_costs/)). Open Prices is a tool for contributing data, not a consumer "where is it cheapest" app. One German reply was blunt: "It doesn't exist." |
| Potential Android features | ML Kit receipt OCR; a list optimizer that picks the cheapest store; price-history charts; reputation scores for contributors to filter spam; contributing data back to Open Prices to solve cold start; a home-screen widget showing the price of your basket. |
| Monetization | Ads, retailer promotions, B2B price-intelligence data, and a premium list optimizer. Willingness to pay is weak: an r/Frugal commenter asked "Since it's an app for frugal people how would one monetize it?", and the answers were "In app ads" and "sell that data". |
| Complexity | Medium. OCR, a backend and spam filtering are manageable; the cold-start data problem is the hard part. |
| Why the score is low | Incumbents exist for deals, commenters say store-brand prices barely differ, and frugal users resist paying. The idea ranks high on demand and low on revenue. |

#### 2. Android pedestrian-signal detector for blind users — 6/10

| Field | Detail |
|---|---|
| Concept / what it does | The user points the camera at an intersection. An on-device model identifies the walk, don't-walk or countdown phase and reports it with distinct beeps or haptics, ideally with cues for lining up with the crosswalk. |
| Who wants it, and why | Blind and low-vision pedestrians crossing busy streets. It has life-safety value. |
| Original requests | "I know this mainly is an Apple forum, but are you making this app available for androids, all android devices?" (Erick, 24 March 2023, [AppleVis](https://www.applevis.com/comment/145382)). "I would also wish for versions of this app to be developed for other devices such as those running Android and associated derivatives such as BlindShell." ([NFB](https://nfb.org/node/15396)) |
| Independent requests | 2. This is a lower bound, because r/Blind was not reachable. |
| Positive reactions | "Tried this app today to cross a busy intersection where cars travel in excess of 40 mph/70 kph. Amazing!" ([AppleVis](https://www.applevis.com/comment/145382)) |
| Existing alternatives | Oko by AYES ([App Store](https://apps.apple.com/us/app/ayes-oko/id1583614988)) and WalkAssist ([App Store](https://apps.apple.com/us/app/walkassist/id1615852366)) are both iOS-only. Google Lookout's Find mode lists "doors, bathrooms, cups, vehicles", not signals ([Play](https://play.google.com/store/apps/details?id=com.google.android.apps.accessibility.reveal)). The top Play result for "pedestrian signal blind" is a toy ([Play search](https://play.google.com/store/search?q=pedestrian%20signal%20blind&c=apps)). |
| Why they fall short | **Exists but not on Android.** Oko's developer said in 2023: "Currently, only iPhones meet these requirements." Android NPUs in 2025–26 weaken that reason. |
| Potential Android features | A LiteRT/TFLite detector; distinct haptic patterns for each signal phase; a CameraX low-latency pipeline; works offline; TalkBack-first UI; region-specific signal models. |
| Monetization | Freemium or subscription; grants and partnerships with blindness organisations. |
| Complexity | High: model accuracy across regions, plus safety liability. |

#### 3. Cross-media tracker for Android (a "Sequel for Android") — 6/10

| Field | Detail |
|---|---|
| Concept / what it does | One polished diary for films, TV, books, games and concerts, with imports from Letterboxd, Goodreads, Trakt and TV Time, plus stats. |
| Who wants it, and why | People juggling four tracking apps or a decade-old spreadsheet, and people who lost TV Time when it shut down on 15 July 2026 ([TechCrunch](https://techcrunch.com/2026/07/02/popular-tv-tracking-app-tv-time-is-shutting-down-as-company-focuses-on-ai)). |
| Original requests | "my only real problem with Letterboxd is that it's limited to just movies" (OP, who builds a tracker); "I wish there was an app that I could track my tv shows that wasn't sucky. I've tried Trakt and Serialzd" ([r/Letterboxd](https://www.reddit.com/r/Letterboxd/comments/1vz1u8b/do_you_track_other_stuff_eg_tvbooks_as_well_as/)) |
| Independent requests | About 4–5 voices in one thread, plus indirect demand from people migrating off TV Time. |
| Positive reactions | "I have a Google Sheet where I track films, TV, music, books, concerts, video games, and live theater. I've kept it up for a decade now." (+17) |
| Existing alternatives | Sequel is iOS-only ([App Store](https://apps.apple.com/app/sequel/id1630746993)). Loomkeep, Calendia and self-hosted Yamtrack exist; Wecult is web and iPhone only ([AlternativeTo](https://alternativeto.net/software/sequel--media-tracker/?p=2)). |
| Why they fall short | **Exists but not on Android** (the polished leader), and **similar apps lack the function** (Android options are niche and less polished). |
| Potential Android features | TMDB, IGDB and Open Library lookups; CSV/GDPR import parsers; Material You home-screen widgets; year-in-review stats; a private-by-default profile, which responds to the 56-comment thread "When will Letterboxd finally let us have private accounts???" ([r/Letterboxd](https://www.reddit.com/r/Letterboxd/comments/1vrx8pl/when_will_letterboxd_finally_let_us_have_private/)). |
| Monetization | Freemium Pro tier for stats, widgets and themes. Sequel's paid Sequel+ tier shows the category earns money. |
| Complexity | Medium. The APIs are free or cheap; the import parsers and the design quality are what set an app apart. |

#### 4. Two-home belongings ledger for co-parents — 5/10

| Field | Detail |
|---|---|
| Concept / what it does | A photo catalog of each child's clothes and items, tagged with which home bought them and where they are now. It adds a handoff checklist, "outgrown" flags, and a read-only share link the other parent can open without installing anything. |
| Who wants it, and why | Separated parents who keep re-buying clothes that stay at the other house; some court orders require belongings to be returned. |
| Original requests (pain, not explicit app requests) | "I work in IT and love data, so the spreadsheets takes me about 30 seconds, and at least gives us direction on what we need to replace." ([r/coparenting](https://reddit.com/r/coparenting/comments/1ldn4mw/how_to_help_coparent_identify_our_clothes/)). "I started taking pictures of all the clothes we bought (with tags still on)…" ([r/coparenting](https://reddit.com/r/coparenting/comments/1vm2vmf/split_custody_how_do_i_keep_my_kids_clothes_marked/)). "it's in the order to return all belongings to each house" ([r/coparenting](https://reddit.com/r/coparenting/comments/17vll0g/i_was_watching_a_video_about_clothes_and/)) |
| More links | [106-comment thread](https://reddit.com/r/coparenting/comments/182yzto/kids_clothes_keep_staying_at_exs_house_i_have_to/), [54 comments](https://reddit.com/r/coparenting/comments/1r1g9j4/other_parent_wants_their_clothes_back_but_i_have/), [111 comments](https://reddit.com/r/coparenting/comments/1uk11y7/sd_always_sent_to_us_in_toosmall_clothes/), [Mumsnet](https://www.mumsnet.com/talk/teenagers/5127004-kids-clothes-when-5050) |
| Independent requests | More than 40 clothing threads in r/coparenting from 2023 to 2026, several with 100+ comments. None of them explicitly asks for an app. |
| Positive reactions | Mixed. The top replies push back: "trying to keep track of 'my clothes' and 'his clothes' is not worth doing and creates quite a lot of pettiness" (+23). |
| Existing alternatives | OurFamilyWizard, 2houses, AppClose and TalkingParents (calendars, messaging, expenses); KidCloset, which has no concept of two households. |
| Why they fall short | **Similar apps lack the function.** No app tracks items across two homes. |
| Potential Android features | Quick photo capture with size tags; a packing list generated from the custody calendar; a web share link; neutral wording ("packing list", not "proof against your ex"). |
| Monetization | One-time unlock or a small subscription. OurFamilyWizard is already a paid product. |
| Complexity | Low to medium. |

#### 5. "Live Listen" for Android: the phone as a hearing-aid remote microphone — 5/10

| Field | Detail |
|---|---|
| Concept / what it does | The user puts the phone on a restaurant table or lectern, and it streams its microphone with low latency to hearing aids (ASHA, LE Audio or Auracast) or earbuds, with noise reduction. |
| Who wants it, and why | Hearing-aid users who would otherwise buy proprietary external microphones. |
| Original requests | "Android doesn't offer a built-in equivalent"; "Android has no native solution" (a prototype builder); "I'm very interested in using your program for Auracast." ([HearingTracker](https://forum.hearingtracker.com/t/-/102572/3)) |
| Independent requests | About 5 participants in one 2025–26 thread. A related iOS Live Listen thread has 61 replies and 5.2k views ([HearingTracker](https://forum.hearingtracker.com/t/iphone-live-listen-function/75065/40)). |
| Positive reactions | "seems so much more useful and so much cheaper than a proprietary external mic" |
| Existing alternatives | Google Sound Amplifier; "Listening Device: Live Listen" (4.6 stars, 100K+ downloads), whose own listing warns "Bluetooth headphones may introduce sound delay" ([Play](https://play.google.com/store/apps/details?id=com.listeningdevice.hearingaid)); manufacturer apps tied to their own hardware. |
| Why they fall short | **Similar apps lack the function.** Latency is the problem: "the latency was really bad and I gave up"; "there's a substantial delay" on a Pixel 4. |
| Potential Android features | LE Audio/Auracast output; a "table mic" mode; a one-tap mode switch (requested); per-phone latency profiles. |
| Monetization | One-time paid app, positioned against hardware microphones. |
| Complexity | Medium–high: Bluetooth latency and fragmentation across devices. |

#### 6. Photo-assisted knitting gauge counter plus pattern math — 5/10

| Field | Detail |
|---|---|
| Concept / what it does | The user photographs a swatch next to a ruler or printed card. The app overlays an adjustable grid (or uses computer vision later) to compute stitches and rows per 10 cm, then feeds resize and "decrease evenly" calculations. |
| Who wants it, and why | Knitters whose garments came out the wrong size. |
| Original requests | "Istg pls someone tell me there is an app to measure this for me!!! … I made a sweater … and it came out too small" ([r/knitting 2026](https://www.reddit.com/r/knitting/comments/1v4rey4/is_there_an_app_that_will_measure_my_gauge_based/)). "Is there an app that can count stitches and rows per inch? … if you showed it your knitting" ([r/knitting 2025](https://www.reddit.com/r/knitting/comments/1l7odxj/is_there_an_app_that_can_count_stitches_and_rows/)). Related: [numbering charts](https://www.reddit.com/r/knitting/comments/1pgt1e0/app_that_helps_number_charts/) |
| Independent requests | 2 direct requests plus 1 related, 2025–2026. |
| Positive reactions | "I'm always asking for this!" (+4). There is also skepticism: "That's not really a thing an app can calculate without something for scale in the photo." (+45) |
| Existing alternatives | Play gauge calculators (Knitting Gauge Quick, and others) with no camera input; iOS Knittrick ([App Store](https://apps.apple.com/us/app/knittrick/id595151670)); a physical gauge ruler; a manual photo-and-zoom workaround ([blog](https://elizabethsmithknits.com/2025/12/26/gauge-measuring-for-hard-to-see-stitches/)). |
| Why they fall short | **Doesn't exist.** No app advertises photo-based counting, and a Ravelry computer-vision attempt was **abandoned** ("I never heard of it being finished"). |
| Potential Android features | Scale calibration from a reference card; a draggable grid overlay; a pattern resize calculator; an offline, AI-free, ad-free design. |
| Monetization | One-time unlock ($3–6), or bundled into a crafts toolkit. |
| Complexity | Medium for the manual grid; high for automatic counting. |

#### 7. Dementia-friendly auto-answer family video calls on Android tablets — 5/10

| Field | Detail |
|---|---|
| Concept / what it does | A locked-down tablet kiosk. Family calls, it answers automatically, the person needs no buttons or logins, and family administer it remotely. |
| Who wants it, and why | Adult children with a parent in a care home. Staff cannot be relied on to set up calls. |
| Original requests | Thread titles (content seen only through search summaries): "Anyone know an easy device or app for my Mum to make video call in Care home?" ([Alzheimer's Society](https://forum.alzheimers.org.uk/threads/anyone-know-an-easy-device-or-app-for-my-mum-to-make-video-call-in-care-home.98208/)); "Can anyone recommend an easy to use mobile phone app" ([thread 2](https://forum.alzheimers.org.uk/threads/can-anyone-recommend-an-easy-to-use-mobile-phone-app.111207/)); "Simple Android Apps for senior citizens" ([City-Data](https://www.city-data.com/forum/caregiving/3256647-simple-android-apps-senior-citizens.html)) |
| Independent requests | 2–3 thread starters; dates not captured. |
| Positive reactions | Not captured (Cloudflare blocked the forum). |
| Existing alternatives | CallBuddy "works exclusively with iPads and iPhones" ([App Store](https://apps.apple.com/ca/app/callbuddy/id6744102656)); Echo Show; the RAZ Memory phone, which is dedicated hardware ([RAZ](https://www.razmobility.com/solutions/memory-cellphone/)). Play searches returned generic auto-answer apps ([search](https://play.google.com/store/search?q=auto%20answer%20video%20call%20elderly&c=apps)). |
| Why they fall short | **Exists but not on Android** (CallBuddy), or **only in expensive platform** (dedicated hardware). |
| Potential Android features | Device-owner kiosk mode; Jitsi/WebRTC calls that answer automatically from whitelisted contacts; remote admin from a family phone; scheduled call windows. |
| Monetization | Family subscription; licences for care homes. |
| Complexity | Medium. |

### Plausible tier: real gap, thin or indirect demand (11)

#### 8. Drafts-style "capture first, decide later" text inbox with actions — 6/10 on product fit, demand thin

| Field | Detail |
|---|---|
| Concept / what it does | The app opens instantly to a blank page with the keyboard up and dictation built in. Configurable actions then send the text elsewhere: append to a file, Tasker, an HTTP endpoint, the calendar. |
| Who wants it, and why | iPhone users switching to Android who rely on Drafts. |
| Original requests | "there is one app that I can't find anything close to: Drafts. Maybe I'm missing something?" ([HN 2025](https://news.ycombinator.com/item?id=44970658)). Drafts is also listed among Apple apps that "have no equivalents" ([HN 2023](https://news.ycombinator.com/item?id=37552112)). |
| Independent requests | 1–2. |
| Positive reactions | Not visible (HN hides comment votes). |
| Existing alternatives | Drafts is iPhone, iPad, Mac and Watch only ([App Store](https://apps.apple.com/us/app/drafts/id1236254471)). Notesnook and other general note apps ([AlternativeTo](https://alternativeto.net/software/drafts/?p=3)). |
| Why they fall short | **Exists but not on Android.** Android alternatives have no action system. |
| Potential Android features | Quick Settings tile and lock-screen widget; share-sheet target; Tasker/MacroDroid intents; a small JS action engine. |
| Monetization | One-time Pro or a subscription for actions and sync. Drafts Pro users already pay. |
| Complexity | Medium; no restricted APIs are needed. |

#### 9. Bookshop spine scanner that flags your to-read list — 5/10

| Field | Detail |
|---|---|
| Concept / what it does | Point the camera at a shelf in a second-hand bookshop, and books on your Goodreads or StoryGraph to-read list are highlighted. |
| Who wants it, and why | Used-book hunters who cannot keep long to-read lists in their heads. |
| Original requests | "I would love an app that scans book spines in bookshelves, and checks if any books appear in my to-read lists on my reading apps." ([r/SomebodyMakeThis](https://www.reddit.com/r/SomebodyMakeThis/comments/1mvt1j6/bookscanning_app/)). Related: [r/books physical library](https://www.reddit.com/r/books/comments/1s8w4p3/book_managment_app/), [StoryGraph roadmap](https://roadmap.thestorygraph.com/features/posts/barcode-scanning) |
| Independent requests | 1 direct request with about 4 supportive replies; several builders responded. |
| Positive reactions | "I love this idea!! ... it's something I would totally use". A Zapier + ChatGPT workaround "still missed around 20% of the books". |
| Existing alternatives | iOS has Shelf Scan ([App Store](https://apps.apple.com/us/app/id6754824642)) and Spines ([App Store](https://apps.apple.com/app/spines/id6757425414)). Android has Book Mind ([Play](https://play.google.com/store/apps/details?id=com.bookmind)) and Shelfd, which scans ISBNs only ([Play](https://play.google.com/store/apps/details?id=com.shelfd.app)). |
| Why they fall short | **Exists but not on Android** for the to-read matching. Android scanners lack that function. |
| Potential Android features | ML Kit OCR on many spines at once; fuzzy title and author matching; Goodreads/StoryGraph CSV import; offline matching. |
| Monetization | One-time Pro plus affiliate links. |
| Complexity | Medium; OCR accuracy on spines decides success. |

#### 10. Swipe-to-discover books for Android — 5/10

| Field | Detail |
|---|---|
| Concept / what it does | Swipe left or right on back-cover blurbs to train a recommendation model. |
| Who wants it, and why | Readers who find book recommendations "way behind other mediums". |
| Original requests | "Is there such thing as an Android app where you can read the back cover summaries of books? Like I'd swipe left or right … and it'll recommend me more books like that?" ([r/suggestmeabook, 122 upvotes](https://www.reddit.com/r/suggestmeabook/comments/1el2hu6/is_there_tinder_for_books/)) |
| Independent requests | 1 post with about 6 supportive top comments. |
| Positive reactions | "I've never heard of anything like this but it sounds like such a good idea!" (+107); "the recommendation software for books feels way behind other mediums like movies and music." (+91); "Omg take my money" (+5) |
| Existing alternatives | iOS: SwipeLit ([App Store](https://apps.apple.com/ca/app/swipelit/id6758277908)), Bookovery ([App Store](https://apps.apple.com/us/app/-/id6740712207)), Bookist ([App Store](https://apps.apple.com/dk/app/bookist/id6469034196)), Blind Date With A Book ([App Store](https://apps.apple.com/us/app/-/id6760789070)). Fable's claimed swipe feature was not verified. |
| Why they fall short | **Exists but not on Android.** The Play Store has not been checked directly. |
| Potential Android features | Open Library/Google Books metadata; page count, genre and awards on each card (requested); Libby deep links. |
| Monetization | Affiliate links; premium filters. |
| Complexity | Low–medium. |

#### 11. Android pet bloodwork and lab-value trend tracker — 5/10

| Field | Detail |
|---|---|
| Concept / what it does | Photograph vet lab results; OCR charts creatinine, SDMA and other values over time against reference ranges. |
| Who wants it, and why | Owners of pets with chronic conditions (cats with kidney disease, dogs with heart murmurs). |
| Original requests | "Need an App or Tool to Help Track/Analyze the Jumble of Vet Results!" ([r/cats](https://reddit.com/r/cats/comments/1ot5o08/need_an_app_or_tool_to_help_trackanalyze_the/)); "App to track cat weight by age and sex?... Does this exist?" ([r/cats](https://reddit.com/r/cats/comments/1qa41x1/app_to_track_cat_weight_by_age_and_sex/)); related: [respiration logging](https://reddit.com/r/Pets/comments/1sfhdm9/vet_app/), [chronic UTIs](https://reddit.com/r/cats/comments/1ryk3g2/dealing_with_a_cat_with_chronic_frequent_utis/) |
| Independent requests | 1–2 direct requests, plus 2 related. |
| Positive reactions | The main request scored 7. |
| Existing alternatives | iOS only: Pawtient AI ([App Store](https://apps.apple.com/app/id6756168872)), CKDKitty ([App Store](https://apps.apple.com/sl/app/ckdkitty/id6758018530)), TendTail ([App Store](https://apps.apple.com/app/id6776025573)); a web tool ([PetHealthLog](https://pethealthlog.pages.dev/cat-senior-bloodwork-tracker)). Android has only generic pet health apps. |
| Why they fall short | **Exists but not on Android**. This is unconfirmed until Play listings are opened. |
| Potential Android features | OCR of lab PDFs and photos; unit normalisation; trend charts to share with the vet; medication and weight logs. |
| Monetization | Freemium plus a subscription; an iOS pet app charges $4.99/month ([GoodDays](https://apps.apple.com/us/app/id6761143846)). |
| Complexity | Medium. |

#### 12. Quilt and EPP layout planner using photos of your own blocks — 4/10

| Field | Detail |
|---|---|
| Concept / what it does | Photograph finished blocks, drop them onto square or hexagon grids, drag and swap them to test arrangements, and get piece counts and yardage. |
| Who wants it, and why | Quilters who balk at EQ8's $239 price. |
| Original requests | "very big wall quilt from 2-inch EPP hexagons. There are close to 400 … Is there any app that would help…" ([r/quilting](https://www.reddit.com/r/quilting/comments/1phj5la/app_for_planning_epp_layouts/)); "upload photos of quilt blocks and then arrange them … like a jigsaw puzzle" ([r/quilting](https://www.reddit.com/r/quilting/comments/13iuhhe/programapp_to_arrange_quilt_squares/)); more: [2024-07](https://www.reddit.com/r/quilting/comments/1e2ixh8/quilting_app_or_program_info/), [2025-01](https://www.reddit.com/r/quilting/comments/1iag4lr/looking_for_a_design_app_that_can_help_me_figure/), [2024-11](https://www.reddit.com/r/quilting/comments/1h29yn9/is_there_an_app_for_that/), [2024-10](https://www.reddit.com/r/quilting/comments/1g2bd8l/is_there_an_app_or_program_to_help_me_design_an/), [crochet](https://www.reddit.com/r/crochet/comments/1q01ed7/looking_for_app_that_i_can_designexperiment_with/) |
| Independent requests | 6 in r/quilting plus 1 in r/crochet, 2023–2025. |
| Positive reactions | "OMG I've been looking everywhere for something like this, THANK YOU!!" (in reply to a web tool built in the thread) |
| Existing alternatives | Quiltography ($14.99, iPad-only) ([App Store](https://apps.apple.com/us/app/quiltography-quilt-design-made-simple/id585991997)); EQ8 ($239, desktop); on Play, Quilteya, Quilt Builder, Quiltsmith, QuiltPlan, FPP Studio. |
| Why they fall short | **Only in expensive platform** for the full feature set, and **similar apps lack the function** on Android: photo-block drag/swap on a hexagon grid is unconfirmed. "EQ8 let's you design hexy quilts, but you cant 'slide' them around." |
| Potential Android features | Photo crop to block; hex, diamond and square grids; shuffle and ombré auto-arrange; yardage math. |
| Monetization | One-time purchase, $5–15. |
| Complexity | Medium. |

#### 13. Practise piano from your own PDF or photographed sheet music — 4/10

| Field | Detail |
|---|---|
| Concept / what it does | Import your own sheet music; the app plays it back, offers a wait mode, and gives rhythm feedback. |
| Who wants it, and why | Learners bored by fixed catalogues; parents of children who practise. |
| Original requests | "Any app/website with PDF upload and interactive player? … most of the songs in Simply Piano are songs I've never heard" ([r/piano](https://www.reddit.com/r/piano/comments/1ub9rnz/any_appwebsite_with_pdf_upload_and_interactive/)); "Is there any app where you upload your sheets and get a listenable version" ([r/piano](https://www.reddit.com/r/piano/comments/1u5mjca/is_there_any_app_where_you_upload_your_sheets_and/)); a rhythm-listening request ([r/piano](https://www.reddit.com/r/piano/comments/1vkx8af/is_there_an_app_that_can_actually_listen_to_you/)); a transcription request ([r/piano](https://www.reddit.com/r/piano/comments/1u0u6w4/is_there_any_app_that_can_transcribe_pieces/)) |
| Independent requests | 4 in 2026. |
| Positive reactions | "Did you ever find out if there's a site that does this? I'm looking for one too." Willingness to pay: "do not mind paying a subscription" ([r/piano](https://www.reddit.com/r/piano/comments/1v7tbxe/sheet_music_is_there_an_app_for_that/)). |
| Existing alternatives | Simply Piano, Flowkey and Artie (own catalogues only); an iOS TestFlight beta. MuseScore, PlayScore 2 and Newzik were not re-verified. |
| Why they fall short | **Similar apps lack the function**; a beta **exists but not on Android**. |
| Potential Android features | OMR import; MIDI keyboard input; acoustic onset detection; a loop-a-bar mode. |
| Monetization | Subscription. |
| Complexity | High (OMR plus acoustic pitch detection); funded competitors are converging on this. |

#### 14. Remote tamper lock for an elderly parent's Android phone — 4/10

| Field | Detail |
|---|---|
| Concept / what it does | A caregiver remotely pins brightness, volume and ringer settings, blocks accidental changes, and fixes the phone from afar. |
| Who wants it, and why | Adult children of parents with dementia or disability. |
| Original requests | "maybe an app that blocks it so that even if he misclicks he cannot change the brightness" ([r/CaregiverSupport](https://reddit.com/r/CaregiverSupport/comments/1sgm47h/smartphone_app_to_block_brightness_changes/)); "The whole slide to answer etc. is not working any more" ([r/TechForAgingParents](https://reddit.com/r/TechForAgingParents/comments/1x94ll1/cell_phone_answeringmaking_calls_android/)); [adware on a Lifeline phone](https://reddit.com/r/TechForAgingParents/comments/1uys0bf/beyond_frustrated_with_my_aunts_phone/) |
| Independent requests | About 3, plus one developer research post. |
| Positive reactions | Not captured. |
| Existing alternatives | 15+ senior launchers (BIG Launcher, Senior Launcher, Juno and others); Samsung's "Press Volume up to answer calls" setting. |
| Why they fall short | **Similar apps lack the function**, probably. Remote configuration and brightness locks were not verified in the launchers. |
| Potential Android features | Device-owner policy enforcement; a remote config dashboard; an auto-answer setting; adware detection. |
| Monetization | Subscription per managed parent. Caregivers are price-sensitive: "I'd pay $10 month max. Only if it is excellent" ([r/AgingParents](https://reddit.com/r/AgingParents/comments/1ofqnzp/unsure_if_i_should_pay_for_an_app_that_helps_me/)). |
| Complexity | Medium–high (differences between phone makers). |

#### 15. Point-at-the-appliance panel reader — 4/10

| Field | Detail |
|---|---|
| Concept / what it does | The user points a finger at a microwave, thermostat or kiosk, and the app reads the label under the fingertip. |
| Who wants it, and why | Blind users facing touch panels. |
| Original requests | "IOS has vizLens, android does not have any equivalent to this app at all." ([AppleVis](https://www.applevis.com/comment/147994)) |
| Independent requests | 1 (2023). |
| Positive reactions | Not captured. |
| Existing alternatives | iOS Magnifier Point and Speak ([Apple](https://support.apple.com/en-mn/guide/iphone/iph32deb9296/ios)); Lookout, Envision and Be My Eyes read text in general ([Play search](https://play.google.com/store/search?q=read%20appliance%20buttons%20blind&c=apps)). |
| Why they fall short | **Exists but not on Android.** |
| Potential Android features | MediaPipe hand tracking plus ML Kit OCR on the region under the fingertip; spoken feedback; offline. |
| Monetization | Freemium. |
| Complexity | High. |

#### 16. Fully offline system-wide "writing tools" for any phone — 4/10

| Field | Detail |
|---|---|
| Concept / what it does | Select text in any app and choose Rewrite, Proofread or Summarize, using an on-device model with no API key. |
| Who wants it, and why | Owners of phones that are not Pixels or Samsungs and envy Apple Intelligence or Galaxy AI. No direct request was found. |
| Original requests | None found (Reddit was blocked). Adjacent interest: [XDA](https://www.xda-developers.com/i-replaced-grammarly-premium-with-a-local-model-on-my-gpu-and-my-drafts-never-leave-my-pc/). |
| Independent requests | 0 direct. |
| Positive reactions | n/a |
| Existing alternatives | Local Writer ([GitHub](https://github.com/aniketsaurav18/local-writer-android)); SwiftSlate ([F-Droid](https://fdroid.gitlab.io/jekyll-fdroid/packages/com.musheer360.swiftslate/)); LLM Hub ([GitHub](https://github.com/timmyy123/LLM-Hub)). |
| Why they fall short | **Similar apps lack the function**: they are early, hobbyist and hard to set up. The gap is polish, not existence. |
| Potential Android features | PROCESS_TEXT intent; llama.cpp or LiteRT models of 1–3B parameters; downloadable model packs. |
| Monetization | One-time Pro. |
| Complexity | Medium. |

#### 17. Per-app notification sound manager with export/import — 4/10

| Field | Detail |
|---|---|
| Concept / what it does | Assign a distinct sound to each app, back up the whole set, and restore it on a new phone. |
| Who wants it, and why | Power users who lose their custom sounds on every new phone. |
| Original requests | "I really wish there was an app that could manage all that, including exporting/importing everything configured" ([HN](https://news.ycombinator.com/item?id=44462783)) |
| Independent requests | 1, plus related restore-bug reports ([Samsung](https://eu.community.samsung.com/t5/galaxy-s21-series/oneui-individual-notification-sounds-for-apps-problems/m-p/3941867), [/e/OS commit](https://gitlab.e.foundation/e/os/android_frameworks_base/-/commit/0058221f041db2fd37e9c82fd80b5937fa4f3f3a)). |
| Positive reactions | n/a |
| Existing alternatives | Unverified; Play was not searched. |
| Why they fall short | **Similar apps lack the function**: Android forbids third-party apps from changing another app's channel settings ([HN](https://news.ycombinator.com/item?id=44472226)). |
| Potential Android features | A NotificationListenerService that plays its own sound per app while the original channel is silenced; JSON export. |
| Monetization | Small one-time unlock. |
| Complexity | Low–medium, though the approach is hacky (latency, phone makers killing background apps). |

#### 18. Photo-proof "did I lock it?" reassurance checklist — 4/10

| Field | Detail |
|---|---|
| Concept / what it does | Take a timestamped photo of the locked door or the switched-off stove, then check it later instead of going back home. |
| Who wants it, and why | People with ADHD or OCD-style checking. |
| Original requests | None found directly. Demand is inferred from at least five iOS apps: Pruvd ([App Store](https://apps.apple.com/app/id6757632735)), Did I Do? ([App Store](https://apps.apple.com/app/id6737065031)), Certain ([App Store](https://apps.apple.com/us/app/-/id6757313797)), Reassure Me ([App Store](https://apps.apple.com/us/app/id6756675829)), Did I ([Product Hunt](https://www.producthunt.com/products/did-i)). |
| Independent requests | 0 direct. |
| Positive reactions | n/a |
| Existing alternatives | On Android: Stay Calm: OCD Checklist, OCD Relief, Check Off. Their photo-proof features were not verified. |
| Why they fall short | **Exists but not on Android**, unverified. |
| Potential Android features | A lock-screen widget; geofenced "leaving home" prompt; photos that expire automatically. |
| Monetization | One-time purchase. |
| Complexity | Low. Clinicians may consider reassurance tools a way of feeding compulsions (not sourced; check before building). |

### Weak leads: single requests, crowded fields or structural barriers (12)

#### 19. Reader for language learners that opens your own EPUBs — 3/10
**Concept:** open your own EPUB, tap a word to translate it, and send saved words to spaced repetition. **Who/why:** long-time ReadEra users learning a language. **Request:** "Is there an app where I can read books and practice new vocabulary in the same app? … books that I have chosen to read" (17 points, 20 comments, [r/languagelearning](https://www.reddit.com/r/languagelearning/comments/1xe6h36/is_there_an_app_where_i_can_read_books_and/)). **Requests:** 1. **Reactions:** LingQ and Readlang suggestions (+13 each); "bought a lifetime subscription … worth it" (Linga). **Alternatives:** Linga, BookLight, Book Translator, Duoreader on Play; LingQ. **Shortfall:** **similar apps lack the function** only marginally; the function exists. **Android features:** EPUB/PDF rendering, offline dictionaries, AnkiDroid export. **Monetization:** lifetime unlock. **Complexity:** medium.

#### 20. Tenuto-style music theory recall drills for Android — 3/10
**Concept:** flashcard quizzes such as "what are the notes in a Dbmin7 chord". **Requests:** "I'm looking to be quizzed on my memory … Flashcard style at minimum" ([r/musictheory](https://www.reddit.com/r/musictheory/comments/1vl2u7j/quizz_app_for_memorizing_theory/)); "Is it iOS only?" and "I have an android phone" ([r/musictheory](https://www.reddit.com/r/musictheory/comments/1ue40ut/app_for_drilling_chords/)). **Requests:** 2. **Reactions:** "Android version? :)". **Alternatives:** Tenuto is iOS-only ([App Store](https://apps.apple.com/us/app/tenuto/id459313476)); Play has Music Theory Companion, ChordIQ, Complete Ear Trainer. **Shortfall:** **exists but not on Android** for Tenuto itself, but substitutes exist. **Android features:** custom drill sets, MIDI input. **Monetization:** one-time. **Complexity:** low.

#### 21. Cheap knitting PDF pattern companion (line marker plus counters) — 3/10
**Concept:** a PDF viewer that remembers your exact row and repeat count. **Requests:** [r/SomebodyMakeThis](https://www.reddit.com/r/SomebodyMakeThis/comments/1x0o3dx/a_knitting_pdf_viewer_that_saves_your_exact_row/); "LooseLoop … SO convenient.. but … requires a subscription which is like 30 bucks a year" ([r/knitting](https://www.reddit.com/r/knitting/comments/1vs97ah/an_app_to_use_as_a_pattern_guide/)); [r/crochet, 91 comments](https://www.reddit.com/r/crochet/comments/1u3bjar/do_you_print_out_your_patterns_or_use_an_app/). **Requests:** 2–3. **Alternatives:** knitCompanion, My Row Counter ([App Store](https://apps.apple.com/app/id1342608792)), Rowkeep. **Shortfall:** **only in expensive platform**, in the sense that price is the complaint. **Angle:** bundle with #6 as a one-time, AI-free crafts toolkit. **Complexity:** low.

#### 22. Password helper for elderly parents, managed by their adult children — 3/10
**Concept:** big "tap to copy" tiles on the parent's phone, managed remotely by the child. **Request:** "An app where adult kids manage their elderly parents' passwords... Every tool I've found assumes the person using it is tech-savvy enough to understand what a 'vault' is" (45 points, 44 comments, [r/SomebodyMakeThis](https://reddit.com/r/SomebodyMakeThis/comments/1vit5w3/an_app_where_adult_kids_manage_their_elderly/)). **Reactions:** "I'm not aware of a specific app designed with this in mind" (+7). **Alternatives:** 1Password, Bitwarden and others with family vaults: "I do this currently with my elderly father, my siblings, and 1Password. It works great" (+3). **Shortfall:** **similar apps lack the function** on the parent-side interface. **Barrier:** trust and security liability. **Complexity:** high.

#### 23. TalkBack-first dictionary and RSS reader — 3/10
**Request:** "No third-party commercial dictionary is fully accessible/navigable on Android … and the same is true about RSS read[ers]" ([AppleVis](https://www.applevis.com/forum/android/what-i-miss-most-about-ios-why-i-m-still-not-going-back?page=1)). **Requests:** 1. **Shortfall:** **similar apps lack the function** (accessibility). **Barrier:** licensing dictionary content. **Monetization:** paid app. **Complexity:** low–medium.

#### 24. Colour-plus-pattern clothing identifier for blind users — 3/10
**Request:** an iOS "clothes color" app that also names patterns is "a huge ... game changer"; on Android, "only a few of them are well-maintained" ([AppleVis](https://www.applevis.com/forum/android/what-i-miss-most-about-ios-why-i-m-still-not-going-back?page=1)). **Requests:** 1. **Shortfall:** **similar apps lack the function**. **Android features:** on-device pattern classifier (stripes, checks, florals). **Complexity:** medium.

#### 25. Activity-pay and miles tracker for truck drivers — 3/10
**Request:** "I want something that will easily track my miles and activity pay." (+3); another driver uses "a spreadhseet. Just not intuitive enough." ([r/Truckers](https://www.reddit.com/r/Truckers/comments/1lj0i7d/trucker_app/)). **Requests:** 2–3, in a thread started by a developer. **Alternatives:** MileIQ, Trucker Path (they track mileage, not pay reconciliation). **Shortfall:** **similar apps lack the function**. **Caveat:** the community is hostile to app pitches ([r/Truckers](https://www.reddit.com/r/Truckers/comments/1uextig/phone_apps/)). **Complexity:** low.

#### 26. Daily resurfacing of your own book notes and quotes — 3/10
**Request:** "I'm looking for an app that I could put book notes into that would then cycle them back to me daily." (14 upvotes, [r/books](https://www.reddit.com/r/books/comments/1gnbuw4/is_there_an_app_for_this/)). **Alternatives:** Readwise, whose daily review appears to be paid ([AlternativeTo](https://alternativeto.net/software/readwise/)); AnkiDroid as a workaround. **Shortfall:** **only in expensive platform**. **Complexity:** low.

#### 27. Cheap job-photo organizer for solo tradespeople — 3/10
**Request:** "my camera rolls is at some 12,000+ photos. Does anyone use an app that say you can make a folder and call it this and that job?" ([r/electricians](https://www.reddit.com/r/electricians/comments/1k4c7m6/do_anyone_of_you_use_a_good_photo_app_for_job_sites/)). **Requests:** 1. **Alternatives:** CompanyCam (expensive, [App Store](https://apps.apple.com/us/app/id960043499)); Timemark, RelayCam, WorkPhotos (vendor comparison pages, [Timemark](https://www.timemark.com/compare/best-companycam-alternative)). **Shortfall:** **only in expensive platform** for the leader, but cheap options exist. **Complexity:** medium (offline-first sync).

#### 28. Matching people by Letterboxd taste — 3/10
**Request:** "is there an app or website when you log your letterboxd and it search for ppl with similar taste based on top4?" (12 upvotes, [r/Letterboxd](https://www.reddit.com/r/Letterboxd/comments/1ssfesv/is_there_an_app_or_website_when_you_log_your/)). **Alternatives:** the "Letterboxd besties" web tool (+15) and Criticker; a tester "had to go down to 2/4 matches and still only got four results". **Shortfall:** **similar apps lack the function** (web-only and thin). **Barrier:** Letterboxd has no open public API. **Complexity:** medium.

#### 29. Multi-BNPL installment tracker (Klarna, Affirm, Afterpay, PayPal Pay in 4, Sezzle) — 3/10
**Concept:** one calendar of every buy-now-pay-later plan, showing due dates and the total owed, so that several payments landing at once are not a surprise. **Evidence:** "For people who use multiple BNPL services (Klarna, Affirm, Afterpay, PayPal Pay in 4, Sezzle, etc.): how do you keep track of everything?" ([r/povertyfinance](https://www.reddit.com/r/povertyfinance/comments/1vc9bna/for_people_who_use_multiple_bnpl_services_klarna/)). This post is builder research, and commenters flag such posts as spam. The pain also shows in "When all of your Klarna payments come out at once." (29 comments, [r/povertyfinance](https://www.reddit.com/r/povertyfinance/comments/1k30uia/)). **Requests:** few direct ones. **Reactions:** the top answer is "I use a free application called GOOGLE SHEETS" (+5). **Alternatives:** PayStreak is iPhone only ([App Store](https://apps.apple.com/us/app/-/id6751249424)); Finny ([guide](https://getfinny.app/blog/track-klarna-afterpay-affirm-payments)); spreadsheets and bill trackers. **Shortfall:** **exists but not on Android** for the one dedicated option. **Android features:** manual plan entry with reminders, a widget showing the next payment, and optional parsing of notifications (Play restricts READ_SMS). **Monetization:** one-time unlock; demand is weak. **Complexity:** low–medium.

#### 30. Hotel booking price-drop monitor — 3/10
**Concept:** watch a hotel you have already booked and alert you to rebook if the price falls. **Request:** "select chosen hotels – track their prices – receive a notification whenever the price of one drops" ([r/travel](https://www.reddit.com/r/travel/comments/1i00kyf/is_there_an_app_that_would_capture_falling_hotel/)). Related requests: [airfare price drops](https://www.reddit.com/r/travel/comments/1bi2sjz/), [room availability alerts](https://www.reddit.com/r/travel/comments/1814smh/), ["like Pruvo but for cruises"](https://www.reddit.com/r/travel/comments/1bjtx6s/). **Requests:** 3–4, 2023–2025, all with low engagement. **Alternatives:** Pruvo, WakePackGo and watchmybooking.com, all named in the thread (mostly web or email; a native Android app was not verified). **Shortfall:** **similar apps lack the function** on Android, unverified. **Caveat:** an expert reply said hotel "prices Almost always go up up up". **Complexity:** high, because it means scraping booking sites against their terms and anti-bot defences.

## Top ten ranked for a solo Android developer

The ranking weighs demand strength, the number of independent requests, evidence that people cannot find the app, lack of alternatives, audience size, commercial potential, and whether one developer can build it. Breadth of repeated demand counts most, because that is what the question asks about. This is why the grocery comparer ranks first despite its low commercial score.

| Rank | Idea | Tier | Requests | Gap class | Score | Solo-dev feasibility |
|---|---|---|---|---|---|---|
| 1 | Crowdsourced shelf-price grocery comparer | Strong | 8+ across 4 communities | Similar apps lack the function | 3 (commercial) | Medium |
| 2 | Pedestrian-signal detector | Strong | 2 | Exists but not on Android | 6 | Hard |
| 3 | Cross-media tracker | Strong | 4–5 plus TV Time migrants | Exists but not on Android | 6 | Medium |
| 4 | Co-parent two-home ledger | Strong | 40+ pain threads | Similar apps lack the function | 5 | Easy |
| 5 | Live Listen remote mic | Strong | ~5 | Similar apps lack the function | 5 | Hard |
| 6 | Knitting gauge photo plus pattern math | Strong | 2–3 | Doesn't exist / abandoned | 5 | Medium |
| 7 | Dementia auto-answer video kiosk | Strong | 2–3 | Exists but not on Android | 5 | Medium |
| 8 | Drafts-style capture inbox | Plausible | 1–2 | Exists but not on Android | 6 | Medium |
| 9 | TBR spine scanner | Plausible | 1 plus replies | Exists but not on Android | 5 | Medium |
| 10 | Swipe-to-discover books | Plausible | 1 viral post plus ~6 comments | Exists but not on Android | 5 | Easy–medium |

**1. Crowdsourced shelf-price grocery comparer.** Build it because it is the **only request cluster repeated across independent communities and countries for four years**: r/Frugal, r/povertyfinance, r/germany and Ask HN. In every case, users say current apps show deals rather than shelf prices. Open Prices gives an open database and licence to bootstrap from ([GitHub](https://github.com/openfoodfacts/open-prices)). Building it as a friendly consumer front end that also feeds data back to Open Prices is the most credible way past cold start. The risks are serious: a cold-start data problem, fake price entries, weak willingness to pay, and commenters who say store-brand prices barely differ. Revenue will come from ads, retailer promotions or B2B data, not subscriptions. A solo developer should start with one city.

**2. Pedestrian-signal detector.** Build it because it is the **cleanest "exists but not on Android" gap** in the study. Two leading iOS apps, a written refusal from the developer ("only iPhones meet these requirements"), and a Play search that returns a toy all point the same way ([AppleVis](https://www.applevis.com/comment/145382)). The value is life-safety, and blindness organisations fund this kind of tool. The model accuracy and liability burden are heavy for one person.

**3. Cross-media tracker.** Build it because the **TV Time shutdown displaced a large audience in July 2026**, and the best all-in-one tracker, Sequel, is iPhone-only ([App Store](https://apps.apple.com/app/sequel/id1630746993)). People are using decade-old spreadsheets instead (+17). The APIs are free, and the category already sells paid tiers. To stand out, build excellent import parsers and Android widgets. Of all ten, this has the best mix of demand, commercial potential and feasibility.

**4. Co-parent two-home ledger.** Build it because the pain is **large, recurring and has no direct competitor**: 40+ threads, several with 100+ comments, and parents who already keep spreadsheets ([r/coparenting](https://reddit.com/r/coparenting/comments/1ldn4mw/how_to_help_coparent_identify_our_clothes/)). It is easy to build and the co-parenting audience already pays for apps like OurFamilyWizard. Frame it as a packing list, not as evidence against an ex, because the top-voted advice warns against pettiness.

**5. Live Listen remote mic.** Build it because hearing-aid users have **already started their own prototypes** out of frustration, and they compare the cost against proprietary microphones, not against free apps ([HearingTracker](https://forum.hearingtracker.com/t/-/102572/3)). Ship for Pixel and LE Audio phones first.

**6. Knitting gauge photo grid plus pattern math.** Build it because it is the **only idea in the study classed as "doesn't exist"**, and an earlier attempt was abandoned. It ties to a tangible failure (a sweater that came out too small), and it fits a one-time, AI-free crafts bundle together with #21 and the hexagon planner (#12).

**7. Dementia auto-answer video kiosk.** Build it because the buyer, an adult child, is clear and already pays for hardware such as Echo Show or Komp. The one dedicated app is iOS-only ([CallBuddy](https://apps.apple.com/ca/app/callbuddy/id6744102656)). Licences for care homes offer a business-to-business route.

**8. Drafts-style capture inbox.** Build it because the **product is proven** (Drafts users pay for Pro) and Android has nothing with an action system ([App Store](https://apps.apple.com/us/app/drafts/id1236254471)). It needs no restricted APIs. The demand evidence is thin (1–2 requests), so validate it before committing.

**9. TBR spine scanner.** Build it because the to-read matching function is **verified missing on Android** while two iOS apps prove the concept ([Shelf Scan](https://apps.apple.com/us/app/id6754824642)). On-device OCR makes it a project of a few weeks to a month.

**10. Swipe-to-discover books.** Build it because a single explicitly Android request drew **the strongest reaction counts of any post in the study** (+107 for "such a good idea", +91 for "recommendation software for books feels way behind"), and at least four iOS apps show the appetite for it ([r/suggestmeabook](https://www.reddit.com/r/suggestmeabook/comments/1el2hu6/is_there_tinder_for_books/)). Check the Play Store directly before building, and confirm whether Fable already offers swipe discovery. The pet bloodwork tracker (#11) narrowly missed this spot: its audience is highly motivated, but it has only 1–2 direct requests.

## Rejected because they already exist on Android

These ideas showed real demand but are already served, so **do not build them as "missing apps"**. **Android flight tracker or logbook** (Flighty-style): Aviate launched in July 2026 ([9to5Google](https://9to5google.com/2026/07/27/aviate-androids-answer-to-flighty-is-now-available-to-download/)), and Wayflight and byAir exist. **Soundscape-style audio navigation**: an Android open beta launched in August 2025 ([STA](https://scottish-tech-army.github.io/Soundscape-Android/newsletters/19-Aug-2025.html)). **Door and object detection**: Lookout's Find mode ([Play](https://play.google.com/store/apps/details?id=com.google.android.apps.accessibility.reveal)). **AAC for non-speaking users**: Avaz, Otsimo and many others ([Play search](https://play.google.com/store/search?q=AAC%20symbols&c=apps)). **Offline POTS and chronic-illness trackers** ([Lunaire](https://play.google.com/store/apps/details?id=uk.lunaire.pots&hl=en_US)) and **ME/CFS pacing** ([Play search](https://play.google.com/store/search?q=ME%2FCFS%20pacing%20heart%20rate&c=apps)). **Offline voice typing** (FUTO Voice, [Privacy Guides](https://discuss.privacyguides.net/t/transcription-tools-that-run-locally/19271/4)) and **offline translation** ([Privacy Guides](https://discuss.privacyguides.net/t/offline-translator-for-android/36095/1)). **Pixel Screenshots clones** (PixelShot, Shots Studio, [Beebom](https://beebom.com/pixelshot-app-brings-pixel-screenshots-any-android-phone/)) and **AI notification summaries** (NotifAI, [Play](https://play.google.com/store/apps/details?id=com.androidexpert35.notifai&hl=en)). **Voice banking**: Voice Back runs on Android ([Voice Back](https://voicebackapp.com/voice-banking)). **Budgeting from bank notifications**: NotifSync and QuickCatch bridge Android notifications to YNAB ([r/ynab](https://www.reddit.com/r/ynab/comments/1x5uv03/none_of_my_banks_connect_to_ynab_so_i_taught_my/)).

Hobby and household rejects: **fabric and yarn stash inventory**, where Play has 15 results despite Cora being iOS-only ([r/quilting](https://www.reddit.com/r/quilting/comments/1e4dad3/fabric_tracking_app/)); **private bird life lists**; **solo MTG against an AI** (Forge runs on Android, [r/mtg](https://www.reddit.com/r/mtg/comments/1xi4axr/is_there_an_app_where_you_can_play_mtg_on_your/)); the **"where did I put it" item finder** (Gemini in Find Hub, [Android Central](https://www.androidcentral.com/apps-software/no-tracker-tag-gemini-can-now-store-item-locations-right-in-find-hub)); **chronic-lateness "leave now" alerts** (Time to Leave, [AlternativeTo](https://alternativeto.net/software/time-to-leave/about)); **pet end-of-life quality-of-life trackers**; **"who fed the pet" logs** ([DogLog](https://play.google.com/store/apps/details?id=com.mobikode.dog)); **kids' clothing size trackers**; **remote medication reminders** (Medisafe, MyTherapy); **home inventory and warranty logs**. Social and work rejects: **adult friend-finding**, where the problem is social, not technical ("people would still use it as a hookup app", +101, [r/CasualConversation](https://www.reddit.com/r/CasualConversation/comments/1tzszdl/why_is_there_no_perfect_app_for_finding_friends/)); **Discogs companions** ([CrateLog](https://play.google.com/store/apps/details?id=app.cratelog)); **concert alerts** (Bandsintown, Songkick); **start-player pickers** (Chwazi relaunched, [r/boardgames](https://www.reddit.com/r/boardgames/comments/1ts7qge/chwazi_is_back_and_i_owe_you_all_an_open_letter/)); **Letterboxd for books** (StoryGraph, Hardcover); **nurse shift calendars**; **TV episode reaction feeds**, now covered by Bingers ([TechCrunch](https://techcrunch.com/2026/08/04/tv-time-co-founder-launches-bingers-to-revive-the-beloved-tv-tracking-app/)). Shopping rejects: **cross-unit price calculators** ("'Compare' for iOS", and shelf tags already show unit prices in many countries, [r/Frugal](https://www.reddit.com/r/Frugal/comments/1hqtkol/is_there_an_iphone_app_that_converts_units_of/)) and **sale and price-drop alerts** (Flipp, Keepa, CamelCamelCamel, [r/Frugal](https://www.reddit.com/r/Frugal/comments/1sjr4vw/is_there_an_app_that_tells_you_when_specific/)).

## Conclusion

The direct answer to "what Android app are people repeatedly asking someone to create, that they would genuinely use, but nobody has successfully brought to market yet?" is **a crowdsourced shelf-price comparison app that tells you which nearby store sells your shopping list cheapest**. Four years of requests across independent communities in the US and Germany, and on Hacker News, show people want it. Every existing tool stops at weekly flyers, a single chain, or a contributor database. Its weakness is money, not demand: frugal users will not pay, so it works only with ads, retailer promotions or B2B data and an open-data cold start. For someone who wants the best overall bet rather than the most-requested idea, the **cross-media tracker for Android** has the best balance of real demand, a proven paying category, and solo-developer feasibility. The **pedestrian-signal detector** is the strongest "exists but not on Android" case, provided the developer can take on the accuracy and liability work.

The broader lesson is that in 2026 "nobody has built it" is almost never true on Google Play. The durable openings are **ports of proven iOS-only niche apps, single missing workflows inside crowded categories, and polish for audiences that dislike subscriptions and AI clutter**. Validation should come from reading complaint threads, not posting surveys, because many of these communities ban market research. Because live Reddit was unreachable, the top candidates (especially #2, #8, #9 and #10) should each get one live Reddit search and a feature-by-feature Play listing check before any code is written.
