"""Turn the painted charm cards (assets/charms/<id>.png) into pixel-art
cards (assets/charms_pixel/<id>.png).

Each card is reduced to 80 x 100 pixels with 32 flat colours (no
dithering), then stored at 4x with nearest-neighbour scaling so every art
pixel stays a crisp square in game. The rounded card corners are cut at the
full 4x size, smooth and anti-aliased, so only the art is pixelated. Run from the project root:
    python3 tools/pixelize_charms.py
"""
import os
from PIL import Image, ImageDraw, ImageEnhance

SRC, DST = "assets/charms", "assets/charms_pixel"
W, H, COLOURS, SCALE = 80, 100, 32, 4
RADIUS = 19  # corner radius at 4x, matching the painted cards


def pixelate(im):
    rgb = Image.new("RGB", im.size, (255, 255, 255))
    rgb.paste(im, mask=im.split()[3])
    rgb = ImageEnhance.Contrast(ImageEnhance.Color(rgb).enhance(1.15)).enhance(1.08)
    small = rgb.resize((W, H), Image.BOX)
    q = small.quantize(colors=COLOURS, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGBA")
    big = q.resize((W * SCALE, H * SCALE), Image.NEAREST)
    big.putalpha(_corner_mask(big.size))
    return big


def _corner_mask(size):
    """A rounded-rectangle alpha mask, drawn 4x larger and scaled down so its
    edge is smooth."""
    k = 4
    m = Image.new("L", (size[0] * k, size[1] * k), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] * k - 1, size[1] * k - 1), radius=RADIUS * k, fill=255)
    return m.resize(size, Image.LANCZOS)


if __name__ == "__main__":
    os.makedirs(DST, exist_ok=True)
    names = sorted(f for f in os.listdir(SRC) if f.endswith(".png"))
    for f in names:
        pixelate(Image.open(os.path.join(SRC, f)).convert("RGBA")).save(os.path.join(DST, f), optimize=True)
    print("pixelized", len(names), "cards into", DST)
