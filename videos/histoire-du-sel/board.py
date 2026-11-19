"""The big board (the user's note: « move from one scene to another without transition, like moving a
camera to a new scene, like we have a big board and we're drawing scenes one beside one »).

The whole film is one long parchment board. Every drawing has its own place on it, in film order,
along a gently winding row. The camera rests on one drawing while the pen draws it, then travels
across the board to the next free place (pulling back a little on the way, so the drawings already
made pass by), and the pen starts the next drawing as the camera arrives. No cuts, no wipes.

    B = Board(entries)          entries: Entry(code, label, arrive, focus=..., extras=[...])
    SHOTS = [(0.0, B.scene)]    one continuous shot for the whole act

The layout is global (LAYOUT, by drawing code), so act 2 starts on act 1's last drawing and travels on.
"""
import math
import numpy as np
from PIL import Image
from vox import W, H
import scenes as S
import plates as PL
from style import Shot, sfx

CELL = 1720                   # distance between two drawings on the board (they nearly touch)
PAN = 1.25                    # seconds the camera takes to travel to the next drawing
DIP = 0.20                    # how far it pulls back mid-travel (0.2 = to 80 %)
START_EARLY = 0.5             # the pen starts this long before the camera has fully landed
HOLD_PUSH = 0.035             # slow push while the pen draws
ORDER = ['G%02d' % i for i in range(1, 32)]
_DY = [0, 110, -80, 60, -120, 40, 130, -50, 90, -110, 20, 120, -90, 50, -40, 100,
       -120, 10, 80, -60, 130, -20, -100, 70, 30, -130, 100, -30, 60, -80, 0]


def world(code):
    i = ORDER.index(code)
    return (i * CELL, _DY[i % len(_DY)])


class Entry:
    def __init__(self, code, label, arrive, focus=(0.5, 0.5), extras=(), backed=True, scale=1.0, offset=(0, 0)):
        self.d = PL.drawing(code, label, backed)
        self.code, self.arrive, self.focus, self.extras = code, arrive, focus, list(extras)
        self.scale, self.offset = scale, offset


def _ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


_GRAIN = None


def _grain():
    global _GRAIN
    if _GRAIN is None:
        from scipy import ndimage
        r = np.random.default_rng(1913)
        g = ndimage.gaussian_filter(r.normal(0, 1, (1024, 1024)), 0.7)
        _GRAIN = (g / g.std()).astype(np.float32)
    return _GRAIN


