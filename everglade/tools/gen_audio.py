"""
Everglade - procedural audio generator.

Synthesises every sound effect, the ambience beds and three gentle music
pieces as OGG Vorbis files (no samples, no third-party audio):

    pip install numpy soundfile
    python tools/gen_audio.py assets/audio
"""

import os
import sys

import numpy as np
import soundfile as sf

SR = 32000
rng = np.random.default_rng(7)


def t_axis(dur):
    return np.arange(int(SR * dur)) / SR


def env(n, attack=0.005, decay=0.2, sustain=0.0, release=0.0, dur=None):
    """Simple exponential-decay envelope sampled to n samples."""
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    d = np.exp(-np.maximum(t - attack, 0) / max(decay, 1e-4))
    e = a * (sustain + (1 - sustain) * d)
    if release > 0:
        tail = np.clip((n / SR - t) / release, 0, 1)
        e *= tail
    return e


def onepole(x, cutoff):
    """Vectorised-ish one pole filter using cumulative trick for constant cutoff."""
    a = float(np.exp(-2 * np.pi * cutoff / SR))
    y = np.empty_like(x)
    acc = 0.0
    b = 1 - a
    for i, v in enumerate(x):
        acc = b * v + a * acc
        y[i] = acc
    return y


def bandpass(x, lo, hi):
    return onepole(x, hi) - onepole(x, lo)


def noise(dur):
    return rng.uniform(-1, 1, int(SR * dur))


def sine(freq, dur, phase=0.0):
    t = t_axis(dur)
    if np.ndim(freq) == 0:
        return np.sin(2 * np.pi * freq * t + phase)
    return np.sin(2 * np.pi * np.cumsum(freq) / SR + phase)


def bell(freq, dur, decay=0.6, bright=1.0):
    t = t_axis(dur)
    partials = [(1.0, 1.0), (2.01, 0.45 * bright), (3.02, 0.22 * bright), (4.17, 0.12 * bright)]
    out = np.zeros_like(t)
    for ratio, amp in partials:
        out += amp * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t / (decay / ratio ** 0.6))
    return out * np.clip(t / 0.003, 0, 1)


def pluck(freq, dur, damping=0.996, bright=0.5):
    """Karplus-Strong plucked string (harp / kalimba-ish)."""
    n = int(SR * dur)
    period = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, period)
    buf = onepole(buf, 2000 + 6000 * bright)
    out = np.zeros(n)
    idx = 0
    for i in range(n):
        v = buf[idx]
        nxt = buf[(idx + 1) % period]
        buf[idx] = damping * 0.5 * (v + nxt)
        out[i] = v
        idx = (idx + 1) % period
    return out * np.clip(np.arange(n) / (SR * 0.002), 0, 1)


def mix(*parts, length=None):
    n = length or max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[: len(p)] += p[:n]
    return out


def place(out, sig, at):
    i = int(at * SR)
    if i >= len(out):
        return
    j = min(len(out), i + len(sig))
    out[i:j] += sig[: j - i]


def normalize(x, peak=0.8):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


def fade(x, fin=0.005, fout=0.02):
    n = len(x)
    a = int(fin * SR)
    b = int(fout * SR)
    if a > 0:
        x[:a] *= np.linspace(0, 1, a)
    if b > 0:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def write(out_dir, name, x, peak=0.8, quality=0.45):
    x = fade(normalize(np.asarray(x, dtype=np.float64), peak))
    path = os.path.join(out_dir, name + ".ogg")
    # write in blocks: some libsndfile builds crash on large single Vorbis writes
    with sf.SoundFile(path, "w", SR, 1, format="OGG", subtype="VORBIS") as f:
        data = x.astype(np.float32)
        for i in range(0, len(data), 8192):
            f.write(data[i:i + 8192])
    print("  wrote", path, f"{len(x) / SR:.2f}s")


# ---------------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------------
def sfx_click():
    d = 0.06
    return sine(1700, d) * env(int(SR * d), 0.001, 0.012) + onepole(noise(d), 3000) * env(int(SR * d), 0.0005, 0.006) * 0.6


def sfx_place_stone():
    d = 0.45
    n = int(SR * d)
    thud = sine(np.linspace(140, 70, n), d) * env(n, 0.002, 0.09)
    grit = onepole(noise(d), 1200) * env(n, 0.001, 0.05) * 1.2
    clack = mix(np.zeros(int(0.05 * SR)), sine(900, 0.08) * env(int(0.08 * SR), 0.001, 0.015) * 0.4)
    return mix(thud, grit, clack, length=n)


