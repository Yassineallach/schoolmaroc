"""Data visualisation in the editorial paper style (complements annotate.bars / wedge / stat).

    line_chart(s.mid, box, [(1950, 2.5), (1988, 5.1), ...], t, start, mark=(1988, 'PUBLISHED'))
    compare(s.mid, (x, y, width), [('Hawking', 237), ('Next', 41)], t, start, unit=' weeks')
    unit_grid(s.mid, (x, y), 100, 33, t, start)               # "one in three" as 100 dots
    counter(s.top, (960, 400), 0, 10_000_000, t, start, suffix='+')
    flow(s.mid, [((x, y), 'STAR'), ((x2, y2), 'COLLAPSE'), ...], t, [start0, start1, ...])
    scale(s.mid, (x, y), [('EARTH', 1), ('SUN', 109)], t, start)

Only chart numbers the narration states. Each chart reveals step by step, on its cue.
"""
import math
import numpy as np
from PIL import Image, ImageDraw
from vox import F_HEAD, F_TYPE, INK
from style import sfx
import presets as P
import annotate as A

TERRA = (205, 88, 48)
BEIGE = (221, 200, 170)
CHARCOAL = (55, 52, 50)
MUTED = (150, 140, 128)


def _fmt(v, decimals=0):
    return f'{v:,.{decimals}f}'


def line_chart(layer, box, points, t, start, dur=1.6, colour=TERRA, axis=CHARCOAL, mark=None, ylabel=None, until=None):
    """Axes draw on, then the line draws through its points left to right; `mark=(x, label)`
    drops a dot and a label on that point when the pen reaches it."""
    sfx('pencil', start, (box[0] + box[2]) / 2, dur=dur + 0.4)
    if t < start:
        return
    x0, y0, x1, y1 = box
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    ymin, ymax = min(0, min(ys)), max(ys) * 1.1
    X = lambda v: x0 + (v - xs[0]) / (xs[-1] - xs[0]) * (x1 - x0)
    Y = lambda v: y1 - (v - ymin) / (ymax - ymin) * (y1 - y0)
    A.stroke(layer, [(x0, y0 - 10), (x0, y1), (x1 + 20, y1)], A.pen((t - start) / 0.4), 4, axis, 1.0, taper=False)
    d = ImageDraw.Draw(layer)
    if t > start + 0.3:
        for v in (xs[0], xs[-1]):
            d.text((X(v), y1 + 30), str(v), font=F_TYPE(26), fill=axis + (255,), anchor='mm')
        if ylabel:
            d.text((x0, y0 - 34), ylabel, font=F_TYPE(26), fill=axis + (255,), anchor='lm')
    pts = [(X(a), Y(b)) for a, b in points]
    p = A.pen((t - start - 0.4) / dur)
    A.stroke(layer, A._resample(pts, 4), p, 6, colour, 1.0)
    if mark is not None:
        mx = X(mark[0])
        frac = (mx - x0) / (x1 - x0)
        if p >= frac:
            my = Y(np.interp(mark[0], xs, ys))
            u = A.pop((t - start - 0.4 - dur * frac) / 0.35)
            r = 12 * u
            d.ellipse((mx - r, my - r, mx + r, my + r), fill=colour + (255,), outline=(244, 238, 224, 255), width=3)
            A.stroke(layer, [(mx, my - 18), (mx, my - 80)], A.pen((t - start - 0.4 - dur * frac - 0.1) / 0.25), 3, colour, 1.0, taper=False)
            d.text((mx, my - 104), mark[1], font=F_HEAD(30), fill=colour + (int(255 * min(1, u)),), anchor='mm')
            sfx('pop', start + 0.4 + dur * frac, mx)


def compare(layer, origin, items, t, start, width=900, height=70, gap=40, unit='', stagger=0.35, highlight=0, decimals=0):
    """Horizontal bars for a comparison; each grows with its value counting up beside it. The
    highlighted bar (index) is terracotta, the others beige."""
    x, y = origin
    vmax = max(v for _, v in items) or 1
    d = ImageDraw.Draw(layer)
    for i, (label, v) in enumerate(items):
        st = start + i * stagger
        sfx('swipe', st, x + width / 2)
        if t < st:
            continue
        yy = y + i * (height + gap)
        u = A.pop((t - st) / 0.8, 0.05)
        wv = width * v / vmax * u
        d.text((x - 20, yy + height / 2), label, font=F_HEAD(34), fill=INK + (255,), anchor='rm')
        d.rectangle((x, yy, x + wv, yy + height), fill=(TERRA if i == highlight else BEIGE) + (255,))
        shown = v * min(1.0, A.pen((t - st) / 0.8))
        d.text((x + wv + 18, yy + height / 2), _fmt(shown, decimals) + unit, font=F_HEAD(34), fill=INK + (255,), anchor='lm')


