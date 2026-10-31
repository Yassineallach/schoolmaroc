# Asset prompts: storybook illustration, never anime

Hand the user prompts they can paste with no edits. Every prompt carries the full style block,
so nothing depends on the image tool remembering the style.

## Workflow: master sheets first

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

Adapt the palette line to the subject and the user's guide. Keep the structure and the **NOT anime** line.

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
