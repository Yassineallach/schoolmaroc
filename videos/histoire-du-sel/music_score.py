"""Original music bed for « L'histoire du sel », synthesised in code (no samples, no rights).

    python music_score.py out/music.wav [seconds] [--from S]

A journey across the world, 72 BPM. Plucked strings (oud-like), a low drone, a soft frame drum.

  A  acts 1-3   need, harvest, trade: A Dorian, a plucked figure over an A drone. The frame drum
                enters with the harvest (act 2) and walks under the caravans (act 3).
  B  act 4      power and revolt (the one change of mood): D minor, a heavier drum on beats 1 and 3,
                a low bowed line, the pluck plays fewer notes.
  C  act 5      abundance: the drum stops, the figure returns in A major and slows,
                ending on an open A chord held after the last word.
Times are narration time (music.py starts the bed after the intro). ACTS is updated from the
rendered acts so the changes land on the act cuts.
"""
import sys
import numpy as np
from scipy.signal import fftconvolve, lfilter

SR = 44100
BPM = 72
BEAT = 60 / BPM
BAR = 4 * BEAT
ACTS = [52.0, 50.0, 66.0, 47.0, 44.0]          # estimate until the acts are rendered
START = np.concatenate([[0], np.cumsum(ACTS)])
HARVEST, TURN, CLOSE, END = START[1], START[3], START[4], START[5]
rng = np.random.default_rng(1930)


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


def pluck(note, vel, decay=1.1):
    """Oud-like pluck: bright partials that die faster than the fundamental, a soft wooden knock."""
    n = int((decay * 2.2) * SR)
    t = np.arange(n) / SR
    f = midi(note)
    out = np.zeros(n)
    for k in range(1, 11):
        fk = f * k * (1 + 0.0007 * k * k)
        if fk > 8000:
            break
        amp = (1 / k) * (0.6 + 0.4 * np.sin(k * 1.3))   # plucked a third of the way along
        out += amp * np.sin(2 * np.pi * fk * t + rng.uniform(0, 6.28)) * np.exp(-t * k * 1.2 / decay)
    knock = rng.normal(0, 1, n) * np.exp(-t / 0.006) * 0.15
    out = out + lfilter([0.3], [1, -0.7], knock)
    return out * env(n, 0.002, 0.3) * vel


def drone(notes, dur):
    """Low drone: detuned sines with a slow breath, like a bowed tanpura-ish bed."""
    n = int((dur + 3) * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for note in notes:
        f = midi(note)
        for det in (-0.07, 0.0, 0.08):
            ff = f * 2 ** (det / 12)
            out += np.sin(2 * np.pi * ff * t) + 0.35 * np.sin(2 * np.pi * 2 * ff * t) + 0.12 * np.sin(2 * np.pi * 3 * ff * t)
    out *= (0.8 + 0.2 * np.sin(2 * np.pi * t / 6.1)) / (len(notes) * 3)
    return out * env(n, min(2.5, dur * 0.4), 2.5)


def bowed(note, dur, vel):
    """Low bowed line (act 4): sawtooth-ish, filtered, slow attack, light vibrato."""
    n = int((dur + 1.2) * SR)
    t = np.arange(n) / SR
    f = midi(note) * (1 + 0.003 * np.sin(2 * np.pi * 5.0 * t) * np.clip(t - 0.4, 0, 1))
    ph = 2 * np.pi * np.cumsum(f) / SR
    out = sum(np.sin(k * ph) / k for k in range(1, 9))
    k = np.exp(-2 * np.pi * 900 / SR)
    out = lfilter([1 - k], [1, -k], out)
    return out * env(n, 0.6, 1.0) * vel


def drum(vel, low=True):
    """Frame drum: a low thud with a pitch drop, or a rim tap."""
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    if low:
        f = 70 + 50 * np.exp(-t / 0.03)
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22)
        skin = rng.normal(0, 1, n) * np.exp(-t / 0.012) * 0.25
        return (body + lfilter([0.2], [1, -0.8], skin)) * vel
    tap = rng.normal(0, 1, n) * np.exp(-t / 0.02)
    k = np.exp(-2 * np.pi * 2500 / SR)
    return (lfilter([1 - k], [1, -k], tap) * 1.6 + np.sin(2 * np.pi * 330 * t) * np.exp(-t / 0.05) * 0.3) * vel


# A Dorian figure (A B C D E F# G), D minor (D E F G A Bb C), A major (A B C# D E F# G#)
FIG_A = [[57, 64, 69, 72, 71, 69, 66, 64], [57, 64, 69, 71, 72, 74, 72, 69],
         [55, 62, 67, 71, 69, 67, 64, 62], [57, 64, 69, 72, 76, 74, 72, 71]]
