"""The channel intro, drawn frame by frame: the official logo coloured in by hand.

    frame = intro_frame(t, next_frame, exit='tear' | 'glide')     # numpy RGB, 1920x1080

Choreography (seconds; the sting's chord blooms at RESOLVE):
  0.00  the ground is already alive: the logo's own #2B2A2A, fine paper grain, soft vignette,
        a very slow drift in its texture
  0.15  a pen travels each contour of the logo (the SVG's own paths, letter by letter), an ink
        dot leading it; a small tick as each contour starts
  0.55  marker strokes colour « AX », then « Lab »: diagonal, tapered at both ends, each with its
        own pressure, darker where they overlap, slight overshoot kept inside the letter
  2.86  RESOLVE: the hatching closes into the exact official logo, the logo settles 0.985 -> 1,
        one soft light sweep crosses it once
  3.10  the brand signature (fine rule + square) draws under it
  0.00-RESOLVE  the camera pushes 1.00 -> 1.04, and settles on the resolve
  4.30  exit, either 'tear' (a torn-paper wipe into the film's first frame) or 'glide' (the logo
        glides to the watermark's corner and size over the film's first frame, then fades)
"""
import math
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import vox
from vox import W, H, alpha_mul
import brand as B

RESOLVE = 2.86
EXIT = 4.30
END = 5.0
LOGO_W = 1100
SS = 2                                   # supersampling for the pen line


# ------------------------------------------------------------------ the logo's own contours
def _parse_d(d):
    toks = re.findall(r'[MmLlCcZz]|-?\d*\.?\d+(?:e-?\d+)?', d)
    subs, cur, pos, start, cmd, i = [], [], (0.0, 0.0), (0.0, 0.0), None, 0

    def num():
        nonlocal i
        v = float(toks[i]); i += 1
        return v
    while i < len(toks):
        tk = toks[i]
        if re.match(r'[MmLlCcZz]', tk):
            cmd = tk; i += 1
            if cmd in 'Zz':
                if cur:
                    cur.append(start); subs.append(cur); cur = []
                pos = start
                continue
        if cmd in 'Mm':
            x, y = num(), num()
            pos = (pos[0] + x, pos[1] + y) if cmd == 'm' else (x, y)
            if cur:
                subs.append(cur)
            cur, start = [pos], pos
            cmd = 'l' if cmd == 'm' else 'L'
        elif cmd in 'Ll':
            x, y = num(), num()
            pos = (pos[0] + x, pos[1] + y) if cmd == 'l' else (x, y)
            cur.append(pos)
        elif cmd in 'Cc':
            c = [num() for _ in range(6)]
            if cmd == 'c':
                c = [pos[0] + c[0], pos[1] + c[1], pos[0] + c[2], pos[1] + c[3], pos[0] + c[4], pos[1] + c[5]]
            p0 = pos
            for s in np.linspace(0, 1, 9)[1:]:
                u = 1 - s
                cur.append((u ** 3 * p0[0] + 3 * u * u * s * c[0] + 3 * u * s * s * c[2] + s ** 3 * c[4],
                            u ** 3 * p0[1] + 3 * u * u * s * c[1] + 3 * u * s * s * c[3] + s ** 3 * c[5]))
            pos = (c[4], c[5])
        else:
            i += 1
    if cur:
        subs.append(cur)
    return subs


def _contours(width):
    """[(colour, [polyline in logo-image pixels, ...]), ...] from the official SVG's own paths."""
    svg = open(B.OFFICIAL, encoding='utf-8').read()
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    k = width / vb[2]
    out = []
    for m in re.finditer(r'<g transform="scale\(([\d.]+)\)"><g transform="translate\(([-\d.]+),([-\d.]+)\) scale\(([-\d.]+),([-\d.]+)\)" fill="(#[0-9A-Fa-f]{6})"[^>]*>(.*?)</g></g>', svg, re.S):
        so, tx, ty, sx, sy = (float(m.group(i)) for i in range(1, 6))
        col = tuple(int(m.group(6)[i:i + 2], 16) for i in (1, 3, 5))
        polys = []
        for d in re.findall(r'<path d="([^"]+)"', m.group(7)):
            for sub in _parse_d(d):
                pts = [(((tx + sx * x) * so - vb[0]) * k, ((ty + sy * y) * so - vb[1]) * k) for x, y in sub]
                if len(pts) > 3:
                    polys.append(pts)
        polys.sort(key=lambda p: min(q[0] for q in p))
        out.append((col, polys))
    out.sort(key=lambda g: min(min(q[0] for q in p) for p in g[1]))
    return out


