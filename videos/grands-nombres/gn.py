"""Shared pieces for "Les très grands nombres": real images with stand-ins while they download,
the chessboard (the film's motif) and grains of wheat.

Stand-ins are drawn only while an asset file is missing (development); every final image is a
real one from assets/ (Commons, credits in assets/credits.json).
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from vox import asset, font, W, H, PAL
import presets as P
import scenes as S

LAPIS = PAL.accent
GOLD = (190, 150, 70)
IVORY = (247, 244, 238)


def have(code):
    return os.path.exists(asset(f'{code}.jpg'))


def image(code, size=(1600, 1000), label=None):
    """The real image, or a plain labelled stand-in while it is not downloaded yet."""
    if have(code):
        return Image.open(asset(f'{code}.jpg')).convert('RGB')
    im = Image.new('RGB', size, (214, 206, 190))
    d = ImageDraw.Draw(im)
    d.rectangle((6, 6, size[0] - 7, size[1] - 7), outline=(150, 140, 120), width=4)
    d.text((size[0] / 2, size[1] / 2), f'{code}  {label or ""}', font=font('Inter600.ttf', 54), fill=(110, 100, 86), anchor='mm')
    return im


def crop_frac(im, box):
    w, h = im.size
    return im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))


# ------------------------------------------------------------------ grains
def grain_sprite(length=62, seed=0):
    """One grain of wheat: cut from the real macro photo (R02) when present, else drawn."""
    rng = np.random.default_rng(seed)
    if have('R02'):
        im = Image.open(asset('R02.jpg')).convert('RGB')
        a = np.asarray(im, np.float32)
        lum = a.mean(2)
        sat = a.max(2) - a.min(2)
        mask = ((sat > 38) | (lum < 150)).astype(np.uint8) * 255      # the grain against its pale ground
        m = Image.fromarray(mask).filter(ImageFilter.MedianFilter(9)).filter(ImageFilter.GaussianBlur(1.2))
        bb = m.point(lambda v: 255 if v > 128 else 0).getbbox()
        a = m.crop(bb)
        g = S.treated(im.crop(bb)).convert('RGBA')      # the identity's treatment, then the cut-out's alpha
        g.putalpha(a)
    else:
        g = Image.new('RGBA', (200, 110), (0, 0, 0, 0))
        d = ImageDraw.Draw(g)
        d.ellipse((6, 8, 194, 102), fill=(201, 158, 86, 255))
        d.line((20, 55, 180, 52), fill=(160, 112, 52, 255), width=5)
    k = length / g.width
    g = g.resize((length, max(4, int(g.height * k))), Image.LANCZOS)
    return g.rotate(rng.uniform(0, 360), Image.BICUBIC, expand=True)


_GRAINS = [grain_sprite(seed=i) for i in range(8)]


def scatter(layer, cx, cy, n, spread, t, start, seed=0, dur=0.5, size=1.0):
    """n grains falling into a square around (cx, cy), staggered irregularly."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        at = start + (dur * (i / max(1, n - 1)) ** 0.7 if n > 1 else 0) + rng.uniform(0, 0.06)
        k = P.clamp01((t - at) / 0.22)
        if k <= 0:
            continue
        g = _GRAINS[(i + seed) % len(_GRAINS)]
        if size != 1.0:
            g = g.resize((max(4, int(g.width * size)), max(4, int(g.height * size))), Image.LANCZOS)
        x = cx + rng.uniform(-spread, spread)
        y = cy + rng.uniform(-spread, spread)
        P.put(layer, g, x, y - 26 * (1 - P.ease_out(k)), lift=0.15 * (1 - k), sh_op=0.22)


# ------------------------------------------------------------------ the chessboard
def board_image(size=760, seed=8):
    """An 8 x 8 board printed on ivory card: lapis squares, ink frame, a paper edge."""
    pad = 34
    n = size + 2 * pad
    im = P.paper_card(n, n, seed=seed, colour=IVORY)
    d = ImageDraw.Draw(im)
    s = size / 8
    for i in range(8):
        for j in range(8):
            if (i + j) % 2:
                x0, y0 = pad + i * s, pad + j * s
                d.rectangle((x0, y0, x0 + s, y0 + s), fill=(205, 212, 230, 255))
    d.rectangle((pad - 3, pad - 3, pad + size + 3, pad + size + 3), outline=PAL.ink + (255,), width=4)
    return im, pad, s


def square_centre(cx, cy, size, k, pad=34):
    """Centre on screen of square k (1..64), counted row by row from the top-left, for a board
    of `size` placed with its centre at (cx, cy)."""
    s = size / 8
    i, j = (k - 1) % 8, (k - 1) // 8
    x0 = cx - size / 2
    y0 = cy - size / 2
    return x0 + (i + 0.5) * s, y0 + (j + 0.5) * s
