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
    a += _noise(H, W, 60, seed, 5)[..., None] + _noise(H, W, 6, seed + 1, 3)[..., None]
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
            col += _noise(h, w, 40, seed, texture)[..., None] + _noise(h, w, 3, seed + 1, texture * 0.6)[..., None]
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


class _Editorial:
    name, label, ink = 'editorial', 'Editorial (original reference)', (26, 26, 26)

    def frame(self, t):
        import bg_motion
        return bg_motion._editorial(t)


THEMES['editorial'] = _Editorial()
