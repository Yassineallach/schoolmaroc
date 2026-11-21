# Missing Android apps people want: Tech / power-user utilities and AI apps

Research date: 2026-11-21. Scope: Android power-user utilities, iOS/macOS apps or features with no Android equivalent, de-Googled/privacy tools, automation, and on-device AI (LLM, vision, speech).

**Important limitation, read first.** Reddit could not be reached at all in this session. The reddit.com search JSON returned an HTML block page, Scrapling on old.reddit.com was refused (the redirect went to an internal IP and was rejected as SSRF), and WebSearch refuses `reddit.com` as a domain ("not accessible to our user agent"). The main demand sources (r/androidapps, r/degoogle, r/LocalLLaMA, r/SomebodyMakeThis) are therefore **missing** from this evidence. Demand evidence comes from Hacker News comments (Algolia API), Lemmy and F-Droid forum searches (which turned up little), and web searches. Request counts below are therefore low. They are lower bounds, not measures of demand.

A second finding matters just as much: **most of the obvious "AI feature Android lacks" ideas already have third-party Android apps**, usually released in 2024-2025. Several candidates are dropped or reclassified for that reason.

## Where are people writing "I wish there was an app" / "is there an Android equivalent" requests, and which requests repeat?

### Takeaway
Direct requests do exist on Hacker News, mostly as side remarks from iPhone-to-Android switchers. They mention specific iOS apps they cannot replace (Drafts, Things, Bear, Mela, Alfred) and specific power-user gaps (per-app notification sound management with backup). I could not verify repetition across communities because Reddit was blocked. No candidate below has more than about 1-3 independent direct requests that I actually saw.

