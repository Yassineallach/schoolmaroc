"""Physical paper objects that join the existing prints, documents and clippings (presets.py).

Builders return RGBA images, so every preset works on them (drop, slide, unfold, flip, stack...):
    newspaper(headline, date='1 APRIL 1988', masthead='THE INKWELL GAZETTE', photo=img)
    polaroid(img, caption='Cambridge')          sticky_note('ask why')          letter(lines)
Animations:
    envelope(layer, LETTER, cx, cy, t, start)   the flap lifts, the letter slides out and settles
    spin_in(layer, PAPER, cx, cy, t, start)     a front page spinning onto the desk (newsreel)
    tape(layer, x, y, t, start, angle=-12)      a strip of tape pressed onto a corner
    pushpin(layer, x, y, t, start)              a terracotta pin pressed into the paper

Only print words the narration supports on newspapers and letters (headline = a spoken fact;
the masthead is a generic invented title, never a real newspaper's name).
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from vox import F_HEAD, F_TYPE, F_SERIF, F_BODY, INK, CREAM, torn_mask, fit_w
from style import sfx
import presets as P
import annotate as A

TERRA = (205, 88, 48)
NEWSPRINT = (234, 228, 212)


def newspaper(headline, date='', masthead='THE INKWELL GAZETTE', sub=None, photo=None, w=900, h=1180, seed=21):
    r = np.random.default_rng(seed)
    base = np.empty((h, w, 3), np.float32)
    base[:] = NEWSPRINT
    base += r.normal(0, 4, (h, w, 1))
    im = Image.fromarray(base.clip(0, 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(im)
    ink = (28, 26, 24, 255)
    d.text((w / 2, 74), masthead, font=F_SERIF(70), fill=ink, anchor='mm')
    d.line((40, 122, w - 40, 122), fill=ink, width=4)
    d.line((40, 130, w - 40, 130), fill=ink, width=1)
    if date:
        d.text((44, 150), date.upper(), font=F_TYPE(24), fill=ink, anchor='lm')
    d.line((40, 170, w - 40, 170), fill=ink, width=1)
    f = F_HEAD(76)
    words, row, y = headline.upper().split(), '', 236
    for word in words:
        test = (row + ' ' + word).strip()
        if d.textlength(test, font=f) > w - 90 and row:
            d.text((w / 2, y), row, font=f, fill=ink, anchor='mm')
            y += 84
            row = word
        else:
            row = test
    d.text((w / 2, y), row, font=f, fill=ink, anchor='mm')
    y += 70
    if sub:
        d.text((w / 2, y), sub, font=F_BODY(32), fill=ink, anchor='mm')
        y += 50
    if photo is not None:
        ph = fit_w(photo.convert('L').convert('RGB'), w - 120)
        ph = ph.crop((0, 0, ph.width, min(ph.height, 420)))
        im.paste(ph, (60, y))
        y += ph.height + 24
    cols, cw = 3, (w - 120) / 3
    for c in range(cols):
        x0 = 44 + c * (cw + 16)
        yy = y
        while yy < h - 60:
            d.line((x0, yy, x0 + cw * r.uniform(0.82, 1.0), yy), fill=(120, 114, 104, 255), width=4)
            yy += 19
    im.putalpha(torn_mask(w, h, seed, amp=4, step=14))
    return im


def polaroid(img, caption='', width=420, seed=31):
    pad, bottom = 22, 110
    ph = fit_w(img.convert('RGB'), width - 2 * pad)
    side = min(ph.width, ph.height)
    ph = ph.crop(((ph.width - side) // 2, 0, (ph.width - side) // 2 + side, side)).resize((width - 2 * pad, width - 2 * pad))
    card = Image.new('RGBA', (width, width - 2 * pad + pad + bottom), (247, 244, 236, 255))
    card.paste(ph, (pad, pad))
    if caption:
        ImageDraw.Draw(card).text((width / 2, card.height - bottom / 2), caption, font=F_TYPE(34), fill=(40, 38, 36, 255), anchor='mm')
    return card


def sticky_note(text, size=300, colour=(240, 206, 158), seed=41):
    im = Image.new('RGBA', (size, size), colour + (255,))
    a = np.asarray(im).astype(np.float32)
    a[..., :3] += np.random.default_rng(seed).normal(0, 3, (size, size, 1))
    a[int(size * 0.82):, :, :3] *= np.linspace(1, 0.9, size - int(size * 0.82))[:, None, None]   # the curling bottom edge
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(im)
    f = F_TYPE(int(size * 0.13))
    words, row, y = text.split(), '', size * 0.28
    for word in words:
        test = (row + ' ' + word).strip()
        if d.textlength(test, font=f) > size * 0.8 and row:
            d.text((size / 2, y), row, font=f, fill=(40, 36, 32, 255), anchor='mm')
            y += size * 0.16
            row = word
        else:
            row = test
    d.text((size / 2, y), row, font=f, fill=(40, 36, 32, 255), anchor='mm')
    return im


def letter(lines, w=620, h=780, seed=51, signature=None):
    """A typed letter on cream paper (lines of text; '---' for ruled filler)."""
    im = P.paper_card(w, h, seed=seed, colour=(248, 244, 233))
    d = ImageDraw.Draw(im)
    y = 90
    for ln in lines:
        if ln == '---':
            d.line((70, y, 70 + np.random.default_rng(seed + y).uniform(0.6, 0.95) * (w - 140), y), fill=(150, 144, 134, 255), width=3)
            y += 34
        else:
            d.text((70, y), ln, font=F_TYPE(32), fill=(36, 34, 32, 255), anchor='lm')
            y += 50
    if signature:
        d.text((w - 90, h - 110), signature, font=F_SERIF(40), fill=(36, 34, 32, 255), anchor='rm')
    return im


def _envelope_parts(w, h):
    body = P.paper_card(w, h, seed=61, colour=(232, 216, 188))
    db = ImageDraw.Draw(body)
    db.line((0, h, w / 2, h * 0.48, w, h), fill=(200, 182, 152, 255), width=3)
    flap = Image.new('RGBA', (w, int(h * 0.55)), (0, 0, 0, 0))
    ImageDraw.Draw(flap).polygon([(0, 0), (w, 0), (w / 2, flap.height)], fill=(222, 204, 172, 255))
    return body, flap


def envelope(layer, paper, cx, cy, t, start, w=700, h=440, dur=1.6):
    """The envelope sits on the desk; its flap lifts open (a flip about the top edge), the
    letter slides up out of it and settles above the envelope."""
    sfx('envelope', start, cx)
    body, flap = _envelope_parts(w, h)
    x0, y0 = cx - w / 2, cy - h / 2
    u_flap = A.pen((t - start) / 0.45)
    u_out = A.pen((t - start - 0.45) / (dur - 0.45))
    lt = fit_w(paper, int(w * 0.8))
    mouth = y0 + h * 0.30                                    # the letter stays tucked below this line
    ly = (mouth + lt.height / 2 + 20) + (-lt.height * 0.62) * u_out
    if u_flap >= 0.5:                                        # open flap stands behind everything
        k = (u_flap - 0.5) * 2
        fl = flap.transpose(Image.FLIP_TOP_BOTTOM).resize((w, max(1, int(flap.height * k))))
        P.put(layer, P.shade(fl, 0.08), cx, y0 - fl.height / 2 + 2, shadow=False)
    P.put(layer, body, cx, cy, lift=0.05)
    if u_out > 0:
        sheet = Image.new('RGBA', layer.size, (0, 0, 0, 0))
        P.put(sheet, lt, cx, ly, lift=0.12)
        m = Image.new('L', layer.size, 255)
        ImageDraw.Draw(m).rectangle((0, mouth, layer.width, layer.height), fill=0)
        sheet.putalpha(Image.fromarray(np.minimum(np.asarray(sheet.getchannel('A')), np.asarray(m))))
        layer.alpha_composite(sheet)
        ImageDraw.Draw(layer).line((x0 + 8, mouth, x0 + w - 8, mouth), fill=(200, 182, 152, 255), width=3)   # the envelope's lip
    if u_flap < 0.5:                                         # closed flap folding up
        k = 1 - u_flap * 2
        fl = flap.resize((w, max(1, int(flap.height * k))))
        P.put(layer, fl, cx, y0 + fl.height / 2, shadow=False)


def spin_in(layer, paper, cx, cy, t, start, dur=1.0, turns=1.5, rot=-4):
    """A front page spins in from the distance and lands flat (the newsreel move): use once,
    for a headline the narration reads."""
    sfx('whoosh', start + dur * 0.6, cx, dur=dur)
    sfx('drop', start + dur * 0.85, cx)
    if t < start:
        return
    u = A.pen((t - start) / dur)
    ang = rot + 360 * turns * (1 - u)
    sc = 0.08 + 0.92 * u
    item = P.rot_scale(paper, ang, sc, key=('spin', id(paper)) if u >= 1 else None)
    P.put(layer, item, cx, cy, lift=0.6 * (1 - u), op=min(1.0, u * 3))


def tape(layer, x, y, t, start, angle=-12, length=170, colour=(206, 188, 150)):
    """A strip of semi-transparent tape pressed onto a corner of a print."""
    sfx('tape', start, x)
    if t < start:
        return
    u = A.pop((t - start) / 0.3, 0.06)
    w_, h_ = int(length * min(1.0, u)), 46
    if w_ < 4:
        return
    st = Image.new('RGBA', (w_, h_), colour + (185,))
    d = ImageDraw.Draw(st)
    d.line((0, 1, w_, 1), fill=(170, 150, 112, 210), width=2)
    d.line((0, h_ - 2, w_, h_ - 2), fill=(170, 150, 112, 210), width=2)
    for xx in (0, w_ - 1):
        for yy in range(0, h_, 6):
            d.line((xx, yy, xx + (4 if xx == 0 else -4), yy + 3), fill=(0, 0, 0, 0), width=3)   # torn ends
    st = st.rotate(angle, Image.BICUBIC, expand=True)
    A._comp(layer, st, x - st.width / 2, y - st.height / 2)


def pushpin(layer, x, y, t, start, colour=TERRA):
    """A pin pressed into the paper: drops a few px with its shadow tightening."""
    sfx('pin', start, x)
    if t < start - 0.1:
        return
    u = A.pop((t - start + 0.1) / 0.3)
    lift = (1 - min(1.0, u)) * 14
    d = ImageDraw.Draw(layer)
    d.ellipse((x - 10 + 6 + lift / 2, y - 4 + 8 + lift / 2, x + 14 + 6 + lift / 2, y + 10 + 8 + lift / 2), fill=(40, 26, 14, 70))
    d.ellipse((x - 16, y - 16 - lift, x + 16, y + 16 - lift), fill=colour + (255,))
    d.ellipse((x - 7, y - 11 - lift, x + 1, y - 3 - lift), fill=(240, 170, 140, 255))
