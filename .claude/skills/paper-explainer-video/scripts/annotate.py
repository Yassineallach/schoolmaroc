"""Editorial annotations: a documentary editor marking up text, photographs and documents live.

Every annotation is drawn by a pen, not faded in: strokes are slightly irregular (seeded, so a
re-render is identical), drawn on with natural easing, and land with a touch of overshoot.
Each one appears on its narration cue and then, if `until` is given, leaves:
    exit='fade'    lifts away over 0.4 s
    exit='settle'  stays as a quiet trace (35 % opacity) so the frame never gets crowded

Coordinates are layer pixels. Text annotations take a box (x0, y0, x1, y1); words_box() and
text_box() give the box of a line drawn with style.words() or of one word in it.
Draw marks that belong to paper on shot.mid (they stay glued to it in camera moves), marks on
headline type on shot.top, marks on captions on shot.hud.

TEXT        sweep, underline, ring, outline, strike, emphasis
PHOTOS      ring, arrow, frame, corners, spotlight, magnify, (Shot.zoom_to / focus for camera)
DOCUMENTS   mark, bracket, stat, connect, (presets.stamp_hit), bars, wedge
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import vox
from vox import INK, F_HEAD, F_TYPE
from style import sfx

from palette import ACTIVE as PAL           # colours come from the episode palette (palette.py)
TERRA = ACCENT = PAL.accent  # primary highlight
ORANGE = ACCENT2 = PAL.accent2
BEIGE = PAL.soft
CHARCOAL = PAL.ink2
SS = 2                       # supersampling for anti-aliased strokes


# ------------------------------------------------------------------ timing
def _c(x):
    return min(max(x, 0.0), 1.0)


def pen(u):
    """Pen speed: quick start, gentle finish."""
    u = _c(u)
    return 1 - (1 - u) ** 2.6


def pop(u, amount=0.10):
    """0 -> 1 with a small overshoot that settles (for scale and stamps)."""
    if u <= 0:
        return 0.0
    if u >= 1:
        return 1.0
    return 1 - math.exp(-6 * u) * math.cos(7.5 * u) + amount * math.sin(math.pi * u) * (1 - u)


def life(t, start, until=None, exit='settle', fade=0.4):
    """Opacity multiplier for an annotation's lifetime."""
    if t < start:
        return 0.0
    if until is None or t < until:
        return 1.0
    k = _c((t - until) / fade)
    return 1 - k if exit == 'fade' else 1 - 0.65 * k


# ------------------------------------------------------------------ hand-drawn geometry
def _resample(pts, step=6.0):
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / step))
        for i in range(1, n + 1):
            out.append((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n))
    return out


def wobble(pts, amp=2.5, seed=0, step=6.0):
    """Hand tremor: smooth noise perpendicular to the path."""
    p = _resample(pts, step)
    if len(p) < 3:
        return p
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, len(p) // 6 + 3)
    x = np.linspace(0, len(n) - 1, len(p))
    noise = np.interp(x, np.arange(len(n)), n) * amp
    out = []
    for i, (x0, y0) in enumerate(p):
        a, b = p[max(0, i - 1)], p[min(len(p) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        out.append((x0 - dy / L * noise[i], y0 + dx / L * noise[i]))
    return out


def stroke(layer, pts, progress, width=8, colour=TERRA, alpha=1.0, taper=True):
    """Anti-aliased marker stroke drawn along pts up to `progress` (0..1)."""
    if progress <= 0 or alpha <= 0.01 or len(pts) < 2:
        return
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:])]
    total = sum(seg) or 1
    target, acc, draw = total * _c(progress), 0.0, [pts[0]]
    for (a, b), L in zip(zip(pts[:-1], pts[1:]), seg):
        if acc + L >= target:
            f = (target - acc) / L if L else 1
            draw.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
            break
        draw.append(b)
        acc += L
    xs, ys = [p[0] for p in draw], [p[1] for p in draw]
    pad = width + 4
    x0, y0 = int(min(xs) - pad), int(min(ys) - pad)
    w, h = int(max(xs) + pad) - x0 + 1, int(max(ys) + pad) - y0 + 1
    m = Image.new('L', (w * SS, h * SS), 0)
    d = ImageDraw.Draw(m)
    n = len(draw)
    for i, (a, b) in enumerate(zip(draw[:-1], draw[1:])):
        k = 1.0
        if taper:                                   # pen pressure: thinner at the very ends
            k = 0.65 + 0.35 * min(1.0, min(i, n - i) / 4)
        wd = max(1, int(width * k * SS))
        pa, pb = ((a[0] - x0) * SS, (a[1] - y0) * SS), ((b[0] - x0) * SS, (b[1] - y0) * SS)
        d.line([pa, pb], fill=255, width=wd)
        d.ellipse((pb[0] - wd / 2, pb[1] - wd / 2, pb[0] + wd / 2, pb[1] + wd / 2), fill=255)
    m = m.resize((w, h), Image.LANCZOS).point(lambda v: int(v * alpha * 0.95))
    tile = Image.new('RGBA', (w, h), colour + (0,))
    tile.putalpha(m)
    _comp(layer, tile, x0, y0)


