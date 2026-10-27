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

## 2. Properties and languages

Fill in **Configuration > Properties** from [`PROPERTIES.md`](PROPERTIES.md):
display name, category (Card), icon, feature graphic, and the description in
English plus the 9 translations. Adding those translations also adds the
game's languages, which the achievement import needs.

## 3. Achievements: import them all at once

**First add the game's languages.** Translations import only for languages
the Play Games project already has; otherwise the import fails with "Locale
not supported". Go to **Play Games Services > Setup and management >
Configuration** and add translations for Chinese (Simplified) zh-CN, Japanese
ja-JP, Korean ko-KR, German de-DE, French fr-FR, Spanish (Spain) es-ES,
Portuguese (Brazil) pt-BR, Italian it-IT and Arabic ar.

Then go to **Achievements > Import achievements** and upload
[`AchievementsImport.zip`](AchievementsImport.zip). It's in Play Console's
format: `AchievementsMetadata.csv`, `AchievementsLocalizations.csv`,
`AchievementsIconsMappings.csv` and the 30 icons, all flat, with no header
rows. It creates all 30 achievements with:

- **Names and descriptions** (no commas, as the format requires)
- **Points**: 1000 in total, Play Games' limit.
- **Incremental**: Card Sharp, Clean Sweep and Big Spender, each with 2500 steps.
- **Initial state**: Revealed.
- **List order**: as in [`achievements.csv`](achievements.csv).
- **Translations**: zh-CN, ja-JP, ko-KR, de-DE, fr-FR, es-ES, pt-BR, it-IT and
  ar, matching the game's own wording.
- **Icons**: 512×512 with no text, as Play asks.

If a language can't be added, upload
[`AchievementsImport-no-translations.zip`](AchievementsImport-no-translations.zip)
instead. It has the same achievements and icons with no translations; enter
those by hand from `translations.csv` on each achievement.

The import only creates new achievements. It can't translate ones that
already exist, so import before adding any by hand. To rebuild the zip, run
`python3 tools/play_games/make_icons.py`, then
`python3 tools/play_games/make_sheets.py`.

## 4. Leaderboards

There's no import for leaderboards, so add the four by hand.
[`LEADERBOARDS.md`](LEADERBOARDS.md) lists every field for each one, in
order: name, description, icon, ordering (Fastest Win is *Smaller is
better*), score limits and the 9 translations.

## 5. Paste the IDs into the game

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

## 6. Test, then publish

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
