"""The big board (the user's notes: « move from one scene to another without transition, like moving a
camera to a new scene, like we have a big board and we're drawing scenes one beside one »; then
« it looks like swiping, not like one board »; « no fill colour »; « use the drawing for the texts too »).

The whole film is one large parchment board, a drafting surface with a faint ruled grid. Every
drawing has its own place on it, laid out in two dimensions: from one drawing the next can be to the
right, up, down or on a diagonal, never back over earlier work. The camera is framed wide enough that
the neighbouring drawings show at the edges, so you see the board around the scene. It rests on a
drawing while the pen draws it (lines only, no fill), then travels over the board to the next place
at a constant height, like a camera on a rostrum, and the pen starts as it lands. Words are written
by the same pen (`write`), stroke by stroke.

    B = Board(entries, prev=<last drawing of the previous act>, end=...)
    SHOTS = [(0.0, B.scene)]
"""
import math
import os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from vox import W, H
import scenes as S
import plates as PL
from style import Shot, sfx

UX, UY = 1300, 900            # board spacing between neighbouring drawings (board pixels): close enough that neighbours show
SCALE = 0.80                  # drawings are drawn smaller than the frame, so the board shows around them
ZOOM = 0.80                   # camera framing at rest: wide, so the board and the neighbouring drawings are in view
PUSH = 0.14                   # the camera moves in on the drawing's detail while the pen works
DIP = 1 / 5200                # on a travel the camera pulls back with the distance (an infinite canvas)
PAN = 1.5                     # seconds the camera takes to travel to the next drawing
START_EARLY = 0.45            # the pen starts this long before the camera has fully landed
ORDER = ['M01'] + ['G%02d' % i for i in range(1, 32)]     # M = pen-drawn maps (tools/make_maps.py)


@lru_cache(maxsize=1)
def layout():
    """Board places for every drawing, in film order: a seeded walk that turns right, up, down or
    on a diagonal, never lands on an earlier place, and never runs backwards."""
    r = np.random.default_rng(1930)
    dirs = [(1.0, 0.0), (0.55, 0.85), (0.55, -0.85), (0.0, 1.0), (0.0, -1.0), (1.0, 0.45), (1.0, -0.45)]
    pts = [(0.0, 0.0)]
    last = None
    for _ in range(len(ORDER) - 1):
        x, y = pts[-1]
        for k in list(r.permutation(len(dirs))):
            dx, dy = dirs[k]
            if last is not None and (dx, dy) == last and dx == 0:
                continue                                      # no two vertical moves in a row
            nx, ny = x + dx, y + dy
            if abs(ny) > 2.2:
                continue
            if all(math.hypot(nx - px, ny - py) >= 0.98 for px, py in pts):
                pts.append((nx, ny)); last = (dx, dy)
                break
        else:
            pts.append((x + 1.0, y)); last = (1.0, 0.0)
    return {c: (p[0] * UX, p[1] * UY) for c, p in zip(ORDER, pts)}


def world(code):
    return layout()[code]


class Entry:
    def __init__(self, code, label, arrive, focus=(0.5, 0.5), extras=(), scale=1.0, offset=(0, 0)):
        self.d = PL.drawing(code, label, backed=False)        # lines only: no fill
        self.code, self.arrive, self.focus, self.extras = code, arrive, focus, list(extras)
        self.scale, self.offset = scale * SCALE, offset


def _ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


# ------------------------------------------------------------------ the board surface
_GRAIN = None


def _grain():
    global _GRAIN
    if _GRAIN is None:
        from scipy import ndimage
        r = np.random.default_rng(1913)
        g = ndimage.gaussian_filter(r.normal(0, 1, (1024, 1024)), 0.7)
        _GRAIN = (g / g.std()).astype(np.float32)
    return _GRAIN


def _lines(v, step, w):
    d = np.abs(((v + step / 2) % step) - step / 2)
    return np.clip(1 - d / w, 0, 1)


