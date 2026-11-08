"""Episode background themes, all in the design language of the original editorial background
(bg_motion.py): cream paper with grain and fibres, large flat textured terracotta and beige
shapes anchored to the corners, translucent diagonal bands, thin dark lines and arcs that
extend and retract, small dot grids that breathe, and an open centre for the collage.

Each episode keeps that vocabulary but gets its own shapes and arrangement, chosen from the
subject. Themes are declarative: a list of elements, each with its own slow drift, so every
decoration moves independently.

  THEMES['cosmic_atlas'].frame(t) -> RGB 1920x1080
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
SS = 3
TAU = 2 * math.pi

# shared palette (from the original reference)
PAPER = (248, 231, 205)
TERRA = (205, 88, 48)
BEIGE = (233, 214, 187)
BAND = (221, 200, 170)
LINE = (92, 82, 72)
ARC = (150, 132, 112)
FAINT = (214, 198, 174)
DOT = (168, 152, 132)
INDIGO = (62, 62, 118)


def _s(t, period, phase=0.0):
    return math.sin(TAU * t / period + phase)


def _noise(h, w, scale, seed, amp):
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, (max(2, h // scale), max(2, w // scale))).astype(np.float32)
    n = np.asarray(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32)
    return (n - 128) / 128.0 * amp


def paper(colour=PAPER, seed=1):
    """The reference paper: soft mottling, speckle, faint edge darkening, fibres; two grain
    variants that crossfade for a barely visible shimmer."""
    a = np.empty((H, W, 3), np.float32)
    a[:] = colour
    a += _noise(H, W, 60, seed, 1.2)[..., None] + _noise(H, W, 6, seed + 1, 2.2)[..., None]      # smooth paper, fine grain
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a -= (((xx / W - 0.5) ** 2 + (yy / H - 0.5) ** 2) * 9)[..., None]
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    r = np.random.default_rng(seed + 2)
    for _ in range(1400):
        x, y = r.uniform(0, W), r.uniform(0, H)
        L, ang = r.uniform(3, 10), r.uniform(0, math.pi)
        c = int(r.uniform(228, 240))
        d.line([(x, y), (x + L * math.cos(ang), y + L * math.sin(ang))], fill=(c, c - 16, c - 40))
    base = np.asarray(img.filter(ImageFilter.GaussianBlur(0.6)), np.float32)
    return tuple(Image.fromarray((base * (1 + 0.022 * _noise(H, W, 1, seed + k, 1.0)[..., None])).clip(0, 255).astype(np.uint8)) for k in (11, 12))


class Tile:
    def __init__(self, bbox, draw, colour, alpha=1.0, texture=0.0, seed=0, scuff=False):
        x0, y0, x1, y1 = [int(round(v)) for v in bbox]
        x0 -= 4; y0 -= 4; x1 += 4; y1 += 4
        self.x0, self.y0 = x0, y0
        w, h = x1 - x0, y1 - y0
        m = Image.new('L', (w * SS, h * SS), 0)
        draw(ImageDraw.Draw(m), lambda x, y: ((x - x0) * SS, (y - y0) * SS), SS)
        m = m.resize((w, h), Image.LANCZOS)
        col = np.empty((h, w, 3), np.float32)
        col[:] = colour
        if texture:
            col += _noise(h, w, 40, seed, texture * 0.25)[..., None] + _noise(h, w, 3, seed + 1, texture * 0.4)[..., None]
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

    def place(self, c, dx=0.0, dy=0.0):
        if self.rgb.width * self.rgb.height > 350_000:   # big slow shapes move in whole pixels
            dx, dy = round(dx), round(dy)
        fx, fy = dx - math.floor(dx), dy - math.floor(dy)
        rgb, mask = self.rgb, self.mask
        if fx or fy:
            tr = (1, 0, -fx, 0, 1, -fy)
            rgb = rgb.transform(rgb.size, Image.AFFINE, tr, Image.BILINEAR)
            mask = mask.transform(mask.size, Image.AFFINE, tr, Image.BILINEAR)
        c.paste(rgb, (self.x0 + math.floor(dx), self.y0 + math.floor(dy)), mask)


# ---------------------------------------------------------------- element vocabulary
def circle(cx, cy, r):
    return (cx - r, cy - r, cx + r, cy + r), lambda d, p, ss: d.ellipse([*p(cx - r, cy - r), *p(cx + r, cy + r)], fill=255)


def ring(cx, cy, rx, ry=None, width=1.3):
    ry = ry or rx
    return (cx - rx, cy - ry, cx + rx, cy + ry), lambda d, p, ss: d.ellipse([*p(cx - rx, cy - ry), *p(cx + rx, cy + ry)], outline=255, width=max(1, int(width * ss)))


def polygon(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys)), lambda d, p, ss: d.polygon([p(x, y) for x, y in pts], fill=255)


def rect(x0, y0, x1, y1):
    return polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def capsule(x0, y0, x1, y1):
    return (x0, y0, x1, y1), lambda d, p, ss: d.rounded_rectangle([*p(x0, y0), *p(x1, y1)], radius=(y1 - y0) / 2 * ss, fill=255)


def segs(lst, width=1.3):
    xs = [v[0] for s in lst for v in s]
    ys = [v[1] for s in lst for v in s]
    return (min(xs), min(ys), max(xs), max(ys)), lambda d, p, ss: [d.line([p(*a), p(*b)], fill=255, width=max(1, int(width * ss))) for a, b in lst]


# element constructors. drift = (amp_x, amp_y, period_x, period_y, phase), in px and seconds
def shape(sh, colour, alpha=1.0, texture=3, scuff=False, drift=(8, 6, 29, 23, 0.0), seed=0):
    return ('tile', sh, colour, alpha, texture, scuff, drift, seed)


def terra(sh, drift=(8, 6, 29, 23, 0.0), seed=0):
    return shape(sh, TERRA, 1.0, 12, True, drift, seed)


def hline(x0, x1, y, grow=60, period=21, phase=0.0, end='left', colour=LINE, alpha=0.85):
    return ('hline', x0, x1, y, grow, period, phase, end, colour, alpha)


def vline(x, y0, y1, grow=40, period=19, phase=0.0, end='bottom', colour=LINE, alpha=0.85):
    return ('vline', x, y0, y1, grow, period, phase, end, colour, alpha)


def dots(x0, y0, cols=6, rows=4, step=34, seed=9):
    return ('dots', x0, y0, cols, rows, step, seed)


def orbiter(cx, cy, rx, ry, a0, a1, period, r, colour):
    return ('orbit', cx, cy, rx, ry, a0, a1, period, r, colour)


def tracer(pts, period, colour=TERRA, r=5, phase=0.0):
    return ('tracer', pts, period, colour, r, phase)


def diag(amp, period, phase=0.0, dx=0.66, dy=0.75):
    """drift along a diagonal (for the bands)"""
    return (amp * dx, amp * dy, period, period, phase - 1.0)


_DOT = {}


def _dot(c, x, y, r, colour, k):
    if k <= 0.02:
        return
    key = (round(r * 4) / 4, round(min(1.0, k) * 20))
    m = _DOT.get(key)
    if m is None:
        rr, n = key[0], int(key[0] * 2 + 4)
        m = Image.new('L', (n * SS, n * SS), 0)
        ImageDraw.Draw(m).ellipse((2 * SS, 2 * SS, (2 + 2 * rr) * SS, (2 + 2 * rr) * SS), fill=int(255 * key[1] / 20))
        m = _DOT[key] = m.resize((n, n), Image.LANCZOS)
    c.paste(colour, (int(x - m.width / 2), int(y - m.height / 2)), m)


class Theme:
    ink = (26, 26, 26)

    def __init__(self, name, label, elements, paper_colour=PAPER, seed=1):
        self.name, self.label, self.elements = name, label, elements
        self.paper_colour, self.seed = paper_colour, seed
        self._built = False

    def build(self):
        self.g1, self.g2 = paper(self.paper_colour, self.seed)
        self.items = []
        for i, e in enumerate(self.elements):
            if e[0] == 'tile':
                _, (bbox, draw), colour, alpha, tex, scuff, drift, seed = e
                self.items.append(('tile', Tile(bbox, draw, colour, alpha, tex, seed or (i * 7 + 3), scuff), drift))
            elif e[0] == 'dots':
                _, x0, y0, cols, rows, step, seed = e
                r = np.random.default_rng(seed)
                self.items.append(('dots', [(x0 + i * step, y0 + j * step * 0.96, r.uniform(0, TAU), r.uniform(5, 9), 0.45 + 0.4 * i / max(1, cols - 1))
                                            for i in range(cols) for j in range(rows)]))
            else:
                self.items.append(e)

    def frame(self, t):
        if not self._built:
            self.build()
            self._built = True
        c = Image.blend(self.g1, self.g2, 0.5 + 0.5 * _s(t, 7.0))
        for it in self.items:
            k = it[0]
            if k == 'tile':
                tile, (ax, ay, px, py, ph) = it[1], it[2]
                tile.place(c, ax * _s(t, px, ph), ay * _s(t, py, ph + 1.0))
            elif k == 'dots':
                for x, y, ph, per, base in it[1]:
                    _dot(c, x, y, 4, DOT, base * (0.35 + 0.65 * (0.5 + 0.5 * math.sin(TAU * t / per + ph))))
            elif k == 'hline':
                _, x0, x1, y, grow, per, ph, end, colour, alpha = it
                g = grow * (0.5 - 0.5 * _s(t, per, ph))
                a, b = (x0 + g, x1) if end == 'left' else (x0, x1 - g)
                c.paste(colour, (int(a), int(y), int(b), int(y) + 2), Image.new('L', (max(1, int(b) - int(a)), 2), int(255 * alpha)))
            elif k == 'vline':
                _, x, y0, y1, grow, per, ph, end, colour, alpha = it
                g = grow * (0.5 - 0.5 * _s(t, per, ph))
                a, b = (y0, y1 - g) if end == 'bottom' else (y0 + g, y1)
                c.paste(colour, (int(x), int(a), int(x) + 2, int(b)), Image.new('L', (2, max(1, int(b) - int(a))), int(255 * alpha)))
            elif k == 'orbit':
                _, cx, cy, rx, ry, a0, a1, per, r, colour = it
                a = a0 + (a1 - a0) * (0.5 + 0.5 * _s(t, per, -1.2))
                _dot(c, cx + rx * math.cos(a), cy + ry * math.sin(a), r, colour, 1.0)
            elif k == 'tracer':
                _, pts, per, colour, r, ph = it
                L = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:])]
                d = ((t / per + ph) % 1.0) * sum(L)
                for (a, b), l in zip(zip(pts[:-1], pts[1:]), L):
                    if d <= l:
                        _dot(c, a[0] + (b[0] - a[0]) * d / l, a[1] + (b[1] - a[1]) * d / l, r, colour, 1.0)
                        break
                    d -= l
        return c


# ================================================================== the episodes
THEMES = {}


def _add(th):
    THEMES[th.name] = th


# ---- this episode: A Brief History of Time ---------------------------------------
# Sun and orbits top-left, a ringed planet bottom-right, the diagonal bands become a light
# cone, dot grids read as star clusters, an indigo moon travels its orbit.
_add(Theme('cosmic_atlas', 'Cosmic atlas (this episode)', [
    shape(polygon([(-120, 1110), (60, 1110), (420, 640), (240, 640)]), BAND, 0.55, 4, drift=diag(10, 34)),
    shape(polygon([(240, 640), (420, 640), (690, 290), (510, 290)]), BAND, 0.32, 4, drift=diag(10, 34)),
    shape(rect(1560, 600, 1960, 1120), BEIGE, 0.85, 3, drift=(0, 10, 32, 32, 0.0)),
    shape(circle(1700, 1060, 300), BEIGE, 1.0, 4, drift=(-8, -6, 37, 31, 2.0)),
    shape(ring(1700, 1060, 470, 120, 1.4), ARC, 0.9, 0, drift=(-8, -6, 37, 31, 2.0)),
    shape(ring(30, -30, 330), ARC, 0.85, 0, drift=(-5, 4, 33, 27, 0.0)),
    shape(ring(30, -30, 470), ARC, 0.6, 0, drift=(4, -3, 39, 29, 1.0)),
    terra(circle(30, -30, 270), drift=(8, 6, 29, 23, 0.0)),
    terra(rect(1780, 120, 1990, 150), drift=(14, 0, 25, 25, 0.5)),
    terra(polygon([(-80, 1020), (260, 1020), (310, 1090), (-80, 1090)]), drift=(10, 0, 26, 26, 1.0)),
    orbiter(30, -30, 470, 470, 0.25, 1.15, 70, 13, INDIGO),
    orbiter(30, -30, 330, 330, 0.55, 1.25, 55, 6, TERRA),
    dots(360, 120), dots(1440, 820, 6, 4),
    hline(1560, 1920, 94, grow=50, period=21, phase=0.8),
    hline(60, 720, 985, grow=80, period=23, phase=2.2, end='right'),
    vline(100, 0, 330, grow=46, period=19),
    vline(1840, 330, 880, grow=90, period=24, phase=0.4, colour=FAINT, alpha=0.9),
], seed=31))

# ---- history: archive --------------------------------------------------------------
_add(Theme('archive', 'History: archive', [
    shape(rect(-40, -40, 420, 380), BEIGE, 0.95, 4, drift=(6, 5, 31, 27, 0.0)),
    shape(segs([((30, y), (330 if y % 3 else 260, y)) for y in range(140, 360, 18)], 3), ARC, 0.6, 0, drift=(6, 5, 31, 27, 0.0)),
    shape(rect(30, 60, 360, 108), LINE, 0.8, 0, drift=(6, 5, 31, 27, 0.0)),
    shape(polygon([(1540, 1120), (1960, 1120), (1960, 520), (1880, 520)]), BAND, 0.5, 4, drift=diag(12, 33, 0, -0.6, 0.8)),
    terra(circle(1780, 140, 110), drift=(5, 5, 27, 23, 0.0)),
    shape(ring(1780, 140, 84, 84, 2.5), (150, 56, 30), 0.8, 0, drift=(5, 5, 27, 23, 0.0)),
    terra(rect(-40, 1010, 560, 1060), drift=(12, 0, 24, 24, 0.0)),
    dots(1420, 820, 7, 4, 30), dots(500, 60, 5, 3),
    hline(40, 900, 975, grow=90, period=22, end='right'),
    vline(470, 0, 260, grow=40, period=18),
    hline(1300, 1920, 360, grow=70, period=26, phase=1.0),
], paper_colour=(244, 226, 196), seed=51))


# ---- science: laboratory -----------------------------------------------------------
def _hexa(cx, cy, r):
    return polygon([(cx + r * math.cos(a), cy + r * math.sin(a)) for a in [TAU * i / 6 + 0.5 for i in range(6)]])


_add(Theme('laboratory', 'Science: laboratory', [
    shape(_hexa(80, 120, 260), BEIGE, 1.0, 4, drift=(6, 5, 33, 29, 0.0)),
    shape(_hexa(1830, 960, 240), BAND, 0.6, 4, drift=(-7, -5, 31, 27, 1.0)),
    terra(polygon([(1600, 1100), (1960, 1100), (1960, 760)]), drift=(8, 0, 27, 27, 0.0)),
    terra(circle(1760, 120, 56), drift=(6, 6, 23, 29, 0.0)),
    shape(segs([((1760, 120), (1640, 230)), ((1760, 120), (1880, 250)), ((1640, 230), (1560, 190))], 1.6), LINE, 0.8, 0, drift=(6, 6, 23, 29, 0.0)),
    shape(circle(1640, 230, 26), BEIGE, 1.0, 3, drift=(6, 6, 23, 29, 0.0)),
    shape(circle(1560, 190, 16), DOT, 1.0, 0, drift=(6, 6, 23, 29, 0.0)),
    shape(ring(80, 120, 330), ARC, 0.7, 0, drift=(-4, 4, 35, 29, 0.0)),
    dots(380, 300, 6, 4), dots(80, 760, 5, 5),
    hline(60, 760, 990, grow=80, period=22, end='right'),
    vline(1500, 320, 720, grow=70, period=24, colour=FAINT, alpha=0.9),
], paper_colour=(246, 236, 220), seed=61))

# ---- medicine: clinic --------------------------------------------------------------
_add(Theme('clinic', 'Medicine: clinic', [
    shape(circle(160, 940, 230), BEIGE, 1.0, 4, drift=(6, -5, 31, 27, 0.0)),
    shape(circle(380, 1040, 120), BAND, 0.55, 4, drift=(-5, 4, 27, 33, 1.0)),
    shape(ring(160, 940, 300), ARC, 0.7, 0, drift=(4, -4, 35, 29, 0.0)),
    terra(capsule(1600, 90, 1990, 170), drift=(12, 0, 25, 25, 0.0)),
    terra(polygon([(1820, 820), (1900, 820), (1900, 900), (1980, 900), (1980, 980), (1900, 980), (1900, 1060), (1820, 1060), (1820, 980), (1740, 980), (1740, 900), (1820, 900)]), drift=(0, 8, 29, 29, 0.0)),
    shape(rect(1500, -40, 1960, 60), BEIGE, 0.9, 3, drift=(10, 0, 33, 33, 0.0)),
    dots(1420, 760, 6, 4), dots(80, 120, 6, 4),
    hline(0, 1100, 1000, grow=0, period=20, colour=ARC, alpha=0.6),
    tracer([(0, 1000), (300, 1000), (330, 950), (350, 1040), (370, 1000), (700, 1000), (730, 950), (750, 1040), (770, 1000), (1100, 1000)], 9.0, TERRA, 5),
    vline(90, 0, 380, grow=50, period=19),
], paper_colour=(242, 236, 220), seed=71))

# ---- technology: circuit -----------------------------------------------------------
_add(Theme('circuit', 'Technology: circuit', [
    shape(rect(-40, -40, 360, 300), BEIGE, 1.0, 3, drift=(6, 5, 31, 27, 0.0)),
    shape(rect(240, 180, 520, 420), BAND, 0.5, 3, drift=(-5, 4, 29, 33, 1.0)),
    terra(rect(1640, 820, 1960, 1120), drift=(0, 8, 27, 27, 0.0)),
    shape(rect(1500, 920, 1720, 1120), BAND, 0.55, 3, drift=(8, 0, 31, 31, 2.0)),
    shape(segs([((1460, 0), (1460, 160)), ((1460, 160), (1700, 160)), ((1700, 160), (1700, 300)), ((1700, 300), (1920, 300)),
                ((0, 620), (220, 620)), ((220, 620), (220, 860)), ((220, 860), (600, 860))], 1.6), LINE, 0.75, 0, drift=(0, 0, 30, 30, 0.0)),
    tracer([(1460, 0), (1460, 160), (1700, 160), (1700, 300), (1920, 300)], 7.0),
    tracer([(0, 620), (220, 620), (220, 860), (600, 860)], 8.5, phase=0.4),
    terra(rect(1440, 140, 1480, 180), drift=(0, 0, 30, 30, 0.0)),
    dots(1280, 760, 6, 4), dots(560, 60, 6, 3),
    hline(60, 760, 990, grow=80, period=22, end='right'),
], paper_colour=(240, 234, 222), seed=81))


# ---- biography: album --------------------------------------------------------------
def _rot_rect(cx, cy, w, h, deg):
    a = math.radians(deg)
    return polygon([(cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))])


_add(Theme('album', 'Biography: album', [
    shape(_rot_rect(140, 190, 380, 460, -9), BEIGE, 1.0, 4, drift=(6, 5, 31, 27, 0.0)),
    shape(_rot_rect(1790, 900, 420, 330, 7), BAND, 0.6, 4, drift=(-6, -5, 33, 29, 1.0)),
    shape(_rot_rect(190, -20, 150, 46, -14), (238, 228, 205), 0.9, 2, drift=(6, 5, 31, 27, 0.0)),
    terra(polygon([(1700, -10), (1930, -10), (1930, 220)]), drift=(6, 6, 25, 29, 0.0)),
    terra(polygon([(-10, 860), (-10, 1090), (220, 1090)]), drift=(6, 6, 27, 23, 1.0)),
    shape(ring(1790, 900, 300, 240, 1.3), ARC, 0.6, 0, drift=(4, -4, 35, 29, 0.0)),
    dots(400, 80, 6, 4), dots(1380, 780, 6, 4),
    hline(1300, 1920, 300, grow=70, period=21, phase=0.8),
    vline(520, 0, 260, grow=40, period=19),
], paper_colour=(249, 233, 210), seed=91))

# ---- space -------------------------------------------------------------------------
_add(Theme('deep_space', 'Space: night sky', [
    shape(circle(1760, 980, 330), INDIGO, 1.0, 8, drift=(-7, -6, 33, 29, 0.0)),
    shape(ring(1760, 980, 430), ARC, 0.8, 0, drift=(5, -4, 37, 31, 0.0)),
    shape(ring(1760, 980, 560), ARC, 0.5, 0, drift=(-4, 4, 41, 35, 1.0)),
    terra(circle(170, 150, 120), drift=(6, 6, 27, 23, 0.0)),
    shape(polygon([(-100, 1120), (80, 1120), (520, 560), (340, 560)]), BAND, 0.5, 4, drift=diag(12, 34)),
    orbiter(1760, 980, 560, 560, 3.4, 4.3, 80, 9, TERRA),
    dots(360, 80, 7, 4, 30), dots(1300, 140, 8, 3, 30), dots(700, 900, 6, 3, 30),
    hline(1300, 1920, 80, grow=60, period=21, phase=0.8),
    vline(80, 300, 760, grow=70, period=24, colour=FAINT, alpha=0.9),
], paper_colour=(244, 232, 214), seed=101))

# ---- economics: ledger -------------------------------------------------------------
_bars = [shape(rect(1560 + i * 64, 1080 - h, 1606 + i * 64, 1120), TERRA if i == 3 else BEIGE, 1.0, 8 if i == 3 else 3, i == 3,
               drift=(0, 10, 23 + i * 3, 23 + i * 3, i)) for i, h in enumerate((180, 260, 220, 360, 300, 420))]
_add(Theme('ledger', 'Economics: ledger', _bars + [
    shape(rect(-40, -40, 380, 260), BEIGE, 0.95, 3, drift=(6, 5, 31, 27, 0.0)),
    shape(segs([((40, y), (300, y)) for y in range(60, 230, 26)], 1.2), ARC, 0.7, 0, drift=(6, 5, 31, 27, 0.0)),
    terra(rect(-40, 1000, 420, 1050), drift=(12, 0, 24, 24, 0.0)),
    shape(segs([((60 + i * 60, 900 - v), (120 + i * 60, 900 - w_)) for i, (v, w_) in enumerate(zip((40, 90, 60, 140, 110, 190, 160), (90, 60, 140, 110, 190, 160, 230)))], 2.5), TERRA, 0.9, 0, drift=(0, 0, 30, 30, 0.0)),
    dots(1600, 120, 6, 4), dots(460, 60, 5, 3),
    hline(60, 760, 960, grow=60, period=22, end='right'),
    vline(1500, 300, 700, grow=70, period=24, colour=FAINT, alpha=0.9),
], paper_colour=(244, 234, 218), seed=111))


# ---- manga / comics history: ink studio --------------------------------------------
# Corner manga panel frames with gutters, screentone dot grids, a crosshatch band, a terracotta
# eclipse (sun-and-ring), a dip-pen nib, ink rules. Made for the Berserk episode.
def _hatch(x0, y0, x1, y1, step=14, slope=1.0):
    """Parallel hatch lines clipped to the box (x0, y0, x1, y1)."""
    def clip(a, b):
        (ax, ay), (bx, by) = a, b
        t0, t1, dx, dy = 0.0, 1.0, bx - ax, by - ay
        for p, q in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
            if p == 0:
                if q < 0:
                    return None
                continue
            r = q / p
            if p < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
        return None if t0 >= t1 else ((ax + dx * t0, ay + dy * t0), (ax + dx * t1, ay + dy * t1))
    lines, h = [], y1 - y0
    span = abs(h * slope)
    for k in range(-int(span / step) - 2, int((x1 - x0) / step) + int(span / step) + 3):
        seg = clip((x0 + k * step, y0), (x0 + k * step + h * slope, y1))
        if seg:
            lines.append(seg)
    return lines


_NIB = [(1690, 860), (1745, 860), (1760, 940), (1717, 1010), (1675, 940)]

_add(Theme('ink_studio', 'Manga: ink studio', [
    shape(rect(-40, -40, 330, 250), BEIGE, 1.0, 3, drift=(5, 4, 33, 29, 0.0)),                                  # panel 1
    shape(rect(350, -40, 560, 250), BAND, 0.7, 3, drift=(5, 4, 33, 29, 0.0)),                                   # panel 2
    shape(segs([((330, -40), (330, 250)), ((-40, 250), (560, 250)), ((350, -40), (350, 250)), ((560, -40), (560, 250))], 2.0), LINE, 0.8, 0, drift=(5, 4, 33, 29, 0.0)),
    shape(segs(_hatch(370, -30, 545, 240, 12, 0.5), 1.1), ARC, 0.55, 0, drift=(5, 4, 33, 29, 0.0)),            # crosshatch in panel 2
    shape(segs(_hatch(370, -30, 545, 240, 12, -0.5), 1.1), ARC, 0.4, 0, drift=(5, 4, 33, 29, 0.0)),
    shape(rect(1520, 640, 1960, 1120), BEIGE, 0.9, 3, drift=(0, 8, 31, 31, 1.0)),                               # panel 3
    shape(segs([((1520, 640), (1520, 1120)), ((1520, 640), (1960, 640))], 2.0), LINE, 0.8, 0, drift=(0, 8, 31, 31, 1.0)),
    shape(polygon(_NIB), (60, 52, 46), 0.85, 0, drift=(0, 8, 31, 31, 1.0)),                                      # dip-pen nib
    shape(segs([((1717, 880), (1717, 975))], 2.0), BEIGE, 1.0, 0, drift=(0, 8, 31, 31, 1.0)),
    shape(polygon([(-120, 1110), (60, 1110), (420, 700), (240, 700)]), BAND, 0.45, 4, drift=diag(10, 34)),     # diagonal band
    shape(ring(1760, 170, 205), ARC, 0.85, 0, drift=(-4, 4, 35, 29, 0.0)),                                      # eclipse ring
    terra(circle(1760, 170, 150), drift=(6, 5, 29, 23, 0.0)),                                                   # eclipse
    shape(circle(1790, 150, 118), (232, 214, 186), 1.0, 3, drift=(4, 4, 37, 31, 1.0)),                         # the shadow crossing it
    terra(rect(-60, 1010, 330, 1055), drift=(10, 0, 26, 26, 1.0)),
    dots(390, 300, 7, 4, 26), dots(1300, 850, 6, 4, 26),                                                        # screentone
    hline(60, 760, 985, grow=80, period=23, phase=2.2, end='right'),
    vline(1490, 300, 620, grow=60, period=24, phase=0.4, colour=FAINT, alpha=0.9),
    hline(600, 1350, 70, grow=90, period=21, phase=0.8),
], paper_colour=(246, 236, 220), seed=131))


# ---- manga ink: recreated from the user's second reference (Berserk episode) ------------
# Aged manga paper; a red sun cut by cream cloud bands; tilted panel frames filled with halftone;
# manga speed lines; red bars; a halftone disc; grey cloud bands; red ink splatter; a dry-brush
# ensō in the corner. Geometry is measured on the 1672x941 reference and scaled by K.
K = 1920 / 1672.0
MI_PAPER = (246, 224, 191)
MI_RED = (190, 48, 26)
MI_GREY = (169, 152, 126)
MI_CLOUD = (214, 190, 158)
MI_INK = (30, 26, 24)


def _k(pts):
    return [(x * K, y * K) for x, y in pts]


class MangaInk(Theme):
    def __init__(self):
        super().__init__('manga_ink', 'Manga: ink and halftone (reference 2)', [], MI_PAPER, 141)

    # -- builders -------------------------------------------------------------
    @staticmethod
    def _poly_mask(w, h, pts, ox, oy):
        m = Image.new('L', (w, h), 0)
        ImageDraw.Draw(m).polygon([(x - ox, y - oy) for x, y in pts], fill=255)
        return np.asarray(m)

    def _halftone(self, pts, colour, step=9, rmax=4.2, grad=((0, 0), (1, 0)), alpha=0.9, seed=1):
        """Dots on a grid inside a polygon; dot size follows a linear gradient between two
        relative points of the bounding box (dense at grad[0], fading at grad[1])."""
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        x0, y0, x1, y1 = int(min(xs)) - 4, int(min(ys)) - 4, int(max(xs)) + 4, int(max(ys)) + 4
        w, h = x1 - x0, y1 - y0
        inside = self._poly_mask(w, h, pts, x0, y0)
        m = Image.new('L', (w * 2, h * 2), 0)
        d = ImageDraw.Draw(m)
        (gx0, gy0), (gx1, gy1) = grad
        vx, vy = (gx1 - gx0) * w, (gy1 - gy0) * h
        L2 = vx * vx + vy * vy or 1
        for j, yy in enumerate(range(0, h, step)):
            for xx in range((j % 2) * step // 2, w, step):
                if inside[min(h - 1, yy), min(w - 1, xx)] == 0:
                    continue
                u = ((xx - gx0 * w) * vx + (yy - gy0 * h) * vy) / L2
                r = rmax * max(0.0, 1 - min(1.0, max(0.0, u))) ** 0.8
                if r > 0.5:
                    d.ellipse(((xx - r) * 2, (yy - r) * 2, (xx + r) * 2, (yy + r) * 2), fill=255)
        m = m.resize((w, h), Image.LANCZOS).point(lambda v: int(v * alpha))
        return self._tile_from(m, colour, x0, y0)

    @staticmethod
    def _tile_from(mask, colour, x0, y0, texture=0.0, seed=0):
        t = Tile.__new__(Tile)
        t.x0, t.y0 = int(x0), int(y0)
        col = np.empty((mask.height, mask.width, 3), np.float32)
        col[:] = colour
        if texture:
            col += _noise(mask.height, mask.width, 30, seed, texture)[..., None] + _noise(mask.height, mask.width, 2, seed + 1, texture * 0.8)[..., None]
        t.rgb = Image.fromarray(col.clip(0, 255).astype(np.uint8))
        t.mask = mask
        return t

    def _shape(self, pts, colour, alpha=1.0, texture=6, seed=3):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        x0, y0, x1, y1 = int(min(xs)) - 3, int(min(ys)) - 3, int(max(xs)) + 3, int(max(ys)) + 3
        w, h = x1 - x0, y1 - y0
        m = Image.new('L', (w * 3, h * 3), 0)
        ImageDraw.Draw(m).polygon([((x - x0) * 3, (y - y0) * 3) for x, y in pts], fill=255)
        m = m.resize((w, h), Image.LANCZOS)
        if texture:                                           # worn print: speckled ink dropout
            r = np.random.default_rng(seed)
            a = np.asarray(m).astype(np.float32)
            a *= (1 - 0.18 * (r.random(a.shape) < 0.08)) * (0.9 + 0.1 * _noise(h, w, 4, seed, 1.0))
            m = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        m = m.point(lambda v: int(v * alpha))
        return self._tile_from(m, colour, x0, y0, texture * 1.2, seed)

    def _lines(self, segs, colour, width=2.2, alpha=1.0, taper=False):
        xs = [v[0] for sg in segs for v in sg]
        ys = [v[1] for sg in segs for v in sg]
        x0, y0, x1, y1 = int(min(xs)) - 8, int(min(ys)) - 8, int(max(xs)) + 8, int(max(ys)) + 8
        w, h = x1 - x0, y1 - y0
        m = Image.new('L', (w * 3, h * 3), 0)
        d = ImageDraw.Draw(m)
        for (ax, ay), (bx, by) in segs:
            if taper:                                          # speed line: thick end -> needle point
                dx, dy = bx - ax, by - ay
                L = math.hypot(dx, dy) or 1
                nx, ny = -dy / L * width / 2, dx / L * width / 2
                d.polygon([((ax + nx - x0) * 3, (ay + ny - y0) * 3), ((ax - nx - x0) * 3, (ay - ny - y0) * 3), ((bx - x0) * 3, (by - y0) * 3)], fill=255)
            else:
                d.line([((ax - x0) * 3, (ay - y0) * 3), ((bx - x0) * 3, (by - y0) * 3)], fill=255, width=max(1, int(width * 3)))
        m = m.resize((w, h), Image.LANCZOS).point(lambda v: int(v * alpha))
        return self._tile_from(m, colour, x0, y0)

    def _clouds(self, bars, colour, alpha=1.0, texture=4, seed=5):
        """Japanese cloud bands: stacked capsules (x0, x1, y, h) in reference coords."""
        xs = [b[0] * K for b in bars] + [b[1] * K for b in bars]
        ys = [b[2] * K for b in bars] + [(b[2] + b[3]) * K for b in bars]
        x0, y0, x1, y1 = int(min(xs)) - 4, int(min(ys)) - 4, int(max(xs)) + 4, int(max(ys)) + 4
        w, h = x1 - x0, y1 - y0
        m = Image.new('L', (w * 3, h * 3), 0)
        d = ImageDraw.Draw(m)
        for bx0, bx1, by, bh in bars:
            r = bh * K * 3 / 2
            d.rounded_rectangle(((bx0 * K - x0) * 3, (by * K - y0) * 3, (bx1 * K - x0) * 3, ((by + bh) * K - y0) * 3), radius=r, fill=255)
        m = m.resize((w, h), Image.LANCZOS).point(lambda v: int(v * alpha))
        return self._tile_from(m, colour, x0, y0, texture, seed)

    def _enso(self, cx, cy, r, width, a0, a1, colour, seed=7):
        """Dry-brush ink ring: many bristle arcs with ragged starts, ends and gaps."""
        R = r + width
        x0, y0 = int(cx - R - 10), int(cy - R - 10)
        w = h = int(2 * R + 20)
        S = 2
        m = Image.new('L', (w * S, h * S), 0)
        d = ImageDraw.Draw(m)
        rng = np.random.default_rng(seed)
        n = 70
        for i in range(n):
            rr = r - width / 2 + width * i / (n - 1) + rng.normal(0, 1.2)
            edge = abs(i / (n - 1) - 0.5) * 2                     # bristles at the edges run dry sooner
            s0 = a0 + rng.uniform(0, 14) + 10 * edge
            s1 = a1 - rng.uniform(0, 30) * (0.3 + edge)
            a = s0
            while a < s1:                                        # dry-brush breaks
                seg = rng.uniform(25, 120) * (1 - 0.6 * edge)
                e = min(s1, a + seg)
                bb = ((cx - rr - x0) * S, (cy - rr - y0) * S, (cx + rr - x0) * S, (cy + rr - y0) * S)
                d.arc(bb, a, e, fill=255, width=max(1, int(rng.uniform(1.6, 3.2) * S)))
                a = e + rng.uniform(0, 6) * edge * 3
        m = m.resize((w, h), Image.LANCZOS)
        return self._tile_from(m, colour, x0, y0, 6, seed)

    def _splatter(self, cx, cy, spread, n, colour, seed):
        rng = np.random.default_rng(seed)
        R = spread + 20
        x0, y0 = int(cx - R), int(cy - R)
        w = h = int(2 * R)
        m = Image.new('L', (w * 3, h * 3), 0)
        d = ImageDraw.Draw(m)
        for _ in range(n):
            ang, dist = rng.uniform(0, 2 * math.pi), abs(rng.normal(0, spread / 2))
            rr = max(0.7, min(4.5, rng.gamma(1.4, 1.1)))
            x, y = R + math.cos(ang) * dist, R + math.sin(ang) * dist
            d.ellipse(((x - rr) * 3, (y - rr) * 3, (x + rr) * 3, (y + rr) * 3), fill=255)
        m = m.resize((w, h), Image.LANCZOS)
        return self._tile_from(m, colour, x0, y0)

    # -- composition ------------------------------------------------------------
    def build(self):
        a = np.empty((H, W, 3), np.float32)                        # aged manga paper
        a[:] = MI_PAPER
        a += _noise(H, W, 80, 7, 1.2)[..., None] + _noise(H, W, 5, 8, 2.2)[..., None]
        a += (_noise(H, W, 2, 9, 1.0)[..., None] * 3)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        a -= (((xx / W - 0.5) ** 2 + (yy / H - 0.5) ** 2) * 14)[..., None]
        r = np.random.default_rng(12)
        for _ in range(9):                                        # faint stains
            cx, cy, rad = r.uniform(0, W), r.uniform(0, H), r.uniform(80, 260)
            m = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * rad ** 2)))
            a -= (m * r.uniform(0.5, 1.0))[..., None] * np.array([0.5, 0.9, 1.4], np.float32)
        img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        base = np.asarray(img.filter(ImageFilter.GaussianBlur(0.5)), np.float32)
        self.g1 = Image.fromarray((base * (1 + 0.02 * _noise(H, W, 1, 21, 1.0)[..., None])).clip(0, 255).astype(np.uint8))
        self.g2 = Image.fromarray((base * (1 + 0.02 * _noise(H, W, 1, 22, 1.0)[..., None])).clip(0, 255).astype(np.uint8))

        P = []                                                     # (tile, drift)
        # left panel: halftone + grey plate, and its ink frame
        lp = _k([(0, 238), (135, 252), (98, 700), (0, 690)])
        P.append((self._shape(_k([(0, 245), (128, 258), (112, 470), (0, 462)]), MI_GREY, 0.28, 6, 1), (4, 3, 37, 31, 0.0)))
        P.append((self._halftone(lp, (90, 80, 68), 10, 4.4, ((0, 0.4), (1, 0.95)), 0.85, 1), (4, 3, 37, 31, 0.0)))
        # bottom-left panel
        bp = _k([(95, 812), (780, 880), (790, 941), (85, 941)])
        P.append((self._shape(_k([(150, 830), (560, 862), (566, 941), (140, 941)]), MI_GREY, 0.45, 6, 2), (6, 0, 41, 41, 1.0)))
        P.append((self._halftone(bp, (90, 80, 68), 10, 4.0, ((0, 0.2), (0.8, 0.0)), 0.8, 2), (6, 0, 41, 41, 1.0)))
        # top-right panel
        tp = _k([(1335, 0), (1610, 0), (1650, 205), (1288, 250)])
        P.append((self._shape(_k([(1355, 0), (1590, 0), (1622, 186), (1310, 228)]), MI_GREY, 0.85, 7, 3), (-5, 4, 35, 29, 0.5)))
        P.append((self._halftone(_k([(1120, 0), (1672, 0), (1672, 360), (1260, 300)]), (110, 98, 82), 7, 2.8, ((0.75, 0.0), (0.05, 0.9)), 0.5, 3), (-3, 2, 43, 37, 0.0)))
        # right halftone disc
        disc = [(1520 * K + 108 * K * math.cos(t_), 440 * K + 108 * K * math.sin(t_)) for t_ in np.linspace(0, 2 * math.pi, 80)]
        P.append((self._halftone(disc, (120, 110, 94), 6, 2.4, ((0.2, 0.0), (0.9, 1.0)), 0.85, 4), (0, 6, 33, 27, 2.0)))
        # bottom-right halftone corner
        P.append((self._halftone(_k([(1420, 600), (1672, 580), (1672, 941), (1450, 941)]), (100, 90, 76), 9, 3.8, ((1.0, 1.0), (0.0, 0.0)), 0.6, 5), (3, -3, 39, 35, 0.0)))
        # grey cloud bands
        P.append((self._clouds([(100, 175, 432, 26), (100, 240, 460, 26), (140, 370, 512, 24), (180, 290, 536, 22)], MI_CLOUD, 0.95, 5, 6), (22, 0, 34, 34, 0.0)))
        P.append((self._clouds([(1175, 1440, 745, 26), (1220, 1400, 772, 24), (1000, 1370, 815, 26)], MI_CLOUD, 0.95, 5, 7), (-26, 0, 38, 38, 1.0)))
        # red sun with cream cloud bands cutting through it
        sun = self._shape([(170 * K + 220 * K * math.cos(t_), 30 * K + 220 * K * math.sin(t_)) for t_ in np.linspace(0, 2 * math.pi, 120)], MI_RED, 1.0, 10, 8)
        P.append((sun, (6, 5, 29, 25, 0.0)))
        P.append((self._clouds([(0, 110, 72, 26), (60, 170, 98, 24), (0, 255, 124, 28), (70, 210, 152, 24)], MI_PAPER, 1.0, 3, 9), (18, 0, 27, 27, 0.5)))
        # red bars
        P.append((self._shape(_k([(46, 650), (127, 650), (110, 941), (20, 941)]), MI_RED, 1.0, 10, 10), (0, 7, 31, 31, 0.0)))
        P.append((self._shape(_k([(1600, 196), (1652, 188), (1626, 512), (1570, 514)]), MI_RED, 1.0, 10, 11), (0, -7, 29, 29, 1.0)))
        # panel ink frames
        P.append((self._lines([(_k([(0, 238)])[0], _k([(135, 252)])[0]), (_k([(135, 252)])[0], _k([(95, 820)])[0]),
                               (_k([(95, 812)])[0], _k([(780, 880)])[0]), (_k([(770, 880)])[0], _k([(785, 941)])[0]),
                               (_k([(1335, 0)])[0], _k([(1288, 250)])[0]), (_k([(1288, 250)])[0], _k([(1652, 200)])[0]), (_k([(1612, 0)])[0], _k([(1652, 205)])[0]),
                               (_k([(1165, 572)])[0], _k([(1562, 572)])[0]), (_k([(1562, 572)])[0], _k([(1548, 941)])[0])], MI_INK, 2.0, 0.95), (3, 2, 45, 39, 0.0)))
        # speed lines (tapered): top, top-right, bottom-left
        rs = np.random.default_rng(14)
        top = [((300 * K + rs.uniform(-40, 40), (60 + i * 2.2) * K), ((900 + rs.uniform(-60, 0)) * K, (56 + i * 0.6) * K)) for i in range(5)]
        tr = [(((1060 - i * 4) * K, (0 + i * 1.5) * K), ((930 + rs.uniform(-30, 20)) * K, (40 + i * 6) * K)) for i in range(7)]
        bl = [((0, (800 + i * 14) * K), ((340 + rs.uniform(-40, 40)) * K, (941 + i * 6) * K)) for i in range(9)]
        self.speed = [self._lines(top, MI_INK, 3.0, 0.9, taper=True), self._lines(tr, MI_INK, 4.0, 0.95, taper=True), self._lines(bl, MI_INK, 5.0, 0.95, taper=True)]
        # ink splatter
        P.append((self._splatter(330 * K, 205 * K, 85, 40, MI_RED, 31), (6, 5, 29, 25, 0.0)))
        P.append((self._splatter(1545 * K, 260 * K, 80, 36, MI_RED, 32), (0, -7, 29, 29, 1.0)))
        P.append((self._splatter(1475 * K, 670 * K, 40, 22, MI_RED, 33), (0, 0, 30, 30, 0.0)))
        # the ensō
        self.enso = self._enso(1705 * K, 945 * K, 245 * K, 92 * K, 150, 300, MI_INK, 34)
        self.parts = P
        self._built = True

    def frame(self, t):
        if not self._built:
            self.build()
        c = Image.blend(self.g1, self.g2, 0.5 + 0.5 * _s(t, 7.0))
        for tile, (ax, ay, px, py, ph) in self.parts:
            tile.place(c, ax * _s(t, px, ph), ay * _s(t, py, ph + 1.0))
        for i, sp in enumerate(self.speed):                        # speed lines surge and settle
            k = 0.5 + 0.5 * _s(t, 6.5 + i * 1.7, i * 2.1)
            sp.place(c, (-1, 1, -1)[i] * 14 * k, (0, -1, 1)[i] * 6 * k)
        self.enso.place(c, 5 * _s(t, 31), 4 * _s(t, 27, 1.0))     # the brush circle breathes
        return c


THEMES['manga_ink'] = MangaInk()


class _Editorial:
    name, label, ink = 'editorial', 'Editorial (original reference)', (26, 26, 26)

    def frame(self, t):
        import bg_motion
        return bg_motion._editorial(t)


THEMES['editorial'] = _Editorial()


# ---- Astrolabe: aged parchment with faint engraved astrolabe / portolan rings ----------
# Matches the user's reference for "Histoire des armes": warm parchment, a dark mottled vignette,
# a great engraved dial rising from the bottom edge, two smaller dials bleeding off the top
# corners. The great dial turns very slowly; the corner dials drift. Ink stays faint so the
# collage on top always reads.
AS_PAPER = (233, 222, 190)
AS_EDGE = (176, 150, 102)
AS_INK = (150, 128, 88)


class Astrolabe(Theme):
    def __init__(self):
        super().__init__('astrolabe', 'Astrolabe parchment (Histoire des armes)', [], AS_PAPER, 77)

    @staticmethod
    def _font(size):
        from PIL import ImageFont
        import os
        here = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'fonts')
        return ImageFont.truetype(os.path.join(here, 'Playfair700.ttf'), size)

    def _parchment(self, seed):
        a = np.empty((H, W, 3), np.float32)
        a[:] = AS_PAPER
        a += _noise(H, W, 90, seed, 1.5)[..., None] + _noise(H, W, 4, seed + 2, 2.2)[..., None]    # smooth parchment, fine grain
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx / W - 0.5) * 1.15) ** 2 + ((yy / H - 0.5) * 1.05) ** 2)
        blot = (0.5 + 0.5 * _noise(H, W, 140, seed + 3, 1.0)).clip(0, 1)
        k = (np.clip((r - 0.28) / 0.40, 0, 1) ** 1.4) * (0.92 + 0.16 * blot)
        a = a * (1 - k[..., None] * 0.7) + np.array(AS_EDGE, np.float32) * (k[..., None] * 0.7)
        img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        d = ImageDraw.Draw(img)
        rng = np.random.default_rng(seed + 5)
        for _ in range(700):                                  # fibres
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            L, ang = rng.uniform(3, 9), rng.uniform(0, math.pi)
            c = int(rng.uniform(214, 230))
            d.line([(x, y), (x + L * math.cos(ang), y + L * math.sin(ang))], fill=(c, c - 10, c - 34))
        return img.filter(ImageFilter.GaussianBlur(0.5))

    def _dial(self, R, rings, seed, letters=()):
        """An engraved dial: concentric rings, tick bands, segment boxes, radial spokes and
        lettering, drawn at 2x as an L mask (255 = full ink)."""
        S2 = 2
        n = int(2 * R + 40)
        m = Image.new('L', (n * S2, n * S2), 0)
        d = ImageDraw.Draw(m)
        c0 = n * S2 / 2
        rng = np.random.default_rng(seed)

        def circ(r, w=2, v=255):
            d.ellipse((c0 - r * S2, c0 - r * S2, c0 + r * S2, c0 + r * S2), outline=v, width=w * S2)

        def ticks(r0, r1, count, w=1, v=230, every=0):
            for i in range(count):
                a = TAU * i / count
                rr = r1 if not every or i % every else r1 + (r1 - r0) * 0.8
                d.line([(c0 + r0 * S2 * math.cos(a), c0 + r0 * S2 * math.sin(a)),
                        (c0 + rr * S2 * math.cos(a), c0 + rr * S2 * math.sin(a))], fill=v, width=w * S2)

        for kind, r, *p in rings:
            if kind == 'ring':
                circ(r, *p)
            elif kind == 'ticks':
                ticks(r, p[0], p[1], 1, 220, p[2] if len(p) > 2 else 0)
            elif kind == 'boxes':                              # alternating filled segments (the checker band)
                r1, count = p
                for i in range(count):
                    if i % 2:
                        continue
                    a0, a1 = 360 * i / count, 360 * (i + 1) / count
                    for rr in np.arange(r, r1, 1.2):
                        d.arc((c0 - rr * S2, c0 - rr * S2, c0 + rr * S2, c0 + rr * S2), a0, a1, fill=150, width=S2)
            elif kind == 'spokes':
                r1, count = p
                for i in range(count):
                    a = TAU * i / count + 0.13
                    d.line([(c0 + r * S2 * math.cos(a), c0 + r * S2 * math.sin(a)),
                            (c0 + r1 * S2 * math.cos(a), c0 + r1 * S2 * math.sin(a))], fill=170, width=S2)
            elif kind == 'grid':                               # a faint chart grid inside the dial
                step = p[0]
                for k in range(-int(r), int(r) + 1, step):
                    h = math.sqrt(max(0, r * r - k * k))
                    d.line([(c0 + k * S2, c0 - h * S2), (c0 + k * S2, c0 + h * S2)], fill=90, width=S2)
                    d.line([(c0 - h * S2, c0 + k * S2), (c0 + h * S2, c0 + k * S2)], fill=90, width=S2)
        for r, text, size, a_start in letters:                 # lettering set along a ring
            f = self._font(size * S2)
            a = a_start
            for ch in text:
                if ch == ' ':
                    a += size * 0.45 / r
                    continue
                g = Image.new('L', (size * 3 * S2, size * 3 * S2), 0)
                ImageDraw.Draw(g).text((g.width / 2, g.height / 2), ch, font=f, fill=210, anchor='mm')
                g = g.rotate(-math.degrees(a) - 90, Image.BICUBIC)
                x, y = c0 + r * S2 * math.cos(a), c0 + r * S2 * math.sin(a)
                m.paste(255, (int(x - g.width / 2), int(y - g.height / 2)), g)
                a += size * 0.78 / r
        return m.resize((n, n), Image.LANCZOS)

    def build(self):
        self.g1 = self._parchment(self.seed)
        big = [('ring', 880, 3), ('ring', 862, 1), ('ticks', 862, 842, 180, 5), ('ring', 842, 1),
               ('boxes', 800, 838, 36), ('ring', 800, 2), ('ring', 740, 1), ('ticks', 740, 724, 120, 10),
               ('ring', 690, 2), ('spokes', 420, 690, 24), ('ring', 640, 1), ('ring', 560, 2),
               ('boxes', 540, 556, 48), ('ring', 420, 2), ('grid', 400, 80), ('ring', 300, 1), ('ring', 140, 2)]
        big_letters = [(765, 'SEPTENTRIO   ORIENS   MERIDIES   OCCIDENS', 34, -2.85),
                       (600, 'I II III IV V VI VII VIII IX X XI XII', 26, -2.6)]
        self.big = self._dial(900, big, self.seed, big_letters)
        self.big_alpha = 0.30
        small = [('ring', 400, 2), ('ticks', 400, 384, 96, 8), ('ring', 384, 1), ('boxes', 350, 380, 24),
                 ('ring', 350, 1), ('spokes', 120, 350, 16), ('ring', 250, 2), ('grid', 240, 60), ('ring', 120, 1)]
        self.tl = self._dial(410, small, self.seed + 1, [(300, 'AFRICA', 28, -2.4)])
        self.tr = self._dial(410, small, self.seed + 2, [(300, 'ASIA', 28, -1.2)])
        self.ink = AS_INK

    def _put(self, c, mask, cx, cy, alpha, dx=0.0, dy=0.0):
        m = mask.point(lambda v, a=alpha: int(v * a))
        c.paste(self.ink, (int(round(cx + dx - mask.width / 2)), int(round(cy + dy - mask.height / 2))), m)

    def frame(self, t):
        if not self._built:
            self.build()
            self._built = True
        c = self.g1.copy()
        ang = 0.9 * math.sin(TAU * t / 240.0) + t * 0.12          # a slow turn, a few degrees a minute
        big = self.big.rotate(ang, Image.BILINEAR)
        self._put(c, big, W / 2 + 40, H + 210, self.big_alpha, 6 * _s(t, 37), 4 * _s(t, 31, 1.0))
        self._put(c, self.tl, 210, 40, 0.22, 7 * _s(t, 29), 5 * _s(t, 23, 0.7))
        self._put(c, self.tr, W - 190, 20, 0.18, -6 * _s(t, 33, 1.4), 5 * _s(t, 27))
        return c


THEMES['astrolabe'] = Astrolabe()
