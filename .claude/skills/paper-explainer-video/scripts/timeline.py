"""Timelines: chronological storytelling on paper.

    T = Timeline(1940, 2020, box=(160, 520, 1760, 560), step=10)
    T.axis(s.mid, t, start)                                   # rule draws on, ticks and years follow
    T.event(s.mid, 1963, 'Diagnosis', t, w(cue(10, '1963')), side='up')      # card on its date
    T.era(s.mid, 1974, 1988, 'Writing the book', t, start)    # bracket spanning a period
    T.now(s.mid, 1988, t, start, frm=1963)                    # a marker sliding along the years
    year_counter(s.top, (960, 300), 1963, 1988, t, start, dur=1.6)            # rolling year digits
    s.pan(...) / T.focus(s, year, at) to travel along a long timeline

Every element appears only when its date is spoken; earlier cards can settle (until=).
"""
import math
import numpy as np
from PIL import Image, ImageDraw
from vox import F_HEAD, F_TYPE, F_SERIF, INK, CREAM
from style import sfx
import presets as P
import annotate as A

TERRA = (205, 88, 48)
LINE = (70, 64, 58)


class Timeline:
    def __init__(self, y0, y1, box=(160, 520, 1760, 560), step=10, minor=None, label_every=None):
        self.y0, self.y1, self.box, self.step = y0, y1, box, step
        self.minor = minor if minor is not None else max(1, step // 5)
        self.label_every = label_every or step

    def x(self, year):
        x0, _, x1, _ = self.box
        return x0 + (year - self.y0) / (self.y1 - self.y0) * (x1 - x0)

    @property
    def y(self):
        return (self.box[1] + self.box[3]) / 2

    def axis(self, layer, t, start, dur=1.0, colour=LINE, width=5, labels=True):
        """The rule draws on left to right; ticks and year labels appear as the pen passes."""
        sfx('pencil', start, (self.box[0] + self.box[2]) / 2, dur=dur)
        x0, _, x1, _ = self.box
        p = A.pen((t - start) / dur)
        if p <= 0:
            return
        y = self.y
        A.stroke(layer, A.wobble([(x0 - 30, y), (x1 + 30, y)], 1.0, 3), p, width, colour, taper=False)
        d = ImageDraw.Draw(layer)
        yr = self.y0
        while yr <= self.y1:
            xx = self.x(yr)
            if (xx - x0 + 30) / (x1 - x0 + 60) <= p:
                major = (yr - self.y0) % self.step == 0
                h = 18 if major else 8
                d.line((xx, y - h, xx, y + h), fill=colour + (255,), width=3 if major else 2)
                if labels and major and (yr - self.y0) % self.label_every == 0:
                    d.text((xx, y + 44), str(yr), font=F_TYPE(30), fill=colour + (255,), anchor='mm')
            yr += self.minor

    def event(self, layer, year, label, t, start, side='up', colour=TERRA, size=34, until=None, exit='settle', sub=None):
        """A dated event: a dot lands on the axis, a stem rises, a paper card with the date and
        the label pops at the end of it."""
        sfx('pop', start, self.x(year))
        if t < start:
            return
        k = A.life(t, start, until, exit)
        x, y = self.x(year), self.y
        u = A.pop((t - start) / 0.4)
        d = ImageDraw.Draw(layer)
        r = 11 * min(1.0, u)
        d.ellipse((x - r, y - r, x + r, y + r), fill=colour + (int(255 * k),))
        sgn = -1 if side == 'up' else 1
        stem = 120
        A.stroke(layer, [(x, y + sgn * 14), (x, y + sgn * stem)], A.pen((t - start - 0.1) / 0.3), 3, colour, k, taper=False)
        if t > start + 0.3:
            f, fs = F_HEAD(size), F_TYPE(26)
            dd = ImageDraw.Draw(Image.new('L', (1, 1)))
            tw = max(dd.textlength(label, font=f), dd.textlength(str(year), font=fs), dd.textlength(sub or '', font=fs))
            hh = 104 + (34 if sub else 0)
            card = P.paper_card(int(tw + 48), hh, seed=int(year) % 97, colour=(246, 241, 229))
            dc = ImageDraw.Draw(card)
            dc.text((24, 30), str(year), font=fs, fill=colour + (255,), anchor='lm')
            dc.text((24, 70), label, font=f, fill=INK + (255,), anchor='lm')
            if sub:
                dc.text((24, 108), sub, font=fs, fill=(90, 84, 78, 255), anchor='lm')
            q = A.pop((t - start - 0.3) / 0.4, 0.08)
            cy = y + sgn * (stem + hh / 2)
            P.put(layer, P.fade_img(P.rot_scale(card, -1.5 * sgn, 0.85 + 0.15 * q), k * min(1.0, q * 2)), x, cy, lift=0.15)

    def era(self, layer, a, b, label, t, start, colour=TERRA, until=None, exit='settle'):
        """A bracket over a span of years with its label, drawn left to right."""
        sfx('marker', start, self.x((a + b) / 2), dur=0.6)
        if t < start:
            return
        k = A.life(t, start, until, exit)
        xa, xb, y = self.x(a), self.x(b), self.y - 70
        p = A.pen((t - start) / 0.6)
        A.stroke(layer, A.wobble([(xa, y + 24), (xa, y), (xb, y), (xb, y + 24)], 0.8, int(a)), p, 5, colour, k)
        if p > 0.6:
            ImageDraw.Draw(layer).text(((xa + xb) / 2, y - 30), label, font=F_TYPE(30), fill=colour + (int(255 * k * min(1, (p - 0.6) / 0.3)),), anchor='mm')

    def now(self, layer, year, t, start, frm=None, dur=1.2, colour=INK):
        """A marker sliding along the axis to `year` (from `frm`), like a finger on the dates."""
        sfx('slide', start, self.x(year), dur=dur)
        if t < start:
            return
        u = A.pen((t - start) / dur)
        yr = year if frm is None else frm + (year - frm) * u
        x, y = self.x(yr), self.y
        d = ImageDraw.Draw(layer)
        d.polygon([(x - 16, y - 46), (x + 16, y - 46), (x, y - 18)], fill=colour + (255,))
        d.text((x, y - 66), str(int(round(yr))), font=F_HEAD(30), fill=colour + (255,), anchor='mm')

    def focus(self, shot, year, at, dur=1.4, zoom=1.6):
        """Camera travels along the timeline to a date and closes in on it."""
        box = (self.x(year) - 960 / zoom, self.y - 540 / zoom, self.x(year) + 960 / zoom, self.y + 540 / zoom)
        shot.zoom_to(box, at, dur=dur, fill=1.0)


def year_counter(layer, xy, a, b, t, start, dur=1.4, size=180, colour=INK, accent=TERRA):
    """Years rolling like an odometer from a to b, each digit drum turning, landing on b in
    the accent colour."""
    for k in range(int(dur / 0.07)):                     # the drum clicking (slowing as it lands)
        sfx('tick', start + dur * (1 - (1 - k * 0.07 / dur) ** 0.5), xy[0])
    if t < start:
        return
    u = A.pen((t - start) / dur)
    val = a + (b - a) * u
    s_a, s_b = str(a), str(b)
    n = max(len(s_a), len(s_b))
    f = F_HEAD(size)
    dd = ImageDraw.Draw(Image.new('L', (1, 1)))
    cw = dd.textlength('0', font=f) * 1.02
    x0 = xy[0] - cw * n / 2
    tile = Image.new('RGBA', (int(cw * n) + 8, int(size * 1.3)), (0, 0, 0, 0))
    dt = ImageDraw.Draw(tile)
    col = tuple(int(colour[i] + (accent[i] - colour[i]) * A._c((t - start - dur) / 0.3)) for i in range(3))
    for i in range(n):
        place = 10 ** (n - 1 - i)
        v = val / place
        digit = int(v) % 10
        frac = v - int(v) if u < 1 else 0.0
        if place > 1:
            frac = frac ** 6                                  # higher digits flip late, like a real counter
        y = tile.height / 2
        for j, dg in ((0, digit), (1, (digit + 1) % 10)):
            dt.text((cw * (i + 0.5) + 4, y + (j - frac) * size * 1.1), str(dg), font=f, fill=col + (255,), anchor='mm')
    m = Image.new('L', tile.size, 0)
    ImageDraw.Draw(m).rectangle((0, int(size * 0.12), tile.width, int(tile.height - size * 0.12)), fill=255)
    tile.putalpha(Image.fromarray(np.minimum(np.asarray(tile.getchannel('A')), np.asarray(m))))
    A._comp(layer, tile, x0 - 4, xy[1] - tile.height / 2)
