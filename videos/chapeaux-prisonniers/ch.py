"""Shared pieces for "L'énigme des chapeaux des prisonniers".

The drawings (PROMPTS.md, G01-G05) come from ChatGPT in a 19th-century wood-engraving style and are
printed in the film's ink on its paper. Until a file is uploaded, a labelled placeholder takes its
place, so uploading assets/G0x.png is all it takes.

The line of ten (G03) is the film's motif. Its ten figures and their heads are measured from the
drawing itself (columns of ink), so the paper hats land on the real heads whatever the drawing.
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from vox import asset, font, W, H, PAL, F_HEAD, F_BODY, F_TYPE, INK, CREAM
import presets as P
import annotate as A
from style import sfx

IMPAIR = PAL.accent          # terracotta: odd
PAIR = PAL.accent2           # teal: even
HAT_BLACK = (30, 28, 26)
HAT_WHITE = (250, 247, 240)


def have(code):
    return os.path.exists(asset(f'{code}.png'))


# ------------------------------------------------------------------ placeholders
def placeholder(size, code, label, figures=0):
    """A plain, clearly labelled stand-in: never passes for the drawing."""
    w, h = size
    im = Image.new('RGBA', size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), fill=(226, 218, 203, 255))
    for x in range(0, w, 28):                                  # dashed frame
        d.line((x, 6, x + 14, 6), fill=(150, 140, 122, 255), width=3)
        d.line((x, h - 7, x + 14, h - 7), fill=(150, 140, 122, 255), width=3)
    for y in range(0, h, 28):
        d.line((6, y, 6, y + 14), fill=(150, 140, 122, 255), width=3)
        d.line((w - 7, y, w - 7, y + 14), fill=(150, 140, 122, 255), width=3)
    d.text((w / 2, 40), f'{code} · {label} · à générer', font=font('Inter600.ttf', max(20, w // 48)),
           fill=(110, 100, 86, 255), anchor='mt')
    return im


def plate(code, label):
    """A full-frame drawing (RGB, 16:9) for S.fullbleed."""
    if have(code):                                             # printed in ink on the film's paper, edge to edge
        import cutout
        ink = cutout.ink_image(asset(f'{code}.png'), 1920)
        base = Image.new('RGBA', (1920, 1080), PAL.paper + (255,))
        base.alpha_composite(ink, (0, (1080 - ink.height) // 2))
        return base.convert('RGB')
    return placeholder((1920, 1080), code, label).convert('RGB')


def drawing(code, width, label, aspect=0.5625):
    """A drawing printed in ink on the paper (RGBA)."""
    if have(code):
        import cutout
        return cutout.ink_image(asset(f'{code}.png'), width)
    return placeholder((width, int(width * aspect)), code, label)


# ------------------------------------------------------------------ the line of ten (G03)
LINE_W = 1640


def _line_placeholder(w):
    """Ten numbered ghost outlines, tallest left: only to place the hats until G03 exists."""
    h = int(w * 0.40)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(10):
        cx = (i + 0.5) * w / 10
        fh = h * (0.92 - 0.30 * i / 9)
        top = h - fh
        r = fh * 0.075
        col = (150, 140, 122, 255)
        d.ellipse((cx - r, top, cx + r, top + 2 * r), outline=col, width=4)
        d.rounded_rectangle((cx - r * 1.25, top + 2.3 * r, cx + r * 1.25, h - 2), radius=int(r), outline=col, width=4)
    return im, _measure(im)


def _measure(im):
    """Ten figures: column runs of ink, then each head's top, centre and width."""
    a = np.asarray(im.split()[-1]).astype(np.float32) / 255
    col = (a > 0.2).sum(0)
    on = col > max(2, 0.004 * a.shape[0])
    runs, x = [], 0
    while x < len(on):
        if on[x]:
            x0 = x
            while x < len(on) and on[x]:
                x += 1
            runs.append([x0, x])
        x += 1
    while len(runs) > 10:                                      # merge the closest neighbours
        gaps = [runs[i + 1][0] - runs[i][1] for i in range(len(runs) - 1)]
        i = int(np.argmin(gaps))
        runs[i] = [runs[i][0], runs[i + 1][1]]
        del runs[i + 1]
    if len(runs) != 10:
        runs = [[int(i * im.width / 10), int((i + 1) * im.width / 10)] for i in range(10)]
    figs = []
    for x0, x1 in runs:
        sub = a[:, x0:x1] > 0.2
        rows = np.where(sub.any(1))[0]
        top, bot = int(rows[0]), int(rows[-1])
        band = sub[top:top + max(6, int((bot - top) * 0.09))]
        xs = np.where(band.any(0))[0]
        hx = x0 + (xs[0] + xs[-1]) / 2 if len(xs) else (x0 + x1) / 2
        hw = (xs[-1] - xs[0]) if len(xs) > 1 else (x1 - x0) * 0.4
        figs.append(dict(x0=x0, x1=x1, top=top, bot=bot, hx=hx, hw=max(hw, (bot - top) * 0.08), h=bot - top))
    return figs


