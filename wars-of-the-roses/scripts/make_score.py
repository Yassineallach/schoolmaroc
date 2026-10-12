#!/usr/bin/env python3
"""Procedural underscore (original, generated here, so no licensing issues).

A slow D-minor string-like pad that follows the chapters, plus a few low impacts on the
battles. Rendered quietly; render.mjs ducks it further under the narration (sidechain).

Usage: python3 scripts/make_score.py output/build/score.wav
"""
import json, sys, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SR = 48000
meta = json.loads((ROOT / "data/scenes.json").read_text())
DUR = meta["meta"]["duration"]
N = int(DUR * SR)
t = np.arange(N) / SR

def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)

# chord progression (MIDI notes); each chord lasts ~8 s with long crossfades
PROG = [
    [38, 50, 57, 62, 65],  # Dm
    [34, 46, 53, 58, 62],  # Bb
    [31, 43, 55, 58, 62],  # Gm
    [33, 45, 52, 57, 61],  # A
    [38, 50, 57, 62, 65],  # Dm
    [36, 48, 55, 60, 64],  # C
    [34, 46, 53, 58, 65],  # Bb
    [33, 45, 52, 57, 64],  # A
]
CH = 8.0
rng = np.random.default_rng(1485)

def voice(freq, tt):
    out = np.zeros(len(tt))
    for det in (-0.0025, 0.0, 0.0031):
        f = freq * (1 + det)
        ph = rng.random() * 6.28
        for h in range(1, 7):
            out += np.sin(2 * np.pi * f * h * tt + ph * h) / h ** 1.6
    return out

pad = np.zeros(N)
n_chords = int(np.ceil(DUR / CH)) + 1
for i in range(n_chords):
    c0 = i * CH
    a, b = max(0, int((c0 - CH * 0.5) * SR)), min(N, int((c0 + CH * 1.5) * SR))
    if b <= a:
        continue
    tt = t[a:b]
    # raised-cosine window spanning 2 chord lengths -> smooth crossfade
    env = np.sin(np.pi * np.clip((tt - (c0 - CH * 0.5)) / (CH * 2), 0, 1)) ** 2
    for j, m in enumerate(PROG[i % len(PROG)]):
        pad[a:b] += voice(hz(m), tt) * env * (0.9 if j == 0 else 0.45)

def lowpass_fast(x, fc):
    # FFT brick-ish low-pass with soft roll-off (fast and good enough for a pad)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / fc) ** 4)
    return np.fft.irfft(X, len(x))

pad = lowpass_fast(pad, 900)
# slow swell / breathing
pad *= 0.75 + 0.25 * np.sin(2 * np.pi * t / 23.0)

# chapter-aware dynamics: quieter during exposition, fuller in battle chapters
dyn = np.full(N, 0.8)
for a, b, g in [(0, 7.5, 0.55), (19.3, 30, 1.0), (140, 168.8, 1.1), (245, 262, 1.2), (262, DUR, 0.9)]:
    m = (t >= a) & (t < b)
    dyn[m] = g
k = int(SR * 2)
dyn = np.convolve(dyn, np.ones(k) / k, mode="same")
pad *= dyn

# low impacts (battles, title, unification)
hits = [(24.5, 1.0), (151.5, 0.9), (161.2, 0.8), (195.8, 0.7), (250.4, 1.0), (257.6, 0.6)]
imp = np.zeros(N)
for at, g in hits:
    s = int(at * SR)
    L = int(3.5 * SR)
    tt = np.arange(L) / SR
    f = 52 * np.exp(-tt * 0.6) + 30
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 1.6)
    noise = lowpass_fast(rng.standard_normal(L), 380) * np.exp(-tt * 3.5) * 0.6
    seg = (body + noise) * g
    e = min(N, s + L)
    imp[s:e] += seg[: e - s]

mix = pad / (np.abs(pad).max() + 1e-9) * 0.16 + imp / (np.abs(imp).max() + 1e-9) * 0.22
# fade in / out
fade = np.minimum(np.clip(t / 3.0, 0, 1), np.clip((DUR - t) / 3.5, 0, 1))
mix *= fade
stereo = np.stack([mix, np.roll(mix, int(0.011 * SR))], axis=1)  # slight width
pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)

out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "output/build/score.wav")
out.parent.mkdir(parents=True, exist_ok=True)
with wave.open(str(out), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"score: {out} {DUR:.1f}s peak={20*np.log10(np.abs(mix).max()+1e-9):.1f}dBFS")
