---
name: paper-explainer-video
description: Build a YouTube educational explainer video (book summary, history, science, biography) in a Vox-style editorial paper-collage look from the user's narration clips and transcript. Use when the user wants an explainer or summary video made from voice-over audio. It covers the storyboard, a per-episode animated background theme, reference-image asset prompts, clean cut-outs, physical scrapbook animations (photo drops, page flips, unfolding documents, tear reveals, stamps, camera zooms into images) synced to the spoken word, contact-sheet QC and a full-quality 1080p render done by Claude in the session. Triggers include "make a video like the Red Rising one", "explainer video from my narration", "paper collage / Vox style video", "book summary video".
---

# Paper-collage explainer video

Made for the *Red Rising* explainer (7:38, 8 acts, 26 narration clips), then upgraded on
*A Brief History of Time* (4:19, 6 acts, 15 clips) into a fully art-directed motion system.
The same pipeline works for any narrated explainer.

**What the output looks like:**

- an **animated editorial background** per episode: cream paper with grain and fibres, large
  flat textured terracotta and beige shapes anchored to the corners, translucent diagonal
  bands, thin lines and arcs that extend and retract, dot grids that breathe, an open centre;
  its shapes and arrangement are chosen from the episode's subject (`themes.py`);
- photographs and painted plates as **torn prints**, documents, newspaper clippings and
  cut-outs that behave like **physical paper**: they drop, slide with friction, unfold, flip,
  stack, tear and get stamped (`presets.py`);
- a **virtual camera** with three-depth parallax, push-ins and zooms into a single image;
- **word-synced typography**: words rise from their own slot as they are spoken, red labels
  sweep in, marker circles and underlines draw on;
- **torn-paper transitions** between shots, never crossfades;
- every reveal, camera move and cut lands on the spoken word.

**Defaults:** 1920×1080, 30 fps, H.264. The final render uses CRF 12.

## Project layout

Keep everything in one folder; the scripts run from inside it, or set `VOX_PROJECT`.

```
project/
  audio/1.wav 1.txt 2.wav 2.txt ...   narration clips plus the exact transcript of each
  assets/                             APPROVED, leftover-checked images only
  episode.json                        {"theme": "cosmic_atlas"}  the episode's background theme
  timing/words.json, words.txt        created automatically as each act is built
  act1.py act2.py ...                 one file per act (copy templates/act_template.py)
  out/                                renders
```

Install: `pip install pillow numpy scipy faster-whisper cairosvg`, plus `ffmpeg` on PATH.

`SK` below means this skill's folder, e.g. `.claude/skills/paper-explainer-video`.

**Worked example** (`SK/examples`): `brief_history_act1.py` is a complete approved act from *A Brief History of Time*:
- camera moves, presets chosen per beat, word cues;
- manual sound cues;
- an `episode.json` for its theme.

`demo_presets.py` renders a numbered reel of all 12 presets on a project's own assets. Show it to the user when they ask what the animations look like.

**Engine files** (all in `SK/scripts`):

| File | What it holds |
|---|---|
| `vox.py` | fonts, colours, word timing (`make_cue`), documents, marker lines, audio mastering, render |
| `style.py` | `Shot` layers, camera and parallax, torn transitions, `words`, `tag`, `underline`, `kicker` |
| `presets.py` | the 12 physical paper animations and item builders (prints, clippings, text, SVG) |
| `themes.py` | per-episode background themes, all in the editorial design language |
| `bg_motion.py` | the original editorial background, and theme selection from `episode.json` |

## Phases

### 1. Script → acts

