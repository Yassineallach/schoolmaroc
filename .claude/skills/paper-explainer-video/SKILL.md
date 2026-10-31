---
name: paper-explainer-video
description: Build a YouTube educational explainer video (book summary, history, science, biography) in a Vox-style editorial paper-collage look from the user's narration clips and transcript. Use when the user wants an explainer or summary video made from voice-over audio. It covers storybook-style asset prompts, clean cut-outs, scenes synced to the spoken word (timing created with each act), contact-sheet QC and a full-quality 1080p render done by Claude in the session. Triggers include "make a video like the Red Rising one", "explainer video from my narration", "paper collage / Vox style video", "book summary video".
---

# Paper-collage explainer video

Made for the *Red Rising* explainer (7:38, 8 acts, 26 narration clips). The same pipeline
works for any narrated explainer.

**What the output looks like:**

- a locked grey paper background (`#DAD9D5`);
- hand-illustrated cut-outs, each with an offset red marker stroke (`#E04329`) and a drop shadow;
- a torn-paper foreground strip;
- painted plates shown as torn photo prints;
- documents, stamps, typed captions and marker lines drawn in code;
- spring entrances, with every reveal and cut landing on the spoken word.

**Defaults:** 1920×1080, 30 fps, H.264. The final render uses CRF 12.

## Project layout

Keep everything in one folder; the scripts run from inside it, or set `VOX_PROJECT`.

```
project/
  audio/1.wav 1.txt 2.wav 2.txt ...   narration clips plus the exact transcript of each
  assets/                             APPROVED, leftover-checked PNGs only
  timing/words.json, words.txt        created automatically as each act is built
  act1.py act2.py ...                 one file per act (copy templates/act_template.py)
  out/                                renders
```

Install: `pip install pillow numpy scipy faster-whisper`, plus `ffmpeg` on PATH.

`SK` below means this skill's folder, e.g. `.claude/skills/paper-explainer-video`.

## Phases

### 1. Script → acts

- **Read every transcript.** The transcript is the source of truth: every visual must illustrate a line that is actually spoken. Don't invent facts, and don't put numbers on screen that the narration does not state.
- **Group the clips into acts** of 40–90 s, each with a title.
- **Plan the shots.** For each act, write a shot list: transcript sentence → visual → which assets → the words that trigger each reveal.

### 2. Visual plan and asset list

- **Get the user's guide.** If the user has a visual guide, follow it exactly. Ask for it if there isn't one.
- **Split the assets** into:
  - (a) things the code draws (see `references/prompts.md`, "Things code draws better");
  - (b) things to ask the user for: characters, places, creatures, real people.
- **Ask for anything that would look bad drawn in code.** Never fake a face, an animal or a landscape with shapes.
- **Show the storyboard first.** For long projects, put it on a Design canvas artifact before generating anything.

### 3. Asset prompts

- **Give ready-to-paste prompts** from `references/prompts.md`. Masters come first; poses use the masters as reference.
- **Storybook, never anime.** If outputs drift toward anime, rewrite the prompts. Don't accept the drift.

### 4. Cut-outs: check every asset before use

Ask what each image is before cutting it:

- **Has its own painted background** (close-ups, scene plates, gas shots): use it as a `PhotoCard` as-is. Don't cut it out, and don't add a background behind it.
- **A figure on plain ivory**: cut it out.

```
python SK/scripts/cutout.py sheet.png assets/hero_standing.png [--crop x0,y0,x1,y1] --mode standard
python SK/scripts/check_cutout.py out/check.png assets/hero_standing.png ...
```

Choose the mode by what the figure is made of:

| Mode | When to use it |
|---|---|
| `standard` | dark or saturated costumes. If eyes, teeth or lamp glass get holed, raise `--head` (0.2–0.35). |
| `gentle` | gold, cream or pale costumes close to the paper colour. Use it when `standard` punches holes in the costume. |
| `edge` | near-paper skin, faces in close-up, pale horses or animals. It fills holes and closes notches so the red stroke never shows through. |

**Open the preview image and look at it.**

- On magenta, any paper leftover (halo, pocket between arm and body, fringe) is obvious.
- On dark, any pale outline glow is obvious.
- Re-cut with another mode or crop until both are clean. Only clean files go into `assets/`.
- The user caught leftovers several times on the first project. This check is not optional.

### 5. Acts, with their word timing

Build the acts one at a time. Word timing is created **together with each act**, not as a separate step:

- **Automatic timing.** When `actN.py` runs `cue = make_cue(CLIPS)`, any clip in `CLIPS` that has no timing yet is aligned on the spot. That uses faster-whisper `small.en`, locally, with the clip's `.txt` as the prompt so names are spelled right. The result is saved to `timing/words.json` and `timing/words.txt`.
- **Order for each act:**
  1. Write `CLIPS`.
  2. Run the act once (e.g. the contact-sheet command in phase 6). This creates its timing.
  3. Open `timing/words.txt` (`word@seconds`) to pick the cue phrases.
  4. Write the scenes against those phrases.
