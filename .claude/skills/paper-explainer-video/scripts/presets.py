"""Physical scrapbook animation presets (1920x1080).

Every preset draws onto a layer (a Shot's .mid or .top) at time t for an element whose action
starts at `start`. Items are plain RGBA images, so the same preset works for photographs,
transparent PNG cut-outs, SVGs (load()) and text (text_item()).

  1  page_flip      a page turning on its hinge, back of the page shown mid-turn
  2  drop           a print falling onto the desk: lift, spin, overshoot, settle
  3  unfold         a tri-folded document opening panel by panel
  4  clipping       newspaper clipping generator (use with slide)
  5  tear_reveal    a paper cover ripped in two, revealing the image beneath
  6  stack          prints landing on a pile, earlier prints nudged by each impact
  7  stamp_hit      a rubber stamp descending, hitting, inking (pass the Shot for the kick)
  8  mask_reveal    an image revealed through a growing torn hole in the page
  9  slide          a document pushed across the desk with friction and rotation lag
  10 assemble       a cut-out flying together from irregular paper pieces
  11 flip           a print flipping over to reveal a second photograph
  12 Shot.zoom_to   (style.py) the camera travelling from the composition into one image
"""
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import vox
from vox import INK, RED, CREAM, F_HEAD, F_SERIF, F_BODY, F_TYPE, torn_mask, lerp
from style import sfx

from palette import ACTIVE as PAL
PAPER_BACK = PAL.paper2
SHADOW = (40, 26, 14)


# ------------------------------------------------------------------ timing curves
def clamp01(x):
    return min(max(x, 0.0), 1.0)


def ease_io(x):
    x = clamp01(x)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def ease_out(x, p=3):
    return 1 - (1 - clamp01(x)) ** p


def damped(u, zeta=0.55, cycles=1.6):
    """Spring response 0->1 over u in [0,1]: overshoot, then settle. zeta sets the overshoot."""
    if u <= 0:
        return 0.0
    if u >= 1:
        return 1.0
    w = cycles * 2 * math.pi
    wd = w * math.sqrt(1 - zeta ** 2)
    e = math.exp(-zeta * w * u)
    return 1 - e * (math.cos(wd * u) + zeta * w / wd * math.sin(wd * u))


# ------------------------------------------------------------------ items
def load(path, width=None, height=None):
    """PNG / JPG / SVG -> RGBA."""
    if str(path).lower().endswith('.svg'):
        import cairosvg, io
        png = cairosvg.svg2png(url=str(path), output_width=width, output_height=height)
        return Image.open(io.BytesIO(png)).convert('RGBA')
    img = Image.open(path).convert('RGBA')
    if width:
        img = vox.fit_w(img, width)
    elif height:
        img = vox.fit_h(img, height)
    return img


def print_card(img, width, border=16, seed=1):
    """A photograph as a torn-edged print with a light border, treated in the identity's way
    (palette.treat: sepia duotone for history, cold for crime, ink for manga...)."""
    import palette
    src = vox.fit_w(palette.treat(img.convert('RGB')), width - 2 * border)
    card = Image.new('RGBA', (src.width + 2 * border, src.height + 2 * border), CREAM + (255,))
    card.paste(src, (border, border))
    card.putalpha(torn_mask(card.width, card.height, seed))
    return card


def text_item(s, size, font=F_HEAD, fill=INK, pad=10):
    f = font(size)
    d = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    l, t_, r, b = d.textbbox((0, 0), s, font=f)
    im = Image.new('RGBA', (r - l + 2 * pad, b - t_ + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - l, pad - t_), s, font=f, fill=fill + (255,))
    return im


def paper_card(w, h, seed=3, colour=PAL.cream, text=None, size=60):
    im = Image.new('RGBA', (w, h), colour + (255,))
    a = np.asarray(im).astype(np.float32)
    a[..., :3] += np.random.default_rng(seed).normal(0, 3, (h, w, 1))
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    if text:
        ImageDraw.Draw(im).text((w / 2, h / 2), text, font=F_HEAD(size), fill=INK + (255,), anchor='mm')
    im.putalpha(torn_mask(w, h, seed, amp=5, step=12))
    return im