def unit_grid(layer, origin, total, k, t, start, cols=10, cell=34, colour=TERRA, base=BEIGE, dur=1.2):
    """`total` dots in a grid; the first `k` fill with the accent one after another
    ("one in three", "a third of...")."""
    x, y = origin
    d = ImageDraw.Draw(layer)
    for i in range(total):
        r_, c_ = divmod(i, cols)
        cx, cy = x + c_ * cell, y + r_ * cell
        u = A.pop((t - start - i * 0.004) / 0.3)
        if u <= 0:
            continue
        rr = cell * 0.36 * min(1.0, u)
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=base + (255,))
        if i < k:
            f = A.pop((t - start - 0.5 - i * dur / max(1, k)) / 0.25)
            if f > 0:
                rf = rr * min(1.0, f)
                d.ellipse((cx - rf, cy - rf, cx + rf, cy + rf), fill=colour + (255,))
    sfx('swipe', start + 0.5, x + cell * cols / 2)


def counter(layer, xy, a, b, t, start, dur=1.6, size=150, colour=INK, accent=TERRA, prefix='', suffix='', decimals=0):
    """A number counting up (thousands separators), easing out and landing in the accent."""
    for k in range(10):
        sfx('tick', start + dur * (1 - (1 - k / 10) ** 0.5), xy[0])
    if t < start:
        return
    u = A.pen((t - start) / dur)
    v = a + (b - a) * u
    land = A._c((t - start - dur) / 0.3)
    col = tuple(int(colour[i] + (accent[i] - colour[i]) * land) for i in range(3))
    sc = 1 + 0.06 * math.sin(math.pi * land)
    f = F_HEAD(int(size * sc))
    ImageDraw.Draw(layer).text(xy, prefix + _fmt(v, decimals) + suffix, font=f, fill=col + (255,), anchor='mm')


def flow(layer, nodes, t, starts, colour=TERRA, box_w=300, box_h=110, links=None):
    """A diagram: paper boxes appear on their cues, joined by hand-drawn arrows in order
    (or by `links` = [(i, j), ...])."""
    links = links or [(i, i + 1) for i in range(len(nodes) - 1)]
    for (i, j) in links:
        if t < starts[j]:
            continue
        (ax, ay), (bx, by) = nodes[i][0], nodes[j][0]
        ang = math.atan2(by - ay, bx - ax)
        ox, oy = math.cos(ang), math.sin(ang)
        pad = lambda: (box_w / 2 + 18) / max(abs(ox), 1e-3) if abs(ox) * box_h > abs(oy) * box_w else (box_h / 2 + 18) / max(abs(oy), 1e-3)
        r = pad()
        A.arrow(layer, (ax + ox * r, ay + oy * r), (bx - ox * r, by - oy * r), t, starts[j] - 0.35, dur=0.35, bend=0.08, width=5, sound=True)
    for k, ((x, y), label) in enumerate(nodes):
        if t < starts[k]:
            continue
        card = P.paper_card(box_w, box_h, seed=k + 31, colour=(246, 241, 229))
        ImageDraw.Draw(card).text((box_w / 2, box_h / 2), label, font=F_HEAD(36), fill=INK + (255,), anchor='mm')
        P.drop(layer, card, x, y, t, starts[k], rot=(-2, 1.5, -1, 2)[k % 4], spin=6, height=0.4, key=('flow', k, label))


def scale(layer, origin, items, t, start, max_r=300, stagger=0.6, colour=TERRA, base=BEIGE):
    """Size comparison: circles whose AREA follows the values, growing one after another along
    a baseline, the largest in the accent."""
    x, y = origin
    vmax = max(v for _, v in items)
    d = ImageDraw.Draw(layer)
    cx = x
    for i, (label, v) in enumerate(items):
        r = max(6, max_r * math.sqrt(v / vmax))
        st = start + i * stagger
        sfx('pop', st, cx + r)
        u = A.pop((t - st) / 0.6, 0.06)
        if u > 0:
            rr = r * u
            d.ellipse((cx, y - 2 * rr, cx + 2 * rr, y), fill=(colour if v == vmax else base) + (255,))
            d.text((cx + rr, y + 34), label, font=F_HEAD(30), fill=INK + (255,), anchor='mm')
        cx += 2 * r + 60
