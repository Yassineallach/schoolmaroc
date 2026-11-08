# Asset prompts: storybook illustration, never anime

Hand the user prompts they can paste with no edits. Every prompt carries the full style block,
so nothing depends on the image tool remembering the style.

## Reference-image workflow (default; ChatGPT and any tool that takes images)

Long style descriptions get averaged into a generic look. With ChatGPT, a 400-word style block produced images that looked nothing like the user's references. Instead:

1. **Pick ONE reference** that shows the style most clearly, and have the user crop it to just that image. A clean figure with few overlays works best.
2. **Short prompt.** The style goes in one line, then one line of what to ignore, then the subject:

```
Use ONLY the drawing style of the attached image: <4-5 key traits, e.g. navy ink outline, hair as a solid mass with fine light strand lines, big flat hard-edged shadows in indigo, violet and lavender, cream highlights, no gradients>.
Ignore <what in the reference is not style: the circles, lines, card, icons>. Do not copy the person.

Draw: <character in one or two sentences: age, build, hair, skin, face, costume>. <Framing and pose>.
Plain empty ivory background. One figure only.
```

3. **One figure, not a sheet,** until the style is right.
4. **Fix in follow-up messages,** one change each, in the same chat:
   - "Same image, but remove the lines and circles."
   - "Same image, flatter shadows, fewer lines on the clothes."
5. **Lock it.** Once a figure is approved, it replaces the original reference for everything after it:

```
Same character and exact same drawing style as the attached image.
Draw him <pose>, full body. Plain empty ivory background. One figure only.
```

New characters use the same pattern: `Exact same drawing style as the attached image. Draw: <new character>. ...`

**Analysing a reference.**
- **Name the traits:** outline colour and weight, how hair is drawn, how shadows are shaped (hard or soft, how many tones), the palette, and the amount of detail.
- **Name what to ignore:** app UI, cards, bookmark icons, geometric overlays, text, and the real person depicted. Never ask for a likeness.
- **Keep figures separable from the paper.** If the reference leaves skin as paper colour, ask for a flat skin tone instead, so the cut-out survives.

### Style: linocut / engraved editorial (user's second style)

Traits that worked when this was the user's reference:

- dark navy-indigo ink contour;
- hair as a solid mass cut by fine parallel cream strand lines;
- large flat hard-edged shadows in deep indigo, muted violet and periwinkle-lavender;
- cream highlights;
- no gradients;
- tiny coral-red accents only.

The reference sheets were book-cover cards with circles, triangles, dot-lines and a bookmark icon. Tell the model to ignore all of these.

### Ready-to-copy prompt shape (used on A Brief History of Time, ChatGPT)

Two style lines, then one line per asset. Give each asset as its own complete code block.

```
Use ONLY the drawing style of the attached image: dark navy-indigo ink outline; dark areas as solid masses cut by fine cream lines; large flat hard-edged shadows in deep indigo, muted violet and periwinkle-lavender; cream highlights; no gradients; tiny coral-red accents only.
Ignore the circles, triangles, dots and lines. Do not copy the person.

Paint: <scene>. Fill the whole 16:9 frame edge to edge, no empty paper border. No text.
```

Cut-outs end instead with: `Draw: <object>. Fill every surface with flat colour, nothing left paper-white. Plain empty ivory background. One object only, fully visible. No text.`
(The reference left faces paper-coloured; asking for filled surfaces keeps the cut-out clean.)
A follow-up asset in the same chat can say: `Same <object> and exact same drawing style as the previous image. Draw it <change>.`

## Workflow: master sheets first (storybook style, text-only tools)

1. **Masters.** Generate one character master sheet per main character with **no reference image**. The user picks the version closest to their visual guide.
2. **Poses.** Every pose prompt attaches the approved master:
   - as the **character reference** for that character;
   - as the **style reference** for everything else.
3. **Old sheets.** Never attach earlier rejected sheets (for example, anime-looking ones). They pull the style back.
4. **Naming.** Number assets so the user can reply in shorthand:
   - `C01` master, `C01-A…H` poses;
   - `E01…` environments;
   - `P01…` props and plates;
   - `A01…` audience or other shots.
