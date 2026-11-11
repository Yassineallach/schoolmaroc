"""Original music bed for "Les très grands nombres", synthesised in code (no samples, no rights).

    python music_score.py out/music.wav [seconds]

Calm and contemplative, 66 BPM, D major. Soft piano arpeggios over a warm pad and a low bass.
The opening phrase doubles its notes bar by bar (1, 2, 4, 8), the film's idea in music.
One change of mood, at the turning point (act 5, 3:26): B minor and a soft pulse.
The last act thins out and ends on a held D major chord.
"""
import sys
import numpy as np
from scipy.signal import fftconvolve

SR = 44100
BPM = 66
BEAT = 60 / BPM
BAR = 4 * BEAT
TURN = 205.9          # act 5 starts: tension
CLOSE = 271.8         # act 6 starts: return and thin out
rng = np.random.default_rng(1883)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env(n, a, r):
    e = np.ones(n)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na:
        e[:na] = np.linspace(0, 1, na) ** 2
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** 1.5
    return e


def piano(note, dur, vel):
    """Soft felt piano: a few inharmonic partials with their own decays and a muted attack."""
    n = int((dur + 2.5) * SR)
    t = np.arange(n) / SR
    f = midi(note)
    out = np.zeros(n)
    for k, (amp, dec) in enumerate([(1.0, 1.6), (0.42, 1.0), (0.18, 0.7), (0.08, 0.45), (0.04, 0.3)], start=1):
        fk = f * k * (1 + 0.0004 * k * k)
        if fk > 9000:
            break
        out += amp * np.sin(2 * np.pi * fk * t + rng.uniform(0, 6.28)) * np.exp(-t / (dec * (1.4 - note / 160)))
    out *= env(n, 0.006, 0.4)
    hold = np.ones(n)
    off = int(dur * SR)
    hold[off:] = np.exp(-np.arange(n - off) / (0.35 * SR))
    return out * hold * vel


def pad(notes, dur):
    """Warm pad: detuned sine stacks with a slow swell."""
    n = int((dur + 3.0) * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for note in notes:
        f = midi(note)
        for det in (-0.12, 0.0, 0.11):
            ff = f * 2 ** (det / 12)
            out += np.sin(2 * np.pi * ff * t) + 0.28 * np.sin(2 * np.pi * 2 * ff * t) + 0.08 * np.sin(2 * np.pi * 3 * ff * t)
    out *= (0.85 + 0.15 * np.sin(2 * np.pi * t / 7.3)) / (len(notes) * 3)
    return out * env(n, dur * 0.45, 2.8)


def bass(note, dur):
    n = int((dur + 1.5) * SR)
    t = np.arange(n) / SR
    f = midi(note)
    return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)) * env(n, 0.25, 1.4)


# chords: (bass, pad voicing, arpeggio pool)
D = 'D'
CH = {
    'Dmaj9': (38, [62, 66, 69, 73], [62, 66, 69, 73, 76, 78]),
    'Bm7':   (35, [62, 66, 69, 71], [59, 62, 66, 69, 71, 74]),
    'Gmaj7': (31, [62, 66, 67, 71], [59, 62, 66, 67, 71, 74]),
    'Asus':  (33, [62, 64, 69, 71], [57, 62, 64, 69, 71, 76]),
    'A':     (33, [61, 64, 69, 71], [57, 61, 64, 69, 71, 76]),
    'Em7':   (28, [62, 64, 67, 71], [59, 62, 64, 67, 71, 74]),
    'F#7':   (30, [61, 64, 66, 70], [58, 61, 64, 66, 70, 73]),
    'Bm':    (35, [59, 62, 66, 71], [59, 62, 66, 71, 74, 78]),
    'Gadd9': (31, [62, 67, 69, 71], [59, 62, 67, 69, 71, 74]),
}
A_PROG = ['Dmaj9', 'Bm7', 'Gmaj7', 'Asus', 'Dmaj9', 'Bm7', 'Gmaj7', 'A']
B_PROG = ['Bm', 'Gmaj7', 'Em7', 'F#7']
C_PROG = ['Dmaj9', 'Gadd9', 'Bm7', 'Asus']


