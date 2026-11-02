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

**Worked example** (`SK/examples`): the six approved acts of *A Brief History of Time* (4:19), with their `episode.json`. Read the act closest to the beat you are building:

| File | Shows |
|---|---|
| `brief_history_act1.py` | mask reveal opening, unfold + zoom into a chart, tear reveal of a person, clipping + stamp; manual monitor beeps |
| `brief_history_act2.py` | equations struck out, a book stack halving, portraits stacked on a timeline, zoom into a plate, dots expanding then rewinding to a point |
| `brief_history_act3.py` | a card torn in two, a bending grid with a planet, an atom dissolving into a cloud, two cards colliding, plate → plate `flip`, event horizon circled after `zoom_to` |
| `brief_history_act4.py` | glow + particles + shrinking disc, diagnosis unfold, shapes `assemble`, letter-card highlight, young → old photo `flip` beside a word screen |
| `brief_history_act5.py` | a cup sliding off a table and shattering, `assemble` then `reverse` + NEVER SEEN stamp, a card flipped on its head, globe with marker arrow and loop |
| `brief_history_act6.py` | typed title struck and corrected, a counter, stacked covers, `page_flip` with a bookmark, crowd + unfold, end title held over the last plate |

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
- **Check each image as it arrives** and say what it will carry. One plate can serve two beats (the collapsing star also became the start of the black-hole `flip`).
- **Don't wait for every asset.** Build the act and use a code-drawn stand-in in the background's flat-shape style, loaded only while the file is missing, so the real asset swaps in by itself:
  `P.load(asset('c01_planet.png')) if os.path.exists(asset('c01_planet.png')) else stand_in()`.
  Never stand in for a person, an animal or a landscape.

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

**Already transparent?** ChatGPT often returns RGBA PNGs with the background already removed (they look black or glowing in chat previews). Check the alpha first (`Image.open(f).mode == 'RGBA'` and transparent corners); if so, skip `cutout.py` but still run `check_cutout.py` and look at it. Pale highlights inside a figure can raise the flag count without being leftovers.

### 5. Acts, with their word timing

Build the acts one at a time. Word timing is created **together with each act**, not as a separate step:

- When `actN.py` runs `cue = make_cue(CLIPS)`, any clip without timing is aligned on the spot (faster-whisper `small.en`, locally, prompted with the clip's `.txt`) and saved to `timing/words.json` and `timing/words.txt`.
- **Order for each act:** write `CLIPS`; run the act once (the contact-sheet command creates the timing); open `timing/words.txt` (`word@seconds`) to pick cue phrases; write the scenes.
- **Re-align a clip** whose audio or transcript changed: `python SK/scripts/align.py 7`.
- **Check every clip is complete.** Whisper can skip speech that matches its transcript prompt word for word (clip 13 of the Hawking film came back with 19 of 61 words). `align.py` now retries automatically when it gets under 80 % of the transcript, but compare word counts after aligning anyway:
  `python -c "import json;t=json.load(open('timing/words.json'));[print(k,len(v),len(open(f'audio/{k}.txt').read().split())) for k,v in sorted(t.items(),key=lambda x:int(x[0]))]"`
- **Cue pitfalls:** `cue()` finds the *first* occurrence, so a repeated word needs its number (`cue(11, 'one', 2)` when "no one" comes before "one-way"). Hyphenated words split into separate tokens (`one`, `-way`). Punctuation is ignored, so `'Pole.'` and `'Pole'` match the same word.

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
| `shatter` | porcelain click, bright crackle, skittering bits | manual only (the teacup in Act 5) |
| `beep`, `tick` | soft monitor beep, tiny click | manual only (counters, ticking clocks, letter-card hops) |

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
- **text over a dark plate**: black type disappears on a zoomed plate; use `tag(...)` (red label, or `bg=CREAM, fg=INK`);
- **missing glyphs**: Archivo Black has no `→` (it renders as a box); `÷`, `²`, `’` and `,` are fine. Write words instead of rare symbols;
- **glows on cream**: a cream or white glow is invisible on the paper; use a warm terracotta glow;
- **contrast**: terracotta text on cream and cream text on red labels pass only as large text (check with `python3 .claude/skills/antislop-human/contrast-check.py "#CD5830" "#F8E7CD"`), so red text stays large (≥ 40 px) and never carries small captions;
- anything on screen the narration does not say.

Fix, re-check. Show the user sheets or a draft per act and get approval before moving on.

### 10. Render: Claude renders the final, in this session

```
cd project && python SK/scripts/render_all.py --acts 3 --draft   # review render of one act
cd project && python SK/scripts/render_all.py                    # FINAL: CRF 12, slow, 320k AAC, all acts
```

- **Run renders in the background** (Bash `run_in_background`) and wait for the completion notice; don't poll with sleep. Measured on 4 cores: a 40–48 s act drafts in 7–9 min; `--acts 5 6` renders two acts in parallel in about 9 min.
- **Don't chain renders with a background waiting loop** (`while ! grep Done ...; do sleep; done; render`). On the Hawking film the waiter died silently at its time limit and two acts never rendered. Start the next render yourself when the completion notice arrives, or render several acts in one `render_all.py --acts ...` call.
- **Before telling the user a render is running, check it is**: `ps aux | grep render_all` and look for the output file.
- **Draft of the whole film:** `out/acts.txt` lists the act files; `ffmpeg -f concat -safe 0 -i out/acts.txt -c copy out/full_draft.mp4` joins them losslessly. An act whose audio was remixed separately (e.g. `act1_sfx.mp4`) can be copied over its act file first.
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
17. Never report work as running or done without checking it (process list, output file, duration). If something silently failed, say so plainly and restart it.
18. Every word on screen must be readable on what is behind it: label backings over dark plates, large size for red text, no missing glyphs.
