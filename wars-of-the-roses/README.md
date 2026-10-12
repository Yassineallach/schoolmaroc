# حروب الوردتين — motion-graphics documentary

A 4:42 Arabic documentary about the Wars of the Roses, styled as a historical manuscript:
aged parchment, iron-gall ink, red rubric and gold leaf. Every frame is generated in code:
engraved maps, timelines, family trees, battle diagrams, bestiary illustrations, heraldic
symbols and kinetic Arabic typography drawn on an HTML Canvas. It uses no stock footage, photographs or AI images. The
narration is the supplied recording, used unedited as the master timeline.

| | |
|---|---|
| Format | 1920×1080, 16:9, 30 fps, H.264 High + AAC 48 kHz stereo, `+faststart` |
| Narration | `input/narration_main.wav`, 278.07 s, 44.1 kHz mono, used unedited |
| Programme length | 282.5 s (narration + a 4.4 s end card) |
| Music | original procedural underscore (`scripts/make_score.py`), ducked under the voice |

## Outputs

| File | What |
|---|---|
| `output/final_video.mp4` | full documentary, 1080p |
| `output/preview.mp4` | 58 s preview: 0:00–0:36 and 1:52–2:14 of the narration |
| `output/subtitles.srt` | Arabic subtitles (83 cues) built from word timestamps |
| `output/thumbnail.png` | 1280×720 YouTube thumbnail |
| `data/scenes.json` | timestamped scene breakdown: 31 scenes, 7 chapters, cues |
| `data/transcript.json` | sentence- and word-level transcript |
| `data/audio_analysis.json` | format, levels, detected pauses |

The rendered MP4s are git-ignored because they exceed GitHub's file-size limits. Run the
commands below to recreate them.

## How it is built

```
input/            narration_main.wav (master), narration_2.wav (pickup of sentence s19, unused)
data/             words_raw.json (ASR), transcript.json, audio_analysis.json, scenes.json
src/
  index.html      loads the engine; ?dev = live player with audio, ?t=12.3 = single frame
  engine/         core.js (easing, timing, lines), background.js (atmosphere, frame, chapter cards)
  typography/     kinetic Arabic text: feathered RTL reveals, word stagger, rolling years
  components/     symbols.js (crown, roses, sword, shield, seal, castle, banner, sun…),
                  bestiary.js (engraved dragon and frost king), got.js (banners, gears, misc.),
                  diagrams.js (family trees, formations, terrain, arrows)
  maps/           geo.js (simplified coastlines + places), map.js (projection, markers, routes)
  timelines/      timeline.js
  scenes/         01_opening … 08_epilogue — one W.scene(id) per entry in scenes.json
  thumbnail.js
scripts/
  analyze_audio.py   probe audio, sentence segmentation, pauses, transcript.json, subtitles.srt
  make_score.py      synthesises the underscore (no third-party music)
  render.mjs         Playwright + Chromium frame renderer -> FFmpeg (parallel workers)
  validate_video.py  codec/resolution/fps/duration, black & frozen frames, audio peak, contact sheet
```

Rendering is deterministic: `window.renderFrame(t)` draws the frame for time `t` from scratch,
so any frame can be rendered alone and workers can split the timeline between them.

## Requirements

- Node 18+ with Playwright (`npm i` in this folder, or a global install) and Chromium
- FFmpeg with libx264 and AAC
- Python 3 with numpy

## Commands

```bash
python3 scripts/analyze_audio.py                 # rebuild transcript.json + subtitles.srt
node scripts/render.mjs --preview                # output/preview.mp4
node scripts/render.mjs                          # output/final_video.mp4 (≈8 min render + encode)
node scripts/render.mjs --ranges 140-169 --out output/ch3.mp4   # any stretch
node scripts/render.mjs --stills 24.6,152,258    # PNG frames in output/stills/
node scripts/render.mjs --thumbnail              # output/thumbnail.png
python3 scripts/validate_video.py output/final_video.mp4 --expect 282.5
```

