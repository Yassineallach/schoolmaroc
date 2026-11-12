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


def _ground_lum(base, box):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0:
        return 200.0
    a = np.asarray(base.crop((x0, y0, x1, y1)).convert('L'), np.float32)
    return float(a.mean())


def place_logo(img, x, y, width, op=1.0, force=False, plate=None, anchor='lt'):
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
    g = _ground_lum(img, (x, y, x + w_, y + h_))
    dark_ground = g < 110
    variant = 'on_dark' if dark_ground else 'on_light'
    im = logo(width, variant, force) if _logo_path(variant) else base
    need = plate if plate is not None else (CFG['logo']['plate'] == 'auto' and abs(_logo_lum(im) - g) < 70)
    if need:
        pad = max(10, int(h_ * 0.22))
        pl = Image.new('RGBA', (w_ + 2 * pad, h_ + 2 * pad), (0, 0, 0, 0))
        col = PAPER if _logo_lum(im) < 128 else PAL.dark
        ImageDraw.Draw(pl).rounded_rectangle((0, 0, pl.width - 1, pl.height - 1), radius=pad, fill=col + (int(255 * CFG['logo']['plate_opacity']),))
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
def reveal(layer, cx, cy, width, t, start, style=None, hold=None, exit_dur=0.6, force=False, signature_under=True, T=None):
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
    u = _c((t - start) / dur)
    tmp = Image.new('RGBA', layer.size, (0, 0, 0, 0))
    if style == 'scale':
        s = 0.94 + 0.06 * _eo(u)
        place_logo(tmp, cx, cy, width * s, op=_eo(u * 1.4), force=force, anchor='mm')
    elif style == 'assemble':
        d = ImageDraw.Draw(tmp)
        col = _ink_for(layer.convert('RGBA') if layer.mode != 'RGBA' else layer, (x0, y0, x0 + w_, y0 + h_))
        g = 40 * (1 - _eo(u / 0.6))
        a = int(255 * (1 - _eo((u - 0.55) / 0.45)))
        if a > 0:
            for (xa, ya, xb, yb) in ((x0 - 30 - g, y0 - 18, x0 + w_ * 0.35 - g, y0 - 18), (x0 + w_ * 0.65 + g, y0 - 18, x0 + w_ + 30 + g, y0 - 18),
                                     (x0 - 30 - g, y0 + h_ + 18, x0 + w_ * 0.35 - g, y0 + h_ + 18), (x0 + w_ * 0.65 + g, y0 + h_ + 18, x0 + w_ + 30 + g, y0 + h_ + 18)):
                d.line((xa, ya, xb, yb), fill=col + (a,), width=2)
        place_logo(tmp, cx, cy, width, op=_eo((u - 0.35) / 0.5), force=force, anchor='mm')
    else:                                                   # mask: the logo appears behind a soft moving edge
        place_logo(tmp, cx, cy, width, op=1.0, force=force, anchor='mm')
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
        signature(layer, cx - (CFG['signature']['length'] + CFG['signature']['gap'] + CFG['signature']['square']) / 2, cy + h_ / 2 + 26,
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
    name = CFG.get('channel_name')
    nf = _font('title', 30)
    nw = int(nf.getlength(name)) if name else 0
    w_ = 28 + (lw_ + 22 if lg is not None else 0) + max(nw, 0) + (22 if name else 0) + bw + (64 if bell else 0) + 24
    h_ = max(84, (lg.height if lg is not None else 0) + 36)
    card = _card(w_, h_)
    d = ImageDraw.Draw(card)
    cx = 28
    if lg is not None:
        card.alpha_composite(lg, (cx, (h_ - lg.height) // 2))
        cx += lw_ + 22
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
        items.append((kind, T0 + 0.15, c.get('dur', 3.2), {}))
    wm = CFG['watermark']
    wm_from = first_end if wm['from'] == 'after_hook' else float(wm['from'] or 0)
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
    for kind, T0, dur, opts in ctas:
        x, y = _corner_xy(CFG['placement']['corner'], CFG['placement']['margin'], 84)
        tl = T - T0
        _voice(kind, T0 + 0.2)
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
                    reveal(tmp, x + lg.width / 2, y + lg.height / 2, wm['width'], first, 0.0, style='mask', force=force, signature_under=False)
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
        circle = (W // 2, 720, 96)
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
    cx0 = col[0] if name != 'centered' else W // 2
    lw = 420 if name != 'centered' else 460
    lg = logo(lw, force=force)
    lh = lg.height if lg is not None else 120
    ly = col[1] + 40 + lh / 2 if name != 'centered' else 300
    lx = cx0 + lw / 2 if name != 'centered' else W / 2
    if RTL and name != 'centered':
        lx = col[2] - lw / 2
    reveal(s.hud, lx, ly, lw, t, 0.2, style=CFG['animation']['reveal'], force=force, T=T0 + 0.2)
    _voice('outro', T0 + 0.6)
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
    if o.get('comment_card') and CFG['cta']['comment']['enabled']:
        qw = (col[2] - col[0]) if name != 'centered' else 900
        qx = col[0] if name != 'centered' else (W - qw) / 2
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
            place_logo(tmp, cxc, cyc, int(r * 1.3), force=force, anchor='mm')
            s.hud.alpha_composite(alpha_mul(tmp, a * 0.9))
        mf = _font('title', 40)
        msg = TXT['outro_sub']
        tx = cxc + r + 40 if not RTL else cxc - r - 40
        if name == 'centered':
            d.text((W / 2, cyc + r + 40), msg, font=mf, fill=ink + (int(255 * a),), anchor='ma')
        else:
            lines = _wrap(msg, mf, (col[2] - tx) if not RTL else (tx - col[0]))
            for i, ln in enumerate(lines):
                d.text((tx, cyc - 26 * len(lines) + 52 * i + 26), ln, font=mf, fill=ink + (int(255 * a),), anchor='lm' if not RTL else 'rm')
        signature(s.hud, tx if not RTL else tx, cyc + 26 * len(_wrap(msg, mf, 600)) + 30, t, switch + 0.5, length=110, colour=PAL.accent)
        _sound('pop', T0 + switch, cxc, 0.4)
    return s


def write_endscreen(path=None):
    path = path or os.path.join(PROJECT, 'out', 'endscreen.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(endscreen_slots(), open(path, 'w'), indent=1)
    return path


if __name__ == '__main__':
    print('official logo:', OFFICIAL or '(none: overlays are off in real renders until brand/logo.svg exists)')
    print('language:', LANG)
    print('comment question:', comment_question())
    print(describe_plan())
    print(json.dumps(endscreen_slots(), indent=1))
