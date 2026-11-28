# Quintessence: Cycle I slice (Godot 4.7, Android)

A tarot-reading roguelike deckbuilder. You lay Minor Arcana into a Three-Card Spread to satisfy three Querents by candlelight. This build is the **Cycle I vertical slice** of the design document *Quintessence: Game Design Document v1.1*.

## What is playable

- Title, then a choice of 1 of 3 Patron Major Arcana
- Three Querents: **The Curious** (600), **The Troubled** (900, Shadow), **The Twin** (1200, boss rule plus Shadow)
- Each Night: hand of 8, 4 Readings, 3 Reshuffles
- Readings: Glimpse, Echo, Path, Triad, Harmony, Court Assembly, River
- Positions: Past (Light x2), Present (+2 Gravity, +3 for a Court), Future (Light x1/2, card returns to hand). An Ace doubles the next card's Light.
- Score: Light x Gravity, with a live preview before you commit
- 8 Major Arcana: Magician, Empress, Lovers, Hermit, Death, Tower, Star, Sun
- The Shadow: shows its target one Reading ahead, then eclipses that position
- Market after each win: 2 Majors, 2 Minor cards, 1 Sigil; reroll; sell
- Win and defeat screens with stats, a one-tap restart, and an autosave after every action (title → Continue)
- Android back button returns to the title (the run is saved)

## Controls (touch)

| Action | How |
|---|---|
| Lay a card | Tap it (fills the first open position) or drag it onto Past / Present / Future |
| Take a card back | Tap it in the spread |
| Read | **Read** button |
| Reshuffle | **Reshuffle**, tap the cards to give back, then **Give back** |
| Arm The Tower / read an Arcana | Tap the Arcana card above the score row |
| Animation speed | **speed** tag, top right (x1, x2, x4, skip) |

## Visual direction

The look is authored from the written direction; no image references were used.

- A single candle is the only light. Its flame height shows Insight ÷ target, and the room gets brighter as you close in on the target.
- Light is gold leaf, Gravity is ink on a paper slip, and the final Insight is pressed into a vermilion wax seal.
- Cards are procedural woodcut prints on bone paper. The Shadow appears as spreading ink.

See `style.json`.

## Layout

```
quintessence/
  app/                     Godot 4.7 project (open this folder in Godot)
    scripts/rules/         pure game rules (no rendering): cards, readings, scoring, arcana, run_state
    scripts/view/          rendering + input: main, card_view, table_view, querent_view, candle_view, fx_view, hud, art
    shaders/               room, darkness (candlelight), flame
    tests/run_tests.gd     headless rules tests + bot that plays full runs through RunState
    tests/driver.gd        drives the real game with pointer events, captures screenshots + input trace
    export_presets.cfg     Android preset (arm64-v8a + armeabi-v7a, debug-signable)
  case.json style.json game.json assets.json review.json   reference-to-game contracts
  review/                  screenshots, traces, test logs
  build/                   APK output (not committed)
```

## Run and test

```bash
# Rules tests (headless)
godot --headless --path app --import
godot --headless --path app -s res://tests/run_tests.gd

# Full input-driven playthrough with screenshots (needs a display; Xvfb works)
xvfb-run -s "-screen 0 720x1280x24" godot --path app --rendering-driver opengl3 \
  --resolution 720x1280 res://tests/driver.tscn -- --out=$PWD/review/run
```

## Build the Android APK

Requirements: Godot 4.7.2 with its export templates, Android SDK (platform-tools, build-tools 35, platform 35) and JDK 17 or newer.

In Godot: **Editor Settings → Export → Android**, then set the Android SDK path, the Java SDK path and a debug keystore. Then:

```bash
godot --headless --path app --export-debug "Android" ../build/quintessence-debug.apk
adb install -r build/quintessence-debug.apk
```

A Play Store release needs a release keystore. Set `keystore/release` in the preset, then use `--export-release`.

## Known limits of this slice

- Only Cycle I. Orientation (reversed cards), Elemental Dignities, the Thread/Fate, Quintessence numerology, Wagers, Debt and Signs unlock in later Cycles and are not built yet.
- No audio.
- Card art is procedural (emblems), not illustrated.
- Targets were tuned with a bot that searches every play (it clears Cycle I in about 95% of runs). Human difficulty still needs playtesting.
- No reduced-motion setting yet. The **skip** speed removes most of the motion.

Fonts: IM Fell English / English SC / DW Pica and Playfair Display, all under the SIL Open Font License (`app/assets/fonts/`).
