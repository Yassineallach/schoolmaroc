"""Calls to action in the channel's own language (brand.json cta.style = 'marker').

They speak the intro's language and the film's: the button is drawn by pen and coloured in by
marker in the channel's orange, the press closes the hatching into solid colour with the first two
notes of the sting, the tick is drawn by pen; the cards are paper on the desk (a clipping dropped
and taped, a tab sliding in from the frame edge, a note pinned); each film can give the like card
one element of its own story (cta.like.motif); words are few, the verb and the reason set apart;
the card goes in the frame's quietest corner and lives exactly as long as the narration's pause.

  subscribe(layer, x, y, t, dur, T0)        tab sliding in, drawn button, press, tick, bell
  like(layer, x, y, t, dur, T0, motif=None) taped clipping, thumb coloured in, optional motif drop
  comment_note(layer, x, y, t, width, T0)   a pinned note; the question written by pen, word by word
  quiet_corner(frame, w, h, ...)            the corner of the frame with the least going on
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from vox import W, H, PAL, alpha_mul
import brand as B


def _c(x):
    return min(max(x, 0.0), 1.0)


def _eo(x):
    return 1 - (1 - _c(x)) ** 3


def _eio(x):
    return 0.5 - 0.5 * math.cos(math.pi * _c(x))


def _ei(x):
    return _c(x) ** 3


ORANGE = B.CTA_FILL
CREAM = B.CTA_TEXT
INK = PAL.ink
PAPER = PAL.light


# ------------------------------------------------------------------ the pen and the marker
def _partial(pts, f):
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:])]
    tot = sum(seg) * f
    out = [pts[0]]
    for (a, b), l in zip(zip(pts[:-1], pts[1:]), seg):
        if tot <= 0 or l == 0:
            break
        k = min(1.0, tot / l)
        out.append((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k))
        tot -= l
    return out


def _rrect_path(x0, y0, x1, y1, r, n=10):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts.append(pts[0])
    rot = len(pts) // 8                                    # start the pen at the top left, like a hand would
    return pts[rot:] + pts[1:rot + 1]


def _pen(layer, pts, f, colour, width=3, dot=True, ss=3):
    """Part f of a polyline drawn by pen (supersampled), with an ink dot leading it."""
    if f <= 0:
        return
    part = _partial(pts, f)
    if len(part) > 1:
        x0 = min(p[0] for p in pts) - 10; y0 = min(p[1] for p in pts) - 10
        x1 = max(p[0] for p in pts) + 10; y1 = max(p[1] for p in pts) + 10
        w_, h_ = int(x1 - x0), int(y1 - y0)
        m = Image.new('L', (w_ * ss, h_ * ss), 0)
        ImageDraw.Draw(m).line([((x - x0) * ss, (y - y0) * ss) for x, y in part], fill=255, width=width * ss, joint='curve')
        m = m.resize((w_, h_), Image.LANCZOS)
        tile = Image.new('RGBA', (w_, h_), colour + (0,))
        tile.putalpha(m)
        layer.alpha_composite(tile, (int(x0), int(y0)))
    if dot and f < 1:
        x, y = part[-1]
        ImageDraw.Draw(layer).ellipse((x - 3.5, y - 3.5, x + 3.5, y + 3.5), fill=colour + (255,))


_HATCH = {}


def _hatch(mask, p, colour, seed=0, spacing=7.0, width=(5, 7), angle=62):
    """Marker strokes colouring a mask in, left to right; p in 0..1. Tapered, with pressure."""
    key = (mask.shape, seed, spacing)
    if key not in _HATCH:
        rng = np.random.default_rng(seed)
        ys, xs = np.where(mask)
        a = math.radians(angle)
        dx, dy = math.cos(a), -math.sin(a)
        nx, ny = -dy, dx
        proj = xs * nx + ys * ny
        strokes, k, flip = [], proj.min() - 3, False
        while k < proj.max() + 3:
            on = np.abs(proj - k) < 1.5
            if on.sum() > 2:
                al = xs[on] * dx + ys[on] * dy
                a0, a1 = al.min() - 4, al.max() + 4
                pts = [(nx * k + dx * (a0 + (a1 - a0) * f) + nx * rng.normal(0, 0.8), ny * k + dy * (a0 + (a1 - a0) * f) + ny * rng.normal(0, 0.8))
                       for f in np.linspace(0, 1, 6)]
                strokes.append((pts[::-1] if flip else pts, float(rng.uniform(*width)), float(rng.uniform(0.6, 0.9))))
                flip = not flip
            k += spacing * float(rng.uniform(0.85, 1.15))
        _HATCH[key] = strokes
    strokes = _HATCH[key]
    h_, w_ = mask.shape
    acc = np.zeros((h_, w_), np.float32)
    n = len(strokes)
    for i, (pts, wd, pr) in enumerate(strokes):
        f = (p * (n + 2) - i) / 2.0
        if f <= 0:
            break
        part = _partial(pts, min(1.0, f))
        if len(part) < 2:
            continue
        L = Image.new('L', (w_, h_), 0)
        d = ImageDraw.Draw(L)
        for j in range(len(part) - 1):
            u = (j + 0.5) / 5
            d.line([part[j], part[j + 1]], fill=255, width=max(2, int(wd * (0.5 + 0.5 * math.sin(math.pi * u) ** 0.6))))
        acc = 1 - (1 - acc) * (1 - np.asarray(L, np.float32) / 255 * pr)
    acc *= mask
    out = np.zeros((h_, w_, 4), np.uint8)
    out[..., :3] = colour
    out[..., 3] = (acc * 255).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')


def _rrect_mask(w_, h_, r, ss=4):
    m = Image.new('L', (w_ * ss, h_ * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w_ * ss - 1, h_ * ss - 1), radius=r * ss, fill=255)
    return np.asarray(m.resize((w_, h_), Image.LANCZOS)) > 127


# ------------------------------------------------------------------ paper
def _paper(w_, h_, seed=3, torn=True, colour=None):
    import presets as P
    c = P.paper_card(int(w_), int(h_), seed=seed, colour=colour or PAPER) if torn else B._card(w_, h_, colour or PAPER, radius=6)
    return c


def _shadow_put(layer, card, x, y, lift=0.0, rot=0.0, op=1.0):
    """Paper on the desk: the shadow grows and softens with the lift (as the film's presets do)."""
    if rot:
        card = card.rotate(rot, Image.BICUBIC, expand=True)
    blur = 10 + 16 * lift
    off = 6 + 18 * lift
    a = card.getchannel('A').point(lambda v: int(v * (0.28 - 0.10 * lift)))
    pad = int(2 * blur + off)
    sh = Image.new('RGBA', (card.width + 2 * pad, card.height + 2 * pad), (0, 0, 0, 0))
    m = Image.new('L', sh.size, 0)
    m.paste(a, (pad, pad))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(blur)))
    layer.alpha_composite(alpha_mul(sh, op), (int(x - pad + off * 0.4), int(y - pad + off)))
    layer.alpha_composite(alpha_mul(card, op), (int(x), int(y)))