def _comp(layer, im, x, y):
    x, y = int(round(x)), int(round(y))
    cx0, cy0 = max(0, -x), max(0, -y)
    cx1, cy1 = min(im.width, layer.width - x), min(im.height, layer.height - y)
    if cx1 > cx0 and cy1 > cy0:
        layer.alpha_composite(im.crop((cx0, cy0, cx1, cy1)), (x + cx0, y + cy0))


# ------------------------------------------------------------------ text boxes
def text_box(xy, s, size, font=F_HEAD, anchor='m'):
    """Box of a line drawn with style.words(layer, xy, s, size, ...)."""
    f = font(size)
    d = ImageDraw.Draw(Image.new('L', (1, 1)))
    ws = s.split(' ')
    total = sum(d.textlength(x, font=f) for x in ws) + 0.28 * size * (len(ws) - 1)
    x0 = xy[0] - total / 2 if anchor == 'm' else (xy[0] - total if anchor == 'r' else xy[0])
    return (x0, xy[1] - size * 0.42, x0 + total, xy[1] + size * 0.42)


def words_box(xy, s, size, word, font=F_HEAD, anchor='m', nth=1):
    """Box of one word (or a run of words) inside a style.words() line."""
    f = font(size)
    d = ImageDraw.Draw(Image.new('L', (1, 1)))
    ws = s.split(' ')
    target = word.split(' ')
    x0, y0, x1, y1 = text_box(xy, s, size, font, anchor)
    x, hits = x0, 0
    for i in range(len(ws)):
        if ws[i:i + len(target)] == target:
            hits += 1
            if hits == nth:
                w = sum(d.textlength(t, font=f) for t in target) + 0.28 * size * (len(target) - 1)
                return (x, y0, x + w, y1)
        x += d.textlength(ws[i], font=f) + 0.28 * size
    raise KeyError(f'{word!r} not in {s!r}')


def grow(box, dx, dy=None):
    dy = dx if dy is None else dy
    return (box[0] - dx, box[1] - dy, box[2] + dx, box[3] + dy)


# ------------------------------------------------------------------ TEXT
def sweep(layer, box, t, start, dur=0.45, colour=TERRA, alpha=0.42, until=None, exit='settle', seed=1, sound=True):
    """Marker swept behind a word or sentence. Draw it BEFORE the text (same layer or one below)."""
    if sound:
        sfx('swipe', start, (box[0] + box[2]) / 2)
    k = life(t, start, until, exit)
    p = pen((t - start) / dur)
    if p <= 0 or k <= 0:
        return
    x0, y0, x1, y1 = grow(box, 10, 4)
    r = np.random.default_rng(seed)
    xe = x0 + (x1 - x0) * p
    top = [(x, y0 + r.normal(0, 1.6) + 3 * math.sin(x / 70 + seed)) for x in np.linspace(x0, xe, 14)]
    bot = [(x, y1 + r.normal(0, 1.6) - 3 * math.sin(x / 60 + seed)) for x in np.linspace(xe, x0, 14)]
    pts = [(x0 + 6, y0 + 4)] + top + [(xe + 6, (y0 + y1) / 2)] + bot
    m = Image.new('L', (layer.width, layer.height), 0)
    ImageDraw.Draw(m).polygon(pts, fill=int(255 * alpha * k))
    bb = (int(x0 - 12), int(y0 - 12), int(x1 + 14), int(y1 + 12))
    tile = Image.new('RGBA', (bb[2] - bb[0], bb[3] - bb[1]), colour + (0,))
    tile.putalpha(m.crop(bb).filter(ImageFilter.GaussianBlur(0.8)))
    _comp(layer, tile, bb[0], bb[1])