def score(total):
    bars = []
    t, i = 0.0, 0
    while t < total - 9:
        if t < TURN:
            name = A_PROG[i % len(A_PROG)]; sec = 'A'
        elif t < CLOSE:
            name = B_PROG[i % len(B_PROG)]; sec = 'B'
        else:
            name = C_PROG[i % len(C_PROG)]; sec = 'C'
        bars.append((t, name, sec, i))
        t += BAR; i += 1
        if (sec == 'A' and t >= TURN) or (sec == 'B' and t >= CLOSE):
            i = 0
    bars.append((t, 'Dmaj9', 'END', 0))
    return bars


def render(total):
    n = int((total + 6) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(sig, at, pan=0.0, g=1.0):
        s = int(at * SR)
        e = min(n, s + len(sig))
        if e <= s:
            return
        L[s:e] += sig[:e - s] * g * np.sqrt(0.5 - pan / 2)
        R[s:e] += sig[:e - s] * g * np.sqrt(0.5 + pan / 2)

    for k, (t0, name, sec, i) in enumerate(score(total)):
        b, voicing, pool = CH[name]
        if sec == 'END':
            add(pad(voicing, 9.0), t0, 0, 0.5)
            add(bass(b, 8.0), t0, 0, 0.45)
            for j, nt in enumerate([62, 66, 69, 73, 78]):
                add(piano(nt, 6.0, 0.30), t0 + j * 0.42, -0.3 + j * 0.15, 0.8)
            break
        add(pad(voicing, BAR + 0.6), t0, 0, 0.42 if sec != 'B' else 0.48)
        if k >= 2:
            add(bass(b, BAR), t0, 0, 0.40)
        # piano: the opening doubles its notes bar by bar (1, 2, 4, 8), then settles into a varied arpeggio
        if k < 4:
            count = 2 ** k
        elif sec == 'C':
            count = 4 if i % 2 == 0 else 3
        else:
            count = 8 if (i % 4) != 3 else 6
        step = BAR / max(count, 1)
        order = list(pool)
        if i % 2:
            order = order[::-1]
        for j in range(count):
            nt = order[j % len(order)]
            if sec == 'C' and j == 0:
                nt += 12
            vel = (0.34 if j == 0 else 0.22) * rng.uniform(0.82, 1.08)
            jitter = rng.normal(0, 0.012)
            add(piano(nt, step * 1.6, vel), t0 + j * step + max(0, jitter), rng.uniform(-0.35, 0.35))
        if sec == 'B':                         # the soft pulse: muted low piano on the off-beats
            for j in range(8):
                if j % 2:
                    add(piano(b + 24, 0.18, 0.12 * rng.uniform(0.85, 1.1)), t0 + j * BAR / 8, 0.0)
        if sec == 'A' and k >= 6 and i % 8 == 7:   # a bell-like high note at phrase ends
            add(piano(pool[-1] + 12, 2.5, 0.10), t0 + 3 * BEAT, 0.4)

    # room: a short synthetic hall (stereo noise tail)
    m = int(2.8 * SR)
    tt = np.arange(m) / SR
    ir_l = rng.normal(0, 1, m) * np.exp(-tt / 0.9)
    ir_r = rng.normal(0, 1, m) * np.exp(-tt / 0.9)
    ir_l[:int(0.012 * SR)] = 0; ir_r[:int(0.017 * SR)] = 0
    ir_l /= np.sqrt((ir_l ** 2).sum()); ir_r /= np.sqrt((ir_r ** 2).sum())
    wl = fftconvolve(L, ir_l)[:n]; wr = fftconvolve(R, ir_r)[:n]
    L, R = 0.72 * L + 0.42 * wl, 0.72 * R + 0.42 * wr
    # gentle tilt: soften the highs
    from scipy.signal import lfilter
    k = np.exp(-2 * np.pi * 5200 / SR)
    L = lfilter([1 - k], [1, -k], L); R = lfilter([1 - k], [1, -k], R)
    out = np.stack([L, R], 1)
    fade = int(5 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    out /= np.abs(out).max() / 0.7
    return out


if __name__ == '__main__':
    import wave
    path = sys.argv[1]
    total = float(sys.argv[2]) if len(sys.argv) > 2 else 325.0
    a = render(total)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype('<i2').tobytes())
    print(path, f'{len(a) / SR:.1f} s')
