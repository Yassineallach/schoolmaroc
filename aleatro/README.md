# Aleatro

A landscape poker roguelike for Android, built with **Godot 4.7** (GL Compatibility renderer).
Package id: `com.mardev.Aleatro`.

Play poker hands to beat a score target. Score = Chips x Mult. Each ante has a Small Blind,
a Big Blind and a Boss Blind with a twist. Beat ante 8 to win, then keep going in Endless mode.
Spend your winnings in the shop on **Charms** (passive bonuses, 5 slots) and **Runes** (level up a hand type).

Art is drawn in code. Audio is original and synthesized offline by two scripts in `tools/`:

- `python3 tools/make_music.py` renders the three music loops to `audio/`.
- `python3 tools/make_sounds.py` renders the sound effect library to `audio/sfx/`
  (about 60 files: UI, cards, scoring, money, bosses, Ace's voice, two ambient loops).

Both need numpy and ffmpeg with libvorbis. The game loads every `.ogg` in `audio/sfx/`
automatically; a file's name is its sound code, and `name_1`, `name_2`, ... are random variations.

## Layout

| Path | Purpose |
| --- | --- |
| `scripts/data.gd` | Hand table, ante targets, charm and boss definitions |
| `scripts/poker.gd` | Poker hand evaluation |
| `scripts/scoring.gd` | Charm effects; builds the per-hand scoring events |
| `scripts/game_state.gd` | Run state: deck, money, blinds, shop rolls |
| `scripts/main.gd` | UI, animations, round/shop flow |
| `scripts/card_view.gd`, `charm_view.gd` | Card and charm views (layers enhancements, seals, editions over the face) |
| `scripts/deck_art.gd` | The pixel deck: corner indices, traditional pip layouts, big ace pips and double-ended court figures, painted at 50x70 and drawn at 2x |
| `scripts/sfx.gd` | Synthesized sound effects |
| `scripts/ui_build.gd` | Declarative menu builder: rows, columns, grids, live text and bars, delayed/hold/once buttons, choice tabs, tooltips |
| `scripts/glide.gd` | Spring mover for cards and charms: chases a target with slight overshoot, leans into fast moves, wobbles when kicked; honours Reduced motion |
| `scripts/motes.gd` | Pixel-square particle emitter: bursts and steady trickles, point or area spawn, drag and gravity, fade-out, prewarm |
| `scripts/debug_boxes.gd` | Developer overlay (F3, or tap the credits line 5 times): outlines every input area in its real rotated shape, coloured by hover / focus / moving, with an fps and node readout |
| `scripts/prof.gd` | Section profiler (calls, avg / max ms, share of time); shown in the debug overlay, F4 clears |
| `scripts/tilt.gd` | Pointer tilt for cards and charms: the face leans away from a hovering mouse or pressing finger (card_fx.gdshader) |
| `scripts/save_check.gd` | Validates a loaded run before resuming (types, ranges, known ids); repairs the profile field by field |

## Building the Android package

Requirements: Godot 4.7.x with export templates, JDK 17+, Android SDK (platform-tools, build-tools 35+).
Set `export/android/android_sdk_path` and `export/android/java_sdk_path` in the Godot editor settings.

Release signing is read from environment variables so the keystore never enters the repo:

```sh
export GODOT_ANDROID_KEYSTORE_RELEASE_PATH=/path/to/aleatro-release.keystore
export GODOT_ANDROID_KEYSTORE_RELEASE_USER=aleatro
export GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD=...

# APK (direct install)
godot --headless --export-release "Android" build/Aleatro.apk

# AAB (Google Play) - needs the Gradle build template once:
#   Project > Install Android Build Template (or unzip android_source.zip into android/build)
godot --headless --export-release "Android AAB" build/Aleatro.aab
```

Bump `version/code` and `version/name` in `export_presets.cfg` for every store release.