### Cited Findings
- iPhone user who wants to switch to Pixel (2025-08-21): "there is one app that I can't find anything close to: Drafts. Maybe I'm missing something? ... the whole experience of adding notes with this app is something I haven't experienced with anything else." The only reply suggested KDE Connect, which answered their clipboard side question, not the Drafts question. — [HN comment](https://news.ycombinator.com/item?id=44970658)
- Long-time Mac user (2023-09-18) listing apps with no equivalent elsewhere: "Ulysses, Bear, Things, Reeder, Mela, Alfred, MindNode ... have no equivalents in the Windows or Linux worlds. I know because I also have a PC and I've looked very hard for replacements." This is about desktop, not Android. — [HN comment](https://news.ycombinator.com/item?id=37552112)
- User about to leave iPhone (2025-06-26): "there are still some nice apps that I really like on iOS and have no true equivalent on Android." No apps were named. — [HN comment](https://news.ycombinator.com/item?id=44384193)
- Power user (2025-07-04): "I really wish there was an app that could manage all that [per-app notification tones], including exporting/importing everything configured, so I could reuse that and not be forced to rebuild it from scratch on each and every new Android." — [HN comment](https://news.ycombinator.com/item?id=44462783)
- The same thread had a library developer reply: "changing the notification sounds of *individual apps or their notification channels* is not possible from outside those apps. Android does not allow third-party apps ... to modify another app's notification settings." The requester answered: "We'll just have to wait for Android to expose that in an API." — [HN reply](https://news.ycombinator.com/item?id=44472226), [HN reply](https://news.ycombinator.com/item?id=44472326)
- Samsung users report that per-app notification sounds are lost or broken after restoring to a new phone. — [Samsung EU Community](https://eu.community.samsung.com/t5/galaxy-s21-series/oneui-individual-notification-sounds-for-apps-problems/m-p/3941867). An AOSP/e-OS framework commit says Backup & Restore restores NotificationManagerService before packages are installed, "so notification channels lose custom sound configurations." — [/e/OS framework commit](https://gitlab.e.foundation/e/os/android_frameworks_base/-/commit/0058221f041db2fd37e9c82fd80b5937fa4f3f3a)
- Wish for an Android app that emulates Apple BLE ecosystem handshakes (2023-08-13): "I wish there was an Android app that emulated all these weird Apple ecosystem BLE handshake things." Only one request, and it is mostly blocked technically. — [HN comment](https://news.ycombinator.com/item?id=37114374)
- Wish for a non-Google gallery that rivals Google/Apple Photos with self-hosted remote galleries (2024-02-26): "There seems to be quite a gap in the market for a Gallery application for Android ... which supports self-hosted remote galleries." — [HN comment](https://news.ycombinator.com/item?id=39512449)
- Request for a physical object or tag at the other side of the house that triggers a phone-addiction block (2025-02-24): "Anybody here know an Android equivalent of this?" — [HN comment](https://news.ycombinator.com/item?id=43164885)
- Wish for an APOD wallpaper app (2023-12-26). — [HN comment](https://news.ycombinator.com/item?id=38770283). Rejected: several APOD wallpaper apps already exist (common knowledge; not re-verified this session).
- GrapheneOS user (2024-12-09): "I wish there was an app database that says what works and what does not" on de-Googled ROMs. — [HN comment](https://news.ycombinator.com/item?id=42368748)

### Inferences
- The best-supported category is "iOS app X has no Android equivalent". Drafts is the clearest named example in the material I saw.
- The phrases the brief suggested ("I wish there was an app", "is there an Android equivalent") mostly return noise on HN. Reddit is still where these requests concentrate, so it has to be checked before any build decision.

### Gaps
- No Reddit, XDA or Product Hunt data, because Reddit and WebSearch-to-Reddit were blocked and the time budget did not allow XDA. Upvote and "me too" counts could not be gathered for any candidate.
- The Lemmy and F-Droid forum keyword searches returned mostly irrelevant posts (privacy news, F-Droid packaging questions). No usable request threads were found there.

## Candidate ideas, verification of non-existence, feasibility and ratings

### Takeaway
After checking for existing apps, only 3-4 candidates survive as real gaps:
- a Drafts-style capture-first text inbox with actions (iOS-only),
- a per-app notification-sound manager with export/import (the workaround is technically awkward),
- a de-Googled compatibility database,
- possibly a polished, fully offline "writing tools" layer for non-Samsung/non-Pixel phones.

Pixel Screenshots clones, AI notification summaries and voice-banking apps already exist on Android, so those are dropped or reclassified.

### Cited Findings

**1. Drafts-style "capture first, decide later" text inbox with actions (iOS-only, category 3)**
- Concept: the app opens instantly to a blank page with the keyboard up. Dictation is built in. A configurable action list then sends the text elsewhere: append to a file, share, send to Tasker or an HTTP endpoint, create a calendar event, deep links.
- Demand: 1 direct request seen ([HN, 2025-08-21](https://news.ycombinator.com/item?id=44970658)), with no answer pointing to an Android equivalent. Drafts also appears in a 2023 list of irreplaceable Apple apps ([HN](https://news.ycombinator.com/item?id=37552112)). Positive reactions: none visible (HN does not show upvotes on comments).
- Verification: the App Store listing covers iPhone, iPad, Mac and Apple Watch only. Its description: "a quick notebook, handy editor, and writing automation tool, all in one", with user-created actions behind a Drafts Pro subscription. — [App Store: Drafts](https://apps.apple.com/us/app/drafts/id1236254471). AlternativeTo lists 50+ "alternatives" and names Notesnook as the top one, but Notesnook is a general note app without an action system. — [AlternativeTo](https://alternativeto.net/software/drafts/?p=3)
- Willingness to pay: Drafts itself runs on a Pro subscription, so its users already pay ([App Store](https://apps.apple.com/us/app/drafts/id1236254471)).
- Classification: (3) exists, but not on Android. The Android options are similar general note apps without the capture-and-action model (category 2).
- Feasibility: high. It needs only a quick-tile or widget entry point, the share sheet, intents to Tasker or MacroDroid, and a JS or simple scripting engine for actions. No restricted APIs.
- Complexity: medium. Monetization: one-time Pro unlock or a subscription for actions and sync. **Score: 6/10.** The need is clear, the product is proven on iOS and there is no direct Android rival, but only 1-2 direct requests were found and the market is niche.

**2. Per-app notification sound manager with export/import (category 2, partly blocked by Android)**
- Concept: assign a distinct sound to each app or contact and back up the whole set, then restore it on a new phone.
- Demand: 1 direct request ([HN, 2025-07-04](https://news.ycombinator.com/item?id=44462783)). Related pain: Samsung users lose per-app sounds after a restore ([Samsung Community](https://eu.community.samsung.com/t5/galaxy-s21-series/oneui-individual-notification-sounds-for-apps-problems/m-p/3941867)), and AOSP had a bug that dropped channel sounds on restore ([/e/OS commit](https://gitlab.e.foundation/e/os/android_frameworks_base/-/commit/0058221f041db2fd37e9c82fd80b5937fa4f3f3a)).
- Feasibility: a third-party app cannot change another app's notification-channel sound ([HN reply](https://news.ycombinator.com/item?id=44472226)). The workable route is a NotificationListenerService that plays its own sound per app or channel while the user silences that app's channel. That approach is allowed under Play policy for notification access, but it adds latency and is hurt by OEM battery killers.
- Existing alternatives: I did not confirm any specific Play Store app offering per-app custom sounds with export/import. The web search returned only forum posts and framework commits, so existence remains **unverified**. Search the Play Store for "per app notification sound" before building.
- Complexity: low to medium. Monetization: small one-time paid unlock. **Score: 4/10.** The pain is real but narrow, the workaround is hacky, and the existence check is incomplete.

**3. De-Googled app compatibility database (GrapheneOS, LineageOS without GMS, /e/OS) (category 2)**
- Concept: a crowd-sourced "does app X work without Play Services or with sandboxed Play" lookup, plus an on-device scan of installed apps.
- Demand: 1 direct request seen ([HN, 2024-12-09](https://news.ycombinator.com/item?id=42368748)): "I wish there was an app database that says what works and what does not."
- Existing alternatives (from general knowledge, **not verified this session**): Plexus (plexus.techlore.tech) is a crowd-sourced microG/de-Googled compatibility database with an Android app. If it is still active, this idea is mostly covered. Check before pursuing.
- Classification: probably (2) or already exists. **Score: 2/10** unless Plexus turns out to be abandoned.

**4. Fully offline system-wide "Writing Tools" for any Android phone (Apple Intelligence envy) (category 2)**
- Concept: select text in any app, then Rewrite, Proofread, Summarize or change Tone using an on-device model, with no API key and no cloud.
- Verification: early open-source apps already exist:
  - Local Writer: MIT licensed, Android 13+, ARM64, bundled offline models, rewrites via the selected-text action and an overlay. — [GitHub: local-writer-android](https://github.com/aniketsaurav18/local-writer-android)
  - SwiftSlate: on F-Droid, works system-wide via the Accessibility Service and the text-selection menu, uses any OpenAI-compatible endpoint, including local Ollama. — [F-Droid: SwiftSlate](https://fdroid.gitlab.io/jekyll-fdroid/packages/com.musheer360.swiftslate/)
  - LLM Hub has a "Writing Aid", but inside its own chat app. — [GitHub: LLM-Hub](https://github.com/timmyy123/LLM-Hub)
  - The best-known Writing Tools clone is desktop-only. — [GitHub: theJayTea/WritingTools](https://github.com/theJayTea/WritingTools)
- Demand: I found no direct Android user request because Reddit was blocked. The XDA piece "I replaced Grammarly Pro with a local model" shows interest on desktop. — [XDA](https://www.xda-developers.com/i-replaced-grammarly-premium-with-a-local-model-on-my-gpu-and-my-drafts-never-leave-my-pc/)
- Feasibility: PROCESS_TEXT intent (no special permission) plus llama.cpp or MediaPipe/LiteRT models of about 1-3B parameters. Avoid relying on the Accessibility API, which brings Play review risk.
- Classification: (2). Similar apps exist but are early, hobbyist and hard to set up. **Score: 4/10.** The gap is polish, not existence, and the demand evidence is weak.

**5. Pixel Screenshots equivalent for non-Pixel phones: DROPPED (already exists)**
- PixelShot uses ML Kit OCR on-device, works on Samsung, Motorola, OnePlus and older Pixels, and does not analyze in the background. — [Beebom](https://beebom.com/pixelshot-app-brings-pixel-screenshots-any-android-phone/). Shots Studio is called "the closest alternative" and offers online or offline AI models. — [Android Police](https://www.androidpolice.com/i-replaced-the-pixel-screenshots-app-with-a-free-alternative/). Other apps are listed on [AlternativeTo](https://alternativeto.net/software/pixel-screenshots/). Samsung is preparing a built-in "Memory" app (One UI 9.5, early 2027). — [Droid-Life, 2026-11-09](https://www.droid-life.com/2026/11/09/samsung-readies-memory-galaxy-alternative-to-pixel-screenshots/), [Android Authority](https://www.androidauthority.com/samsung-memory-app-pixel-screenshot-3732805/)
- Verdict: several established apps, and the largest OEM is building it in. Reject.

**6. AI notification summaries like iOS 18 for any Android phone: DROPPED (already exists)**
- Existing apps:
  - Sum Up uses Gemini and needs an API key. — [Play Store](https://play.google.com/store/apps/details?id=com.gustavoas.sumup&hl=en_US), [Beebom](https://beebom.com/get-ios-18-ai-notification-summary-android/)
  - NotiSummary is open source and uses ChatGPT. — [GitHub](https://github.com/noti-summary/NotiSummary), [Play Store](https://play.google.com/store/apps/details?id=org.muilab.noti.summary&hl=en_US)
  - NotifAI runs on-device with Gemini Nano on supported Pixel and Samsung phones. — [Play Store](https://play.google.com/store/apps/details?id=com.androidexpert35.notifai&hl=en)
- Remaining sliver: an on-device summary for phones without Gemini Nano. This is a feature, not an app gap. Reject.

**7. iOS "Personal Voice" (voice banking for ALS or speech loss) on Android: RECLASSIFIED (cross-platform paid apps exist)**
- Apple's Personal Voice is iOS/macOS only. — [iDownloadBlog](https://www.idownloadblog.com/2023/07/17/how-to-use-personal-voice-iphone-mac/)
- Android options:
  - Voice Back: iPhone, iPad and Android, voice clone from about 10 seconds of audio, $29.99 lifetime or $4.99/month. — [Voice Back](https://voicebackapp.com/voice-banking)
  - The Voice Keeper: on Google Play. — [EatSpeakThink](https://eatspeakthink.com/easy-voice-banking-with-voicekeeper/)
  - Acapela My-Own-Voice: funded by Team Gleason for some users. — [ALS Forums](https://www.alsforums.com/community/threads/message-banking-solutions.54755/)
  - A comparison chart of services exists. — [MND Association chart, Oct 2025](https://www.mndassociation.org/sites/default/files/public/2025-10/Voice%20banking%20services%20comparison%20chart%20-%20Oct%202025.pdf)
- Willingness to pay: proven by those price points. But the field is served, and the work is clinically sensitive. **Score: 3/10**, and only as an offline, on-device, private variant.

**8. Self-hosted / de-Googled gallery with Google-Photos-grade AI search: DROPPED for a solo developer**
- Demand: [HN, 2024-02-26](https://news.ycombinator.com/item?id=39512449).
- Existing (general knowledge, not re-verified this session): Immich, with a mature Android app and CLIP search, and PhotoPrism. Reject because established solutions exist.

**9. Physical-object trigger for anti-phone-addiction (NFC tag "unlock" for app blocking): LIKELY EXISTS**
- Demand: [HN, 2025-02-24](https://news.ycombinator.com/item?id=43164885).
- Brick, Unpluq and others are known NFC-tag blockers (general knowledge, not verified this session), and Tasker or MacroDroid can do NFC triggers. Likely category (2) or already served. Reject pending verification.

**Rejected on technical or policy grounds**
- Apple BLE ecosystem emulation on Android ([HN](https://news.ycombinator.com/item?id=37114374)): it needs Apple's proprietary authentication and is mostly infeasible.
- Changing other apps' notification-channel settings directly: Android sandboxing forbids it ([HN](https://news.ycombinator.com/item?id=44472226)).
- Call screening, recording or AI call assistants on non-Pixel phones: call-audio APIs are restricted, and Play policy limits Accessibility-based call recording (general knowledge).

### Inferences
- Ranked shortlist: (1) Drafts-style capture inbox, 6/10; (4) offline writing tools, 4/10; (2) per-app notification sounds, 4/10; (7) offline voice banking, 3/10. Everything else is dropped.
- For AI apps, the pattern is that Android developers ship clones of each new Apple or Pixel AI feature within months. Pixel Screenshots and iOS 18 summaries both got third-party clones within about a year. A "missing AI app" niche is therefore usually a polish, privacy or offline gap, not a true absence.
- None of these candidates has the cross-community, multi-request evidence the brief asks for. Treat the shortlist as hypotheses to check on Reddit, not as validated opportunities.

### Gaps
- Request counts, upvotes and recency on Reddit for every candidate (blocked).
- No Play Store or F-Droid searches were run for: a Drafts-like app with actions (to be sure nothing new launched in 2025-2026); per-app notification sounds with backup; whether Plexus is still active; NFC phone-blocker apps.
- Requests for apps people want from iOS beyond Drafts (Things 3, Halide, Overcast, Apple Journal, Shortcuts-simple automation): not researched, because of the tool budget.
- On-device LLM and speech uses requested in r/LocalLLaMA (offline Whisper meeting transcription, local RAG over phone files, on-device photo Q&A): not researched, because Reddit was blocked.
