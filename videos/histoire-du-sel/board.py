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

    B = Board(entries, before=<previous acts' Entry lists, finished>, end=...)
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

SCALE = 0.80                  # drawings are drawn smaller than the frame, so the board shows around them
ZOOM = 0.80                   # camera framing at rest: wide, so the board and the neighbouring drawings are in view
PUSH = 0.14                   # the camera moves in on the drawing's detail while the pen works
DIP = 1 / 5200                # on a travel the camera pulls back with the distance (an infinite canvas)
PAN = 1.5                     # seconds for a travel to the neighbouring drawing; longer travels take longer
START_EARLY = 0.45            # the pen starts this long before the camera has fully landed

# The board's composition: layout « C », chosen by the user from the compact random boards
# (tools/layout_options.py organic2(42, cols=9, rows=6, sx=1380, sy=880, jx=70, jy=50)): a dense,
# hand-placed wall where every next drawing is a neighbour of the last one, in any direction.
LAYOUT = {
    'M01': (38, -6),
    'G01': (50, 900),
    'G02': (-57, 1808),
    'G03': (1372, 853),
    'G04': (1400, 32),
    'G05': (2799, -31),
    'G06': (4088, -2),
    'G07': (5546, -36),
    'G08': (4102, 897),
    'G09': (2755, 834),
    'G10': (2712, 1778),
    'G33': (1388, 1716),
    'G11': (37, 2669),
    'G12': (-52, 3515),
    'M06': (1426, 2653),
    'G13': (1416, 3505),
    'G14': (-18, 4443),
    'G32': (1446, 4439),
    'G15': (2756, 4369),
    'G16': (2736, 3507),
    'G17': (2794, 2687),
    'G38': (4131, 1793),
    'M04': (5478, 831),
    'G18': (6924, -3),
    'G19': (6909, 906),
    'G20': (5560, 1776),
    'G21': (4168, 2621),
    'G22': (5549, 2668),
    'M07': (4187, 3550),
    'G23': (4124, 4379),
    'G24': (5470, 4361),
    'G25': (5514, 3527),
    'G37': (6860, 4391),
    'G26': (8324, 4367),
    'M05': (6834, 3514),
    'M08': (8303, 3511),
    'C01': (9632, 4413),
    'G27': (11033, 4377),
    'G34': (11079, 3542),
    'G35': (11007, 2687),
    'G28': (9652, 3508),
    'G29': (8288, 2668),
    'G36': (6919, 1765),
    'G30': (6908, 2620),
    'M09': (8251, 1776),
    'G31': (9611, 2660),
}
SIZE = {'M01': 1.035, 'G01': 0.93, 'G02': 0.946, 'G03': 0.927, 'G04': 1.028, 'G05': 1.014, 'G06': 0.756, 'G07': 0.994, 'G08': 0.988, 'G09': 0.997, 'G10': 0.962, 'G33': 0.725, 'G11': 0.974, 'G12': 0.949, 'M06': 1.007, 'G13': 0.988, 'G14': 0.926, 'G32': 1.039, 'G15': 0.987, 'G16': 0.989, 'G17': 0.903, 'G38': 0.681, 'M04': 1.017, 'G18': 0.912, 'G19': 0.974, 'G20': 1.041, 'G21': 0.789, 'G22': 0.94, 'M07': 0.712, 'G23': 0.978, 'G24': 0.903, 'G25': 1.024, 'G37': 1.034, 'G26': 0.983, 'M05': 0.916, 'M08': 0.942, 'C01': 0.999, 'G27': 1.009, 'G34': 0.916, 'G35': 1.037, 'G28': 0.935, 'G29': 0.787, 'G36': 0.956, 'G30': 0.871, 'M09': 1.021, 'G31': 0.948}


def world(code):
    return LAYOUT[code]


def mid(a, b_, dy=0):
    """The point between two drawings (to frame both)."""
    (x0, y0), (x1, y1) = LAYOUT[a], LAYOUT[b_]
    return ((x0 + x1) / 2, (y0 + y1) / 2 + dy)


def frame_of(codes, margin=1.12):
    """Camera centre and zoom that frame these drawings together (for stops showing a group)."""
    xs0, ys0, xs1, ys1 = [], [], [], []
    for c in codes:
        x, y = LAYOUT[c]
        w, h = 1500 * SIZE.get(c, 1.0) * SCALE, 880 * SIZE.get(c, 1.0) * SCALE
        xs0.append(x - w / 2); xs1.append(x + w / 2); ys0.append(y - h / 2); ys1.append(y + h / 2)
    x0, x1, y0, y1 = min(xs0), max(xs1), min(ys0), max(ys1)
    z = min(W / ((x1 - x0) * margin), H / ((y1 - y0) * margin), ZOOM)
    return ((x0 + x1) / 2, (y0 + y1) / 2), max(0.2, z)


def edge(a, b_, inset=0.0):
    """Points on the facing edges of drawings a and b (for a pen line from one to the other)."""
    (ax, ay), (bx, by) = LAYOUT[a], LAYOUT[b_]
    def out(x, y, c, tx, ty):
        w, h = 1500 * SIZE.get(c, 1.0) * SCALE / 2 * (1 - inset), 880 * SIZE.get(c, 1.0) * SCALE / 2 * (1 - inset)
        dx, dy = tx - x, ty - y
        k = min(w / abs(dx) if dx else 1e9, h / abs(dy) if dy else 1e9)
        return (x + dx * k, y + dy * k)
    return out(ax, ay, a, bx, by), out(bx, by, b_, ax, ay)


def extent():
    """Bounding box of everything on the board (for the final view)."""
    xs = [p[0] for p in LAYOUT.values()]
    ys = [p[1] for p in LAYOUT.values()]
    return min(xs) - 800, min(ys) - 500, max(xs) + 800, max(ys) + 500


class Entry:
    def __init__(self, code, label, arrive=None, focus=(0.5, 0.5), extras=(), scale=None, offset=(0, 0),
                 look=False, at=None, zoom=None, stay=False, max_dur=None):
        """A drawing on the board, drawn by the pen as the camera arrives (arrive=None: as soon as the
        travel from the previous stop ends). look=True: a camera stop only, nothing drawn (at= a
        board point, zoom= its framing), e.g. to look back over earlier drawings. stay=True: the
        camera holds where it is (the previous stop frames this drawing too) while the pen draws it."""
        self.look, self.at, self.zoom, self.stay, self.max_dur = look, at, zoom, stay, max_dur
        self.d = None if look else PL.drawing(code, label, backed=False)   # lines only: no fill
        self.code, self.arrive, self.focus, self.extras = code, arrive, focus, list(extras)
        self.scale = (scale or SIZE.get(code, 1.0)) * SCALE
        self.offset = offset


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
    T, spans = PL._order(a, None, step=1, write=True)
    return Image.fromarray(rgba, 'RGBA'), T, spans


def write(text, size, dx, dy, at, dur=None, frac=False, anchor='m'):
    """An extra for an Entry: the pen writes `text` at (dx, dy) from the drawing's centre (or, with
    frac=True, at fractions of the drawing's box), starting at act time `at`. The writing speed is
    the same for every word (about 9 letters a second) unless dur is given."""
    dur = dur or max(0.5, 0.11 * len(text.replace(' ', '')))
    def fn(c, lt, e):
        lines, T, spans = _text_ink(text, size)
        if frac:
            bx, by, bw, bh = e.d.box
            px, py = bx + dx * bw, by + dy * bh
        else:
            px, py = W / 2 + dx, H / 2 + dy
        x0 = int(px - (0 if anchor == 'l' else lines.width / 2))
        y0 = int(py - lines.height / 2)
        PL.draw_layers(c, lines, None, T, lt, at - e.start, dur, x0, y0)
    fn.sound = (at, dur, lambda: _text_ink(text, size)[2])
    return fn


# ------------------------------------------------------------------ the board and its camera
class Board:
    def __init__(self, entries, before=(), end=None, marks=None, before_marks=()):
        """entries: this act's drawings in order. before: the earlier acts' entries (with their
        words), shown finished on the board; the act opens travelling from the last of them.
        marks: pen lines and words placed on the board itself (Line, Note), across drawings."""
        self.entries = entries
        self.before = [b_ for b_ in before if not b_.look]
        prev = self.spot(before[-1]) if before else None
        last_z = None
        for i, e in enumerate(entries):
            if not e.look:
                e.d.layers(e.scale)
            if e.stay and prev is not None:
                e.at, e.zoom = prev, (last_z or ZOOM * (1 + PUSH))
            x, y, fx, fy = self.spot(e)
            last_z = e.zoom if (e.look or e.stay) else (e.zoom or ZOOM) * (1 + PUSH)   # the camera's zoom when this stop ends
            dist = math.hypot(x - prev[0], y - prev[1]) if prev else 0.0
            e.pan = 0.05 if e.stay else PAN + min(2.5, max(0.0, dist - 2000) / 9000)   # long travels take longer
            if e.arrive is None:
                e.arrive = (e.pan + 0.2) if (prev and i == 0) else (entries[i - 1].arrive + 0.1 if i else 0.0)
            e.start = max(0.0, e.arrive - START_EARLY) if e.arrive > 0 else 0.0
            prev = (x + fx, y + fy)
        for i, e in enumerate(entries):
            nxt = entries[i + 1].arrive - entries[i + 1].pan if i + 1 < len(entries) else (end or e.arrive + 6)
            e.dur = 0.0 if e.look else min(e.max_dur or PL.DRAW, max(0.7, 0.6 * (nxt - e.arrive)))
        self.marks, self.before_marks = (marks if marks is not None else []), before_marks          # kept by reference: acts add marks after building the board
        self.prev = self.before[-1].code if self.before else None
        self.end = end
        self._done = {}

    def spot(self, e):
        if e.at is not None:
            return e.at[0], e.at[1], 0.0, 0.0
        wx, wy = world(e.code)
        fx = (e.focus[0] - 0.5) * 1500 * e.scale * 0.45
        fy = (e.focus[1] - 0.5) * 880 * e.scale * 0.45
        return wx + e.offset[0], wy + e.offset[1], fx, fy

    def camera(self, t):
        """Rest on a drawing (a slow push towards its focus), then travel to the next at the same
        height above the board: a straight, eased move over the surface, no zooming."""
        es = self.entries
        stops = [(es[0].arrive - es[0].pan if self.prev else -1e9, es[0])]
        stops += [(e.arrive - e.pan, e) for e in es[1:]]
        i = 0
        for k, (t0, _) in enumerate(stops):
            if t >= t0:
                i = k
        t0, e = stops[i]
        x1, y1, fx1, fy1 = self.spot(e)
        rest_from = t0 + e.pan if (i > 0 or self.prev) else 0.0
        zr = e.zoom or ZOOM
        if t >= rest_from:
            nxt = stops[i + 1][0] if i + 1 < len(stops) else (self.end or rest_from + 8)
            k = _ease((t - rest_from) / max(0.5, nxt - rest_from))
            return x1 + fx1 * k, y1 + fy1 * k, zr * (1 + (0.0 if (e.look or e.stay) else PUSH) * k)
        pe = self.before[-1] if i == 0 else stops[i - 1][1]
        px, py, pfx, pfy = self.spot(pe)
        x0, y0 = px + pfx, py + pfy
        z0 = (pe.zoom or ZOOM) * (1 + (0.0 if (pe.look or pe.stay) else PUSH))
        u = min(1.0, max(0.0, (t - t0) / e.pan))
        k = _ease(u)
        pull = min(0.32, math.hypot(x1 - x0, y1 - y0) * DIP)   # longer travels show more of the board
        if e.look and e.zoom:
            pull = 0.0                                        # a framing stop: zoom straight to it
        z = (z0 + (zr - z0) * k) * (1 - pull * math.sin(math.pi * u))
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
        items = [(None, b_) for b_ in self.before] + [(e, e.code) for e in self.entries if not e.look]
        for e, b_ in items:
            src = e if e is not None else b_
            wx, wy = world(src.code)
            wx, wy = wx + src.offset[0], wy + src.offset[1]
            sx, sy = (wx - cx) * z + W / 2, (wy - cy) * z + H / 2
            if sx + W * z / 2 < 0 or sx - W * z / 2 > W or sy + H * z / 2 < 0 or sy - H * z / 2 > H:
                continue
            if e is None:
                c = self._before_cell(b_)
            else:
                if t < e.start - 0.01:
                    continue
                last = max([e.start + PL.draw_time(e)] + [fn.sound[0] + fn.sound[1] for fn in e.extras if hasattr(fn, 'sound')])
                c = self.cell(e, t, final=t > last + 0.3)
            c = c.resize((max(1, int(W * z)), max(1, int(H * z))), Image.BILINEAR)
            frame.alpha_composite(c, (int(round(sx - c.width / 2)), int(round(sy - c.height / 2))))
        for m in self.before_marks:
            m.draw(frame, 1e6, cx, cy, z)
        for m in self.marks:
            m.draw(frame, t, cx, cy, z)
            m.sound()
        s.mid.alpha_composite(frame)
        for e in self.entries:                 # the pen's scratch, for drawings and for words
            if e.look:
                for fn in e.extras:
                    if hasattr(fn, 'sound'):
                        at, dur, sp = fn.sound
                        sfx('draw', at, W / 2, dur=dur, gate=PL.gate(sp(), dur))
                continue
            sfx('draw', max(0.0, e.start), W / 2, dur=PL.draw_time(e), gate=PL.gate(e.d.spans, PL.draw_time(e)))
            for fn in e.extras:
                if hasattr(fn, 'sound'):
                    at, dur, sp = fn.sound
                    sfx('draw', at, W / 2, dur=dur, gate=PL.gate(sp(), dur))
        return s

    def _before_cell(self, b_):
        """An earlier act's drawing, finished, with its words."""
        key = '_b_' + b_.code
        if key not in self._done:
            self._done[key] = self.cell(b_, 1e6)
        return self._done[key]


# ------------------------------------------------------------------ pen marks on the board itself
def _screen(p, cx, cy, z):
    return ((p[0] - cx) * z + W / 2, (p[1] - cy) * z + H / 2)


class Line:
    """A pen line across the board (board coordinates): dashed or solid, with an arrowhead."""
    def __init__(self, pts, at, dur=0.9, dashed=True, arrow=True, width=5):
        self.pts, self.at, self.dur, self.dashed, self.arrow, self.width = pts, at, dur, dashed, arrow, width

    def draw(self, frame, t, cx, cy, z):
        import annotate as A
        if t < self.at:
            return
        A.connect(frame, [_screen(p, cx, cy, z) for p in self.pts], t, self.at, dur=self.dur,
                  dashed=self.dashed, dots=False, width=max(2, self.width * z / ZOOM), sound=False,
                  colour=S.PAL.ink, arrowhead=self.arrow)

    def sound(self):
        sfx('draw', self.at, W / 2, dur=self.dur, gate=PL.gate(((0.0, 1.0),), self.dur))


class Note:
    """Words handwritten by the pen on the board itself (board coordinates of their centre, or of
    their left end with anchor='l')."""
    def __init__(self, text, size, xy, at, dur=None, anchor='m'):
        self.text, self.size, self.xy, self.at, self.anchor = text, size, xy, at, anchor
        self.dur = dur or max(0.5, 0.11 * len(text.replace(' ', '')))

    def draw(self, frame, t, cx, cy, z):
        if t < self.at:
            return
        lines, T, _ = _text_ink(self.text, self.size)
        tile = Image.new('RGBA', lines.size, (0, 0, 0, 0))
        PL.draw_layers(tile, lines, None, T, t, self.at, self.dur, 0, 0)
        tile = tile.resize((max(1, int(tile.width * z)), max(1, int(tile.height * z))), Image.BILINEAR)
        sx, sy = _screen(self.xy, cx, cy, z)
        x0 = sx - (0 if self.anchor == 'l' else tile.width / 2)
        if -tile.width < x0 < W and -tile.height < sy < H + tile.height:
            frame.alpha_composite(tile, (int(x0), int(sy - tile.height / 2)))

    def sound(self):
        sfx('draw', self.at, W / 2, dur=self.dur, gate=PL.gate(_text_ink(self.text, self.size)[2], self.dur))


def final_view():
    """The closing stop: the whole board in view."""
    x0, y0, x1, y1 = extent()
    z = min(W / (x1 - x0), H / (y1 - y0))
    return Entry('END', 'tout le tableau', look=True, at=((x0 + x1) / 2, (y0 + y1) / 2), zoom=z)