def ground(cx, cy, z):
    """The board's parchment under the camera: base colour, very smooth large tone changes in board
    coordinates (they move with the camera), fine grain, and an even vignette on the screen."""
    base = np.array(S.PAL.paper, np.float32)
    deep = np.array(S.PAL.paper2, np.float32)
    xs = cx + (np.arange(W, dtype=np.float32) - W / 2) / z
    ys = cy + (np.arange(H, dtype=np.float32) - H / 2) / z
    lf = (0.5 + 0.18 * np.sin(xs / 900.0 + 1.3)[None, :] + 0.14 * np.sin(ys / 640.0 + 0.4)[:, None]
          + 0.10 * np.sin((xs[None, :] + ys[:, None]) / 1500.0))
    lf = np.clip(lf, 0, 1)[..., None] * 0.35
    img = base[None, None, :] * (1 - lf) + deep[None, None, :] * lf
    g = _grain()
    gi = (ys.astype(np.int64) % 1024)[:, None], (xs.astype(np.int64) % 1024)[None, :]
    img += g[gi][..., None] * 3.2
    vy = np.linspace(-1, 1, H, dtype=np.float32)[:, None]
    vx = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
    vig = 1 - 0.16 * np.clip((vx ** 2 + vy ** 2) / 2, 0, 1) ** 1.3
    img *= vig[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')


class Board:
    def __init__(self, entries, prev=None, end=None):
        """entries: this act's drawings in order. prev: the code of the drawing the act starts from
        (the previous act's last one, already drawn), so the act opens with the camera travelling."""
        self.entries = entries
        for i, e in enumerate(entries):          # the pen gets at most 60 % of the time before the next move
            e.d.layers(e.scale)
            e.start = max(0.0, e.arrive - START_EARLY) if e.arrive > 0 else 0.0   # the pen starts as the camera lands
            nxt = entries[i + 1].arrive - PAN if i + 1 < len(entries) else (end or e.arrive + 6)
            e.dur = min(PL.DRAW, max(1.2, 0.6 * (nxt - e.arrive)))
        self.prev = prev
        self.end = end
        self._done = {}

    # -- camera: rest on a drawing, travel to the next one
    def target(self, e):
        wx, wy = world(e.code)
        return wx + e.offset[0], wy + e.offset[1]

    def camera(self, t):
        es = self.entries
        stops = []
        if self.prev:
            px, py = world(self.prev)
            stops.append((-1e9, px, py))
        for e in es:
            x, y = self.target(e)
            stops.append((e.arrive - PAN, x, y))
        i = max(k for k, s in enumerate(stops) if t >= s[0]) if t >= stops[0][0] else 0
        t0, x1, y1 = stops[i]
        if i == 0 or t >= t0 + PAN:                          # resting: a slow push towards the focus
            e = es[i - 1] if self.prev else es[i]
            rest_from = (t0 + PAN) if i > 0 else 0.0
            nxt = stops[i + 1][0] if i + 1 < len(stops) else (self.end or rest_from + 8)
            k = _ease((t - rest_from) / max(0.5, nxt - rest_from))
            fx = (e.focus[0] - 0.5) * 1500 * e.scale * k * 0.25
            fy = (e.focus[1] - 0.5) * 880 * e.scale * k * 0.25
            if i == 0 and self.prev:
                return x1, y1, 1.0
            return x1 + fx, y1 + fy, 1.0 + HOLD_PUSH * k
        # travelling from the previous stop to this one
        _, x0, y0 = stops[i - 1]
        prev_e = (es[i - 2] if self.prev else es[i - 1]) if i >= 1 else None
        z0 = 1.0 + (HOLD_PUSH if prev_e is not None and not (i - 1 == 0 and self.prev) else 0.0)
        if prev_e is not None and not (i - 1 == 0 and self.prev):
            x0 += (prev_e.focus[0] - 0.5) * 1500 * prev_e.scale * 0.25
            y0 += (prev_e.focus[1] - 0.5) * 880 * prev_e.scale * 0.25
        u = (t - t0) / PAN
        k = _ease(u)
        z = (z0 + (1.0 - z0) * k) * (1 - DIP * math.sin(math.pi * min(1, max(0, u))))
        return x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, z

    # -- one drawing's cell (1920x1080, centred on its board place), as drawn by time t
    def cell(self, e, t, final=False):
        lt = t - e.start
        if final and e.code in self._done:
            return self._done[e.code]
        c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        s = Shot(0, 1)                         # a scratch shot just to draw into
        s.mid = c
        s.D = 99
        lines, fill, order = e.d.layers(e.scale)
        x0 = int(W / 2 - lines.width / 2)
        y0 = int(H / 2 - lines.height / 2)
        e.d.box = (x0, y0, lines.width, lines.height)
        PL.draw_layers(c, lines, fill, order, lt, 0.0, PL.draw_time(e), x0, y0)
        for fn in e.extras:
            fn(c, lt, e)
        if final:
            self._done[e.code] = c
        return c

    def scene(self, t, D):
        s = Shot(t, D)
        S.env(s, 'bleed')
        cx, cy, z = self.camera(t)
        frame = ground(cx, cy, z)
        items = ([(None, self.prev)] if self.prev else []) + [(e, e.code) for e in self.entries]
        for e, code in items:
            wx, wy = world(code) if e is None else world(code)
            sx = (wx - cx) * z + W / 2
            sy = (wy - cy) * z + H / 2
            if sx + W * z / 2 < 0 or sx - W * z / 2 > W or sy + H * z / 2 < 0 or sy - H * z / 2 > H:
                continue
            if e is None:
                c = self._prev_cell()
            else:
                if t < e.start - 0.01:
                    continue
                done = t - e.start > PL.draw_time(e) + 0.6 and not e.extras
                c = self.cell(e, t, final=done)
            if abs(z - 1) > 1e-3:
                c = c.resize((max(1, int(W * z)), max(1, int(H * z))), Image.BILINEAR)
            frame.alpha_composite(c, (int(round(sx - c.width / 2)), int(round(sy - c.height / 2))))
        s.mid.alpha_composite(frame)
        for e in self.entries:                 # the pen's scratch for each drawing
            sfx('draw', max(0.0, e.start), W / 2, dur=PL.draw_time(e),
                spans=tuple(tuple(round(v, 4) for v in sp) for sp in getattr(e.d, 'spans', ((0, 1),))[:400]))
        return s

    def _prev_cell(self):
        if '_prev' not in self._done:
            e = Entry(self.prev, '', -100.0)
            e.start = -100.0
            self._done['_prev'] = self.cell(e, 0.0)
        return self._done['_prev']
