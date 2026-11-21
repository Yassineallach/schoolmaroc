# Missing Android Apps: Accessibility, Chronic Illness, Seniors, Offline Utilities

Research date: 2026-11-21.

**Method note (read first):** Reddit could not be reached at all from this environment. The direct JSON endpoints were blocked by the network proxy (redirected to 127.0.0.1, "SSRF protection"), and the web-search tool refuses `reddit.com` ("domains are not accessible to our user agent"). Unfiltered web searches returned no Reddit threads either. So none of the suggested subreddits (r/Blind, r/deaf, r/ADHD, r/ChronicIllness, r/AgingParents, r/SomebodyMakeThis and so on) were sampled. The evidence below comes from sources that could be read:
- AppleVis forum, read with Scrapling. AppleVis is the largest blind-user forum and has an Android sub-forum.
- HearingTracker forum.
- The F-Droid forum's 895-post "What types of apps are you missing from the FOSS ecosystem?" megathread, through the Discourse API.
- Privacy Guides forum, through the Discourse API.
- Hacker News, through the Algolia API.
- Lemmy, through its API.
- National Federation of the Blind (NFB) articles.
- Google Play search pages, fetched directly.

The Alzheimer's Society forum is behind a Cloudflare challenge. Its content is known only from web-search summaries and is marked as such. Because of all this, request counts are low. They do **not** show the real volume of demand. They are a lower bound from non-Reddit communities.

## Which "missing app" requests have real, direct user evidence?

### Takeaway
I found four candidates with direct, dated requests from real users plus checks that no app fills the gap:
1. An Android walk/don't-walk pedestrian-signal detector. It is iOS-only today (Oko, WalkAssist). This is the strongest.
2. An Android "Live Listen"-style remote microphone that streams to hearing aids. Only hobby prototypes and laggy generic amplifiers exist.
3. A point-at-the-appliance panel reader. VizLens and iOS Magnifier's Point and Speak have no Android twin.
4. A dementia-friendly auto-answer family video-call setup for Android tablets. The one dedicated app, CallBuddy, is iPhone/iPad only.

Several other popular-sounding ideas are already served on Android and should be dropped (see the rejections in the next section).

### Cited Findings

