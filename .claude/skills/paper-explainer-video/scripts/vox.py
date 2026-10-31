"""Paper-collage explainer engine: locked paper background, cut-outs with an offset red marker stroke,
torn-paper foreground, spring entrances, code-drawn documents/stamps/marker lines, word-cue timing,
narration mastering and full-quality H.264 rendering.

Layer model per scene: locked grey paper background -> midground cut-outs with an offset
red marker stroke -> torn-paper foreground occluder. Elements spring up from below
(damping 18, mass 0.75, stiffness 110) crossed with a 16-frame opacity ramp; charts and
lines draw on. Painted plates become torn photo prints in the collage.
"""
import math, os, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 30
HERE = os.path.dirname(os.path.abspath(__file__))
# Project layout (override with VOX_PROJECT):
#   <project>/assets/   approved plates and cut-outs (PNG)
#   <project>/audio/    narration clips 1.wav, 2.wav, ... (+ matching 1.txt scripts)
#   <project>/timing/words.json   word timestamps from align.py
#   <project>/out/      renders
PROJECT = os.environ.get('VOX_PROJECT', os.getcwd())
SCR = PROJECT
FONTS = os.environ.get('VOX_FONTS', os.path.join(os.path.dirname(HERE), 'assets', 'fonts'))
ASSETS = os.path.join(PROJECT, 'assets')
AUD = os.path.join(PROJECT, 'audio')


def asset(name):
    """Path of an approved asset inside <project>/assets."""
    return os.path.join(ASSETS, name)

PAPER = (218, 217, 213)   # #DAD9D5
INK = (26, 26, 26)        # #1A1A1A
RED = (224, 67, 41)       # #E04329
CREAM = (238, 233, 222)
GREY = (150, 148, 143)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


F_HEAD = lambda s: font('ArchivoBlack.ttf', s)
F_SERIF = lambda s: font('Playfair700.ttf', s)
F_BODY = lambda s: font('PTSerif.ttf', s)
F_TYPE = lambda s: font('SpecialElite.ttf', s)


# ---------- motion ----------
def _spring_table(damping=18.0, mass=0.75, stiffness=110.0, n=240):
    x, v, out = 0.0, 0.0, []
    dt = 1.0 / FPS / 8
    for _ in range(n):
        out.append(x)
        for _ in range(8):
            a = (-stiffness * (x - 1.0) - damping * v) / mass
            v += a * dt
            x += v * dt
    return np.array(out)


SPRING = _spring_table()


def spring(frames):
    """Remotion-style spring progress for a frame offset (0 before start)."""
    if frames <= 0:
        return 0.0
    i = int(frames)
    if i >= len(SPRING) - 1:
        return 1.0
    f = frames - i
    return float(SPRING[i] * (1 - f) + SPRING[i + 1] * f)