- **Read every transcript.** The transcript is the source of truth: every visual must illustrate a line that is actually spoken. Don't invent facts, and don't put numbers on screen that the narration does not state (no ages, no dates, no headlines it doesn't say).
- **Group the clips into acts** of 40–90 s, each with a title.
- **Plan the shots.** For each act, write a shot list: transcript sentence → visual → which assets → which preset → the words that trigger each reveal.

### 2. Storyboard, background theme, asset list

- **Show the storyboard first** on a Design canvas artifact: an overview board plus one board per act. Each shot shows its cue words, the on-screen text, the visual, and whether each asset is drawn in code or needed from the user.
- **Choose the episode's background theme** from the subject (see "Background themes" below), set it in `episode.json`, and show the user a still plus a 15 s preview (`python SK/scripts/bg_motion.py out/bg_preview.mp4 15`) before any act uses it.
- **Split the assets** into:
  - (a) things the code draws (see `references/prompts.md`, "Things code draws better");
  - (b) things to ask the user for: characters, places, creatures, real people.
- **Real people come only from the user's own photographs**, used as torn prints. Never redraw or generate a likeness.

### 3. Asset prompts

- **Ask which tool and which style.** Ask which image tool the user generates with (ChatGPT, Midjourney, others) and whether they have reference images.
- **Reference image plus a short prompt** (see `references/prompts.md`, "Reference-image workflow"). Crop the reference for the user to the single cleanest figure, with no UI, cards or icons.
  - Name only the 4–5 visual traits that matter, and the things in the reference to ignore.
  - Long style descriptions made the results look *nothing* like the references.
- **Give every prompt complete and ready to copy**, one code block per asset, numbered (`P01` plates, `C01` cut-outs). Do the first one alone; once approved, it becomes the style reference for the rest.
- **Plates** say "Fill the whole 16:9 frame edge to edge"; **cut-outs** say "Fill every surface with flat colour, nothing left paper-white. Plain empty ivory background", so the cut survives.
- **Fix with short follow-ups**, one change per message. **Never anime.**

### 4. Cut-outs: check every asset before use

Ask what each image is before cutting it:

- **Has its own painted background** (scenes, plates): use it as a print as-is. Don't cut it out, and don't add a background behind it.
- **A figure on plain ivory**: cut it out.

```
python SK/scripts/cutout.py sheet.png assets/hero_standing.png [--crop x0,y0,x1,y1] --mode standard
python SK/scripts/check_cutout.py out/check.png assets/hero_standing.png ...
```

| Mode | When to use it |
|---|---|
| `standard` | dark or saturated costumes. If eyes, teeth or lamp glass get holed, raise `--head` (0.2–0.35). |
| `gentle` | gold, cream or pale costumes close to the paper colour. |
| `edge` | near-paper skin, faces in close-up, pale animals. Fills holes so nothing shows through. |

**Open the preview and look at it**, on magenta and on dark. Re-cut until both are clean. Only clean files go into `assets/`. This check is not optional.

### 5. Acts, with their word timing

Build the acts one at a time. Word timing is created **together with each act**, not as a separate step:

- When `actN.py` runs `cue = make_cue(CLIPS)`, any clip without timing is aligned on the spot (faster-whisper `small.en`, locally, prompted with the clip's `.txt`) and saved to `timing/words.json` and `timing/words.txt`.
- **Order for each act:** write `CLIPS`; run the act once (the contact-sheet command creates the timing); open `timing/words.txt` (`word@seconds`) to pick cue phrases; write the scenes.
- **Re-align a clip** whose audio or transcript changed: `python SK/scripts/align.py 7`.

Copy `templates/act_template.py` to `actN.py`. Rules:

- **Scenes** are `sX(t, D)` returning a `Shot`. Every reveal uses `w(cue(clip, 'phrase'))`; cuts are `cue(...) - LEAD` in `SHOTS`; `END = cue.total` (last act: `+ 3.0` to hold the end title).
- **Layers — put each thing on the right one:**
  - `s.mid`: the paper on the desk (prints, documents, clippings, cut-outs) **and the marks made on it** (marker circles, stamps). Marks on `s.top` drift off their words when the camera zooms.
  - `s.top`: headline type that is part of the composition.
  - `s.hud`: captions, red labels, the chapter kicker. Fixed to the screen, so camera zooms never push them off-frame.
- **Camera — one purposeful move per shot:**
  - `s.camera(z0, z1, focus0, focus1)`: slow drift across the shot (1.00 → 1.03–1.08).
  - `s.push(at, dz, focus)`: push in when something becomes relevant; the focus stays put.
  - `s.zoom_to(rect, at, dur, fill, back_at=)`: travel from the full composition into one image.
- **Cuts:** the third item of a `SHOTS` entry picks the transition: `'lr'`/`'rl'` torn wipe, `'up'` new sheet laid over. Vary them. Elements already present when a shot opens start at `ENTER`, so the wipe reveals the new composition landing.
- **Typography:** `words(layer, xy, text, size, t, [one cue per word])` (each word rises as it is spoken), `tag(...)` for a red label, `underline(...)`, `kicker(s.hud, t, n, 'Act title')` on the first shot of each act. Big type: 2–4 words. Typed captions (`font=F_TYPE`) are short quotes from the narration.
- **Layout:** one idea per shot; keep decoration-free space in the centre; nothing over the corner shapes that matters (red on terracotta is unreadable).
- **Violence is implied only.**

### 6. Physical scrapbook presets

All in `presets.py`; every one is configurable (position, start, duration, rotation) and takes any RGBA item: `print_card(photo)`, transparent cut-out PNGs, `load('x.svg')`, `text_item('WORD', size)`, `paper_card(...)`, `clipping(...)`, `document(...)`.

| # | Preset | Use it when the narration… |
|---|---|---|
| 1 | `page_flip` | turns to a new chapter, a book is opened, "least finished" |
| 2 | `drop` | introduces a photograph or person |
| 3 | `unfold` | reads out a record, letter, diagnosis, chart |
| 4 | `clipping` + `slide` | mentions publication, the press, a public event |
| 5 | `tear_reveal` | reveals who or what something is ("The man is…") |
| 6 | `stack` | lists people, years, editions, evidence |
| 7 | `stamp_hit` | gives a verdict, a date, a refusal (pass `shot=s` for the kick) |
| 8 | `mask_reveal` | opens an act or a memory: the image appears through a torn hole |
| 9 | `slide` | moves a document into the story ("Back in England sits…") |
| 10 | `assemble` | something comes together or breaks apart (`reverse=True`) |
| 11 | `flip` | a before/after: young → old, theory → result |
| 12 | `Shot.zoom_to` | the camera should single out one image from the composition |

**Do not animate everything at once.** One physical action per beat, chosen by what the narration is doing; the rest of the frame stays still or drifts. Mix durations (0.8–1.6 s) so nothing feels repetitive.

### 7. Background themes

Every episode gets its own background, but every theme speaks the design language of the user's original editorial background: the same paper, flat textured terracotta + beige corner shapes, translucent diagonal bands, thin dark lines and arcs, breathing dot grids, an open centre. Only the shapes and their arrangement change with the subject. Do not invent a new visual style (dark grounds, heavy patterns) unless the user asks.

| Theme | Subject | Its own shapes |
|---|---|---|
| `editorial` | default | the original reference: circles, bands, blocks |
| `cosmic_atlas` | science + space + biography | sun with orbit arcs and a travelling moon, light-cone bands, ringed planet |
| `archive` | history | newspaper block, wax seal, sloping band |
| `laboratory` | science | hexagons, molecule, terracotta triangle |
| `clinic` | medicine | cell circles, capsule, cross, travelling heartbeat |
| `circuit` | technology | stacked blocks, circuit lines with a travelling dot |
| `album` | biography | tilted prints with tape, photo corners |
| `deep_space` | space | indigo planet with orbits, small terracotta moon |
| `ledger` | economics | bar blocks, line chart, ledger block |

**New theme:** add a `Theme(name, label, [elements], paper_colour, seed)` in `themes.py` from the element vocabulary (`shape`, `terra`, `hline`, `vline`, `dots`, `orbiter`, `tracer`, `diag`). Keep big shapes off the centre, keep terracotta as the accent, give every element its own drift period (20–45 s). Show the user a board of themes and a 15 s preview before using it.

### 8. Sound effects

Effects are generated in code (`sfx.py`) and synced automatically: every preset and helper registers a sound event when it draws, with its time and screen position.

| Event | Sound | Registered by |
|---|---|---|
| `drop` | air swish, papery slap on landing | `drop`, `stack`, `Photo.place` |
| `slide` | friction rustle that slows with the sheet | `slide`, `unfold` (entry) |
| `unfold` | two crisp creases | `unfold` |
| `tear` / `reveal` | paper rip (fibre crackle) / slow gentle tear | `tear_reveal` / `mask_reveal` |
| `wipe` / `sheet` | quick rip / sheet sliding over | transitions `'lr' 'rl'` / `'up'` |
| `stamp` | descent hiss, wooden thud, rubber knock | `stamp_hit` |
| `flip` / `pageflip` | swish and tap / whoosh, rustle, flap | `flip` / `page_flip` |
| `assemble` | light taps as pieces lock | `assemble` |
| `type` | typewriter keys, one per letter | typed captions (`words(..., font=F_TYPE)`), `kicker` |
| `marker` / `swipe` | felt-tip scratch | `underline` / `tag` |
| `zoom` | soft low air swell | `Shot.zoom_to` |
| `beep`, `tick` | soft monitor beep, tiny click | manual only |

- **Manual cues** for things presets don't know about (marker circles, strikes, story sounds): `sfx('marker', w(cue(1, 'word')), x)` inside the scene.
- **Mix:** each sound is varied per event (seeded, deterministic), panned to its x position, summed at −13 dB, and ducked by 9 dB while the narration speaks. Target: effects about 20 dB below the voice (stem ≈ −37 LUFS against −16), loudest stamp peak ≈ −16 dBFS. The user found −10 dB under the voice too loud: keep effects subtle.
- `render_all.py` mixes them in automatically. `VOX_SFX=0` turns them off; `VOX_SFX_DB` sets the level (default `-13`; `-17` quieter, `-9` louder). The stem alone is written next to the mix as `mix.wav.sfx.wav`.
- **Add audio to an already-rendered act** without re-rendering the picture: `vox.collect_events(act.frame, act.END)`, `sfx.mix_into(narration_wav, events, out_wav)`, then mux with `ffmpeg -c:v copy`.
- **Sound must not contradict the story.** No flat-line tone when the patient survives, no gunshots for implied violence.

### 9. QC before rendering

```
cd project && PYTHONPATH=SK/scripts:. python act1.py sheet out/act1_sheet.png 2 6 10 15 22
```

**Look at the contact sheet.** Pick moments just after each reveal **and** moments mid-transition and mid-preset. Check for:

- cut-out leftovers;
- text overlapping a figure, running off-frame, or red text on a terracotta shape;
- marks (circles, stamps) still sitting on their words during camera moves;
- a black edge during a zoom (the background must always cover the frame);
- empty frames revealed by a wipe (use `ENTER` for elements present at the cut);
- anything on screen the narration does not say.

Fix, re-check. Show the user sheets or a draft per act and get approval before moving on.

### 10. Render: Claude renders the final, in this session

```
cd project && python SK/scripts/render_all.py --acts 3 --draft   # review render of one act
cd project && python SK/scripts/render_all.py                    # FINAL: CRF 12, slow, 320k AAC, all acts
```

- **Run renders in the background** (Bash `run_in_background`) and wait for the completion notice; don't poll with sleep. With the full motion system an act renders at roughly 13 s of render per 1 s of video per process.
- Don't run two renders at once on a small machine; queue the second behind the first.
- **Act drafts:** after each act is approved on its contact sheet, render a `--draft` and send it with `SendUserFile`.
- **Final:** all acts, CRF 12, joined losslessly into `out/full.mp4`, narration mastered to −16 LUFS. Check the duration with ffprobe, spot-check frames, then send it.
- **Files over 100 MB** stay out of git. Send them directly.

## Rules learned from the user (keep them)

1. Base everything on the transcript.
2. Ask for assets that would look bad drawn in code.
3. Storybook / editorial illustration, never anime, in prompts and in what you accept.
4. Check every asset for background leftovers before using it (magenta check).
5. Never add a background behind an image that already has one.
6. The film should feel like an explainer, not a movie: paper collage, documents and type carry the ideas.
7. Every cut, reveal and camera move lands on the word it illustrates.
8. Real-person likeness comes only from images the user provides, shown as photo prints.
9. Claude renders the final at full quality in the session and sends the file.
10. Create word timing as each act is built, never as a separate pass afterwards.
11. Asset prompts are short, lean on a reference image, and are given complete and ready to copy.
12. **The user approves visual changes before they go into the film.** Build a preview (still, 15 s clip or demo reel) and wait for the go-ahead before re-rendering acts.
13. Backgrounds follow the user's original editorial design language; each episode gets a fresh arrangement of it, never a different style.
14. No grey torn-paper strip along the bottom: the corner shapes anchor the frame.
15. Elements behave like physical paper (lift, shadow, overshoot, settle); never PowerPoint-style fades or flat slides.
16. Sound effects stay subtle: about 20 dB under the voice (the first mix at 10 dB under was too loud). Change single sounds or the level by remixing the audio only, never by re-rendering the picture.
