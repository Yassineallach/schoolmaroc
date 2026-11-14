"""Channel branding and calls to action: the same channel in every video, the video's own
identity everywhere else.

Configuration: SK/brand/brand.json (the channel), overridden per video by episode.json "brand".
Logo: SK/brand/logo.svg, the official file, rendered with cairosvg at the exact pixel size of
each use (sharp at any size, transparency kept, never redrawn, recoloured or distorted). Official
light/dark variants are used when supplied ("on_dark", "on_light"); otherwise a soft paper plate
sits behind the logo on a ground it would not read on. Until logo.svg exists, nothing is drawn in
a real render (a placeholder can never reach a film); demos pass force=True.

What it provides
  logo(width)                          the official logo as RGBA at that width
  signature(layer, x, y, t, start)     the brand's small editorial mark: a rule that draws, a square
  reveal(layer, cx, cy, width, t, start, style=)  the animated logo reveal (mask | scale | assemble)
  watermark                            drawn by overlay(): selective, configurable, fades with the shots
  cta_subscribe / cta_like / cta_comment / cta_share / cta_next   the five call-to-action cards
  plan()                               where CTAs go in this film, read from the narration's pauses
  overlay(frame, T, shot, ...)         called by style.make_frame on every finished frame
  outro_scene(t, D)                    the end screen, a Shot for the last act: (cue.total + 0.4, brand.outro_scene)
  endscreen_slots()                    the rectangles YouTube's end-screen elements go on (also out/endscreen.json)

Language: texts come from brand.json "text"[lang] where lang is episode.json "lang".
"""
import glob
import io
import json
import math
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import vox
from vox import W, H, PAL, font, alpha_mul

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAND_DIR = os.path.join(HERE, 'brand')
PROJECT = vox.PROJECT


# ------------------------------------------------------------------ configuration
def _merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = _merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def _load():
    base = json.load(open(os.path.join(BRAND_DIR, 'brand.json'), encoding='utf-8'))
    ep_path = os.path.join(PROJECT, 'episode.json')
    ep = json.load(open(ep_path, encoding='utf-8')) if os.path.exists(ep_path) else {}
    cfg = _merge(base, ep.get('brand', {}))
    cfg['_lang'] = ep.get('lang', 'en')
    return cfg


CFG = _load()
LANG = CFG['_lang'] if CFG['_lang'] in CFG['text'] else 'en'
TXT = CFG['text'][LANG]
RTL = LANG == 'ar'


def _logo_path(key='file'):
    f = CFG['logo'].get(key)
    if not f:
        return None
    p = f if os.path.isabs(f) else os.path.join(BRAND_DIR, f)
    if not os.path.exists(p):
        p = os.path.join(PROJECT, f)
    return p if os.path.exists(p) else None


OFFICIAL = _logo_path('file')
PLACEHOLDER = os.path.join(BRAND_DIR, CFG['logo']['placeholder'])
ACTIVE = bool(CFG.get('enabled', True) and OFFICIAL)        # real renders draw nothing without the official logo


def _font(role, size):
    return font(CFG['typography'][role], int(size))


def _col(key, default):
    c = CFG['colors'].get(key)
    if c:
        c = c.lstrip('#')
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    return default


CTA_FILL = _col('cta', PAL.accent)            # the video's accent unless the channel defines one
CTA_TEXT = _col('cta_text', PAL.light)
INK = PAL.ink
PAPER = PAL.light


# ------------------------------------------------------------------ the logo
_LOGO = {}


def _svg(path, width):
    import cairosvg
    png = cairosvg.svg2png(url=path, output_width=int(width))
    return Image.open(io.BytesIO(png)).convert('RGBA')


def logo(width, variant=None, force=False):
    """The official logo at `width` px (aspect kept). variant: None | 'on_dark' | 'on_light'."""
    path = (variant and _logo_path(variant)) or OFFICIAL or (PLACEHOLDER if force else None)
    if path is None:
        return None
    w = max(8, int(round(width / 2.0) * 2))
    key = (path, w)
    if key not in _LOGO:
        _LOGO[key] = _svg(path, w) if path.endswith('.svg') else _raster(path, w)
    return _LOGO[key]


def _raster(path, w):
    im = Image.open(path).convert('RGBA')
    return im.resize((w, max(1, round(im.height * w / im.width))), Image.LANCZOS)


def _logo_lum(im):
    a = np.asarray(im, np.float32)
    m = a[..., 3] > 40
    return float((a[..., :3][m] @ [0.299, 0.587, 0.114]).mean()) if m.any() else 128.0


def _ground_of(layer, box, default=230.0):
    """The tone under box on a layer that may be transparent (a HUD layer): measured where the
    layer is opaque, else `default` (the grounds are light unless a scene says otherwise)."""
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(layer.width, x1), min(layer.height, y1)
    if x1 <= x0 or y1 <= y0:
        return default
    reg = layer.crop((x0, y0, x1, y1))
    if reg.mode == 'RGBA' and np.asarray(reg.getchannel('A')).mean() < 128:
        return default
    return float(np.asarray(reg.convert('L'), np.float32).mean())


def _lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _clash(im, ground):
    """True when a real part of the logo (a quarter of its ink or more) is too close in tone to the
    ground to read: e.g. a cream 'Lab' on cream paper, even if the orange 'AX' would read."""
    a = np.asarray(im, np.float32)
    m = a[..., 3] > 120
    if not m.any():
        return False
    lum = a[..., :3][m] @ [0.299, 0.587, 0.114]
    return float((np.abs(lum - ground) < 75).mean()) > 0.25


def _ground_lum(base, box):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0:
        return 200.0
    a = np.asarray(base.crop((x0, y0, x1, y1)).convert('L'), np.float32)
    return float(a.mean())


