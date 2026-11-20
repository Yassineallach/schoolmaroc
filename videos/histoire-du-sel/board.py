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

# The board's composition (board pixels, centre of each drawing): three rows, so that the closing
# view of the whole board reads as one picture.
#   middle row, left to right: act 1 (the goats, then the NaCl triangle) and act 2 (farming, then the
#     three methods with the world map above and the buried-sea section below the miners);
#   bottom row, right to left: act 3 then act 4, coming back under the first two acts;
#   top row: act 5, the industrial age, mirrored above act 2's three methods (pans -> modern pond,
#     brine pans -> evaporator, miners -> dynamite); the last goat comes home above the first goats.
LAYOUT = {
    'M01': (0, 0), 'G01': (1400, 0), 'G02': (2800, 0), 'G03': (4200, 0), 'G04': (5600, 0), 'G05': (7000, 0),
    'G06': (9200, -500), 'G07': (8550, 560), 'G08': (9950, 560),                       # the NaCl triangle
    'G09': (11600, 0), 'G33': (13000, -880), 'G10': (13000, 0), 'G11': (14400, 0),     # timeline under this row
    'G12': (15800, 0), 'M06': (17200, -900), 'G13': (18600, 0), 'G14': (20000, 0), 'G32': (20000, 980),
    # act 3, right to left
    'G15': (24300, 2700), 'G16': (22900, 2700), 'G17': (21500, 2700), 'G38': (20100, 2700),
    'M04': (18600, 2700), 'G18': (17200, 3120), 'G19': (15800, 3120), 'G20': (14300, 2700),
    # act 4, right to left
    'G21': (12900, 2700), 'G22': (11500, 2700), 'G23': (10100, 2700), 'M07': (9450, 1820), 'G24': (8800, 2700),
    'G25': (7300, 2700), 'G37': (7300, 3680), 'G26': (5900, 3680), 'M05': (5900, 2700), 'M08': (4500, 3260),
    # act 5, above act 2
    'C01': (11600, -2400), 'G27': (13000, -2400), 'G34': (15800, -2400), 'G35': (18600, -2400), 'G28': (20000, -2400),
    'G29': (21500, -2400), 'G36': (22900, -2400), 'G30': (24300, -2400), 'M09': (25700, -2400),
    'G31': (1400, -1250),
}
# size hierarchy: maps a little larger, small objects smaller
SIZE = {'M01': 1.0, 'M04': 1.0, 'M05': 1.0, 'M06': 1.1, 'G21': 0.8, 'G29': 0.8, 'G30': 0.85, 'G06': 0.75,
        'M07': 0.75, 'M08': 1.0, 'G33': 0.8, 'G38': 0.7}


def world(code):
    return LAYOUT[code]


def mid(a, b_, dy=0):
    """The point between two drawings (to frame both)."""
    (x0, y0), (x1, y1) = LAYOUT[a], LAYOUT[b_]
    return ((x0 + x1) / 2, (y0 + y1) / 2 + dy)


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
