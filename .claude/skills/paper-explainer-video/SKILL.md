---
name: paper-explainer-video
description: Build a YouTube educational explainer video (book summary, history, science, biography) in a Vox-style editorial paper-collage look from the user's narration clips and transcript. Use when the user wants an explainer or summary video made from voice-over audio. It covers the storyboard, a visual identity art-directed for each topic (colour roles, textures, type, image treatment, mood arc), varied scene environments and compositions, a per-episode animated background theme, reference-image asset prompts, clean cut-outs, physical scrapbook animations (photo drops, page flips, unfolding documents, tear reveals, stamps, camera zooms into images) synced to the spoken word, contact-sheet QC and a full-quality 1080p render done by Claude in the session. Triggers include "make a video like the Red Rising one", "explainer video from my narration", "paper collage / Vox style video", "book summary video".
---

# Paper-collage explainer video

Made for the *Red Rising* explainer (7:38, 8 acts, 26 narration clips), then upgraded on
*A Brief History of Time* (4:19, 6 acts, 15 clips) into a fully art-directed motion system.
The same pipeline works for any narrated explainer.

**What the output looks like:**

- a **visual identity art-directed for the topic**: the engine reads the transcript and builds
  colours (17 roles + chart series), paper texture, image treatment, typefaces and preferred
  scenes from ten identities, their variants, the region, the period and the tone, so a WWII
  film, a dark manga and a film on AI look nothing alike (`identities.py`, `palette.py`);
- **every scene its own editorial page**: archive paper, dark grounds, full-bleed images,
  split screens, full-screen type, infographic grids, halftone panels, solid colour, chosen
  per sentence and never repeated back to back, with moods that tone scenes inside the
  identity (`scenes.py`);
- an **animated editorial background** per episode, used as one of those grounds: paper with
  grain, large flat textured shapes anchored to the corners, translucent bands, lines and arcs
  that extend and retract, dot grids that breathe, an open centre (`themes.py`);
- photographs and painted plates as **torn prints**, documents, newspaper clippings and
  cut-outs that behave like **physical paper**: they drop, slide with friction, unfold, flip,
  stack, tear and get stamped (`presets.py`);
- a **virtual camera** with three-depth parallax, push-ins and zooms into a single image;
- **word-synced typography**: words rise from their own slot as they are spoken, red labels
  sweep in, marker circles and underlines draw on;
- **torn-paper transitions** between shots, never crossfades;
- every reveal, camera move and cut lands on the spoken word.
- **real images first**: museum objects, excavation and archive photographs from Wikimedia Commons, credited, with generated drawings only for what was never photographed;
- **no empty screens**: something is on screen from the first frame of every shot (`check_empty.py`);
- **made by an editor, not a template**: a hook in the first seconds, images that speak without labels, varied rhythm, restraint in effects, a music bed, honest captions (see "Craft" below, `check_pacing.py`, `music.py`).

**Defaults:** 1920×1080, 30 fps, H.264. The final render uses CRF 12.

## Project layout

Keep everything in one folder; the scripts run from inside it, or set `VOX_PROJECT`.

```
project/
  audio/1.wav 1.txt 2.wav 2.txt ...   narration clips plus the exact transcript of each
  assets/                             APPROVED, leftover-checked images only
  episode.json                        {"subject": "...", "theme": "cosmic_atlas"}  one-line topic + background theme;
                                      "palette" defaults to "auto" (identity from the topic), or name one
  timing/words.json, words.txt        created automatically as each act is built
  act1.py act2.py ...                 one file per act (copy templates/act_template.py)
  out/                                renders
```

Install: `pip install pillow numpy scipy faster-whisper cairosvg`, plus `ffmpeg` on PATH.

`SK` below means this skill's folder, e.g. `.claude/skills/paper-explainer-video`.

**Worked example** (`SK/examples`): the six approved acts of *A Brief History of Time* (4:19), with their `episode.json`, and the first approved acts of *Histoire des armes* (5:34, French narration, real images from Commons, the astrolabe background), the reference for history films. Read the act closest to the beat you are building:

| File | Shows |
|---|---|
| `brief_history_act1.py` | mask reveal opening, unfold + zoom into a chart, tear reveal of a person, clipping + stamp; manual monitor beeps |
| `brief_history_act2.py` | equations struck out, a book stack halving, portraits stacked on a timeline, zoom into a plate, dots expanding then rewinding to a point |
| `brief_history_act3.py` | a card torn in two, a bending grid with a planet, an atom dissolving into a cloud, two cards colliding, plate → plate `flip`, event horizon circled after `zoom_to` |
| `brief_history_act4.py` | glow + particles + shrinking disc, diagnosis unfold, shapes `assemble`, letter-card highlight, young → old photo `flip` beside a word screen |
| `brief_history_act5.py` | a cup sliding off a table and shattering, `assemble` then `reverse` + NEVER SEEN stamp, a card flipped on its head, globe with marker arrow and loop |
| `histoire_armes_act1.py` | *Histoire des armes* (French narration, history identity, astrolabe background, real Commons photos): mask reveal of a real site photo + name card, strikes on spoken words, full-bleed excavation photo, a spear strip cut from a photo with a measuring line, term card, timeline on archive, distance diagram, a row of real objects for "succession" |
| `histoire_armes_act2.py` | the user's ChatGPT ink drawing printed on the parchment (`cutout.ink_image`), a camera move into that plate instead of a diagram, wood breaking apart beside a stone that stays, map zoom to a town, a number struck and corrected, a public-domain engraving as an ink cut-out, a real object with its detail circled |
| `histoire_armes_*.json` | that film's `episode.json`, Commons `sources.json` and `picks.json` |
| `brief_history_act6.py` | typed title struck and corrected, a counter, stacked covers, `page_flip` with a bookmark, crowd + unfold, end title held over the last plate |

`demo_presets.py`, `demo_annotate.py`, `demo_toolkit.py`, `demo_typo.py` and `demo_scenes.py` render numbered reels of the presets, the annotations, the storytelling toolkit (maps, timeline, charts, objects, camera, transitions), the typography system and the scene environments on a project's own assets. Show one to the user when they ask what the animations look like. `demo_palettes.py <out_dir>` (or `scripts/identity_board.py --all`) renders the visual identity guide: a page per identity, an overview, and identities derived from sample topics.

**Engine files** (all in `SK/scripts`):

