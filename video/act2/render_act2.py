"""Act 2 — The Author (0:57.7–1:42.3). Renders frames and pipes them to ffmpeg.

Usage: python3 render_act2.py stills t1 t2 ...   (t in act-local seconds)
       python3 render_act2.py video out.mp4
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SCR, 'act1'))
import ink
from ink import INK, shape, stroke, ink_text, ellipse_pts, wobble

W, H, FPS = 1920, 1080, 30
A3 = os.path.join(SCR, 'assets', 'v3')
B3 = os.path.join(SCR, 'batch3', '583e6c6d-Assets3')
AUD = os.path.join(SCR, 'rar', 'ac0d80b8-voxcpm_clips_texts_20261029_1949')
FONTS = os.path.join(SCR, 'fonts')
T0 = 57.7  # act start in the full video

GOLD = (196, 154, 69)
RED = (163, 59, 46)
RUST = (184, 100, 63)
MUTED = (96, 74, 56)
STONE = (150, 132, 112)
WOOD = (150, 102, 62)
PAGE = (236, 224, 198)
NAVY = (40, 46, 66)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


F_HEAD = font('Fraunces700.woff2', 76)
F_BIG = font('Fraunces700.woff2', 170)
F_SIGN = font('Fraunces700.woff2', 38)
F_CAP = font('Fraunces500i.woff2', 40)
F_STAMP = font('Fraunces700.woff2', 30)



class FadeDraw:
    """ImageDraw that blends translucent text instead of overwriting pixels."""
    def __init__(self, img):
        self.img = img
        self.d = ImageDraw.Draw(img)

    def textlength(self, *a, **k):
        return self.d.textlength(*a, **k)

    def text(self, xy, s, font, fill, anchor='la'):
        ov = Image.new('RGBA', self.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).text(xy, s, font=font, fill=fill, anchor=anchor)
        self.img.alpha_composite(ov)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


def boil(t):
    return int(t * 8)


rng = np.random.default_rng(7)
_g = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
_g = np.asarray(Image.fromarray(((_g * 40) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.8)), np.float32)
GRAIN = ((_g - 128) / 128.0)[..., None]
yy, xx = np.mgrid[0:H, 0:W]
_r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
VIGNETTE = (1 - 0.32 * np.clip(_r - 0.55, 0, 1) ** 1.4)[..., None].astype(np.float32)
PAPER = ink.make_paper()


def finish(img, vignette=False):
    a = np.asarray(img.convert('RGB'), np.float32) * (1 + 0.035 * GRAIN)
    if vignette:
        a = a * VIGNETTE
    return a.clip(0, 255).astype(np.uint8)


def paper():
    return PAPER.convert('RGBA')


def kenburns(img, t, s0, s1, c0, c1):
    iw, ih = img.size
    s = lerp(s0, s1, t)
    cw = iw / s
    ch = cw * H / W
    cx, cy = lerp(c0[0], c1[0], t) * iw, lerp(c0[1], c1[1], t) * ih
    x0 = min(max(cx - cw / 2, 0), iw - cw)
    y0 = min(max(cy - ch / 2, 0), ih - ch)
    return img.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BICUBIC)


def stamp(layer, cx, cy, text, ang=-9, alpha=255, scale=1.0, f=None):
    f = f or F_STAMP
    tw = int(ImageDraw.Draw(layer).textlength(text, font=f)) + 50
    t = Image.new('RGBA', (tw, 80), (0, 0, 0, 0))
    td = ImageDraw.Draw(t)
    stroke(td, [(8, 8), (tw - 8, 8), (tw - 8, 72), (8, 72)], 4, color=RED, seed=len(text), amp=1.2, closed=True)
    td.text((tw / 2, 41), text, font=f, fill=RED + (255,), anchor='mm')
    a = np.asarray(t).copy()
    a[np.random.default_rng(5).random(a.shape[:2]) < 0.15, 3] = 0
    a[..., 3] = (a[..., 3].astype(np.float32) * alpha / 255).astype(np.uint8)
    t = Image.fromarray(a, 'RGBA')
    if scale != 1:
        t = t.resize((int(t.width * scale), int(t.height * scale)), Image.BICUBIC)
    t = t.rotate(ang, resample=Image.BICUBIC, expand=True)
    layer.alpha_composite(t, (int(cx - t.width / 2), int(cy - t.height / 2)))


# ---------- the author panels: they carry their own drawn background, so they are shown as they are ----------
P01 = Image.open(os.path.join(A3, 'P01_v2.png')).convert('RGBA')
P_PAPER = (239, 220, 184)


def panel(box, height):
    p = P01.crop(box)
    p = p.resize((round(p.width * height / p.height), height), Image.LANCZOS)
    m = Image.new('L', p.size, 255)
    m = Image.fromarray((np.asarray(m, np.float32) * 0).astype(np.uint8))
    fade = 70
    yy_, xx_ = np.mgrid[0:p.height, 0:p.width]
    d = np.minimum.reduce([xx_, yy_, p.width - 1 - xx_, p.height - 1 - yy_]).astype(np.float32)
    p.putalpha(Image.fromarray((np.clip(d / fade, 0, 1) * 255).astype(np.uint8)))
    return p


DESK = panel((0, 0, 850, 1024), 1000)
CLOSING = panel((850, 100, 1536, 1024), 1000)
P_BG = Image.new('RGBA', (W, H), P_PAPER + (255,))


PORTRAIT = Image.open(os.path.join(A3, 'P02_portrait.png')).convert('RGBA')
PORTRAIT_PAPER = (237, 219, 178)


def feather(img, fade):
    yy_, xx_ = np.mgrid[0:img.height, 0:img.width]
    d = np.minimum.reduce([xx_, yy_, img.width - 1 - xx_, img.height - 1 - yy_]).astype(np.float32)
    a = np.asarray(img.getchannel('A'), np.float32) * np.clip(d / fade, 0, 1)
    img.putalpha(Image.fromarray(a.astype(np.uint8)))
    return img


def s11(t, D):
    """His creator, Pierce Brown: the portrait (with its own paper background) and a name label."""
    k = ease(t / D)
    img = Image.new('RGBA', (W, H), PORTRAIT_PAPER + (255,))
    s = lerp(1.0, 1.06, k)
    ph = int(1000 * s)
    p = PORTRAIT.resize((round(PORTRAIT.width * ph / PORTRAIT.height), ph), Image.LANCZOS)
    p = feather(p, 40)
    img.alpha_composite(p, (int(700 - p.width / 2), int(H - p.height + 45)))
    d = FadeDraw(img)
    a = int(255 * ease((t - 0.8) / 0.6))
    d.text((1180, 470), 'Pierce Brown', font=F_HEAD, fill=INK + (a,), anchor='lm')
    a2 = int(255 * ease((t - 1.4) / 0.6))
    d.text((1184, 560), 'author of Red Rising', font=F_CAP, fill=MUTED + (a2,), anchor='lm')
    if a2:
        stroke(ImageDraw.Draw(img), [(1184, 515), (1184 + 470 * ease((t - 1.1) / 0.6), 515)], 4, seed=3, amp=1.0, alpha=a2)
    return img.convert('RGB')


def s17(t, D):
    """He closes a book he finds too safe and sets it aside."""
    k = ease(t / D)
    img = P_BG.copy()
    s = lerp(1.04, 1.0, k)
    p = CLOSING.resize((int(CLOSING.width * s), int(CLOSING.height * s)), Image.BICUBIC)
    img.alpha_composite(p, (int(W / 2 - p.width / 2), int(H / 2 - p.height * 0.5)))
    return img.convert('RGB')


# ---------- hand-inked icons ----------
def clapper(l, cx, cy, s, seed):
    shape(l, [(cx - 70 * s, cy - 20 * s), (cx + 70 * s, cy - 20 * s), (cx + 70 * s, cy + 70 * s), (cx - 70 * s, cy + 70 * s)], (60, 52, 50), seed=seed, outline=3.5, hatch=False)
    shape(l, [(cx - 72 * s, cy - 32 * s), (cx + 66 * s, cy - 62 * s), (cx + 70 * s, cy - 42 * s), (cx - 68 * s, cy - 14 * s)], PAGE, seed=seed + 1, outline=3, hatch=False)
    d = ImageDraw.Draw(l)
    for i in range(4):
        x = cx - 50 * s + i * 34 * s
        stroke(d, [(x, cy - 24 * s - i * 7 * s), (x + 18 * s, cy - 44 * s - i * 7 * s)], 8 * s, color=(60, 52, 50), seed=seed + 5 + i, amp=0.6)


def button(l, cx, cy, s, seed):
    shape(l, ellipse_pts(cx, cy, 70 * s, 70 * s, 50)[:-1], RED, seed=seed, outline=4, hatch=False, shade=0.15)
    star = []
    for i in range(10):
        r = (42 if i % 2 == 0 else 18) * s
        a = -math.pi / 2 + i * math.pi / 5
        star.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    shape(l, star, PAGE, seed=seed + 1, outline=2.5, hatch=False, shade=0)


def cup(l, cx, cy, s, seed, t=0):
    d = ImageDraw.Draw(l)
    stroke(d, ellipse_pts(cx + 52 * s, cy + 10 * s, 22 * s, 26 * s, 30), 7 * s, color=(150, 120, 90), seed=seed + 2, amp=0.5, closed=True)
    shape(l, [(cx - 48 * s, cy - 40 * s), (cx + 48 * s, cy - 40 * s), (cx + 40 * s, cy + 55 * s), (cx - 40 * s, cy + 55 * s)], (196, 172, 140), seed=seed, outline=3.5, hatch=False)
    for i in range(3):
        x = cx - 25 * s + i * 25 * s
        stroke(d, [(x + 6 * math.sin(t * 3 + i + u / 6) * s, cy - 55 * s - u * 4 * s) for u in range(10)], 3, color=STONE, seed=seed + 9 + i, amp=0.5)


def notebook(l, cx, cy, s, seed):
    shape(l, [(cx - 55 * s, cy - 70 * s), (cx + 55 * s, cy - 70 * s), (cx + 55 * s, cy + 70 * s), (cx - 55 * s, cy + 70 * s)], PAGE, seed=seed, outline=3.5, hatch=False)
    d = ImageDraw.Draw(l)
    for i in range(6):
        d.ellipse((cx - 64 * s, cy - 58 * s + i * 22 * s, cx - 48 * s, cy - 46 * s + i * 22 * s), outline=INK + (255,), width=3)
    for i in range(5):
        stroke(d, [(cx - 35 * s, cy - 40 * s + i * 22 * s), (cx + 40 * s, cy - 40 * s + i * 22 * s)], 2.2, color=STONE, seed=seed + 20 + i, amp=0.8)


def timeline(l, d, x0, x1, y, seed, upto=1.0):
    pts = [(x0 + (x1 - x0) * u / 60, y) for u in range(int(60 * upto) + 1)]
    if len(pts) > 1:
        stroke(d, pts, 6, seed=seed, amp=2.0)


ICONS = [(clapper, 'television'), (button, 'politics'), (cup, 'odd jobs'), (notebook, 'writing')]


def s12(t, D):
    img = paper()
    d = ImageDraw.Draw(img)
    b = boil(t)
    timeline(img, d, 140, 1780, 700, 31, ease(t / 1.2))
    for i, (fn, label) in enumerate(ICONS):
        t0 = 0.8 + i * 1.15
        p = ease((t - t0) / 0.5)
        if p <= 0:
            continue
        x = 340 + i * 420
        stroke(d, [(x, 700), (x, 660)], 5, seed=40 + i, amp=0.5)
        s = 1.2 * (0.6 + 0.4 * p)
        if fn is cup:
            fn(img, x, 520, s, seed=b * 9 + i, t=t)
        else:
            fn(img, x, 520, s, seed=b * 9 + i)
        ink_text(img, (x, 770), label, F_CAP, fill=MUTED, alpha=int(255 * p))
    ink_text(img, (W / 2, 170), 'His early twenties', F_HEAD, alpha=int(255 * ease(t / 0.8)))
    return img.convert('RGB')


def letter(l, cx, cy, ang, seed, rejected=0.0):
    w_, h_ = 460, 580
    t = Image.new('RGBA', (w_ + 40, h_ + 40), (0, 0, 0, 0))
    shape(t, [(20, 20), (20 + w_, 20), (20 + w_, 20 + h_), (20, 20 + h_)], PAGE, seed=seed, outline=3.5, hatch=False, shade=0.08)
    td = ImageDraw.Draw(t)
    for i in range(9):
        L = w_ - 120 - (seed * 37 + i * 53) % 120
        stroke(td, [(70, 90 + i * 46), (70 + L, 90 + i * 46)], 2.4, color=STONE, seed=seed + i, amp=0.8)
    if rejected > 0:
        stamp(t, w_ / 2 + 20, h_ / 2 + 80, 'REJECTED', ang=-14, alpha=int(255 * rejected), scale=1.8)
    t = t.rotate(ang, resample=Image.BICUBIC, expand=True)
    l.alpha_composite(t, (int(cx - t.width / 2), int(cy - t.height / 2)))


def s13(t, D):
    img = paper()
    n = 7
    for i in range(n):
        t0 = i * 0.62
        if t < t0:
            continue
        p = ease((t - t0) / 0.4)
        ang = ((i * 37) % 13 - 6) * 1.1
        cx = W / 2 + ((i * 53) % 9 - 4) * 14
        cy = lerp(-400, 640 - i * 14, p)
        letter(img, cx, cy, ang, seed=11 + i, rejected=ease((t - t0 - 0.35) / 0.15))
    if t > 3.4:
        ink_text(img, (W / 2, 120), 'Rejection after rejection', F_HEAD, alpha=int(255 * ease((t - 3.4) / 0.6)))
    return img.convert('RGB')


E10 = Image.open(os.path.join(B3, 'E10.png')).convert('RGB').resize((2304, 1296), Image.LANCZOS)
F_YEAR = font('Fraunces700.woff2', 120)


def s14(t, D):
    """The timeline reaches 2014, then the page opens onto the painted fleet over Mars."""
    if t < 1.5:
        img = paper()
        d = ImageDraw.Draw(img)
        timeline(img, d, 140, 1780, 700, 31, 1.0)
        x = lerp(340, 1500, ease(t / 1.1))
        stroke(d, [(x, 700), (x, 640)], 6, seed=7, amp=0.5)
        ink_text(img, (x, 560), '2014', F_YEAR, fill=RUST, alpha=int(255 * ease(t / 0.4)))
        return img.convert('RGB')
    k = ease((t - 1.5) / (D - 1.5))
    if t < 1.9:
        a_ = s14(1.49, D); b_ = s14(1.9, D)
        return Image.blend(a_, b_, ease((t - 1.5) / 0.4))
    img = kenburns(E10, k, 1.0, 1.12, (0.5, 0.55), (0.5, 0.48)).convert('RGBA')
    d = FadeDraw(img)
    a = int(255 * ease((t - 1.9) / 0.6))
    d.text((W / 2, 150), '2014', font=F_YEAR, fill=(243, 235, 221, a), anchor='mm')
    if t > 2.8:
        ac = int(255 * ease((t - 2.8) / 0.6))
        d.text((W / 2, 980), 'an epic rebellion set among the stars', font=F_CAP, fill=(243, 235, 221, ac), anchor='mm')
    return img.convert('RGB')


SPINE_COLS = [(150, 84, 58), (94, 116, 136), (122, 132, 92), (120, 110, 100), (176, 140, 80), (72, 70, 76), (140, 70, 64)]


def make_shelf():
    Wd = 3400
    img = Image.new('RGBA', (Wd, H), (0, 0, 0, 0))
    r = np.random.default_rng(12)
    for row, base in enumerate((330, 640, 950)):
        x = 60
        while x < Wd - 120:
            w_ = r.integers(46, 92)
            h_ = r.integers(190, 262)
            col = SPINE_COLS[r.integers(len(SPINE_COLS))]
            shape(img, [(x, base - h_), (x + w_, base - h_), (x + w_, base), (x, base)], col, seed=int(x + row * 7), outline=3, hatch=False, shade=0.18, amp=0.8)
            d = ImageDraw.Draw(img)
            for k in (0.18, 0.82):
                stroke(d, [(x + 6, base - h_ * k), (x + w_ - 6, base - h_ * k)], 2.2, color=tuple(int(c * 0.7) for c in col), seed=int(x + k * 10), amp=0.4)
            x += w_ + r.integers(2, 8)
        shape(img, [(20, base), (Wd - 20, base), (Wd - 20, base + 36), (20, base + 36)], WOOD, seed=200 + row, outline=4, hatch=False, shade=0.2, amp=1.5)
    return img


SHELF = make_shelf()


def s15(t, D):
    img = paper()
    x = lerp(0, SHELF.width - W, ease(t / D))
    img.alpha_composite(SHELF.crop((int(x), 0, int(x) + W, H)))
    return img.convert('RGB')


def arena(l, cx, cy, s, seed):
    for i, (rx, ry, col) in enumerate(((170, 70, (176, 140, 80)), (130, 52, (196, 168, 110)), (88, 34, (214, 190, 140)))):
        shape(l, ellipse_pts(cx, cy + i * 10, rx * s, ry * s, 50)[:-1], col, seed=seed + i, outline=3.5, hatch=False, shade=0.12)


def wall(l, cx, cy, s, seed):
    shape(l, [(cx - 180 * s, cy - 90 * s), (cx + 180 * s, cy - 90 * s), (cx + 180 * s, cy + 80 * s), (cx - 180 * s, cy + 80 * s)], STONE, seed=seed, outline=4, hatch=False, shade=0.12)
    d = ImageDraw.Draw(l)
    for j in range(4):
        y = cy - 90 * s + (j + 1) * 34 * s
        stroke(d, [(cx - 176 * s, y), (cx + 176 * s, y)], 2.4, seed=seed + j, amp=0.8)
    for i in range(-4, 5):
        shape(l, [(cx + i * 40 * s - 14 * s, cy - 90 * s), (cx + i * 40 * s + 14 * s, cy - 90 * s), (cx + i * 40 * s + 14 * s, cy - 120 * s), (cx + i * 40 * s - 14 * s, cy - 120 * s)], STONE, seed=seed + 20 + i, outline=3, hatch=False, shade=0)
    shape(l, [(cx - 45 * s, cy + 80 * s), (cx - 45 * s, cy - 10 * s), (cx, cy - 45 * s), (cx + 45 * s, cy - 10 * s), (cx + 45 * s, cy + 80 * s)], (60, 44, 34), seed=seed + 40, outline=3.5, hatch=False, shade=0)


def tower(l, cx, cy, s, seed, t):
    beam_a = math.sin(t * 1.4) * 0.45
    L = 260 * s
    tip = (cx, cy - 120 * s)
    beam = [tip, (tip[0] + math.cos(-math.pi / 2 + beam_a - 0.22) * L * -1 if False else tip[0] + math.sin(beam_a - 0.22) * L, tip[1] - math.cos(beam_a - 0.22) * L),
            (tip[0] + math.sin(beam_a + 0.22) * L, tip[1] - math.cos(beam_a + 0.22) * L)]
    shape(l, beam, (240, 220, 150), seed=seed + 9, outline=0, hatch=False, shade=0, alpha=170)
    shape(l, [(cx - 40 * s, cy - 110 * s), (cx + 40 * s, cy - 110 * s), (cx + 55 * s, cy + 90 * s), (cx - 55 * s, cy + 90 * s)], (72, 70, 76), seed=seed, outline=4, hatch=False, shade=0.15)
    shape(l, [(cx - 58 * s, cy - 140 * s), (cx + 58 * s, cy - 140 * s), (cx + 58 * s, cy - 106 * s), (cx - 58 * s, cy - 106 * s)], (96, 92, 100), seed=seed + 1, outline=3.5, hatch=False, shade=0)


def s16(t, D):
    img = paper()
    b = boil(t)
    items = [(arena, 'arenas', 0.2), (wall, 'walled cities', 1.6), (tower, 'cruel governments', 3.2)]
    for i, (fn, label, t0) in enumerate(items):
        p = ease((t - t0) / 0.6)
        if p <= 0:
            continue
        x = 400 + i * 560
        s = 0.7 + 0.3 * p
        shape(img, ellipse_pts(x, 520, 240, 240, 60)[:-1], (232, 220, 196), seed=60 + i, outline=3, hatch=False, shade=0, alpha=int(255 * p))
        if fn is tower:
            fn(img, x, 560, s, b * 3 + i, t)
        else:
            fn(img, x, 560, s, b * 3 + i)
        ink_text(img, (x, 820), label, F_CAP, fill=MUTED, alpha=int(255 * p))
    ink_text(img, (W / 2, 140), 'Young adult dystopias', F_HEAD, alpha=int(255 * ease(t / 0.6)))
    return img.convert('RGB')


E09A = Image.open(os.path.join(B3, 'E09A.png')).convert('RGB').resize((2304, 1296), Image.LANCZOS)


def blot_mask(cx, cy, r, seed):
    m = Image.new('L', (W, H), 0)
    if r > 0:
        pts = wobble(ellipse_pts(cx, cy, r, r * 0.86, 90)[:-1], seed, amp=r * 0.06, closed=True)
        ImageDraw.Draw(m).polygon(pts, fill=255)
        for i in range(0):
            a = i * 0.63 + seed
            d = r * (1.0 + 0.08 * (i % 3))
            rr = r * 0.12
            x, y = cx + math.cos(a) * d, cy + math.sin(a) * d * 0.86
            ImageDraw.Draw(m).ellipse((x - rr, y - rr, x + rr, y + rr), fill=255)
    return m.filter(ImageFilter.GaussianBlur(2))


def s18(t, D):
    """Ink floods the page and opens onto a real battlefield: war should feel like war."""
    bf = kenburns(E09A, ease(t / D), 1.0, 1.08, (0.5, 0.55), (0.5, 0.5)).convert('RGBA')
    if t > 1.4:
        return bf.convert('RGB')
    img = paper()
    r = lerp(0, 1400, ease(t / 1.4))
    ink_layer = Image.new('RGBA', (W, H), (34, 24, 20, 255))
    img.paste(ink_layer, (0, 0), blot_mask(W / 2, H / 2, r, 3))
    inner = blot_mask(W / 2, H / 2, max(0, r - 90), 3)
    img.paste(bf, (0, 0), inner)
    return img.convert('RGB')


# act-local start times (narration: clip 4 starts at 0.0, clip 5 at 23.8)
SHOTS = [(0.0, s11, False), (6.3, s12, False), (13.3, s13, False), (18.8, s14, True),
         (23.8, s15, False), (28.1, s16, False), (34.3, s17, False), (39.3, s18, True)]
END = 44.6
XF = 0.25


def frame(t):
    starts = [s for s, _, _ in SHOTS] + [END]
    i = max(j for j in range(len(SHOTS)) if starts[j] <= t)

    def render(j, tt):
        s0, fn, vig = SHOTS[j]
        D = starts[j + 1] - s0
        return finish(fn(min(max(tt - s0, 0), D + XF), D), vig)
    cur = render(i, t)
    if i + 1 < len(SHOTS) and starts[i + 1] - t < XF and SHOTS[i + 1][1] is not s18:
        w = ease((t - (starts[i + 1] - XF)) / (2 * XF))
        cur = (cur * (1 - w) + render(i + 1, t) * w).astype(np.uint8)
    elif i > 0 and t - starts[i] < XF and SHOTS[i][1] is not s18:
        w = ease((t - (starts[i] - XF)) / (2 * XF))
        cur = (render(i - 1, t) * (1 - w) + cur * w).astype(np.uint8)
    return cur


def main():
    mode = sys.argv[1]
    if mode == 'stills':
        for s in sys.argv[2:]:
            Image.fromarray(frame(float(s))).save(os.path.join(HERE, f'still_{s}.png'))
        return
    out = sys.argv[2]
    wav = os.path.join(HERE, 'act2_audio.wav')
    lst = os.path.join(HERE, 'act2_audio.txt')
    with open(lst, 'w') as fh:
        for n in (4, 5):
            fh.write(f"file '{os.path.join(AUD, f'{n}.wav')}'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-ar', '48000', '-ac', '2', wav], check=True)
    n = int(round(END * FPS))
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for f in range(n):
        p.stdin.write(frame(f / FPS).tobytes())
        if f % 150 == 0:
            print(f'frame {f}/{n}', flush=True)
    p.stdin.close()
    p.wait()
    print('done', out)


if __name__ == '__main__':
    main()
