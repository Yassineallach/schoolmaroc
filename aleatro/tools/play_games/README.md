# Google Play Games Services for Aleatro

Play Games Services v2 is built in: sign-in, 30 achievements and 4
leaderboards. The game side is done. What's left is entering these in Play
Console and pasting back the IDs it gives you.

- Project ID: **451331127820** (it's already inside the app's manifest)
- Package: **com.mardev.Aleatro**

## 1. Credentials (sign-in won't work without them)

Go to Play Console > Aleatro > **Grow users > Play Games Services > Setup and
management > Configuration**. Under **Credentials**, add an **Android**
credential for each key that signs the app. Both use package
`com.mardev.Aleatro`.

| For | SHA-1 |
|---|---|
| Builds installed from Google Play (Play App Signing) | Copy it from **Test and release > App integrity > App signing**: "App signing key certificate" |
| The APK installed directly (your upload/release key) | `34:84:7B:12:79:B8:B2:D9:58:20:F9:C0:C1:F4:09:89:A1:9D:52:7E` |

If Play Console asks, set up the OAuth consent screen in the linked Google
Cloud project first (External, app name Aleatro, your support email).

## 2. Achievements

Go to **Achievements > Add achievement** for each row of
[`achievements.csv`](achievements.csv), **in that order**:

- **Name** and **Description**: from the sheet.
- **Icon**: `icons/achievements/<key>.png` (512×512).
- **Incremental**: on only for the three rows with *incremental steps*:
  Card Sharp, Clean Sweep and Big Spender, each with **2500** steps.
- **Initial state**: Revealed.
- **Points**: from the sheet. They add up to exactly 1000, Play Games' limit.
- **List order**: as in the sheet.

Translations: on each achievement, **Add translations** for zh-CN, ja-JP,
ko-KR, de-DE, fr-FR, es-ES, pt-BR, it-IT and ar from
[`translations.csv`](translations.csv). These match the game's own wording.

## 3. Leaderboards

Go to **Leaderboards > Add leaderboard** for each row of
[`leaderboards.csv`](leaderboards.csv):

- **Score format**: Numeric, no decimals.
- **Ordering**: *Larger is better*, except **Fastest Win**, which is *Smaller
  is better*.
- **Icon**: `icons/leaderboards/<key>.png`.
- **Translations**: the last four rows of `translations.csv`.

## 4. Paste the IDs into the game

On the Achievements page (or Leaderboards; it's the same file), click **Get
resources**, choose **Android**, and copy the XML into
**`res://pgs/games-ids.xml`**, replacing what's there. Then build.

The game matches each ID by its resource name, for example
`achievement_victory_lap` or `leaderboard_fastest_win`. That's the English name
in snake_case, so keep the English names exactly as in the sheets. The *resource
name* column shows what each should come out as.

Until the IDs are in, players still earn achievements. They're kept on the
device and sent on the next sign-in once a build has the IDs. Career bests go
to the leaderboards the same way.

## 5. Test, then publish

- **Configuration > Testers**: add the Google accounts that should see Play
  Games before it's published.
- When it all works, **Review and publish** the Play Games Services config.
  Achievements and leaderboards can't be deleted after publishing.

## How it fits together

- `android_plugin/`: the Java plugin (`AleatroPGS`), built into
  `addons/aleatro_pgs/bin/aleatro_pgs.aar` by `android_plugin/build.sh`. Only
  rebuild it if the Java changes.
- `addons/aleatro_pgs/`: the editor plugin that adds the AAR and
  `play-services-games-v2` to Android exports. Both Android presets use Gradle
  builds for this.
- `scripts/achievements.gd`: the achievement and leaderboard list and goals.
- `scripts/play_games.gd`: talks to the plugin. Off Android it does nothing.
- `make_icons.py` and `make_sheets.py` regenerate the icons and sheets.
