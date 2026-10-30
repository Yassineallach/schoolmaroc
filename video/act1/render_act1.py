"""Act 1 — The Mines (0:00–0:57.7). Renders frames and pipes them to ffmpeg.

Usage: python3 render_act1.py stills t1 t2 ...   -> writes still_<t>.png
       python3 render_act1.py video out.mp4       -> full render with audio
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance, ImageOps
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ink
from ink import INK, shape, stroke, ink_text, ellipse_pts, wobble

W, H, FPS = 1920, 1080, 30
ROOT = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.dirname(ROOT)
A3 = os.path.join(SCR, 'assets', 'v3')
B2 = os.path.join(SCR, 'batch2', 'c39d8063-Assets2')
AUD = os.path.join(SCR, 'rar', 'ac0d80b8-voxcpm_clips_texts_20261029_1949')
FONTS = os.path.join(SCR, 'fonts')

IVORY = (243, 235, 221)
GOLD = (196, 154, 69)
RED = (163, 59, 46)
RUST = (184, 100, 63)
MUTED = (96, 74, 56)
STONE = (150, 132, 112)
WOOD = (150, 102, 62)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


F_TITLE = font('Fraunces700.woff2', 190)
F_HEAD = font('Fraunces700.woff2', 76)
F_SIGN = font('Fraunces700.woff2', 38)
F_CAP = font('Fraunces500i.woff2', 40)
F_CRATE = font('Fraunces700.woff2', 26)
F_WORDS = font('Inter600.woff2', 44)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


def boil(t):
    return int(t * 8)


def load(path):
    return Image.open(path).convert('RGBA')


# ---------- shared textures ----------
rng = np.random.default_rng(7)
_g = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
_g = np.asarray(Image.fromarray(((_g * 40) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.8)), np.float32)
GRAIN = ((_g - 128) / 128.0)[..., None]
yy, xx = np.mgrid[0:H, 0:W]
_r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
VIGNETTE = (1 - 0.32 * np.clip(_r - 0.55, 0, 1) ** 1.4)[..., None].astype(np.float32)
PAPER = ink.make_paper()


def finish(img, vignette=True):
    a = np.asarray(img.convert('RGB'), np.float32)
    a = a * (1 + 0.035 * GRAIN)
    if vignette:
        a = a * VIGNETTE
    return a.clip(0, 255).astype(np.uint8)


def paper_layer():
    return PAPER.convert('RGBA')


def kenburns(img, t, s0, s1, c0, c1, out=(W, H)):
    iw, ih = img.size
    s = lerp(s0, s1, t)
    cw = iw / s
    ch = cw * out[1] / out[0]
    cx = lerp(c0[0], c1[0], t) * iw
    cy = lerp(c0[1], c1[1], t) * ih
    x0 = min(max(cx - cw / 2, 0), iw - cw)
    y0 = min(max(cy - ch / 2, 0), ih - ch)
    return img.crop((x0, y0, x0 + cw, y0 + ch)).resize(out, Image.BICUBIC)


def grade(fig, mult=0.88, warm=(1.0, 0.94, 0.84), floor_dark=0.35):
    """Match a cut-out to the amber mine light: warm tint plus darker legs (light comes from the helmet lamps)."""
    a = np.asarray(fig, np.float32).copy()
    h = a.shape[0]
    g = np.linspace(1.0, 1.0 - floor_dark, h)[:, None]
    for c in range(3):
        a[..., c] *= mult * warm[c] * g
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


def fit_h(fig, h):
    return fig.resize((round(fig.width * h / fig.height), h), Image.LANCZOS)


def alpha_scale(img, k):
    if k >= 1:
        return img
    a = np.asarray(img).copy()
    a[..., 3] = (a[..., 3].astype(np.float32) * max(k, 0)).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')


def glow(canvas, cx, cy, r, color=(255, 196, 120), strength=0.45):
    g = Image.new('L', canvas.size, 0)
    ImageDraw.Draw(g).ellipse((cx - r, cy - r, cx + r, cy + r), fill=int(255 * strength))
    g = g.filter(ImageFilter.GaussianBlur(r * 0.6))
    col = Image.new('RGBA', canvas.size, color + (0,))
    col.putalpha(g)
    canvas.alpha_composite(col)


# ---------- assets ----------
E01 = load(os.path.join(B2, 'E01.png'))
E01 = E01.resize((1920, round(E01.height * 1920 / E01.width)), Image.LANCZOS)
VISOR = load(os.path.join(A3, 'C01C_visor_v2.png')).resize((2304, 1296), Image.LANCZOS)
E02 = load(os.path.join(B2, 'E02.png')).resize((2304, 1296), Image.LANCZOS)
E03 = load(os.path.join(B2, 'E03.png')).resize((2496, 1404), Image.LANCZOS)
TUNNEL = ImageEnhance.Brightness(E03.crop((0, 120, 1500, 964)).resize((2304, 1296), Image.LANCZOS).filter(ImageFilter.GaussianBlur(4))).enhance(0.62)
TUNNEL_CU = ImageEnhance.Brightness(TUNNEL.filter(ImageFilter.GaussianBlur(10))).enhance(0.8)
NAROL = grade(fit_h(load(os.path.join(ROOT, 'src', 'narol34.png')), 1500))
DARROW_SIDE = grade(ImageOps.mirror(fit_h(load(os.path.join(ROOT, 'src', 'darrowside.png')), 1400)))
NAROL_CU = grade(fit_h(load(os.path.join(ROOT, 'src', 'narolhead.png')), 1000), 0.9, floor_dark=0.2)
DARROW_CU = grade(fit_h(load(os.path.join(ROOT, 'src', 'darrowhead.png')), 1060), 0.95, (1.0, 0.96, 0.88), floor_dark=0.2)
CLIMB = grade(fit_h(load(os.path.join(A3, 'C01B_climbing.png')), 1080), 0.92, floor_dark=0.15)
REAPER = fit_h(load(os.path.join(ROOT, 'src', 'reaper.png')), 900)
MINER_SIL = fit_h(load(os.path.join(A3, 'C01A_standing.png')), 820)
TITLE_BG = ImageEnhance.Brightness(E01.crop((0, 1500, 1920, 2580)).filter(ImageFilter.GaussianBlur(5))).enhance(0.42)


def fg_rocks(seed=11):
    """Dark, soft foreground rock silhouettes (the guide's foreground layer)."""
    l = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(l)
    left = [(-40, H + 40), (-40, 720), (90, 690), (210, 760), (330, 880), (420, H + 40)]
    right = [(W + 40, H + 40), (W + 40, 640), (1820, 610), (1700, 700), (1610, 860), (1540, H + 40)]
    for pts, s in ((left, seed), (right, seed + 1)):
        d.polygon(wobble(pts, s, 14, closed=True), fill=(24, 15, 11, 255))
    return l.filter(ImageFilter.GaussianBlur(7))


FG_ROCKS = fg_rocks()


def silhouette(fig, body=(26, 20, 18), rim=RED, reveal=0.0):
    a = np.asarray(fig, np.float32)
    alpha = a[..., 3]
    out = np.zeros_like(a)
    out[..., :3] = np.array(body, np.float32) * (1 - reveal) + a[..., :3] * 0.55 * reveal
    out[..., 3] = alpha
    sh = np.zeros_like(alpha)
    sh[:, 7:] = alpha[:, :-7]
    edge = np.clip(alpha - sh, 0, 255) / 255.0
    edge = np.asarray(Image.fromarray((edge * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32)[..., None] / 255.0
    out[..., :3] = out[..., :3] * (1 - edge) + np.array(rim, np.float32) * edge
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGBA')


SIL_MINER = silhouette(MINER_SIL)
SIL_REAPER = silhouette(REAPER)


# ---------- hand-drawn graphics ----------
def leaf_pts(cx, cy, ang, L, Wd):
    pts = []
    for i in range(18):
        u = i / 17 * math.pi * 2
        x = math.cos(u) * L / 2
        y = math.sin(u) * Wd / 2 * (1 - 0.4 * math.cos(u))
        pts.append((cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)))
    return pts


def laurel(layer, cx, cy, R, progress, scale=1.0, alpha=255, seed=0):
    """Two inked branches curving up from the bottom, leaves budding along them."""
    d = ImageDraw.Draw(layer)
    n = 10
    st = ease(progress / 0.5)
    for side in (-1, 1):
        if st > 0:
            m = int(40 * st) + 1
            arc = []
            for i in range(m):
                a = math.radians(118 + 128 * i / 40)
                x = cx + math.cos(a) * R
                arc.append((x if side == -1 else 2 * cx - x, cy + math.sin(a) * R))
            if len(arc) > 1:
                stroke(d, arc, 4.5 * scale, seed=seed + side, amp=1.0, alpha=alpha)
        for i in range(n):
            vis = ease(progress * n * 1.25 - i)
            if vis <= 0:
                continue
            a = math.radians(124 + i * 12.5)
            px, py = cx + math.cos(a) * R, cy + math.sin(a) * R
            tang = a + math.pi / 2
            if side == 1:
                px = 2 * cx - px
                tang = math.pi - tang
            ang = tang + (0.8 if side == -1 else -0.8)
            shape(layer, leaf_pts(px, py, ang, 52 * scale * vis, 19 * scale * vis), GOLD, seed=seed + i * 7 + side, outline=2.4 * scale, hatch=False, amp=0.8, alpha=alpha)


def crate(layer, x, y, w, h, label, seed):
    shape(layer, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], WOOD, seed=seed, outline=4, amp=1.6)
    d = ImageDraw.Draw(layer)
    for k in (0.33, 0.66):
        stroke(d, [(x + 6, y + h * k), (x + w - 6, y + h * k)], 2.4, seed=seed + int(k * 10), amp=1.0)
    stroke(d, [(x + 8, y + 8), (x + w - 8, y + h - 8)], 3, seed=seed + 5, amp=1.2)
    shape(layer, [(x + w * 0.12, y + h * 0.36), (x + w * 0.88, y + h * 0.36), (x + w * 0.88, y + h * 0.64), (x + w * 0.12, y + h * 0.64)], (236, 224, 198), seed=seed + 9, outline=2, hatch=False, amp=0.8)
    ink_text(layer, (x + w / 2, y + h / 2), label, F_CRATE)


def heap_pts(cx, base, w, h, seed):
    r = np.random.default_rng(seed)
    pts = [(cx - w / 2, base)]
    for i in range(1, 16):
        u = i / 16
        pts.append((cx - w / 2 + w * u, base - h * math.sin(math.pi * u) ** 0.8 + r.uniform(-1, 1) * h * 0.06))
    pts.append((cx + w / 2, base))
    return pts


def stamp(layer, cx, cy, text, ang=-9, alpha=255):
    t = Image.new('RGBA', (420, 150), (0, 0, 0, 0))
    td = ImageDraw.Draw(t)
    stroke(td, [(14, 14), (406, 14), (406, 136), (14, 136)], 6, color=RED, seed=4, amp=1.5, closed=True)
    td.text((210, 77), text, font=F_HEAD, fill=RED + (255,), anchor='mm')
    a = np.asarray(t).copy()
    holes = np.random.default_rng(5).random(a.shape[:2]) < 0.16
    a[holes, 3] = 0
    a[..., 3] = (a[..., 3].astype(np.float32) * alpha / 255).astype(np.uint8)
    t = Image.fromarray(a, 'RGBA').rotate(ang, resample=Image.BICUBIC, expand=True)
    layer.alpha_composite(t, (int(cx - t.width / 2), int(cy - t.height / 2)))


# ---------- shots ----------
def s1(t, D):
    y = lerp(0, 1500, ease(t / D))
    return E01.crop((0, y, 1920, y + 1080)).convert('RGB')


def s2(t, D):
    return kenburns(VISOR, ease(t / D), 1.0, 1.14, (0.5, 0.5), (0.47, 0.55)).convert('RGB')


def s3(t, D):
    img = paper_layer()
    b = boil(t)
    if t > 0.3:
        ink_text(img, (W / 2, 150), 'The Laurel', F_HEAD, alpha=int(255 * ease((t - 0.3) / 0.8)))
    laurel(img, W / 2, 420, 165, ease(t / 2.6), seed=b * 31)
    for i, lab in enumerate(['FOOD', 'WATER', 'MEDICINE', 'FOOD']):
        t0 = 2.6 + i * 0.45
        if t > t0:
            p = ease((t - t0) / 0.5)
            crate(img, W / 2 - 520 + i * 265, lerp(560, 680, p), 240, 160, lab, seed=b * 13 + i * 3)
    if t > 4.6:
        ink_text(img, (W / 2, 930), 'a prize for the hardest-working clan', F_CAP, fill=MUTED, alpha=int(255 * ease((t - 4.6) / 0.6)))
    return img.convert('RGB')


def s4a(t, D):
    """Medium two-shot in a lamp-lit tunnel: Narol warns, Darrow listens, facing each other."""
    k = ease(t / D)
    bg = kenburns(TUNNEL, k, 1.0, 1.03, (0.42, 0.5), (0.44, 0.5)).convert('RGBA')
    glow(bg, 960, 330, 380, strength=0.35)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    breathe = 1 + 0.004 * math.sin(t * 2.2)
    n = NAROL.resize((NAROL.width, int(NAROL.height * breathe)), Image.BILINEAR)
    lay.alpha_composite(n, (int(560 - n.width / 2), 1520 - n.height + 90))
    lay.alpha_composite(DARROW_SIDE, (int(1230 - DARROW_SIDE.width / 2), 1500 - DARROW_SIDE.height + 90))
    s = lerp(1.0, 1.07, k)
    lay = lay.resize((int(W * s), int(H * s)), Image.BICUBIC)
    ox, oy = int((lay.width - W) / 2), int((lay.height - H) * 0.3)
    bg.alpha_composite(lay.crop((ox, oy, ox + W, oy + H)))
    bg.alpha_composite(FG_ROCKS)
    return bg.convert('RGB')


def closeup(fig, cx, t, D, lamp):
    k = ease(t / D)
    bg = kenburns(TUNNEL_CU, k, 1.05, 1.1, (0.5, 0.5), (0.5, 0.5)).convert('RGBA')
    glow(bg, lamp[0], lamp[1], 420, strength=0.3)
    s = lerp(1.0, 1.05, k)
    f = fig.resize((int(fig.width * s), int(fig.height * s)), Image.BICUBIC)
    bg.alpha_composite(f, (int(cx - f.width / 2), int(H - f.height + 60 * s)))
    return bg.convert('RGB')


def s4b(t, D):
    return closeup(NAROL_CU, 760, t, D, (1300, 250))


def s4c(t, D):
    return closeup(DARROW_CU, 1180, t, D, (700, 200))


CLANS = [('Gamma', 0.62), ('Lykos', 0.95), ('Omicron', 0.48), ('Upsilon', 0.55)]


def s5(t, D):
    img = paper_layer()
    b = boil(t)
    d = ImageDraw.Draw(img)
    ink_text(img, (W / 2, 120), 'Who wins the Laurel?', F_HEAD)
    base, maxh, bw = 800, 430, 300
    xs = [W / 2 - 600 + i * 400 for i in range(4)]
    stroke(d, [(120, base), (W - 120, base)], 4, seed=b * 5 + 1, amp=2.5)
    for i, (name, v) in enumerate(CLANS):
        p = ease((t - i * 0.15) / 1.3)
        if p > 0.02:
            col = RUST if name == 'Lykos' else STONE
            shape(img, heap_pts(xs[i], base, bw, maxh * v * p, 40 + i), col, seed=b * 11 + i, outline=4, light=(-1, -1.2))
            rr = np.random.default_rng(i)
            for j in range(5):
                rx = xs[i] + rr.uniform(-0.3, 0.3) * bw
                ry = base - rr.uniform(0.1, 0.55) * maxh * v * p
                shape(img, ellipse_pts(rx, ry, 18, 12, 14), tuple(int(c * 0.85) for c in col), seed=b * 3 + j + i * 9, outline=2.2, hatch=False, amp=1.0)
        stroke(d, [(xs[i], base), (xs[i], 945)], 7, color=(110, 76, 46), seed=b + i * 4, amp=1.0)
        shape(img, [(xs[i] - 105, 868), (xs[i] + 105, 862), (xs[i] + 108, 926), (xs[i] - 102, 930)], (214, 178, 128), seed=b * 7 + i, outline=3, hatch=False, amp=1.2)
        ink_text(img, (xs[i], 897), name, F_SIGN)

    def top(j):
        return base - maxh * CLANS[j][1]
    if t > 1.6:
        a = int(255 * ease((t - 1.6) / 0.4))
        sl = ease((t - 2.4) / 1.0)
        lx = lerp(xs[1], xs[0], sl)
        ly = lerp(top(1), top(0), sl) - 90 - 70 * math.sin(math.pi * sl)
        laurel(img, lx, ly, 62, 1.0, scale=0.42, alpha=a, seed=b * 17)
    if t > 3.5:
        stamp(img, xs[0] + 40, top(0) - 230, 'RIGGED', alpha=int(255 * ease((t - 3.5) / 0.25)))
    return img.convert('RGB')


def s6(t, D):
    img = kenburns(E02, ease(t / D), 1.03, 1.16, (0.5, 0.5), (0.5, 0.56))
    burst = 0
    for b in (0.0, 1.5, 3.0):
        if t >= b:
            burst = max(burst, math.exp(-(t - b) * 3.0))
    amp = 16 * burst
    dx, dy = amp * math.sin(t * 61.0), amp * math.cos(t * 47.0)
    img = img.transform((W, H), Image.AFFINE, (1, 0, -dx, 0, 1, -dy), resample=Image.BILINEAR)
    pulse = 0.5 + 0.5 * math.sin(t * math.pi * 2 * 1.6)
    return Image.blend(img.convert('RGB'), Image.new('RGB', (W, H), RED), 0.10 + 0.14 * pulse)


def s7(t, D):
    k = ease(t / D)
    bg = kenburns(E03, k, 1.15, 1.15, (0.5, 0.62), (0.5, 0.45)).convert('RGBA')
    rise = lerp(120, 0, ease(t / (D * 0.8)))
    bg.alpha_composite(CLIMB, (W // 2 - CLIMB.width // 2 + 120, int(H - CLIMB.height + 170 + rise)))
    return bg.convert('RGB')


def s8(t, D):
    img = kenburns(TITLE_BG.convert('RGB'), ease(t / D), 1.0, 1.06, (0.5, 0.5), (0.5, 0.5)).convert('RGBA')
    d = ImageDraw.Draw(img)
    title = 'RED RISING'
    widths = [d.textlength(ch, font=F_TITLE) for ch in title]
    sp = 18
    x = W / 2 - (sum(widths) + sp * (len(title) - 1)) / 2
    for i, (ch, w) in enumerate(zip(title, widths)):
        a = ease((t - 0.2 - i * 0.09) / 0.5)
        if a > 0:
            d.text((x, 470 + (1 - a) * 18), ch, font=F_TITLE, fill=IVORY + (int(255 * a),), anchor='lm')
        x += w + sp
    for i, wd in enumerate(['BRUTAL', 'DEFIANT', 'SOULFUL']):
        t0 = 2.3 + i * 0.8
        if t > t0:
            a = int(255 * ease((t - t0) / 0.5))
            cx = W / 2 - 420 + i * 420
            ws = [d.textlength(c, font=F_WORDS) for c in wd]
            x2 = cx - (sum(ws) + 8 * (len(wd) - 1)) / 2
            for c, w in zip(wd, ws):
                d.text((x2, 650), c, font=F_WORDS, fill=GOLD + (a,), anchor='lm')
                x2 += w + 8
    return img.convert('RGB')


def s9(t, D):
    img = Image.new('RGBA', (W, H), (30, 34, 40, 255))
    k = ease((t - 1.2) / 2.2)
    sc = lerp(1.0, 1.12, k)
    mm = SIL_MINER.resize((int(SIL_MINER.width * sc), int(SIL_MINER.height * sc)), Image.BILINEAR)
    if k < 1:
        img.alpha_composite(alpha_scale(mm, 1 - k), (W // 2 - mm.width // 2, 1010 - mm.height))
    if k > 0:
        rv = 0.35 * ease((t - 3.8) / 1.5)
        r = silhouette(REAPER, reveal=rv) if rv > 0.01 else SIL_REAPER
        img.alpha_composite(alpha_scale(r, k), (W // 2 - r.width // 2 + 40, 1030 - r.height))
    if t > 3.6:
        ink_text(img, (1520, 520), 'The Reaper', F_HEAD, fill=(226, 205, 180), alpha=int(255 * ease((t - 3.6) / 0.6)))
    return img.convert('RGB')


def bez(p0, p1, p2, p3, n=120):
    return [((1 - u) ** 3 * p0[0] + 3 * (1 - u) ** 2 * u * p1[0] + 3 * (1 - u) * u * u * p2[0] + u ** 3 * p3[0],
             (1 - u) ** 3 * p0[1] + 3 * (1 - u) ** 2 * u * p1[1] + 3 * (1 - u) * u * u * p2[1] + u ** 3 * p3[1])
            for u in (i / n for i in range(n + 1))]


SC = 1.3
CW, CH = int(W * SC), int(H * SC)
SOC = (1900, 700)
MARS = (560, 700)
SEG1 = wobble(bez((330, 1100), (330, 990), (450, 900), (560, 872)), 21, 2.0)
SEG2 = wobble(bez((732, 700), (1000, 560), (1500, 900), (1900, 700)), 22, 2.0)
PATH = SEG1 + SEG2
GAP = len(SEG1)
PATH_W = 7 * (1 + ink._noise(len(PATH), 5, 0.3))


def map_base():
    l = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(l)
    for i, r in enumerate((150, 240, 330)):
        stroke(d, ellipse_pts(SOC[0], SOC[1], r, r * 0.55, 90), 2.6, color=STONE, seed=60 + i, amp=1.5, closed=True)
    shape(l, ellipse_pts(MARS[0], MARS[1], 170, 170, 70)[:-1], RUST, seed=70, outline=5, light=(-1, -1))
    for cx_, cy_, rr in ((500, 650, 26), (610, 760, 18), (630, 640, 14)):
        stroke(d, ellipse_pts(cx_, cy_, rr, rr * 0.8, 24), 2.2, color=(130, 66, 40), seed=cx_, amp=1.0, closed=True)
    shape(l, [(200, 1100), (460, 1100), (460, 1270), (200, 1270)], (110, 70, 48), seed=71, outline=4)
    stroke(d, [(330, 1100), (330, 1270)], 4, color=(240, 190, 110), seed=72, amp=0.8)
    ink_text(l, (330, 1320), 'the mines of Lykos', F_CAP)
    ink_text(l, (MARS[0], MARS[1] - 220), 'Mars', F_CAP)
    return l


MAP_BASE = map_base()
PAPER_BIG = ink.make_paper(9).resize((CW, CH), Image.BICUBIC)


def book(layer, x, y, numeral, alpha, seed):
    shape(layer, [(x - 34, y - 44), (x + 34, y - 44), (x + 34, y + 44), (x - 34, y + 44)], (236, 224, 198), seed=seed, outline=3.5, hatch=False, amp=1.2, alpha=alpha)
    stroke(ImageDraw.Draw(layer), [(x - 24, y - 44), (x - 24, y + 44)], 3, seed=seed + 1, amp=0.6, alpha=alpha)
    ink_text(layer, (x + 5, y), numeral, F_SIGN, alpha=alpha)


def s10(t, D):
    img = PAPER_BIG.convert('RGBA')
    img.alpha_composite(MAP_BASE)
    d = ImageDraw.Draw(img)
    g = ease((t - 3.4) / 0.8)
    if g:
        r = 70 * g
        a = int(255 * g)
        for i in range(12):
            ang = i / 12 * math.pi * 2
            stroke(d, [(SOC[0] + math.cos(ang) * (r + 14), SOC[1] + math.sin(ang) * (r + 14)), (SOC[0] + math.cos(ang) * (r + 44), SOC[1] + math.sin(ang) * (r + 44))], 4, color=GOLD, seed=80 + i, amp=0.8, alpha=a)
        shape(img, ellipse_pts(SOC[0], SOC[1], r, r, 40)[:-1], GOLD, seed=81, outline=4, alpha=a, hatch=False)
        ink_text(img, (SOC[0], SOC[1] - 400), 'The Society', F_HEAD, alpha=a)
    n = max(2, int(len(PATH) * ease(t / 4.2)))
    for lo, hi in ((0, min(n, GAP)), (GAP, n)):
        for i in range(lo, hi - 1):
            d.line([PATH[i], PATH[i + 1]], fill=INK + (255,), width=int(PATH_W[i]))
    for j, frac in enumerate((0.14, 0.6, 0.86)):
        idx = int(len(PATH) * frac)
        if n > idx:
            x, y = PATH[idx]
            book(img, x, y, ['I', 'II', 'III'][j], int(255 * ease((n - idx) / 25)), seed=90 + j)
    k = ease(t / (D * 0.75))
    s = lerp(1.9, 1.0, k)
    cw, ch = CW / s, CH / s
    cx, cy = lerp(420, CW / 2, k), lerp(1080, CH / 2, k)
    x0 = min(max(cx - cw / 2, 0), CW - cw)
    y0 = min(max(cy - ch / 2, 0), CH - ch)
    return img.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BICUBIC).convert('RGB')


# ---------- flat explainer backgrounds (override the painted-environment shots) ----------
BG = (92, 60, 42)          # warm mine brown, sampled from the mine environment so flat shots fit the painted ones
BG_DISC = (132, 88, 56)
BG_GROUND = (66, 42, 30)
BG_DARK = (52, 38, 30)
BG_DEEP = (43, 37, 34)
GAS = (150, 168, 92)

FIG_NAROL = fit_h(load(os.path.join(ROOT, 'src', 'narol34.png')), 900)
FIG_DARROW_SIDE = ImageOps.mirror(fit_h(load(os.path.join(ROOT, 'src', 'darrowside.png')), 840))
FIG_NAROL_CU = fit_h(load(os.path.join(ROOT, 'src', 'narolhead.png')), 900)
FIG_DARROW_CU = fit_h(load(os.path.join(ROOT, 'src', 'darrowhead.png')), 940)
FIG_CLIMB = fit_h(load(os.path.join(A3, 'C01B_climbing.png')), 900)


def flat(color):
    return Image.new('RGBA', (W, H), color + (255,))


def disc(img, cx, cy, r, color=BG_DISC, seed=1):
    shape(img, ellipse_pts(cx, cy, r, r, 60)[:-1], color, seed=seed, outline=0, hatch=False, shade=0, amp=4)


def ground(img, y, seed=2):
    shape(img, [(-20, y), (W + 20, y), (W + 20, H + 20), (-20, H + 20)], BG_GROUND, seed=seed, outline=3.5, hatch=False, shade=0, amp=3)


def foot_shadow(img, cx, y, w):
    d = ImageDraw.Draw(img)
    d.ellipse((cx - w / 2, y - 14, cx + w / 2, y + 14), fill=(36, 22, 15, 150))


STRATA = [((196, 120, 78), 260), ((168, 96, 62), 520), ((206, 150, 96), 760), ((150, 84, 58), 1020),
          ((122, 72, 52), 1320), ((176, 108, 70), 1600), ((104, 64, 48), 1900), ((84, 54, 42), 2600)]


def make_section():
    """Flat, hand-inked cross-section of the Martian crust for the opening pan."""
    Hh = 2600
    img = Image.new('RGBA', (W, Hh), (226, 196, 160, 255))
    ImageDraw.Draw(img).rectangle((0, 230, W, Hh), fill=(196, 120, 78, 255))
    top = 230
    prev = top
    for i, (col, y) in enumerate(STRATA):
        r = np.random.default_rng(i)
        upper = [(x, prev + r.uniform(-18, 18)) for x in range(-200, W + 360, 160)] if i else [(x, top) for x in range(-200, W + 360, 160)]
        lower = [(W + 200, Hh + 40), (-200, Hh + 40)]
        shape(img, upper + lower, col, seed=100 + i, outline=3, hatch=False, shade=0, amp=6)
        prev = y
    d = ImageDraw.Draw(img)
    # surface details: low hills and a small headframe over the shaft
    shape(img, [(-20, top), (300, 170), (620, top)], (190, 112, 76), seed=120, outline=3, hatch=False, shade=0)
    shape(img, [(1250, top), (1600, 150), (1950, top)], (190, 112, 76), seed=121, outline=3, hatch=False, shade=0)
    for a, b in (((900, top), (960, 110)), ((1020, top), (960, 110)), ((925, 170), (995, 170))):
        stroke(d, [a, b], 6, seed=a[0] + b[1], amp=0.8)
    # the shaft
    shape(img, [(938, top), (982, top), (982, 2560), (938, 2560)], (60, 40, 30), seed=130, outline=3, hatch=False, shade=0, amp=1.5)
    for y in range(300, 2560, 140):
        d.ellipse((953, y - 7, 967, y + 7), fill=(240, 196, 110, 255))
    # side tunnels
    for (x0, x1, y) in ((300, 938, 640), (982, 1640, 980), (420, 938, 1450), (982, 1500, 1880)):
        shape(img, [(x0, y - 22), (x1, y - 22), (x1, y + 22), (x0, y + 22)], (60, 40, 30), seed=x0 + y, outline=2.5, hatch=False, shade=0, amp=2)
    # gas pockets
    for (cx, cy, rx, ry) in ((520, 1180, 150, 60), (1420, 1520, 180, 70), (700, 2050, 160, 60), (1250, 2300, 210, 80)):
        shape(img, ellipse_pts(cx, cy, rx, ry, 40)[:-1], GAS, seed=cx, outline=3, hatch=True, shade=0.25, amp=8)
    return img


SECTION = make_section()


def drill(img, cx, y):
    shape(img, [(cx - 34, y - 70), (cx + 34, y - 70), (cx + 34, y), (cx - 34, y)], (200, 168, 96), seed=140, outline=3, hatch=False, amp=1)
    shape(img, [(cx - 34, y), (cx + 34, y), (cx, y + 70)], (150, 150, 150), seed=141, outline=3, hatch=False, amp=1)
    ImageDraw.Draw(img).ellipse((cx - 9, y - 58, cx + 9, y - 40), fill=(255, 220, 140, 255))


def s1_flat(t, D):
    k = ease(t / D)
    y = lerp(0, 1480, k)
    img = SECTION.copy()
    drill(img, 960, lerp(320, 2100, ease(t / D)))
    return img.crop((0, int(y), W, int(y) + H)).convert('RGB')


def gas_cloud(img, cx, cy, r, seed):
    for i, (dx, dy, rr) in enumerate(((0, 0, 1.0), (-0.6, 0.2, 0.7), (0.6, 0.15, 0.75), (0.1, -0.45, 0.65))):
        shape(img, ellipse_pts(cx + dx * r, cy + dy * r, rr * r, rr * r * 0.8, 36)[:-1], GAS, seed=seed + i, outline=3, hatch=False, shade=0.2, amp=5, alpha=230)


def s2_flat(t, D):
    k = ease(t / D)
    img = flat(BG_DARK)
    disc(img, 760, 560, 430, (74, 54, 42), seed=3)
    gas_cloud(img, lerp(1750, 1450, k), 470, lerp(150, 230, k), seed=boil(t) * 5)
    s = lerp(1.0, 1.06, k)
    f = FIG_DARROW_CU.resize((int(FIG_DARROW_CU.width * s), int(FIG_DARROW_CU.height * s)), Image.BICUBIC)
    img.alpha_composite(f, (int(720 - f.width / 2), H - f.height + 40))
    return img.convert('RGB')


def s4a(t, D):
    k = ease(t / D)
    img = flat(BG)
    disc(img, 960, 500, 440, seed=4)
    ground(img, 975, seed=5)
    nx, dx = 770, 1180
    foot_shadow(img, nx, 975, 340)
    foot_shadow(img, dx, 978, 230)
    breathe = 1 + 0.004 * math.sin(t * 2.2)
    n = FIG_NAROL.resize((FIG_NAROL.width, int(FIG_NAROL.height * breathe)), Image.BILINEAR)
    img.alpha_composite(n, (int(nx - n.width / 2), 982 - n.height))
    img.alpha_composite(FIG_DARROW_SIDE, (int(dx - FIG_DARROW_SIDE.width / 2), 985 - FIG_DARROW_SIDE.height))
    s = lerp(1.0, 1.05, k)
    big = img.resize((int(W * s), int(H * s)), Image.BICUBIC)
    ox, oy = int((big.width - W) / 2), int((big.height - H) * 0.4)
    return big.crop((ox, oy, ox + W, oy + H)).convert('RGB')


def flat_closeup(fig, cx, t, D, seed):
    k = ease(t / D)
    img = flat(BG)
    disc(img, cx, 520, 470, seed=seed)
    s = lerp(1.0, 1.05, k)
    f = fig.resize((int(fig.width * s), int(fig.height * s)), Image.BICUBIC)
    img.alpha_composite(f, (int(cx - f.width / 2), int(H - f.height + 50 * s)))
    return img.convert('RGB')


def s4b(t, D):
    return flat_closeup(FIG_NAROL_CU, 820, t, D, 6)


def s4c(t, D):
    return flat_closeup(FIG_DARROW_CU, 1100, t, D, 7)


def gauge(img, cx, cy, R, val, seed):
    d = ImageDraw.Draw(img)
    shape(img, ellipse_pts(cx, cy, R + 26, R + 26, 70)[:-1], (120, 98, 70), seed=seed, outline=5, hatch=False, shade=0.12)
    shape(img, ellipse_pts(cx, cy, R, R, 70)[:-1], (236, 224, 198), seed=seed + 1, outline=4, hatch=False, shade=0)
    a0, a1 = math.radians(150), math.radians(390)
    red0 = a0 + (a1 - a0) * 0.72
    pts = [(cx + math.cos(a) * (R - 18), cy + math.sin(a) * (R - 18)) for a in np.linspace(red0, a1, 30)]
    pts += [(cx + math.cos(a) * (R - 60), cy + math.sin(a) * (R - 60)) for a in np.linspace(a1, red0, 30)]
    shape(img, pts, RED, seed=seed + 2, outline=2.5, hatch=False, shade=0, amp=1.5)
    for i in range(11):
        a = a0 + (a1 - a0) * i / 10
        stroke(d, [(cx + math.cos(a) * (R - 18), cy + math.sin(a) * (R - 18)), (cx + math.cos(a) * (R - 52), cy + math.sin(a) * (R - 52))], 4, seed=seed + 10 + i, amp=0.5)
    ink_text(img, (cx, cy + R * 0.42), 'GAS', F_SIGN)
    a = a0 + (a1 - a0) * val
    stroke(d, [(cx, cy), (cx + math.cos(a) * (R - 40), cy + math.sin(a) * (R - 40))], 9, color=(40, 30, 24), seed=seed + 30, amp=0.4)
    d.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=(40, 30, 24, 255))


def s6_flat(t, D):
    img = flat(BG_DEEP)
    burst = 0
    for b in (0.0, 1.5, 3.0):
        if t >= b:
            burst = max(burst, math.exp(-(t - b) * 3.0))
    val = min(0.97, lerp(0.35, 0.93, ease(t / 3.2)) + 0.03 * math.sin(t * 23) * burst)
    gauge(img, 960, 540, 330, val, seed=boil(t) * 7)
    amp = 14 * burst
    dx, dy = amp * math.sin(t * 61.0), amp * math.cos(t * 47.0)
    img = img.transform((W, H), Image.AFFINE, (1, 0, -dx, 0, 1, -dy), resample=Image.BILINEAR, fillcolor=BG_DEEP + (255,))
    pulse = 0.5 + 0.5 * math.sin(t * math.pi * 2 * 1.6)
    return Image.blend(img.convert('RGB'), Image.new('RGB', (W, H), RED), 0.06 + 0.12 * pulse * ease((t - 1.0) / 1.0))


FIG_STAND = fit_h(load(os.path.join(A3, 'C01A_standing.png')), 1000)


def ledge(img, y, seed=12):
    pts = [(-30, y + 20)] + [(x, y + np.random.default_rng(seed + x).uniform(-14, 14)) for x in range(60, W, 180)] + [(W + 30, y + 10), (W + 30, H + 30), (-30, H + 30)]
    shape(img, pts, (124, 76, 48), seed=seed, outline=4, hatch=False, shade=0, amp=3)
    lip = [(-30, y + 20)] + pts[1:-3] + [(W + 30, y + 10)] + [(W + 30, y + 46)] + [(x, yy + 34) for x, yy in reversed(pts[1:-3])] + [(-30, y + 54)]
    shape(img, lip, (150, 96, 62), seed=seed + 1, outline=0, hatch=False, shade=0, amp=2)


def s7(t, D):
    img = flat(BG)
    disc(img, 960, 300, 380, (176, 122, 72), seed=8)
    rise = lerp(520, 0, ease(t / (D * 0.75)))
    img.alpha_composite(FIG_STAND, (W // 2 - FIG_STAND.width // 2, int(90 + rise)))
    ledge(img, 800)
    return img.convert('RGB')


def s8_flat(t, D):
    img = flat(BG_DARK)
    d = ImageDraw.Draw(img)
    title = 'RED RISING'
    widths = [d.textlength(ch, font=F_TITLE) for ch in title]
    sp = 18
    x = W / 2 - (sum(widths) + sp * (len(title) - 1)) / 2
    for i, (ch, w) in enumerate(zip(title, widths)):
        a = ease((t - 0.2 - i * 0.09) / 0.5)
        if a > 0:
            d.text((x, 470 + (1 - a) * 18), ch, font=F_TITLE, fill=IVORY + (int(255 * a),), anchor='lm')
        x += w + sp
    for i, wd in enumerate(['BRUTAL', 'DEFIANT', 'SOULFUL']):
        t0 = 2.3 + i * 0.8
        if t > t0:
            a = int(255 * ease((t - t0) / 0.5))
            cx = W / 2 - 420 + i * 420
            ws = [d.textlength(c, font=F_WORDS) for c in wd]
            x2 = cx - (sum(ws) + 8 * (len(wd) - 1)) / 2
            for c, w in zip(wd, ws):
                d.text((x2, 650), c, font=F_WORDS, fill=GOLD + (a,), anchor='lm')
                x2 += w + 8
    return img.convert('RGB')


# (start, render_fn, vignette)
SHOTS = [(0.0, s1, True), (5.5, s2, True), (9.5, s3, False),
         (15.8, s4a, False), (18.6, s4b, False), (20.6, s4c, False),
         (22.5, s5, False), (27.0, s6, True), (31.5, s7, False), (36.1, s8, True), (43.0, s9, False), (49.0, s10, False)]
CUTS = {18.6, 20.6}  # hard cuts inside the conversation (shot / reverse shot)
END = 57.7
XF = 0.25


def frame(t):
    starts = [s for s, _, _ in SHOTS] + [END]
    i = max(j for j in range(len(SHOTS)) if starts[j] <= t)

    def render(j, tt):
        s0, fn, vig = SHOTS[j]
        D = starts[j + 1] - s0
        return finish(fn(min(max(tt - s0, 0), D + XF), D), vig)
    cur = render(i, t)
    if i + 1 < len(SHOTS) and starts[i + 1] - t < XF and starts[i + 1] not in CUTS:
        w = ease((t - (starts[i + 1] - XF)) / (2 * XF))
        cur = (cur * (1 - w) + render(i + 1, t) * w).astype(np.uint8)
    elif i > 0 and t - starts[i] < XF and starts[i] not in CUTS:
        w = ease((t - (starts[i] - XF)) / (2 * XF))
        cur = (render(i - 1, t) * (1 - w) + cur * w).astype(np.uint8)
    if t < 0.6:
        cur = (cur * ease(t / 0.6)).astype(np.uint8)
    return cur


def main():
    mode = sys.argv[1]
    if mode == 'stills':
        for s in sys.argv[2:]:
            Image.fromarray(frame(float(s))).save(os.path.join(ROOT, f'still_{s}.png'))
        return
    out = sys.argv[2]
    wav = os.path.join(ROOT, 'act1_audio.wav')
    lst = os.path.join(ROOT, 'act1_audio.txt')
    with open(lst, 'w') as fh:
        for n in (1, 2, 3):
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