def _line():
    if have('G03'):
        import cutout
        im = cutout.ink_image(asset('G03.png'), LINE_W)
        return im, _measure(im)
    return _line_placeholder(LINE_W)


LINE, FIGS = _line()


def line_size(scale=1.0):
    return int(LINE.width * scale), int(LINE.height * scale)


def head(i, cx, cy, scale=1.0):
    """Screen point at the top of figure i's head, for a LINE drawn centred at (cx, cy)."""
    f = FIGS[i]
    return (cx + (f['hx'] - LINE.width / 2) * scale, cy + (f['top'] - LINE.height / 2) * scale)


def figure(i, scale=1.0):
    """Figure i cut out of the line (RGBA) and its offset from the line's centre."""
    f = FIGS[i]
    pad = 6
    x0, x1 = max(0, f['x0'] - pad), min(LINE.width, f['x1'] + pad)
    im = LINE.crop((x0, 0, x1, LINE.height))
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    return im, ((x0 + x1) / 2 - LINE.width / 2) * scale


def put_line(layer, cx, cy, scale=1.0, only=None, op=1.0):
    """The whole line (or the figures in `only`), flat on the paper."""
    if only is None and scale == 1.0:
        P.put(layer, LINE, cx, cy, op=op, sh_op=0.12)
        return
    for i in (only if only is not None else range(10)):
        im, dx = figure(i, scale)
        P.put(layer, im, cx + dx, cy, op=op, sh_op=0.12)


# ------------------------------------------------------------------ hats
_HATS = {}


_GEN = {}


def _generated_hats():
    """The user's ChatGPT hats (assets/H01.png: black hat left, white hat right, on white).
    Split at the widest empty gap, then the white paper connected to the border is cut away:
    the black outline closes each hat, so the white hat's inside survives."""
    if _GEN or not have('H01'):
        return _GEN
    from scipy import ndimage
    im = Image.open(asset('H01.png')).convert('RGB')
    a = np.asarray(im).astype(np.float32)
    ink = a.mean(2) < 200
    cols = ink.any(0)
    xs = np.where(cols)[0]
    gaps = [(x1 - x0, x0, x1) for x0, x1 in zip(xs[:-1], xs[1:]) if x1 - x0 > 20]
    split = max(gaps)[1] + max(gaps)[0] // 2 if gaps else im.width // 2
    for name, (x0, x1) in (('noir', (0, split)), ('blanc', (split, im.width))):
        sub = a[:, x0:x1]
        light = sub.mean(2) > 225
        lab, _ = ndimage.label(light)
        border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
        bg = np.isin(lab, list(border))
        bg = ndimage.binary_dilation(bg, iterations=1) & (sub.mean(2) > 160)
        rgba = np.dstack([sub, (~bg * 255).astype(np.float32)]).clip(0, 255).astype(np.uint8)
        cut = Image.fromarray(rgba, 'RGBA')
        _GEN[name] = cut.crop(cut.getbbox())
    return _GEN


