"""Hand-inked drawing helpers that follow the visual guide: organic outlines with controlled
irregularity and varying weight, flat fills with one shadow tone, sparse hatching, paper grain.
A `boil` seed that changes ~8 times a second gives the lines a subtle frame-by-frame life."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

INK = (59, 42, 32)
W, H = 1920, 1080


def _noise(n, seed, amp, freq=1.0):
    r = np.random.default_rng(abs(seed))
    out = np.zeros(n)
    x = np.linspace(0, 1, n)
    for k in (2, 5, 11):
        out += r.uniform(-1, 1) * np.sin(2 * math.pi * (k * freq * x + r.uniform(0, 1))) / k
    return out * amp


def resample(pts, step=5.0, closed=False):
    pts = list(pts) + ([pts[0]] if closed else [])
    out = [pts[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / step))
        for i in range(1, n + 1):
            out.append((x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n))
    return out


def wobble(pts, seed, amp=2.2, closed=False):
    p = resample(pts, closed=closed)
    n = len(p)
    if n < 3:
        return p
    a = np.array(p)
    d = np.gradient(a, axis=0)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-6)
    off = _noise(n, seed, amp, freq=max(1, n / 120))
    a = a + nrm * off[:, None]
    return [tuple(v) for v in a]


def stroke(draw, pts, width, color=INK, seed=0, amp=2.0, closed=False, alpha=255):
    """Ink line with varying weight (thicker mid-stroke, tapering ends)."""
    p = wobble(pts, seed, amp, closed)
    n = len(p)
    wv = _noise(n, seed + 99, 0.35) + 1.0
    col = tuple(color[:3]) + (alpha,)
    for i in range(n - 1):
        taper = 1.0 if closed else min(1.0, (i + 1) / 6, (n - i) / 6) * 0.6 + 0.4
        w = max(1, width * wv[i] * taper)
        draw.line([p[i], p[i + 1]], fill=col, width=int(round(w)))
        r = w / 2
        draw.ellipse((p[i][0] - r, p[i][1] - r, p[i][0] + r, p[i][1] + r), fill=col)


def shape(layer, pts, fill, seed=0, outline=3.5, shade=0.22, light=(-1, -1), hatch=True, amp=2.0, alpha=255):
    """Filled organic shape: base colour, one shadow tone on the side away from the light,
    a little hatching inside the shadow, and an inked outline."""
    p = wobble(pts, seed, amp, closed=True)
    xs = [q[0] for q in p]; ys = [q[1] for q in p]
    x0, y0, x1, y1 = int(min(xs)) - 6, int(min(ys)) - 6, int(max(xs)) + 7, int(max(ys)) + 7
    w, h = max(2, x1 - x0), max(2, y1 - y0)
    loc = [(q[0] - x0, q[1] - y0) for q in p]
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).polygon(loc, fill=255)
    mask = np.asarray(m) > 0
    size = max(w, h)
    dx, dy = int(-light[0] * size * shade), int(-light[1] * size * shade)
    dx, dy = max(-(w - 1), min(w - 1, dx)), max(-(h - 1), min(h - 1, dy))
    sh = np.zeros_like(mask)
    ys_, xs_ = slice(max(0, -dy), h - max(0, dy)), slice(max(0, -dx), w - max(0, dx))
    ys2, xs2 = slice(max(0, dy), h - max(0, -dy)), slice(max(0, dx), w - max(0, -dx))
    sh[ys2, xs2] = mask[ys_, xs_]
    shadow = mask & ~sh
    base = np.array(fill[:3], np.float32)
    dark = base * 0.72
    img = np.zeros((h, w, 4), np.float32)
    img[mask, :3] = base
    img[shadow, :3] = dark
    if hatch and shadow.sum() > 60:
        hl = Image.new('L', (w, h), 0)
        hd = ImageDraw.Draw(hl)
        r = np.random.default_rng(abs(seed) + 7)
        for k in range(-h, w, 10):
            hd.line([(k + r.uniform(-2, 2), h), (k + h * 0.6 + r.uniform(-2, 2), 0)], fill=110, width=2)
        hm = (np.asarray(hl) / 255.0) * shadow
        img[..., :3] = img[..., :3] * (1 - hm[..., None]) + np.array(INK, np.float32) * hm[..., None]
    img[..., 3] = mask * alpha
    tile = Image.fromarray(img.clip(0, 255).astype(np.uint8), 'RGBA')
    layer.alpha_composite(tile, (x0, y0))
    if outline:
        stroke(ImageDraw.Draw(layer), p, outline, seed=seed + 3, amp=0.6, closed=True, alpha=alpha)


def ellipse_pts(cx, cy, rx, ry, n=64, a0=0, a1=2 * math.pi):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def make_paper(seed=3):
    r = np.random.default_rng(abs(seed))
    low = r.normal(0, 1, (H // 24, W // 24)).astype(np.float32)
    low = np.asarray(Image.fromarray(((low * 30) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) - 128
    fine = r.normal(0, 1, (H, W)).astype(np.float32) * 5
    base = np.array([243, 233, 214], np.float32)
    a = base + (low * 0.07)[..., None] + fine[..., None]
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for _ in range(700):  # paper fibres
        x, y = r.uniform(0, W), r.uniform(0, H)
        L, ang = r.uniform(6, 22), r.uniform(0, math.pi)
        c = int(r.uniform(205, 228))
        d.line([(x, y), (x + L * math.cos(ang), y + L * math.sin(ang))], fill=(c, c - 8, c - 22), width=1)
    return img.filter(ImageFilter.GaussianBlur(0.5))


def ink_text(layer, xy, s, font, fill=INK, anchor='mm', alpha=255):
    """Text with a slightly uneven, printed-ink edge."""
    t = Image.new('L', layer.size, 0)
    ImageDraw.Draw(t).text(xy, s, font=font, fill=255, anchor=anchor)
    bb = t.getbbox()
    if not bb:
        return
    m = np.asarray(t, np.float32)
    r = np.random.default_rng(hash(s) % 1000)
    m = m * (0.86 + 0.14 * r.random(m.shape))
    col = Image.new('RGBA', layer.size, tuple(fill[:3]) + (0,))
    col.putalpha(Image.fromarray((m * alpha / 255).astype(np.uint8)))
    layer.alpha_composite(col)