def underline(layer, box, t, start, dur=0.45, colour=TERRA, width=8, double=False, until=None, exit='settle', seed=2, sound=True):
    """Hand-drawn underline (optionally a second, shorter return stroke)."""
    if sound:
        sfx('marker', start, (box[0] + box[2]) / 2, dur=dur)
    k = life(t, start, until, exit)
    x0, x1, y = box[0] - 8, box[2] + 10, box[3] + 10
    pts = wobble([(x0, y + 2), ((x0 + x1) / 2, y - 3), (x1, y + 1)], 1.8, seed)
    stroke(layer, pts, pen((t - start) / dur), width, colour, k)
    if double:
        pts2 = wobble([(x1 - 20, y + 14), ((x0 + x1) / 2, y + 11), (x0 + 40, y + 15)], 1.8, seed + 1)
        stroke(layer, pts2, pen((t - start - dur * 0.85) / (dur * 0.8)), width * 0.8, colour, k)


def ring(layer, box, t, start, dur=0.6, colour=TERRA, width=8, turns=1.12, tilt=-4, until=None, exit='settle', seed=3, sound=True):
    """A hand-drawn ellipse around a word or a photo detail; it overshoots its own start like a
    real pen loop."""
    if sound:
        sfx('marker', start, (box[0] + box[2]) / 2, dur=dur)
    k = life(t, start, until, exit)
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    rx, ry = (box[2] - box[0]) / 2 + 18, (box[3] - box[1]) / 2 + 14
    r = np.random.default_rng(seed)
    a0, tl = r.uniform(-2.6, -2.0), math.radians(tilt)
    pts = []
    for i in range(90):
        a = a0 + i / 89 * 2 * math.pi * turns
        g = 1 + 0.05 * math.sin(3 * a + seed) + 0.04 * (i / 89)          # loosening loop
        x, y = rx * g * math.cos(a), ry * g * math.sin(a)
        pts.append((cx + x * math.cos(tl) - y * math.sin(tl), cy + x * math.sin(tl) + y * math.cos(tl)))
    stroke(layer, wobble(pts, 1.4, seed, 8), pen((t - start) / dur), width, colour, k)


def outline(layer, box, t, start, dur=0.7, colour=TERRA, width=6, until=None, exit='settle', seed=4, sound=True):
    """Rectangle drawn as four quick strokes whose corners overshoot, like a fast editor's box."""
    if sound:
        sfx('marker', start, (box[0] + box[2]) / 2, dur=dur)
    k = life(t, start, until, exit)
    x0, y0, x1, y1 = grow(box, 14, 10)
    o = 12
    sides = [[(x0 - o, y0), (x1 + 4, y0 - 2)], [(x1, y0 - o), (x1 + 2, y1 + 4)],
             [(x1 + o, y1), (x0 - 4, y1 + 2)], [(x0, y1 + o), (x0 - 2, y0 - 6)]]
    for i, sd in enumerate(sides):
        u = (t - start - i * dur / 4.6) / (dur / 3.6)
        stroke(layer, wobble(sd, 1.3, seed + i), pen(u), width, colour, k)