Flags: `--workers N` (default 4), `--no-music`, `--no-grain`.

**Live editing:** run `npx http-server -c-1 .` in this folder and open
`http://localhost:8080/src/index.html?dev` (add `&t=140` to jump). The player plays the
narration and draws in real time. Space toggles play/pause; ← and → seek.

## Editing

- **Timing and text:** edit `data/scenes.json`. Each scene has `start`/`end`, `cues` (seconds on
  the narration clock, taken from word timestamps in `transcript.json`) and `text` (every on-screen
  string). Scene code reads these values, so retiming or rewording needs no code changes.
- **Transitions:** set `transition.type` (`dissolve`, `match`, `cut`, `fade-from-black`) and `dur`
  on the incoming scene. Set `camera.z`, `x` and `y` to `[from, to]` for slow drifts and zooms.
- **Look:** the palette and fonts live in `W.C` and `W.F` in `src/engine/core.js`.
  The fonts are Amiri, Reem Kufi and Cinzel, all SIL OFL, in `src/fonts/`.
- **New scene:** add an entry to `scenes.json`, then write `W.scene('id', { draw(ctx, t, S) {…} })`
  in a scene file.
- **Pickup take:** `input/narration_2.wav` re-records sentence s19 (2:35.7–2:40.3). The master
  take is used unchanged. To swap in the pickup, splice it into a copy of the master and point
  `meta.audio` at that copy.

## Historical notes

On-screen text follows the narration and adds only well-attested facts: dates, places and the
names of battles the narration describes without naming. Examples are St Albans 1455, the Act of
Accord 1460, Wakefield 30 Dec 1460, Towton 1461, Barnet and Tewkesbury 1471, Milford Haven
7 Aug 1485 and Bosworth 22 Aug 1485. Battle diagrams are abstract and marked
«رسم توضيحي — المواقع والتشكيلات تقريبية»: they show who fought and who broke, not verified
formations. Where the narration simplifies, the graphics stay accurate without contradicting it:

- Henry Tudor is shown as a *descendant* of John of Gaunt through the Beauforts.
- Lionel, Edward III's second son, appears dimmed in the family tree.

## YouTube

**Title**
حروب الوردتين | الصراع الدموي الذي ألهم «صراع العروش» — وثائقي

**Description**
لم تعرف إنجلترا التنانين ولا الكائنات الجليدية، لكنها عاشت صراعًا دمويًا على العرش بين عائلتين نبيلتين: آل لانكاستر أصحاب الوردة الحمراء، وآل يورك أصحاب الوردة البيضاء.
في هذا الوثائقي المصوَّر بالرسوم المتحركة نتتبع القصة من وفاة إدوارد الثالث عام 1377، مرورًا بالملك الضعيف هنري السادس وطموح ريتشارد دوق يورك، وصعود إدوارد الرابع وانقلاب «صانع الملوك» وارويك، ولغز أميرَي البرج، وصولًا إلى معركة بوسورث عام 1485 وزواج هنري تيودور من إليزابيث يورك الذي وحّد الوردتين.

⏱️ الفصول
0:00 مقدمة
0:30 الجذور
1:27 الملك الضعيف
2:20 صعود يورك
2:48 صانع الملوك
3:20 ريتشارد الثالث
3:49 الوردة الموحّدة
4:22 خاتمة

#حروب_الوردتين #تاريخ #وثائقي #إنجلترا #صراع_العروش #تيودور

**Thumbnail concept** (`output/thumbnail.png`)
An illuminated parchment page: York's white rose on the left and Lancaster's red rose on the
right, a gold-leaf crown between them, and the rubricated title «حروب الوردتين» (حروب in ink,
الوردتين in red) above the kicker «الصراع الذي ألهم «صراع العروش»». Everything is drawn in the
film's own manuscript style.
