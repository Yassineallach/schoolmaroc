"""The film's one picture system (the user's notes: « the artwork animation must be consistent », then
the ink-sketch style of their goat reference).

Every picture is a ChatGPT drawing in one black ink-sketch style, a single subject on white
(PROMPTS.md). Each is shown the same way: its lines in the film's ink (cutout.ink_image) are DRAWN onto the same
parchment (the astrolabe theme) stroke by stroke, as if a pen were tracing them (the user's request:
« make every scene like it's being drawn »), then its white fill settles in under the lines; the
same slow camera push runs over every shot, and every cut is the same torn wipe.

How the drawing order is made: the ink lines are split into connected strokes; every stroke grows
from its own starting point along its own line (geodesic distance inside the ink), and the strokes
are drawn one after another in a sweep across the drawing, with overlap. The order is computed once
per drawing and cached in out/_drawon.
"""
import os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from vox import W, H, F_HEAD, asset
import presets as P
import scenes as S
import cutout
from style import ENTER, sfx

BOX = (1500, 880)         # every drawing fits the same box
DRAW = 3.0                # the pen takes this long on every shot (less on very short shots)
PUSH = (1.0, 1.05)        # same slow push on every shot


def _placeholder(label):
    im = Image.new('RGB', (1500, 880), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 1480, 860), radius=30, outline=(0, 0, 0), width=8)
    d.text((750, 440), label, font=F_HEAD(56), fill=(0, 0, 0), anchor='mm')
    return im


class Drawing:
    def __init__(self, code, label, backed=True):
        self.code, self.label, self.backed = code, label, backed
        self.path = next((asset(code + e) for e in ('.png', '.jpg') if os.path.exists(asset(code + e))), None)

    @lru_cache(maxsize=2)
    def ink(self, scale=1.0):
        if self.path:
            src = Image.open(self.path)
            if src.mode == 'RGBA':                      # transparent PNG: put it on white first
                bg = Image.new('RGB', src.size, (255, 255, 255)); bg.paste(src, (0, 0), src); src = bg
            src = src.convert('RGB')
        else:
            src = _placeholder(f'{self.code} · {self.label}')
        k = min(BOX[0] * scale / src.width, BOX[1] * scale / src.height)
        return cutout.ink_image(src, int(src.width * k), backed=self.backed)

    @lru_cache(maxsize=2)
    def layers(self, scale=1.0):
        """(lines, fill, order): the ink lines alone, the paper fill alone (None if unbacked), and
        for every pixel the moment (0..1) its line is drawn."""
        full = self.ink(scale)
        if self.backed:
            src = Drawing(self.code, self.label, backed=False)
            lines = src.ink(scale)
        else:
            lines = full
        la = np.asarray(lines)[..., 3]
        fill = None
        if self.backed:
            fa = np.asarray(full).astype(np.float32)
            fa[..., 3] = np.clip(fa[..., 3] - la, 0, 255)
            fill = Image.fromarray(fa.astype(np.uint8), 'RGBA')
        T, spans = _order(la, f'{self.code}_{lines.width}' if self.path else None)
        self.spans = spans
        return lines, fill, T


def _order(alpha, key, step=2):
    """Draw-on time (0..1) for every pixel, and the pen-down spans, for ONE pen: the ink is thinned
    to its centre lines, the pen follows them one line at a time (depth-first along each line,
    lifting at branch ends), and goes on to the nearest unfinished line, so only one place is ever
    being drawn. Every ink pixel takes the time of the nearest centre-line point."""
    from skimage.morphology import skeletonize
    cache = os.path.join(asset('..'), 'out', '_drawon', f'{key}.npz') if key else None
    if cache and os.path.exists(cache):
        z = np.load(cache)
        return z['T'], [tuple(x) for x in z['spans']]
    h, w = alpha.shape
    ink = alpha[::step, ::step] > 40
    sk = skeletonize(ink)
    ys, xs = np.nonzero(sk)
    N = len(ys)
    if N == 0:
        return np.zeros((h, w), np.float32), [(0.0, 1.0)]
    idx = -np.ones(sk.shape, np.int64); idx[ys, xs] = np.arange(N)
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    deg = np.zeros(N, np.int32)
    for dy, dx in nb:
        yy, xx = ys + dy, xs + dx
        ok = (yy >= 0) & (yy < sk.shape[0]) & (xx >= 0) & (xx < sk.shape[1])
        deg[ok] += (idx[yy[ok], xx[ok]] >= 0)
    seen = np.zeros(N, bool)
    tim = np.zeros(N, np.float64)
    clock, pen = 0.0, (0.0, 0.0)
    spans, down = [], None
    left = N
    while left:
        cand = np.nonzero(~seen)[0]
        d2 = (ys[cand] - pen[0]) ** 2 + (xs[cand] - pen[1]) ** 2 - 4000.0 * (deg[cand] <= 1)   # prefer line ends
        s0 = int(cand[np.argmin(d2)])
        clock += 6 + 0.15 * np.hypot(ys[s0] - pen[0], xs[s0] - pen[1])   # the pen lifts and travels
        stack, prev = [s0], None
        while stack:
            i = stack.pop()
            if seen[i]:
                continue
            if prev is not None and max(abs(ys[i] - ys[prev]), abs(xs[i] - xs[prev])) > 1:
                if down is not None:
                    spans.append((down, clock)); down = None
                clock += 4                                     # back to the branch point
            if down is None:
                down = clock
            seen[i] = True; left -= 1
            clock += 1
            tim[i] = clock
            prev = i
            for dy, dx in nb:
                yy, xx = ys[i] + dy, xs[i] + dx
                if 0 <= yy < sk.shape[0] and 0 <= xx < sk.shape[1]:
                    j = idx[yy, xx]
                    if j >= 0 and not seen[j]:
                        stack.append(j)
        if down is not None:
            spans.append((down, clock)); down = None
        pen = (ys[prev], xs[prev])
    tim /= clock
    spans = [(a / clock, b / clock) for a, b in spans]
    grid = np.ones(sk.shape, np.float64)
    grid[ys, xs] = tim
    _, (iy, ix) = ndimage.distance_transform_edt(~sk, return_indices=True)
    T = grid[iy, ix].astype(np.float32)
    T = np.kron(T, np.ones((step, step), np.float32))[:h, :w]
    # merge tiny spans so the sound follows strokes, not single pixels
    merged = []
    for s_, e_ in spans:
        if merged and s_ - merged[-1][1] < 0.004:
            merged[-1] = (merged[-1][0], e_)
        else:
            merged.append((s_, e_))
    if cache:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        np.savez(cache, T=T, spans=np.array(merged))
    return T, merged