def strike(layer, box, t, start, dur=0.35, colour=TERRA, width=9, scribble=False, until=None, exit=None, seed=5, sound=True):
    """Red strike-through, slightly slanted; scribble=True crosses it out twice."""
    if sound:
        sfx('marker', start, (box[0] + box[2]) / 2, dur=dur)
    k = life(t, start, until, exit) if exit else (1.0 if t >= start else 0.0)
    x0, x1, ym = box[0] - 10, box[2] + 10, (box[1] + box[3]) / 2 + 2
    stroke(layer, wobble([(x0, ym + 6), (x1, ym - 6)], 1.2, seed), pen((t - start) / dur), width, colour, k)
    if scribble:
        stroke(layer, wobble([(x1, ym + 8), (x0 + 6, ym - 4)], 1.2, seed + 1), pen((t - start - dur) / dur), width, colour, k)


def emphasis(layer, xy, word, size, t, start, font=F_HEAD, base=INK, colour=TERRA, scale=1.12, dur=0.5, until=None, anchor='m', sound=False):
    """An important word turns terracotta and swells slightly, then settles back to full size.
    Draw the word with this instead of words() (it also draws the word before `start`)."""
    if sound:
        sfx('tick', start, xy[0])
    f = font(size)
    u = (t - start) / dur
    c = _c(u / 0.4)
    if until is not None and t > until:
        c *= 1 - _c((t - until) / 0.5)
    col = tuple(int(base[i] + (colour[i] - base[i]) * c) for i in range(3))
    sc = 1 + (scale - 1) * math.sin(math.pi * _c(u)) if t >= start else 1.0
    d = ImageDraw.Draw(Image.new('L', (1, 1)))
    l, tp, r_, b = d.textbbox((0, 0), word, font=f)
    pad = 12
    im = Image.new('RGBA', (r_ - l + 2 * pad, b - tp + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - l, pad - tp), word, font=f, fill=col + (255,))
    if abs(sc - 1) > 1e-3:
        im = im.resize((int(im.width * sc), int(im.height * sc)), Image.BICUBIC)
    x = xy[0] - im.width / 2 if anchor == 'm' else xy[0] - pad * sc
    _comp(layer, im, x, xy[1] - im.height / 2)


# ------------------------------------------------------------------ PHOTOS
def arrow(layer, p0, p1, t, start, dur=0.55, colour=TERRA, width=8, bend=0.22, head=26, until=None, exit='settle', seed=6, sound=True):
    """Curved hand-drawn arrow from p0 to p1; the head is two quick strokes once the shaft lands."""
    if sound:
        sfx('marker', start, p1[0], dur=dur)
    k = life(t, start, until, exit)
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    c = (mx - dy * bend, my + dx * bend)
    pts = [((1 - s) ** 2 * p0[0] + 2 * (1 - s) * s * c[0] + s * s * p1[0],
            (1 - s) ** 2 * p0[1] + 2 * (1 - s) * s * c[1] + s * s * p1[1]) for s in np.linspace(0, 1, 40)]
    stroke(layer, wobble(pts, 1.2, seed), pen((t - start) / dur), width, colour, k)
    a = math.atan2(p1[1] - pts[-4][1], p1[0] - pts[-4][0])
    for j, side in enumerate((1, -1)):
        q = (p1[0] - head * math.cos(a + side * 0.5), p1[1] - head * math.sin(a + side * 0.5))
        stroke(layer, [p1, q], pen((t - start - dur - 0.06 * j) / 0.14), width, colour, k)


def frame(layer, box, t, start, dur=0.7, colour=TERRA, width=6, until=None, exit='settle', seed=7, sound=True):
    """A rectangular frame isolating an area of a photograph (same hand as outline())."""
    outline(layer, (box[0] + 14, box[1] + 10, box[2] - 14, box[3] - 10), t, start, dur, colour, width, until, exit, seed, sound)