def place_logo(img, x, y, width, op=1.0, force=False, plate=None, anchor='lt', ground=None):
    """Composite the logo onto img (RGBA) with readability handled: an official variant for the
    ground if there is one, else a soft plate behind it when logo and ground are too close."""
    base = logo(width, force=force)
    if base is None or op <= 0:
        return None
    w_, h_ = base.size
    if anchor == 'mm':
        x, y = x - w_ / 2, y - h_ / 2
    elif anchor == 'rt':
        x = x - w_
    g = ground if ground is not None else _ground_lum(img, (x, y, x + w_, y + h_))   # pass `ground` when drawing on a transparent layer
    dark_ground = g < 110
    variant = 'on_dark' if dark_ground else 'on_light'
    im = logo(width, variant, force) if _logo_path(variant) else base
    need = plate if plate is not None else (CFG['logo']['plate'] == 'auto' and _clash(im, g))
    if need:
        pad = max(8, int(h_ * 0.30))
        pl = Image.new('RGBA', (w_ + 2 * pad, h_ + 2 * pad), (0, 0, 0, 0))
        pc = CFG['logo'].get('plate_color')
        col = tuple(int(pc.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) if pc else (PAPER if _logo_lum(im) < 128 else PAL.dark)
        ImageDraw.Draw(pl).rounded_rectangle((0, 0, pl.width - 1, pl.height - 1), radius=max(3, pad // 3), fill=col + (int(255 * CFG['logo']['plate_opacity']),))
        img.alpha_composite(alpha_mul(pl, op), (int(x - pad), int(y - pad)))
    img.alpha_composite(alpha_mul(im, op), (int(x), int(y)))
    return (x, y, x + w_, y + h_)


# ------------------------------------------------------------------ motion helpers (the engine's easing)
def _c(x):
    return min(max(x, 0.0), 1.0)


def _eo(x):
    x = _c(x)
    return 1 - (1 - x) ** 3


def _eio(x):
    x = _c(x)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def _life(t, start, dur, enter=None, exit_=None):
    """0..1 presence of an element living [start, start + dur]: eased in, eased out."""
    a = CFG['animation']
    enter, exit_ = enter or a['enter'], exit_ or a['exit']
    if t < start or t > start + dur:
        return 0.0
    return min(_eo((t - start) / enter), _eio((start + dur - t) / exit_))


def _ink_for(img, box):
    return PAPER if _ground_lum(img, box) < 110 else INK


def _sound(kind, T, x, gain=1.0):
    if not CFG['sounds']['enabled']:
        return
    import style
    style.EVENTS[(kind, round(T, 3), round(x))] = {'gain': gain * CFG['sounds']['gain']}


def voice_file(kind):
    """The recorded line for a CTA (episode.json brand.cta.voice.<kind>), converted once to the
    mixer's format; None when no line is configured. Nothing is ever spoken unless recorded."""
    f = CFG['cta'].get('voice', {}).get(kind)
    if not f:
        return None
    src = f if os.path.isabs(f) else os.path.join(PROJECT, f)
    if not os.path.exists(src):
        return None
    import sfx, subprocess
    dst = os.path.join(PROJECT, 'out', f'_brand_voice_{kind}.wav')
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', src, '-ac', '2', '-ar', str(sfx.SR), '-c:a', 'pcm_s16le', dst], check=True)
    return dst


def voice_seconds(kind):
    f = voice_file(kind)
    if not f:
        return 0.0
    import wave
    with wave.open(f) as w:
        return w.getnframes() / w.getframerate()


def _voice(kind, T):
    f = voice_file(kind)
    if f:
        import style
        style.EVENTS[('voice', round(T, 3), 960)] = {'file': f}


# ------------------------------------------------------------------ signature
def signature(layer, x, y, t, start, length=None, colour=None, dur=0.6, op=1.0, rtl=None):
    """The brand's small editorial mark: a fine rule drawing out from (x, y) and a small solid
    square at its end. Accompanies the logo; never competes with it."""
    sg = CFG['signature']
    length = length or sg['length']
    colour = colour or _col('signature', PAL.accent)
    rtl = RTL if rtl is None else rtl
    p = _eo((t - start) / dur)
    if p <= 0 or op <= 0:
        return
    ov = Image.new('RGBA', (int(length + sg['gap'] + sg['square'] + 8), sg['square'] + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    cy = ov.height / 2
    L = length * p
    d.rectangle((0, cy - sg['width'] / 2, L, cy + sg['width'] / 2), fill=colour + (255,))
    q = _eo((t - start - dur * 0.6) / 0.35)
    if q > 0:
        s = sg['square'] * q
        x0 = length + sg['gap']
        d.rectangle((x0, cy - s / 2, x0 + s, cy + s / 2), fill=colour + (255,))
    if rtl:
        ov = ov.transpose(Image.FLIP_LEFT_RIGHT)
        x -= ov.width
    layer.alpha_composite(alpha_mul(ov, op), (int(x), int(y - cy)))


# ------------------------------------------------------------------ animated logo reveal
def reveal(layer, cx, cy, width, t, start, style=None, hold=None, exit_dur=0.6, force=False, signature_under=True, T=None, ground=None):
    """Logo reveal centred on (cx, cy). style: 'mask' (a clean wipe behind a moving edge),
    'scale' (opacity + 0.94 -> 1 settle), 'assemble' (four fine rules close in, then the logo).
    hold=None keeps it on screen; otherwise it exits gently after `hold` seconds."""
    style = style or CFG['animation']['reveal']
    dur = CFG['animation']['reveal_dur']
    im = logo(width, force=force)
    if im is None or t < start:
        return
    if T is not None:
        _sound('reveal', T, cx, 0.5)
    k = 1.0
    if hold is not None:
        k = 1 - _eio((t - start - dur - hold) / exit_dur)
        if k <= 0:
            return
    w_, h_ = im.size
    x0, y0 = cx - w_ / 2, cy - h_ / 2
    if ground is None:
        ground = _ground_of(layer, (x0, y0, x0 + w_, y0 + h_))
    u = _c((t - start) / dur)
    tmp = Image.new('RGBA', layer.size, (0, 0, 0, 0))
    if style == 'scale':
        s = 0.94 + 0.06 * _eo(u)
        place_logo(tmp, cx, cy, width * s, op=_eo(u * 1.4), force=force, anchor='mm', ground=ground)
    elif style == 'assemble':
        d = ImageDraw.Draw(tmp)
        col = _ink_for(layer.convert('RGBA') if layer.mode != 'RGBA' else layer, (x0, y0, x0 + w_, y0 + h_))
        g = 40 * (1 - _eo(u / 0.6))
        a = int(255 * (1 - _eo((u - 0.55) / 0.45)))
        if a > 0:
            for (xa, ya, xb, yb) in ((x0 - 30 - g, y0 - 18, x0 + w_ * 0.35 - g, y0 - 18), (x0 + w_ * 0.65 + g, y0 - 18, x0 + w_ + 30 + g, y0 - 18),
                                     (x0 - 30 - g, y0 + h_ + 18, x0 + w_ * 0.35 - g, y0 + h_ + 18), (x0 + w_ * 0.65 + g, y0 + h_ + 18, x0 + w_ + 30 + g, y0 + h_ + 18)):
                d.line((xa, ya, xb, yb), fill=col + (a,), width=2)
        place_logo(tmp, cx, cy, width, op=_eo((u - 0.35) / 0.5), force=force, anchor='mm', ground=ground)
    else:                                                   # mask: the logo appears behind a soft moving edge
        place_logo(tmp, cx, cy, width, op=1.0, force=force, anchor='mm', ground=ground)
        m = Image.new('L', layer.size, 0)
        edge = x0 - 40 + (w_ + 80) * _eio(u)
        if RTL:
            ImageDraw.Draw(m).rectangle((W - (W - (x0 + w_ + 40)) - (w_ + 80) * _eio(u), 0, W, H), fill=255)
        else:
            ImageDraw.Draw(m).rectangle((0, 0, edge, H), fill=255)
        m = m.filter(ImageFilter.GaussianBlur(10))
        tmp.putalpha(Image.fromarray(np.minimum(np.asarray(tmp.getchannel('A')), np.asarray(m))))
        if u < 1:
            ImageDraw.Draw(tmp).rectangle((edge - 1, y0 - 6, edge + 1, y0 + h_ + 6), fill=PAL.accent + (int(200 * (1 - u)),))
    layer.alpha_composite(alpha_mul(tmp, k))
    if signature_under:
        below = h_ / 2 + (int(h_ * 0.30) + 22 if _clash(im, ground) else 26)          # clear of the plate when there is one
        signature(layer, cx - (CFG['signature']['length'] + CFG['signature']['gap'] + CFG['signature']['square']) / 2, cy + below,
                  t, start + dur * 0.7, op=k)


# ------------------------------------------------------------------ icons (drawn at 4x, line style of the annotations)
def _icon(kind, size, colour, fill=None, p=1.0):
    S = 4
    n = int(size * S)
    im = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lw = max(2, int(n * 0.07))
    c = colour + (255,)
    if kind == 'bell':
        d.chord((n * .2, n * .12, n * .8, n * .8), 180, 360, outline=c, width=lw)
        d.line((n * .2, n * .46, n * .2, n * .68), fill=c, width=lw)
        d.line((n * .8, n * .46, n * .8, n * .68), fill=c, width=lw)
        d.line((n * .12, n * .7, n * .88, n * .7), fill=c, width=lw)
        d.ellipse((n * .42, n * .74, n * .58, n * .9), fill=c)
    elif kind == 'thumb':
        pts = [(n * .3, n * .45), (n * .48, n * .14), (n * .58, n * .2), (n * .54, n * .4), (n * .82, n * .4), (n * .86, n * .48),
               (n * .78, n * .84), (n * .3, n * .84)]
        if fill:
            d.polygon(pts, fill=fill + (int(255 * p),))
            d.rectangle((n * .1, n * .45, n * .24, n * .84), fill=fill + (int(255 * p),))
        d.line(pts + [pts[0]], fill=c, width=lw, joint='curve')
        d.rectangle((n * .1, n * .45, n * .24, n * .84), outline=c, width=lw)
    elif kind == 'bubble':
        d.rounded_rectangle((n * .08, n * .14, n * .92, n * .7), radius=n * .14, outline=c, width=lw)
        d.polygon([(n * .26, n * .66), (n * .22, n * .9), (n * .46, n * .68)], fill=c)
    elif kind == 'share':
        a, b, e = (n * .26, n * .5), (n * .74, n * .24), (n * .74, n * .76)
        d.line([a, b], fill=c, width=lw)
        d.line([a, e], fill=c, width=lw)
        for q in (a, b, e):
            d.ellipse((q[0] - n * .1, q[1] - n * .1, q[0] + n * .1, q[1] + n * .1), fill=c)
    elif kind == 'play':
        d.polygon([(n * .3, n * .2), (n * .82, n * .5), (n * .3, n * .8)], fill=c)
    elif kind == 'check':
        d.line([(n * .18, n * .52), (n * .42, n * .76), (n * .84, n * .26)], fill=c, width=int(lw * 1.3), joint='curve')
    return im.resize((int(size), int(size)), Image.LANCZOS)


def _shadow(card, blur=14, off=8, op=0.22):
    a = card.getchannel('A').point(lambda v: int(v * op))
    sh = Image.new('RGBA', (card.width + 4 * blur, card.height + 4 * blur), (0, 0, 0, 0))
    m = Image.new('L', sh.size, 0)
    m.paste(a, (2 * blur, 2 * blur))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(blur)))
    return sh, 2 * blur - off


def _card(w, h, colour=None, radius=12):
    c = Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0))
    ImageDraw.Draw(c).rounded_rectangle((0, 0, c.width - 1, c.height - 1), radius=radius, fill=(colour or PAPER) + (255,))
    return c


def _put_card(layer, card, x, y, k, rise=None):
    """A card arriving: soft rise and opacity, its shadow growing with it (paper settling)."""
    if k <= 0:
        return
    rise = CFG['animation']['rise'] if rise is None else rise
    sh, o = _shadow(card)
    yy = y + rise * (1 - k)
    layer.alpha_composite(alpha_mul(sh, k), (int(x - o), int(yy - o + 4)))
    layer.alpha_composite(alpha_mul(card, k), (int(x), int(yy)))


def _text(d, xy, s, f, fill, anchor='la'):
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def _wrap(s, f, width):
    words, lines, cur = [x for x in s.split(' ') if x], [], ''          # plain spaces only: non-breaking spaces hold
    for w_ in words:
        nxt = (cur + ' ' + w_).strip()
        if f.getlength(nxt) <= width or not cur:
            cur = nxt
        else:
            lines.append(cur)
            cur = w_
    return lines + [cur] if cur else lines


# ------------------------------------------------------------------ the CTAs
def cta_subscribe(layer, x, y, t, start, dur=4.2, T0=None, force=False, show_logo=True, bell=True):
    """A refined subscribe card: the logo, the channel name if configured, a quiet button that is
    pressed once (it turns to 'Abonné' with a drawn tick), a bell that rings twice, then a clean exit."""
    k = _life(t, start, dur)
    if k <= 0:
        return
    f = _font('label', 26)
    lab, done = TXT['subscribe'], TXT['subscribed']
    bw = int(max(f.getlength(lab), f.getlength(done) + 34) + 56)
    lg = logo(150, force=force) if show_logo else None
    lw_ = lg.width if lg is not None else 0
    name = CFG.get('channel_name') if lg is None else None          # the logo already names the channel
    nf = _font('title', 30)
    nw = int(nf.getlength(name)) if name else 0
    w_ = 28 + (lw_ + 22 if lg is not None else 0) + max(nw, 0) + (22 if name else 0) + bw + (64 if bell else 0) + 24
    h_ = max(84, (lg.height if lg is not None else 0) + 36)
    card = _card(w_, h_)
    d = ImageDraw.Draw(card)
    cx = 28
    if lg is not None:
        box = place_logo(card, cx + 6, (h_ - lg.height) // 2, lg.width, force=force, ground=_lum(PAPER))
        cx += lw_ + 22 + (12 if box and _clash(lg, _lum(PAPER)) else 0)
    if name:
        _text(d, (cx, h_ / 2), name, nf, INK + (255,), 'lm')
        cx += nw + 22
    press = start + 1.35
    pz = _c((t - press) / 0.22)
    pressed = t >= press + 0.11
    s = 1 - 0.05 * math.sin(math.pi * pz)
    bh = 54
    bx0, by0 = cx, (h_ - bh) / 2
    btn = Image.new('RGBA', (bw * 4, bh * 4), (0, 0, 0, 0))
    bd = ImageDraw.Draw(btn)
    fill = tuple(int(a + (b - a) * _eo((t - press - 0.1) / 0.3)) for a, b in zip(CTA_FILL, PAL.muted))
    bd.rounded_rectangle((0, 0, btn.width - 1, btn.height - 1), radius=bh * 2, fill=fill + (255,))
    btn = btn.resize((bw, bh), Image.LANCZOS)
    bdd = ImageDraw.Draw(btn)
    if pressed:
        tick = _icon('check', 26, CTA_TEXT)
        btn.alpha_composite(tick, (22, (bh - 26) // 2))
        _text(bdd, (22 + 32, bh / 2), done, f, CTA_TEXT + (255,), 'lm')
    else:
        _text(bdd, (bw / 2, bh / 2), lab, f, CTA_TEXT + (255,), 'mm')
    if s != 1:
        btn = btn.resize((int(bw * s), int(bh * s)), Image.LANCZOS)
    card.alpha_composite(btn, (int(bx0 + bw * (1 - s) / 2), int(by0 + bh * (1 - s) / 2)))
    if bell:
        ring = t - (press + 0.45)
        ang = 16 * math.exp(-max(ring, 0) * 3.2) * math.sin(max(ring, 0) * 15) if ring > 0 else 0
        b = _icon('bell', 36, INK).rotate(ang, Image.BICUBIC, center=(18, 4))
        card.alpha_composite(b, (int(bx0 + bw + 20), int((h_ - 36) / 2)))
    if T0 is not None:
        _sound('tick', T0 + (press - start) + 0.05, x + bx0, 0.8)
    _put_card(layer, card, x, y, k)
    return w_, h_


def cta_like(layer, x, y, t, start, dur=3.2, T0=None):
    """An outlined thumb that fills with the accent once, a small settle, and one short line."""
    k = _life(t, start, dur)
    if k <= 0:
        return
    f = _font('body', 30)
    msg = CFG['cta'].get('like_text') or TXT['like']
    w_ = int(f.getlength(msg)) + 28 + 50 + 22 + 30
    card = _card(w_, 84)
    d = ImageDraw.Draw(card)
    u = _c((t - start - 0.7) / 0.35)
    pulse = 1 + 0.10 * math.sin(math.pi * u)
    ic = _icon('thumb', 50 * pulse, INK, fill=CTA_FILL, p=_eo(u))
    card.alpha_composite(ic, (int(28 + (50 - ic.width) / 2), int((84 - ic.height) / 2)))
    _text(d, (28 + 50 + 22, 42), msg, f, INK + (255,), 'lm')
    if T0 is not None:
        _sound('pop', T0 + 0.75, x + 50, 0.6)
    _put_card(layer, card, x, y, k)


def cta_comment(layer, x, y, t, start, dur=4.0, question=None, width=780, T0=None):
    """A comment card: a speech-bubble icon, the label, and the video's own question, set in the
    channel's serif and revealed line by line."""
    k = _life(t, start, dur)
    if k <= 0:
        return
    q = question or comment_question()
    lf, qf = _font('label', 22), _font('title', 40)
    lines = _wrap(q, qf, width - 64)
    lh = 52
    h_ = 30 + 34 + 16 + lh * len(lines) + 30
    card = _card(width, h_)
    d = ImageDraw.Draw(card)
    card.alpha_composite(_icon('bubble', 34, PAL.accent), (32, 28))
    _text(d, (32 + 46, 45), TXT['comment_label'].upper(), lf, PAL.muted + (255,), 'lm')
    for i, ln in enumerate(lines):
        p = _eo((t - start - 0.35 - 0.18 * i) / 0.5)
        if p <= 0:
            continue
        tile = Image.new('RGBA', (width, lh + 10), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((32, 4 + (1 - p) * 18), ln, font=qf, fill=INK + (255,))
        m = Image.new('L', tile.size, 0)
        ImageDraw.Draw(m).rectangle((0, 0, width, lh + 10), fill=int(255 * p))
        card.alpha_composite(Image.composite(tile, Image.new('RGBA', tile.size, (0, 0, 0, 0)), m), (0, 30 + 34 + 16 + i * lh - 6))
    if T0 is not None:
        _sound('pop', T0 + 0.2, x + 60, 0.5)
    _put_card(layer, card, x, y, k)
    return width, h_


def cta_share(layer, x, y, t, start, dur=3.0, T0=None):
    """Three nodes joined by lines that draw out from the first: sharing, in the line style."""
    k = _life(t, start, dur)
    if k <= 0:
        return
    f = _font('body', 30)
    msg = TXT['share']
    w_ = int(f.getlength(msg)) + 28 + 46 + 22 + 30
    card = _card(w_, 84)
    d = ImageDraw.Draw(card)
    u = _eo((t - start - 0.4) / 0.6)
    a, b, e = (28 + 12, 42), (28 + 38, 24), (28 + 38, 60)
    for q in (b, e):
        d.line([a, (a[0] + (q[0] - a[0]) * u, a[1] + (q[1] - a[1]) * u)], fill=PAL.accent + (255,), width=3)
    for i, q in enumerate((a, b, e)):
        r = 7 * (1 if i == 0 else _eo((t - start - 0.7 - 0.1 * i) / 0.25))
        if r > 0:
            d.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=PAL.accent + (255,))
    _text(d, (28 + 46 + 22, 42), msg, f, INK + (255,), 'lm')
    _put_card(layer, card, x, y, k)


def _thumb_slot(w_, h_, img=None, t=0.0, start=0.0):
    """A 16:9 slot: the thumbnail when there is one, else a quiet placeholder (paper, fine frame,
    a small play mark) that YouTube's end-screen element will cover."""
    slot = Image.new('RGBA', (w_, h_), (0, 0, 0, 0))
    if img is not None:
        im = img.convert('RGB')
        r = max(w_ / im.width, h_ / im.height)
        im = im.resize((int(im.width * r + 1), int(im.height * r + 1)), Image.LANCZOS)
        im = im.crop(((im.width - w_) // 2, (im.height - h_) // 2, (im.width - w_) // 2 + w_, (im.height - h_) // 2 + h_))
        slot.paste(im, (0, 0))
    else:
        ImageDraw.Draw(slot).rectangle((0, 0, w_ - 1, h_ - 1), fill=PAL.dark + (34,))
        pl = _icon('play', 54, PAL.dark)
        slot.alpha_composite(alpha_mul(pl, 0.35), ((w_ - 54) // 2, (h_ - 54) // 2))
    return slot


def _frame_draw(layer, box, t, start, colour, width=2, dur=0.9):
    """A fine frame drawn around a slot, corner to corner (the annotation pen, no tremor)."""
    p = _eio((t - start) / dur)
    if p <= 0:
        return
    x0, y0, x1, y1 = box
    per = 2 * (x1 - x0) + 2 * (y1 - y0)
    L = per * p
    d = ImageDraw.Draw(layer)
    segs = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    for a, b in segs:
        sl = math.hypot(b[0] - a[0], b[1] - a[1])
        if L <= 0:
            break
        f_ = min(1.0, L / sl)
        d.line([a, (a[0] + (b[0] - a[0]) * f_, a[1] + (b[1] - a[1]) * f_)], fill=colour + (255,), width=width)
        L -= sl


def cta_next(layer, box, t, start, title=None, thumbnail=None, label=True, T0=None, dur=None, colour=None):
    """Next-video card: the slot (thumbnail or placeholder), a frame that draws around it, the
    label above and the title under it."""
    k = 1.0 if dur is None else _life(t, start, dur)
    if t < start or k <= 0:
        return
    x0, y0, x1, y1 = [int(v) for v in box]
    img = None
    if thumbnail:
        p = thumbnail if os.path.isabs(thumbnail) else os.path.join(PROJECT, thumbnail)
        img = Image.open(p) if os.path.exists(p) else None
    slot = _thumb_slot(x1 - x0, y1 - y0, img)
    op = _eo((t - start - 0.2) / 0.6) * k
    layer.alpha_composite(alpha_mul(slot, op), (x0, y0))
    col = colour or _ink_for(layer, (x0, y0 - 60, x1, y0))
    _frame_draw(layer, (x0 - 8, y0 - 8, x1 + 8, y1 + 8), t, start, col, 2)
    lf = _font('label', 22)
    d = ImageDraw.Draw(layer)
    if label:
        a = int(255 * _eo((t - start - 0.4) / 0.5) * k)
        txt = label if isinstance(label, str) else TXT['next_label']
        d.text((x0, y0 - 26), txt.upper(), font=lf, fill=col + (a,), anchor='ls')
    if title:
        tf = _font('title', 30)
        a = int(255 * _eo((t - start - 0.7) / 0.5) * k)
        d.text((x0, y1 + 22), title, font=tf, fill=col + (a,), anchor='la')
    if T0 is not None:
        _sound('pencil', T0, x0, 0.4)


# ------------------------------------------------------------------ the comment question
_TEMPLATES = {
    'fr': {'history_archive': 'Quelle période de l’histoire aimeriez-vous que l’on explore ensuite ?',
           'science_space': 'Quelle question sur l’univers aimeriez-vous voir expliquée ensuite ?',
           'philosophy': 'Et vous, où s’arrête votre imagination ?',
           'manga_ink': 'Quelle œuvre aimeriez-vous que l’on analyse ensuite ?'},
    'en': {'history_archive': 'Which period of history should we explore next?',
           'science_space': 'Which question about the universe should we explain next?',
           'philosophy': 'Where does your imagination stop?',
           'manga_ink': 'Which story should we look at next?'},
}


def comment_question():
    """The video's own question (episode.json brand.cta.comment.question), else a question shaped
    by the video's identity, else the generic one. Write the question per video: specific and
    connected to its subject."""
    q = CFG['cta']['comment'].get('question')
    if q:
        return q
    try:
        import palette
        return _TEMPLATES.get(LANG, {}).get(palette.IDENTITY.base) or TXT['question_template']
    except Exception:
        return TXT['question_template']


# ------------------------------------------------------------------ planning: where the CTAs go
def _acts():
    """[(act number, first clip, last clip)] from the project's act files."""
    out = []
    for f in sorted(glob.glob(os.path.join(PROJECT, 'act*.py'))):
        m = re.search(r'act(\d+)\.py$', f)
        src = open(f, encoding='utf-8').read()
        c = re.search(r'^CLIPS\s*=\s*\(([^)]*)\)', src, re.M)
        if m and c:
            clips = [int(x) for x in re.findall(r'\d+', c.group(1))]
            if clips:
                out.append((int(m.group(1)), min(clips), max(clips)))
    return sorted(out)


def _clip_starts():
    st, acc = {}, 0.0
    for c in sorted(vox._DUR):
        st[c] = acc
        acc += vox._DUR[c]
    return st, acc


def pauses(min_gap=0.45):
    """Natural pauses in the narration: [(film time, length)] between words and between clips."""
    st, total = _clip_starts()
    out = []
    prev_end = None
    for c in sorted(vox._DUR):
        ws = vox._WORDS.get(c, [])
        for wd in ws:
            s = st[c] + wd['s']
            if prev_end is not None and s - prev_end >= min_gap:
                out.append((prev_end, s - prev_end))
            prev_end = st[c] + wd['e']
        if not ws:
            prev_end = None
    return out


_PLAN = None


def plan():
    """The CTA schedule in film time: [(kind, T0, dur, opts)]. Rules: nothing before the hook has
    landed (act 1 plays clean), a mid-film CTA only in a real pause inside the configured window
    and away from act openings and from the last act (the close is left alone), the main
    subscribe and the comment question in the outro. Explicit times in the config win."""
    global _PLAN
    if _PLAN is not None:
        return _PLAN
    st, total = _clip_starts()
    acts = _acts()
    pl = CFG['placement']
    act_start = {a: st.get(c0, 0.0) for a, c0, _ in acts}
    first_end = (st[acts[0][2]] + vox._DUR[acts[0][2]]) if acts and acts[0][2] in st else total * 0.12
    last_start = act_start[acts[-1][0]] if acts and len(acts) >= 6 else total * 0.85
    lo, hi = pl['mid_window'][0] * total, pl['mid_window'][1] * total
    gaps = [(T, g) for T, g in pauses(pl['min_pause']) if lo <= T <= hi and T >= first_end
            and all(abs(T - s0) > pl['avoid_act_start'] for s0 in act_start.values())
            and not (pl['avoid_last_act'] and T >= last_start)]
    gaps.sort(key=lambda x: -x[1])
    items, used = [], []
    for kind in ('like', 'subscribe_mid', 'share'):
        c = CFG['cta'].get(kind, {})
        if not c.get('enabled'):
            continue
        need = voice_seconds(kind) + 0.4 if voice_file(kind) else 0.0     # a recorded line only goes in a pause that holds it
        if c.get('at') not in (None, 'auto'):
            T0 = float(c['at'])
        else:
            T0 = next((T for T, g in gaps if g >= need and all(abs(T - u) > 25 for u in used)), None)
        if T0 is None:
            continue
        used.append(T0)
        dur = c.get('dur', 3.2)
        if CFG['cta'].get('style') == 'marker':             # live exactly as long as the narration's pause allows
            lo_, hi_ = c.get('min_dur', 2.4), c.get('max_dur', 3.5)
            nxt = [Tp for Tp, g in pauses(0.3) if Tp > T0 + lo_]
            dur = min(hi_, (nxt[0] - T0 + 0.2) if nxt else hi_)
        items.append((kind, T0 + 0.15, dur, {}))
    wm = CFG['watermark']
    wm_from = first_end if wm['from'] == 'after_hook' else 0.0 if wm['from'] == 'after_intro' else float(wm['from'] or 0)   # after_intro: the intro's logo glides into the corner, the watermark holds it
    items.append(('watermark', wm_from, total - wm_from, {}))
    _PLAN = items
    return items


def describe_plan():
    rows = []
    for kind, T0, dur, _ in plan():
        rows.append(f'{kind:<14} {int(T0 // 60)}:{T0 % 60:05.2f}  for {dur:.1f} s')
    return '\n'.join(rows)


# ------------------------------------------------------------------ the per-frame overlay
_ENV_CACHE = {}


_CORNER = {}
_MOTIF = {}


def _motif():
    """The film's own element for the like card (episode.json brand.cta.like.motif), or None."""
    f = CFG['cta']['like'].get('motif')
    if not f:
        return None
    if f not in _MOTIF:
        p = f if os.path.isabs(f) else os.path.join(PROJECT, f)
        _MOTIF[f] = Image.open(p).convert('RGBA') if os.path.exists(p) else None
    return _MOTIF[f]


def _visible_env(env):
    return env not in CFG['watermark']['hide_env']


def overlay(frame, T, shot=None, shot_span=None, neighbours=None, force=False):
    """Draw the watermark and the planned CTAs on a finished frame (numpy RGB). T: film time.
    shot: the Shot on screen (its env decides the watermark); shot_span (start, end) in film time;
    neighbours: (prev_env, next_env) so the watermark fades only where its visibility changes."""
    if not (ACTIVE or force):
        return frame
    if shot is not None and getattr(shot, 'brand_free', False):
        return frame
    items = [it for it in plan() if it[1] - 0.1 <= T <= it[1] + it[2] + 0.1]
    if not items:
        return frame
    img = Image.fromarray(frame).convert('RGBA')
    ctas = [it for it in items if it[0] != 'watermark']
    marker = CFG['cta'].get('style') == 'marker'
    for kind, T0, dur, opts in ctas:
        x, y = _corner_xy(CFG['placement']['corner'], CFG['placement']['margin'], 84)
        tl = T - T0
        _voice(kind, T0 + 0.2)
        if marker and kind in ('like', 'subscribe_mid'):
            import brand_cta as BC
            key = (kind, round(T0, 2))
            if key not in _CORNER:
                _CORNER[key] = BC.quiet_corner(np.asarray(img.convert('RGB')), 720, 160)
            c_, cx_, cy_ = _CORNER[key]
            if kind == 'like':
                BC.like(img, cx_, cy_ + 20, tl, dur, T0=T0, motif=_motif())
            else:
                BC.subscribe(img, cx_, cy_ + 20, tl, dur, T0=T0, force=force)
            continue
        if kind == 'like':
            cta_like(img, x, y, tl, 0.0, dur, T0=T0)
        elif kind == 'subscribe_mid':
            cta_subscribe(img, x, y - 20, tl, 0.0, dur, T0=T0, force=force)
        elif kind == 'share':
            cta_share(img, x, y, tl, 0.0, dur, T0=T0)
    wm = CFG['watermark']
    if wm['enabled'] and any(it[0] == 'watermark' for it in items):
        env = getattr(shot, 'env', 'theme') if shot is not None else 'theme'
        op = 1.0 if _visible_env(env) else 0.0
        if shot_span is not None and neighbours is not None:
            s0, s1 = shot_span
            pe, ne = neighbours
            if op > 0 and pe is not None and not _visible_env(pe):
                op = min(op, _eio((T - s0) / wm['fade']))
            if op > 0 and ne is not None and not _visible_env(ne):
                op = min(op, _eio((s1 - T) / wm['fade']))
        if ctas:
            op = 0.0
        wm_item = next(it for it in items if it[0] == 'watermark')
        first = T - wm_item[1]
        if op > 0:
            x, y = _corner_xy(wm['corner'], wm['margin'], 0, wm['width'])
            if wm.get('ident') and first < 2.4:                  # the first appearance is a small reveal
                tmp = Image.new('RGBA', img.size, (0, 0, 0, 0))
                lg = logo(wm['width'], force=force)
                if lg is not None:
                    reveal(tmp, x + lg.width / 2, y + lg.height / 2, wm['width'], first, 0.0, style='mask', force=force, signature_under=False,
                           ground=_ground_lum(img, (x, y, x + lg.width, y + lg.height)))
                    img.alpha_composite(alpha_mul(tmp, wm['opacity'] * op))
            else:
                place_logo(img, x, y, wm['width'], op=wm['opacity'] * op, force=force)
    return np.asarray(img.convert('RGB'))


def _corner_xy(corner, margin, h_, w_=0):
    mx, my = margin
    x = mx if corner in ('tl', 'bl') else W - mx - w_
    y = my if corner in ('tl', 'tr') else H - my - h_
    return x, y


# ------------------------------------------------------------------ the outro / end screen
SLOT = (608, 342)                      # 16:9, about a third of the frame: the size YouTube's video element takes


def endscreen_layout(n_videos=None):
    """The layout for the available recommendations: 'split' (logo + message left, two slots
    stacked right), 'feature' (one large slot right), 'centered' (no slots). Returns
    (name, slots, subscribe circle, text column box)."""
    o = CFG['outro']
    vids = [v for v in o['next_videos']] if n_videos is None else [{}] * n_videos
    n = len(vids)
    name = o['layout'] if o['layout'] != 'auto' else ('split' if n >= 2 else 'feature' if n == 1 else 'centered')
    if name == 'split':
        w_, h_ = SLOT
        x0 = W - 132 - w_
        slots = [(x0, 150, x0 + w_, 150 + h_), (x0, 150 + h_ + 96, x0 + w_, 150 + 2 * h_ + 96)]
        circle = (300, 820, 96)
        col = (132, 150, 940, 980)
    elif name == 'feature':
        w_, h_ = 832, 468
        slots = [(W - 132 - w_, 300, W - 132, 300 + h_)]
        circle = (300, 820, 96)
        col = (132, 150, 860, 980)
    else:
        slots = []
        circle = (W // 2, 500 if CFG['cta'].get('style') == 'marker' else 720, 96)
        col = (360, 160, W - 360, 960)
    if RTL:                                                   # mirrored for right-to-left channels
        slots = [(W - b[2], b[1], W - b[0], b[3]) for b in slots]
        circle = (W - circle[0], circle[1], circle[2])
        col = (W - col[2], col[1], W - col[0], col[3])
    return name, slots, circle, col


def endscreen_slots():
    """The end-screen rectangles in pixels and in percent of the frame, for YouTube Studio."""
    name, slots, circle, _ = endscreen_layout()
    out = {'layout': name, 'frame': [W, H],
           'videos': [{'px': list(b), 'percent': [round(100 * b[0] / W, 1), round(100 * b[1] / H, 1), round(100 * (b[2] - b[0]) / W, 1)]} for b in slots],
           'subscribe': {'px': [circle[0] - circle[2], circle[1] - circle[2], circle[0] + circle[2], circle[1] + circle[2]],
                         'percent': [round(100 * (circle[0] - circle[2]) / W, 1), round(100 * (circle[1] - circle[2]) / H, 1), round(100 * 2 * circle[2] / W, 1)]}}
    return out


def outro_seconds():
    return float(CFG['outro']['seconds']) if CFG['outro']['enabled'] else 0.0


def outro_scene(t, D, force=False):
    """The end screen as a Shot (append it to the last act's SHOTS after the narration):
    the logo reveals in the text column with the signature under it, the slots draw in for the
    end-screen elements, the video's comment question, then the subscribe message beside the
    subscribe element's circle. Nothing essential sits inside a slot or the circle."""
    import style
    import scenes as S
    s = style.Shot(t, D)
    s.brand_free = True                                      # no watermark or mid CTA on the end screen
    S.env(s, CFG['outro']['env'])
    name, slots, circle, col = endscreen_layout()
    o = CFG['outro']
    ink = S.ink(s)
    T0 = vox._SCENE_START
    gl = _lum(PAL.dark) if _lum(ink) > 128 else _lum(PAL.light)          # the outro's ground tone, from its ink
    cx0 = col[0] if name != 'centered' else W // 2
    lw = 420 if name != 'centered' else 460
    lg = logo(lw, force=force)
    lh = lg.height if lg is not None else 120
    ly = col[1] + 40 + lh / 2 if name != 'centered' else 300
    lx = cx0 + lw / 2 if name != 'centered' else W / 2
    if RTL and name != 'centered':
        lx = col[2] - lw / 2
    if not (CFG['cta'].get('style') == 'marker' and t >= min(D - 4.2, 5.4)):
        reveal(s.hud, lx, ly, lw, t, 0.2, style=CFG['animation']['reveal'], force=force, T=T0 + 0.2, ground=gl)
    _voice('outro', T0 + 0.6)
    _sting('outro', T0 + 0.2)
    y = ly + lh / 2 + 60
    if CFG.get('tagline'):
        tf = _font('body', 30)
        a = int(255 * _eo((t - 1.1) / 0.6))
        ImageDraw.Draw(s.hud).text((cx0 if name != 'centered' else W / 2, y), CFG['tagline'], font=tf, fill=ink + (a,),
                                    anchor='la' if name != 'centered' else 'ma')
        y += 56
    for i, b in enumerate(slots):
        v = o['next_videos'][i] if i < len(o['next_videos']) else {}
        if o['show_slot_frames'] or v.get('thumbnail'):
            cta_next(s.hud, b, t, 1.0 + 0.35 * i, title=v.get('title'), thumbnail=v.get('thumbnail'), label=(i == 0),
                     T0=T0 + 1.0 + 0.35 * i, colour=ink)
    qy = y + 20
    switch = min(D - 4.2, 5.4)
    marker = CFG['cta'].get('style') == 'marker'
    if o.get('comment_card') and CFG['cta']['comment']['enabled']:
        qw = (col[2] - col[0]) if name != 'centered' else 900
        qx = col[0] if name != 'centered' else (W - qw) / 2
        if marker:
            import brand_cta as BC
            k_out = 1 - _eio((t - switch + 0.4) / 0.5)
            if k_out > 0:
                tmp = Image.new('RGBA', s.hud.size, (0, 0, 0, 0))
                BC.comment_note(tmp, qx, qy, t - 1.6, width=qw, T0=T0 + 1.6)
                s.hud.alpha_composite(alpha_mul(tmp, k_out))
        else:
            cta_comment(s.hud, qx, qy, t, 1.6, dur=switch - 1.6, width=qw, T0=T0 + 1.6)
    # the subscribe element's place: a fine circle with the logo inside, and the message beside it
    a = _eo((t - switch) / 0.7)
    if a > 0:
        cxc, cyc, r = circle
        d = ImageDraw.Draw(s.hud)
        p = _eio((t - switch) / 0.9)
        d.arc((cxc - r, cyc - r, cxc + r, cyc + r), -90, -90 + 360 * p, fill=ink + (int(255 * a),), width=2)
        sl = logo(int(r * 1.3), force=force)
        if sl is not None:
            tmp = Image.new('RGBA', s.hud.size, (0, 0, 0, 0))
            if marker:                                       # the logo glides down into the circle, which fills like an avatar
                g_ = _eio((t - switch) / 0.9)
                pc = CFG['logo'].get('plate_color') or '#2B2A2A'
                disc = tuple(int(pc.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
                fa = _eio((t - switch - 0.35) / 0.6)
                if fa > 0:
                    S4 = 4
                    m = Image.new('L', (2 * r * S4, 2 * r * S4), 0)
                    ImageDraw.Draw(m).ellipse((0, 0, 2 * r * S4 - 1, 2 * r * S4 - 1), fill=int(255 * fa))
                    m = m.resize((2 * r, 2 * r), Image.LANCZOS)
                    dk = Image.new('RGBA', (2 * r, 2 * r), disc + (0,))
                    dk.putalpha(m)
                    s.hud.alpha_composite(dk, (int(cxc - r), int(cyc - r)))
                gx, gy = lx + (cxc - lx) * g_, ly + (cyc - ly) * g_
                gw = lw + (int(r * 1.62) - lw) * g_          # lands large, filling the disc's width
                place_logo(tmp, gx, gy, gw, force=force, anchor='mm', ground=gl, plate=False if fa > 0.5 else None)
                s.hud.alpha_composite(tmp)
            else:
                place_logo(tmp, cxc, cyc, int(r * 1.3), force=force, anchor='mm', ground=gl)
                s.hud.alpha_composite(alpha_mul(tmp, a * 0.9))
        mf = _font('title', 40)
        msg = TXT['outro_sub']
        if marker and name == 'centered':                    # the verb and the reason, set apart
            vf = _font('label', 44)
            aa = int(255 * _eo((t - switch - 0.6) / 0.5))
            d.text((W / 2, cyc + r + 34), TXT.get('outro_sub_verb', ''), font=vf, fill=CTA_FILL + (aa,), anchor='ma')
            if TXT.get('outro_sub_reason'):
                d.text((W / 2, cyc + r + 92), TXT['outro_sub_reason'], font=_font('title', 36), fill=ink + (aa,), anchor='ma')
            _sound('pop', T0 + switch, cxc, 0.4)
            return s
        tx = cxc + r + 40 if not RTL else cxc - r - 40
        if name == 'centered':
            d.text((W / 2, cyc + r + 40), msg, font=mf, fill=ink + (int(255 * a),), anchor='ma')
        else:
            lines = _wrap(msg, mf, (col[2] - tx) if not RTL else (tx - col[0]))
            for i, ln in enumerate(lines):
                d.text((tx, cyc - 26 * len(lines) + 52 * i + 26), ln, font=mf, fill=ink + (int(255 * a),), anchor='lm' if not RTL else 'rm')
        if name == 'centered':
            sl_ = CFG['signature']
            signature(s.hud, W / 2 - (110 + sl_['gap'] + sl_['square']) / 2, cyc + r + 116, t, switch + 0.5, length=110, colour=PAL.accent)
        else:
            signature(s.hud, tx, cyc + 26 * len(_wrap(msg, mf, 600)) + 30, t, switch + 0.5, length=110, colour=PAL.accent)
        _sound('pop', T0 + switch, cxc, 0.4)
    return s


def write_endscreen(path=None):
    path = path or os.path.join(PROJECT, 'out', 'endscreen.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(endscreen_slots(), open(path, 'w'), indent=1)
    return path


# ------------------------------------------------------------------ the intro card (before the narration)
def tile(size, force=False):
    """The official square logo (brand.json logo.tile) at size x size px."""
    p = _logo_path('tile')
    if p is None:
        lg = logo(size, force=force)
        return lg
    key = (p, int(size))
    if key not in _LOGO:
        _LOGO[key] = _svg(p, int(size))
    return _LOGO[key]


def intro_seconds():
    return float(CFG['intro']['seconds']) if CFG['intro']['enabled'] else 0.0


def _episode_title():
    if CFG['intro'].get('title'):
        return CFG['intro']['title']
    p = os.path.join(PROJECT, 'episode.json')
    return json.load(open(p, encoding='utf-8')).get('title') if os.path.exists(p) else None


def intro_scene(t, D, force=False):
    """The channel's opening card, played before the narration (act0.py): a thin line of text
    (« Une histoire présentée par »), then the official square tile, a fine vertical rule and the
    video's title. Choreography: the line rises word by word; the tile opens from its centre and
    settles; the rule draws down; the title slides out from behind the rule; a hold; then the card
    clears to the ground so the hook can cut in. The ground and the title's ink are the video's."""
    import style
    import scenes as S
    s = style.Shot(t, D)
    s.brand_free = True
    S.env(s, CFG['intro']['env'])
    ink = S.ink(s)
    soft = tuple(int(a * 0.62 + b * 0.38) for a, b in zip(ink, PAL.light if _lum(ink) < 128 else PAL.dark))
    T0 = vox._SCENE_START
    out = 1 - _eio((t - (D - 0.65)) / 0.55)                      # the whole card clears at the end
    if out <= 0:
        return s
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # 1. the line, word by word, each rising inside its own slot
    line = CFG['intro'].get('line') or TXT.get('intro_line', '')
    lf = _font('light', 66)
    words_ = line.split(' ')
    widths = [lf.getlength(w_) for w_ in words_]
    space = lf.getlength(' ')
    total = sum(widths) + space * (len(words_) - 1)
    x = (W - total) / 2
    y = 300
    for i, (w_, ww) in enumerate(zip(words_, widths)):
        p = _eo((t - 0.2 - 0.07 * i) / 0.55)
        if p > 0:
            tile_ = Image.new('RGBA', (int(ww) + 8, 110), (0, 0, 0, 0))
            ImageDraw.Draw(tile_).text((2, 14 + (1 - p) * 60), w_, font=lf, fill=soft + (int(255 * min(1, p * 1.6)),))
            layer.alpha_composite(tile_, (int(x), int(y - 14)))
        x += ww + space

    # 2. the row: tile | rule | title, centred as a group
    ts = int(CFG['intro']['tile_size'])
    title = _episode_title() or ''
    tf = _font('title', 82)
    tl = _wrap(title, tf, 700) if title else []
    tw = max((tf.getlength(l_) for l_ in tl), default=0)
    gap = 64
    row_w = ts + gap + 3 + (gap + tw if tl else 0)
    x0 = (W - row_w) / 2
    cy = 640
    rule_x = x0 + ts + gap

    # the tile opens from its centre (a square mask growing), with a small settle in scale
    u = _c((t - 0.75) / 0.75)
    if u > 0:
        im = tile(ts, force=force)
        if im is not None:
            k = 0.94 + 0.06 * _eo(u)
            im2 = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
            m = Image.new('L', im2.size, 0)
            r = _eio(u) * 0.5
            ImageDraw.Draw(m).rectangle((im2.width * (0.5 - r), im2.height * (0.5 - r), im2.width * (0.5 + r), im2.height * (0.5 + r)), fill=255)
            im2.putalpha(Image.fromarray(np.minimum(np.asarray(im2.getchannel('A')), np.asarray(m))))
            if _lum(PAL.light) - _lum(ink) < 0 or _ground_dark(s):
                ImageDraw.Draw(im2).rectangle((0, 0, im2.width - 1, im2.height - 1), outline=soft + (120,), width=1)
            layer.alpha_composite(im2, (int(x0 + (ts - im2.width) / 2), int(cy - im2.height / 2)))
        if CFG['intro']['sound']:
            _sound('reveal', T0 + 0.75, x0 + ts / 2, 0.5)

    # the rule draws downwards
    v = _eio((t - 1.05) / 0.55)
    if v > 0:
        hh = ts * 1.0
        d.rectangle((rule_x, cy - hh / 2, rule_x + 2, cy - hh / 2 + hh * v), fill=ink + (255,))
        if CFG['intro']['sound']:
            _sound('pencil', T0 + 1.05, rule_x, 0.35)

    # the title slides out from behind the rule
    if tl:
        q = _eo((t - 1.4) / 0.8)
        if q > 0:
            lh = 92
            blk = Image.new('RGBA', (int(tw) + 40, lh * len(tl) + 30), (0, 0, 0, 0))
            bd = ImageDraw.Draw(blk)
            for i, l_ in enumerate(tl):
                bd.text((0, i * lh), l_, font=tf, fill=ink + (255,))
            off = -(1 - q) * (tw * 0.35 + 60)
            clip = Image.new('RGBA', (int(tw) + 60, blk.height), (0, 0, 0, 0))
            clip.alpha_composite(blk, (int(off) if off > -blk.width else 0, 0))
            layer.alpha_composite(alpha_mul(clip, min(1.0, q * 1.5)), (int(rule_x + 3 + gap), int(cy - blk.height / 2 + 6)))
        sig_at = 2.0
        signature(layer, rule_x + 3 + gap, cy + (92 * len(tl)) / 2 + 30, t, sig_at, length=96, colour=PAL.accent)
    s.hud.alpha_composite(alpha_mul(layer, out))
    return s


def _ground_dark(shot):
    import scenes as S
    return _lum(S.ink(shot)) > 128


def intro_act():
    """(SHOTS, END, CLIPS) for a project's act0.py: the intro card on its own, before act 1."""
    return [(0.0, intro_scene)], intro_seconds(), ()


# ------------------------------------------------------------------ the colouring-in intro
_CI = {}


def _ci_build(width, force=False):
    """Masks and marker strokes for the colouring-in intro, built once. The colours come from the
    official logo itself: each flat colour of the SVG is one group, coloured in left to right."""
    key = (int(width), force)
    if key in _CI:
        return _CI[key]
    from PIL import ImageFilter as F
    im = logo(width, force=force)
    a = np.asarray(im).astype(np.int16)
    alpha = a[..., 3] > 100
    rgb = a[..., :3]
    # group the logo's pixels by colour (its flat colours), largest first, left to right
    cols = {}
    for c in map(tuple, rgb[alpha].reshape(-1, 3)[::17] // 24 * 24):
        cols[c] = cols.get(c, 0) + 1
    groups = []
    for c, n in sorted(cols.items(), key=lambda kv: -kv[1])[:4]:
        m = alpha & (np.abs(rgb // 24 * 24 - np.array(c)).sum(2) == 0)
        if m.sum() < 0.04 * alpha.sum():
            continue
        m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(F.MaxFilter(3)).filter(F.MinFilter(3))) > 127
        real = tuple(int(v) for v in np.median(a[..., :3][m & alpha], axis=0))
        xs = np.where(m.any(0))[0]
        groups.append(dict(mask=m, colour=real, x0=int(xs.min()), x1=int(xs.max())))
    groups.sort(key=lambda g: g['x0'])
    rng = np.random.default_rng(7)
    ic = CFG['intro']
    ang = math.radians(ic['stroke_angle'])
    dx, dy = math.cos(ang), -math.sin(ang)                 # stroke direction (up and to the right)
    nx, ny = -dy, dx                                       # across the strokes
    hh, ww = im.height, im.width
    for g in groups:
        ys, xs = np.where(g['mask'])
        proj = xs * nx + ys * ny
        lo, hi = proj.min() - 4, proj.max() + 4
        strokes = []
        k = lo
        flip = False
        while k < hi:
            cx, cy = nx * k, ny * k
            L = (ww + hh) * 1.2
            p0 = (cx - dx * L, cy - dy * L)
            p1 = (cx + dx * L, cy + dy * L)
            pts = []
            for f in np.linspace(0, 1, 7):
                j = rng.normal(0, 1.4)
                pts.append((p0[0] + (p1[0] - p0[0]) * f + nx * j, p0[1] + (p1[1] - p0[1]) * f + ny * j))
            if flip:
                pts = pts[::-1]
            strokes.append((pts, float(rng.uniform(*ic['stroke_width']))))
            k += ic['stroke_spacing'] * float(rng.uniform(0.82, 1.18))
            flip = not flip
        g['strokes'] = strokes
        edge = Image.fromarray((g['mask'] * 255).astype(np.uint8))
        outer = edge.filter(F.MaxFilter(5))
        inner = edge.filter(F.MinFilter(3))
        g['edge'] = np.asarray(outer).astype(np.int16) - np.asarray(inner).astype(np.int16) > 100
    _CI[key] = (im, groups)
    return _CI[key]


def _stroke_partial(d, pts, frac, width, fill):
    """Draw the first `frac` of a polyline (a marker stroke being drawn)."""
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:])]
    total = sum(seg) * frac
    out = [pts[0]]
    for (a, b), l in zip(zip(pts[:-1], pts[1:]), seg):
        if total <= 0:
            break
        f = min(1.0, total / l)
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
        total -= l
    if len(out) > 1:
        d.line(out, fill=fill, width=int(width), joint='curve')


def intro_color_scene(t, D, force=False):
    """The logo coloured in by hand: each letter's outline is traced, then marker strokes fill
    it colour by colour (the logo's own colours, left to right), leaving the small gaps real
    colouring leaves; the hand-coloured logo then settles into the exact official logo, holds,
    and clears. Played on the logo's own ground."""
    import style
    s = style.Shot(t, D)
    s.brand_free = True
    ic = CFG['intro']
    gc = ic.get('ground')
    ground = tuple(int(gc.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) if gc else PAL.dark
    s.hud.paste(ground + (255,), (0, 0, W, H))
    T0 = vox._SCENE_START
    _sting('intro', T0)
    im, groups = _ci_build(ic['logo_width'], force)
    ox, oy = int((W - im.width) / 2), int((H - im.height) / 2 - 10)
    n = len(groups)
    t_out, t_res = D - 0.7, D - 1.75                       # resolve to the clean logo, then clear
    fill_span = (t_res - 0.55) / max(n, 1)
    canvas = Image.new('RGBA', im.size, (0, 0, 0, 0))
    for gi, g in enumerate(groups):
        col = g['colour']
        # 1. the outline is traced left to right
        p_out = _eio((t - 0.15 - 0.25 * gi) / 0.85)
        if p_out > 0:
            xcut = g['x0'] + (g['x1'] - g['x0'] + 10) * p_out
            e = g['edge'].copy()
            e[:, int(xcut):] = False
            ov = np.zeros(im.size[::-1] + (4,), np.uint8)
            ov[e] = col + (230,)
            canvas.alpha_composite(Image.fromarray(ov, 'RGBA'))
        # 2. marker strokes colour it in, each one drawn quickly, left to right
        start = 0.45 + fill_span * gi
        strokes = g['strokes']
        if t > start:
            sm = Image.new('L', im.size, 0)
            sd = ImageDraw.Draw(sm)
            per = fill_span * 1.15 / max(len(strokes), 1)
            for i, (pts, wd) in enumerate(strokes):
                f = (t - start - i * per) / 0.12
                if f <= 0:
                    break
                _stroke_partial(sd, pts, min(1.0, f), wd, 255)
            m = np.minimum(np.asarray(sm), (g['mask'] * 255).astype(np.uint8))
            ov = np.zeros(im.size[::-1] + (4,), np.uint8)
            ov[..., :3] = col
            ov[..., 3] = m
            canvas.alpha_composite(Image.fromarray(ov, 'RGBA'))
        if ic.get('sound', True):
            for j in range(4):
                _sound('marker', T0 + start + fill_span * j / 4, ox + g['x0'] + (g['x1'] - g['x0']) * j / 4, 0.55)
    # 3. the hand-coloured logo settles into the exact official logo
    r = _eio((t - t_res) / 0.6)
    if r > 0:
        canvas = Image.blend(canvas, im, r) if r < 1 else im.copy()
    k = 1 - _eio((t - t_out) / 0.6)
    if k > 0:
        s.hud.alpha_composite(alpha_mul(canvas, k), (ox, oy))
    return s


def intro_act():
    """(SHOTS, END, CLIPS) for a project's act0.py: the intro on its own, before act 1.
    brand.json intro.style: 'color_in' (the logo coloured in by hand) or 'card' (presented-by card)."""
    fn = intro_color_scene if CFG['intro'].get('style', 'color_in') == 'color_in' else intro_scene
    return [(0.0, fn)], intro_seconds(), ()


# ------------------------------------------------------------------ the channel's sonic signature
def _synth_note(f, dur, vel, sr, kind='piano', seed=0):
    rng = np.random.default_rng(seed)
    n = int((dur + 2.5) * sr)
    t = np.arange(n) / sr
    out = np.zeros(n)
    if kind == 'bell':                                     # soft glass bell: inharmonic partials, long decay
        for k, (r, a, dec) in enumerate(((1.0, 1.0, 2.2), (2.76, 0.32, 1.0), (5.40, 0.12, 0.5), (8.93, 0.05, 0.25))):
            out += a * np.sin(2 * np.pi * f * r * t + rng.uniform(0, 6.28)) * np.exp(-t / dec)
        att = int(0.004 * sr)
    else:                                                  # felt piano pluck
        for k, (a, dec) in enumerate(((1.0, 1.4), (0.45, 0.8), (0.18, 0.5), (0.07, 0.3)), start=1):
            out += a * np.sin(2 * np.pi * f * k * (1 + 0.0004 * k * k) * t + rng.uniform(0, 6.28)) * np.exp(-t / dec)
        att = int(0.006 * sr)
    out[:att] *= np.linspace(0, 1, att) ** 2
    off = int(dur * sr)
    if off < n:
        out[off:] *= np.exp(-np.arange(n - off) / (0.5 * sr))
    return out * vel


def _midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def compose_sting(short=False, sr=48000):
    """The AX Lab sting (stereo float array). Long version, timed to the colouring-in intro: a pad
    breathes in while the outlines are traced; as « AX » is coloured, a felt-piano motif rises
    (D, F#, A, D); as « Lab » is coloured it answers (E, A, C#); when the logo resolves, a D major
    add9 chord blooms with a low D and a glass bell; then it rings out under the clearing card.
    Short version (outro): the answer and the bloom only."""
    dur = 2.6 if short else 4.6
    n = int((dur + 0.4) * sr)
    L, R = np.zeros(n), np.zeros(n)

    def add(sig, at, pan=0.0, g=1.0):
        i = int(at * sr)
        j = min(n, i + len(sig))
        if j > i:
            L[i:j] += sig[:j - i] * g * math.sqrt(0.5 - pan / 2)
            R[i:j] += sig[:j - i] * g * math.sqrt(0.5 + pan / 2)

    def pad(notes, at, length, g):
        m = int((length + 1.5) * sr)
        t = np.arange(m) / sr
        s = np.zeros(m)
        for nt in notes:
            for det in (-0.1, 0.0, 0.09):
                f = _midi(nt) * 2 ** (det / 12)
                s += np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
        a = int(length * 0.6 * sr)
        env = np.ones(m)
        env[:a] = np.linspace(0, 1, a) ** 2
        env[int(length * sr):] = np.exp(-np.arange(m - int(length * sr)) / (0.7 * sr))
        add(s * env / (len(notes) * 3), at, 0.0, g)

    if short:
        rise, ans, bloom = [], [(0.10, 64), (0.42, 69), (0.74, 73)], 1.05
    else:
        pad([50, 57, 62], 0.0, 2.9, 0.22)                  # breath under the outlines
        rise = [(0.50, 62), (0.82, 66), (1.12, 69), (1.42, 74)]     # « AX » being coloured
        ans = [(1.78, 76), (2.12, 69), (2.44, 73)]                  # « Lab » answers
        bloom = 2.86                                                # the logo resolves
    for i, (at, m) in enumerate(rise + ans):
        add(_synth_note(_midi(m), 0.45, 0.34 if i % 2 == 0 else 0.28, sr, seed=i), at, -0.3 + 0.6 * ((i % 4) / 3), 1.0)
    for j, m in enumerate((50, 57, 62, 66, 69, 76)):         # D major add9, spread
        add(_synth_note(_midi(m), 1.6, 0.22, sr, seed=20 + j), bloom + 0.012 * j, -0.4 + 0.16 * j, 1.0)
    add(_synth_note(_midi(38), 1.8, 0.45, sr, seed=40), bloom, 0.0, 1.0)          # low D
    add(_synth_note(_midi(86), 1.4, 0.16, sr, 'bell', seed=41), bloom + 0.03, 0.25, 1.0)
    add(_synth_note(_midi(93), 1.2, 0.08, sr, 'bell', seed=42), bloom + 0.09, -0.25, 1.0)
    pad([50, 57, 62, 66, 76], bloom, dur - bloom - 0.3, 0.18)
    # a short room, then a fade to silence at the end of the card
    from scipy.signal import fftconvolve
    m = int(1.6 * sr)
    tt = np.arange(m) / sr
    rng = np.random.default_rng(3)
    irl = rng.normal(0, 1, m) * np.exp(-tt / 0.55)
    irr = rng.normal(0, 1, m) * np.exp(-tt / 0.55)
    irl /= np.sqrt((irl ** 2).sum()); irr /= np.sqrt((irr ** 2).sum())
    L = 0.75 * L + 0.35 * fftconvolve(L, irl)[:n]
    R = 0.75 * R + 0.35 * fftconvolve(R, irr)[:n]
    out = np.stack([L, R], 1)[:int(dur * sr)]
    f = int(0.5 * sr)
    out[-f:] *= np.linspace(1, 0, f)[:, None] ** 1.5
    return out / (np.abs(out).max() / 0.8)


def write_stings():
    """Render the channel's stings into SK/brand/ (normalised to brand.json music.lufs)."""
    import subprocess, wave
    paths = []
    for short, name in ((False, CFG['music']['intro']), (True, CFG['music']['outro'])):
        a = compose_sting(short)
        raw = os.path.join(BRAND_DIR, '_' + name)
        with wave.open(raw, 'wb') as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(48000)
            w.writeframes((a * 32767).astype('<i2').tobytes())
        dst = os.path.join(BRAND_DIR, name)
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', raw, '-af', f"loudnorm=I={CFG['music']['lufs']}:TP=-2:LRA=7",
                        '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', dst], check=True)
        os.remove(raw)
        paths.append(dst)
    if CFG['music'].get('tap'):
        a = compose_tap()
        raw = os.path.join(BRAND_DIR, '_tap.wav')
        with wave.open(raw, 'wb') as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(48000)
            w.writeframes((a * 32767).astype('<i2').tobytes())
        dst = os.path.join(BRAND_DIR, CFG['music']['tap'])
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', raw, '-af', 'loudnorm=I=-26:TP=-6:LRA=7', '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', dst], check=True)
        os.remove(raw)
        paths.append(dst)
    return paths


def compose_tap(sr=48000):
    """The first two notes of the sting (D4, F#4), softly: the subscribe press."""
    n = int(1.4 * sr)
    out = np.zeros(n)
    for at, m, v in ((0.0, 62, 0.34), (0.11, 66, 0.30)):
        sig = _synth_note(_midi(m), 0.35, v, sr, seed=m)
        i = int(at * sr)
        out[i:i + len(sig)] += sig[:n - i]
    f = int(0.4 * sr)
    out[-f:] *= np.linspace(1, 0, f)
    out /= np.abs(out).max() / 0.8
    return np.stack([out, out], 1)


def write_pinned_comment(path=None):
    """The video's comment question, ready to post as the pinned comment."""
    path = path or os.path.join(PROJECT, 'out', 'pinned_comment.txt')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(comment_question() + '\n')
    return path


def _sting(kind, T, gain=None):
    """Place the channel sting (intro | outro) at film time T in the mix, at full level."""
    mc = CFG.get('music', {})
    if not mc.get('enabled') or not mc.get(kind):
        return
    p = os.path.join(BRAND_DIR, mc[kind])
    if not os.path.exists(p):
        return
    import style
    style.EVENTS[('voice', round(T, 3), 960)] = {'file': p, 'gain': mc.get(f'{kind}_gain', 1.0) if gain is None else gain}


if __name__ == '__main__' and '--sting' in sys.argv:
    print(write_stings())
    sys.exit()
if __name__ == '__main__':
    print('official logo:', OFFICIAL or '(none: overlays are off in real renders until brand/logo.svg exists)')
    print('language:', LANG)
    print('comment question:', comment_question())
    print(describe_plan())
    print(json.dumps(endscreen_slots(), indent=1))