def clipping(headline, lines=('---',) * 9, w=620, h=560, seed=7, date=None):
    """A newspaper clipping: newsprint, a serif headline, ruled columns, torn edges.
    Only put words on it that the narration supports."""
    r = np.random.default_rng(seed)
    base = np.empty((h, w, 3), np.float32)
    base[:] = (232, 226, 210)
    base += r.normal(0, 4, (h, w, 1))
    im = Image.fromarray(base.clip(0, 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(im)
    y = 34
    if date:
        d.text((w / 2, y), date.upper(), font=F_TYPE(22), fill=PAL.ink2 + (255,), anchor='mm')
        y += 26
        d.line((30, y, w - 30, y), fill=(60, 56, 50, 255), width=2)
        y += 18
    f = F_SERIF(54)
    words, row = headline.split(), ''
    for word in words:  # wrap the headline
        test = (row + ' ' + word).strip()
        if d.textlength(test, font=f) > w - 70 and row:
            d.text((w / 2, y + 30), row, font=f, fill=PAL.ink + (255,), anchor='mm')
            y += 62
            row = word
        else:
            row = test
    d.text((w / 2, y + 30), row, font=f, fill=PAL.ink + (255,), anchor='mm')
    y += 84
    col = (w - 90) // 2
    for c in range(2):
        x0 = 35 + c * (col + 20)
        yy = y
        while yy < h - 40:
            d.line((x0, yy, x0 + col * r.uniform(0.75, 1.0), yy), fill=(120, 114, 104, 255), width=4)
            yy += 19
    im.putalpha(torn_mask(w, h, seed, amp=9, step=10))
    return im


# ------------------------------------------------------------------ drawing helpers
def comp(layer, im, x, y):
    """alpha_composite that tolerates negative / off-canvas positions."""
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(0, -x), max(0, -y)
    x1, y1 = min(im.width, layer.width - x), min(im.height, layer.height - y)
    if x1 <= x0 or y1 <= y0:
        return
    if (x0, y0, x1, y1) != (0, 0, im.width, im.height):
        im = im.crop((x0, y0, x1, y1))
    layer.alpha_composite(im, (x + x0, y + y0))


def fade_img(im, k):
    return vox.alpha_mul(im, clamp01(k))


def shade(im, k, tint=(0, 0, 0)):
    """Darken an RGBA image by k (0..1) - light falling off a turning page."""
    if k <= 0.01:
        return im
    a = np.asarray(im).astype(np.float32)
    a[..., :3] = a[..., :3] * (1 - k) + np.array(tint, np.float32) * k
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


def soft_shadow(im, lift=0.0, opacity=0.30):
    """Shadow of an item `lift` above the page: higher = larger, softer, fainter."""
    r = 5 + 26 * lift
    pad = int(r * 2.6) + 6
    q = 4
    a = im.getchannel('A').resize((max(1, im.width // q), max(1, im.height // q)), Image.BILINEAR)
    small = Image.new('L', ((im.width + 2 * pad) // q + 1, (im.height + 2 * pad) // q + 1), 0)
    small.paste(a, (pad // q, pad // q))
    small = small.filter(ImageFilter.GaussianBlur(r / q)).resize((im.width + 2 * pad, im.height + 2 * pad), Image.BILINEAR)
    k = opacity * (1 - 0.45 * lift)
    sh = Image.new('RGBA', small.size, SHADOW + (0,))
    sh.putalpha(small.point(lambda v: int(v * k)))
    return sh, pad


def put(layer, im, cx, cy, lift=0.0, op=1.0, shadow=True, sh_op=0.30):
    """Place an item centred at (cx, cy) with a lift-dependent shadow."""
    x, y = cx - im.width / 2, cy - im.height / 2
    if shadow:
        sh, pad = soft_shadow(im, lift, sh_op)
        comp(layer, fade_img(sh, op), x - pad + 6 + 30 * lift, y - pad + 10 + 46 * lift)
    comp(layer, fade_img(im, op), x, y)


def _persp(src, dst):
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
        B += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(B, float))


def warp(im, quad):
    """Map the image onto quad (TL, TR, BR, BL in layer pixels). Returns (image, x0, y0)."""
    xs, ys = [p[0] for p in quad], [p[1] for p in quad]
    x0, y0 = math.floor(min(xs)), math.floor(min(ys))
    w, h = math.ceil(max(xs)) - x0 + 1, math.ceil(max(ys)) - y0 + 1
    if w < 3 or h < 3:
        return None, x0, y0
    loc = [(x - x0, y - y0) for x, y in quad]
    try:
        c = _persp([(0, 0), (im.width, 0), (im.width, im.height), (0, im.height)], loc)
    except np.linalg.LinAlgError:
        return None, x0, y0
    out = im.convert('RGBa').transform((w, h), Image.PERSPECTIVE, tuple(c), Image.BICUBIC).convert('RGBA')
    return out, x0, y0


def put_quad(layer, im, quad, lift=0.0, op=1.0, darken=0.0, shadow=True):
    out, x0, y0 = warp(shade(im, darken), quad)
    if out is None:
        return
    if shadow:
        sh, pad = soft_shadow(out, lift)
        comp(layer, fade_img(sh, op), x0 - pad + 6 + 30 * lift, y0 - pad + 10 + 46 * lift)
    comp(layer, fade_img(out, op), x0, y0)


def back_of(im):
    """The back of a sheet: same silhouette, plain paper with a faint show-through."""
    b = Image.new('RGBA', im.size, PAPER_BACK + (255,))
    ghost = im.convert('L').transpose(Image.FLIP_LEFT_RIGHT).point(lambda v: 255 - v)
    b = Image.composite(Image.new('RGBA', im.size, (200, 190, 172, 255)), b, ghost.point(lambda v: int(v * 0.10)))
    b.putalpha(im.getchannel('A').transpose(Image.FLIP_LEFT_RIGHT))
    return b


_cache = {}


def rot_scale(im, ang, sc, key=None):
    if key is not None and (key, round(ang, 2), round(sc, 3)) in _cache:
        return _cache[(key, round(ang, 2), round(sc, 3))]
    out = im
    if abs(sc - 1) > 1e-3:
        out = out.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
    if abs(ang) > 0.01:
        out = out.convert('RGBa').rotate(ang, Image.BICUBIC, expand=True).convert('RGBA')
    if key is not None:
        if len(_cache) > 400:
            _cache.clear()
        _cache[(key, round(ang, 2), round(sc, 3))] = out
    return out


# ------------------------------------------------------------------ 1. page flip
def page_flip(layer, page, hinge_x, cy, t, start, dur=1.15, opening=False, persp=0.10):
    """A page hinged on its left edge at hinge_x. opening=False: the page turns over from the
    left and lands on the right (revealing its front). opening=True: it lifts off the right
    side and turns away (revealing whatever was drawn beneath it)."""
    sfx('pageflip', start, hinge_x, dur=dur)
    u = ease_io((t - start) / dur)
    if t < start:
        u = 0.0
    a = math.pi * (u if opening else 1 - u)          # 0 = lying flat on the right
    w, h = page.width, page.height
    y0, y1 = cy - h / 2, cy + h / 2
    xf = hinge_x + w * math.cos(a)
    e = persp * h * math.sin(a)
    lift = 0.55 * math.sin(a)
    dark = 0.38 * math.sin(a) ** 2
    if math.cos(a) >= 0:
        quad = [(hinge_x, y0), (xf, y0 - e), (xf, y1 + e), (hinge_x, y1)]
        put_quad(layer, page, quad, lift, 1.0, dark)
    else:
        quad = [(xf, y0 - e), (hinge_x, y0), (hinge_x, y1), (xf, y1 + e)]
        put_quad(layer, back_of(page), quad, lift, 1.0, dark * 0.6)


# ------------------------------------------------------------------ 2. drop
def drop(layer, im, cx, cy, t, start, rot=-3.0, spin=16.0, height=1.0, speed=1.0, key=None, from_y=-140):
    """A print dropped onto the desk: starts lifted (bigger, soft far shadow), spins down,
    overshoots a touch, settles flat."""
    sfx('drop', start / 1.0, cx, gain=0.5)
    if t < start:
        return
    u = (t - start) * speed
    p = damped(u / 0.9, zeta=0.5, cycles=1.25)
    h = height * max(0.0, 1 - p)
    sc = 1 + 0.20 * height * (1 - p)
    ang = rot + spin * (1 - p)
    op = ease_out(u / 0.18)
    item = rot_scale(im, ang, sc, key if p >= 0.999 else None)
    put(layer, item, cx, cy + from_y * (1 - p), lift=h, op=op)


# ------------------------------------------------------------------ 3. unfold
def unfold(layer, doc, cx, cy, t, start, dur=1.3, enter=0.45, crease=True):
    """A letter folded in three: it slides in folded, then the top flap opens toward the
    viewer, then the bottom flap. Fold creases stay visible."""
    sfx('slide', start - enter, cx, dur=enter + 0.3)
    sfx('unfold', start, cx, dur=dur)
    w, h = doc.width, doc.height
    ph = h / 3
    x0, x1 = cx - w / 2, cx + w / 2
    ya, yb = cy - h / 2 + ph, cy - h / 2 + 2 * ph
    if t < start - enter:
        return
    e_in = ease_out((t - (start - enter)) / enter, 4)
    dy = (1 - e_in) * 260
    top, mid, bot = (doc.crop((0, int(i * ph), w, int((i + 1) * ph))) for i in range(3))
    ya_, yb_ = ya + dy, yb + dy
    sh, pad = soft_shadow(mid, 0.15)
    comp(layer, fade_img(sh, e_in), x0 - pad + 10, ya_ - pad + 16)
    comp(layer, fade_img(mid, e_in), x0, ya_)
    if crease:
        d = ImageDraw.Draw(layer)
        for yy in (ya_, yb_):
            d.line((x0 + 4, yy, x1 - 4, yy), fill=(150, 140, 125, int(90 * e_in)), width=2)

    def flap(img, hinge_y, ang, down):
        # ang: 0 = open flat, pi = folded over the middle panel
        s = 1 if down else -1                       # direction the flap extends when open
        yf = hinge_y + s * ph * math.cos(ang)
        e = 0.08 * w * math.sin(ang)
        dark = 0.35 * math.sin(ang) ** 2
        if math.cos(ang) >= 0:      # front side visible
            quad = ([(x0, hinge_y), (x1, hinge_y), (x1 + e, yf), (x0 - e, yf)] if down else
                    [(x0 - e, yf), (x1 + e, yf), (x1, hinge_y), (x0, hinge_y)])
            put_quad(layer, img, quad, 0.35 * math.sin(ang), e_in, dark)
        else:                       # back of the flap, lying over the middle panel
            b = back_of(img).transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.FLIP_LEFT_RIGHT)
            quad = ([(x0 - e, yf), (x1 + e, yf), (x1, hinge_y), (x0, hinge_y)] if down else
                    [(x0, hinge_y), (x1, hinge_y), (x1 + e, yf), (x0 - e, yf)])
            put_quad(layer, b, quad, 0.35 * math.sin(ang), e_in, dark * 0.5)
    u1 = damped((t - start) / (dur * 0.62), zeta=0.6, cycles=1.1)
    u2 = damped((t - start - dur * 0.38) / (dur * 0.62), zeta=0.6, cycles=1.1)
    flap(bot, yb_, math.pi * (1 - u2), True)
    flap(top, ya_, math.pi * (1 - u1), False)


# ------------------------------------------------------------------ 9. slide (friction)
def slide(layer, im, frm, to, t, start, dur=1.1, rot=-2.0, lag=9.0, key=None):
    """Pushed across the desk: quick start, friction-slowed arrival with a tiny overshoot.
    The sheet lags into a rotation while moving and straightens as it stops."""
    sfx('slide', start, to[0], dur=dur)
    if t < start:
        return
    u = (t - start) / dur
    p = damped(u, zeta=0.72, cycles=0.95)
    dp = (damped(u + 0.01, 0.72, 0.95) - p) / 0.01
    dirx = 1 if to[0] >= frm[0] else -1
    ang = rot - dirx * lag * min(1.0, dp / 2.5)
    lift = 0.12 * min(1.0, dp / 2.5)
    x, y = lerp(frm[0], to[0], p), lerp(frm[1], to[1], p)
    item = rot_scale(im, ang, 1.0, key if u >= 1 else None)
    put(layer, item, x, y, lift=lift, op=ease_out(u / 0.12))


# ------------------------------------------------------------------ 5. tear reveal
@lru_cache(maxsize=16)
def _tear_halves(w, h, seed, cover_id):
    cover = _tear_halves.covers[cover_id]
    r = np.random.default_rng(seed)
    pts = []
    x = w / 2
    for y in range(-10, h + 20, 14):
        x += r.normal(0, 7)
        x = min(max(x, w * 0.38), w * 0.62)
        pts.append((x, y))
    lm = Image.new('L', (w, h), 0)
    ImageDraw.Draw(lm).polygon([(0, -10)] + pts + [(0, h + 20)], fill=255)
    rm = Image.eval(lm, lambda v: 255 - v)
    out = []
    for m, sgn in ((lm, -1), (rm, 1)):
        half = cover.copy()
        half.putalpha(Image.fromarray(np.minimum(np.asarray(m), np.asarray(cover.getchannel('A')))))
        lip = Image.new('L', (w, h), 0)            # torn white fibre edge
        ImageDraw.Draw(lip).line([(p[0] + sgn * 2, p[1]) for p in pts], fill=255, width=7)
        lip = Image.fromarray(np.minimum(np.asarray(lip), np.asarray(half.getchannel('A'))))
        half = Image.composite(Image.new('RGBA', (w, h), (252, 249, 240, 255)), half, lip)
        out.append(half)
    return out


_tear_halves.covers = {}


def tear_reveal(layer, cover, cx, cy, t, start, dur=0.95, seed=3, spread=760):
    """A paper cover over (cx, cy) is ripped down the middle and pulled apart.
    Draw the hidden image first, then call this."""
    sfx('tear', start, cx, dur=dur)
    cid = id(cover)
    _tear_halves.covers[cid] = cover
    if t < start:
        put(layer, cover, cx, cy, lift=0.05)
        return
    u = clamp01((t - start) / dur)
    if u >= 1:
        return
    L, R = _tear_halves(cover.width, cover.height, seed, cid)
    k = u ** 1.7                                   # resists, then gives way
    op = 1 - ease_io((u - 0.55) / 0.45)
    for half, sgn in ((L, -1), (R, 1)):
        item = rot_scale(half, -sgn * 16 * k, 1 + 0.04 * k)
        put(layer, item, cx + sgn * spread * k, cy + 80 * k * k, lift=0.3 * k, op=op)


# ------------------------------------------------------------------ 6. stack
def stack(layer, items, spots, t, starts, rots=None):
    """Prints landing one after another; each impact nudges the prints already underneath."""
    rots = rots or [(-4, 3, -1, 5, -2)[i % 5] for i in range(len(items))]
    for i, (im, (cx, cy), st) in enumerate(zip(items, spots, starts)):
        nx = ny = 0.0
        for j in range(i + 1, len(items)):
            land = starts[j] + 0.32
            if t > land:
                k = math.exp(-(t - land) * 6) * math.sin((t - land) * 30)
                dx, dy = cx - spots[j][0], cy - spots[j][1]
                n = math.hypot(dx, dy) or 1
                nx += 7 * k * dx / n
                ny += 7 * k * dy / n
        drop(layer, im, cx + nx, cy + ny, t, st, rot=rots[i], spin=rots[i] * 3, height=0.8, key=('stk', id(im), i))


# ------------------------------------------------------------------ 7. stamp hit
@lru_cache(maxsize=32)
def stamp_image(s, size, colour=RED):
    f = F_HEAD(size)
    tw = int(ImageDraw.Draw(Image.new('RGBA', (1, 1))).textlength(s, font=f)) + 64
    th = int(size * 1.5)
    st = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    d.rectangle((6, 6, tw - 6, th - 6), outline=colour + (255,), width=7)
    d.text((tw / 2, th / 2 + 2), s, font=f, fill=colour + (255,), anchor='mm')
    a = np.asarray(st).astype(np.float32)
    r = np.random.default_rng(len(s) * 7 + size)
    a[r.random(a.shape[:2]) < 0.12, 3] = 0                        # dry-ink dropout
    grain = np.asarray(Image.fromarray((r.random((th // 6 + 1, tw // 6 + 1)) * 255).astype(np.uint8)).resize((tw, th), Image.BICUBIC), np.float32) / 255
    a[..., 3] *= 0.72 + 0.28 * grain                               # uneven inking
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


def stamp_hit(layer, s, cx, cy, t, start, size=90, ang=-8.0, shot=None, descent=0.2):
    """The stamp drops from above the page (big, faint, shadowed) and hits at `start`;
    a split second of ink spread, then it sits flat. Pass shot to kick the camera."""
    sfx('stamp', start, cx)
    if shot is not None:
        shot.hit(start)
    if t < start - descent:
        return
    im = stamp_image(s, size)
    if t < start:
        u = clamp01((t - (start - descent)) / descent)
        sc, op = lerp(1.9, 1.02, u ** 2), 0.25 + 0.6 * u
        item = rot_scale(im, ang + 6 * (1 - u), sc)
        put(layer, item, cx, cy, lift=1 - u, op=op, sh_op=0.18)
        return
    k = clamp01((t - start) / 0.12)
    item = rot_scale(im, ang, lerp(1.04, 1.0, k), key=('stamp', s, size, ang) if k >= 1 else None)
    put(layer, item, cx, cy, op=1.0, shadow=False)


# ------------------------------------------------------------------ 8. mask reveal
def mask_reveal(layer, im, cx, cy, t, start, dur=1.2, seed=5, origin=(0.5, 0.5), lip=True):
    """The image is revealed through a growing, irregular torn hole, with a paper lip and a
    soft inner shadow around the opening."""
    sfx('reveal', start, cx, dur=dur)
    if t < start:
        return
    u = ease_out((t - start) / dur, 3)
    w, h = im.width, im.height
    if u >= 0.999:
        put(layer, im, cx, cy, lift=0.0)
        return
    r = np.random.default_rng(seed)
    n = 72
    harm = [(r.uniform(0.04, 0.12), r.integers(2, 9), r.uniform(0, 6.28)) for _ in range(5)]
    ox, oy = origin[0] * w, origin[1] * h
    R = math.hypot(max(ox, w - ox), max(oy, h - oy)) * 1.25 * u
    pts = []
    for i in range(n):
        th = i / n * 2 * math.pi
        k = 1 + sum(a * math.sin(f * th + p + u * 2) for a, f, p in harm) + r.normal(0, 0.025)
        pts.append((ox + math.cos(th) * R * k, oy + math.sin(th) * R * k))
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    a = np.minimum(np.asarray(m), np.asarray(im.getchannel('A')))
    out = im.copy()
    out.putalpha(Image.fromarray(a))
    if lip:
        ring = Image.new('L', (w, h), 0)
        ImageDraw.Draw(ring).line(pts + [pts[0]], fill=255, width=9)
        inner = ring.filter(ImageFilter.GaussianBlur(9))
        out = Image.composite(Image.new('RGBA', (w, h), (30, 20, 12, 255)), out, Image.fromarray((np.asarray(inner) * 0.35 * (a > 0)).astype(np.uint8)))
        ring = Image.fromarray(np.minimum(np.asarray(ring), a))
        out = Image.composite(Image.new('RGBA', (w, h), (250, 245, 232, 255)), out, ring)
    put(layer, out, cx, cy, lift=0.0, sh_op=0.18)


# ------------------------------------------------------------------ 10. assemble
@lru_cache(maxsize=16)
def _pieces(key, n, seed):
    im = _pieces.items[key]
    w, h = im.width, im.height
    r = np.random.default_rng(seed)
    a = np.asarray(im.getchannel('A'))
    ys, xs = np.nonzero(a > 20)
    idx = r.choice(len(xs), n, replace=False)
    sx, sy = xs[idx].astype(np.float32), ys[idx].astype(np.float32)
    q = 4
    gy, gx = np.mgrid[0:h:q, 0:w:q].astype(np.float32)
    # jittered Voronoi -> irregular paper pieces
    gx2 = gx + np.asarray(Image.fromarray((r.random(gx.shape) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), np.float32) / 255 * 30
    lab = np.argmin((gx2[..., None] - sx) ** 2 + (gy[..., None] - sy) ** 2, axis=2)
    lab = np.asarray(Image.fromarray(lab.astype(np.uint8)).resize((w, h), Image.NEAREST))
    out = []
    for i in range(n):
        m = (lab == i) & (a > 0)
        if not m.any():
            continue
        yy, xx = np.nonzero(m)
        box = (xx.min(), yy.min(), xx.max() + 1, yy.max() + 1)
        piece = im.crop(box)
        pa = np.asarray(piece.getchannel('A')).copy()
        pa[~m[box[1]:box[3], box[0]:box[2]]] = 0
        piece.putalpha(Image.fromarray(pa))
        ang = math.atan2((box[1] + box[3]) / 2 - h / 2, (box[0] + box[2]) / 2 - w / 2) + r.normal(0, 0.5)
        out.append((piece, (box[0] + box[2]) / 2 - w / 2, (box[1] + box[3]) / 2 - h / 2, ang, r.uniform(-50, 50), r.uniform(380, 640)))
    return out


_pieces.items = {}


def assemble(layer, im, cx, cy, t, start, n=7, dur=0.9, stagger=0.09, seed=4, reverse=False):
    """A cut-out flies together from irregular paper pieces (reverse=True: it breaks apart)."""
    sfx('assemble', start, cx, n=n, stagger=stagger, dur=dur, reverse=reverse)
    key = id(im)
    _pieces.items[key] = im
    pcs = _pieces(key, n, seed)
    end = start + dur + stagger * len(pcs)
    if (t >= end and not reverse) or (t < start and reverse):
        put(layer, im, cx, cy)
        return
    if (t < start and not reverse) or (t >= end and reverse):
        return
    for i, (piece, ox, oy, ang, spin, dist) in enumerate(pcs):
        u = (t - start - i * stagger) / dur
        p = damped(u, zeta=0.62, cycles=1.0) if not reverse else 1 - ease_out(u, 2)
        if (not reverse and u <= 0):
            continue
        k = 1 - p
        item = rot_scale(piece, spin * k, 1 + 0.15 * k)
        put(layer, item, cx + ox + math.cos(ang) * dist * k, cy + oy + math.sin(ang) * dist * k,
            lift=0.5 * max(0.0, k), op=ease_out(u / 0.15) if not reverse else 1 - ease_io((u - 0.6) / 0.4))


# ------------------------------------------------------------------ 11. flip
def flip(layer, front, back, cx, cy, t, start, dur=0.85, persp=0.12, axis='y'):
    """A print lifts, flips over its vertical (or horizontal) axis and lands showing a
    second photograph."""
    sfx('flip', start, cx, dur=dur)
    u = 0.0 if t < start else ease_io((t - start) / dur)
    a = math.pi * u
    im = front if math.cos(a) >= 0 else back
    lift = math.sin(a)
    sc = 1 + 0.07 * lift
    w, h = im.width * sc, im.height * sc
    c = abs(math.cos(a))
    e = persp * (h if axis == 'y' else w) * math.sin(a) * (1 if math.cos(a) >= 0 else -1)
    if axis == 'y':
        hw = w / 2 * c
        quad = [(cx - hw, cy - h / 2 - e / 2), (cx + hw, cy - h / 2 + e / 2), (cx + hw, cy + h / 2 - e / 2), (cx - hw, cy + h / 2 + e / 2)]
    else:
        hh = h / 2 * c
        quad = [(cx - w / 2 - e / 2, cy - hh), (cx + w / 2 + e / 2, cy - hh), (cx + w / 2 - e / 2, cy + hh), (cx - w / 2 + e / 2, cy + hh)]
    put_quad(layer, im, quad, 0.6 * lift, 1.0, 0.35 * lift ** 2)