def corners(layer, box, t, start, dur=0.4, colour=TERRA, width=7, arm=46, until=None, exit='settle', seed=8, sound=True):
    """Crop marks: four L-shaped corners snapping in around a region."""
    if sound:
        sfx('tick', start, (box[0] + box[2]) / 2)
    k = life(t, start, until, exit)
    s = 1 + 0.25 * (1 - pop((t - start) / dur, 0.0))
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    hw, hh = (box[2] - box[0]) / 2 * s, (box[3] - box[1]) / 2 * s
    p = pen((t - start) / dur)
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        x, y = cx + sx * hw, cy + sy * hh                       # corner; both arms point inward
        stroke(layer, [(x, y - sy * arm), (x, y), (x - sx * arm, y)], p, width, colour, k, taper=False)


def spotlight(layer, centre, radius, t, start, dur=0.6, dim=0.42, colour=CHARCOAL, until=None, exit='fade', feather=22, sound=True):
    """Everything outside a soft circle dims, focusing the eye. Draw it last on the layer that
    holds the photo (shot.mid) so it covers the paper and the photo but not the captions."""
    if sound:
        sfx('zoom', start, centre[0], dur=dur)
    k = life(t, start, until, exit) * pen((t - start) / dur)
    if k <= 0.01:
        return
    r = radius * (1.6 - 0.6 * pen((t - start) / dur))
    q = 4
    m = Image.new('L', (layer.width // q, layer.height // q), int(255 * dim * k))
    ImageDraw.Draw(m).ellipse(((centre[0] - r) / q, (centre[1] - r) / q, (centre[0] + r) / q, (centre[1] + r) / q), fill=0)
    m = m.filter(ImageFilter.GaussianBlur(feather / q)).resize(layer.size, Image.BILINEAR)
    ov = Image.new('RGBA', layer.size, colour + (0,))
    ov.putalpha(m)
    layer.alpha_composite(ov)


def magnify(layer, src, centre, radius, zoom, to, t, start, dur=0.5, colour=TERRA, until=None, exit='fade', sound=True):
    """A loupe: the region of `src` (usually the layer itself, after the photo is drawn) around
    `centre` is enlarged `zoom` times into a round lens placed at `to`, joined to the detail by a
    hand-drawn line and a small ring."""
    if sound:
        sfx('zoom', start, to[0], dur=dur)
    k = life(t, start, until, exit)
    p = pop((t - start) / dur, 0.08)
    if p <= 0.01 or k <= 0.01:
        return
    ring(layer, (centre[0] - radius / zoom, centre[1] - radius / zoom, centre[0] + radius / zoom, centre[1] + radius / zoom),
         t, start, 0.35, colour, 5, until=until, exit=exit, sound=False)
    stroke(layer, wobble([centre, to], 1.0, 9), pen((t - start - 0.15) / 0.3), 4, colour, k)
    rr = radius / zoom
    crop = src.crop((int(centre[0] - rr), int(centre[1] - rr), int(centre[0] + rr), int(centre[1] + rr)))
    R = max(4, int(radius * p))
    lens = crop.convert('RGBA').resize((2 * R, 2 * R), Image.BICUBIC)
    m = Image.new('L', (2 * R * SS, 2 * R * SS), 0)
    ImageDraw.Draw(m).ellipse((0, 0, 2 * R * SS - 1, 2 * R * SS - 1), fill=255)
    lens.putalpha(m.resize((2 * R, 2 * R), Image.LANCZOS).point(lambda v: int(v * k)))
    sh = Image.new('RGBA', (2 * R + 40, 2 * R + 40), (40, 26, 14, 0))
    sm = Image.new('L', sh.size, 0)
    ImageDraw.Draw(sm).ellipse((20, 26, 20 + 2 * R, 26 + 2 * R), fill=int(80 * k))
    sh.putalpha(sm.filter(ImageFilter.GaussianBlur(10)))
    _comp(layer, sh, to[0] - R - 20 + 8, to[1] - R - 20 + 10)
    rim = Image.new('RGBA', (2 * R + 16, 2 * R + 16), PAL.light + (0,))
    rm = Image.new('L', ((2 * R + 16) * SS, (2 * R + 16) * SS), 0)
    ImageDraw.Draw(rm).ellipse((0, 0, (2 * R + 16) * SS - 1, (2 * R + 16) * SS - 1), fill=int(255 * k))
    rim.putalpha(rm.resize(rim.size, Image.LANCZOS))
    _comp(layer, rim, to[0] - R - 8, to[1] - R - 8)
    _comp(layer, lens, to[0] - R, to[1] - R)
    stroke(layer, [(to[0] + (R + 8) * math.cos(a), to[1] + (R + 8) * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 60)],
           1.0, 4, colour, k, taper=False)


def focus(shot, box, at, hold=2.0, dur=1.2, fill=0.85):
    """Camera travels into a detail, holds, and pulls back out (wraps Shot.zoom_to)."""
    shot.zoom_to(box, at, dur=dur, fill=fill, back_at=at + dur + hold)


# ------------------------------------------------------------------ DOCUMENTS / INFO
def mark(layer, xy, kind, t, start, size=34, colour=TERRA, width=7, until=None, exit='settle', seed=10, sound=True):
    """Margin marks: 'tick', 'cross', 'star' (asterisk), 'dash', 'question'."""
    if sound:
        sfx('tick', start, xy[0])
    k = life(t, start, until, exit)
    x, y, s = xy[0], xy[1], size
    shapes = {'tick': [[(x - s * .5, y), (x - s * .1, y + s * .4), (x + s * .6, y - s * .55)]],
              'cross': [[(x - s * .45, y - s * .45), (x + s * .45, y + s * .45)], [(x + s * .45, y - s * .45), (x - s * .45, y + s * .45)]],
              'star': [[(x, y - s * .5), (x, y + s * .5)], [(x - s * .45, y - s * .25), (x + s * .45, y + s * .25)], [(x + s * .45, y - s * .25), (x - s * .45, y + s * .25)]],
              'dash': [[(x - s * .5, y), (x + s * .5, y)]],
              'question': [[(x - s * .3, y - s * .3), (x - s * .1, y - s * .55), (x + s * .25, y - s * .5), (x + s * .3, y - s * .2), (x, y + s * .05), (x, y + s * .2)], [(x, y + s * .45), (x + 1, y + s * .5)]]}
    for i, pts in enumerate(shapes[kind]):
        stroke(layer, wobble(pts, 0.8, seed + i, 4), pen((t - start - i * 0.12) / 0.18), width, colour, k)


def bracket(layer, x, y0, y1, t, start, side='left', dur=0.5, colour=TERRA, width=6, depth=26, until=None, exit='settle', seed=11, sound=True):
    """A curly brace grouping lines of a document; side='left' opens to the right."""
    if sound:
        sfx('marker', start, x, dur=dur)
    k = life(t, start, until, exit)
    s_ = 1 if side == 'left' else -1          # left brace: arms open to the right, tip points left
    ym = (y0 + y1) / 2
    d_ = min(depth, (y1 - y0) / 4)
    ctrl = [(x + s_ * d_, y0), (x, y0 + d_), (x, ym - d_ * 0.7), (x - s_ * d_ * 0.8, ym),
            (x, ym + d_ * 0.7), (x, y1 - d_), (x + s_ * d_, y1)]
    stroke(layer, wobble(_chaikin(ctrl, 3), 0.9, seed, 5), pen((t - start) / dur), width, colour, k)


def _chaikin(pts, n=2):
    for _ in range(n):
        out = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            out += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        out.append(pts[-1])
        pts = out
    return pts


def stat(layer, xy, text, size, t, start, colour=TERRA, font=F_HEAD, until=None, exit='settle'):
    """A statistic that matters: a marker sweep lands behind it, then the figure turns
    terracotta and swells briefly."""
    box = text_box(xy, text, size, font)
    sweep(layer, box, t, start, 0.4, BEIGE, 0.9, until, exit)
    emphasis(layer, xy, text, size, t, start + 0.25, font, INK, colour, 1.1, until=until)


def connect(layer, pts, t, start, dur=0.6, colour=TERRA, width=5, dashed=False, arrowhead=True, dots=True, until=None, exit='settle', seed=12, sound=True):
    """A connecting line between items (a route through several points), with end dots and an
    optional arrowhead."""
    if sound:
        sfx('marker', start, pts[-1][0], dur=dur)
    k = life(t, start, until, exit)
    p = pen((t - start) / dur)
    if dots and t >= start:
        d = ImageDraw.Draw(layer)
        x, y = pts[0]
        d.ellipse((x - 8, y - 8, x + 8, y + 8), fill=colour + (int(255 * k),))
    path = wobble(pts, 1.0, seed)
    if dashed:
        seg = _resample(path, 4)
        n = len(seg)
        for i in range(0, n - 1, 6):
            if i / n < p:
                stroke(layer, seg[i:i + 4], 1.0, width, colour, k, taper=False)
    else:
        stroke(layer, path, p, width, colour, k)
    if p >= 1 and arrowhead:
        a = math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0])
        for side in (1, -1):
            stroke(layer, [pts[-1], (pts[-1][0] - 20 * math.cos(a + side * 0.5), pts[-1][1] - 20 * math.sin(a + side * 0.5))],
                   pen((t - start - dur) / 0.12), width, colour, k)
    elif p >= 1 and dots:
        x, y = pts[-1]
        ImageDraw.Draw(layer).ellipse((x - 8, y - 8, x + 8, y + 8), fill=colour + (int(255 * k),))


