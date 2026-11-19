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
        return lines, fill, _order(la, f'{self.code}_{lines.width}' if self.path else None)


def _order(alpha, key, step=2):
    """Draw-on time (0..1) for every pixel: strokes in a sweep, each growing along its own line."""
    cache = os.path.join(asset('..'), 'out', '_drawon', f'{key}.npy') if key else None
    if cache and os.path.exists(cache):
        return np.load(cache)
    h, w = alpha.shape
    ink = alpha[::step, ::step] > 40
    ink = ndimage.binary_dilation(ink, iterations=1)                 # close hairline gaps in a stroke
    lab, n = ndimage.label(ink, structure=np.ones((3, 3)))
    if n == 0:
        return np.zeros((h, w), np.float32)
    ys, xs = np.nonzero(lab)
    ids = lab[ys, xs]
    # each stroke starts at its upper-left-most point (smallest x + y)
    key_ = xs + ys
    start = np.full(n + 1, np.iinfo(np.int64).max); np.minimum.at(start, ids, key_)
    seed = np.zeros_like(ink)
    seed[ys[key_ == start[ids]], xs[key_ == start[ids]]] = True
    # geodesic distance from the seed, inside the ink (iterative dilation)
    dist = np.full(ink.shape, -1, np.int32); dist[seed] = 0
    front, d, st = seed.copy(), 0, np.ones((3, 3), bool)
    while front.any() and d < 6000:
        d += 1
        nxt = ndimage.binary_dilation(front, structure=st) & ink & (dist < 0)
        dist[nxt] = d
        front = nxt
    dist[dist < 0] = 0
    dmax = np.zeros(n + 1); np.maximum.at(dmax, ids, dist[ys, xs])
    size = np.bincount(ids, minlength=n + 1).astype(float)
    # strokes in a sweep: by the stroke's centre, left to right with a little top-to-bottom
    cx = np.bincount(ids, weights=xs, minlength=n + 1) / np.maximum(size, 1)
    cy = np.bincount(ids, weights=ys, minlength=n + 1) / np.maximum(size, 1)
    sweep = (cx / ink.shape[1]) * 0.75 + (cy / ink.shape[0]) * 0.25
    # contours first, then shading: long strokes (outlines) are drawn in the first 70 % of the
    # time, each growing along its own length; short strokes (hatching, fur) fill in after them
    big = dmax >= max(25, 0.12 * dmax.max())
    rel = np.clip(dmax / max(dmax.max(), 1), 0, 1)
    t0 = np.where(big, sweep * 0.30, 0.55 + sweep * 0.38)
    dur = np.where(big, 0.25 + 0.40 * rel, 0.07)
    local = dist[ys, xs] / np.maximum(dmax[ids], 1)
    T = np.ones(ink.shape, np.float32)
    T[ys, xs] = t0[ids] + dur[ids] * local
    T = T / max(T[ys, xs].max(), 1e-6)
    T = np.kron(T, np.ones((step, step), np.float32))[:h, :w]
    T = ndimage.grey_erosion(T, size=(3, 3))                       # cover the antialiased line edges
    if cache:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        np.save(cache, T.astype(np.float32))
    return T.astype(np.float32)


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
    if not getattr(s, '_pencil', False):
        sfx('pencil', max(0.0, start), cx, dur=dur)
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
    edge = np.clip((p - order) / 0.015, 0, 1)                      # a soft pen tip on the growing line
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