- **Re-align a clip** whose audio or transcript changed: `python SK/scripts/align.py 7`.
- **If a phrase is not found:** check `words.txt` for the spelling, use the nth occurrence, or use a neighbouring two-word phrase that is unique.

Copy `templates/act_template.py` to `actN.py`. Rules:

- **`CLIPS`** lists the act's clips, and **`cue = make_cue(CLIPS)`**.
- **Timing:**
  - Each scene is `sX(t, D)`, and every reveal uses `w(cue(clip, 'phrase'))`.
  - Cuts are `cue(...) - LEAD` in `SHOTS`. No hand-typed seconds.
  - `END = cue.total`. In the last act, use `+ 3.0` to hold the end title; the audio is padded 4 s.
- **Layer order:**
  1. `background()`
  2. plates, sheets and cut-outs
  3. `c.alpha_composite(FG)` (the foreground strip)
  4. text, stamps and marker marks on top
- **Layout:** one idea per shot. Big text: a headline of 2–4 words. Typed captions are short quotes from the narration.
- **Motion and side:**
  - Use the `side=` of a cut-out to put the red stroke on the far side.
  - Use slow `zoom=lerp(1, 1.08, ease(t/D))` push-ins on plates.
- **Violence is implied only:** a silhouette, a stamp, a cut away. Nothing graphic.

Engine reference (all in `scripts/vox.py`):

- **Objects:** `Cutout(img, h).place(c, cx, bottom, t, start, side=)`; `PhotoCard(img, width, rot, seed).place(c, cx, cy, t, start, zoom=)`.
- **Sheets:** `document(w, h, lines, title=)` plus `place_sheet(...)`.
- **Text and marks:**
  - `headline` and `typewriter`;
  - `stamp`;
  - `marker_line`, `marker_circle` and `strike`;
  - `shake(img, t, hits)`.
- **Layout:** `torn_mask` and `foreground()`.
- **Constants:** `W`, `H`, `PAPER`, `INK`, `RED`, `CREAM`.

### 6. QC before rendering

```
cd project && PYTHONPATH=SK/scripts python act1.py sheet out/act1_sheet.png 2 6 10 15 22
```

**Look at the contact sheet.** Pick one moment per scene, just after its last reveal. Check for:

- cut-out leftovers;
- text overlapping a figure, or running off-frame;
- a plate taller than 1080 (use a smaller width for portrait plates);
- empty frames;
- things that don't match the line being spoken.

Fix them, then re-check. On long projects, show the user sheets or a draft per act and get approval before moving on.

### 7. Render: Claude renders the final, in this session

The final video is rendered **here, by Claude, on Claude's machine**. Not on the user's PC, and not on Kaggle. The user only receives the finished file.

```
cd project && python SK/scripts/render_all.py --acts 3 --draft   # review render of one act
cd project && python SK/scripts/render_all.py                    # FINAL: CRF 12, slow, 320k AAC, all acts
```

- **Run renders in the background** (Bash `run_in_background`). Rendering is CPU-bound: about 1 min of render per 5 s of video per process, so a full 7–8 min film takes over an hour. Keep working, or wait for the completion notice. Don't poll with sleep.
- **Act drafts:** after each act is approved on its contact sheet, render a `--draft` of that act and send it with `SendUserFile`, so the user can review it while you build the next act.
- **Final:** when all acts are approved, render without `--draft`.
  - It writes one file per act, then joins them losslessly into `out/full.mp4`.
  - Narration is mastered automatically: EQ, 3:1 compression, −16 LUFS.
  - Check the duration with ffprobe and spot-check a few frames.
  - Then send `out/full.mp4` to the user with `SendUserFile`.
- **Files over 100 MB** stay out of git (`.gitignore`). Send them directly.
- **Render scripts for the user's own PC:** only if the user explicitly asks. The default is: Claude renders, the user downloads.

## Rules learned from the user (keep them)

1. Base everything on the transcript.
2. Ask for assets that would look bad drawn in code.
3. Storybook illustration, not anime, in prompts and in what you accept.
4. Check every asset for background leftovers before using it (magenta check). Never put an asset with leftovers in a render.
5. Never add a background behind an image that already has one. Flat paper goes only behind cut-outs.
6. The film should feel like an explainer, not a movie. Paper collage, documents and text carry the ideas; plates are illustrations pinned to the page.
7. Every cut and reveal lands on the word it illustrates.
8. Real-person likeness, such as an author's portrait, comes only from an image the user provides.
9. Claude renders the final at full quality in the session and sends the file. Never push rendering onto the user.
10. Create word timing as each act is built, never as a separate pass afterwards.