def _tape(w_=96, h_=30, seed=5):
    rng = np.random.default_rng(seed)
    t = Image.new('RGBA', (w_, h_), (214, 196, 160, 150))
    d = ImageDraw.Draw(t)
    for x in (0, w_ - 1):
        for y in range(0, h_, 3):
            d.point((x + (rng.integers(-1, 2) if x else rng.integers(0, 2)), y), fill=(0, 0, 0, 0))
    d.line((0, 1, w_, 1), fill=(190, 170, 130, 170)); d.line((0, h_ - 2, w_, h_ - 2), fill=(190, 170, 130, 170))
    return t


# ------------------------------------------------------------------ subscribe
def subscribe(layer, x, y, t, dur=3.6, T0=None, force=False):
    """A paper tab slides in from the frame's edge (friction, no bounce); the button is drawn by pen
    and coloured in by marker in the channel's orange; at the press the hatching closes into solid
    colour, the button dips, the first notes of the sting sound, « Abonné » appears and its tick is
    drawn by pen; the bell rings twice; the tab slides back out."""
    if t < 0 or t > dur:
        return
    tf = B._font('label', 27)
    rf = B._font('body', 22)
    lab, done = B.TXT['subscribe'], B.TXT['subscribed']
    reason = B.TXT.get('subscribe_reason', '')
    bw = int(max(tf.getlength(lab), tf.getlength(done) + 34) + 60)
    bh = 56
    lg = B.logo(132, force=force)
    lw = lg.width if lg is not None else 0
    pad = 26
    cw = pad + (lw + 30 if lg is not None else 0) + bw + 22 + 40 + pad
    ch = pad + bh + 10 + 26 + pad - 6
    card = _paper(cw, ch, seed=21, torn=False)
    if lg is not None:
        B.place_logo(card, pad + 8, (ch - lg.height) // 2 - 2, lg.width, force=force, ground=B._lum(PAPER))
    bx = pad + (lw + 30 if lg is not None else 0)
    by = pad - 2
    # the button: outline by pen, marker fill, press
    o = _c((t - 0.35) / 0.45)
    fillp = _c((t - 0.62) / 0.6)
    press = 1.3
    snapped = t >= press
    btn = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    mask = _rrect_mask(bw, bh, bh // 2)
    if not snapped:
        btn.alpha_composite(_hatch(mask, fillp, ORANGE, seed=4, spacing=6.5))
        if o < 1 or fillp < 1:
            _pen(btn, [(px + 0.5, py + 0.5) for px, py in _rrect_path(1.5, 1.5, bw - 2.5, bh - 2.5, bh / 2 - 2)], _eio(o), ORANGE, width=3, dot=o < 1)
        else:
            _pen(btn, [(px + 0.5, py + 0.5) for px, py in _rrect_path(1.5, 1.5, bw - 2.5, bh - 2.5, bh / 2 - 2)], 1.0, ORANGE, width=3, dot=False)
        a = int(255 * _eo((t - 0.95) / 0.3))
        if a > 0:
            ImageDraw.Draw(btn).text((bw / 2, bh / 2), lab, font=tf, fill=CREAM + (a,), anchor='mm')
    else:
        q = _c((t - press) / 0.14)
        solid = Image.new('RGBA', (bw, bh), ORANGE + (255,))
        solid.putalpha(Image.fromarray((mask * 255).astype(np.uint8)))
        hat = _hatch(mask, 1.0, ORANGE, seed=4, spacing=6.5)
        btn = Image.blend(hat, solid, q) if q < 1 else solid
        bd = ImageDraw.Draw(btn)
        if t < press + 0.12:
            bd.text((bw / 2, bh / 2), lab, font=tf, fill=CREAM + (255,), anchor='mm')
        else:
            bd.text((22 + 34, bh / 2), done, font=tf, fill=CREAM + (255,), anchor='lm')
            tick = [(22, bh / 2 + 1), (31, bh / 2 + 10), (47, bh / 2 - 9)]
            _pen(btn, tick, _eio((t - press - 0.12) / 0.28), CREAM, width=3, dot=False)
    dip = 1 - 0.045 * math.sin(math.pi * _c((t - press + 0.02) / 0.22))
    if dip != 1:
        btn = btn.resize((int(bw * dip), int(bh * dip)), Image.LANCZOS)
    card.alpha_composite(btn, (int(bx + bw * (1 - dip) / 2), int(by + bh * (1 - dip) / 2)))
    # the reason, set apart under the verb
    ra = int(255 * _eo((t - 1.0) / 0.4))
    if ra > 0 and reason:
        ImageDraw.Draw(card).text((bx + 4, by + bh + 8), reason, font=rf, fill=PAL.muted + (ra,))
    # the bell
    ring = t - (press + 0.5)
    ang = 15 * math.exp(-max(ring, 0) * 3.0) * math.sin(max(ring, 0) * 15) if ring > 0 else 0
    bell = B._icon('bell', 34, INK).rotate(ang, Image.BICUBIC, center=(17, 3))
    card.alpha_composite(bell, (int(bx + bw + 22), int(by + (bh - 34) / 2)))
    # in from the frame edge with friction, out the same way
    edge_left = x < W / 2
    k_in = _eo(t / 0.55)
    k_out = _ei((t - (dur - 0.45)) / 0.45)
    dist = (x + cw + 40) if edge_left else (W - x + 40)
    xx = x - (1 - k_in) * dist * (1 if edge_left else -1) - k_out * dist * (1 if edge_left else -1)
    _shadow_put(layer, card, xx, y, lift=0.25 * (1 - k_in) + 0.25 * k_out)
    if T0 is not None:
        B._sound('slide', T0 + 0.02, x, 0.35)
        B._sound('pencil', T0 + 0.35, x + bx, 0.25)
        B._sound('marker', T0 + 0.65, x + bx + bw / 2, 0.35)
        _tap(T0 + press)
        B._sound('slide', T0 + dur - 0.45, x, 0.25)
    return cw, ch


def _tap(T):
    mc = B.CFG.get('music', {})
    if mc.get('enabled') and mc.get('tap'):
        import os
        import style
        p = os.path.join(B.BRAND_DIR, mc['tap'])
        if os.path.exists(p):
            style.EVENTS[('voice', round(T, 3), 960)] = {'file': p, 'gain': mc.get('tap_gain', 0.55)}


# ------------------------------------------------------------------ like
def like(layer, x, y, t, dur=3.0, T0=None, motif=None):
    """A clipping dropped on the desk and taped; the thumb is drawn by pen and coloured in by
    marker; optionally one element of the film's own story drops onto it (motif, RGBA image);
    the reason in the serif, the verb set apart in small caps."""
    if t < 0 or t > dur:
        return
    rf = B._font('title', 42)
    vf = B._font('label', 23)
    msg = B.CFG['cta']['like'].get('text') or B.TXT['like']
    verb = (B.CFG['cta']['like'].get('verb') or B.TXT.get('like_verb', '')).upper()
    tw = max(rf.getlength(msg), vf.getlength(verb) * 1.15)
    icon = 76
    cw = int(30 + icon + 28 + tw + 38)
    ch = 136
    card = _paper(cw, ch, seed=31, torn=True)
    d = ImageDraw.Draw(card)
    ix, iy = 28, (ch - icon) // 2
    # the thumb: outline drawn, then coloured in
    th = B._icon('thumb', icon, INK)
    o = _eo((t - 0.35) / 0.45)
    m = Image.new('L', th.size, 0)
    ImageDraw.Draw(m).rectangle((0, 0, icon * o, icon), fill=255)
    th.putalpha(Image.fromarray(np.minimum(np.asarray(th.getchannel('A')), np.asarray(m))))
    fm = B._icon('thumb', icon, INK, fill=ORANGE, p=1.0)
    fa = np.asarray(fm).astype(np.int16)
    fill_mask = (fa[..., 3] > 100) & (np.abs(fa[..., :3] - np.array(ORANGE)).sum(2) < 90)
    fp = _c((t - 0.75) / 0.55)
    if fp > 0:
        card.alpha_composite(_hatch(fill_mask, fp, ORANGE, seed=8, spacing=5.0, width=(4, 5)), (ix, iy))
    if t > 1.35:
        q = _c((t - 1.35) / 0.15)
        solid = np.zeros(fa.shape, np.uint8)
        solid[..., :3] = ORANGE
        solid[..., 3] = (fill_mask * 255 * q).astype(np.uint8)
        card.alpha_composite(Image.fromarray(solid, 'RGBA'), (ix, iy))
    card.alpha_composite(th, (ix, iy))
    # words: the reason, then the verb set apart
    tx = ix + icon + 26
    a1 = int(255 * _eo((t - 0.45) / 0.4))
    d.text((tx, 24), msg, font=rf, fill=INK + (a1,))
    a2 = int(255 * _eo((t - 0.95) / 0.4))
    sp = 0
    for ch_ in verb:                                          # small caps with a little tracking
        d.text((tx + sp, 88), ch_, font=vf, fill=ORANGE + (a2,))
        sp += vf.getlength(ch_) + 1.6
    # the drop: falls with a slight turn, settles; the tape lands with it
    k = _eo(t / 0.5)
    out = _ei((t - (dur - 0.4)) / 0.4)
    rot = -5 + 3.5 * k
    yy = y - 70 * (1 - k)
    tape = _tape()
    if k >= 0.85:
        card.alpha_composite(tape.rotate(4, Image.BICUBIC, expand=True), (cw // 2 - 50, -6))
    _shadow_put(layer, card, x, yy - 10 * out, lift=0.4 * (1 - k) + 0.3 * out, rot=rot, op=1 - out)
    # the film's own element drops onto the thumb as it fills
    if motif is not None and 0.55 < t:
        u = _eo((t - 0.55) / 0.45)
        mo = motif.resize((max(2, int(motif.width * 34 / motif.height)), 34), Image.LANCZOS).rotate(-25, Image.BICUBIC, expand=True)
        mx = x + ix + icon * 0.62                            # it lands on the thumb itself
        my = yy + iy + icon * 0.42 - 110 * (1 - u)
        layer.alpha_composite(alpha_mul(mo, (1 - out) * min(1, u * 2)), (int(mx - mo.width / 2), int(my - mo.height / 2)))
    if T0 is not None:
        B._sound('drop', T0 + 0.45, x + 60, 0.4)
        B._sound('tape', T0 + 0.5, x + cw / 2, 0.3)
        B._sound('marker', T0 + 0.8, x + 60, 0.3)
        B._sound('pop', T0 + 1.36, x + 60, 0.35)
    return cw, ch


# ------------------------------------------------------------------ the pinned comment note (outro)
def comment_note(layer, x, y, t, width=820, T0=None, question=None):
    """A note pinned to the desk: the label, then the video's question written by pen, word by
    word, an ink dot at the nib."""
    if t < 0:
        return
    q = question or B.comment_question()
    lf = B._font('label', 20)
    qf = B._font('title', 40)
    lines = B._wrap(q, qf, width - 76)
    lh = 54
    ch = 34 + 30 + 16 + lh * len(lines) + 34
    card = _paper(width, ch, seed=41, torn=True)
    d = ImageDraw.Draw(card)
    card.alpha_composite(B._icon('bubble', 30, ORANGE), (38, 30))
    d.text((38 + 42, 45), B.TXT['comment_label'].upper(), font=lf, fill=PAL.muted + (255,), anchor='lm')
    # the question, written: each word revealed left to right behind the nib
    words = [(i, w_) for i, ln in enumerate(lines) for w_ in ln.split(' ')]
    per = 0.16
    start = 0.55
    xcur = {}
    for n, (li, w_) in enumerate(words):
        f = (t - start - n * per) / per
        x0 = xcur.get(li, 38)
        ww = qf.getlength(w_)
        xcur[li] = x0 + ww + qf.getlength(' ')
        if f <= 0:
            continue
        f = min(1.0, f)
        tile = Image.new('RGBA', (int(ww) + 6, lh + 8), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((0, 2), w_, font=qf, fill=INK + (255,))
        m = Image.new('L', tile.size, 0)
        ImageDraw.Draw(m).rectangle((0, 0, tile.width * f, tile.height), fill=255)
        tile.putalpha(Image.fromarray(np.minimum(np.asarray(tile.getchannel('A')), np.asarray(m.filter(ImageFilter.GaussianBlur(2))))))
        yy = 34 + 30 + 16 + li * lh
        card.alpha_composite(tile, (int(x0), int(yy)))
        if f < 1:
            d.ellipse((x0 + ww * f - 3, yy + lh * 0.62 - 3, x0 + ww * f + 3, yy + lh * 0.62 + 3), fill=INK + (255,))
    k = _eo(t / 0.5)
    _shadow_put(layer, card, x, y + 40 * (1 - k), lift=0.35 * (1 - k), rot=-1.2 * k + -4 * (1 - k), op=min(1.0, k * 1.6))
    if k >= 0.9:                                              # the push pin
        px, py = x + width / 2, y + 14
        dd = ImageDraw.Draw(layer)
        dd.ellipse((px - 11 + 3, py - 11 + 5, px + 11 + 3, py + 11 + 5), fill=(0, 0, 0, 60))
        dd.ellipse((px - 11, py - 11, px + 11, py + 11), fill=ORANGE + (255,))
        dd.ellipse((px - 5, py - 7, px, py - 2), fill=(255, 220, 190, 200))
    if T0 is not None:
        B._sound('drop', T0 + 0.4, x + width / 2, 0.35)
        B._sound('pin', T0 + 0.5, x + width / 2, 0.4)
        B._sound('pencil', T0 + start, x + 100, 0.3)
    return width, ch


# ------------------------------------------------------------------ the quiet corner
def quiet_corner(frame, w_, h_, candidates=('bl', 'br', 'tl', 'tr'), margin=(64, 70)):
    """The candidate corner where a w x h card covers the least of what is on screen: fine detail
    (edges at half resolution, so small things like a grain count) and anything that differs from
    the plain ground (the frame's dominant tone). frame: numpy RGB or PIL image."""
    img = Image.fromarray(frame) if isinstance(frame, np.ndarray) else frame
    g = np.asarray(img.convert('L').resize((W // 2, H // 2)), np.float32)
    ex = np.abs(np.diff(g, axis=1))[:-1, :] + np.abs(np.diff(g, axis=0))[:, :-1]
    hist = np.bincount(np.clip(g.astype(int), 0, 255).ravel(), minlength=256)
    groundv = float(np.argmax(np.convolve(hist, np.ones(9), 'same')))
    off = np.abs(g - groundv) > 10
    best, score = None, 1e9
    for c in candidates:
        x, y = B._corner_xy(c, margin, h_, w_)
        x0, y0, x1, y1 = int(x / 2), int(y / 2), int((x + w_) / 2), int((y + h_) / 2)
        reg = ex[max(0, y0):y1, max(0, x0):x1]
        if not reg.size:
            continue
        s_ = float((reg > 18).mean() * 4 + off[max(0, y0):y1, max(0, x0):x1].mean())
        if s_ < score:
            best, score = (c, x, y), s_
    return best
