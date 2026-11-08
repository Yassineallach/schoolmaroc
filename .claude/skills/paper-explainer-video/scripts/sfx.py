"""Procedural paper / desk sound effects, generated in code and synced to the animation.

The presets and style helpers register events while frames are drawn
(style.event(kind, abs_time, x, params)). build_track() turns those events into a stereo
48 kHz effects stem: each sound is synthesised fresh (seeded per event, so no two drops sound
identical), panned to the element's x position, and ducked under the narration.

Kinds: drop, slide, unfold, tear, wipe, sheet, stamp, reveal, assemble, flip, pageflip,
       type, marker, swipe, zoom, beep, tick
"""
import math
import numpy as np

SR = 48000


def _rng(kind, t):
    import zlib
    return np.random.default_rng(zlib.crc32(f'{kind}:{t:.3f}'.encode()))


def _env(n, attack, decay, sr=SR):
    t = np.arange(n) / sr
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-np.maximum(t - attack, 0) / max(decay, 1e-4))


def _band(x, lo, hi):
    """FFT band-pass with soft skirts."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = 1 / (1 + (lo / np.maximum(f, 1)) ** 4) / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * g, len(x))


def _norm(x, peak):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


def _sec(s):
    return int(s * SR)


def _crackle(r, n, density, lo=1500, hi=9000):
    """Sparse paper fibre snaps."""
    imp = np.zeros(n)
    k = int(density * n / SR)
    idx = r.integers(0, n, max(1, k))
    imp[idx] = r.uniform(0.3, 1.0, len(idx)) * r.choice([-1, 1], len(idx))
    click = np.exp(-np.arange(int(0.004 * SR)) / (0.0009 * SR))
    return _band(np.convolve(imp, click)[:n], lo, hi)


# ------------------------------------------------------------------ sound designs
# each returns (offset_seconds, mono_signal): the sound starts at event_time + offset

def s_drop(r, p):
    """A print landing: short air swish, then a soft papery slap."""
    n = _sec(0.55)
    air = _band(r.normal(0, 1, n), 900, 6000) * _env(n, 0.18, 0.06)
    land = np.zeros(n)
    i0 = _sec(0.26)
    m = n - i0
    slap = _band(r.normal(0, 1, m), 300, 4500) * _env(m, 0.002, 0.035)
    thump = np.sin(2 * math.pi * r.uniform(90, 130) * np.arange(m) / SR) * _env(m, 0.001, 0.05)
    land[i0:] = slap + 0.6 * thump
    return -0.02, _norm(0.35 * air + land, p.get('gain', 0.5))


def s_slide(r, p):
    """Paper pushed across a desk: friction rustle that slows with the sheet."""
    dur = p.get('dur', 1.1)
    n = _sec(dur * 0.85)
    t = np.arange(n) / SR
    v = np.exp(-t / (dur * 0.28))
    rustle = _band(r.normal(0, 1, n), 1800, 9000) * v * (0.7 + 0.3 * np.sin(2 * math.pi * r.uniform(18, 30) * t))
    grit = _crackle(r, n, 260) * v
    return 0.0, _norm(rustle + 0.6 * grit, 0.42)


def s_unfold(r, p):
    """Two crisp creases opening."""
    dur = p.get('dur', 1.3)
    n = _sec(dur + 0.4)
    out = np.zeros(n)
    for off in (0.0, dur * 0.38):
        i0 = _sec(off + 0.05)
        m = _sec(0.28)
        snap = _crackle(r, m, 900, 1200, 8000) * _env(m, 0.01, 0.08)
        body = _band(r.normal(0, 1, m), 600, 5000) * _env(m, 0.03, 0.09)
        out[i0:i0 + m] += snap + 0.5 * body
    return -0.05, _norm(out, 0.45)


def s_tear(r, p, length=None, gain=0.55):
    """A paper rip: dense fibre crackle riding a rising-then-falling band of noise."""
    L = length or p.get('dur', 0.9) * 0.7
    n = _sec(L)
    t = np.arange(n) / SR
    shape = np.sin(np.pi * np.clip(t / L, 0, 1)) ** 0.6
    body = _band(r.normal(0, 1, n), 700, 7000) * shape
    fibres = _crackle(r, n, 2600, 1500, 10000) * shape
    return 0.0, _norm(0.55 * body + fibres, gain)


def s_wipe(r, p):
    """Torn-paper transition: a quick rip across the frame."""
    off, x = s_tear(r, p, length=0.42, gain=0.38)
    return -0.32, x


def s_sheet(r, p):
    """New sheet laid over: soft slide-up swoosh with a light landing."""
    n = _sec(0.6)
    t = np.arange(n) / SR
    sw = _band(r.normal(0, 1, n), 700, 5000) * np.sin(np.pi * np.clip(t / 0.5, 0, 1)) ** 2
    m = _sec(0.1)
    sw[_sec(0.45):_sec(0.45) + m] += _band(r.normal(0, 1, m), 300, 3000) * _env(m, 0.002, 0.03) * 1.5
    return -0.4, _norm(sw, 0.3)


def s_stamp(r, p):
    """Rubber stamp: a short descent hiss, then a dull wooden thud with a rubber knock."""
    n = _sec(0.5)
    out = np.zeros(n)
    pre = _sec(0.16)
    out[:pre] = _band(r.normal(0, 1, pre), 1500, 6000) * np.linspace(0, 1, pre) ** 2 * 0.12
    m = n - pre
    tt = np.arange(m) / SR
    thud = np.sin(2 * math.pi * (r.uniform(62, 78) * tt + 30 * (1 - np.exp(-tt / 0.02)) * 0.02)) * _env(m, 0.001, 0.09)
    knock = _band(r.normal(0, 1, m), 180, 1400) * _env(m, 0.001, 0.025)
    click = _band(r.normal(0, 1, m), 2500, 9000) * _env(m, 0.0005, 0.006)
    out[pre:] = 1.0 * thud + 0.8 * knock + 0.35 * click
    return -0.16, _norm(out, 0.6)


def s_reveal(r, p):
    """Torn hole opening in the page: a slow, gentle tear."""
    off, x = s_tear(r, p, length=p.get('dur', 1.2) * 0.6, gain=0.32)
    return 0.0, x


def s_assemble(r, p):
    n_p, stagger, dur = p.get('n', 7), p.get('stagger', 0.09), p.get('dur', 0.9)
    n = _sec(n_p * stagger + dur + 0.3)
    out = np.zeros(n)
    for i in range(n_p):
        i0 = _sec(i * stagger + dur * (0.35 if not p.get('reverse') else 0.0))
        m = _sec(0.06)
        if i0 + m < n:
            out[i0:i0 + m] += _band(r.normal(0, 1, m), 800, 6000) * _env(m, 0.001, 0.015) * r.uniform(0.6, 1.0)
    return 0.0, _norm(out, 0.4)


def s_flip(r, p):
    dur = p.get('dur', 0.85)
    n = _sec(dur + 0.2)
    t = np.arange(n) / SR
    sw = _band(r.normal(0, 1, n), 600, 4500) * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 3
    m = _sec(0.08)
    i0 = _sec(dur * 0.95)
    sw[i0:i0 + m] += _band(r.normal(0, 1, m), 300, 3500) * _env(m, 0.001, 0.02) * 2
    return 0.0, _norm(sw, 0.35)


def s_pageflip(r, p):
    dur = p.get('dur', 1.15)
    n = _sec(dur + 0.2)
    t = np.arange(n) / SR
    whoosh = _band(r.normal(0, 1, n), 500, 5000) * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    rustle = _crackle(r, n, 500) * np.sin(np.pi * np.clip(t / dur, 0, 1))
    m = _sec(0.09)
    i0 = _sec(dur * 0.97)
    flap = np.zeros(n)
    flap[i0:i0 + m] = _band(r.normal(0, 1, m), 250, 3000) * _env(m, 0.001, 0.025)
    return 0.0, _norm(whoosh + 0.5 * rustle + 2.2 * flap, 0.42)


def s_type(r, p):
    """Typewriter keys: one strike per character (spaces silent), with tiny timing jitter."""
    chars, cps = p.get('n', 6), p.get('cps', 11)
    n = _sec(chars / cps + 0.15)
    out = np.zeros(n)
    for i in range(chars):
        i0 = _sec(i / cps + r.uniform(-0.008, 0.008) + 0.01)
        m = _sec(0.03)
        if 0 <= i0 and i0 + m < n:
            key = _band(r.normal(0, 1, m), 1800, 7500) * _env(m, 0.0004, 0.004)
            body = _band(r.normal(0, 1, m), 250, 1200) * _env(m, 0.0008, 0.012)
            out[i0:i0 + m] += (key + 0.7 * body) * r.uniform(0.6, 1.0)
    return 0.0, _norm(out, 0.22)


def s_marker(r, p):
    """Felt marker on paper: a short, slightly squeaky scratch."""
    L = p.get('dur', 0.45)
    n = _sec(L)
    t = np.arange(n) / SR
    sh = np.sin(np.pi * np.clip(t / L, 0, 1)) ** 0.8
    scratch = _band(r.normal(0, 1, n), 2500, 8000) * sh * (0.7 + 0.3 * np.sin(2 * math.pi * r.uniform(9, 14) * t))
    return 0.0, _norm(scratch, 0.18)


def s_swipe(r, p):
    o, x = s_marker(r, dict(dur=0.32))
    return 0.0, x * 1.2


def s_zoom(r, p):
    """Camera travelling in: a soft low air swell."""
    L = p.get('dur', 1.4)
    n = _sec(L)
    t = np.arange(n) / SR
    return 0.0, _norm(_band(r.normal(0, 1, n), 150, 1800) * np.sin(np.pi * np.clip(t / L, 0, 1)) ** 2, 0.16)


def s_beep(r, p):
    """Monitor beep (soft, sine with a short envelope)."""
    n = _sec(0.16)
    t = np.arange(n) / SR
    return 0.0, np.sin(2 * math.pi * 1046 * t) * _env(n, 0.004, 0.06) * 0.12


def s_tick(r, p):
    n = _sec(0.03)
    return 0.0, _band(r.normal(0, 1, n), 1500, 8000) * _env(n, 0.0005, 0.005) * 0.15


def s_shatter(r, p):
    """Porcelain hitting the floor: a hard click, a bright crackle burst, a few skittering bits."""
    n = _sec(0.9)
    out = np.zeros(n)
    m = _sec(0.05)
    out[:m] += _band(r.normal(0, 1, m), 1500, 9000) * _env(m, 0.0005, 0.008) * 1.5
    burst = _sec(0.35)
    out[:burst] += _crackle(r, burst, 6000, 2500, 12000) * _env(burst, 0.002, 0.08)
    for _ in range(7):
        i0 = _sec(r.uniform(0.12, 0.7))
        k = _sec(0.025)
        if i0 + k < n:
            out[i0:i0 + k] += _band(r.normal(0, 1, k), 3000, 10000) * _env(k, 0.0005, 0.005) * r.uniform(0.2, 0.6)
    return 0.0, _norm(out, 0.55)


def s_pin(r, p):
    """A map pin landing: tiny descending whistle of air, then a soft tack into paper."""
    n = _sec(0.35)
    out = np.zeros(n)
    m = _sec(0.12)
    out[:m] = _band(r.normal(0, 1, m), 2000, 7000) * np.linspace(0, 1, m) ** 2 * 0.2
    k = _sec(0.06)
    out[m:m + k] += _band(r.normal(0, 1, k), 400, 3500) * _env(k, 0.0005, 0.012)
    tt = np.arange(k) / SR
    out[m:m + k] += np.sin(2 * math.pi * 180 * tt) * _env(k, 0.0005, 0.02) * 0.5
    return -0.12, _norm(out, 0.4)


def s_pencil(r, p):
    """Graphite on paper: a dry, grainy scratch for routes, axes and timelines."""
    L = p.get('dur', 0.8)
    n = _sec(L)
    t = np.arange(n) / SR
    sh = np.sin(np.pi * np.clip(t / L, 0, 1)) ** 0.5
    grain = _crackle(r, n, 1800, 2000, 9000) * sh
    hiss = _band(r.normal(0, 1, n), 3000, 9000) * sh * 0.4
    return 0.0, _norm(grain + hiss, 0.16)


def s_whoosh(r, p):
    """Air movement for camera travels and shape wipes (no tonal sweep, no 'swish' cliche)."""
    L = p.get('dur', 0.6)
    n = _sec(L)
    t = np.arange(n) / SR
    sh = np.sin(np.pi * np.clip(t / L, 0, 1)) ** 1.5
    return -L * 0.5, _norm(_band(r.normal(0, 1, n), 250, 3200) * sh, 0.2)


def s_envelope(r, p):
    """Paper flap lifting, then a letter sliding out."""
    n = _sec(1.1)
    out = np.zeros(n)
    m = _sec(0.25)
    out[:m] = _crackle(r, m, 700, 1200, 7000) * _env(m, 0.03, 0.1)
    k = _sec(0.7)
    t = np.arange(k) / SR
    out[_sec(0.35):_sec(0.35) + k] += _band(r.normal(0, 1, k), 1500, 8000) * np.sin(np.pi * t / 0.7) * 0.6
    return 0.0, _norm(out, 0.32)


def s_tape(r, p):
    """Tape torn from the roll and pressed down."""
    n = _sec(0.45)
    out = np.zeros(n)
    m = _sec(0.18)
    out[:m] = _crackle(r, m, 9000, 2500, 11000) * _env(m, 0.005, 0.06)
    k = _sec(0.05)
    out[_sec(0.3):_sec(0.3) + k] = _band(r.normal(0, 1, k), 400, 3000) * _env(k, 0.001, 0.015)
    return 0.0, _norm(out, 0.3)


def s_pop(r, p):
    """Soft paper pop for chart points and data reveals."""
    n = _sec(0.08)
    t = np.arange(n) / SR
    return 0.0, (np.sin(2 * math.pi * r.uniform(520, 640) * t) * _env(n, 0.001, 0.02) + _band(r.normal(0, 1, n), 800, 4000) * _env(n, 0.0005, 0.006) * 0.4) * 0.14


DESIGNS = dict(pin=s_pin, pencil=s_pencil, whoosh=s_whoosh, envelope=s_envelope, tape=s_tape, pop=s_pop, shatter=s_shatter, drop=s_drop, slide=s_slide, unfold=s_unfold, tear=s_tear, wipe=s_wipe, sheet=s_sheet,
               stamp=s_stamp, reveal=s_reveal, assemble=s_assemble, flip=s_flip, pageflip=s_pageflip,
               type=s_type, marker=s_marker, swipe=s_swipe, zoom=s_zoom, beep=s_beep, tick=s_tick)


# ------------------------------------------------------------------ mixing
def build_track(events, length, narration=None, level_db=-13.0, duck_db=-9.0):
    """events: iterable of (kind, t, x, params). Returns float32 stereo (n, 2) at 48 kHz.
    narration: optional (n, 2) array; the effects duck by duck_db while it is speaking."""
    n = _sec(length)
    out = np.zeros((n, 2), np.float32)
    for kind, t, x, p in sorted(events, key=lambda e: e[1]):
        fn = DESIGNS.get(kind)
        if fn is None:
            continue
        off, sig = fn(_rng(kind, t), p or {})
        i0 = _sec(t + off)
        if i0 >= n or i0 + len(sig) <= 0:
            continue
        a, b = max(0, i0), min(n, i0 + len(sig))
        s = sig[a - i0:b - i0]
        pan = 0.0 if x is None else max(-0.6, min(0.6, (x / 1920 - 0.5) * 1.2))
        out[a:b, 0] += s * math.cos((pan + 1) * math.pi / 4) * math.sqrt(2)
        out[a:b, 1] += s * math.sin((pan + 1) * math.pi / 4) * math.sqrt(2)
    out *= 10 ** (level_db / 20)
    if narration is not None:
        m = min(len(narration), n)
        env = np.abs(narration[:m]).mean(axis=1)
        k = _sec(0.06)
        env = np.convolve(env, np.ones(k) / k, 'same')
        speaking = np.clip(env / (np.percentile(env[env > 0], 60) + 1e-9), 0, 1) if (env > 0).any() else env
        att = _sec(0.25)
        sm = np.convolve(speaking, np.ones(att) / att, 'same')
        gain = 10 ** (duck_db * sm / 20)
        out[:m] *= gain[:, None]
    return np.clip(out, -1, 1)


def read_wav(path):
    import wave
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        return a.reshape(-1, w.getnchannels())


def write_wav(path, a):
    import wave
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


def mix_into(narration_wav, events, out_wav, level_db=-13.0):
    """Narration + effects stem -> out_wav (also writes <out_wav>.sfx.wav, the stem alone)."""
    nar = read_wav(narration_wav)
    fx = build_track(events, len(nar) / SR, nar, level_db)
    write_wav(out_wav + '.sfx.wav', fx)
    mix = nar[:len(fx)] + fx[:len(nar)]
    peak = np.max(np.abs(mix))
    if peak > 0.98:
        mix *= 0.98 / peak
    write_wav(out_wav, mix)