def bars(layer, box, values, t, start, highlight=(), labels=None, colour=TERRA, base=BEIGE, ink=CHARCOAL, stagger=0.08, fill_at=None, sound=True):
    """A small bar chart drawn in: the axis, then bars rise one by one; at fill_at the
    highlighted bars fill with terracotta from the bottom (only the bars the narration names)."""
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(layer)
    if t >= start:
        stroke(layer, [(x0, y1), (x1, y1)], pen((t - start) / 0.4), 4, ink, 1.0, taper=False)
    n = len(values)
    vmax = max(values) or 1
    bw = (x1 - x0) / (n * 1.5 + 0.5)
    for i, v in enumerate(values):
        u = pop((t - start - 0.3 - i * stagger) / 0.5, 0.06)
        if u <= 0:
            continue
        bx = x0 + bw * (0.5 + 1.5 * i)
        top = y1 - (y1 - y0) * (v / vmax) * u
        d.rectangle((bx, top, bx + bw, y1 - 2), fill=base + (255,))
        if i in highlight and fill_at is not None and t >= fill_at:
            f = pen((t - fill_at) / 0.5)
            d.rectangle((bx, y1 - 2 - (y1 - 2 - top) * f, bx + bw, y1 - 2), fill=colour + (255,))
        if labels:
            d.text((bx + bw / 2, y1 + 22), labels[i], font=F_TYPE(22), fill=ink + (255,), anchor='mm')
    if sound and fill_at is not None:
        sfx('swipe', fill_at, (x0 + x1) / 2)


