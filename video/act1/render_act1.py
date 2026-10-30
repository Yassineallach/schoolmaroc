"""Act 1 — The Mines (0:00–0:57.7). Renders frames and pipes them to ffmpeg.

Usage: python3 render_act1.py stills t1 t2 ...   -> writes still_<t>.png
       python3 render_act1.py video out.mp4       -> full render with audio
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

W, H, FPS = 1920, 1080, 30
ROOT = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.dirname(ROOT)
A3 = os.path.join(SCR, 'assets', 'v3')
B2 = os.path.join(SCR, 'batch2', 'c39d8063-Assets2')
AUD = os.path.join(SCR, 'rar', 'ac0d80b8-voxcpm_clips_texts_20261029_1949')
FONTS = os.path.join(SCR, 'fonts')

IVORY = (243, 235, 221)
BROWN = (59, 42, 32)
GOLD = (196, 154, 69)
RED = (163, 59, 46)
RUST = (184, 100, 63)
MUTED = (90, 70, 54)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


F_TITLE = font('Fraunces700.woff2', 190)
F_HEAD = font('Fraunces700.woff2', 72)
F_LABEL = font('Inter600.woff2', 34)
F_SMALL = font('Inter600.woff2', 24)
F_WORDS = font('Inter600.woff2', 44)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


def load(path):
    return Image.open(path).convert('RGBA' if path.endswith('.png') else 'RGB')


# ---------- shared textures ----------
rng = np.random.default_rng(7)
_grain = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
_grain = np.asarray(Image.fromarray(((_grain * 40) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.8)), np.float32)
GRAIN = ((_grain - 128) / 128.0)[..., None]
yy, xx = np.mgrid[0:H, 0:W]
_r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
VIGNETTE = (1 - 0.32 * np.clip(_r - 0.55, 0, 1) ** 1.4)[..., None].astype(np.float32)


def finish(img, vignette=True):
    a = np.asarray(img.convert('RGB'), np.float32)
    a = a * (1 + 0.035 * GRAIN)
    if vignette:
        a = a * VIGNETTE
    return a.clip(0, 255).astype(np.uint8)


def paper():
    base = Image.new('RGB', (W, H), IVORY)
    return base


def kenburns(img, t, s0, s1, c0, c1):
    """img larger than frame; s = zoom (1 = fit width), c = centre in img fraction."""
    iw, ih = img.size
    s = lerp(s0, s1, t)
    cw = iw / s
    ch = cw * H / W
    cx = lerp(c0[0], c1[0], t) * iw
    cy = lerp(c0[1], c1[1], t) * ih
    x0 = min(max(cx - cw / 2, 0), iw - cw)
    y0 = min(max(cy - ch / 2, 0), ih - ch)
    return img.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BICUBIC)


def tint(fig, mult=0.9, warm=(1.0, 0.95, 0.88)):
    a = np.asarray(fig, np.float32).copy()
    a[..., 0] *= mult * warm[0]
    a[..., 1] *= mult * warm[1]
    a[..., 2] *= mult * warm[2]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


def fit_h(fig, h):
    return fig.resize((round(fig.width * h / fig.height), h), Image.LANCZOS)


def shadow(canvas, cx, y, w):
    sh = Image.new('L', (int(w * 1.4), 60), 0)
    ImageDraw.Draw(sh).ellipse((0, 0, sh.width - 1, 59), fill=120)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    blk = Image.new('RGBA', sh.size, (20, 12, 8, 0))
    blk.putalpha(sh)
    canvas.alpha_composite(blk, (int(cx - sh.width / 2), int(y - 30)))


# ---------- assets ----------
E01 = load(os.path.join(B2, 'E01.png'))
E01 = E01.resize((1920, round(E01.height * 1920 / E01.width)), Image.LANCZOS)
VISOR = load(os.path.join(A3, 'C01C_visor_v2.png')).resize((2304, 1296), Image.LANCZOS)
E02 = load(os.path.join(B2, 'E02.png')).resize((2304, 1296), Image.LANCZOS)
E03 = load(os.path.join(B2, 'E03.png')).resize((2496, 1404), Image.LANCZOS)
E03_DARK = ImageEnhance.Brightness(E03.filter(ImageFilter.GaussianBlur(3))).enhance(0.55)
DARROW = tint(fit_h(load(os.path.join(A3, 'C01A_standing.png')), 800), 0.88)
NAROL = tint(fit_h(load(os.path.join(ROOT, 'src', 'narol.png')), 760), 0.88)
CLIMB = tint(fit_h(load(os.path.join(A3, 'C01B_climbing.png')), 1080), 0.92)
REAPER = fit_h(load(os.path.join(ROOT, 'src', 'reaper.png')), 900)
MINER_SIL = fit_h(load(os.path.join(A3, 'C01A_standing.png')), 820)
TITLE_BG = ImageEnhance.Brightness(E01.crop((0, 1500, 1920, 2580)).filter(ImageFilter.GaussianBlur(5))).enhance(0.42)


def silhouette(fig, body=(26, 20, 18), rim=RED, reveal=0.0):
    a = np.asarray(fig, np.float32)
    alpha = a[..., 3]
    out = np.zeros_like(a)
    col = np.array(body, np.float32)
    out[..., :3] = col * (1 - reveal) + a[..., :3] * 0.55 * reveal
    out[..., 3] = alpha
    sh = np.zeros_like(alpha)
    sh[:, 7:] = alpha[:, :-7]
    edge = np.clip(alpha - sh, 0, 255) / 255.0
    edge = np.asarray(Image.fromarray((edge * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32)[..., None] / 255.0
    out[..., :3] = out[..., :3] * (1 - edge) + np.array(rim, np.float32) * edge
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGBA')


SIL_MINER = silhouette(MINER_SIL)
SIL_REAPER = silhouette(REAPER)


def alpha_scale(img, k):
    if k >= 1:
        return img
    a = np.asarray(img).copy()
    a[..., 3] = (a[..., 3].astype(np.float32) * max(k, 0)).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')


# ---------- drawing helpers ----------
def leaf(d, cx, cy, ang, L=46, Wd=17, fill=GOLD, alpha=255):
    pts = []
    for i in range(24):
        u = i / 23 * math.pi * 2
        x = math.cos(u) * L / 2
        y = math.sin(u) * Wd / 2 * (1 - 0.35 * math.cos(u))
        pts.append((cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)))
    d.polygon(pts, fill=fill + (alpha,), outline=BROWN + (alpha,), width=3)


def laurel(d, cx, cy, R, progress, scale=1.0, alpha=255):
    n = 11
    shown = progress * n * 2
    k = 0
    for side in (-1, 1):
        for i in range(n):
            a0 = math.radians(115 + i * 13.5)
            ang = math.pi - a0 if side == 1 else a0
            px = cx + side * -math.cos(a0) * R * -1 if False else cx + (-math.cos(a0) * R if side == -1 else math.cos(a0) * R * -1 * -1)
            px = cx + (math.cos(a0) * R if side == -1 else -math.cos(a0) * R)
            py = cy + math.sin(a0) * R
            vis = min(max(shown - k, 0), 1)
            if vis > 0:
                tang = (a0 + math.pi / 2) if side == -1 else (math.pi - a0 - math.pi / 2)
                leaf(d, px, py, tang + side * 0.5, L=46 * scale, Wd=17 * scale, alpha=int(alpha * vis))
            k += 1
    if progress > 0.05:
        st = ease((progress - 0.05) / 0.4)
        d.arc((cx - R, cy - R, cx + R, cy + R), 115, 115 + 13.5 * (n - 1) * st, fill=BROWN + (alpha,), width=int(4 * scale))
        d.arc((cx - R, cy - R, cx + R, cy + R), 65 - 13.5 * (n - 1) * st, 65, fill=BROWN + (alpha,), width=int(4 * scale))


def text_center(d, xy, s, f, fill, spacing=0):
    if spacing:
        widths = [d.textlength(ch, font=f) for ch in s]
        total = sum(widths) + spacing * (len(s) - 1)
        x = xy[0] - total / 2
        for ch, w in zip(s, widths):
            d.text((x, xy[1]), ch, font=f, fill=fill, anchor='lm')
            x += w + spacing
    else:
        d.text(xy, s, font=f, fill=fill, anchor='mm')


def crate(d, x, y, w, h, label):
    d.rectangle((x, y, x + w, y + h), fill=(164, 112, 70), outline=BROWN, width=4)
    d.line((x, y, x + w, y + h), fill=BROWN, width=3)
    d.line((x + w, y, x, y + h), fill=BROWN, width=3)
    d.rectangle((x + w * 0.12, y + h * 0.38, x + w * 0.88, y + h * 0.62), fill=IVORY, outline=BROWN, width=2)
    d.text((x + w / 2, y + h / 2), label, font=F_SMALL, fill=BROWN, anchor='mm')


# ---------- shots ----------
def s1(t, D):
    k = ease(t / D)
    y = lerp(0, 1500, k)
    return E01.crop((0, y, 1920, y + 1080)).convert('RGB')


def s2(t, D):
    return kenburns(VISOR, ease(t / D), 1.0, 1.14, (0.5, 0.5), (0.47, 0.55)).convert('RGB')


def s3(t, D):
    img = paper().convert('RGBA')
    d = ImageDraw.Draw(img)
    laurel(d, W / 2, 430, 170, ease(t / 2.4))
    if t > 0.6:
        a = int(255 * ease((t - 0.6) / 0.8))
        text_center(d, (W / 2, 150), 'THE LAUREL', F_HEAD, BROWN + (a,))
    labels = ['FOOD', 'WATER', 'MEDICINE', 'FOOD']
    for i, lab in enumerate(labels):
        t0 = 2.4 + i * 0.45
        if t > t0:
            p = ease((t - t0) / 0.5)
            x = W / 2 - 490 + i * 250
            yy0 = lerp(560, 690, p)
            crate(d, x, yy0, 230, 150, lab)
    if t > 4.4:
        a = int(255 * ease((t - 4.4) / 0.6))
        text_center(d, (W / 2, 930), 'FOR THE HARDEST-WORKING CLAN  ·  LYKOS', F_LABEL, MUTED + (a,), spacing=3)
    return img.convert('RGB')


def s4(t, D):
    k = ease(t / D)
    bg = kenburns(E03_DARK, k, 1.0, 1.08, (0.5, 0.55), (0.52, 0.55)).convert('RGBA')
    shadow(bg, 610, 1020, NAROL.width * 0.6)
    shadow(bg, 1330, 1030, DARROW.width * 0.7)
    nx = int(lerp(330, 345, k))
    bg.alpha_composite(NAROL, (nx, 1020 - NAROL.height))
    bg.alpha_composite(DARROW, (1330 - DARROW.width // 2, 1030 - DARROW.height))
    return bg.convert('RGB')


CLANS = [('GAMMA', 0.62), ('LYKOS', 0.95), ('OMICRON', 0.48), ('UPSILON', 0.55)]


def s5(t, D):
    img = paper().convert('RGBA')
    d = ImageDraw.Draw(img)
    text_center(d, (W / 2, 120), 'WHO WINS THE LAUREL?', F_HEAD, BROWN)
    base, maxh, bw = 900, 560, 220
    xs = [W / 2 - 510 + i * 340 for i in range(4)]
    for i, (name, v) in enumerate(CLANS):
        p = ease((t - i * 0.15) / 1.2)
        h = maxh * v * p
        col = RUST if name == 'LYKOS' else (150, 132, 112)
        d.rectangle((xs[i] - bw / 2, base - h, xs[i] + bw / 2, base), fill=col, outline=BROWN, width=4)
        d.text((xs[i], base + 40), name, font=F_LABEL, fill=BROWN, anchor='mm')
    # laurel goes to Lykos first, then slides to Gamma
    if t > 1.6:
        a = int(255 * ease((t - 1.6) / 0.4))
        slide = ease((t - 2.4) / 0.9)
        lx = lerp(xs[1], xs[0], slide)
        top_l = base - maxh * CLANS[1][1]
        top_g = base - maxh * CLANS[0][1]
        ly = lerp(top_l, top_g, slide) - 95
        laurel(d, lx, ly, 60, 1.0, scale=0.4, alpha=a)
    if t > 3.4:
        a = int(255 * ease((t - 3.4) / 0.5))
        d.text((xs[0], base - maxh * CLANS[0][1] - 190), 'RIGGED', font=F_LABEL, fill=RED + (a,), anchor='mm')
    return img.convert('RGB')


def s6(t, D):
    k = t / D
    img = kenburns(E02, ease(k), 1.03, 1.16, (0.5, 0.5), (0.5, 0.56))
    burst = 0
    for b in (0.0, 1.5, 3.0):
        if t >= b:
            burst = max(burst, math.exp(-(t - b) * 3.0))
    amp = 16 * burst
    dx = amp * math.sin(t * 61.0)
    dy = amp * math.cos(t * 47.0)
    img = img.transform((W, H), Image.AFFINE, (1, 0, -dx, 0, 1, -dy), resample=Image.BILINEAR)
    pulse = 0.5 + 0.5 * math.sin(t * math.pi * 2 * 1.6)
    red = Image.new('RGB', (W, H), RED)
    return Image.blend(img.convert('RGB'), red, 0.10 + 0.14 * pulse)


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
    total = sum(widths) + sp * (len(title) - 1)
    x = W / 2 - total / 2
    for i, (ch, w) in enumerate(zip(title, widths)):
        a = ease((t - 0.2 - i * 0.09) / 0.5)
        if a > 0:
            d.text((x, 470 + (1 - a) * 18), ch, font=F_TITLE, fill=IVORY + (int(255 * a),), anchor='lm')
        x += w + sp
    words = ['BRUTAL', 'DEFIANT', 'SOULFUL']
    for i, wd in enumerate(words):
        t0 = 2.3 + i * 0.8
        if t > t0:
            a = int(255 * ease((t - t0) / 0.5))
            text_center(d, (W / 2 - 420 + i * 420, 650), wd, F_WORDS, GOLD + (a,), spacing=8)
    return img.convert('RGB')


def s9(t, D):
    img = Image.new('RGBA', (W, H), (30, 34, 40, 255))
    k = ease((t - 1.2) / 2.2)
    m = SIL_MINER
    sc = lerp(1.0, 1.12, k)
    mm = m.resize((int(m.width * sc), int(m.height * sc)), Image.BILINEAR)
    if k < 1:
        img.alpha_composite(alpha_scale(mm, 1 - k), (W // 2 - mm.width // 2, 1010 - mm.height))
    if k > 0:
        rv = 0.35 * ease((t - 3.8) / 1.5)
        r = silhouette(REAPER, reveal=rv) if rv > 0.01 else SIL_REAPER
        img.alpha_composite(alpha_scale(r, k), (W // 2 - r.width // 2 + 40, 1030 - r.height))
    if t > 3.6:
        d = ImageDraw.Draw(img)
        a = int(255 * ease((t - 3.6) / 0.6))
        text_center(d, (1520, 520), 'THE REAPER', F_HEAD, (226, 205, 180, a))
    return img.convert('RGB')


def bez(p0, p1, p2, p3, n=120):
    out = []
    for i in range(n + 1):
        u = i / n
        out.append(((1 - u) ** 3 * p0[0] + 3 * (1 - u) ** 2 * u * p1[0] + 3 * (1 - u) * u * u * p2[0] + u ** 3 * p3[0],
                    (1 - u) ** 3 * p0[1] + 3 * (1 - u) ** 2 * u * p1[1] + 3 * (1 - u) * u * u * p2[1] + u ** 3 * p3[1]))
    return out


SC = 1.3
CW, CH = int(W * SC), int(H * SC)
SEG1 = bez((330, 1150), (330, 1010), (450, 900), (560, 872))
SEG2 = bez((732, 700), (1000, 560), (1500, 900), (1900, 700))
PATH = SEG1 + SEG2
GAP = len(SEG1)
SOC = (1900, 700)
MARS = (560, 700)


def s10(t, D):
    img = Image.new('RGBA', (CW, CH), IVORY + (255,))
    d = ImageDraw.Draw(img)
    # orbit rings around the Society
    for i, r in enumerate((150, 240, 330)):
        a = int(255 * ease((t - 1.6 - i * 0.25) / 0.6))
        if a:
            d.ellipse((SOC[0] - r, SOC[1] - r * 0.55, SOC[0] + r, SOC[1] + r * 0.55), outline=(150, 132, 112, a), width=3)
    # Mars and mine
    d.ellipse((MARS[0] - 170, MARS[1] - 170, MARS[0] + 170, MARS[1] + 170), fill=RUST, outline=BROWN, width=5)
    d.rectangle((200, 1150, 460, 1340), fill=(110, 70, 48), outline=BROWN, width=4)
    d.line((330, 1150, 330, 1340), fill=(240, 190, 110), width=4)
    d.text((330, 1380), 'MINES OF LYKOS', font=F_LABEL, fill=BROWN, anchor='mm')
    d.text((MARS[0], MARS[1] + 215), 'MARS', font=F_LABEL, fill=BROWN, anchor='mm')
    # gold centre
    g = ease((t - 3.4) / 0.8)
    if g:
        r = 70 * g
        d.ellipse((SOC[0] - r, SOC[1] - r, SOC[0] + r, SOC[1] + r), fill=GOLD, outline=BROWN, width=5)
        a = int(255 * g)
        d.text((SOC[0], SOC[1] - 400), 'THE SOCIETY', font=F_HEAD, fill=BROWN + (a,), anchor='mm')
    # route
    p = ease(t / 4.2)
    n = max(2, int(len(PATH) * p))
    d.line(PATH[:min(n, GAP)], fill=BROWN, width=8, joint='curve')
    if n > GAP + 1:
        d.line(PATH[GAP:n], fill=BROWN, width=8, joint='curve')
    for j, frac in enumerate((0.3, 0.6, 0.86)):
        idx = int(len(PATH) * frac)
        if n > idx:
            x, y = PATH[idx]
            a = int(255 * ease((n - idx) / 25))
            d.rectangle((x - 30, y - 40, x + 30, y + 40), fill=IVORY + (a,), outline=BROWN + (a,), width=4)
            d.text((x, y), ['I', 'II', 'III'][j], font=F_LABEL, fill=BROWN + (a,), anchor='mm')
    # camera pull-back from the mine to the full system
    k = ease(t / (D * 0.75))
    s = lerp(1.9, 1.0, k)
    cw, ch = CW / s, CH / s
    cx = lerp(420, CW / 2, k)
    cy = lerp(1120, CH / 2, k)
    x0 = min(max(cx - cw / 2, 0), CW - cw)
    y0 = min(max(cy - ch / 2, 0), CH - ch)
    return img.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BICUBIC).convert('RGB')


# (start, render_fn, vignette)
SHOTS = [(0.0, s1, True), (5.5, s2, True), (9.5, s3, False), (15.8, s4, True), (22.5, s5, False),
         (27.0, s6, True), (31.5, s7, True), (36.1, s8, True), (43.0, s9, True), (49.0, s10, False)]
END = 57.7
XF = 0.25  # half-length of crossfades


def frame(t):
    starts = [s for s, _, _ in SHOTS] + [END]
    i = max(j for j in range(len(SHOTS)) if starts[j] <= t)
    def render(j, tt):
        s0, fn, vig = SHOTS[j]
        D = starts[j + 1] - s0
        return finish(fn(min(max(tt - s0, 0), D + XF), D), vig)
    cur = render(i, t)
    if i + 1 < len(SHOTS) and starts[i + 1] - t < XF:
        nxt = render(i + 1, t)
        w = ease((t - (starts[i + 1] - XF)) / (2 * XF))
        cur = (cur * (1 - w) + nxt * w).astype(np.uint8)
    elif i > 0 and t - starts[i] < XF:
        prv = render(i - 1, t)
        w = ease((t - (starts[i] - XF)) / (2 * XF))
        cur = (prv * (1 - w) + cur * w).astype(np.uint8)
    # fade in from black at the very start
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
