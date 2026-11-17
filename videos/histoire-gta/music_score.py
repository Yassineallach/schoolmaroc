"""Original music bed for « L'histoire de GTA », synthesised in code (no samples, no rights).

    python music_score.py out/music.wav

Times are narration time (music.py starts the bed after the intro). Two moods, 96 BPM:

  A  acts 1-3   the origins: D minor, a low pulsing synth bass, a sparse muted pluck, a pad;
                tense and sneaky, like the bugged chase in Dundee. Thins out under the scandal (act 3).
  B  acts 4-7   the turning point, GTA III in 3D (the one change of mood): an 80s synth arpeggio over
                a soft drum-machine pulse, F major / D minor, the Vice City colour.
  Q  the last question of act 7: everything thins to a held suspended chord that never resolves.
"""
import sys
import numpy as np
from scipy.signal import fftconvolve, lfilter

SR = 44100
BPM = 96
BEAT = 60 / BPM
BAR = 4 * BEAT
# act lengths of the rendered acts 1-7 (out/actN.mp4), so the bed follows the picture
ACTS = [55.133, 53.533, 61.767, 47.633, 86.400, 46.567, 42.933]
START = np.concatenate([[0], np.cumsum(ACTS)])
TURN = START[3]               # act 4: GTA III, Liberty City in 3D
QUESTION = START[6] + 32.4    # act 7, « Après près de trois décennies, une question demeure »
END = START[7]
rng = np.random.default_rng(1997)


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


def lowpass(x, fc):
    k = np.exp(-2 * np.pi * fc / SR)
    return lfilter([1 - k], [1, -k], x)


def saw(f, t, partials=12):
    return sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, partials + 1))


def synth_bass(note, dur, vel):
    n = int((dur + 0.3) * SR)
    t = np.arange(n) / SR
    out = lowpass(saw(midi(note), t, 8), 420) * np.exp(-t / max(0.12, dur * 0.8))
    return out * env(n, 0.004, 0.08) * vel


def pluck(note, vel, decay=0.22, bright=1800):
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    out = lowpass(saw(midi(note), t, 10), bright) * np.exp(-t / decay)
    return out * env(n, 0.002, 0.1) * vel


def pad(notes, dur, swell=0.4, bright=1400):
    n = int((dur + 3.0) * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for note in notes:
        for det in (-0.08, 0.0, 0.07):
            out += saw(midi(note) * 2 ** (det / 12), t, 6)
    out = lowpass(out, bright) * (0.85 + 0.15 * np.sin(2 * np.pi * t / 5.3)) / (len(notes) * 3)
    return out * env(n, dur * swell, 2.6)


def kick(vel):
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    f = 48 + 90 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16) * vel


def hat(vel):
    n = int(0.08 * SR)
    x = rng.normal(0, 1, n)
    x = x - lowpass(x, 7000)
    return x * np.exp(-np.arange(n) / (SR * 0.018)) * vel


def snap(vel):
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    x = lowpass(x - lowpass(x, 900), 6000)
    return (x * np.exp(-t / 0.06) + 0.5 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04)) * vel


def bell(note, dur, vel):
    n = int((dur + 1.0) * SR)
    t = np.arange(n) / SR
    f = midi(note)
    out = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d)
              for a, r, d in [(1.0, 1.0, 2.6), (0.5, 2.76, 1.2), (0.25, 5.4, 0.6)])
    return out * env(n, 0.002, 0.6) * vel


# chords: (bass note, pad voicing, arpeggio notes)
CH = {
    'Dm':   (38, [57, 62, 65], [62, 65, 69, 74]),
    'Bb':   (34, [58, 62, 65], [58, 62, 65, 70]),
    'Gm':   (31, [58, 62, 67], [55, 58, 62, 67]),
    'A':    (33, [57, 61, 64], [57, 61, 64, 69]),
    'F':    (29, [60, 65, 69], [65, 69, 72, 77]),
    'C':    (36, [60, 64, 67], [64, 67, 72, 76]),
    'Asus': (33, [57, 62, 64], []),
}
A_PROG = ['Dm', 'Dm', 'Bb', 'A']
B_PROG = ['Dm', 'Bb', 'F', 'C']