**Candidate 1: Pedestrian-signal (walk/don't-walk) detector for blind users, Android. Classification (3): exists only on iOS.**
- What it would do: point the phone camera at the intersection and identify the pedestrian signal phase (walk, don't walk, countdown) on the device. Report it through distinct beeps or haptics, ideally with crosswalk alignment cues.
- The app that sets the standard, Oko by AYES, is listed only on the Apple App Store. It is described as recognising "walk and don't walk signals" through haptics, audio and colour cues. — [Oko on App Store](https://apps.apple.com/us/app/ayes-oko/id1583614988)
- WalkAssist is a second app of this type and is also iOS-only. It "recognizes traffic related objects (crosswalk signal, crosswalk, and traffic signals)". — [WalkAssist on App Store](https://apps.apple.com/us/app/walkassist/id1615852366)
- Direct request, AppleVis, user "Erick", 24 March 2023: "I know this mainly is an Apple forum, but are you making this app available for androids, all android devices?" — [AppleVis: Every traffic light accessible with OKO](https://www.applevis.com/comment/145382)
- Developer reply, Willem Van de Mierop of AYES, 31 May 2023: "We currently do not support Android, because our software runs locally on the phone it requires a good camera, a good battery and a powerful computerchip. Currently, only iPhones meet these requirements. Our focus is to expand the iOS app to different regions..." — [same thread](https://www.applevis.com/comment/145382)
- Demand signal from the same thread, "Just Another Blind Guy", 26 May 2023: "Tried this app today to cross a busy intersection where cars travel in excess of 40 mph/70 kph. Amazing!" — [same thread](https://www.applevis.com/comment/145382)
- Second independent request, a blind reviewer in an NFB publication: "I would also wish for versions of this app to be developed for other devices such as those running Android and associated derivatives such as BlindShell." — [NFB: Does OKO Have the Green Light in the Blindness Community?](https://nfb.org/node/15396)
- Android check: Google Play searches for "pedestrian signal blind" and "crosswalk walk signal" returned no assistive signal detector. The top "Pedestrian signal" result (com.ruckygames.signaltool) is a toy that "reproduces a Japanese pedestrian traffic light". — [Google Play search](https://play.google.com/store/search?q=pedestrian%20signal%20blind&c=apps)
- Google's Lookout on Android lists Find mode for "doors, bathrooms, cups, vehicles". Its listing does not mention pedestrian signals. — [Lookout on Google Play](https://play.google.com/store/apps/details?id=com.google.android.apps.accessibility.reveal)
- Older background: an AppleVis poster said "Intersection Explorer", an old Android app, has no clear replacement. — [AppleVis: What I miss most about iOS](https://www.applevis.com/forum/android/what-i-miss-most-about-ios-why-i-m-still-not-going-back?page=1)
- Independent requests found: 2 (AppleVis, 2023; NFB article, undated in what I saw). Positive reactions: thread praise as quoted. Willingness to pay: not stated. Oko's price was not confirmed. Recency: 2023.

**Candidate 2: "Live Listen" for Android, using the phone as a remote microphone that streams to hearing aids or earbuds. Classification (2): similar apps exist but don't do the job well.**
- What it would do: put the phone on a restaurant table or lectern and stream its microphone to the user's hearing aids with low latency. That means ASHA or LE Audio/Auracast, or Bluetooth earbuds. It would add noise reduction and a "table mic" mode.
- The HearingTracker thread "I built a hearing aid mic streaming app — because I needed it" ran from 5 May 2025 to 24 February 2026. The author, thivyan.pillay, wrote: "Android doesn't offer a built-in equivalent", and later: "Android has no native solution". — [HearingTracker forum](https://forum.hearingtracker.com/t/-/102572/3)
- Clothears, 15 May 2025: the prototype "seems so much more useful and so much cheaper than a proprietary external mic". About earlier attempts: "the latency was really bad and I gave up". — [HearingTracker forum](https://forum.hearingtracker.com/t/-/102572/3)
- Nerdrunner, 22 July 2025: "there's a substantial delay" on a Pixel 4 over Classic Bluetooth, and "I'm very interested in using your program for Auracast." — [HearingTracker forum](https://forum.hearingtracker.com/t/-/102572/3)
- paul.cleary.nz, 15 May 2025: uses an iPhone as a remote "table microphone" and asked for that mode. TerryDarc, 24 February 2026, asked for a simple mode switch. — [HearingTracker forum](https://forum.hearingtracker.com/t/-/102572/3)
- Earlier thread "Iphone 'live listen' function": started March 2023, last reply April 2025, 61 replies, 5.2k views. This shows sustained interest in the iOS feature. — [HearingTracker forum](https://forum.hearingtracker.com/t/iphone-live-listen-function/75065/40)
- Existing Android alternatives:
  - Google Sound Amplifier ([Play](https://play.google.com/store/search?q=live%20listen&c=apps)).
  - Generic "Listening Device: Live Listen" (com.listeningdevice.hearingaid). Rated 4.6 with 100K+ downloads, and its own listing warns "Bluetooth headphones may introduce sound delay". — [Google Play](https://play.google.com/store/apps/details?id=com.listeningdevice.hearingaid)
  - Manufacturer remote-mic apps such as myPhonak and Starkey T2 Remote, which control proprietary hardware.
  - The Hark prototype in the HearingTracker thread.
- Independent requests found: about 5 participants in one thread, 2025–2026. Willingness to pay: none explicit. "Cheaper than a proprietary external mic" suggests people would pay against roughly $200+ hardware, but that price is my estimate, not sourced.

**Candidate 3: Point-at-appliance panel reader (VizLens or Point and Speak style), Android. Classification (3): exists only on iOS.**
- What it would do: the user points a finger at a microwave, thermostat or kiosk touch panel, and the app reads the label under the fingertip.
- AppleVis, Josh Kennedy, 19 May 2023, after 3–4 months on Android: "IOS has vizLens, android does not have any equivalent to this app at all." He also missed iOS screen recognition that can "describe and activate and manipulate controls ... not made accessible by the app developers. Android cannot do this." — [AppleVis: My review, why I returned to iOS from Android](https://www.applevis.com/comment/147994)
- iOS Magnifier's Point and Speak "can identify and read text on physical objects that you point to–like keypads on doors or buttons on electrical appliances". A web search found no equivalent Android feature. — [Apple Support: Magnifier live descriptions](https://support.apple.com/en-mn/guide/iphone/iph32deb9296/ios)
- On Android, Lookout, Envision and Be My Eyes read text in general, but none advertises fingertip-targeted reading. — [Google Play search](https://play.google.com/store/search?q=read%20appliance%20buttons%20blind&c=apps)
- Independent requests found: 1 direct (2023). This is weak and needs more evidence.

**Candidate 4: Auto-answer, one-touch family video calling for people with dementia on Android tablets. Classification (2)/(5): similar apps lack the key function, or it needs dedicated hardware.**
- What it would do: a locked-down kiosk for a care-home tablet. Family calls and it auto-answers, staff do nothing, and the person needs no buttons, logins or updates. It is administered remotely by family.
- Alzheimer's Society forum threads with direct requests in their titles: "Anyone know an easy device or app for my Mum to make video call in Care home?" and "Can anyone recommend an easy to use mobile phone app". These threads are behind Cloudflare and I could not open them. What I know of their content comes from a web-search summary: one user set up an Android tablet in a care home and "controlled it remotely", and another used an Echo Show. — [Thread 1](https://forum.alzheimers.org.uk/threads/anyone-know-an-easy-device-or-app-for-my-mum-to-make-video-call-in-care-home.98208/); [Thread 2](https://forum.alzheimers.org.uk/threads/can-anyone-recommend-an-easy-to-use-mobile-phone-app.111207/)
- City-Data caregiving thread "Simple Android Apps for senior citizens (assisted, facility, dementia, mother)". Content also known only from the search summary. — [City-Data](https://www.city-data.com/forum/caregiving/3256647-simple-android-apps-senior-citizens.html)
- The closest dedicated app, CallBuddy (a FaceTime launcher for dementia), "works exclusively with iPads and iPhones". — [CallBuddy on App Store](https://apps.apple.com/ca/app/callbuddy/id6744102656)
- A Google Play search for "auto answer video call elderly" returned only generic phone-call auto-answer apps, plus JusTalk and Google Meet. "Dementia video call care home" returned mostly random-chat apps. — [Play search 1](https://play.google.com/store/search?q=auto%20answer%20video%20call%20elderly&c=apps); [Play search 2](https://play.google.com/store/search?q=dementia%20video%20call%20care%20home&c=apps)
- The RAZ Memory Cell Phone is a separate dedicated handset, not an app. — [RAZ Mobility](https://www.razmobility.com/solutions/memory-cellphone/)
- Independent requests found: 2–3 thread starters. I could not get dates or reaction counts.

**Weaker or single-request candidates (kept, with low scores)**
- **ADHD "passive time-until-next-anchor" countdown.** It shows "15 mins until stand-up" without alarms. A developer built DuePal on iOS (Dynamic Island) for a friend with ADHD, "since I couldn't find an existing app that did exactly this (simple, non-intrusive, strictly visual)". This is HN, 2 January 2026, and it is the builder's own claim. — [HN: DuePal](https://news.ycombinator.com/item?id=46465112). I did not check Android for existing persistent-notification countdown apps, and they probably exist. Treat it as unverified.
- **FOSS one-handed cursor accessibility tool** (an alternative to Quick Cursor and Edge Gestures). F-Droid user Unospa, 13 June 2026: "on a degoogled device I'm sadly limited to the free version, as it can only be purchased—and purchases restored—on a phone with Google Play Services." — [F-Droid forum megathread #928](https://forum.f-droid.org/t/x/183/928). Classification (2): a proprietary app exists. 1 request.
- **TalkBack-optimised dictionary and RSS reader.** AppleVis poster: "No third-party commercial dictionary is fully accessible/navigable on Android (name AHD 5/ODE/Merriam-Webster on iOS), and the same is true about RSS read[ers]". — [AppleVis: What I miss most about iOS](https://www.applevis.com/forum/android/what-i-miss-most-about-ios-why-i-m-still-not-going-back?page=1). 1 request. My scrape did not capture the date.
- **Reliable colour-plus-pattern identifier for blind users.** An AppleVis poster relies on an iOS "clothes color" app that also gives patterns ("a huge ... game changer"), and was afraid of losing it on Android. A reply said Android colour apps are many but "only a few of them are well-maintained", and that Speek works "not very well". — [same AppleVis thread](https://www.applevis.com/forum/android/what-i-miss-most-about-ios-why-i-m-still-not-going-back?page=1). Classification (2). 1 request.

### Inferences
- Blind-user demand clusters around **iOS-only on-device computer-vision tools**. Oko's developer said in 2023 that Android hardware was too weak. Android phones in 2025–26 have NPUs, so that reason is weaker now. This is the clearest "category 3" opportunity.
- Hearing-aid streaming demand is real, but it is technically gated by Android Bluetooth latency and how ASHA and LE Audio support varies by phone. A solo developer can ship a "good enough on Pixels/LE Audio phones" version, but support costs will be high.
- Requests in the senior/dementia space usually come from **adult children, not the seniors**. A caregiver-administered kiosk fits that buyer better than another launcher.

### Gaps
- No Reddit data at all (see the method note). The deaf/HoH, ADHD, autism, dyslexia, POTS, migraine and AgingParents communities therefore have little or no direct-quote coverage. A follow-up researcher with Reddit access should search r/Blind ("Oko android"), r/hardofhearing ("live listen android"), r/dementia and r/AgingParents ("auto answer video call tablet").
- Upvote and "me too" counts are mostly unavailable. AppleVis and HearingTracker threads gave participant counts, not vote counts.
- I could not check prices or willingness to pay for Oko, WalkAssist or CallBuddy.
- I did not check Product Hunt or GitHub for Android pedestrian-signal or point-to-read projects. There are research prototypes in the literature, such as the SKI walk-light detector ([PDF](https://www.ski.org/wp-content/uploads/2025/01/ivanchenko-coughlan-shen-icchp10.pdf)), but I found no consumer Android release.

## Which plausible ideas should be rejected because Android already has them?

### Takeaway
Many ideas that sound like gaps are already filled on Android: Soundscape-style audio navigation, door detection, AAC, offline/no-account chronic-illness symptom trackers, ME/CFS heart-rate pacing, offline voice typing and offline translation. Building any of these would be a clone, not a missing app.

### Cited Findings
- **Soundscape-style 3D audio navigation (Microsoft Soundscape successor) — exists on Android.** The Scottish Tech Army's Soundscape for Android open beta went live on 8 August 2025 with about 400 testers. — [STA newsletter 19 Aug 2025](https://scottish-tech-army.github.io/Soundscape-Android/newsletters/19-Aug-2025.html); [release notes](https://scottish-tech-army.github.io/Soundscape-Android/release-notes.html). A Guide Dogs UK page saying it doesn't work on Android is out of date. — [Guide Dogs](https://www.guidedogs.org.uk/getting-support/information-and-advice/how-can-technology-help-me/apps/soundscape/)
- **Door/object detection (iOS Magnifier Door Detection) — mostly covered.** Lookout's Find mode finds "doors, bathrooms, cups, vehicles" with "direction and distance". Lookout has 1M+ downloads and a 4.0 rating. — [Lookout on Google Play](https://play.google.com/store/apps/details?id=com.google.android.apps.accessibility.reveal)
- **AAC for autism/non-speaking users — saturated.** Proloquo2Go is iOS-only, but Google Play lists many AAC apps, including Avaz, Otsimo AAC, Symboloud, SymboTalk, OpenSpeak AAC and Context AAC. — [Play search "AAC symbols"](https://play.google.com/store/search?q=AAC%20symbols&c=apps); [AlternativeTo: Proloquo2Go alternatives](https://alternativeto.net/software/proloquo2go)
- **Offline, no-account chronic illness/POTS tracker — saturated.** Lunaire POTS & Dysautonomia Tracker (Android) says it is offline with no accounts. "Chronic Illness Tracker" (Android) says it is offline-first. Many iOS equivalents exist. — [Lunaire POTS on Play](https://play.google.com/store/apps/details?id=uk.lunaire.pots&hl=en_US); [Chronic Illness Tracker on Play](https://play.google.com/store/apps/details?id=chronic.illness.tracker&hl=en_US)
- **ME/CFS and Long COVID heart-rate pacing — exists on Android.** Google Play has "ME/CFS Pacing" (au.org.emerge.pacing), "Visible: Pacing for illness" and "Heart Alert" (Polar alert). The best-known pacing apps (WatchME, Pacing, Trackuility, PaceME) are iOS-only, but Android is not empty. — [Play search](https://play.google.com/store/search?q=ME%2FCFS%20pacing%20heart%20rate&c=apps); [WatchME, iOS](https://apps.apple.com/app/watchme/id1583153009)
- **Offline/local voice typing — exists.** FUTO Voice works "completely offline". — [Privacy Guides forum](https://discuss.privacyguides.net/t/transcription-tools-that-run-locally/19271/4). VoxScribe (sherpa-onnx with Whisper) is heading to F-Droid as of October 2026. — [F-Droid forum](https://forum.f-droid.org/t/packaging-question-before-an-rfp-offline-voice-typing-app-with-sherpa-onnx-and-a-bundled-whisper-model/34915/1)
- **Offline translator — exists.** The offline-translator project uses Firefox models on the device. — [Privacy Guides forum, March 2026](https://discuss.privacyguides.net/t/offline-translator-for-android/36095/1)
- **One-tap medication/vitamin intake log, private — old request, now weak.** F-Droid user Corwin asked for this on 20 April 2021 ("Privacy would be a very big deal ... Calendula ... has way too many scary permissions"). On 15 December 2021 he said no FOSS app fit, so he built one in SailForms. — [F-Droid #453](https://forum.f-droid.org/t/x/183/453); [#596](https://forum.f-droid.org/t/x/183/596). The request predates 2023 and the category is crowded, so I reject it.
- **Generic private "track any variable" app.** Request on the F-Droid forum, 9 October 2026, with 3 posts. — [F-Droid forum](https://forum.f-droid.org/t/app-for-tracking-any-data-record-analyze-real-time-input/34887/1). Rejected: FOSS trackers of this kind already exist (for example Track & Graph). I did not re-check that in this session.

### Inferences
- In 2025–26, "privacy-first offline tracker" and "offline AI utility" ideas mostly get answered with existing FOSS apps on Privacy Guides and F-Droid. The offline-utility category looks crowded. Gaps there are narrow feature gaps, not missing apps.

### Gaps
- I did not check whether Lookout's Find mode works well in practice for door finding compared with iOS LiDAR.
- I did not run Play checks for dyslexia tools (system-wide fonts, reading-ruler overlays) or deaf tools (speaker-labelled offline captions), so I make no claim about them either way.

## Ratings of the surviving ideas (solo Android developer)

### Takeaway
The pedestrian-signal detector has the best mix of verified iOS-only status, serious need and a clear audience, but it is technically and legally the hardest. The dementia video-call kiosk is the easiest to build and has the clearest paying buyer (adult children).

### Cited Findings
Ratings combine the sourced evidence above with my own judgement. The scores are inferences, not sourced facts.

| # | Idea | Class | Requests found | Complexity | Monetization | Score /10 | Justification |
|---|---|---|---|---|---|---|---|
| 1 | Pedestrian-signal detector ([Oko thread](https://www.applevis.com/comment/145382), [NFB](https://nfb.org/node/15396)) | 3 (iOS-only) | 2 (2023) | High: on-device detection model, regional signal variants, safety liability | Freemium or subscription; grants and partnerships with blindness organisations | 6 | Verified gap on Play; life-safety value; the developer's "Android too weak" reason is now outdated. Risks: liability and accuracy across regions. |
| 2 | Live Listen-style remote mic ([HearingTracker](https://forum.hearingtracker.com/t/-/102572/3)) | 2 | ~5 people in 1 thread (2025–26) | Med–High: latency, LE Audio/Auracast, device fragmentation | One-time paid ($5–15) against $200+ hardware mics (price is my estimate) | 5 | Real recurring need. Existing apps have latency complaints, and a prototype has already started. |
| 3 | Dementia auto-answer video-call kiosk ([Alzheimer's forum](https://forum.alzheimers.org.uk/threads/anyone-know-an-easy-device-or-app-for-my-mum-to-make-video-call-in-care-home.98208/), [CallBuddy iOS](https://apps.apple.com/ca/app/callbuddy/id6744102656)) | 2/5 | 2–3 (dates unknown) | Medium: kiosk/device-owner mode, WebRTC or Jitsi, remote admin | Family subscription; B2B care-home licences | 5 | Paying buyer exists; current options are hardware (Komp, Echo Show) or iOS-only; evidence is indirect. |
| 4 | Point-to-read appliance panels ([AppleVis](https://www.applevis.com/comment/147994)) | 3 | 1 (2023) | High: fingertip tracking plus OCR | Freemium | 4 | Clear gap, but only one request. LLM-based describers (Be My AI, Lookout) partly cover it. |
| 5 | TalkBack-first dictionary/RSS ([AppleVis](https://www.applevis.com/forum/android/what-i-miss-most-about-ios-why-i-m-still-not-going-back?page=1)) | 2 | 1 | Low–Med | Paid app | 3 | Small niche, easy to build; licensing dictionary content is a barrier. |
| 6 | Colour-plus-pattern identifier ([AppleVis](https://www.applevis.com/forum/android/what-i-miss-most-about-ios-why-i-m-still-not-going-back?page=1)) | 2 | 1 | Medium | Paid or one-time | 3 | Existing apps described as poorly maintained; low request count. |
| 7 | FOSS one-handed cursor ([F-Droid #928](https://forum.f-droid.org/t/x/183/928)) | 2 | 1 (2026) | Medium (AccessibilityService) | Donations or F-Droid; limited | 2 | Proprietary app exists; the audience is mainly de-Googled users. |
| 8 | ADHD passive countdown ([HN DuePal](https://news.ycombinator.com/item?id=46465112)) | Unverified | 1 (builder) | Low | One-time | 2 | Builder's own claim; Android alternatives not checked. |

### Inferences
- Only ideas 1–3 clear the bar of a verified gap plus more than one independent person. Ideas 4–8 do not meet the brief's "multiple independent requests" standard and should be treated as leads, not findings.
- The deep-research coordinator should not report this category as "8–10 validated ideas". Given the Reddit block, 3 validated ideas and 5 leads is the honest result.

### Gaps
- I did not search the Apple App Store separately for the weaker ideas.
- Market-size figures, such as the number of blind Android users or of hearing-aid users on Android, were not collected.