def drawing(code, label, backed=True):
    """backed=False for open line drawings (neurons) where filling the silhouette closes gaps."""
    return Drawing(code, label, backed)


def plate(s, d, t, start=ENTER, focus_to=(0.5, 0.5), scale=1.0, cx=W / 2, cy=H / 2 + 10):
    """The drawing on the parchment, revealed and pushed the same way in every shot."""
    S.env(s, 'theme')
    im = d.ink(scale)
    fx = cx - im.width / 2 + focus_to[0] * im.width
    fy = cy - im.height / 2 + focus_to[1] * im.height
    d.box = (cx - im.width / 2, cy - im.height / 2, im.width, im.height)   # where it sits, for marks
    s.camera(PUSH[0], PUSH[1], (W / 2, H / 2), (fx, fy))
    draw_on(s, d, t, start, scale, cx, cy)


def draw_on(s, d, t, start, scale, cx, cy):
    """The pen draws the lines (DRAW s), then the white fill settles in under them (0.5 s)."""
    lines, fill, order = d.layers(scale)
    dur = min(DRAW, max(1.2, 0.55 * s.D))
    if t < start:
        return
    # the pen's scratch, following its strokes (silent while it lifts between lines)
    sfx('draw', max(0.0, start), cx, dur=dur, spans=tuple(tuple(round(v, 4) for v in sp) for sp in d.spans[:400]))
    p = (t - start) / dur
    x0, y0 = int(cx - lines.width / 2), int(cy - lines.height / 2)
    if fill is not None and p > 0.85:
        k = min(1.0, (p - 0.85) / (0.5 / dur + 0.15))
        fa = np.asarray(fill).copy()
        fa[..., 3] = (fa[..., 3] * k).astype(np.uint8)
        s.mid.alpha_composite(Image.fromarray(fa, 'RGBA'), (x0, y0))
    if p >= 1.0:
        s.mid.alpha_composite(lines, (x0, y0))
        return
    la = np.asarray(lines).copy()
    edge = np.clip((p - order) / 0.004, 0, 1)                      # a crisp pen tip on the growing line
    la[..., 3] = (la[..., 3] * edge).astype(np.uint8)
    s.mid.alpha_composite(Image.fromarray(la, 'RGBA'), (x0, y0))


def cuts(shots):
    """Same torn wipe on every cut, alternating direction."""
    return [sh if i == 0 else (sh[0], sh[1], 'lr' if i % 2 else 'rl') for i, sh in enumerate(shots)]


def at(d, fx, fy):
    """Screen point of a spot in the drawing, given as fractions of its width and height."""
    x0, y0, w, h = d.box
    return (x0 + fx * w, y0 + fy * h)


def rect(d, f0x, f0y, f1x, f1y):
    a, b = at(d, f0x, f0y), at(d, f1x, f1y)
    return (a[0], a[1], b[0], b[1])


# ---- the drawing sound: a pen scratching on paper, only while the pen is down
import sfx as _sfx


def _s_draw(r, p):
    L = p.get('dur', 3.0)
    n = _sfx._sec(L)
    t = np.arange(n) / _sfx.SR
    gate = np.zeros(n)
    for a, b in p.get('spans', ((0, 1),)):
        gate[int(a * n):int(b * n)] = 1.0
    k = int(0.012 * _sfx.SR)                                   # soft pen landings and lifts
    gate = np.convolve(gate, np.ones(k) / k, mode='same')
    wob = 0.75 + 0.25 * np.sin(2 * np.pi * (7 + 3 * r.random()) * t + r.random() * 6)   # the hand's rhythm
    grain = _sfx._crackle(r, n, 2600, 1500, 7000)
    hiss = _sfx._band(r.normal(0, 1, n), 2200, 6500) * 0.55
    body = _sfx._band(r.normal(0, 1, n), 400, 1400) * 0.25    # the nib dragging on the fibres
    return 0.0, _sfx._norm((grain + hiss + body) * gate * wob, 0.22)


_sfx.DESIGNS['draw'] = _s_draw
