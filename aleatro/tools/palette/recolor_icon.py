"""Move the app icon's swirl to the Velvet Lounge palette: reds to rose,
blues to teal, the dark ground to plum. The card (mask) is left alone.
Usage: python3 tools/palette/recolor_icon.py <src.png> <card mask.png>
writes icon.png, icon_background.png and the Play Games 512 icon.
"""
import colorsys, sys
from PIL import Image

def recolor(im, m=None):
    im = im.convert("RGBA"); px = im.load(); mp = m.load() if m else None
    for y in range(im.height):
        for x in range(im.width):
            if mp and mp[x, y] > 128:
                continue
            r, g, b, a = px[x, y]
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            hd = h * 360
            if v < 0.32 or s < 0.2:  # the dark ground -> plum
                nh, s2, v2 = 268, max(s, 0.45), v * 1.05
            elif hd >= 300 or hd < 40:  # reds and oranges -> rose
                d = ((hd - 355 + 180) % 360) - 180
                nh, s2, v2 = (339 + d * 0.6) % 360, s * 0.92, v * 0.95
            elif 160 <= hd < 260:  # blues -> teal
                nh, s2, v2 = 172 + (hd - 210) * 0.4, s * 0.85, v * 0.72
            else:
                continue
            r2, g2, b2 = colorsys.hsv_to_rgb(nh / 360, min(1, s2), min(1, v2))
            px[x, y] = (round(r2 * 255), round(g2 * 255), round(b2 * 255), a)
    return im

src = Image.open(sys.argv[1]).convert("RGB")
mask = Image.open(sys.argv[2]).convert("L")
out = recolor(src, mask)
i512 = out.resize((512, 512), Image.LANCZOS)
i512.save("icon.png")
i512.convert("RGB").save("tools/play_games/properties/icon_512.png")
recolor(Image.open("icon_background.png")).convert("RGB").save("icon_background.png")

# the adaptive foreground's card cutout keeps a thin ring of swirl around the
# card; recolour only that ring (pixels within RING of the transparent edge)
from PIL import ImageFilter
RING = 9
fg = Image.open("icon_foreground.png").convert("RGBA")
solid = fg.getchannel("A").point(lambda a: 255 if a > 8 else 0)
inner = solid.filter(ImageFilter.MinFilter(RING * 2 + 1))
ring = Image.eval(inner, lambda a: 255 - a)  # 255 where near the edge
rc = recolor(fg, inner)  # mask: skip the inner card
fg.paste(rc, (0, 0), ring)
fg.save("icon_foreground.png")
