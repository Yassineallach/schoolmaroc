"""Turn the painted charm cards (assets/charms/<id>.png) into pixel-art
cards (assets/charms_pixel/<id>.png).

Each card is reduced to 80 x 100 pixels with 32 flat colours (no
dithering), then stored at 4x with nearest-neighbour scaling so every art
pixel stays a crisp square in game. Run from the project root:
    python3 tools/pixelize_charms.py
"""
import os
from PIL import Image, ImageEnhance

SRC, DST = "assets/charms", "assets/charms_pixel"
W, H, COLOURS, SCALE = 80, 100, 32, 4


def pixelate(im):
    rgb = Image.new("RGB", im.size, (255, 255, 255))
    rgb.paste(im, mask=im.split()[3])
    rgb = ImageEnhance.Contrast(ImageEnhance.Color(rgb).enhance(1.15)).enhance(1.08)
    small = rgb.resize((W, H), Image.BOX)
    q = small.quantize(colors=COLOURS, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGBA")
    q.putalpha(im.split()[3].resize((W, H), Image.BOX).point(lambda v: 255 if v > 128 else 0))
    return q.resize((W * SCALE, H * SCALE), Image.NEAREST)


if __name__ == "__main__":
    os.makedirs(DST, exist_ok=True)
    names = sorted(f for f in os.listdir(SRC) if f.endswith(".png"))
    for f in names:
        pixelate(Image.open(os.path.join(SRC, f)).convert("RGBA")).save(os.path.join(DST, f), optimize=True)
    print("pixelized", len(names), "cards into", DST)