def wedge(layer, centre, r, a0, a1, t, start, dur=0.6, colour=TERRA, base=BEIGE, ink=CHARCOAL, sound=True):
    """Pie chart: the disc draws in, then the section from a0 to a1 (degrees, 0 = up,
    clockwise) fills with the accent like a clock hand sweeping."""
    if sound:
        sfx('swipe', start + 0.3, centre[0])
    if t < start:
        return
    cx, cy = centre
    q = 2
    m = Image.new('RGBA', (int(2 * r + 8) * q, int(2 * r + 8) * q), (0, 0, 0, 0))
    d = ImageDraw.Draw(m)
    bb = (4 * q, 4 * q, (2 * r + 4) * q, (2 * r + 4) * q)
    d.ellipse(bb, fill=base + (int(255 * pen((t - start) / 0.3)),))
    f = pen((t - start - 0.3) / dur)
    if f > 0:
        d.pieslice(bb, a0 - 90, a0 - 90 + (a1 - a0) * f, fill=colour + (255,))
    m = m.resize((int(2 * r + 8), int(2 * r + 8)), Image.LANCZOS)
    _comp(layer, m, cx - r - 4, cy - r - 4)
    stroke(layer, [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 80)],
           pen((t - start) / 0.4), 3, ink, 1.0, taper=False)
