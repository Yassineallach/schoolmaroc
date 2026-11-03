"""Editorial scene transitions, used by style.make_frame alongside the original torn wipes.

In SHOTS, the third item names the cut:  (start, scene, 'circle')  or  (start, scene, ('zoom', {'at': (x, y)}))

  'lr' / 'rl'   torn-paper wipe (style.py, unchanged)          'up'  new sheet laid over (unchanged)
  'pageturn'    the old scene turns away like a page, hinged on the left, revealing the new one
  'circle'      the new scene opens through a growing circle with a terracotta rim  {'at': (x, y)}
  'shape'       a textured terracotta band sweeps diagonally, carrying the new scene behind it
  'zoom'        the camera dives into a point of the old scene and comes out in the new  {'at': (x, y)}
  'collage'     the new scene arrives as torn paper strips dropping in one after another

Pick the cut from the story: a turn of chapter -> pageturn; zooming into a place or a detail ->
zoom or circle; a change of subject -> shape; a montage or a list -> collage; ordinary cuts ->
the torn wipes. Never use the same special cut twice in a row.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
TERRA = (205, 88, 48)
PAPER_BACK = (236, 226, 206)

# seconds before / after the cut that each transition occupies
DUR = {'pageturn': (0.55, 0.35), 'circle': (0.40, 0.22), 'shape': (0.42, 0.22), 'zoom': (0.50, 0.30), 'collage': (0.55, 0.40)}
SOUND = {'pageturn': 'pageflip', 'circle': 'whoosh', 'shape': 'whoosh', 'zoom': 'whoosh', 'collage': 'drop'}

_YY, _XX = np.mgrid[0:H, 0:W].astype(np.float32)


def _eio(x):
    x = min(max(x, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def _shadow_edge(out, d, width=40, strength=0.25):
    """Darken pixels just outside an edge (d > 0 inside the new region)."""
    sh = (d <= 0) & (d > -width)
    out[sh] *= (1 - strength + strength * (-d[sh] / width))[:, None]


def pageturn(a, b, p, opts):
    import presets as P
    u = _eio(p)
    ang = math.pi * u
    out = b.astype(np.float32)
    xf = W * math.cos(ang)                         # far edge of the turning page, hinge at x = 0
    out[:, :int(min(W, 90 + 260 * math.sin(ang)))] *= 0.86 + 0.14 * np.linspace(0, 1, int(min(W, 90 + 260 * math.sin(ang))))[None, :, None]
    img = Image.fromarray(out.clip(0, 255).astype(np.uint8)).convert('RGBA')
    e = 0.10 * H * math.sin(ang)
    if math.cos(ang) > 0.01:
        page = Image.fromarray(a).convert('RGBA')
        quad = [(0, 0), (xf, -e), (xf, H + e), (0, H)]
        P.put_quad(img, page, quad, lift=0.5 * math.sin(ang), op=1.0, darken=0.35 * math.sin(ang) ** 2)
    elif math.cos(ang) < -0.01:
        back = Image.new('RGBA', (W, H), PAPER_BACK + (255,))
        quad = [(xf, -e), (0, 0), (0, H), (xf, H + e)]
        P.put_quad(img, back, quad, lift=0.5 * math.sin(ang), op=1.0, darken=0.2 * math.sin(ang) ** 2)
    return np.asarray(img.convert('RGB'))


def circle(a, b, p, opts):
    cx, cy = opts.get('at', (W / 2, H / 2))
    rmax = math.hypot(max(cx, W - cx), max(cy, H - cy)) + 20
    r = rmax * _eio(p) ** 1.3
    d = r - np.sqrt((_XX - cx) ** 2 + (_YY - cy) ** 2)
    out = a.astype(np.float32)
    inside = d > 0
    out[inside] = b[inside]
    rim = (d > 0) & (d < 9)
    out[rim] = out[rim] * 0.15 + np.array(TERRA, np.float32) * 0.85
    _shadow_edge(out, d, 30, 0.22)
    return out.clip(0, 255).astype(np.uint8)


_tex = None


def shape(a, b, p, opts):
    global _tex
    if _tex is None:
        r = np.random.default_rng(3)
        _tex = (r.normal(0, 1, (H, W)) * 6).astype(np.float32)
    band = opts.get('band', 220)
    u = _eio(p)
    diag = (_XX + _YY * 0.55)
    span = W + H * 0.55 + band * 2
    e = -band + span * u                              # leading edge of the band
    out = a.astype(np.float32)
    behind = diag < e - band
    out[behind] = b[behind]
    inband = (diag >= e - band) & (diag < e)
    col = np.array(TERRA, np.float32)[None, :] + _tex[inband][:, None]
    out[inband] = col
    for edge in (e, e - band):                        # thin ink rules on both edges of the band
        rule = np.abs(diag - edge) < 1.6
        out[rule] = out[rule] * 0.3 + np.array((60, 40, 30), np.float32) * 0.7
    return out.clip(0, 255).astype(np.uint8)


def zoom(a, b, p, opts):
    cx, cy = opts.get('at', (W / 2, H / 2))
    u = _eio(p)
    s1 = 1 + 1.8 * u ** 2                              # dive into the old scene
    A = Image.fromarray(a)
    A = A.transform((W, H), Image.AFFINE, (1 / s1, 0, cx - cx / s1, 0, 1 / s1, cy - cy / s1), Image.BILINEAR)
    s2 = 1.15 - 0.15 * u                               # the new scene settles from slightly close
    B = Image.fromarray(b).transform((W, H), Image.AFFINE, (1 / s2, 0, W / 2 - W / 2 / s2, 0, 1 / s2, H / 2 - H / 2 / s2), Image.BILINEAR)
    k = _eio((p - 0.45) / 0.4)
    blur = 6 * math.sin(math.pi * min(1.0, p))
    out = Image.blend(A, B, k)
    if blur > 0.6:
        out = out.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(out)


_strips = None


def collage(a, b, p, opts):
    import presets as P
    global _strips
    n = opts.get('pieces', 5)
    if _strips is None or len(_strips) != n:
        r = np.random.default_rng(11)
        xs = np.linspace(0, W, n + 1)
        _strips = []
        for i in range(n):
            x0, x1 = xs[i] - 14, xs[i + 1] + 14
            pts = [(x0 + r.uniform(-8, 8), y) for y in range(-20, H + 40, 40)] + [(x1 + r.uniform(-8, 8), y) for y in range(H + 40, -20, -40)]
            m = Image.new('L', (W, H), 0)
            ImageDraw.Draw(m).polygon(pts, fill=255)
            _strips.append((m, r.uniform(-5, 5), r.choice([-1, 1])))
    if p >= 0.999:
        return b
    img = Image.fromarray(a).convert('RGBA')
    B = Image.fromarray(b).convert('RGBA')
    order = [2, 0, 4, 1, 3][:n] if n == 5 else list(range(n))
    for k, i in enumerate(order):
        m, rot, sgn = _strips[i]
        u = (p - k * 0.12) / 0.5
        if u <= 0:
            continue
        q = P.damped(min(u, 1.0), zeta=0.55, cycles=1.2)
        piece = B.copy()
        piece.putalpha(m)
        bb = m.getbbox()
        piece = piece.crop(bb)
        ang = rot * (1 - q)
        sc = 1 + 0.12 * (1 - q)
        item = P.rot_scale(piece, ang, sc)
        cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2 - 260 * (1 - q) * sgn
        P.put(img, item, cx, cy, lift=0.6 * (1 - q), op=min(1.0, u * 4))
    return np.asarray(img.convert('RGB'))


KINDS = {'pageturn': pageturn, 'circle': circle, 'shape': shape, 'zoom': zoom, 'collage': collage}


def apply(kind, a, b, p, opts=None):
    return KINDS[kind](a, b, p, opts or {})