| File | What it holds |
|---|---|
| `vox.py` | fonts, base colours (from the identity), word timing (`make_cue`), documents, marker lines, audio mastering, render |
| `style.py` | `Shot` layers, camera and parallax, torn transitions, `words`, `tag`, `underline`, `kicker` |
| `presets.py` | the 12 physical paper animations and item builders (prints, clippings, text, SVG) |
| `annotate.py` | editorial annotations: marker sweeps, underlines, rings, boxes, strikes, emphasis, arrows, spotlight, loupe, marks, brackets, connectors, charts |
| `transitions.py` | special cuts: page turn, circle, shape wipe, zoom-through, collage (the torn wipes stay in `style.py`) |
| `maps.py` | animated maps from bundled Natural Earth data (`assets/geo`): zooms, routes, pins, borders, map cards |
| `timeline.py` | timelines: axis, dated events, eras, a sliding date marker, rolling year counter |
| `charts.py` | line charts, comparisons, unit grids, counters, flow diagrams, size comparisons |
| `objects.py` | newspapers, letters, envelopes, polaroids, sticky notes, tape, push pins, spin-in |
| `typo.py` | editorial typography: a 10-role hierarchy (English + Arabic), 12 kinetic animations, newspaper / big-number / term / name compositions |
| `identities.py` | design tokens of the ten visual identities (17 HEX colour roles, chart series, texture, image treatment, type, scene preferences, variants) plus regions and periods |
| `palette.py` | the identity engine: topic analysis, identity derivation, contrast repair, image treatment, scene moods |
| `identity_board.py` | the visual identity guide: a page per identity, an overview, and a board of identities derived from sample topics |
| `scenes.py` | scene environments (theme, paper, cream, charcoal, solid accent, halftone, archive, geometric, grid, full-bleed) and compositions (full-bleed, split screen, full-screen type, panel grid, letterbox, thirds) |
| `storyboard.py` | narration analysis: the episode identity and why, then purpose, mood, environment, technique, weight, cue, cut and typographic moment for every sentence |
| `themes.py` | per-episode background themes, all in the editorial design language (each maps to an identity family) |
| `bg_motion.py` | the original editorial background, and theme selection from `episode.json` (none named: the identity's default, e.g. history → `astrolabe`) |
| `commons.py` | real images from Wikimedia Commons: search per slot with contact sheets, download with credits, a table of links for the user to download by hand |
| `check_pacing.py` | the pacing and variety check: shot lengths and their spread, repeated environments and cuts, how many shots carry text, text-heavy frames, effect budgets, images used too often or multiplied, a title before the hook, real images without a caption |
| `music.py` | lays a music bed under a finished film (looped, faded, ducked by the voice) without re-rendering the picture |
| `check_empty.py` | the no-empty-screens check: flags every stretch where a shot shows only its ground |
| `brand.py` | channel branding: the official SVG logo, watermark, reveal, signature, subscribe / like / comment / share / next-video CTAs, CTA placement from the narration's pauses, the YouTube end screen (config: `brand/brand.json`) |

## Phases

### 1. Script → acts

- **Read every transcript.** The transcript is the source of truth: every visual must illustrate a line that is actually spoken. Don't invent facts, and don't put numbers on screen that the narration does not state (no ages, no dates, no headlines it doesn't say).
- **Group the clips into acts** of 40–90 s, each with a title.
- **Analyse the narration first:** `python SK/scripts/storyboard.py --all` (from the project folder) reads every sentence and proposes, for each:
  - **purpose:** what the sentence does: date, number, fraction, place, journey, person, people, quote, comparison, process, list, correction, document, reveal, detail, action, emotion, or plain idea;
  - **technique:** from the whole toolkit, with no repeat in a row and no special technique twice within three shots;
  - **weight:** complex, medium or simple, alternated so the film breathes; emotional lines are always simple;
  - **cue word and time,** and a **cut** into the shot.
  It also writes `timing/plan.md`. Read it as advice: fix what it misreads and keep what the user asked for.
- **Plan the hook first.** The first 10 seconds decide whether the viewer stays. Open on the film's strongest image, full frame, with the narration's first line; no chapter label, title card or logo before something has happened (the act 1 kicker waits until the second shot or is dropped). If the narration's opening line is weak, tell the user and suggest moving a stronger line or the closing question to the front as a cold open, before they record.
- **Plan one returning motif and the ending.** Pick one visual idea that comes back transformed (on *Histoire des armes*, the HUMAIN → DANGER distance line returned longer for gunpowder, then as DÉCISION → CONSÉQUENCES). Make the last image answer the first (the hand on the spear answers the spear in the mud). A film that closes its own loop feels authored.
- **Plan the shots.** For each act, write a shot list: transcript sentence → visual → which assets → which technique → the words that trigger each reveal. Some moments get complex motion graphics; many should stay simple (one image, a slow push, a few words).

### 2. Storyboard, visual identity, background theme, asset list

- **Show the storyboard first** on a Design canvas artifact: an overview board plus one board per act. Each shot shows its cue words, the on-screen text, the visual, and whether each asset is drawn in code or needed from the user.
- **Settle the episode's visual identity** (see "Visual identity" below). Put a one-line `"subject"` in `episode.json`. `storyboard.py` prints the identity the engine derived and why. Override it if needed (`"palette": "crime/historical"`), and show the user its page: `python SK/scripts/identity_board.py --page <identity> out/identity.png`.
- **Choose the episode's background theme.** History films use `astrolabe` by default (it is chosen automatically when `episode.json` names no theme). Otherwise pick one from the same identity family as the visual identity (`identities.THEME_IDENTITY`; a mismatched theme is replaced by the identity's paper) and the subject (see "Background themes" below), set it in `episode.json`, and show the user a still plus a 15 s preview (`python SK/scripts/bg_motion.py out/bg_preview.mp4 15`) before any act uses it.
- **Split the assets** into:
  - (a) things the code draws (see `references/prompts.md`, "Things code draws better");
  - (b) **real images**: objects, artefacts, sites, documents, paintings and archive photographs that exist (see phase 3);
  - (c) generated drawings, only for what no photograph can show (prehistoric scenes, reconstructions, a symbolic close-up);
  - (d) things only the user can give: photos of real people.
- **Real people come only from the user's own photographs**, used as torn prints. Never redraw or generate a likeness.

### 3. Images: real first, then prompts

**Use a real image whenever one exists.** The user prefers real photographs, museum objects, archive pictures and public-domain paintings to generated pictures. Generated drawings are only for what was never photographed.

1. **Search Wikimedia Commons.** Write `sources.json` (slot → 2–3 queries, in English and in the subject's language), then:
   `python SK/scripts/commons.py search sources.json out/commons`
   It keeps only public domain, CC0, CC BY and CC BY-SA files and draws one contact sheet per slot (`out/commons/<slot>.jpg`). It pauses between slots, honours `Retry-After` and resumes where it stopped, so run it in the background.
2. **Pick by looking at the sheets.** Choose what shows exactly what the sentence says (the real Schöningen spear, a sword found in the Thames), not something merely related. Avoid photos of people unless the user agrees. Record picks in `picks.json` (`{"P02": "File:..."}`).
3. **Download:** `python SK/scripts/commons.py get P02 "File:..."` (saves `assets/P02.jpg` and its credit).
4. **When Commons rate-limits this machine** (HTTP 429 is common on shared cloud IPs), don't wait: give the user the links and let them download.
   `python SK/scripts/commons.py links` prints a table of every pick not yet in `assets/`: the code to save it as, the file page and the **direct file link** (the direct link opens the original image; a file page can show a different picture first). Put each link in a markdown link or a code block so it doesn't break across lines. When the user uploads the files, save them under their codes and record the credits with `python SK/scripts/commons.py credit P02 "File:..."`.
5. **Nothing free found?** Tell the user which slots have no public-domain or freely licensed image, and **ask them to search** (museum sites, Europeana, Gallica, the Met open access, their own photos) before falling back to a generated drawing.
6. **Credits are mandatory** for CC BY and CC BY-SA: `assets/credits.json` feeds a `CREDITS.txt` the user pastes into the video description. **No credits card in the video** unless the user asks for one (the user's choice on *Histoire des armes*). For images the user found and uploaded, ask for the file page link so the author and licence can be recorded.

Real images get the identity's treatment (sepia duotone in history) and are placed as torn prints, full-bleed plates or split screens like any other image.

**Generated drawings** (only for what remains):

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
| `ink` | pen-and-ink or engraved line art on white: the paper becomes transparent and the lines take the identity's ink, so the drawing reads as printed on the film's paper. Add `--backed` to fill the silhouette with light paper when the object overlaps other things. |

**Open the preview and look at it**, on magenta and on dark. Re-cut until both are clean. Only clean files go into `assets/`. This check is not optional.

**Ink drawings and engravings** (the user's ChatGPT ink plates, public-domain engravings): `cutout.py --mode ink`, or in code `cutout.ink_image(asset('P03.png'), 1800)`, which returns the drawing as RGBA with transparent paper and the identity's ink, ready for `mask_reveal`, `slide`, `drop`. A full-frame ink plate printed this way sits on the film's paper like an engraving; use `S.fullbleed` with the original file when the camera must move into it.

**Already transparent?** ChatGPT often returns RGBA PNGs with the background already removed (they look black or glowing in chat previews). Check the alpha first (`Image.open(f).mode == 'RGBA'` and transparent corners); if so, skip `cutout.py` but still run `check_cutout.py` and look at it. Pale highlights inside a figure can raise the flag count without being leftovers.

### 5. Acts, with their word timing

Build the acts one at a time. Word timing is created **together with each act**, not as a separate step:

- When `actN.py` runs `cue = make_cue(CLIPS)`, any clip without timing is aligned on the spot (faster-whisper `small.en`, locally, prompted with the clip's `.txt`) and saved to `timing/words.json` and `timing/words.txt`.
- **Order for each act:** write `CLIPS`; run the act once (the contact-sheet command creates the timing); open `timing/words.txt` (`word@seconds`) to pick cue phrases; write the scenes.
- **Re-align a clip** whose audio or transcript changed: `python SK/scripts/align.py 7`.
- **Check every clip is complete.** Whisper can skip speech that matches its transcript prompt word for word (clip 13 of the Hawking film came back with 19 of 61 words). `align.py` now retries automatically when it gets under 80 % of the transcript, but compare word counts after aligning anyway:
  `python -c "import json;t=json.load(open('timing/words.json'));[print(k,len(v),len(open(f'audio/{k}.txt').read().split())) for k,v in sorted(t.items(),key=lambda x:int(x[0]))]"`
- **Narration not in English:** set `VOX_LANG` (`VOX_LANG=fr python SK/scripts/align.py`; the multilingual `small` model is used, and a prompted pass that does not match the transcript is retried unprompted). `storyboard.py` and the topic analysis read English keywords, so write the `episode.json` subject in English and plan the shots by hand. Whisper splits elisions: *n'est* comes back as `n` + `'est`, *d'une* as `d` + `'une`, so cue the word before or after (`cue(1, 'Ce')`, `cue(1, "'archeologue")`); *l'hoplologie* written with ’ stays one token. Accents are folded for matching (`'sediment'` finds *sédiment*). Proper names can be misheard ("Thieme" came back as "Art Mutiem"): cue a neighbouring word instead.
- **Cue pitfalls:** `cue()` finds the *first* occurrence, so a repeated word needs its number (`cue(11, 'one', 2)` when "no one" comes before "one-way"). Hyphenated words split into separate tokens (`one`, `-way`). Punctuation is ignored, so `'Pole.'` and `'Pole'` match the same word.

Copy `templates/act_template.py` to `actN.py`. Rules:

- **Scenes** are `sX(t, D)` returning a `Shot`. Every reveal uses `w(cue(clip, 'phrase'))`; cuts are `cue(...) - LEAD` in `SHOTS`; `END = cue.total` (last act: `+ 3.0` to hold the end title).
- **Layers — put each thing on the right one:**
  - `s.mid`: the paper on the desk (prints, documents, clippings, cut-outs) **and the marks made on it** (marker circles, stamps). Marks on `s.top` drift off their words when the camera zooms.
  - `s.top`: headline type that is part of the composition.
  - `s.hud`: captions, red labels, the chapter kicker. Fixed to the screen, so camera zooms never push them off-frame.
- **Camera — at most one purposeful move per shot, and about one shot in four with none** (locked off; see Craft 2):
  - `s.camera(z0, z1, focus0, focus1)`: slow drift across the shot (1.00 → 1.03–1.08).
  - `s.push(at, dz, focus)`: push in when something becomes relevant; the focus stays put.
  - `s.zoom_to(rect, at, dur, fill, back_at=)`: travel from the full composition into one image.
- **Cuts:** the third item of a `SHOTS` entry picks the transition: `'lr'`/`'rl'` torn wipe, `'up'` new sheet laid over. Vary them. Elements already present when a shot opens start at `ENTER`, so the wipe reveals the new composition landing.
- **Typography:** `words(layer, xy, text, size, t, [one cue per word])` (give one cue per *token*, separators like `·` included, or the last word never appears) (each word rises as it is spoken), `tag(...)` for a red label, `underline(...)`, `kicker(s.hud, t, n, 'Act title')` on the first shot of each act (in act 1, on the second shot: nothing comes before the hook). Big type: 2–4 words. Typed captions (`font=F_TYPE`) are short quotes from the narration.
- **Text budget:** one text element per shot, two at most, and some shots with none (Craft 1). A list the narrator reads is shown by images, not by three labels.
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
| 7 | `stamp_hit` | gives a verdict, a date, a refusal (pass `shot=s` for the kick); three per film at most |
| 8 | `mask_reveal` | opens an act or a memory: the image appears through a torn hole |
| 9 | `slide` | moves a document into the story ("Back in England sits…") |
| 10 | `assemble` | something comes together or breaks apart (`reverse=True`) |
| 11 | `flip` | a before/after: young → old, theory → result |
| 12 | `Shot.zoom_to` | the camera should single out one image from the composition |

**Do not animate everything at once.** One physical action per beat, chosen by what the narration is doing; the rest of the frame stays still or drifts. Mix durations (0.8–1.6 s) so nothing feels repetitive.

### 7. Editorial annotations

`annotate.py` makes the film feel like an editor marking up text, photographs and documents in real time. Every mark is drawn by a pen: anti-aliased strokes with pressure taper, a seeded hand tremor (identical on re-render), quick-start/soft-finish easing, and a small overshoot (rings loop past their start, corners overshoot, emphasis swells and settles). Each one makes its own sound (marker scratch, swipe, tick, air swell).

| Family | Function | Use it when the narration… |
|---|---|---|
| Text | `sweep(layer, box, t, start)` | names the key word or phrase (draw it **before** the text) |
| | `underline(..., double=True)` | stresses a word or a figure |
| | `ring(layer, box, ...)` | singles out one word or one detail |
| | `outline(layer, box, ...)` | quotes a phrase or a line on a document |
| | `strike(layer, box, ..., scribble=)` | corrects or rejects something ("Short" → "Brief") |
| | `emphasis(layer, xy, word, size, t, start)` | a word turns to the accent colour and swells, then settles (draw the word with this, not `words()`) |
| Photos | `ring` / `arrow(layer, p0, p1, ...)` | points at a person or an object in the picture |
| | `frame` / `corners` | isolates an area of a photograph |
| | `spotlight(layer, centre, r, ...)` | the eye must go to one place; draw it **last** on `shot.mid` |
| | `magnify(layer, layer.copy(), centre, r, zoom, to, ...)` | a small detail must be seen up close (a loupe with a leader line) |
| | `focus(shot, box, at, hold)` | the camera travels into the detail, holds, and pulls back |
| Documents | `mark(layer, xy, 'tick' / 'cross' / 'star' / 'dash' / 'question', ...)` | margin notes on a record |
| | `bracket(layer, x, y0, y1, ..., side=)` | groups lines that belong together |
| | `stat(layer, xy, '237 WEEKS', size, ...)` | a number the narration says: soft sweep + accent swell |
| | `connect(layer, [points], ..., dashed=, arrowhead=)` | links two items, or a document to a note |
| | `presets.stamp_hit(...)` | a verdict or a date lands with impact |
| | `bars(layer, box, values, ..., highlight=, fill_at=)` / `wedge(layer, c, r, a0, a1, ...)` | a chart where only the named part fills with the accent |

**Placing them:**
- **Boxes for text:** `words_box(xy, line, size, 'word')` gives the box of one word inside a `style.words()` line, and `text_box(...)` the whole line. Never guess pixel boxes for type.
- **Layers:** marks on paper and photos go on `shot.mid`, marks on headline type on `shot.top`, marks on captions on `shot.hud`, so they stay glued to what they mark during camera moves.
- **Lifetimes:** pass `until=<cue>` so a mark leaves when the narration moves on: `exit='settle'` (fades to a 35 % trace), `exit='fade'` (lifts away), or omit for marks that must stay (strikes, stamps).

**Style rules:**
- **One mark at a time,** on the word that names the thing. A frame holds at most two or three active marks, and earlier marks settle.
- **Colour** (from the episode palette): the accent for the mark the narration is on, the soft colour for background sweeps behind figures, secondary ink for spotlights and chart axes, and accent2 only as a second colour. In the editorial palette these are terracotta, beige, charcoal and muted orange.
- **No glows, neon or particles.** Strokes are 5–9 px; the spotlight dims to about 40 %.
- **Only highlight what is spoken.** Never circle a detail, box a phrase or fill a chart section the narration doesn't mention.

### 8. Storytelling toolkit

All of these plug into the same `Shot`, layers, camera, sounds and paper style. Pick by what the sentence does (see the planner above), not to show off.

**Transitions** (`transitions.py`), named as the third item of a `SHOTS` entry:

| Cut | Use it for |
|---|---|
| `'lr'`, `'rl'`, `'up'` | ordinary cuts (torn wipes and a new sheet laid over); the default |
| `'pageturn'` | a new chapter or a turn in the story |
| `('circle', {'at': (x, y)})` | opening from a point: a place, a detail, a reveal |
| `'shape'` | a change of subject or side (comparisons, corrections) |
| `('zoom', {'at': (x, y)})` | diving from the old shot into a detail that becomes the new shot |
| `'collage'` | montage, lists, several people or events |

Never use the same special cut twice in a row; most cuts in a film should still be the plain torn wipes.

**Maps** (`maps.py`): `WorldMap(box)` draws a printed map with beige land, ink coastlines and a faint graticule, with the paper itself as the sea.
- `zoom(t, [(t0, view), ...])` gives camera-like zooms (log-interpolated); `around('Italy' | (lon, lat), km)` frames a place.
- `draw(..., highlight={'GBR': cue})` fills a named country on its cue; `border()` draws a country's outline in marker, then fills it.
- `route([...stops])` draws a dashed journey with a travelling dot; `marker(lonlat, 'LABEL')` drops a pin with a paper label.
- `city('Geneva')` looks up the 243 bundled cities; `map_card()` makes a printed map as a paper object, to unfold, drop or slide.
- Held views are cached (about 16 ms), and a zooming frame costs about 0.6 s.

**Timelines** (`timeline.py`): `Timeline(y0, y1, box, step)`.
- `axis()` draws the rule, ticks and years.
- `event(year, label, start, side, until=)` makes a card pop on the spoken date; `era()` brackets a span; `now()` slides a marker along the dates.
- `focus(shot, year, at)` moves the camera along to a date; `year_counter()` rolls the year digits.

**Charts** (`charts.py`, alongside `annotate.bars/wedge/stat`):
- `line_chart(... mark=(x, 'LABEL'))`, `compare([(label, value)...])`, `unit_grid(total, k)`;
- `counter(a, b)`, `flow([(xy, 'LABEL')...], starts)`, `scale([(label, value)...])` (circle area follows the value).
- Only chart numbers the narration states.

**Objects** (`objects.py`):
- `newspaper(headline, date, photo=)`, with an invented masthead, never a real paper's name;
- `letter(lines)`, `polaroid(img, caption)`, `sticky_note(text)`;
- animated: `envelope(layer, letter, ...)`, where the flap opens and the letter rises; `spin_in(...)`, the newsreel front page, at most once a film; `tape()`; `pushpin()`;
- every builder returns RGBA, so all presets apply (drop, slide, unfold, flip, stack).

**Camera** (`style.Shot`), on top of `camera`, `push`, `zoom_to`:
- `pan(at, dx, dy, dur)`: a lateral dolly across the desk;
- `drift(amp)`: subtle handheld float for quiet shots;
- `rack(at, sharp='mid', amount, before='top')`: a focus shift between depths;
- `layer(depth)`: extra planes at any parallax depth (0.6 for a far cut-out, 1.4 for a near foreground prop) to build layered compositions where elements overlap and cast shadows on each other.

**Sounds** for all of it are registered automatically: `pin`, `pencil`, `whoosh`, `envelope`, `tape` and `pop`, plus the earlier ones.

**Real images before drawings:** a diagram earns its place only when it explains what no image can (rule 27). For an object, a place or an action, use the real image or a camera move into a plate.

**Pacing rules:**
- Alternate complex beats (a map zoom with a route, a flow diagram, a collage) with simple ones (one image, slow push, a few typed words).
- Emotional lines are always simple.
- Do not reuse one technique within three shots unless the story repeats on purpose.

### 9. Editorial typography

`typo.py` is the type system. Typography carries the explanation at the moments that need it, and stays out of the way otherwise.

**Hierarchy**: `Text(s, role)`. Each role has its own English face and Arabic face, size, colour, case and tracking:

| Role | English | Arabic | For |
|---|---|---|---|
| `headline` | Archivo Black 128, caps | Noto Kufi Arabic 900 | discoveries, the idea of an act |
| `subhead` | Archivo Black 64, caps | Noto Kufi 800 | secondary lines, contradictions |
| `statement` | Fraunces 700, 76 | Noto Kufi 700 | dramatic or emotional lines, word by word |
| `name` | Playfair 700, 92 | Amiri Bold | people (with `name_card`) |
| `date` | Archivo Black 300, accent | Noto Kufi 900 | years (with `big_number`) |
| `stat` | Archivo Black 240 | Noto Kufi 900 | numbers the narration states |
| `caption` | Special Elite 42 | Noto Naskh 500 | explanatory captions (typed) |
| `quote` | Fraunces 500 italic, 64 | Amiri | quotations |
| `label` | Inter 600, 26, caps, +6 tracking | Noto Naskh 600 | places, kickers, small labels |
| `term` | Archivo Black 56, caps | Noto Kufi 800 | technical terms (with `term_card`) |

Colours come from the episode palette: ink, secondary ink, light ink and accent (warm black, charcoal, cream and terracotta in `editorial`). Override any of size, colour, tracking, `max_w`, alignment and line height per `Text`.

**Animations**: `T.draw(layer, xy, t, start, anim=..., cues=[one per word], accent={'WORD': at}, until=, anchor=)`:
- `words`: each word rises inside its own slot (clipping mask).
- `letters`: letter-by-letter stagger.
- `lines`: line reveal from behind a mask.
- `scale`: words scale into position with a slight overshoot.
- `slide`: words arrive from alternating directions.
- `assemble`: scattered letters converge into the line.
- `split`: each line slices through its middle and the halves pull apart, then rejoin; use it for contradictions.
- `tracking`: letter spacing closes from wide.
- `cutout`: each word on a paper scrap, dropped onto the desk.
- `mask` with `shape='circle' | 'diagonal' | 'bars' | 'rect'`: revealed through a geometric shape, with a trace in the accent colour.
- `stamp`: rubber-stamp impact (pass `shot=s` for the camera kick).
- `type`: typewriter.
- `accent`: any word turns from its ink to the accent on its cue (`accent_colour=S.accent(s)` on dark grounds; `type_page` does this itself).
- Marker work: `T.box('WORD', xy)` gives the exact box for `annotate.sweep / underline / ring / strike`.

**Compositions:**
- `press(...)`: newspaper headline; the rules draw, the dateline types, the headline wipes in behind a rule in the accent colour.
- `big_number(...)`: oversized numerals whose digits roll into place, with a label and an accent bar.
- `term_card(...)`: the term, a typed one-line gloss and a bracket.
- `name_card(...)`: a small-caps role line, the name in display serif, and a short rule.

**Arabic:**
- Text containing Arabic is shaped with HarfBuzz (Pillow + raqm) and laid out right to left, aligned right by default.
- Letter-level animations fall back to word level, because Arabic letters join.
- The typewriter re-shapes each frame, so letters connect as they are typed.
- `big_number(..., lang='ar')` and `Text(..., digits='arabic')` give Arabic-Indic digits (١٩٨٨).
- Arabic needs looser line height (1.5) for its dots and marks; this is automatic except for numerals.
- Fonts are bundled under the SIL Open Font License (`assets/fonts/OFL-arabic-fonts.txt`).
- Check every Arabic line with a native reader; never machine-guess wording.

**When to use type** (`storyboard.py` adds a *typography* column; about 40% of sentences at most, labels and tags included, and at least a quarter of the shots with no text at all):

| Narration | Typography |
|---|---|
| a discovery | `headline` with `scale` or `lines` |
| a historical date | `big_number` (role `date`) |
| a number that matters | `big_number` (role `stat`) or `annotate.stat` |
| a name, at its first mention | `name_card` |
| a contradiction | `split`, or `annotate.strike` + `accent` for a correction |
| a short dramatic or emotional line | `statement` word by word, nothing else on screen |
| technical terminology | `term_card` with a one-line gloss taken from the narration |
| a quotation | `quote` with a `mask` reveal |

**Rules:**
- Never two big type moments in a row, and never the same animation within three moments.
- Most sentences stay with images.
- Type sits in generous negative space, often asymmetric: a headline on the left third with a print on the right.
- Type must stay readable at 1920×1080: captions at least 40 px, labels at least 24 px, accent-coloured text large.

### 10. Scene environments and compositions

**Every shot is its own editorial page.** The episode background (`themes.py`) is one environment among ten, not a wallpaper behind everything. Change the ground *and* the arrangement: scale, position, layering and the elements' relationship with the frame.

```
S.env(s, 'charcoal')          # inside a scene; style.compose draws this ground instead of the theme
colour = S.ink(s)             # light ink on dark grounds, dark ink on light ones (from the palette)
hi = S.accent(s)              # the highlight that reads on this ground and suits the scene's mood
```

| Environment | Ground | Use it for | Composition that fits |
|---|---|---|---|
| `theme` | the episode's animated background | continuity; the most common ground (≤ 40 %) | collage of prints, documents and type |
| `paper` | warm paper, no shapes | calm explanation, documents | prints and documents |
| `cream` | minimal light ground, one hairline rule | one idea, one quote, generous space | `type_page`, or one print on the thirds |
| `charcoal` | the palette's dark ground, with grain | drama, death, turning points, night | `type_page` in light ink, or one lit print |
| `accent` | solid ground in the palette's colour (`terra` still works) | one statement or one number, rarely | `type_page`, `big_number` in light ink |
| `halftone` | manga halftone + speed lines | action, manga and comics subjects | `panel_grid`, cut-out action |
| `archive` | aged newsprint with faint columns, smooth | history, dates, the press, records | clippings, documents, stacks |
| `geometric` | big flat shapes, diagonal split | comparisons, systems, two sides | `split`, two cards facing |
| `grid` | clean graph grid | infographics, charts, timelines | `charts.py`, `timeline.py` |
| `bleed` | none | a photo or illustration that speaks alone | `fullbleed`, `letterbox`, `split` |

**Compositions** (`scenes.py`):
- `fullbleed(s, img, t, start, ken, focus, focus_to, darken)`: the image fills the frame with a slow Ken Burns move; `darken` shades the bottom so captions read.
- `split(s, left, right, t, start, ratio, divide='tear'|'line'|'shape')`: two images face each other.
- `type_page(s, text, t, start, role, …)`: one sentence owns the frame.
- `panel_grid(s, images, t, starts, cols)`: a manga page or contact sheet, panels landing on their cues.
- `letterbox(s, img, t, start)`: cinematic bars close in for a dramatic beat.
- `rule_of_thirds('left'|'right')`: anchor points for asymmetric layouts.

**Every ground is smooth.** All environments (paper, cream, archive, grid, geometric, charcoal, accent) and the background themes take only a faint cloud and a fine paper grain, never large mottling, foxing blotches or tide-mark stains: on screen they read as dents and dirty patches (the user's note on *Histoire des armes*, first on the dark and red pages, then on every colour). The identity's `mottle` setting no longer adds blotches. Vignettes are even darkenings toward the edges.

**Planning:** `storyboard.py` now adds an **environment** column. It picks from each sentence's purpose, never repeats either of the two previous environments, keeps each within its share (`scenes.CAPS`), and gives dark or solid grounds only to short, strong beats. On the Berserk narration it used all ten environments across 54 sentences with no back-to-back repeat.

**Rules:**
- Never force a background behind every shot. A full-screen illustration, a split screen or plain charcoal type is often stronger.
- No two consecutive shots share an environment *or* a layout. Alternate collage, full-bleed, type and diagram.
- **Dramatic** moments: `charcoal`, `bleed`, `letterbox`. **Historical** information: `archive`. **Explanations**: `cream`, `grid`, `paper`. **Complex subjects**: rich collages on `theme` or `archive`.
- Join different environments with the strongest cuts: `pageturn` into archive, `circle` or `zoom` into a full-bleed image, `shape` between the two sides of a comparison, torn wipes for the rest.
- Brand constants hold everywhere: the same typefaces and roles, the episode palette, paper grain on every ground, torn-edge prints and pen-drawn marks. Every ground is built from the palette, so a manga episode's archive page is off-white and ink, a space episode's is pale blue. Text on dark grounds uses `S.ink(s)`, highlights use `S.accent(s)`.

### 11. Visual identity: art-directed per video, toned per scene

**The engine builds a visual identity for every video from its topic.** Ten categories are starting points, not limits. Each one is a full identity: colour roles with HEX values, chart series, paper texture, image treatment, a type pairing, and the scene environments it favours. The topic decides the final identity.

**Files:**
- `scripts/identities.py`: the design tokens. There's one editable block per identity, plus regions and periods. No other module hardcodes a colour.
- `scripts/palette.py`: the engine. It analyses the topic, builds and repairs the identity, and provides moods and image treatment.
- `scripts/identity_board.py`: the reference guide.

```
episode.json   {"subject": "Berserk: Kentaro Miura and Kouji Mori"}           # "palette" defaults to "auto"
               {"palette": "manga_ink/dark"}                                     # force an identity / variant
               {"palette": {"base": "manga_ink", "accent_primary": "#C4842A"}}  # the video's own colour
python SK/scripts/palette.py "the history of Japan from the Meiji restoration"   # what the engine derives, and why
python SK/scripts/identity_board.py --all out/identity                           # the guide: pages, overview, topic board
```

| Identity | Character | Grounds | Accents | Texture · images · type |
|---|---|---|---|---|
| `editorial` | Vox explainer | warm off-white #F3ECDF, ink #1E1C1A | terracotta #CD5830, teal #1F6F74, yellow marker #F2C14E | fibre paper · natural · Archivo Black + Fraunces |
| `history_archive` | document from a drawer | parchment #E6D5B0, walnut #2A1D13 | oxblood #7E2219, brass #7A5C22, gold wash | smooth parchment, fine specks · sepia duotone · Playfair + Special Elite |
| `science_space` | deep space | chalk blue #E4E9F2, space navy #0A0F24 | violet #5B3FD0, cosmic blue, amber starlight #FFB547 | star field · cool · Archivo + Inter |
| `manga_ink` | manuscript page | white #F6F4EE, pure black #0B0B0B | vermilion hanko #C42A1A, screentone grey | screentone · ink (B/W) · Archivo Black |
| `crime` | case file | cold grey #DADDDF, manila #D9C59A, #101418 | dried crimson #8C1C1C, steel blue, tape yellow #F2C230 | photocopy toner · cold duotone · typewriter captions |
| `technology` | interface | cool white #EDF0F3, graphite #0A0E14 | electric blue #1F5BE0, teal, cyan #2FE0FF, lime #B8F03A | dot grid · cool · Inter throughout |
| `philosophy` | marble and lapis | ivory #F1ECE2, aubergine night #1A1730 | lapis #2B4A9B, gold leaf #E3C278 | marble veins · warm · Playfair + PT Serif |
| `nature` | field notebook | linen #EEEBDD, forest #12201A | forest #2F6B3F, clay #A0552A, leaf #C9E27A | deckle fibre · natural · Fraunces |
| `culture` | museum | warm stone #EFE6DA, #22151C | plum #7A2A4E, turquoise #1F7A78, saffron #F0B44C | canvas weave · warm · Playfair + Fraunces |
| `economics` | the financial page | salmon #F6E7D9, navy #0F1A2B | market blue #0F4C81, gain green #1E7A4C, loss red | ledger rules · natural · Fraunces + Inter |

**Colour roles** (the same 17 in every identity): primary / secondary / minimal / dark / solid grounds; primary / secondary / muted / on-dark text; primary / secondary / on-dark accents; highlight (marker sweeps, tape, washes); border; divider; soft fill; texture tint. There are also five ordered **chart series** (`charts.series(i)`). Modules read them as `palette.ACTIVE.paper`, `.accent`, `.highlight`, `.chart` and so on.

**How the topic shapes the identity** (`palette.analyse` reads the transcript and episode.json `subject`, with the subject weighted 5×):
- **Category:** keyword scores pick the base. Unknown subjects fall back to `editorial`.
- **Variant:** a sub-genre within the category.
  - `manga_ink/dark` (seinen, horror, revenge; titles like Berserk or Attack on Titan) vs `manga_ink/bright` (adventure, shonen; One Piece).
  - `science_space/cosmos` vs `/lab`.
  - `technology/retro` (history of computing: beige plastic, phosphor green) vs AI.
  - `nature/ocean` and `/arid`.
  - `economics/crisis`.
  - `crime/historical`.
- **Second subject:** its accent becomes the supporting colour.
  - "The history of X" puts X's identity on archive paper, with sepia prints and an archive opening.
  - "The history of computers" leads with `technology/retro`, not history.
- **Region:** shifts supporting colours towards the place's visual culture. Japan: beni red and ai indigo. Maghreb: zellige green, Majorelle blue, saffron. Also Islamic world, China, Egypt, the classical world, India, Russia and others. For history, culture, editorial and philosophy it also sets the accent.
- **Period:** changes the atmosphere. Antiquity: stone and bronze. Medieval: lapis and gold. World wars: khaki, olive, gunmetal, drained colour. Cold war: concrete. Contemporary: cleaner paper.
- **Tone:** dark or bright, from the narration's emotional words. It shifts the balance of dark and light compositions.
- **Contrast is repaired automatically, never the grounds:** body text 7:1, secondary 4.5:1, accents 3:1, light text 4.5:1 on the solid ground, ink 4.5:1 over the highlight. Every change is listed in `IDENTITY.why`.

**What the identity controls** (one identity, every element):
- **Grounds:** all ten environments are built from its colours and texture overlay (`scenes.py`).
- **Type:** its fonts replace the role defaults (`typo.py`).
- **Highlights:** marker sweeps use the highlight colour (`annotate.py`).
- **Charts:** series colours (`charts.py`).
- **Images:** prints, full-bleed images, splits and panel grids get its treatment (`palette.treat`). Sepia and cold are duotones built from the identity's own dark and light grounds, so photographs belong to the film.
- **Maps:** land, coast and border colours (`maps.py`).
- **Objects and transitions:** paper colours and rules.
- **Background theme:** the `theme` environment draws the episode's theme only when the theme belongs to the same identity family. Otherwise it falls back to the identity's own paper, so terracotta shapes never sit behind a technology film.

**A red accent means different things:** oxblood sealing wax in history, dried crimson on a cold case file, a vermilion hanko on a manga page, loss on the financial page. Choose the identity for what the colour should *mean*.

**Narrative colour** (variation without randomness):
- **Opening:** the film opens on the identity's signature environment: archive for history, deep-space dark for science, halftone for manga, case-file dark for crime, grid for technology and economics, full-bleed image for nature and culture, cream for philosophy.
- **Within the film:** each identity weights the environments it favours (`IDENTITY.bias`). Moods tone scenes inside the identity (table below). A dramatic turn moves to the dark ground, a key statistic to the solid ground.
- **Close:** a reflective close returns to cream or paper.
- **Planning:** `storyboard.py` prints the identity with its reasons, the mood arc and the environment plan.

| Mood | Grade | Leans on |
|---|---|---|
| `neutral` | none | accent |
| `calm` | slightly softer, warmer | accent2 |
| `wonder` | a little richer and cooler | accent |
| `hope` | warmer, lifted | accent2 |
| `triumph` | richer, warmer, more contrast | accent |
| `tense` | cooler, less saturated, more contrast | accent |
| `mystery` | cool, desaturated, a little darker | accent2 |
| `menace` | desaturated, hard contrast, darker | accent |
| `grief` | strongly desaturated, quiet | muted |

Moods are smoothed: grief and menace hold for two lines and aren't broken by a passing "but". A lone weak cue is ignored.

**Rules:**
- **Settle the identity before the storyboard.** Run `palette.py` on the transcript, read `why`, and override it if the engine misread the subject. Show the user its page from `identity_board.py`.
- **Accents mark what the narration is on.** Never put an accent on more than one or two things per frame.
- **Tone changes only where the story does.** Hold a tone across its beat and never change colour shot to shot. Variety comes from environments and layouts; the identity gives continuity.
- **A new identity** goes in `identities.py` with all 17 roles, five chart colours, texture, image treatment, type, scenes and keywords. Check it with `python SK/scripts/palette.py --check` and look at its page before using it.
- **Never force cream, terracotta or any recurring palette** on a subject it doesn't suit.

### 12. Background themes

**History films use `astrolabe`** (from the user's parchment reference): smooth aged parchment with an even dark vignette, a large engraved astrolabe dial rising from the bottom edge and turning very slowly, two smaller dials drifting in the top corners, faint Latin lettering. The engraving stays faint so the collage always reads. It is the default for the `history_archive` identity (`identities.DEFAULT_THEME`); approved on *Histoire des armes*.

When the user gives a reference image for a background, match it (that wins over the rule below). Otherwise every episode gets its own background, but every theme speaks the design language of the user's original editorial background: the same paper, flat textured terracotta + beige corner shapes, translucent diagonal bands, thin dark lines and arcs, breathing dot grids, an open centre. Only the shapes and their arrangement change with the subject. Do not invent a new visual style (dark grounds, heavy patterns) unless the user asks.

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
| `astrolabe` | history (from a user reference) | dark-vignetted parchment, a great engraved dial rising from the bottom edge that turns slowly, two corner dials drifting |

**New theme:** add a `Theme(name, label, [elements], paper_colour, seed)` in `themes.py` from the element vocabulary (`shape`, `terra`, `hline`, `vline`, `dots`, `orbiter`, `tracer`, `diag`). Keep big shapes off the centre, take the colours from the episode palette, give every element its own drift period (20–45 s). Show the user a board of themes and a 15 s preview before using it.

### 13. Sound effects

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
| `pin` | air whistle, soft tack into paper | `maps.marker`, `objects.pushpin` |
| `pencil` | dry graphite scratch | `maps.route`, `maps.border`, `Timeline.axis`, `charts.line_chart` |
| `whoosh` | air movement (no tonal sweep) | `circle`, `shape`, `zoom` transitions, `objects.spin_in` |
| `envelope` | flap lifting, letter sliding out | `objects.envelope` |
| `tape` | tape torn and pressed | `objects.tape` |
| `pop` | soft paper pop | timeline events, chart points, size circles |
| `beep`, `tick` | soft monitor beep, tiny click | manual only (counters, ticking clocks, letter-card hops) |

- **Manual cues** for things presets don't know about (marker circles, strikes, story sounds): `sfx('marker', w(cue(1, 'word')), x)` inside the scene.
- **Mix:** each sound is varied per event (seeded, deterministic), panned to its x position, summed at −13 dB, and ducked by 9 dB while the narration speaks. Target: effects about 20 dB below the voice (stem ≈ −37 LUFS against −16), loudest stamp peak ≈ −16 dBFS. The user found −10 dB under the voice too loud: keep effects subtle.
- `render_all.py` mixes them in automatically. `VOX_SFX=0` turns them off; `VOX_SFX_DB` sets the level (default `-13`; `-17` quieter, `-9` louder). The stem alone is written next to the mix as `mix.wav.sfx.wav`.
- **Add audio to an already-rendered act** without re-rendering the picture: `vox.collect_events(act.frame, act.END)`, `sfx.mix_into(narration_wav, events, out_wav)`, then mux with `ffmpeg -c:v copy`.
- **Sound must not contradict the story.** No flat-line tone when the patient survives, no gunshots for implied violence.

### 14. Craft: what separates an edited film from a generated one

Viewers forgive simple pictures; they leave when a film feels automatic. These are the tells, each seen on a real render, and the fix for each. `python SK/scripts/check_pacing.py` measures the ones that can be measured.

**1. Text that repeats the voice.** The strongest tell. On the first cut of *Histoire des armes*, 64 of 65 shots carried a label, most of them the narrator's own words in capitals ("PRESTIGE · STATUT · BRAVOURE"). The viewer reads what they are hearing and stops looking at the image.
- At least a quarter of the shots have **no text at all**: the image and the voice are enough.
- On-screen text adds something the voice does not: a name spelled out, a date, a place, a term, a number, a correction. It never transcribes a list the narrator is reading.
- One text element per shot, two at most (a headline and a caption). Three labels dropping one after another is a slide, not a shot.
- Sentence case for statements and captions; capitals only for short headlines (one to three words) and stamps.
- Type follows the language's own rules. French: a thin space before `? ! : ;`, « guillemets », the typographic apostrophe ’, accents on capitals (É, À), `IIᵉ` or "IIe siècle" set consistently. Arabic: checked by a native reader.

**2. Everything moves, all the time, the same way.** A slow push on every single shot, every print dropping with the same spin, every reveal on the same 0.3 s ease.
- One shot in four is **locked off**: no camera move, one element arriving, then stillness. Stillness is what makes the next move register.
- Vary how things arrive within an act: a drop, then something already lying there, then a slide, then a cut straight to a full-bleed image with no entrance at all.
- Break symmetry by hand: unequal rotations (−4°, +1.5°, −2°), uneven spacing, one print overlapping another, one element partly out of frame. Three cards evenly spaced in a row look machine-set.
- Give staggers an irregular rhythm (0.0, 0.25, 0.7 s), not a constant step.

**3. Effects as decoration.** A stamp on every date, a torn-paper special cut at every sentence.
- Per film: at most three stamps, one `spin_in`, two `flip`s, two letterboxes. Special cuts (`pageturn`, `circle`, `shape`, `zoom`) are for act changes and real turns; four cuts in five are plain.
- When in doubt, cut it. If removing an effect loses no meaning, it was decoration.

**4. Rhythm with no shape.** Shots that all last five seconds.
- Mix quick beats (2–3 s) with long holds (7–10 s) on the images that deserve them. No shot under 2 s. A shot over 10 s must change inside (a second image, a push to a detail).
- Let the film breathe after a strong line: hold the image one beat past the last word before cutting. Ask the user for 0.5–1 s of silence between narration clips at act changes; never trim the pauses they recorded.
- Build to the end: the last act is the simplest and slowest, and the final shot holds 3–5 s.

**5. The same image again and again.** The same sword print nine times in a grid, the same photo in five shots.
- An image appears at most twice in a film (a third time only as the planned callback). Need "many"? Show a real image that contains many (a hoard, a rack of swords, a relief of soldiers), not one print multiplied.
- Never reuse an image as a stand-in for something else (a Deccan sword playing "a ceremonial sabre").

**6. Images that look found, not chosen.**
- Crop to the subject. Cut museum objects out of their glass case and wall (or crop tight) so the object, not the display, is the picture; a rectangle of grey case around a small sword wastes the frame.
- Minimum quality: 1600 px on the long side for a print, 2400 px for a full-bleed plate. No watermarked or stock-site previews, no AI-generated "photos" of real things (the Pngtree drone was refused for both reasons).
- **The image must be the thing named.** A reconnaissance drone is not "un drone armé"; a 19th-century cavalryman is not a pre-Islamic horseman. If only a near match exists, tell the user and let them choose.
- **Caption what the image is** with `caption(s.hud, 'Lance VII, Schöningen, 1997', t, start, on_dark=)` (in `style.py`: small serif, sentence case, bottom-right by default, soft dark backing on photos, fades in with no sound): object, place, museum or date of the photograph, taken from its source page ("Lance VII, Schöningen, 1997", "Sabre de fabricant damascène, vers 1900"). These captions describe the image, so they may state facts the narration does not; everything else on screen still comes from the narration (rule 1). Captions are what make a film read as documentary rather than slideshow.
- Mark generated drawings honestly: `caption(s.hud, 'Illustration', t, start, corner='bl')` (or "Reconstitution"), so a drawing is never mistaken for evidence.

**7. Generated drawings that give themselves away.**
- At most three or four per film, all in one style from one reference, used where no photograph can exist.
- Check each one before accepting it: hands and fingers, the number of legs on animals, anachronisms (a curved sabre in the 6th century, stirrups, modern tack), repeated texture patterns, garbled lettering. Send it back with a one-line fix rather than hiding the fault with a crop.
- Role lines and glosses are facts too: a name card's role ("Hoplologue") and a term card's definition must come from the narration, not from general knowledge.

**8. Sound with no bed.** Voice and paper sounds over silence feel unfinished.
- Ask the user for a music track they have the right to use (or its name in a library such as the YouTube Audio Library), calm and without vocals. Lay it in with `python SK/scripts/music.py out/full.mp4 music.mp3 out/full_music.mp4`: about 14 dB under the voice, ducked further while the narrator speaks, faded in and out. The picture is not re-rendered.
- One change of music mood at most, at the film's turning point.
- Measure the final file (`ffmpeg -i out/full.mp4 -af ebur128 -f null -`): integrated loudness between −17 and −15 LUFS, or remix.

**9. No packaging.** A professional upload is more than the file.
- **End screen:** ask whether the user wants one; if so hold the last frame 8–10 s with the lower two thirds clear for YouTube's end-screen elements.
- **Chapters:** give the act start times as a ready-to-paste chapter list (first at 0:00), act titles written as short promises or questions, not labels.
- **Thumbnail:** one subject from the film, one contrast, at most four words; offer to set the words in the film's own typeface over the user's image so the thumbnail matches the video. Check it at 160×90 px.
- **Description:** two lines that state the question the film answers, then the chapters; credits below (`CREDITS.txt`), never on screen unless asked.

**Run before every draft:** `check_empty.py`, then `check_pacing.py` (it also reads the act sources: more than three stamps, two flips, two letterboxes or one spin-in, special cuts on more than a quarter of the cuts, an image in more than three places, a print dropped in a loop, a kicker on the film's first shot, an act with real images and no `caption()`). Read its numbers aloud to yourself: the share of text-free shots, the spread of shot lengths, repeated environments. Fix the film, not the numbers.

### 15. QC before rendering

```
cd project && PYTHONPATH=SK/scripts:. python act1.py sheet out/act1_sheet.png 2 6 10 15 22
```

**First, no empty screens:** `python SK/scripts/check_empty.py 1` (or no argument for every act). It flags every stretch of 0.75 s or more where a shot shows only its ground; fix them all before the contact sheet. A shot must have something on screen from its first frame: the print the sentence is about, a line or diagram that draws in, the typed sentence, a label. Never leave the viewer on a bare background waiting for the cue word. (On *Histoire des armes* it caught exactly the three gaps the user found: 0:19, 0:30–0:34 and 0:38–0:41.)

**Look at the contact sheet.** Pick moments just after each reveal **and** moments mid-transition and mid-preset. Check for:

- cut-out leftovers;
- text overlapping a figure, running off-frame, or red text on a terracotta shape;
- marks (circles, stamps) still sitting on their words during camera moves;
- a black edge during a zoom (the background must always cover the frame);
- empty frames revealed by a wipe (use `ENTER` for elements present at the cut);
- **text near the frame edge during a camera push**: a name card or headline placed near the right edge on `s.top` is pushed off-frame by `s.camera(1.0, 1.05, ...)`; keep 120 px of margin at the end of the move, or push toward the text;
- **a word on screen before it is spoken**: every word, label and mark appears on its cue (`A.emphasis` now waits for its start unless `before=True`);
- **text over a dark plate**: black type disappears on a zoomed plate; use `tag(...)` (red label, or `bg=CREAM, fg=INK`);
- **missing glyphs**: Archivo Black has no `→` (it renders as a box); `÷`, `²`, `’` and `,` are fine. Write words instead of rare symbols;
- **glows on cream**: a cream or white glow is invisible on the paper; use a glow in the accent colour;
- **contrast**: run `python SK/scripts/palette.py` after changing a palette. Accent text on light grounds and light text on accent labels pass only as large text (in `editorial`, terracotta on cream is 3.4:1), so accent-coloured text stays large (≥ 40 px) and never carries small captions;
- **pale objects on cream** (tape, envelopes, sticky notes, paper cards) need a darker edge or a shadow, or they vanish: tape uses a tan tint with ruled edges;
- **objects that move out of something** (a letter leaving its envelope, a card from a pocket) must stay on screen at every frame; check the start, middle and end of the move;
- **chart values that are not narrated** must be labelled as illustrative, or not shown at all;
- **invented names** (newspaper mastheads, signatures) must not be a real publication or person;
- **after changing the engine**, render one frame from every existing act to prove nothing broke:
  `python -c "import importlib;[importlib.import_module(f'act{n}').frame(5.0) for n in range(1,7)]"`;
- **the same print twice in one frame**, or an image already used twice in the film (Craft 5);
- **an image that is not what the narration names**, or a stand-in passing as the real thing (Craft 6);
- **a caption or label in the wrong language convention** (missing accent on a capital, straight apostrophe, no space before `?` in French);
- anything on screen the narration does not say, image captions excepted (Craft 6).

Fix, re-check. Show the user sheets or a draft per act and get approval before moving on.

### 16. Render: Claude renders the final, in this session

```
cd project && python SK/scripts/render_all.py --acts 3 --draft   # review render of one act
cd project && python SK/scripts/render_all.py                    # FINAL: CRF 12, slow, 320k AAC, all acts
```

- **Run renders in the background** (Bash `run_in_background`) and wait for the completion notice; don't poll with sleep. Background jobs may start in the repository root, not the project folder, so always set the project explicitly: `VOX_PROJECT=/abs/path/to/project python SK/scripts/render_all.py --acts 1 --draft` (without it the render fails with `act1.py` not found). Measured on 4 cores: a 40–60 s act drafts in 7–10 min alone; two acts in parallel (`--acts 1 2`) take about 21 min together, so render one act at a time while reviewing and batch only the final.
- **Don't chain renders with a background waiting loop** (`while ! grep Done ...; do sleep; done; render`). On the Hawking film the waiter died silently at its time limit and two acts never rendered. Start the next render yourself when the completion notice arrives, or render several acts in one `render_all.py --acts ...` call.
- **Before telling the user a render is running, check it is**: `ps aux | grep render_all` and look for the output file.
- **Cost of the heavier tools** (4 cores): a held map view is about 16 ms because frames are cached, but a zooming map is about 0.6 s a frame, so keep map zooms to 1.5–2.5 s. Transitions add about 0.3 s per frame while they run. Plan longer renders for map-heavy acts.
- **Demo reels without narration:** `vox.collect_events(frame, END, step=0.25)` then `sfx.build_track(events, END, None, level_db=-9)`, and mux with `ffmpeg -c:v copy`. Without a voice to duck under, −9 dB keeps the effects audible.
- **Draft of the whole film:** `out/acts.txt` lists the act files; `ffmpeg -f concat -safe 0 -i out/acts.txt -c copy out/full_draft.mp4` joins them losslessly. An act whose audio was remixed separately (e.g. `act1_sfx.mp4`) can be copied over its act file first.
- **Act drafts:** after each act is approved on its contact sheet, render a `--draft` and send it with `SendUserFile`.
- **Final:** all acts, CRF 12, joined losslessly into `out/full.mp4`, narration mastered to −16 LUFS. Check the duration with ffprobe, measure the loudness of the joined file (`-af ebur128`; −17 to −15 LUFS, the first final of *Histoire des armes* came out at −17.1), spot-check frames, then send it. If the user supplied music, run `music.py` on the joined file and send that version.
- **Files over 100 MB** stay out of git. Send them directly.

### 17. Channel branding and calls to action

The channel stays recognisable in every film; each film keeps its own identity. `brand.py` holds the system, `brand/brand.json` the channel's settings, and each video overrides any key in `episode.json` under `"brand"`.

**The logo.** The official file is `brand/logo.svg`, used as supplied: rendered by cairosvg at the exact pixel size of each use (sharp at any size, transparency and proportions kept), never redrawn, recoloured or distorted. Official variants for dark or light grounds go in `logo.on_dark` / `logo.on_light`; without them a soft paper plate sits behind the logo wherever logo and ground are too close in tone. **Until `brand/logo.svg` exists, real renders draw no branding at all**: a placeholder can never reach a film (the demos alone show `brand/placeholder.svg`, marked LOGO).

| Element | Function | Use |
|---|---|---|
| Watermark | drawn by `overlay()` | small (112 px), top-right, 62 % opacity; starts after the hook with a small reveal; hidden on `bleed`, `accent` and `charcoal` shots and while a CTA is up; fades only where its visibility changes |
| Logo reveal | `reveal(layer, cx, cy, width, t, start, style=)` | `mask` (a clean wipe behind a moving edge), `scale` (0.94 → 1 settle), `assemble` (four fine rules close in); optional `hold` then a gentle exit |
| Signature | `signature(layer, x, y, t, start)` | the brand's mark: a fine rule that draws, a small square at its end; under the logo, under the subscribe message |
| Subscribe | `cta_subscribe(...)` | logo, channel name if set, a quiet button pressed once (it turns to « Abonné » with a drawn tick), a bell that rings twice |
| Like | `cta_like(...)` | an outlined thumb that fills with the accent once, one short line |
| Comment | `cta_comment(..., question=)` | a speech-bubble card with the video's own question, revealed line by line |
| Share | `cta_share(...)` | three nodes whose lines draw out; one short line |
| Next video | `cta_next(layer, box, ...)` | the thumbnail (or a quiet placeholder), a frame drawn around it, « À voir ensuite », the title |
| Outro | `outro_scene(t, D)` | the end screen, as a Shot |

**Placement is read from the narration** (`plan()`, printed by `python SK/scripts/brand.py`): nothing during act 1 (the hook plays clean); a mid-film CTA (the like card by default) only in a real pause of the narration inside 38–72 % of the film, never within 6 s of an act opening and never in the last act; the subscribe CTA and the comment question in the outro, after the narration has ended. Explicit times in the config (`"at": 212.5`) win. Different films get different schedules; none is forced.

**The comment question is written per video**, specific and connected to the subject (`brand.cta.comment.question`), in the video's language: « Et vous, jusqu’où arrivez-vous à compter avant de penser simplement « beaucoup » ? » for *Les très grands nombres*. Without one, a question shaped by the identity is used, then the generic one. All CTA texts are in `brand.json` `"text"` per language (fr, en, ar); Arabic is checked by a native reader.

**The outro** (8–12 s, default 10) is appended to the last act after the narration:
```
SHOTS += [(cue.total + 0.4, brand.outro_scene)]
END = cue.total + 0.4 + brand.outro_seconds()
```
It takes the video's ground (`outro.env`, default the identity's paper) and palette; only the logo, signature and type are the channel's. Layouts adapt to the recommendations available: `split` (two slots stacked right, logo and messages left), `feature` (one large slot), `centered` (no slots). The slots are 16:9 at about a third of the frame, the size YouTube's video elements take; the subscribe element gets a circle with the logo; nothing essential sits inside a slot, the circle, or the bottom tenth (player controls). `brand.write_endscreen()` writes `out/endscreen.json` with every rectangle in pixels and percent, to place the elements in YouTube Studio exactly over them.

**Sound and voice.** CTA sounds are the engine's own (`tick` on the press, `pop` on cards, `reveal`, `pencil` on slot frames), at 60 % of their usual level; `"sounds": {"enabled": false}` turns them off. No CTA is ever spoken unless a recorded line is configured (`"cta": {"voice": {"like": "audio/cta_like.wav", "outro": "audio/cta_outro.wav"}}`); a voiced mid-film CTA is only placed in a pause long enough to hold the whole line, so it never talks over the narration.

**Demo:** `python SK/examples/demo_brand.py out/brand [--reel]` renders the watermark on a frame of the film, the three reveals, the subscribe CTA, the comment/like/share cards, the three outro layouts on three grounds, and with `--reel` a 30 s reel with its sounds.

## Rules learned from the user (keep them)

1. Base everything on the transcript.
2. Never draw in code what should be an image: use a real image first (rule 25), a generated drawing only when none can exist.
3. Generated drawings follow the user's reference style for the film (storybook, linocut, ink engraving); never anime, in prompts and in what you accept.
4. Check every asset for background leftovers before using it (magenta check).
5. Never add a background behind an image that already has one.
6. The film should feel like an explainer, not a movie: paper collage, documents and type carry the ideas.
7. Every cut, reveal and camera move lands on the word it illustrates.
8. Real-person likeness comes only from images the user provides, shown as photo prints.
9. Claude renders the final at full quality in the session and sends the file.
10. Create word timing as each act is built, never as a separate pass afterwards.
11. Asset prompts are short, lean on a reference image, and are given complete and ready to copy.
12. **The user approves visual changes before they go into the film.** Build a preview (still, 15 s clip or demo reel) and wait for the go-ahead before re-rendering acts.
13. A background the user gives as a reference is matched (the astrolabe parchment for history). Without one, backgrounds follow the user's original editorial design language in a fresh arrangement per episode. Colours come from the episode palette (rule 23).
14. No grey torn-paper strip along the bottom: the corner shapes anchor the frame.
15. Elements behave like physical paper (lift, shadow, overshoot, settle); never PowerPoint-style fades or flat slides.
16. Sound effects stay subtle: about 20 dB under the voice (the first mix at 10 dB under was too loud). Change single sounds or the level by remixing the audio only, never by re-rendering the picture.
17. Never report work as running or done without checking it (process list, output file, duration). If something silently failed, say so plainly and restart it.
18. Every word on screen must be readable on what is behind it: label backings over dark plates, large size for red text, no missing glyphs.
19. Annotations follow the narration: one mark per spoken idea, drawn on its word, settling when the narration moves on; never highlight everything at once.
20. Choose every visual from what the sentence means and feels: analyse the narration first (storyboard.py), vary the techniques, and leave some moments deliberately simple.
21. Typography is part of the explanation, not decoration: give type to discoveries, dates, names, contradictions, terms and quotes, and leave most sentences to images.
22. Every scene is a new editorial composition: vary the environment and the arrangement shot to shot (scenes.py), never the same background or layout twice in a row, while typography, the episode palette, paper texture and animation principles stay constant.
23. Every video is art-directed for its subject. The engine derives a visual identity from the topic: category, sub-genre, second subject, region, period and tone (identities.py, palette.py). Every colour, texture, typeface and image treatment on screen comes from it. Accents mark only what matters, the tone shifts only where the story's emotion does, and contrast always passes. Different videos must look noticeably different. Never force cream, terracotta or any recurring palette onto a subject it doesn't suit.
24. **No empty screens.** Every shot has something on screen from its first frame to its last; a background alone is never a shot. Run `check_empty.py` before every render.
25. **Real images first.** Search for real, freely licensed images (Commons) before prompting for drawings; give the user the direct download links when this machine is rate-limited; when nothing free exists, ask the user to search before generating. Credit every image in the video description, not on screen.
26. **History films use the astrolabe parchment background**, and every ground of every colour stays smooth: fine grain only, no mottled patches, stains or dents.
27. **Drawings only when they explain.** Code-drawn shapes (diagrams, arrows, lines, schematic stones or arms) appear only where they make an idea clearer than any image could: a measurement, a distance between two things, a non-linear path, a correction. Everything else is shown with a real image: an object, a photograph, a painting, or the camera moving into a plate to the detail the sentence names. Never draw something just to fill the screen; fill it with the right image instead (rule 24). On *Histoire des armes* the drawn staircase of "progress" became a row of real objects (spear, stone point, bronze sword), the drawn stone and arm became a camera move into the lakeshore plate, and the pressure arrows became the real Levallois point with its tip circled.
28. **Images speak; text adds.** At least a quarter of the shots carry no text. On-screen words never transcribe the narrator: they add a name, a date, a place, a term or a number. One text element per shot, two at most.
29. **Restraint reads as craft.** Some shots are locked off; effects are rationed per film (three stamps, special cuts only at real turns); nothing is laid out in perfect symmetry or timed on a constant stagger; an image is used at most twice and never multiplied.
30. **Hook, shape, close.** The film opens on its strongest image with no title before it, varies its rhythm between quick beats and long holds, returns to one motif, and ends on an image that answers the first.
31. **Honest pictures.** The image is the thing the narration names, or the user decides on a near match; real images carry a small caption of what they are; generated drawings are few, checked for faults and anachronisms, and marked as illustrations.
32. **A finished film has a music bed and packaging**: music supplied by the user, mixed far under the voice; measured loudness; chapters, thumbnail and description offered with the file.
33. **The brand is recognisable but never overshadows the story.** The official logo is used as supplied (never redrawn or recoloured); no branding in the hook; CTAs only in real pauses and in the outro; the comment question is specific to the video; the outro keeps the video's own palette and leaves YouTube's end-screen areas clear.
