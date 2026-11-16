"""Shared pieces for « L'histoire de GTA ».

No gameplay footage: Rockstar's video policy excludes monetised use, so the chases are drawn here,
as a top-down paper city with cut-out cars. Real material is limited to stills shown while the
narration talks about them (the Race'n'Chase mock-up) and to captures of the press articles
that carry each claim (SOURCES.md), with the quoted sentence highlighted on its spoken cue.
"""
import json
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from vox import asset, font, W, H, PAL, F_HEAD, F_TYPE, INK, CREAM, torn_mask
import presets as P
import annotate as A
from style import sfx

ROAD = (58, 62, 66)
BLOCK = PAL.paper
KERB = (182, 186, 188)
DASH = PAL.highlight
THIEF = PAL.accent_dark          # evidence-tape yellow: the player's car
COP = (24, 28, 34)
SIREN_R, SIREN_B = (205, 40, 40), (52, 92, 210)


# ------------------------------------------------------------------ articles
def article(head, body, outlet, date, width=1180, seed=21, pad=46):
    """A press article as a printed web page on the desk: outlet and date, the real headline and
    the real paragraph (Playwright captures in assets/), torn edges. Returns (card, boxes): the
    boxes of the captured phrases (A0x_*.json) in card pixels, for annotate.sweep."""
    hd, bd = Image.open(asset(head)).convert('RGB'), Image.open(asset(body)).convert('RGB')
    inner = width - 2 * pad
    k_h = min(1.0, inner / hd.width)
    hd = hd.resize((int(hd.width * k_h), int(hd.height * k_h)), Image.LANCZOS)
    k_b = inner / bd.width
    bd = bd.resize((inner, int(bd.height * k_b)), Image.LANCZOS)
    y_top = pad + 40
    y_rule = y_top + hd.height + 18
    y_body = y_rule + 24
    h = y_body + bd.height + pad
    card = Image.new('RGBA', (width, h), (255, 255, 255, 255))     # the captures' own white
    d = ImageDraw.Draw(card)
    d.text((pad, pad), f'{outlet.upper()}   ·   {date}', font=font('Inter600.ttf', 24), fill=PAL.muted + (255,))
    card.paste(hd, (pad, y_top))
    d.line((pad, y_rule, width - pad, y_rule), fill=(205, 205, 200, 255), width=2)
    card.paste(bd, (pad, y_body))
    a = np.asarray(card).astype(np.float32)
    a[..., :3] += np.random.default_rng(seed).normal(0, 2.2, (h, width, 1))
    card = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    card.putalpha(torn_mask(width, h, seed, amp=5, step=12))
    boxes = {}
    meta = asset(body.rsplit('.', 1)[0] + '.json')
    try:
        for ph, rects in json.load(open(meta))['boxes'].items():
            boxes[ph] = [(pad + x0 * k_b, y_body + y0 * k_b, pad + x1 * k_b, y_body + y1 * k_b) for x0, y0, x1, y1 in rects or []]
    except FileNotFoundError:
        pass
    return card, boxes


def highlight(layer, card_xy, boxes, t, start, gap=0.35, until=None, colour=None, strength=0.85):
    """Highlighter over one phrase of an article placed with its top-left at card_xy, line by
    line, as the narration reaches it. Multiplied into the page like real marker ink, so the
    printed words stay dark and readable on top of the colour."""
    x, y = card_xy
    tmp = Image.new('RGBA', layer.size, (0, 0, 0, 0))
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        A.sweep(tmp, (x + x0, y + y0, x + x1, y + y1), t, start + i * gap, until=until, sound=(i == 0), seed=7 + i,
                colour=colour or PAL.highlight, alpha=1.0)
    a = np.asarray(tmp).astype(np.float32)
    k = a[..., 3:4] / 255.0 * strength
    if k.max() <= 0:
        return
    base = np.asarray(layer).astype(np.float32)
    mul = 1 - k + k * a[..., :3] / 255.0
    base[..., :3] *= mul
    layer.paste(Image.fromarray(base.clip(0, 255).astype(np.uint8), 'RGBA'))