def ease_out_cubic(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


def arrive(t, start, rise=380):
    """(y offset, opacity) for an element that springs up from below at `start` seconds."""
    fr = (t - start) * FPS
    p = spring(fr)
    op = ease_out_cubic(fr / 16.0)
    return (1 - p) * rise, op


# ---------- background (locked, identical in every scene) ----------
def _make_paper(seed=4):
    r = np.random.default_rng(seed)
    low = r.normal(0, 1, (H // 30, W // 30)).astype(np.float32)
    low = np.asarray(Image.fromarray(((low * 30) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) - 128
    fine = r.normal(0, 1, (H, W)).astype(np.float32) * 6
    a = np.array(PAPER, np.float32) + (low * 0.10)[..., None] + fine[..., None]
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for _ in range(900):
        x, y = r.uniform(0, W), r.uniform(0, H)
        L, ang = r.uniform(5, 18), r.uniform(0, math.pi)
        c = int(r.uniform(196, 212))
        d.line([(x, y), (x + L * math.cos(ang), y + L * math.sin(ang))], fill=(c, c, c - 4), width=1)
    for _ in range(3):  # faint creases
        y0 = r.uniform(0, H)
        d.line([(0, y0), (W, y0 + r.uniform(-80, 80))], fill=(205, 204, 200), width=2)
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    wash = Image.new('RGB', (W, H), (232, 226, 214))  # soft warm wash
    return Image.blend(img, wash, 0.12).convert('RGBA')


BG = _make_paper()


def background():
    return BG.copy()


# ---------- grain + finish ----------
_g = np.random.default_rng(7).normal(0, 1, (H // 2, W // 2)).astype(np.float32)
GRAIN = ((np.asarray(Image.fromarray(((_g * 40) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) - 128) / 128.0)[..., None]


def finish(img):
    a = np.asarray(img.convert('RGB'), np.float32) * (1 + 0.03 * GRAIN)
    return a.clip(0, 255).astype(np.uint8)


# ---------- helpers ----------
def alpha_mul(img, k):
    if k >= 0.999:
        return img
    a = np.asarray(img).copy()
    a[..., 3] = (a[..., 3].astype(np.float32) * max(0.0, k)).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')


def fit_h(img, h):
    return img.resize((max(1, round(img.width * h / img.height)), h), Image.LANCZOS)


def fit_w(img, w):
    return img.resize((w, max(1, round(img.height * w / img.width))), Image.LANCZOS)


def shadow_of(img, blur=26, offset=28, opacity=0.28):
    a = np.asarray(img.getchannel('A'), np.float32) * opacity
    sh = Image.new('RGBA', img.size, (55, 45, 31, 0))
    sh.putalpha(Image.fromarray(a.astype(np.uint8)))
    pad = blur * 2
    big = Image.new('RGBA', (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    big.alpha_composite(sh, (pad, pad))
    return big.filter(ImageFilter.GaussianBlur(blur)), pad, offset


def silhouette(img, color=RED):
    s = Image.new('RGBA', img.size, color + (0,))
    s.putalpha(img.getchannel('A'))
    return s


class Cutout:
    """A cut-out subject with its offset red marker stroke and drop shadow, pre-rendered."""

    def __init__(self, img, height, stroke_x=26, stroke_y=8):
        self.img = fit_h(img, height)
        self.stroke = silhouette(self.img)
        self.sx, self.sy = stroke_x, stroke_y
        self.shadow, self.pad, self.soff = shadow_of(self.img)

    def place(self, canvas, cx, bottom, t, start, rise=380, side=None, extra_y=0):
        dy, op = arrive(t, start, rise)
        if op <= 0:
            return
        x = int(cx - self.img.width / 2)
        y = int(bottom - self.img.height + dy + extra_y)
        sx = self.sx if side is None else (abs(self.sx) * (1 if side == 'right' else -1))
        canvas.alpha_composite(alpha_mul(self.shadow, op), (x - self.pad, y - self.pad + self.soff))
        canvas.alpha_composite(alpha_mul(self.stroke, op), (x + sx, y + self.sy))
        canvas.alpha_composite(alpha_mul(self.img, op), (x, y))


def torn_mask(w, h, seed, amp=7, step=9):
    r = np.random.default_rng(seed)
    pts = []
    for x in range(0, w, step):
        pts.append((x, r.uniform(0, amp)))
    for y in range(0, h, step):
        pts.append((w - r.uniform(0, amp), y))
    for x in range(w, 0, -step):
        pts.append((x, h - r.uniform(0, amp)))
    for y in range(h, 0, -step):
        pts.append((r.uniform(0, amp), y))
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


class PhotoCard:
    """A painted plate shown as a torn photo print on the paper, with a cream border."""

    def __init__(self, img, width, rot=-2.0, seed=1, border=16, crop=None):
        src = img.convert('RGB')
        if crop:
            src = src.crop(crop)
        self.src = fit_w(src, width)
        self.width, self.rot, self.seed, self.border = width, rot, seed, border
        self.h = self.src.height

    def render(self, zoom=1.0, pan=(0.5, 0.5)):
        w, h = self.width, self.h
        if zoom > 1.0:
            cw, ch = w / zoom, h / zoom
            x0 = (w - cw) * pan[0]
            y0 = (h - ch) * pan[1]
            inner = self.src.crop((x0, y0, x0 + cw, y0 + ch)).resize((w, h), Image.BICUBIC)
        else:
            inner = self.src
        b = self.border
        card = Image.new('RGBA', (w + 2 * b, h + 2 * b), CREAM + (255,))
        card.paste(inner, (b, b))
        card.putalpha(torn_mask(card.width, card.height, self.seed))
        return card.rotate(self.rot, resample=Image.BICUBIC, expand=True)

    def place(self, canvas, cx, cy, t, start, zoom=1.0, pan=(0.5, 0.5), rise=380):
        dy, op = arrive(t, start, rise)
        if op <= 0:
            return
        card = self.render(zoom, pan)
        sh, pad, off = shadow_of(card, blur=22, offset=20, opacity=0.30)
        x, y = int(cx - card.width / 2), int(cy - card.height / 2 + dy)
        canvas.alpha_composite(alpha_mul(sh, op), (x - pad, y - pad + off))
        canvas.alpha_composite(alpha_mul(card, op), (x, y))


def torn_strip(w, h, color, seed, top_only=True):
    r = np.random.default_rng(seed)
    pts = [(0, h)]
    for x in range(0, w + 12, 12):
        pts.append((x, r.uniform(0, 18) + 8 * math.sin(x / 140 + seed)))
    pts.append((w, h))
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    s = Image.new('RGBA', (w, h), color + (255,))
    fibres = np.random.default_rng(seed + 1).normal(0, 1, (h, w)).astype(np.float32) * 5
    a = np.asarray(s, np.float32)
    a[..., :3] += fibres[..., None]
    s = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    s.putalpha(m)
    return s


@lru_cache(maxsize=8)
def foreground(color=(150, 146, 138), height=200, seed=3):
    """The torn-paper band that occludes subjects' lower bodies and anchors the frame."""
    strip = torn_strip(W + 80, height, color, seed)
    sh, pad, off = shadow_of(strip, blur=18, offset=-10, opacity=0.35)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    layer.alpha_composite(sh, (-40 - pad, H - height - pad + off))
    layer.alpha_composite(strip, (-40, H - height))
    return layer


def text(canvas, xy, s, f, fill=INK, anchor='mm', alpha=1.0, tracking=0):
    ov = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    if tracking:
        widths = [d.textlength(c, font=f) for c in s]
        total = sum(widths) + tracking * (len(s) - 1)
        x = xy[0] - total / 2 if anchor[0] == 'm' else xy[0]
        for c, w in zip(s, widths):
            d.text((x, xy[1]), c, font=f, fill=fill + (int(255 * alpha),), anchor='l' + anchor[1])
            x += w + tracking
    else:
        d.text(xy, s, font=f, fill=fill + (int(255 * alpha),), anchor=anchor)
    canvas.alpha_composite(ov)


def headline(canvas, xy, s, size, t, start, fill=INK, anchor='mm', tracking=-2, rise=120):
    dy, op = arrive(t, start, rise)
    if op > 0:
        text(canvas, (xy[0], xy[1] + dy), s, F_HEAD(size), fill, anchor, op, tracking)


def typewriter(canvas, xy, s, size, t, start, cps=22, fill=INK, anchor='lm', cursor=True):
    n = int(max(0, (t - start)) * cps)
    if n <= 0:
        return
    shown = s[:n]
    f = F_TYPE(size)
    text(canvas, xy, shown, f, fill, anchor)
    if cursor and n < len(s) and int(t * 3) % 2 == 0:
        d = ImageDraw.Draw(canvas)
        w = d.textlength(shown, font=f)
        x = xy[0] + w + 4 if anchor[0] == 'l' else xy[0] + w / 2 + 4
        d.rectangle((x, xy[1] - size * 0.45, x + size * 0.45, xy[1] + size * 0.45), fill=fill + (255,))


def marker_line(canvas, pts, progress, width=10, color=RED, seed=0):
    """Hand-drawn red marker line that draws on (strokeDashoffset equivalent)."""
    if progress <= 0 or len(pts) < 2:
        return
    seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    total = sum(seg)
    target = total * min(progress, 1.0)
    d = ImageDraw.Draw(canvas)
    acc, r = 0.0, np.random.default_rng(seed)
    for i, L in enumerate(seg):
        if acc >= target:
            break
        f = min(1.0, (target - acc) / L) if L else 1
        a, b = pts[i], pts[i + 1]
        e = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        d.line([a, e], fill=color + (235,), width=width)
        d.ellipse((e[0] - width / 2, e[1] - width / 2, e[0] + width / 2, e[1] + width / 2), fill=color + (235,))
        acc += L


def marker_circle(canvas, cx, cy, rx, ry, progress, width=9, seed=0):
    r = np.random.default_rng(seed)
    pts = []
    for i in range(80):
        a = -math.pi * 0.6 + i / 79 * math.pi * 2.15
        k = 1 + 0.04 * math.sin(i * 0.4 + seed)
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    marker_line(canvas, pts, progress, width)


def strike(canvas, x0, x1, y, progress, width=8):
    marker_line(canvas, [(x0, y + 3), ((x0 + x1) / 2, y - 2), (x1, y + 2)], progress, width)


def stamp(canvas, cx, cy, s, size, t, start, ang=-8):
    if t < start:
        return
    p = min(1.0, (t - start) * FPS / 5)
    sc = lerp(1.6, 1.0, ease_out_cubic(p))
    f = F_HEAD(size)
    tw = int(ImageDraw.Draw(canvas).textlength(s, font=f)) + 60
    th = int(size * 1.5)
    st = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    d.rectangle((6, 6, tw - 6, th - 6), outline=RED + (255,), width=7)
    d.text((tw / 2, th / 2 + 2), s, font=f, fill=RED + (255,), anchor='mm')
    a = np.asarray(st).astype(np.float32)
    a[np.random.default_rng(len(s)).random(a.shape[:2]) < 0.13, 3] = 0
    a[..., 3] *= min(1.0, p * 1.5)
    st = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    st = st.resize((int(tw * sc), int(th * sc)), Image.BICUBIC).rotate(ang, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(st, (int(cx - st.width / 2), int(cy - st.height / 2)))


def document(w, h, lines, seed=1, title=None, title_size=44, body_size=30, typed=False):
    """A cream sheet with a serif title and body lines (code-drawn document)."""
    doc = Image.new('RGBA', (w, h), (245, 241, 230, 255))
    d = ImageDraw.Draw(doc)
    y = 70
    if title:
        d.text((w / 2, y), title, font=F_SERIF(title_size), fill=INK + (255,), anchor='mm')
        d.line((60, y + 42, w - 60, y + 42), fill=INK + (255,), width=3)
        y += 100
    f = F_TYPE(body_size) if typed else F_BODY(body_size)
    for ln in lines:
        if ln == '---':
            r = np.random.default_rng(seed + y)
            d.line((60, y, 60 + r.uniform(0.5, 0.95) * (w - 120), y), fill=GREY + (255,), width=3)
            y += 34
        else:
            d.text((60, y), ln, font=f, fill=INK + (255,), anchor='lm')
            y += int(body_size * 1.55)
    doc.putalpha(torn_mask(w, h, seed, amp=4, step=14))
    return doc


def place_sheet(canvas, sheet, cx, cy, t, start, rot=0.0, rise=380):
    dy, op = arrive(t, start, rise)
    if op <= 0:
        return None
    s = sheet.rotate(rot, resample=Image.BICUBIC, expand=True) if rot else sheet
    sh, pad, off = shadow_of(s, blur=20, offset=18, opacity=0.28)
    x, y = int(cx - s.width / 2), int(cy - s.height / 2 + dy)
    canvas.alpha_composite(alpha_mul(sh, op), (x - pad, y - pad + off))
    canvas.alpha_composite(alpha_mul(s, op), (x, y))
    return x, y


def shake(img, t, hits, amp=14, fill=PAPER):
    burst = 0.0
    for b in hits:
        if t >= b:
            burst = max(burst, math.exp(-(t - b) * 3.0))
    if burst < 0.01:
        return img
    dx, dy = amp * burst * math.sin(t * 61), amp * burst * math.cos(t * 47)
    return img.transform(img.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy), resample=Image.BILINEAR, fillcolor=fill + (255,))


# ---------- assembly ----------
def make_frame(shots, end, t, xf=0.2):
    """shots: list of (start, fn). Scenes cut with a short crossfade."""
    starts = [s for s, _ in shots] + [end]
    i = max(j for j in range(len(shots)) if starts[j] <= t)

    def render(j, tt):
        global _SCENE_START
        s0, fn = shots[j]
        _SCENE_START = s0
        return finish(fn(tt - s0, starts[j + 1] - s0))
    cur = render(i, t)
    if i + 1 < len(shots) and starts[i + 1] - t < xf:
        w = ease((t - (starts[i + 1] - xf)) / (2 * xf))
        cur = (cur * (1 - w) + render(i + 1, t) * w).astype(np.uint8)
    elif i > 0 and t - starts[i] < xf:
        w = ease((t - (starts[i] - xf)) / (2 * xf))
        cur = (render(i - 1, t) * (1 - w) + cur * w).astype(np.uint8)
    return cur


def master_audio(clips, out_wav):
    """Concatenate narration clips and apply the vox-skill mastering chain."""
    lst = out_wav + '.txt'
    with open(lst, 'w') as fh:
        for n in clips:
            fh.write(f"file '{os.path.join(AUD, f'{n}.wav')}'\n")
    chain = ('highpass=f=85,equalizer=f=350:t=q:w=1:g=-2,equalizer=f=3000:t=q:w=1:g=2.5,'
             'equalizer=f=6800:t=q:w=2:g=-3,acompressor=threshold=-20dB:ratio=3:attack=10:release=120,'
             'loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur=4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-af', chain, '-ar', '48000', '-ac', '2', out_wav], check=True)


def render_video(frame_fn, end, clips, out, workdir):
    os.makedirs(workdir, exist_ok=True)
    wav = os.path.join(workdir, 'mastered.wav')
    master_audio(clips, wav)
    n = int(round(end * FPS))
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', wav, '-c:v', 'libx264', '-preset', os.environ.get('VOX_PRESET', 'medium'), '-crf', os.environ.get('VOX_CRF', '18'),
                          '-tune', 'animation', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', os.environ.get('VOX_ABR', '192k'), '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for f in range(n):
        p.stdin.write(frame_fn(f / FPS).tobytes())
        if f % 300 == 0:
            print(f'frame {f}/{n}', flush=True)
    p.stdin.close()
    p.wait()
    print('done', out)


def contact_sheet(frame_fn, times, out):
    tiles = [Image.fromarray(frame_fn(t)).resize((960, 540)) for t in times]
    rows = (len(tiles) + 1) // 2
    c = Image.new('RGB', (1920, rows * 540))
    for i, tl in enumerate(tiles):
        c.paste(tl, ((i % 2) * 960, (i // 2) * 540))
    c.save(out)


# ---------- exact word timing ----------
import json as _json, re as _re, wave as _wave
_TIMING = os.path.join(PROJECT, 'timing', 'words.json')
_WORDS = {int(k): v for k, v in _json.load(open(_TIMING)).items()} if os.path.exists(_TIMING) else {}
_DUR = {}
for _f in os.listdir(AUD) if os.path.isdir(AUD) else []:
    if _f.endswith('.wav') and _f[:-4].isdigit():
        with _wave.open(os.path.join(AUD, _f)) as _w:
            _DUR[int(_f[:-4])] = _w.getnframes() / _w.getframerate()


def _norm(s):
    return _re.sub(r"[^a-z0-9']", '', s.lower().replace('’', "'"))


def make_cue(clips):
    """Returns cue(clip, phrase, nth=1, edge='s') -> act-local seconds of that spoken phrase."""
    off, acc = {}, 0.0
    for c in clips:
        off[c] = acc
        acc += _DUR[c]

    def cue(clip, phrase, nth=1, edge='s'):
        toks = [_norm(x) for x in phrase.split() if _norm(x)]
        ws = _WORDS[clip]
        nw = [_norm(w['w']) for w in ws]
        hits = [i for i in range(len(nw) - len(toks) + 1) if nw[i:i + len(toks)] == toks]
        if len(hits) < nth:
            raise KeyError(f'clip {clip}: "{phrase}" not found ({len(hits)} hits)')
        i = hits[nth - 1]
        w = ws[i] if edge == 's' else ws[i + len(toks) - 1]
        return off[clip] + w[edge]
    cue.total = acc
    return cue


_SCENE_START = 0.0


def w(abs_time):
    """Convert an act-local cue time into the current scene's local time."""
    return abs_time - _SCENE_START


LEAD = 0.12  # cut this far before the word so the crossfade completes on it