def sfx_stone_tick():
    d = 0.08
    n = int(SR * d)
    return sine(rng.uniform(700, 900), d) * env(n, 0.001, 0.012) * 0.6 + onepole(noise(d), 2500) * env(n, 0.0005, 0.01)


def sfx_place_wood():
    d = 0.3
    n = int(SR * d)
    k = sine(420, d) * env(n, 0.001, 0.05) + sine(615, d) * env(n, 0.001, 0.035) * 0.6 + sine(1180, d) * env(n, 0.001, 0.02) * 0.3
    return k + onepole(noise(d), 1800) * env(n, 0.0005, 0.015) * 0.5


def sfx_wood_tick():
    d = 0.07
    n = int(SR * d)
    return sine(rng.uniform(500, 650), d) * env(n, 0.001, 0.015)


def sfx_place_path():
    d = 0.35
    n = int(SR * d)
    x = np.zeros(n)
    for i in range(10):
        g = onepole(noise(0.03), rng.uniform(1500, 3500)) * env(int(0.03 * SR), 0.001, 0.008)
        place(x, g, rng.uniform(0, 0.25))
    return x


def sfx_brush():
    d = 0.2
    n = int(SR * d)
    return bandpass(noise(d), 600, 3500) * np.sin(np.linspace(0, np.pi, n)) ** 2


def sfx_build():
    d = 1.4
    n = int(SR * d)
    whoosh = bandpass(noise(d), 300, 2500) * np.sin(np.linspace(0, np.pi, n)) ** 3 * 0.5
    out = np.zeros(n)
    for i, f in enumerate([523.25, 659.25, 783.99, 1046.5]):
        place(out, bell(f, 0.9, 0.5) * 0.35, 0.18 + i * 0.07)
    thud = sine(np.linspace(110, 60, n), d) * env(n, 0.003, 0.12) * 0.7
    return whoosh + out + thud


def sfx_plant():
    d = 0.25
    n = int(SR * d)
    pop = sine(np.linspace(300, 700, n), d) * env(n, 0.002, 0.03)
    rustle = bandpass(noise(d), 1500, 6000) * env(n, 0.005, 0.06) * 0.4
    return pop + rustle


def sfx_erase():
    d = 0.45
    n = int(SR * d)
    cut = np.linspace(4000, 300, n)
    x = noise(d)
    y = np.empty(n)
    acc = 0.0
    for i in range(n):
        a = np.exp(-2 * np.pi * cut[i] / SR)
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y * env(n, 0.01, 0.15)


def sfx_dig():
    d = 0.3
    n = int(SR * d)
    return onepole(noise(d), 700) * env(n, 0.005, 0.08) * 1.5


def sfx_rumble():
    d = 0.35
    n = int(SR * d)
    return onepole(noise(d), 220) * np.sin(np.linspace(0, np.pi, n)) * 2.0


def sfx_splash():
    d = 0.9
    n = int(SR * d)
    x = bandpass(noise(d), 400, 5000) * env(n, 0.005, 0.18)
    for i in range(8):
        f0 = rng.uniform(500, 1400)
        dd = rng.uniform(0.04, 0.09)
        bub = sine(np.linspace(f0, f0 * 1.8, int(dd * SR)), dd) * env(int(dd * SR), 0.002, 0.02) * 0.4
        place(x, bub, rng.uniform(0.05, 0.6))
    return x


def sfx_undo():
    d = 0.35
    n = int(SR * d)
    return sine(np.linspace(900, 500, n), d) * env(n, 0.005, 0.1) * 0.6 + bell(660, d, 0.15) * 0.3


def sfx_shutter():
    d = 0.25
    n = int(SR * d)
    x = np.zeros(n)
    for at in (0.0, 0.09):
        c = onepole(noise(0.04), 4000) * env(int(0.04 * SR), 0.0005, 0.008)
        place(x, c, at)
    return x


def sfx_season():
    d = 1.6
    n = int(SR * d)
    out = np.zeros(n)
    notes = [587.33, 659.25, 783.99, 880.0, 1174.66]
    for i, f in enumerate(notes):
        place(out, bell(f, 1.2, 0.7, 0.6) * 0.3, i * 0.08)
    return out