DRONE_A = [[33, 45, 52], [33, 45, 52], [31, 43, 50], [33, 45, 52]]
FIG_B = [[62, 69, 74, 77, 76, 74], [58, 65, 70, 74, 72, 70], [60, 67, 72, 76, 74, 72], [57, 64, 69, 73, 72, 69]]
DRONE_B = [[38, 50, 57], [34, 46, 53], [36, 48, 55], [33, 45, 52]]
BASS_B = [38, 34, 36, 33]
FIG_C = [[57, 64, 69, 73, 76], [54, 61, 66, 69, 73], [50, 57, 62, 66, 69], [52, 59, 64, 68, 71]]
DRONE_C = [[33, 45, 52], [30, 42, 49], [26, 38, 45], [28, 40, 47]]


def render(total, t_from=0.0):
    n = int((total + 8) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(sig, at, pan=0.0, g=1.0):
        s = int(at * SR)
        e = min(n, s + len(sig))
        if e <= s or s < 0:
            return
        L[s:e] += sig[:e - s] * g * np.sqrt(0.5 - pan / 2)
        R[s:e] += sig[:e - s] * g * np.sqrt(0.5 + pan / 2)

    t, i, last = 0.0, 0, None
    while t < min(total, END) - 2:
        sec = 'A' if t < TURN else ('B' if t < CLOSE else 'C')
        if sec != last:
            i, last = 0, sec
        j = i % 4
        if sec == 'A':
            add(drone(DRONE_A[j], BAR + 0.5), t, 0, 0.55)
            notes = FIG_A[j] if i >= 2 else FIG_A[j][:2 + 2 * i]      # the figure fills in at the start
            step = BAR / 8
            for k, nt in enumerate(notes):
                swing = 0.06 * BEAT if k % 2 else 0.0
                add(pluck(nt, (0.30 if k == 0 else 0.20) * rng.uniform(0.85, 1.1)),
                    t + k * step + swing + abs(rng.normal(0, 0.01)), rng.uniform(-0.4, 0.4))
            if t >= HARVEST:                                          # the walking frame drum
                add(drum(0.34), t, -0.1)
                add(drum(0.14, low=False), t + 1.5 * BEAT, 0.25)
                add(drum(0.24), t + 2 * BEAT, -0.1)
                add(drum(0.12, low=False), t + 3.5 * BEAT, 0.25)
        elif sec == 'B':
            add(drone(DRONE_B[j], BAR + 0.5), t, 0, 0.6)
            add(bowed(BASS_B[j] + 12, BAR, 0.18), t, 0.0)
            step = BAR / 6
            for k, nt in enumerate(FIG_B[j]):
                if k in (1, 4) and j % 2:
                    continue
                add(pluck(nt, 0.24 * rng.uniform(0.85, 1.1), 1.4), t + k * step, rng.uniform(-0.3, 0.3))
            add(drum(0.42), t, 0)
            add(drum(0.34), t + 2 * BEAT, 0)
        else:
            add(drone(DRONE_C[j], BAR + 0.5), t, 0, 0.5)
            step = BAR / 5
            for k, nt in enumerate(FIG_C[j]):
                add(pluck(nt, (0.26 if k == 0 else 0.17) * rng.uniform(0.9, 1.05), 1.6),
                    t + k * step, rng.uniform(-0.35, 0.35))
        t += BAR
        i += 1
    # the end: an open A chord, plucked slowly upward, then held by the drone
    if total >= END - 2:
        add(drone([33, 45, 52, 57], 9.0), t, 0, 0.55)
        for k, nt in enumerate([45, 52, 57, 61, 64, 69]):
            add(pluck(nt, 0.24, 2.4), t + k * 0.45, -0.3 + k * 0.12)

    # room: a short synthetic hall
    m = int(2.4 * SR)
    tt = np.arange(m) / SR
    irs = []
    for d in (0.011, 0.016):
        ir = rng.normal(0, 1, m) * np.exp(-tt / 0.75)
        ir[:int(d * SR)] = 0
        irs.append(ir / np.sqrt((ir ** 2).sum()))
    L, R = 0.74 * L + 0.40 * fftconvolve(L, irs[0])[:n], 0.74 * R + 0.40 * fftconvolve(R, irs[1])[:n]
    k = np.exp(-2 * np.pi * 5600 / SR)
    L, R = lfilter([1 - k], [1, -k], L), lfilter([1 - k], [1, -k], R)
    out = np.stack([L, R], 1)
    out = out[int(t_from * SR):]
    fade = int(5 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    out /= np.abs(out).max() / 0.7
    return out


def write(path, a):
    import wave
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype('<i2').tobytes())


if __name__ == '__main__':
    path = sys.argv[1]
    total = float(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else END + 8
    t_from = float(sys.argv[sys.argv.index('--from') + 1]) if '--from' in sys.argv else 0.0
    a = render(total, t_from)
    write(path, a)
    print(path, f'{len(a) / SR:.1f} s')