def render(total):
    n = int((total + 8) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(sig, at, pan=0.0, g=1.0):
        s = int(at * SR)
        e = min(n, s + len(sig))
        if e <= s or s < 0:
            return
        L[s:e] += sig[:e - s] * g * np.sqrt(0.5 - pan / 2)
        R[s:e] += sig[:e - s] * g * np.sqrt(0.5 + pan / 2)

    # ---- A: the origins (acts 1-3)
    t, i = 0.0, 0
    while t + BAR <= TURN - BAR + 0.01:
        name = A_PROG[i % len(A_PROG)]
        b, voicing, arp = CH[name]
        scandal = t >= START[2]                       # act 3: thinner, darker
        if i % 2 == 0:
            add(pad(voicing, 2 * BAR, 0.4, 1000 if scandal else 1400), t, 0, 0.30)
        if i >= 1:                                    # the pulse: eighth notes, accents on 1 and the &-of-2
            for j in range(8):
                if scandal and j % 2:
                    continue
                vel = 0.34 if j in (0, 3) else 0.20
                add(synth_bass(b + (12 if j == 7 and i % 4 == 3 else 0), BEAT / 2 * 0.9, vel), t + j * BEAT / 2)
        if i >= 2 and not scandal:                    # the sneaky muted pluck, with rests
            pattern = [0, None, 2, 1, None, 3, None, 2] if i % 4 < 2 else [None, 1, None, 2, 3, None, 1, None]
            for j, k in enumerate(pattern):
                if k is not None:
                    add(pluck(arp[k], 0.20 * rng.uniform(0.85, 1.05), 0.12, 1400), t + j * BEAT / 2, rng.uniform(-0.4, 0.4))
        if scandal and i % 4 == 3:
            add(bell(74, 2.0, 0.07), t + 2 * BEAT, 0.3)
        t += BAR
        i += 1
    # one bar of held tension, then the turn
    add(pad(CH['Asus'][1], TURN - t + 0.5, 0.3), t, 0, 0.32)
    add(synth_bass(33, TURN - t, 0.28), t)

    # ---- B: the phenomenon (acts 4-7), the 80s arpeggio and the drum machine
    t, i = TURN, 0
    while t + BAR <= QUESTION - 0.01:
        name = B_PROG[i % len(B_PROG)]
        b, voicing, arp = CH[name]
        add(pad(voicing, BAR + 0.4, 0.15, 1800), t, 0, 0.26)
        for j in range(8):
            add(synth_bass(b, BEAT / 2 * 0.85, 0.30 if j % 2 == 0 else 0.20), t + j * BEAT / 2)
        if i >= 1:                                    # sixteenth-note arpeggio, up and down
            seq = arp + arp[-2:0:-1]
            for j in range(16):
                vel = (0.15 if j % 4 == 0 else 0.10) * rng.uniform(0.9, 1.05)
                add(pluck(seq[j % len(seq)] + 12, vel, 0.10, 2600), t + j * BEAT / 4, -0.35 + 0.7 * ((j // 2) % 2))
        if i >= 2:                                    # soft drum machine: kick on 1 and 3, snap on 2 and 4, hats
            for j in range(4):
                if j % 2 == 0:
                    add(kick(0.42), t + j * BEAT)
                else:
                    add(snap(0.16), t + j * BEAT, 0.1)
            for j in range(8):
                add(hat(0.05 if j % 2 else 0.08), t + j * BEAT / 2, 0.3)
        t += BAR
        i += 1

    # ---- Q: the question; a held suspension and a slow low pulse that never resolves
    q = t
    b, voicing, _ = CH['Asus']
    add(pad(voicing + [69], END - q + 2.0, 0.2, 1200), q, 0, 0.34)
    k = 0
    while q + k * BEAT * 2 < END - 1.0:
        add(synth_bass(b, BEAT, 0.22), q + k * BEAT * 2)
        k += 1
    add(bell(76, 4.0, 0.10), END - 3.0, 0.2)

    # room
    m = int(2.0 * SR)
    tt = np.arange(m) / SR
    irs = []
    for d in (0.011, 0.017):
        ir = rng.normal(0, 1, m) * np.exp(-tt / 0.55)
        ir[:int(d * SR)] = 0
        irs.append(ir / np.sqrt((ir ** 2).sum()))
    L = 0.78 * L + 0.32 * fftconvolve(L, irs[0])[:n]
    R = 0.78 * R + 0.32 * fftconvolve(R, irs[1])[:n]
    out = np.stack([L, R], 1)[:int(total * SR)]
    fade = int(4 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    out /= np.abs(out).max() / 0.7
    return out


if __name__ == '__main__':
    import wave
    path = sys.argv[1]
    total = float(sys.argv[2]) if len(sys.argv) > 2 else END + 1.0
    a = render(total)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype('<i2').tobytes())
    print(path, f'{len(a) / SR:.1f} s')
