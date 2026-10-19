"""Renders Aleatro's three music loops (table, shop, boss) to audio/*.ogg.

All tracks share tempo and length so the game can play them in sync and
crossfade between them. Run: python3 tools/make_music.py (needs numpy, ffmpeg).
"""
import os
import subprocess
import tempfile
import wave

import numpy as np

SR = 32000
BPM = 96
BEAT = 60 / BPM
BARS = 8
LENGTH = BARS * 4 * BEAT
N = int(LENGTH * SR)
TAIL = int(3 * SR)
OUT = os.path.join(os.path.dirname(__file__), "..", "audio")
rng = np.random.default_rng(7)


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def env(n, attack=0.005, decay=3.0):
    t = np.arange(n) / SR
    a = np.clip(t / attack, 0, 1)
    return a * np.exp(-t * decay)


def epiano(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    tone = (np.sin(2 * np.pi * f * t) * np.exp(-t * 2.5)
            + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 5)
            + 0.08 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t * 9))
    return tone * env(n, 0.004, 0.3)


def pluck(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 20)) * env(n, 0.002, 9)


def bell(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t * 3)) * env(n, 0.002, 2.2)


def bass(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    shape = np.clip(t / 0.01, 0, 1) * np.clip((dur - t) / 0.05, 0, 1)
    return np.tanh(1.6 * tone) * shape


def pad(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    tone = sum(np.sin(2 * np.pi * f * k * t * (1 + 0.002 * k)) / k for k in range(1, 7))
    shape = np.clip(t / 0.6, 0, 1) * np.clip((dur - t) / 0.6, 0, 1)
    return lowpass(tone * shape, 0.08)


def kick(dur=0.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    freq = 45 + 75 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 14)


def hat(dur=0.08):
    n = int(dur * SR)
    noise = rng.uniform(-1, 1, n)
    return np.diff(noise, prepend=0) * np.exp(-np.arange(n) / SR * 70)


def snare(dur=0.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = lowpass(rng.uniform(-1, 1, n), 0.4)
    return (0.6 * noise + 0.4 * np.sin(2 * np.pi * 185 * t)) * np.exp(-t * 22)


def lowpass(x, k):
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += k * (v - acc)
        y[i] = acc
    return y


class Track:
    def __init__(self):
        self.buf = np.zeros(N + TAIL)

    def add(self, beat, sound, vol):
        start = int(beat * BEAT * SR)
        end = min(start + len(sound), len(self.buf))
        self.buf[start:end] += sound[: end - start] * vol

    def render(self, peak=0.7):
        out = self.buf[:N].copy()
        out[:TAIL] += self.buf[N:]  # wrap tails so the loop is seamless
        return out / np.max(np.abs(out)) * peak


def swing(beat):
    return beat + (0.06 if beat % 1 == 0.5 else 0)


def table():
    """Laid-back A minor groove: Am9 Fmaj7 Dm9 E7, twice, with a melody the second time."""
    t = Track()
    chords = [[57, 60, 64, 67, 71], [53, 57, 60, 64], [50, 53, 57, 60, 64], [52, 56, 59, 62, 65]]
    roots = [45, 41, 38, 40]
    for bar in range(BARS):
        b = bar * 4
        ch = chords[bar % 4]
        for hit, length in ((0, 1.4), (1.5, 0.5), (2.5, 1.3)):
            for k, m in enumerate(ch):
                t.add(b + hit + 0.012 * k, epiano(hz(m), length + 1.5), 0.10)
        r = roots[bar % 4]
        for beat, m in ((0, r), (1.5, r + 7), (2, r + 12), (3, r + 7), (3.5, r + 10)):
            t.add(b + swing(beat), bass(hz(m - 12), 0.42), 0.32)
        for beat in (0, 2.5):
            t.add(b + beat, kick(), 0.55)
        for beat in (1, 3):
            t.add(b + beat, snare(), 0.18)
        for e in range(8):
            t.add(b + swing(e / 2), hat(), 0.05 if e % 2 else 0.08)
    melody = [(16, 76, 1), (17, 74, 0.5), (17.5, 72, 1.5), (19.5, 69, 0.5), (20, 72, 1), (21, 74, 1), (22, 76, 2),
              (24, 77, 1), (25, 76, 0.5), (25.5, 74, 1.5), (28, 71, 1), (29, 74, 1), (30, 76, 2)]
    for beat, m, d in melody:
        t.add(swing(beat), bell(hz(m), d + 1.2), 0.07)
    return t.render()


def shop():
    """Bouncy C major I-vi-ii-V with a plucked arpeggio."""
    t = Track()
    chords = [[60, 64, 67, 71], [57, 60, 64, 67], [62, 65, 69, 72], [55, 59, 62, 65]]
    roots = [36, 33, 38, 31]
    for bar in range(BARS):
        b = bar * 4
        ch = chords[bar % 4]
        for e in range(8):
            m = ch[[0, 1, 2, 3, 2, 1, 2, 3][e]] + 12
            t.add(b + swing(e / 2), pluck(hz(m), 0.6), 0.10)
        for hit in (0, 2):
            for m in ch:
                t.add(b + hit, epiano(hz(m), 2.2), 0.05)
        r = roots[bar % 4]
        for beat, m in ((0, r), (1, r + 12), (1.5, r + 7), (2, r), (3, r + 12), (3.5, r + 10)):
            t.add(b + swing(beat), bass(hz(m), 0.35), 0.3)
        for beat in (0, 1, 2, 3):
            t.add(b + beat, kick(), 0.4 if beat % 2 == 0 else 0.25)
        for beat in (1, 3):
            t.add(b + beat, snare(), 0.14)
        for e in range(8):
            t.add(b + swing(e / 2), hat(), 0.07)
    return t.render()


def boss():
    """Tense D minor pulse over a low pad, with a dissonant bell motif."""
    t = Track()
    pads = [[50, 53, 57], [51, 55, 58], [50, 53, 57], [48, 52, 55]]
    roots = [38, 39, 38, 36]
    for bar in range(BARS):
        b = bar * 4
        for m in pads[bar % 4]:
            t.add(b, pad(hz(m), 4.4), 0.12)
        r = roots[bar % 4]
        for e in range(8):
            t.add(b + e / 2, bass(hz(r - 12 + (12 if e == 7 else 0)), 0.22), 0.3)
        for beat in range(4):
            t.add(b + beat, kick(), 0.6)
        t.add(b + 3.5, kick(), 0.35)
        for e in range(16):
            t.add(b + e / 4, hat(0.05), 0.045 if e % 4 else 0.08)
        if bar % 2 == 1:
            t.add(b + 3, snare(0.3), 0.2)
    motif = [(0, 74), (1.5, 75), (3, 81), (4, 80)]
    for bar in (2, 6):
        for beat, m in motif:
            t.add(bar * 4 + beat, bell(hz(m), 2.5), 0.08)
    return t.render()


def save(name, samples):
    os.makedirs(OUT, exist_ok=True)
    pcm = (np.clip(samples, -1, 1) * 32767).astype(np.int16)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        path = tmp.name
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    dest = os.path.join(OUT, f"music_{name}.ogg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-c:a", "libvorbis", "-q:a", "4", dest], check=True)
    os.remove(path)
    print(dest, f"{LENGTH:.1f}s")


if __name__ == "__main__":
    save("table", table())
    save("shop", shop())
    save("boss", boss())
