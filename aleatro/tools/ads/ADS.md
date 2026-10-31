# Ads and "Remove ads" for Aleatro: what to set up

The game side is done: AdMob rewarded and interstitial ads, Google's consent
form (UMP), and a one-time "Remove ads" purchase. Any ID left empty falls
back to **Google's test ads only**.

Privacy policy: **https://mar-devl.github.io/aleatro-legal/**
(source: `tools/site/index.html`). app-ads.txt is live at
**https://mar-devl.github.io/app-ads.txt**, so the Play Console developer
website must be **https://mar-devl.github.io/**.

All your IDs go in one file: **`res://ads/ads.cfg`**. Fill it in, then build.
Every build, debug or release, uses those real IDs, so register your own
phone as a test device (section 5) before you play.

## 1. AdMob: the app and five ad units

Go to [AdMob](https://admob.google.com), then **Apps > Add app > Android**,
and link it to the Google Play listing for `com.mardev.Aleatro`. Copy the
**App ID** (it has a `~`) into `ads.cfg` under `[admob] app_id`.

Then create **five ad units**, under **Ad units > Add ad unit**, one per
placement, so AdMob reports each one separately:

| Ad unit name | Format | Where it shows | `ads.cfg` key |
|---|---|---|---|
| Aleatro – Cash-out | **Interstitial** | After a round's cash-out, before the shop | `interstitial_cash_out` |
| Aleatro – Run end | **Interstitial** | When leaving a lost run (New Run / Main Menu) | `interstitial_run_end` |
| Aleatro – One more hand | **Rewarded** | After losing a blind: one more hand | `rewarded_second_chance` |
| Aleatro – Free reroll | **Rewarded** | In the shop: one free reroll | `rewarded_shop_reroll` |
| Aleatro – Extra pick | **Rewarded** | In a booster pack: one more pick | `rewarded_pack_pick` |

Settings for each unit:

- **Interstitial units:** keep the default ad types (text, image and video). Under
  *Advanced settings*, set a **frequency cap of 10 impressions per user per day**.
  The game's own limit is stricter; this is a safety net.
- **Rewarded units:** reward amount **1**, reward item **`reward`**. The game
  decides what the reward is, so the value doesn't matter. Turn on *Override
  reward settings from third-party ad networks* if you add mediation later.
  Frequency cap: **12 per user per day**.
- **No banner, app open or native units.** The plan leaves them out on purpose.

Copy each **Ad unit ID** (it has a `/`) into its key in `ads.cfg`.

## 2. AdMob: the consent message (needed in Europe)

Go to **AdMob > Privacy & messaging > European regulations (GDPR) > Create
message**, choose the Aleatro app, add your privacy policy URL, and publish
it. The game shows this form on first launch in the EEA, UK and Switzerland.
It also adds **Privacy choices** to the pause menu where players need it.
Without a published message, players in Europe get limited ads or none.

You can also publish a US state regulations message from the same page.

## 3. app-ads.txt

AdMob shows you a line under **Apps > Aleatro > app-ads.txt**. Put it in a
file called `app-ads.txt` at the root of the website listed as Aleatro's
developer website on Google Play. Unverified apps earn less.

## 4. Play Console: "Remove ads" and declarations

> **Not possible from Morocco.** Google Play merchant registration isn't
> available there, so the `remove_ads` product can't be sold. Skip step 1
> below. The game hides the "Remove ads" button when Play has no product.
> The declarations in step 2 still apply. See `tools/store/STORE.md`, section 5.

1. **Monetize > Products > In-app products > Create product**
   - Product ID: **`remove_ads`** (or change `[iap] remove_ads` in `ads.cfg`)
   - Name: Remove ads
   - Description: Removes the ads between rounds for good. Optional reward ads stay available.
   - Price: **$3.99**, then let Play set the regional prices.
   - Activate it.
2. **Policy > App content**
   - **Ads:** *Yes, my app contains ads.*
   - **Data safety:** declare *Device or other IDs* (advertising ID), collected and
     shared for **Advertising or marketing** and **Analytics**, by the AdMob SDK.
   - **Advertising ID:** *Yes*, used for advertising and analytics.
   - **Target audience:** if you include under-13s, the Families policy applies and
     ad settings must change. The plan assumes 13+.
3. To test the purchase, add your Google account under **Settings > License
   testing**, then install a build from a testing track.

## 5. Test before you go live

- **Register your phone under AdMob > Settings > Test devices.** It then gets
  test ads from your real units, which is safe to tap. Never tap real ads on an
  unregistered device: AdMob can flag that as invalid activity.
- `[debug] test_ads=true` in `ads.cfg` switches every unit to Google's sample
  units, for devices you can't register.
- New ad units can take up to an hour to serve. Until then the game simply
  shows nothing at those moments, which is the intended fallback.

## The rules the game follows

These are the starting values from the monetisation plan, set in
`scripts/ads.gd` (`RULES` and `REWARD_LIMITS`):

- **No interstitial** in a player's first run, during a blind, in the shop or
  a pack, in challenges, or at Gold Chip stake. After winning a run there is no
  ad either.
- **Cash-out interstitials** only from 24 hours after install, at least
  **5 minutes and 3 rounds apart**. The gap grows by 1 minute and 1 round with
  each ad in a session.
- At most **4 interstitials per session and 10 per day**. A session ends after
  30 minutes away.
- A rewarded ad buys **10 minutes with no interstitial**.
- **Rewarded ads:** at most 12 a day. One more hand once per run (the run is then
  marked *assisted* and doesn't count for Fastest Win or stake unlocks), a free
  reroll once per shop and 3 per run, and an extra pick once per ante.
- **Remove ads** turns off the interstitials only. Rewarded ads stay
  available, since players choose them. It's offered once after the first
  finished run, then at most weekly after the fifth interstitial, and is always
  in the pause menu.
- An ad that isn't ready is skipped, never waited for.

## How it fits together

- `android_plugin/src/main/java/com/mardev/aleatro/pgs/AleatroAds.java`: AdMob
  (Ads SDK 25.4.0), UMP 3.2.0 and Play Billing 8.3.0, built into
  `addons/aleatro_pgs/bin/aleatro_pgs.aar` by `android_plugin/build.sh`.
- `addons/aleatro_pgs/plugin.gd`: adds the SDKs at export and writes the
  AdMob app ID from `ads.cfg` into the manifest.
- `scripts/ads.gd`: the rules, preloading, consent state and the purchase.
- `scripts/main.gd`: the five placements (search for `ads.`).
