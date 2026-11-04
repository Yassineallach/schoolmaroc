"""Art-directed motion layer on top of the engine (vox.py): camera, parallax, transitions, type.

Every scene function returns a Shot with three transparent layers:
  shot.mid  paper on the desk: photos, plates, documents, cut-outs, AND the marks made on
            them (marker circles, stamps), so they stay glued to the paper during zooms
  shot.top  headline type laid out in the composition
  shot.hud  captions, labels, chapter kicker: fixed to the screen, never zoomed
compose() puts them over the episode background (bg_motion.motion_bg) through a virtual camera
with parallax: background 0.35x, mid 1x, top 1.15x of every zoom/pan; hud stays put.
Camera: shot.camera() (slow move over the shot), shot.push() (push-in on a cue, focus point
stays put), shot.zoom_to() (travel from the full composition into one image, optional pull-back).
Stamps register a hit: a short camera kick. Cuts are torn-paper wipes ('lr', 'rl') or a new
sheet laid over the old one ('up'), never a crossfade. Elements present at a cut start at
ENTER so the wipe reveals the new composition already landing.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import vox
from vox import W, H, FPS, INK, RED, CREAM, F_HEAD, F_TYPE, F_SERIF, spring, ease, ease_out_cubic, lerp, shadow_of, alpha_mul, torn_mask, finish
import bg_motion

PAPER_BACK = (241, 231, 212)

# ---- sound-effect events: registered while frames are drawn, turned into audio by sfx.py ----
EVENTS = {}


def event(kind, t_abs, x=None, **params):
    """Register a sound at absolute act time t_abs (seconds), at screen x (for panning)."""
    EVENTS[(kind, round(t_abs, 3), None if x is None else round(x))] = params


def sfx(kind, at, x=None, **params):
    """Manual cue from a scene: at is scene-local seconds (e.g. w(cue(...)))."""
    event(kind, vox._SCENE_START + at, x, **params)

ENTER = -0.36   # scene-local start for elements already present when the wipe reveals the shot


def ease_io(x):
    x = min(max(x, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def sp(t, start):
    """Spring progress 0..1 (slight overshoot) for an element entering at `start`."""
    return spring((t - start) * FPS)


def fade(t, start, dur=0.5):
    return ease_out_cubic((t - start) * FPS / (dur * FPS)) if t > start else 0.0


# ---------------------------------------------------------------- shot + camera
class Shot:
    def __init__(self, t, D):
        self.t, self.D = t, D
        self.mid = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        self.top = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        self.hud = Image.new('RGBA', (W, H), (0, 0, 0, 0))   # captions/labels: fixed to the screen
        # camera = scale s and the world point L that sits at the centre of the screen
        self.zoom, self.lx, self.ly = 1.0, W / 2, H / 2
        self.hits = []
        self.extra = {}                                     # depth -> RGBA layer (see layer())
        self.blur = {'bg': 0.0, 'mid': 0.0, 'top': 0.0}    # rack focus, in px (see rack())
        self.shake = (0.0, 0.0)

    def layer(self, depth):
        """An extra layer at any parallax depth (0.35 = background, 1 = mid, 1.15 = top).
        Depths below 1 sit behind shot.mid, between 1 and 1.15 between mid and top, above 1.15
        in front of top. Use it for foreground props, far cut-outs, a second plane of paper."""
        if depth not in self.extra:
            self.extra[depth] = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        return self.extra[depth]

    def pan(self, at, dx, dy=0.0, dur=2.0):
        """Lateral camera travel of (dx, dy) world px starting at `at` (a dolly across a desk)."""
        k = ease_io((self.t - at) / dur)
        self.lx += dx * k
        self.ly += dy * k

    def drift(self, amp=4.0, period=7.0):
        """Subtle handheld drift: a slow, non-repeating float of a few pixels."""
        t = self.t
        self.lx += amp * (math.sin(t * 2 * math.pi / period) + 0.5 * math.sin(t * 2 * math.pi / (period * 0.43) + 1.3))
        self.ly += amp * 0.6 * (math.cos(t * 2 * math.pi / (period * 1.3)) + 0.4 * math.sin(t * 2 * math.pi / (period * 0.37)))

    def rack(self, at, sharp='mid', amount=5.0, dur=0.8, before=None):
        """Focus shift: from `at` the depths other than `sharp` blur by `amount` px. If `before`
        is given (a depth name), that depth was the sharp one and the focus racks from it."""
        k = ease_io((self.t - at) / dur)
        for name in self.blur:
            target = 0.0 if name == sharp else amount * (0.6 if name == 'bg' else 1.0)
            start = 0.0 if before is None or name == before else amount * (0.6 if name == 'bg' else 1.0)
            self.blur[name] = start + (target - start) * k

    def _hold(self, F, s_new):
        """Change zoom to s_new while point F keeps its current screen position."""
        sx = (F[0] - self.lx) * self.zoom + W / 2
        sy = (F[1] - self.ly) * self.zoom + H / 2
        self.zoom = s_new
        self.lx, self.ly = F[0] - (sx - W / 2) / s_new, F[1] - (sy - H / 2) / s_new

    def camera(self, z0, z1, focus0=(W / 2, H / 2), focus1=None):
        """Slow move across the whole shot: zoom z0->z1 about a focus point drifting focus0->focus1."""
        k = ease_io(self.t / max(self.D, 0.01))
        f1 = focus1 or focus0
        F = (lerp(focus0[0], f1[0], k), lerp(focus0[1], f1[1], k))
        s = lerp(z0, z1, k)
        self.zoom = s
        self.lx, self.ly = F[0] - (F[0] - W / 2) / s, F[1] - (F[1] - H / 2) / s

    def push(self, at, dz, focus=None, dur=1.6):
        """A purposeful push-in when something becomes relevant; the focus point stays put."""
        k = ease_io((self.t - at) / dur)
        if k > 0:
            self._hold(focus or (self.lx, self.ly), self.zoom + dz * k)

    def zoom_to(self, rect, at, dur=1.4, fill=0.92, back_at=None, back_dur=1.2):
        """Camera travels from the full composition into one image (rect = x0, y0, x1, y1),
        optionally pulling back out at back_at."""
        sfx('zoom', at, None, dur=dur)
        k = ease_io((self.t - at) / dur)
        if back_at is not None:
            k *= 1 - ease_io((self.t - back_at) / back_dur)
        if k <= 0:
            return
        cx, cy = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
        st = fill * min(W / (rect[2] - rect[0]), H / (rect[3] - rect[1]))
        self.zoom = lerp(self.zoom, st, k)
        self.lx, self.ly = lerp(self.lx, cx, k), lerp(self.ly, cy, k)

    def hit(self, at):
        self.hits.append(at)


def _xf(img, s, lx, ly, dx=0.0, dy=0.0):
    """Camera: world point (lx, ly) to screen centre at scale s, plus a shake offset."""
    a = 1 / s
    c, f = lx - (W / 2 + dx) * a, ly - (H / 2 + dy) * a
    if abs(s - 1) < 1e-4 and abs(c) < 0.01 and abs(f) < 0.01:
        return img
    coeff = (a, 0, c, 0, a, f)
    if img.mode == 'RGBA':
        return img.convert('RGBa').transform(img.size, Image.AFFINE, coeff, Image.BILINEAR).convert('RGBA')
    return img.transform(img.size, Image.AFFINE, coeff, Image.BILINEAR)


def compose(shot, T):
    z = shot.zoom
    kick = 0.0
    for h in shot.hits:
        if shot.t >= h:
            kick = max(kick, math.exp(-(shot.t - h) * 7.0))
    sx = 7 * kick * math.sin(shot.t * 70)
    sy = 5 * kick * math.cos(shot.t * 53)

    def look(m):  # parallax: each depth travels a fraction m of the camera move
        return 1 + (z - 1) * m, W / 2 + (shot.lx - W / 2) * m, H / 2 + (shot.ly - H / 2) * m
    bs, blx, bly = look(0.35)
    bs = max(bs, 1.0)                              # the background must always cover the frame
    blx = min(max(blx, W / 2 / bs), W - W / 2 / bs)
    bly = min(max(bly, H / 2 / bs), H - H / 2 / bs)
    bg = _blur(_xf(bg_motion.motion_bg(T), bs, blx, bly).convert('RGBA'), shot.blur.get('bg', 0))

    def extra(lo, hi):
        for dpt in sorted(d for d in shot.extra if lo <= d < hi):
            s_, lx_, ly_ = look(dpt)
            bg.alpha_composite(_xf(shot.extra[dpt], max(0.05, s_), lx_, ly_, sx * dpt * 0.6, sy * dpt * 0.6))
    extra(-9, 1.0)
    s, lx, ly = look(1.0)
    bg.alpha_composite(_blur(_xf(shot.mid, s + 0.012 * kick, lx, ly, sx * 0.6, sy * 0.6), shot.blur.get('mid', 0)))
    extra(1.0, 1.15)
    s, lx, ly = look(1.15)
    bg.alpha_composite(_blur(_xf(shot.top, s + 0.02 * kick, lx, ly, sx, sy), shot.blur.get('top', 0)))
    extra(1.15, 99)
    bg.alpha_composite(_xf(shot.hud, 1.0, W / 2, H / 2, sx * 0.3, sy * 0.3))
    return finish(bg)


def _blur(img, px):
    if px < 0.4:
        return img
    if img.mode == 'RGBA':
        return img.convert('RGBa').filter(ImageFilter.GaussianBlur(px)).convert('RGBA')
    return img.filter(ImageFilter.GaussianBlur(px))


# ---------------------------------------------------------------- transitions
_r = np.random.default_rng(5)
_J = np.convolve(_r.normal(0, 1, 2400), np.ones(9) / 9, 'same') * 10 + _r.normal(0, 1, 2400) * 0.9
_YY, _XX = np.mgrid[0:H, 0:W].astype(np.float32)


def _tear(a, b, p, kind):
    """Blend frame a -> b. 'lr'/'rl': torn wipe; 'up': new sheet slides up over the old one."""
    if kind == 'up':
        edge = lerp(H + 60, -60, ease_io(p)) + _J[:W][None, :] * 1.2
        d = _YY - edge                       # >0 below the edge: new sheet
    else:
        e = lerp(-260, W + 260, ease_io(p)) + (_YY - H / 2) * 0.18 + _J[:H][:, None] * 1.4
        d = (e - _XX) if kind == 'lr' else (_XX - (W - e))
    out = a.astype(np.float32)
    new = d > 0
    out[new] = b[new]
    lip = (d > 0) & (d < 14)                 # the torn paper lip
    out[lip] = out[lip] * 0.25 + np.array(PAPER_BACK, np.float32) * 0.75
    sh = (d <= 0) & (d > -34)                # soft shadow cast on the old frame
    out[sh] *= (0.80 + 0.20 * (-d[sh] / 34))[:, None]
    return out.clip(0, 255).astype(np.uint8)


def make_frame(shots, end, t, clips, pre=0.38, post=0.17):
    """shots: list of (start, fn) or (start, fn, kind). fn(t, D) -> Shot. T for the background
    runs continuously across the whole film."""
    T = sum(vox._DUR[c] for c in vox._DUR if c < min(clips)) + t
    starts = [s[0] for s in shots] + [end]
    import transitions as TR

    def cut(j):
        k = shots[j][2] if len(shots[j]) > 2 else ('lr', 'up', 'rl')[j % 3]
        return (k, {}) if isinstance(k, str) else (k[0], k[1] if len(k) > 1 else {})
    for j in range(1, len(shots)):            # transition sounds, at the cut
        kind, opts = cut(j)
        if kind in TR.KINDS:
            event(TR.SOUND[kind], starts[j] - TR.DUR[kind][0] * 0.4, opts.get('at', (W / 2, 0))[0], dur=sum(TR.DUR[kind]))
        else:
            event('sheet' if kind == 'up' else 'wipe', starts[j], W * (0.3 if kind == 'lr' else 0.7 if kind == 'rl' else 0.5))

    def render(j, tt):
        s0, fn = shots[j][0], shots[j][1]
        vox._SCENE_START = s0
        return compose(fn(tt - s0, starts[j + 1] - s0), T)

    i = max(j for j in range(len(shots)) if starts[j] <= t)
    for j in (i, i + 1):
        if not 0 < j < len(shots):
            continue
        kind, opts = cut(j)
        a_, b_ = TR.DUR[kind] if kind in TR.KINDS else (pre, post)
        if starts[j] - a_ <= t < starts[j] + b_:
            p = (t - (starts[j] - a_)) / (a_ + b_)
            if kind in TR.KINDS:
                return TR.apply(kind, render(j - 1, t), render(j, t), p, opts)
            return _tear(render(j - 1, t), render(j, t), p, kind)
    return render(i, t)


# ---------------------------------------------------------------- elements
class Photo:
    """A photograph or painted plate as a torn print: enters with a spring, a settling tilt and
    a slight scale-down, like a print dropped onto the desk."""

    def __init__(self, img, width, rot=-2.0, seed=1, border=16):
        src = vox.fit_w(img.convert('RGB'), width)
        b = border
        card = Image.new('RGBA', (src.width + 2 * b, src.height + 2 * b), CREAM + (255,))
        card.paste(src, (b, b))
        card.putalpha(torn_mask(card.width, card.height, seed))
        self.card, self.rot = card, rot
        self.shadow, self.pad, self.off = shadow_of(card, blur=22, offset=22, opacity=0.30)
        self._cache = None

    def place(self, layer, cx, cy, t, start, frm='up', dist=420, tilt=7.0):
        sfx('drop', start, cx, gain=0.4)
        if t < start:
            return
        p = sp(t, start)
        op = fade(t, start, 0.35)
        dx, dy = {'up': (0, 1), 'left': (-1, 0), 'right': (1, 0), 'down': (0, -1)}[frm]
        ox, oy = dx * (1 - p) * dist, dy * (1 - p) * dist
        ang = self.rot + (1 - p) * tilt * (1 if frm != 'left' else -1)
        sc = lerp(1.07, 1.0, min(p, 1.0))
        if p > 0.999 and self._cache:
            card, sh = self._cache
        else:
            card = self.card.resize((int(self.card.width * sc), int(self.card.height * sc)), Image.BILINEAR).rotate(ang, Image.BICUBIC, expand=True)
            sh = self.shadow.resize((int(self.shadow.width * sc), int(self.shadow.height * sc)), Image.BILINEAR).rotate(ang, Image.BICUBIC, expand=True)
            if p > 0.999:
                self._cache = (card, sh)
        x, y = int(cx - card.width / 2 + ox), int(cy - card.height / 2 + oy)
        layer.alpha_composite(alpha_mul(sh, op * 0.9), (x - (sh.width - card.width) // 2, y - (sh.height - card.height) // 2 + self.off))
        layer.alpha_composite(alpha_mul(card, op), (x, y))


def sheet(layer, img, cx, cy, t, start, rot=0.0, frm='up', dist=420):
    """Documents / covers: same drop-in as Photo (cached per object id)."""
    key = ('_ph', rot)
    ph = getattr(img, '_photo', None)
    if ph is None or ph.rot != rot:
        ph = Photo.__new__(Photo)
        ph.card, ph.rot, ph._cache = img, rot, None
        ph.shadow, ph.pad, ph.off = shadow_of(img, blur=20, offset=18, opacity=0.28)
        img._photo = ph
    ph.place(layer, cx, cy, t, start, frm, dist, tilt=5.0)


def words(layer, xy, s, size, t, times, fill=INK, anchor='m', font=None, gap=0.28):
    """Each word rises out of its own slot as it is spoken. times: one start per word, or a
    single start (words then follow 0.09 s apart)."""
    f = (font or F_HEAD)(size)
    ws = s.split(' ')
    if not isinstance(times, (list, tuple)):
        times = [times + i * 0.09 for i in range(len(ws))]
    d = ImageDraw.Draw(layer)
    widths = [d.textlength(x, font=f) for x in ws]
    total = sum(widths) + gap * size * (len(ws) - 1)
    x = xy[0] - total / 2 if anchor == 'm' else (xy[0] - total if anchor == 'r' else xy[0])
    hh = int(size * 1.35)
    if font is F_TYPE:
        for word, st in zip(ws, times):
            sfx('type', st, xy[0], n=len(word), cps=14)
    for word, wd, st in zip(ws, widths, times):
        if t > st:
            p = min(1.0, sp(t, st))
            tile = Image.new('RGBA', (int(wd) + 8, hh), (0, 0, 0, 0))
            ImageDraw.Draw(tile).text((4, hh * 0.5 + (1 - p) * hh * 0.9), word, font=f, fill=fill + (int(255 * fade(t, st, 0.25)),), anchor='lm')
            layer.alpha_composite(tile, (int(x - 4), int(xy[1] - hh / 2)))
        x += wd + gap * size


def tag(layer, xy, s, size, t, start, bg=RED, fg=CREAM, anchor='m'):
    """A red editorial label: the bar sweeps across, then the words rise inside it."""
    sfx('swipe', start, xy[0])
    if t < start:
        return
    f = F_HEAD(size)
    tw = ImageDraw.Draw(layer).textlength(s, font=f)
    pad = size * 0.35
    w_, h_ = tw + pad * 2, size * 1.45
    x0 = xy[0] - w_ / 2 if anchor == 'm' else xy[0]
    y0 = xy[1] - h_ / 2
    k = ease_out_cubic((t - start) / 0.35)
    ImageDraw.Draw(layer).rectangle((x0, y0, x0 + w_ * k, y0 + h_), fill=bg + (240,))
    words(layer, (x0 + pad, xy[1]), s, size, t, start + 0.18, fill=fg, anchor='l')


def underline(layer, x0, x1, y, t, start, width=9, seed=0):
    sfx('marker', start, (x0 + x1) / 2, dur=0.45)
    vox.marker_line(layer, [(x0, y + 2), ((x0 + x1) / 2, y - 3), (x1, y + 1)], ease_out_cubic((t - start) / 0.45), width, seed=seed)


KICKER_XY = (64, 925)          # per-episode override: style.KICKER_XY = (x, y) where the theme has a clear rule


def kicker(layer, t, n, title, start=0.4, hold=5.5, xy=None):
    """Chapter label resting on the background's bottom-left rule (or at xy / KICKER_XY)."""
    sfx('type', start + 0.25, 200, n=len(title.replace(' ', '')) + 2, cps=30)
    if t < start or t > start + hold + 0.8:
        return
    op = fade(t, start, 0.4) * (1 - ease((t - start - hold) / 0.8))
    ov = Image.new('RGBA', (900, 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.text((0, 35), f'{n:02d}', font=F_HEAD(34), fill=RED + (255,), anchor='lm')
    s = title.upper()
    m = int(min(len(s), max(0, t - start - 0.25) * 30))
    d.text((70, 35), s[:m], font=F_TYPE(30), fill=INK + (255,), anchor='lm')
    layer.alpha_composite(alpha_mul(ov, op), tuple(int(v) for v in (xy or KICKER_XY)))