def ground(cx, cy, z):
    """The parchment under the camera, in board coordinates (it moves with the camera): smooth
    large tone changes, fine grain, a faint ruled drafting grid, and an even vignette on screen."""
    base = np.array(S.PAL.paper, np.float32)
    deep = np.array(S.PAL.paper2, np.float32)
    ink = np.array(S.PAL.ink, np.float32)
    xs = cx + (np.arange(W, dtype=np.float32) - W / 2) / z
    ys = cy + (np.arange(H, dtype=np.float32) - H / 2) / z
    lf = (0.5 + 0.18 * np.sin(xs / 900.0 + 1.3)[None, :] + 0.14 * np.sin(ys / 640.0 + 0.4)[:, None]
          + 0.10 * np.sin((xs[None, :] + ys[:, None]) / 1500.0))
    lf = np.clip(lf, 0, 1)[..., None] * 0.35
    img = base[None, None, :] * (1 - lf) + deep[None, None, :] * lf
    gx = np.maximum(_lines(xs, 120, 1.0 / z) * 0.5, _lines(xs, 600, 1.3 / z))
    gy = np.maximum(_lines(ys, 120, 1.0 / z) * 0.5, _lines(ys, 600, 1.3 / z))
    grid = np.maximum(gx[None, :], gy[:, None])[..., None] * 0.11
    img = img * (1 - grid) + ink[None, None, :] * grid
    g = _grain()
    gi = (ys.astype(np.int64) % 1024)[:, None], (xs.astype(np.int64) % 1024)[None, :]
    img += g[gi][..., None] * 3.0
    vy = np.linspace(-1, 1, H, dtype=np.float32)[:, None]
    vx = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
    img *= (1 - 0.14 * np.clip((vx ** 2 + vy ** 2) / 2, 0, 1) ** 1.3)[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')


# ------------------------------------------------------------------ words written by the pen
@lru_cache(maxsize=16)
def _text_ink(text, size):
    """A word as ink lines on transparent paper, with its pen order (centre lines, one pen)."""
    import vox
    f = ImageFont.truetype(os.path.join(os.path.dirname(vox.__file__), '..', 'assets', 'fonts', 'Fraunces500i.ttf'), size)
    d0 = ImageDraw.Draw(Image.new('L', (1, 1)))
    l, t, r, b = d0.textbbox((0, 0), text, font=f)
    pad = 20
    m = Image.new('L', (r - l + 2 * pad, b - t + 2 * pad), 0)
    ImageDraw.Draw(m).text((pad - l, pad - t), text, font=f, fill=255)
    a = np.asarray(m)
    rgba = np.zeros(a.shape + (4,), np.uint8)
    rgba[..., :3] = S.PAL.ink
    rgba[..., 3] = a
    T, spans = PL._order(a, None, step=1)
    return Image.fromarray(rgba, 'RGBA'), T, spans


def write(text, size, dx, dy, at, dur=1.1):
    """An extra for an Entry: the pen writes `text` at (dx, dy) from the drawing's centre, starting
    at act time `at` (the spoken word)."""
    def fn(c, lt, e):
        lines, T, spans = _text_ink(text, size)
        x0 = int(W / 2 + dx - lines.width / 2)
        y0 = int(H / 2 + dy - lines.height / 2)
        PL.draw_layers(c, lines, None, T, lt, at - e.start, dur, x0, y0)
    fn.sound = (at, dur, lambda: _text_ink(text, size)[2])
    return fn


# ------------------------------------------------------------------ the board and its camera
class Board:
    def __init__(self, entries, prev=None, end=None):
        """entries: this act's drawings in order. prev: the code of the drawing the act starts from
        (the previous act's last one, already drawn)."""
        self.entries = entries
        for i, e in enumerate(entries):
            e.d.layers(e.scale)
            e.start = max(0.0, e.arrive - START_EARLY) if e.arrive > 0 else 0.0
            nxt = entries[i + 1].arrive - PAN if i + 1 < len(entries) else (end or e.arrive + 6)
            e.dur = min(PL.DRAW, max(1.2, 0.6 * (nxt - e.arrive)))
        self.prev, self.end = prev, end
        self._done = {}

    def spot(self, e):
        wx, wy = world(e.code)
        fx = (e.focus[0] - 0.5) * 1500 * e.scale * 0.45
        fy = (e.focus[1] - 0.5) * 880 * e.scale * 0.45
        return wx + e.offset[0], wy + e.offset[1], fx, fy

    def camera(self, t):
        """Rest on a drawing (a slow push towards its focus), then travel to the next at the same
        height above the board: a straight, eased move over the surface, no zooming."""
        es = self.entries
        stops = [(es[0].arrive - PAN if self.prev else -1e9, es[0])]
        stops += [(e.arrive - PAN, e) for e in es[1:]]
        i = 0
        for k, (t0, _) in enumerate(stops):
            if t >= t0:
                i = k
        t0, e = stops[i]
        x1, y1, fx1, fy1 = self.spot(e)
        rest_from = t0 + PAN if (i > 0 or self.prev) else 0.0
        if t >= rest_from:
            nxt = stops[i + 1][0] if i + 1 < len(stops) else (self.end or rest_from + 8)
            k = _ease((t - rest_from) / max(0.5, nxt - rest_from))
            return x1 + fx1 * k, y1 + fy1 * k, ZOOM * (1 + PUSH * k)
        if i == 0:                                           # travelling in from the previous act
            px, py = world(self.prev)
            x0, y0, z0 = px, py, ZOOM
        else:
            px, py, pfx, pfy = self.spot(stops[i - 1][1])
            x0, y0, z0 = px + pfx, py + pfy, ZOOM * (1 + PUSH)
        u = min(1.0, max(0.0, (t - t0) / PAN))
        k = _ease(u)
        pull = min(0.32, math.hypot(x1 - x0, y1 - y0) * DIP)   # longer travels show more of the board
        z = (z0 + (ZOOM - z0) * k) * (1 - pull * math.sin(math.pi * u))
        return x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, z

    def cell(self, e, t, final=False):
        """One drawing's place (a 1920x1080 cell centred on it), as drawn by time t."""
        if final and e.code in self._done:
            return self._done[e.code]
        lt = t - e.start
        c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        lines, _, order = e.d.layers(e.scale)
        x0, y0 = int(W / 2 - lines.width / 2), int(H / 2 - lines.height / 2)
        e.d.box = (x0, y0, lines.width, lines.height)
        PL.draw_layers(c, lines, None, order, lt, 0.0, PL.draw_time(e), x0, y0)
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
            wx, wy = world(code)
            if e is not None:
                wx, wy = wx + e.offset[0], wy + e.offset[1]
            sx, sy = (wx - cx) * z + W / 2, (wy - cy) * z + H / 2
            if sx + W * z / 2 < 0 or sx - W * z / 2 > W or sy + H * z / 2 < 0 or sy - H * z / 2 > H:
                continue
            if e is None:
                c = self._prev_cell()
            else:
                if t < e.start - 0.01:
                    continue
                last = max([e.start + PL.draw_time(e)] + [fn.sound[0] + fn.sound[1] for fn in e.extras if hasattr(fn, 'sound')])
                c = self.cell(e, t, final=t > last + 0.3)
            c = c.resize((max(1, int(W * z)), max(1, int(H * z))), Image.BILINEAR)
            frame.alpha_composite(c, (int(round(sx - c.width / 2)), int(round(sy - c.height / 2))))
        s.mid.alpha_composite(frame)
        for e in self.entries:                 # the pen's scratch, for drawings and for words
            sfx('draw', max(0.0, e.start), W / 2, dur=PL.draw_time(e),
                spans=tuple(tuple(round(v, 4) for v in sp) for sp in getattr(e.d, 'spans', ((0, 1),))[:400]))
            for fn in e.extras:
                if hasattr(fn, 'sound'):
                    at, dur, sp = fn.sound
                    sfx('draw', at, W / 2, dur=dur, spans=tuple(tuple(round(v, 4) for v in x) for x in sp()[:200]))
        return s

    def _prev_cell(self):
        if '_prev' not in self._done:
            e = Entry(self.prev, '', -100.0)
            e.d.layers(e.scale)
            e.start, e.dur = -100.0, PL.DRAW
            self._done['_prev'] = self.cell(e, 0.0)
        return self._done['_prev']