# ------------------------------------------------------------------ the paper city
@lru_cache(maxsize=2)
def city(seed=3):
    """Top-down city on the desk: dark road paper, torn paper blocks, yellow lane dashes.
    Roads run along x = COLS and y = ROWS (world px)."""
    r = np.random.default_rng(seed)
    im = Image.new('RGBA', (W, H), ROAD + (255,))
    a = np.asarray(im).astype(np.float32)
    a[..., :3] += r.normal(0, 4, (H, W, 1))
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(im)
    for y in ROWS:                                        # lane dashes
        for x in range(0, W, 70):
            d.rectangle((x, y - 3, x + 34, y + 3), fill=DASH + (230,))
    for x in COLS:
        for y in range(0, H, 70):
            d.rectangle((x - 3, y, x + 3, y + 34), fill=DASH + (230,))
    xs = [-200] + COLS + [W + 200]
    ys = [-200] + ROWS + [H + 200]
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            x0, x1 = xs[i] + ROAD_W, xs[i + 1] - ROAD_W
            y0, y1 = ys[j] + ROAD_W, ys[j + 1] - ROAD_W
            if x1 - x0 < 40 or y1 - y0 < 40:
                continue
            w, h = int(x1 - x0), int(y1 - y0)
            kerb = Image.new('RGBA', (w + 16, h + 16), KERB + (255,))
            kerb.putalpha(torn_mask(w + 16, h + 16, seed + i * 7 + j, amp=3, step=14))
            P.put(im, kerb, (x0 + x1) / 2, (y0 + y1) / 2, lift=0.0, sh_op=0.35)
            blk = P.paper_card(w, h, seed=seed + 31 * i + j, colour=BLOCK)
            P.put(im, blk, (x0 + x1) / 2, (y0 + y1) / 2, shadow=False)
            bd = ImageDraw.Draw(im)                        # roofs: a few flat rectangles, like a plan
            for _ in range(int(r.integers(1, 4))):
                rw, rh = r.integers(w // 5, w // 2), r.integers(h // 5, h // 2)
                rx, ry = r.integers(x0 + 14, max(x0 + 15, x1 - rw - 14)), r.integers(y0 + 14, max(y0 + 15, y1 - rh - 14))
                bd.rectangle((rx, ry, rx + rw, ry + rh), outline=PAL.border + (255,), width=3)
    return im


COLS = [330, 960, 1590]
ROWS = [250, 830]
ROAD_W = 70


# ------------------------------------------------------------------ cars
@lru_cache(maxsize=8)
def _car(kind, siren=0):
    """A top-down car cut out of paper, nose pointing right (+x), 128 x 66 px."""
    w, h = 128, 66
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    body = THIEF if kind == 'thief' else COP
    d.rounded_rectangle((2, 4, w - 3, h - 5), radius=18, fill=body + (255,), outline=(20, 20, 20, 255), width=3)
    if kind == 'cop':                                          # white doors band
        d.rectangle((40, 6, 86, h - 7), fill=(236, 236, 232, 255))
    d.rounded_rectangle((76, 12, 100, h - 13), radius=6, fill=(120, 150, 170, 255))    # windscreen
    d.rounded_rectangle((24, 14, 40, h - 15), radius=5, fill=(100, 125, 140, 255))     # rear window
    if kind == 'cop':
        a, b = (SIREN_R, SIREN_B) if siren == 0 else (SIREN_B, SIREN_R)
        d.rectangle((54, 14, 66, 32), fill=a + (255,))
        d.rectangle((54, 34, 66, 52), fill=b + (255,))
    for yy in (9, h - 13):                                     # headlights
        d.rectangle((w - 9, yy, w - 4, yy + 5), fill=(250, 240, 200, 255))
    im.putalpha(Image.fromarray(np.minimum(np.asarray(im)[..., 3], np.asarray(torn_mask(w, h, 5 if kind == 'thief' else 9, amp=2, step=8)))))
    return im


def car(layer, kind, x, y, heading, t, lift=0.0, scale=1.0):
    """Draw a car at (x, y), heading in degrees (0 = +x, 90 = down the screen)."""
    im = _car(kind, int(t * 6) % 2 if kind == 'cop' else 0)
    if scale != 1.0:
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    im = im.rotate(-heading, Image.BICUBIC, expand=True)
    P.put(layer, im, x, y, lift=lift, sh_op=0.45)


# ------------------------------------------------------------------ routes
class Route:
    """A polyline through the street grid, walked at constant speed."""
    def __init__(self, pts):
        self.pts = [np.array(p, float) for p in pts]
        self.seg = [np.linalg.norm(b - a) for a, b in zip(self.pts, self.pts[1:])]
        self.total = sum(self.seg)

    def at(self, s):
        """(x, y, heading) at arc length s, rounding the corners."""
        s = max(0.0, min(self.total, s))
        acc = 0.0
        for i, L in enumerate(self.seg):
            if s <= acc + L or i == len(self.seg) - 1:
                a, b = self.pts[i], self.pts[i + 1]
                u = (s - acc) / max(L, 1e-6)
                p = a + (b - a) * u
                hd = math.degrees(math.atan2(*(b - a)[::-1]))
                corner = 90.0                               # ease the heading through each corner
                if i + 1 < len(self.seg) and L - (s - acc) < corner:
                    c = self.pts[i + 2]
                    hn = math.degrees(math.atan2(*(c - b)[::-1]))
                    k = 1 - (L - (s - acc)) / corner
                    hd = hd + ((hn - hd + 180) % 360 - 180) * 0.5 * k
                return float(p[0]), float(p[1]), hd
            acc += L


def look(frm, to):
    return math.degrees(math.atan2(to[1] - frm[1], to[0] - frm[0]))


# ------------------------------------------------------------------ small drawn props (act 2)
def creature(layer, x, y, t, scale=1.0):
    """A tiny marching creature (generic: round head, tuft of hair, small body), walking right."""
    s = scale
    step = math.sin(t * 12 + x * 0.05)
    d = ImageDraw.Draw(layer)
    d.ellipse((x - 9 * s, y - 34 * s, x + 9 * s, y - 16 * s), fill=(240, 200, 170, 255))      # head
    d.ellipse((x - 10 * s, y - 42 * s, x + 6 * s, y - 28 * s), fill=(70, 160, 70, 255))        # hair
    d.rounded_rectangle((x - 8 * s, y - 18 * s, x + 8 * s, y + 2 * s), radius=4 * s, fill=(60, 80, 190, 255))
    d.line((x - 4 * s, y + 2 * s, x - 4 * s + 5 * s * step, y + 12 * s), fill=(60, 80, 190, 255), width=int(5 * s))
    d.line((x + 4 * s, y + 2 * s, x + 4 * s - 5 * s * step, y + 12 * s), fill=(60, 80, 190, 255), width=int(5 * s))


def exit_door(layer, x, y, scale=1.0):
    s = scale
    d = ImageDraw.Draw(layer)
    d.rectangle((x - 40 * s, y - 90 * s, x + 40 * s, y + 12 * s), fill=(120, 80, 50, 255), outline=(40, 30, 20, 255), width=4)
    d.rectangle((x - 26 * s, y - 70 * s, x + 26 * s, y + 12 * s), fill=(20, 20, 20, 255))
    d.text((x, y - 104 * s), 'SORTIE', font=F_HEAD(int(26 * s)), fill=PAL.ink + (255,), anchor='mm')


@lru_cache(maxsize=4)
def radio_card(seed=51):
    """A car radio cut out of paper: chrome face, frequency scale, two knobs."""
    w, h = 520, 230
    im = P.paper_card(w, h, seed=seed, colour=(70, 74, 80))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((90, 50, w - 90, 130), radius=10, fill=(230, 200, 120, 255), outline=(30, 30, 30, 255), width=3)
    for i, f in enumerate(range(88, 109, 4)):
        x = 110 + i * (w - 220) / 5
        d.line((x, 105, x, 125), fill=(40, 40, 40, 255), width=3)
        d.text((x, 80), str(f), font=F_TYPE(26), fill=(40, 40, 40, 255), anchor='mm')
    for cx in (50, w - 50):
        d.ellipse((cx - 32, 58, cx + 32, 122), fill=(30, 30, 30, 255), outline=(150, 150, 150, 255), width=4)
    for i in range(5):
        d.rounded_rectangle((120 + i * 60, 158, 160 + i * 60, 190), radius=5, fill=(30, 30, 30, 255))
    return im


def radio_needle(layer, cx, cy, k):
    """The tuning needle over radio_card placed at (cx, cy), k in 0..1 across the scale."""
    x = cx - 260 + 110 + k * (520 - 220)
    ImageDraw.Draw(layer).line((x, cy - 65, x, cy - 10), fill=(200, 30, 30, 255), width=5)


@lru_cache(maxsize=4)
def payphone_card(seed=61):
    """A public payphone cut out of paper: box, handset on its hook, keypad."""
    w, h = 300, 470
    im = P.paper_card(w, h, seed=seed, colour=(150, 155, 160))
    d = ImageDraw.Draw(im)
    d.rectangle((30, 30, w - 30, 90), fill=(40, 70, 140, 255))
    d.text((w / 2, 60), 'TÉLÉPHONE', font=F_HEAD(30), fill=(240, 240, 240, 255), anchor='mm')
    for r in range(4):
        for c in range(3):
            x, y = 110 + c * 46, 150 + r * 52
            d.rounded_rectangle((x - 18, y - 18, x + 18, y + 18), radius=5, fill=(60, 60, 60, 255))
    d.rectangle((60, 380, w - 60, 420), fill=(60, 60, 60, 255))
    return im


@lru_cache(maxsize=2)
def handset():
    im = Image.new('RGBA', (90, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((25, 40, 65, 260), radius=18, fill=(25, 25, 25, 255))
    d.rounded_rectangle((5, 0, 85, 60), radius=20, fill=(25, 25, 25, 255))
    d.rounded_rectangle((5, 240, 85, 300), radius=20, fill=(25, 25, 25, 255))
    return im


# ------------------------------------------------------------------ typed quotes
_TYPED = {}


def typed_quote(layer, xy, text, t, start, size=40, width=1500, cps=24, paper=True, colour=None):
    """A quotation typed letter by letter (typewriter, with key sounds) on a strip of paper,
    centred on xy. Used for every quote and every translated quote in the film."""
    import typo as TY
    key = (text, size, width)
    if key not in _TYPED:
        _TYPED[key] = TY.Text(text, 'caption', size=size, colour=colour or INK, max_w=width, align='m')
    T = _TYPED[key]
    if t < start - 0.25:
        return
    x, y = xy
    if paper:
        k = P.clamp01((t - start + 0.25) / 0.25)
        strip = P.paper_card(int(T.w + 70), int(T.h + 40), seed=91, colour=CREAM)
        P.put(layer, P.fade_img(strip, k), x, y + T.h / 2, sh_op=0.25)
    T.draw(layer, (x, y), t, start, anim='type', anchor='m', stagger=1.0 / cps)
