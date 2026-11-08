"""Animated editorial background (the original reference design) + episode theme selection.

motion_bg(t) returns the background of the theme named in <project>/episode.json
({"theme": "cosmic_atlas"}; default "editorial"). Themes live in themes.py.
The editorial design below was recreated in code from the user's first reference image.

motion_bg(t) -> RGB PIL image 1920x1080 for film time t (seconds). Same design, colours and layout
as the reference; every element drifts on its own slow cycle (20-40 s) for depth, thin lines
extend and retract, dots breathe, and the paper grain shimmers very slightly.
All geometry below is measured in the reference's own 1672x941 pixels and scaled by S.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
S = W / 1672.0
SS = 3  # supersampling for anti-aliased edges

PAPER = (248, 231, 205)
ORANGE = (205, 88, 48)
BEIGE = (233, 214, 187)
BAND = (221, 200, 170)
LINE = (92, 82, 72)
ARC = (150, 132, 112)
FAINT = (214, 198, 174)
DOT = (168, 152, 132)
TAU = 2 * math.pi


def _noise(h, w, scale, seed, amp):
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, (max(2, h // scale), max(2, w // scale))).astype(np.float32)
    n = np.asarray(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32)
    return (n - 128) / 128.0 * amp


def _paper():
    a = np.empty((H, W, 3), np.float32)
    a[:] = PAPER
    a += _noise(H, W, 60, 1, 5)[..., None]          # broad mottling
    a += _noise(H, W, 6, 2, 3)[..., None]           # mid speckle
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = ((xx / W - 0.5) ** 2 + (yy / H - 0.5) ** 2)
    a -= (v * 9)[..., None]                         # very soft edge darkening
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    r = np.random.default_rng(3)
    for _ in range(1400):                           # paper fibres
        x, y = r.uniform(0, W), r.uniform(0, H)
        L, ang = r.uniform(3, 10), r.uniform(0, math.pi)
        c = int(r.uniform(228, 240))
        d.line([(x, y), (x + L * math.cos(ang), y + L * math.sin(ang))], fill=(c, c - 16, c - 40))
    return np.asarray(img.filter(ImageFilter.GaussianBlur(0.6)), np.float32)


_BASE = _paper()
BG1 = Image.fromarray((_BASE * (1 + 0.022 * _noise(H, W, 1, 11, 1.0)[..., None])).clip(0, 255).astype(np.uint8))
BG2 = Image.fromarray((_BASE * (1 + 0.022 * _noise(H, W, 1, 12, 1.0)[..., None])).clip(0, 255).astype(np.uint8))


class Tile:
    """A pre-rendered, anti-aliased, textured shape placed at (x0, y0) in frame pixels."""

    def __init__(self, bbox, shape, colour, alpha=1.0, texture=0.0, seed=0, scuff=False):
        x0, y0, x1, y1 = [int(round(v * S)) for v in bbox]
        x0 -= 4; y0 -= 4; x1 += 4; y1 += 4
        self.x0, self.y0 = x0, y0
        w, h = x1 - x0, y1 - y0
        m = Image.new('L', (w * SS, h * SS), 0)
        shape(ImageDraw.Draw(m), lambda x, y: ((x * S - x0) * SS, (y * S - y0) * SS))
        m = m.resize((w, h), Image.LANCZOS)
        col = np.empty((h, w, 3), np.float32)
        col[:] = colour
        if texture:
            col += _noise(h, w, 40, seed, texture)[..., None]
            col += _noise(h, w, 3, seed + 1, texture * 0.6)[..., None]
        if scuff:
            r = np.random.default_rng(seed + 2)
            sc = Image.new('L', (w, h), 0)
            d = ImageDraw.Draw(sc)
            for _ in range(int(w * h / 900)):
                x, y = r.uniform(0, w), r.uniform(0, h)
                L, ang = r.uniform(4, 22), r.uniform(0, math.pi)
                d.line([(x, y), (x + L * math.cos(ang), y + L * math.sin(ang))], fill=int(r.uniform(60, 160)))
            sc = np.asarray(sc.filter(ImageFilter.GaussianBlur(0.7)), np.float32)[..., None] / 255.0
            col = col * (1 - sc * 0.35) + np.array((236, 150, 105), np.float32) * (sc * 0.35)
        self.rgb = Image.fromarray(col.clip(0, 255).astype(np.uint8))
        self.mask = m.point(lambda v: int(v * alpha))

    def place(self, canvas, dx, dy):
        fx, fy = dx - math.floor(dx), dy - math.floor(dy)
        rgb, mask = self.rgb, self.mask
        if fx or fy:  # sub-pixel shift so slow drifts glide instead of stepping
            tr = (1, 0, -fx, 0, 1, -fy)
            rgb = rgb.transform(rgb.size, Image.AFFINE, tr, Image.BILINEAR)
            mask = mask.transform(mask.size, Image.AFFINE, tr, Image.BILINEAR)
        canvas.paste(rgb, (self.x0 + math.floor(dx), self.y0 + math.floor(dy)), mask)


def circle(cx, cy, r):
    return lambda d, p: d.ellipse([*p(cx - r, cy - r), *p(cx + r, cy + r)], fill=255)


def ring(cx, cy, r, width):
    return lambda d, p: d.ellipse([*p(cx - r, cy - r), *p(cx + r, cy + r)], outline=255, width=int(width * SS))


def poly(pts):
    return lambda d, p: d.polygon([p(x, y) for x, y in pts], fill=255)


# ---- the elements of the reference, back to front ----
BAND1 = Tile((-80, 560, 420, 1010), poly([(-80, 578), (80, 578), (440, 1010), (-80, 1010)]), BAND, 0.6, 4, 20)
STRIPE = Tile((-120, 540, 420, 1010), poly([(-120, 560), (-40, 560), (400, 1010), (320, 1010)]), BAND, 0.35, 3, 29)
BAND2 = Tile((-80, 700, 520, 1010), poly([(-80, 722), (305, 722), (530, 1010), (-80, 1010)]), BAND, 0.5, 4, 21)
RECT1 = Tile((1531, 578, 1720, 1010), poly([(1531, 578), (1720, 578), (1720, 1010), (1531, 1010)]), BEIGE, 0.9, 3, 22)
RECT2 = Tile((1243, 868, 1740, 1010), poly([(1243, 868), (1740, 868), (1740, 1010), (1243, 1010)]), BAND, 0.35, 3, 23)
TR_CIRC = Tile((1250, -260, 1810, 290), circle(1530, 16, 272), BEIGE, 1.0, 4, 24)
TL_ARC = Tile((-210, -300, 350, 255), ring(72, -24, 273, 1.3), ARC, 0.85)
BR_ARC = Tile((1360, 670, 2040, 1350), ring(1700, 1010, 335, 1.3), ARC, 0.85)
TL_CIRC = Tile((-235, -295, 275, 215), circle(20, -40, 252), ORANGE, 1.0, 12, 25, True)
BR_CIRC = Tile((1400, 710, 2000, 1310), circle(1700, 1010, 295), ORANGE, 1.0, 12, 26, True)
BL_BAR = Tile((-80, 885, 300, 1000), poly([(-80, 885), (240, 885), (290, 950), (-80, 950)]), ORANGE, 1.0, 10, 27, True)
TR_BAR = Tile((1573, 107, 1760, 133), poly([(1573, 107), (1760, 107), (1760, 133), (1573, 133)]), ORANGE, 1.0, 8, 28, True)

_dot = Image.new('L', (12 * SS, 12 * SS), 0)
ImageDraw.Draw(_dot).ellipse((SS * 2, SS * 2, SS * 10, SS * 10), fill=255)
DOT_SPRITE = _dot.resize((12, 12), Image.LANCZOS)
_r = np.random.default_rng(9)
DOTS = []
for gx, gy in ((297, 112), (1286, 732)):
    for i in range(6):
        for j in range(4):
            DOTS.append((gx + i * 29.6, gy + j * 28.4, _r.uniform(0, TAU), _r.uniform(5.0, 9.0), 0.45 + 0.4 * (i / 5)))


def _s(t, period, phase=0.0):
    return math.sin(TAU * t / period + phase)


def _hline(c, x0, x1, y, colour, alpha, width=2):
    x0, x1 = int(round(x0 * S)), int(round(x1 * S))
    y = int(round(y * S))
    if x1 > x0:
        c.paste(colour, (x0, y, x1, y + width), Image.new('L', (x1 - x0, width), int(255 * alpha)))


def _vline(c, x, y0, y1, colour, alpha, width=2):
    y0, y1 = int(round(y0 * S)), int(round(y1 * S))
    x = int(round(x * S))
    if y1 > y0:
        c.paste(colour, (x, y0, x + width, y1), Image.new('L', (width, y1 - y0), int(255 * alpha)))


def _editorial(t):
    w = 0.5 + 0.5 * _s(t, 7.0)                       # grain shimmer: two grain fields crossfade
    c = Image.blend(BG1, BG2, w)

    # far layer: slow, large travel along their own diagonals
    k = 12 * _s(t, 34)
    BAND1.place(c, k * 0.65, k * 0.76)
    k = 9 * _s(t, 41, 2.4)
    STRIPE.place(c, k * 0.70, k * 0.72)
    k = 16 * _s(t, 27, 1.3)
    BAND2.place(c, k * 0.72, k * 0.69)
    RECT1.place(c, 0, 10 * _s(t, 32))
    RECT2.place(c, 14 * _s(t, 29, 2.0), 0)
    TR_CIRC.place(c, -12 * _s(t, 37), 7 * _s(t, 31, 2.0))

    # thin lines: extend and retract
    _vline(c, 1603, 290, 290 + 470 * (0.82 + 0.18 * _s(t, 24, 0.4)), FAINT, 0.9)
    TL_ARC.place(c, -5 * _s(t, 33), 4 * _s(t, 27))
    BR_ARC.place(c, 6 * _s(t, 30, 1.1), -5 * _s(t, 35, 0.3))

    # near layer: the orange shapes
    TL_CIRC.place(c, 8 * _s(t, 29), 6 * _s(t, 23, 1.0))
    BR_CIRC.place(c, -7 * _s(t, 31, 0.7), -6 * _s(t, 26))
    BL_BAR.place(c, 10 * _s(t, 26, 1.0), 0)
    TR_BAR.place(c, 14 * _s(t, 25, 0.5), 0)

    _vline(c, 87, 0, 295 * (0.86 + 0.14 * _s(t, 19)), LINE, 0.85)
    _hline(c, 1372 + 45 * (0.5 - 0.5 * _s(t, 21, 0.8)), 1672, 82, LINE, 0.85)
    _hline(c, 52, 632 - 70 * (0.5 - 0.5 * _s(t, 23, 2.2)), 858, LINE, 0.85)

    # dots breathe, each on its own phase
    for x, y, ph, per, base in DOTS:
        k = base * (0.35 + 0.65 * (0.5 + 0.5 * math.sin(TAU * t / per + ph)))
        c.paste(DOT, (int(x * S) - 6, int(y * S) - 6), DOT_SPRITE.point(lambda v, k=k: int(v * k)))
    return c


# ---- episode theme selection: episode.json {"theme": "<name>"} in the project folder ----
import json as _json, os as _os
_CFG = _os.path.join(_os.environ.get('VOX_PROJECT', _os.getcwd()), 'episode.json')
THEME_NAME = _json.load(open(_CFG)).get('theme') if _os.path.exists(_CFG) else None
if not THEME_NAME:                      # no theme named: the identity's own (history -> astrolabe)
    try:
        import palette as _pl, identities as _id
        THEME_NAME = _id.DEFAULT_THEME.get(_pl.IDENTITY.base, 'editorial')
    except Exception:
        THEME_NAME = 'editorial'


def motion_bg(t):
    import themes
    return themes.THEMES[THEME_NAME].frame(t)


if __name__ == '__main__':
    import subprocess, sys
    out, secs = sys.argv[1], float(sys.argv[2])
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30',
                          '-i', '-', '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for f in range(int(secs * 30)):
        p.stdin.write(motion_bg(f / 30).tobytes())
    p.stdin.close(); p.wait()