def hat(colour, w):
    """A hat, cut out: black or white. The user's generated hats when assets/H01.png exists,
    otherwise a drawn stand-in (a paper top hat with an ink edge)."""
    key = (colour, int(w))
    if key in _HATS:
        return _HATS[key]
    gen = _generated_hats()
    if colour in gen:
        g = gen[colour]
        im = g.resize((int(w), max(1, int(g.height * w / g.width))), Image.LANCZOS)
        _HATS[key] = im
        return im
    S = 4
    hw = int(w * S)
    hh = int(w * 0.92 * S)
    im = Image.new('RGBA', (hw + 8 * S, hh + 8 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = 4 * S, 4 * S
    fill = HAT_BLACK if colour == 'noir' else HAT_WHITE
    edge = INK
    lw = int(5.0 * S)
    crown = [(ox + hw * 0.22, oy + hh * 0.06), (ox + hw * 0.78, oy + hh * 0.06),
             (ox + hw * 0.74, oy + hh * 0.80), (ox + hw * 0.26, oy + hh * 0.80)]
    d.polygon(crown, fill=fill + (255,))
    d.ellipse((ox + hw * 0.22, oy, ox + hw * 0.78, oy + hh * 0.13), fill=fill + (255,))
    d.ellipse((ox, oy + hh * 0.72, ox + hw, oy + hh * 0.98), fill=fill + (255,))
    band = (PAL.ink2 if colour == 'blanc' else (70, 64, 58))
    d.polygon([(ox + hw * 0.26, oy + hh * 0.62), (ox + hw * 0.74, oy + hh * 0.62),
               (ox + hw * 0.735, oy + hh * 0.72), (ox + hw * 0.265, oy + hh * 0.72)], fill=band + (255,))
    if colour == 'blanc':                                      # the ink edge that keeps it readable on paper
        d.line(crown[:2], fill=edge + (255,), width=lw)
        d.line([crown[1], crown[2]], fill=edge + (255,), width=lw)
        d.line([crown[3], crown[0]], fill=edge + (255,), width=lw)
        d.arc((ox + hw * 0.22, oy, ox + hw * 0.78, oy + hh * 0.13), 0, 360, fill=edge + (255,), width=lw)
        d.arc((ox, oy + hh * 0.72, ox + hw, oy + hh * 0.98), 0, 360, fill=edge + (255,), width=lw)
    else:                                                      # a soft sheen so black reads as an object
        d.line([(ox + hw * 0.34, oy + hh * 0.12), (ox + hw * 0.32, oy + hh * 0.58)], fill=(78, 72, 66, 255), width=int(4 * S))
    im = im.resize((im.width // S, im.height // S), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    rng = np.random.default_rng(len(_HATS) + 7)
    fib = rng.normal(0, 1, a.shape[:2]).astype(np.float32)
    fib = np.asarray(Image.fromarray(((fib * 30) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32) - 128
    a[..., :3] += fib[..., None] * (0.10 if colour == 'noir' else 0.06)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    _HATS[key] = im
    return im


def unknown_hat(w):
    """The hat its wearer cannot see: a dashed outline with a question mark."""
    key = ('?', int(w))
    if key in _HATS:
        return _HATS[key]
    base = hat('blanc', w)
    a = np.asarray(base).astype(np.float32)
    a[..., :3] = np.array(PAL.paper2, np.float32)
    a[..., 3] *= 0.92
    im = Image.fromarray(a.astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(im)
    d.text((im.width / 2, im.height * 0.47), '?', font=F_HEAD(int(w * 0.48)), fill=PAL.muted + (255,), anchor='mm')
    _HATS[key] = im
    return im


def hat_w(i, scale=1.0):
    return FIGS[i]['hw'] * 1.55 * scale


def hat_at(i, cx, cy, scale=1.0):
    """Centre of the hat sitting on figure i."""
    hx, hy = head(i, cx, cy, scale)
    w = hat_w(i, scale)
    if _generated_hats():                                      # brim bottom a little below the top of the head
        h = hat('noir', w).height
        return hx, hy + 0.22 * w - h / 2
    return hx, hy - w * 0.92 * 0.16


def place_hat(layer, i, colour, cx, cy, t, start, scale=1.0, drop=True, seed=0):
    """Put (or drop, on its word) a hat on figure i of a line centred at (cx, cy)."""
    w = hat_w(i, scale)
    im = hat(colour, w) if colour in ('noir', 'blanc') else unknown_hat(w)
    x, y = hat_at(i, cx, cy, scale)
    rot = [-4, 2, -1.5, 3, -2.5, 1, -3, 2.5, -1, 1.5][(i + seed) % 10]
    if not drop:
        if t >= start:
            P.put(layer, P.rot_scale(im, rot, 1.0), x, y, sh_op=0.18)
        return
    P.drop(layer, im, x, y, t, start, rot=rot, spin=10, height=0.6, key=f'hat{colour}{i}{int(w)}', from_y=-90)


def flip_hat(layer, i, colour, cx, cy, t, start, scale=1.0):
    """The '?' turns over to show the hat's colour."""
    w = hat_w(i, scale)
    x, y = hat_at(i, cx, cy, scale)
    P.flip(layer, unknown_hat(w), hat(colour, w), x, y, t, start, dur=0.7)


# ------------------------------------------------------------------ marks of the demonstration
def cone(layer, eye, x_end, y_top, y_bot, t, start, colour=IMPAIR, dur=0.7, until=None, alpha=0.20):
    """The line of sight: a translucent wedge from the eye over the heads in front."""
    if t < start:
        return
    k = A.life(t, start, until, 'fade')
    u = P.ease_io((t - start) / dur)
    xe = eye[0] + (x_end - eye[0]) * u
    yt = eye[1] + (y_top - eye[1]) * u
    yb = eye[1] + (y_bot - eye[1]) * u
    over = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    d.polygon([eye, (xe, yt), (xe, yb)], fill=colour + (int(255 * alpha * k),))
    d.line([eye, (xe, yt)], fill=colour + (int(200 * k),), width=3)
    d.line([eye, (xe, yb)], fill=colour + (int(200 * k),), width=3)
    layer.alpha_composite(over)
    if abs(t - start) < 1 / 30:
        sfx('whoosh', start, eye[0], gain=0.3)


def bubble(text, size=56, dark=False, blank=False):
    """A speech bubble, typed: « noir », « blanc »."""
    f = F_BODY(size)
    tw = f.getlength(text)
    w, h = int(tw + size * 1.4), int(size * 1.9)
    im = Image.new('RGBA', (w + 8, h + int(size * 0.7) + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bg = PAL.light if not dark else PAL.light
    d.rounded_rectangle((4, 4, w + 4, h + 4), radius=int(h * 0.45), fill=bg + (255,), outline=INK + (255,), width=4)
    d.polygon([(w * 0.22, h), (w * 0.16, h + size * 0.62), (w * 0.38, h)], fill=bg + (255,))
    d.line([(w * 0.22, h + 2), (w * 0.16, h + size * 0.62), (w * 0.38, h + 2)], fill=INK + (255,), width=4)
    if not blank:
        d.text((w / 2 + 4, h / 2 + 4), text, font=f, fill=INK + (255,), anchor='mm')
    return im


def pop_in(layer, im, cx, cy, t, start, dur=0.35, until=None, sound=True):
    """A card or bubble that pops into place with a small overshoot."""
    if sound and t >= start - 1 / 30 and t < start + 1 / 30:
        sfx('pop', start, cx)
    if t < start:
        return
    k = A.life(t, start, until, 'fade') if until is not None else 1.0
    u = P.clamp01((t - start) / dur)
    sc = 0.6 + 0.4 * P.damped(u, 0.45, 1.2)
    P.put(layer, P.rot_scale(im, 0, sc), cx, cy, op=min(1.0, u * 3) * k, sh_op=0.18)


def note_card(lines, size=46, w=None, colour=(240, 220, 170), seed=41):
    """A small handwritten-looking note (typed face) on coloured paper."""
    f = F_TYPE(size)
    tw = max(f.getlength(s) for s in lines)
    w = w or int(tw + size * 1.6)
    h = int(size * (1.5 * len(lines) + 1.2))
    card = P.paper_card(w, h, seed=seed, colour=colour)
    d = ImageDraw.Draw(card)
    for k, s in enumerate(lines):
        d.text((w / 2, size * (1.2 + 1.5 * k)), s, font=f, fill=INK + (255,), anchor='mm')
    return card


# ------------------------------------------------------------------ the hats of the film
# act 1's last line-up (act1.HATS_NEXT), seen again at the start of act 2
SHOWN = ['blanc', 'noir', 'noir', 'blanc', 'blanc', 'noir', 'blanc', 'noir', 'blanc', 'blanc']
# the narration's example (clips 14-20), from the back of the line (1, the tallest) to the front (10, « vous »):
# 1 sees 3 black (3, 4, 10) and says « noir » (wrong: his is white); 2 white; 3 and 4 black; 5-9 white; 10 black
EXAMPLE = ['blanc', 'blanc', 'noir', 'noir', 'blanc', 'blanc', 'blanc', 'blanc', 'blanc', 'noir']