5. **Background.** Characters and props go on a **plain warm ivory background**, one figure only, full body visible, no text. That keeps the cut-out clean (see SKILL.md, phase 4).
6. **Shot plates.** Close-ups and shots that need a setting are generated **with their own painted background** at 16:9. They are used as-is (as a `PhotoCard`) and never cut out or given an extra background.

## CH: character style block (append to every character or pose prompt)

```
Style: 2D hand-drawn editorial illustration for an educational animated short film, in the spirit of a hand-illustrated storybook rather than anime. Simplified stylized anatomy with natural, varied proportions; slightly simplified head; small simple eyes with readable direction; clearly defined eyebrows; minimal nose; simple mouth; soft, natural hair shapes drawn as simple masses. Organic hand-drawn outlines in deep brown (#3B2A20), medium weight around the silhouette and thinner inside, with slight irregularity. Flat color fills with one shadow tone, one light tone and only a few small highlights; restrained painterly shading; subtle paper grain and light brush texture; muted earthy palette of warm ivory, terracotta, rust red, muted blue, desaturated green, deep brown and muted gold; soft warm directional light. NOT anime, NOT manga, no large glossy eyes, no spiky anime hair, no sharp cel-shaded highlights, no 3D render, no photorealism, no glossy corporate vector style, no heavy gradients, no glow.
```

Adapt the palette line to the subject, the user's guide and the episode's visual identity: take the colours from `python SK/scripts/palette.py` (its grounds, accents and dark tone), so generated plates belong to the same film as the type, charts and paper. For a monochrome identity (`manga_ink`) ask for black ink and screentone only. Keep the structure and the **NOT anime** line.

## EN: environment style block

```
Style: hand-painted background plate for a 2D educational animated short film, storybook illustration feel. Clear foreground, middle ground and background layers; simple readable shapes; organic deep-brown outlines on key forms; flat fills with soft painterly shading and subtle paper grain; muted earthy palette; soft directional light. No characters unless stated, no text, no labels. NOT anime, no 3D render, no photorealism, no heavy gradients, no glow. 16:9 widescreen.
```

## Patterns

**Master sheet**

```
Character reference sheet of <name>, <age/role>. <build>; <hair as a simple mass>; <skin>; <small eye colour>; <expression>. <costume, item by item>. Show as separate, evenly spaced figures: front view, three-quarter view, side view, full-body standing pose, <story poses>, and four head close-ups: <emotions>. Plain warm ivory background, no text, no labels. <CH block>
```

**Pose cut-out** (character reference: master)

```
Single full-body figure of the same <person> as the reference image, <name>, <pose and direction, e.g. facing three-quarter left>, <expression>, exact same face, hair, skin tone, <costume items> as the reference. One figure only, centered, full body visible from head to boots, plain warm ivory background. <CH block> No text, no labels, no other figures, no photorealism, no 3D render.
```

**Close-up plate**

```
Extreme close-up of <detail> of the same <person> as the reference image, <what is visible>, <light>, <surroundings>. <CH block> No text, no photorealism, no 3D render. 16:9 widescreen.
```

## Continuity rules: spell them out in every prompt

- Give props a **side and a count**, and repeat them in capitals when the model drifts. For example: "ONE red scarf tied tightly around his LEFT WRIST (not the elbow, not the right arm)".
- When a character changes over the story (age, caste, injury), name what stays (face structure, skin, scar) and what changes.
- Costume colours must come from the subject, not the palette. A pale or gold costume will need `--mode gentle` when cutting out.

## Things code draws better than image models

Do **not** prompt for these. The engine draws them crisply, in the collage style:

- documents and letters;
- stamps ("RIGGED", "CLASSIFIED");
- headlines and typed captions;
- maps with marker routes;
- charts, arrows and circles;
- caste or org diagrams made of small cut-outs;
- book covers;
- strike-throughs.

## Things to ask the user for, rather than draw in code

Ask the user for these:

- people and faces;
- animals;
- vehicles;
- landscapes;
- anything organic;
- **real people**, such as the author's portrait.

For a real person, ask the user for a photo they have rights to use. Never generate a likeness.