def sfx_heart():
    d = 0.8
    n = int(SR * d)
    out = np.zeros(n)
    place(out, bell(880, 0.6, 0.35), 0.0)
    place(out, bell(1318.5, 0.6, 0.35), 0.1)
    return out


def sfx_nope():
    d = 0.3
    n = int(SR * d)
    out = np.zeros(n)
    for at, f in ((0.0, 330), (0.12, 262)):
        place(out, sine(f, 0.12) * env(int(0.12 * SR), 0.003, 0.04), at)
    return out


def formant_voice(f0_curve, dur, formants, breath=0.05):
    n = int(SR * dur)
    phase = np.cumsum(f0_curve[:n]) / SR
    saw = 2 * (phase % 1.0) - 1.0
    src = saw + noise(dur)[:n] * breath
    out = np.zeros(n)
    for fc, bw, amp in formants:
        out += bandpass(src, max(50, fc - bw / 2), fc + bw / 2) * amp
    return out


def sfx_baa(variant):
    d = 0.75 + 0.1 * variant
    n = int(SR * d)
    t = np.arange(n) / SR
    base = 210 + 40 * variant
    f0 = base * (1 + 0.06 * np.sin(2 * np.pi * 7.5 * t)) * np.interp(t, [0, 0.08, d], [0.9, 1.08, 0.95])
    v = formant_voice(f0, d, [(750, 300, 1.0), (1250, 400, 0.6), (2600, 600, 0.25)], 0.12)
    e = np.interp(t, [0, 0.05, 0.12, d - 0.2, d], [0, 0.6, 1.0, 0.7, 0])
    return v * e


def sfx_quack(variant):
    d = 0.22
    n = int(SR * d)
    t = np.arange(n) / SR
    f0 = (380 + 60 * variant) * np.interp(t, [0, d], [1.1, 0.85])
    v = formant_voice(f0, d, [(900, 500, 1.0), (1900, 600, 0.7)], 0.3)
    return v * np.interp(t, [0, 0.015, 0.08, d], [0, 1, 0.7, 0])


def sfx_cluck(variant):
    d = 0.35
    n = int(SR * d)
    out = np.zeros(n)
    for i in range(2 + variant):
        dd = 0.07
        t = np.arange(int(dd * SR)) / SR
        f0 = 520 * np.interp(t, [0, dd], [1.2, 0.9])
        place(out, formant_voice(f0, dd, [(1100, 500, 1.0), (2300, 700, 0.5)], 0.3) * np.interp(t, [0, 0.01, dd], [0, 1, 0]), i * 0.1)
    return out


def sfx_chirp(variant):
    d = 0.4
    n = int(SR * d)
    out = np.zeros(n)
    count = 2 + variant
    for i in range(count):
        dd = 0.07
        nn = int(dd * SR)
        f = np.linspace(3200 + 300 * i, 4600 - 200 * variant, nn)
        place(out, sine(f, dd) * np.sin(np.linspace(0, np.pi, nn)) ** 2, i * 0.09)
    return out


# ---------------------------------------------------------------------------
# Ambience
# ---------------------------------------------------------------------------
def amb_day():
    d = 30.0
    n = int(SR * d)
    t = np.arange(n) / SR
    wind = onepole(noise(d), 500) * (0.5 + 0.35 * np.sin(2 * np.pi * t / 11.0) + 0.15 * np.sin(2 * np.pi * t / 4.3))
    leaves = bandpass(noise(d), 2500, 7000) * (0.06 + 0.05 * np.sin(2 * np.pi * t / 6.0) ** 2)
    out = wind * 0.6 + leaves
    for i in range(14):
        at = rng.uniform(0.5, d - 1.5)
        place(out, sfx_chirp(rng.integers(0, 3)) * rng.uniform(0.05, 0.12), at)
    # make the loop seamless by cross-fading the ends
    xf = int(1.0 * SR)
    out[:xf] = out[:xf] * np.linspace(0, 1, xf) + out[-xf:] * np.linspace(1, 0, xf)
    return out[: n - xf]


def amb_night():
    d = 20.0
    n = int(SR * d)
    t = np.arange(n) / SR
    out = onepole(noise(d), 300) * 0.25
    for k in range(3):
        f = 4200 + k * 350
        rate = 2.2 + k * 0.7
        gate = (np.sin(2 * np.pi * rate * t + k) > 0.3).astype(float)
        trill = (np.sin(2 * np.pi * 28 * t) > 0).astype(float)
        out += np.sin(2 * np.pi * f * t) * gate * trill * 0.05 * (0.6 + 0.4 * np.sin(2 * np.pi * t / (7 + k)))
    xf = int(1.0 * SR)
    out[:xf] = out[:xf] * np.linspace(0, 1, xf) + out[-xf:] * np.linspace(1, 0, xf)
    return out[: n - xf]