# ------------------------------------------------------------------ built once
_B = {}


def _build():
    if _B:
        return _B
    rng = np.random.default_rng(11)
    gc = B.CFG['intro'].get('ground') or '#2B2A2A'
    ground = np.array([int(gc.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx / W - 0.5) * 1.15) ** 2 + ((yy / H - 0.5) * 1.05) ** 2)
    vign = 1 - 0.38 * np.clip((r - 0.25) / 0.55, 0, 1) ** 1.6
    _B['base'] = ground[None, None, :] * vign[..., None]
    # slow texture: two large noise fields that drift against each other
    def field(seed, sc):
        n = np.random.default_rng(seed).normal(0, 1, (H // sc + 4, W // sc + 4)).astype(np.float32)
        return np.asarray(Image.fromarray(((n * 30) + 128).clip(0, 255).astype(np.uint8)).resize(((W // sc + 4) * sc, (H // sc + 4) * sc), Image.BICUBIC), np.float32) - 128
    _B['m1'], _B['m2'] = field(3, 90), field(4, 140)
    _B['grain'] = [rng.normal(0, 1, (H, W)).astype(np.float32) for _ in range(4)]
    im = B.logo(LOGO_W)
    _B['logo'] = im
    _B['contours'] = _contours(LOGO_W)
    # the colour groups: masks from the official render, strokes per group
    a = np.asarray(im).astype(np.int16)
    alpha = a[..., 3]
    groups = []
    for col, polys in _B['contours']:
        d = np.abs(a[..., :3] - np.array(col)).sum(2)
        m = (alpha > 90) & (d < 120)
        m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 127   # slight overshoot room
        ys, xs = np.where(m)
        ic = B.CFG['intro']
        ang = math.radians(ic.get('stroke_angle', 62))
        dx, dy = math.cos(ang), -math.sin(ang)
        nx, ny = -dy, dx
        proj = xs * nx + ys * ny
        strokes, kk, flip = [], proj.min() - 4, False
        while kk < proj.max() + 4:
            cx, cy = nx * kk, ny * kk
            # the stroke spans only the letter: endpoints from the mask along this line
            on = np.abs(proj - kk) < 2.0
            if on.sum() > 3:
                along = xs[on] * dx + ys[on] * dy
                a0, a1 = along.min() - 6, along.max() + 6
                pts = []
                for f in np.linspace(0, 1, 9):
                    s_ = a0 + (a1 - a0) * f
                    j = rng.normal(0, 1.2)
                    pts.append((cx + dx * s_ + nx * j, cy + dy * s_ + ny * j))
                strokes.append((pts[::-1] if flip else pts, float(rng.uniform(*ic.get('stroke_width', [7, 10]))),
                                float(rng.uniform(0.55, 0.85))))
                flip = not flip
            kk += ic.get('stroke_spacing', 11) * float(rng.uniform(0.85, 1.15))
        groups.append(dict(colour=col, mask=m, strokes=strokes, x0=int(xs.min()), x1=int(xs.max())))
    _B['groups'] = groups
    return _B


def _ease(x):
    x = min(max(x, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def _eo(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def _poly_partial(pts, frac):
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:])]
    total = sum(seg) * frac
    out = [pts[0]]
    for (a, b), l in zip(zip(pts[:-1], pts[1:]), seg):
        if total <= 0 or l == 0:
            break
        f = min(1.0, total / l)
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
        total -= l
    return out


def _ground(t):
    b = _build()
    a = b['base'].copy()
    s1, s2 = int(t * 9) % 90, int(t * 6) % 140                     # the texture drifts very slowly
    m = b['m1'][s1:s1 + H, s1:s1 + W] * 0.028 + b['m2'][s2:s2 + H, :W] * 0.022   # barely there: grounds stay smooth
    g = b['grain'][int(t * 15) % 4] * 1.8
    a += (m + g)[..., None]
    return a


def _logo_layer(t):
    """The logo as it is at time t (RGBA, logo-image size)."""
    b = _build()
    im = b['logo']
    lw, lh = im.size
    if t >= RESOLVE + 0.35:
        return im.copy(), []
    canvas = np.zeros((lh, lw, 4), np.float32)
    tips = []
    # 1. the pen: each contour traced, one after another, letters left to right
    allc = [(col, p) for col, polys in b['contours'] for p in polys]
    per, step = 0.30, 0.11
    pen = Image.new('L', (lw * SS, lh * SS), 0)
    pd = ImageDraw.Draw(pen)
    pen_rgb = np.zeros((lh, lw, 3), np.float32)
    for i, (col, pts) in enumerate(allc):
        st = 0.15 + step * i
        f = (t - st) / per
        if f <= 0:
            continue
        f = _ease(min(f, 1.0))
        part = _poly_partial(pts, f)
        if len(part) > 1:
            single = Image.new('L', (lw * SS, lh * SS), 0)
            ImageDraw.Draw(single).line([(x * SS, y * SS) for x, y in part], fill=235, width=3 * SS, joint='curve')
            sm = np.asarray(single.resize((lw, lh), Image.LANCZOS), np.float32) / 255
            pen_rgb = pen_rgb * (1 - sm[..., None]) + np.array(col, np.float32) * sm[..., None]
            pd.bitmap((0, 0), single, fill=255)
        if f < 1:
            tips.append((part[-1], col))
    pm = np.asarray(pen.resize((lw, lh), Image.LANCZOS), np.float32) / 255
    canvas[..., :3] = pen_rgb
    canvas[..., 3] = pm * 0.9
    # 2. the marker strokes
    n = len(b['groups'])
    span = (RESOLVE - 0.65) / n
    for gi, g in enumerate(b['groups']):
        start = 0.55 + span * gi
        if t <= start:
            continue
        strokes = g['strokes']
        dur_each = 0.11
        per_s = (span * 1.05 - dur_each) / max(len(strokes), 1)
        acc = np.zeros((lh, lw), np.float32)
        for i, (pts, wd, pressure) in enumerate(strokes):
            f = (t - start - i * per_s) / dur_each
            if f <= 0:
                break
            part = _poly_partial(pts, min(1.0, f))
            if len(part) < 2:
                continue
            L = Image.new('L', (lw, lh), 0)
            d = ImageDraw.Draw(L)
            nseg = len(part) - 1
            for k in range(nseg):                                 # tapered: thin at both ends
                u = (k + 0.5) / max(len(pts) - 1, 1)
                taper = 0.45 + 0.55 * math.sin(math.pi * min(1.0, u)) ** 0.6
                d.line([part[k], part[k + 1]], fill=255, width=max(2, int(wd * taper)))
            s = np.asarray(L, np.float32) / 255 * pressure
            acc = 1 - (1 - acc) * (1 - s)                          # overlaps grow darker / denser
        acc *= g['mask']
        col = np.array(g['colour'], np.float32)
        a0 = canvas[..., 3]
        canvas[..., :3] = canvas[..., :3] * (1 - acc[..., None]) + col * acc[..., None]
        canvas[..., 3] = 1 - (1 - a0) * (1 - acc)
        if t < start + span * 1.05:
            tips.append(((g['x0'] + (g['x1'] - g['x0']) * min(1, (t - start) / (span * 1.05)), lh * 0.5), None))
    rgba = np.empty((lh, lw, 4), np.uint8)
    rgba[..., :3] = canvas[..., :3].clip(0, 255).astype(np.uint8)
    rgba[..., 3] = (canvas[..., 3] * 255).clip(0, 255).astype(np.uint8)
    out = Image.fromarray(rgba, 'RGBA')
    # 3. the resolve: the hatching closes into the exact official logo
    r = _ease((t - RESOLVE) / 0.35)
    if r > 0:
        out = Image.blend(out, im, r)
    return out, [tp for tp in tips if tp[1] is not None]


def _sweep(img, t):
    """One soft light sweep across the logo, once, after the resolve; masked by the logo."""
    u = (t - RESOLVE - 0.05) / 0.5
    if not 0 < u < 1:
        return img
    lw, lh = img.size
    x = -lw * 0.2 + lw * 1.4 * _ease(u)
    band = Image.new('L', (lw, lh), 0)
    ImageDraw.Draw(band).polygon([(x - 60, 0), (x + 20, 0), (x - 40 + 0.45 * lh, lh), (x - 120 + 0.45 * lh, lh)], fill=int(95 * math.sin(math.pi * u)))
    band = band.filter(ImageFilter.GaussianBlur(14))
    m = np.minimum(np.asarray(band), np.asarray(img.getchannel('A')))
    light = Image.new('RGBA', (lw, lh), (255, 250, 240, 0))
    light.putalpha(Image.fromarray(m))
    out = img.copy()
    out.alpha_composite(light)
    return out


def _signature_layer(t):
    sg = B.CFG['signature']
    col = _build()['groups'][0]['colour']                         # the logo's own first colour
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    B.signature(lay, W / 2 - (sg['length'] + sg['gap'] + sg['square']) / 2, 0, t, RESOLVE + 0.25, colour=col, dur=0.55)
    return lay


def card(t):
    """The intro card alone at time t (RGB float array)."""
    b = _build()
    g = _ground(t)
    img = Image.fromarray(g.clip(0, 255).astype(np.uint8)).convert('RGBA')
    lg, tips = _logo_layer(t)
    lg = _sweep(lg, t)
    push = 1.0 + 0.04 * _ease(t / RESOLVE)                         # the camera pushes in, settles on the resolve
    settle = 1.0 - 0.015 * math.sin(math.pi * min(1.0, max(0.0, (t - RESOLVE) / 0.4))) if t > RESOLVE else 1.0
    k = push * settle
    lw, lh = lg.size
    tw, th = int(lw * k), int(lh * k)
    lgs = lg.resize((tw, th), Image.LANCZOS)
    ox, oy = (W - tw) / 2, (H - th) / 2 - 20 * k
    img.alpha_composite(lgs, (int(ox), int(oy)))
    d = ImageDraw.Draw(img)
    for (x, y), col in tips:                                        # the ink dot leading each pen line
        X, Y = ox + x * k, oy + y * k
        d.ellipse((X - 4, Y - 4, X + 4, Y + 4), fill=col + (255,))
    sig = _signature_layer(t)
    img.alpha_composite(sig, (0, int(oy + th + 46 * k)))
    return img, (ox, oy, tw, th)


def sounds(t0=0.0, exit_kind='tear'):
    b = _build()
    B._sting('intro', t0)
    allc = [(col, p) for col, polys in b['contours'] for p in polys]
    for i in range(len(allc)):
        B._sound('tick', t0 + 0.15 + 0.11 * i, W / 2 - 400 + 100 * i, 0.4)
    n = len(b['groups'])
    span = (RESOLVE - 0.65) / n
    for gi, g in enumerate(b['groups']):
        for j in range(5):
            B._sound('marker', t0 + 0.55 + span * gi + span * j / 5, W / 2 - LOGO_W / 2 + g['x0'] + (g['x1'] - g['x0']) * j / 5, 0.5)
    B._sound('wipe' if exit_kind == 'tear' else 'whoosh', t0 + EXIT + 0.05, W / 2, 0.35)


def intro_frame(t, next_frame=None, exit_kind='tear'):
    """The intro at time t as a finished frame (numpy RGB). next_frame(): the film's first frame,
    revealed by the exit."""
    sounds(0.0, exit_kind)
    img, (ox, oy, tw, th) = card(min(t, EXIT))
    if t < EXIT or next_frame is None:
        return vox.finish(img)
    nxt = next_frame()
    p = min(1.0, (t - EXIT) / (END - EXIT - 0.05))
    if exit_kind == 'tear':
        import style
        return style._tear(vox.finish(img), nxt, p, 'lr')
    # glide: the logo travels to the watermark's corner and size over the film's first frame, then fades
    wm = B.CFG['watermark']
    base = Image.fromarray(nxt).convert('RGBA')
    ground = Image.fromarray(_ground(EXIT).clip(0, 255).astype(np.uint8)).convert('RGBA')
    base = Image.blend(ground, base, _ease(p / 0.7))
    u = _ease(p / 0.8)
    lg = _build()['logo']
    w0, w1 = tw, wm['width']
    x1, y1 = B._corner_xy(wm['corner'], wm['margin'], 0, w1)
    ww = w0 + (w1 - w0) * u
    hh = lg.height * ww / lg.width
    x = ox + (x1 - ox) * u
    y = oy + (y1 - oy) * u
    op = 1.0 - (1 - wm['opacity']) * u
    op *= 1 - _ease((p - 0.8) / 0.2)
    if op > 0:
        small = lg.resize((max(2, int(ww)), max(2, int(hh))), Image.LANCZOS)
        g = B._ground_lum(Image.fromarray(nxt), (x1, y1, x1 + w1, y1 + w1 * lg.height / lg.width))
        if B._clash(lg, g):                                   # the logo's own plate fades in as it lands on a light ground
            pad = max(6, int(hh * 0.30))
            pc = B.CFG['logo'].get('plate_color') or '#2B2A2A'
            col = tuple(int(pc.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
            pl = Image.new('RGBA', (small.width + 2 * pad, small.height + 2 * pad), (0, 0, 0, 0))
            ImageDraw.Draw(pl).rounded_rectangle((0, 0, pl.width - 1, pl.height - 1), radius=max(3, pad // 3),
                                                 fill=col + (int(255 * B.CFG['logo']['plate_opacity'] * _ease(u)),))
            base.alpha_composite(alpha_mul(pl, op), (int(x - pad), int(y - pad)))
        base.alpha_composite(alpha_mul(small, op), (int(x), int(y)))
    return vox.finish(base)
