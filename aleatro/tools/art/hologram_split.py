"""Split the Hologram charm's art the way Balatro builds its Hologram joker:
a plain card (the frame) and the figure as a separate floating sprite that
hologram.gdshader draws as a glowing projection.

  python3 tools/art/hologram_split.py            # writes hologram_frame/soul.png
  python3 tools/art/hologram_split.py --report   # just lists the pieces found
"""
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ART = Path(__file__).resolve().parents[2] / "assets" / "charms_pixel"
PAPER = 225  # a pixel with every channel above this is card paper

def components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)]); seen[y, x] = True; pts = []
                while q:
                    cy, cx = q.popleft(); pts.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; q.append((ny, nx))
                ys = [p[0] for p in pts]; xs = [p[1] for p in pts]
                out.append({"pts": pts, "box": (min(xs), min(ys), max(xs), max(ys))})
    return out

def main():
    im = np.array(Image.open(ART / "hologram.png").convert("RGBA")).astype(np.float32)
    rgb, a = im[..., :3], im[..., 3]
    ink = (rgb.min(axis=2) <= PAPER) & (a > 200)
    parts = components(ink)
    # the JOKER lettering runs down the two outer columns; the figure is the rest
    h, w = ink.shape
    def is_letter(c):  # lettering, or the card's own border
        x0, y0, x1, y1 = c["box"]
        return x1 < w * 0.19 or x0 > w * 0.82 or y0 > h * 0.97
    figure = [c for c in parts if not is_letter(c)]
    if "--report" in sys.argv:
        for c in sorted(parts, key=lambda c: -len(c["pts"]))[:20]:
            print(len(c["pts"]), c["box"], "letter" if is_letter(c) else "figure")
        return
    mask = np.zeros_like(ink)
    for c in figure:
        for y, x in c["pts"]:
            mask[y, x] = True
    # the pale face and highlights are paper-coloured: take in every pocket
    # of paper the figure closes around
    outside = np.zeros_like(mask)
    q = deque((y, x) for y in range(h) for x in (0, w - 1)) + deque((y, x) for x in range(w) for y in (0, h - 1))
    for y, x in q:
        outside[y, x] = not mask[y, x]
    q = deque(p for p in q if outside[p])
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and not outside[ny, nx] and not mask[ny, nx]:
                outside[ny, nx] = True; q.append((ny, nx))
    mask = ~outside
    # frame: the figure painted over with the paper around it
    paper = np.median(rgb[~ink & (a > 200)], axis=0)
    frame = im.copy()
    frame[mask, :3] = paper
    Image.fromarray(frame.astype(np.uint8)).save(ART / "hologram_frame.png")
    # soul: the figure alone, recoloured in projector teal and see-through,
    # as Balatro's floating sprite is (hologram.fs keeps its translucent pixels
    # and makes the solid ones vanish)
    lum = (rgb @ np.array([0.299, 0.587, 0.114])) / 255.0
    lo, hi = np.percentile(lum[mask], [3, 97])
    lum = np.clip((lum - lo) / (hi - lo), 0.0, 1.0)
    dark, light = np.array([10, 80, 95]), np.array([200, 255, 240])
    soul = np.zeros_like(im)
    soul[..., :3] = dark + (light - dark) * lum[..., None]
    soul[..., 3] = np.where(mask, 150, 0)
    # at 3/4 size (each 4px art pixel becomes 3px), so with Balatro's float
    # scale on top it still sits between the JOKER lettering
    img = Image.fromarray(soul.astype(np.uint8))
    small = img.resize((w * 3 // 4, h * 3 // 4), Image.NEAREST)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(small, ((w - small.width) // 2, (h - small.height) // 2))
    out.save(ART / "hologram_soul.png")
    print("figure pixels:", int(mask.sum()))

main()