# ---------------------------------------------------------------------------
# Music: slow pentatonic plucks over warm pads, lots of breathing space
# ---------------------------------------------------------------------------
def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pad(freqs, dur, vol=0.12):
    n = int(SR * dur)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):
            ff = f * 2 ** (det / 12)
            out += np.sin(2 * np.pi * ff * t + rng.uniform(0, 6)) * 0.33
    shape = np.sin(np.linspace(0, np.pi, n)) ** 1.5
    return onepole(out, 1400) * shape * vol


def music(seed, root, prog, tempo, bars, scale):
    local = np.random.default_rng(seed)
    beat = 60.0 / tempo
    bar = beat * 4
    total = bar * bars + 4.0
    out = np.zeros(int(SR * total))
    for b in range(bars):
        chord = prog[b % len(prog)]
        freqs = [midi(root + chord + iv) for iv in (0, 7, 12, 16)]
        place(out, pad(freqs, bar * 1.15, 0.10), b * bar)
        # bass pluck
        place(out, pluck(midi(root + chord - 12), bar, 0.997, 0.2) * 0.35, b * bar)
        # melody: sparse pentatonic notes
        step = 0
        while step < 8:
            if local.random() < 0.55:
                deg = scale[local.integers(0, len(scale))]
                octave = 12 if local.random() < 0.6 else 24
                note = midi(root + octave + deg)
                place(out, pluck(note, 2.5, 0.9985, 0.6) * local.uniform(0.18, 0.3), b * bar + step * beat * 0.5)
            step += local.choice([1, 2, 2, 3])
        if b % 4 == 3:
            place(out, bell(midi(root + 36 + scale[local.integers(0, len(scale))]), 2.5, 1.2, 0.4) * 0.08, b * bar + bar * 0.75)
    # gentle reverb-ish smear (a few feedback taps)
    wet = np.zeros_like(out)
    for delay, g in ((0.113, 0.35), (0.197, 0.28), (0.293, 0.22), (0.417, 0.16), (0.61, 0.12)):
        k = int(delay * SR)
        wet[k:] += out[:-k] * g
    out = out + onepole(wet, 3000) * 0.8
    fade_n = int(3.0 * SR)
    out[-fade_n:] *= np.linspace(1, 0, fade_n)
    return out


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "assets", "audio")
    os.makedirs(out_dir, exist_ok=True)
    simple = {
        "click": sfx_click, "place_stone": sfx_place_stone, "stone_tick": sfx_stone_tick,
        "place_wood": sfx_place_wood, "wood_tick": sfx_wood_tick, "place_path": sfx_place_path,
        "brush": sfx_brush, "build": sfx_build, "plant": sfx_plant, "erase": sfx_erase, "dig": sfx_dig,
        "rumble": sfx_rumble, "splash": sfx_splash, "undo": sfx_undo, "shutter": sfx_shutter,
        "season": sfx_season, "heart": sfx_heart, "nope": sfx_nope,
    }
    for name, fn in simple.items():
        write(out_dir, name, fn(), 0.7)
    for v in (1, 2):
        write(out_dir, f"baa_{v}", sfx_baa(v - 1), 0.7)
        write(out_dir, f"quack_{v}", sfx_quack(v - 1), 0.6)
        write(out_dir, f"cluck_{v}", sfx_cluck(v - 1), 0.5)
        write(out_dir, f"chirp_{v}", sfx_chirp(v - 1), 0.4)
    write(out_dir, "amb_day", amb_day(), 0.5)
    write(out_dir, "amb_night", amb_night(), 0.4)
    major_penta = [0, 2, 4, 7, 9]
    write(out_dir, "music_morning", music(1, 60, [0, 5, 9 - 12, 7 - 12], 76, 24, major_penta), 0.55)
    write(out_dir, "music_meadow", music(2, 57, [0, 5, 3, 7], 70, 24, [0, 3, 5, 7, 10]), 0.55)
    write(out_dir, "music_evening", music(3, 55, [0, 9 - 12, 5, 7], 64, 20, major_penta), 0.5)


if __name__ == "__main__":
    main()
