"""Recolour the painted J/Q/K/A faces (assets/cards/<rank>_<suit>.png) from
the old suit inks to the four-colour deck in Data.SUIT_COLORS.
Each suit's own ink family (hue window around the old ink) moves to the new
hue, keeping each pixel's shading. Run once from the project folder.
"""
import colorsys, glob, os
from PIL import Image

def hsv(hexs):
    r, g, b = (int(hexs[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)

# suit: (old ink, new ink, hue window in degrees)
SUITS = {0: ("2c3564", "2a2733", 22), 1: ("f90d49", "d42a35", 16),
         2: ("155c5d", "1d8443", 24), 3: ("fa4d27", "2b6fd6", 13)}

for path in sorted(glob.glob("assets/cards/*_*.png")):
    suit = int(os.path.basename(path)[:-4].split("_")[1])
    old, new, win = SUITS[suit]
    oh, os_, ov = hsv(old)
    nh, ns, nv = hsv(new)
    im = Image.open(path).convert("RGBA")
    px = im.load()
    changed = 0
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            d = ((h - oh + 0.5) % 1.0) - 0.5
            if s < 0.3 or abs(d) * 360 > win:
                continue
            h2 = (nh + d) % 1.0
            s2 = min(1.0, s * ns / os_)
            v2 = min(1.0, v * nv / ov)
            r2, g2, b2 = colorsys.hsv_to_rgb(h2, s2, v2)
            px[x, y] = (round(r2 * 255), round(g2 * 255), round(b2 * 255), a)
            changed += 1
    im.save(path)
    print(path, changed)
