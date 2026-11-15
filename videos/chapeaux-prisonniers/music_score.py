"""Original music bed for "L'énigme des chapeaux des prisonniers", synthesised in code (no samples, no rights).

    python music_score.py out/music.wav [seconds]

A puzzle in two moods, 90 BPM. Times are narration time (music.py starts the bed after the intro).

  A  0:00-1:10   the capture and the rules: A minor, sneaky pizzicato over a low pad, a woodblock now and then
  P  1:10-1:16   "Mettez la vidéo en pause": the music falls to a clock tick, one tick on each of
                 « Trois », « Deux », « Un », then silence
  B  1:16-2:44   the turning point, « La clé » (the one change of mood): A major, a marimba ostinato that
                 swings between two notes, like the parity passed down the line
  H  2:44-2:52   « Tout repose maintenant sur vous »: everything thins to a held suspended chord and a low pulse,
                 then near silence while your hat turns over
  R  2:52        the reveal: the chord resolves, a bell
  C  2:54-end    the rule and the release: the same colours, slower and sparser; ends on a held A major chord
"""
import sys
import numpy as np
from scipy.signal import fftconvolve, lfilter

SR = 44100
BPM = 90
BEAT = 60 / BPM
BAR = 4 * BEAT
PAUSE = 70.25         # clip 7 « Mettez la vidéo en pause »
TICKS = [71.11, 72.11, 73.11, 74.11, 75.11]   # the last three land on « Trois », « Deux », « Un »
TURN = 76.71          # clip 11 « La clé » : act 2
HOLD = 164.48         # clip 20 « Tout repose maintenant sur vous »
REVEAL = 172.35       # the silent beat after « chose » : your hat turns over
CLOSE = 173.95        # clip 21 : act 4
END = 210.13          # narration ends
rng = np.random.default_rng(1010)


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


def pluck(note, dur, vel):
    """Pizzicato string: Karplus-Strong with a soft, damped loop."""
    f = midi(note)
    p = max(2, int(SR / f))
    n = int((dur + 0.6) * SR)
    buf = rng.uniform(-1, 1, p)
    buf = lfilter([0.5, 0.5], [1], buf)
    out = np.zeros(n)
    damp = 0.996 if note < 50 else 0.992
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = damp * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    out *= np.exp(-np.arange(n) / (SR * (0.55 if note < 50 else 0.35)))
    return out * env(n, 0.002, 0.08) * vel


def marimba(note, vel):
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    f = midi(note)
    out = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.42)
           + 0.35 * np.sin(2 * np.pi * 3.93 * f * t) * np.exp(-t / 0.08)
           + 0.12 * np.sin(2 * np.pi * 9.2 * f * t) * np.exp(-t / 0.03))
    return out * env(n, 0.003, 0.2) * vel


def bell(note, dur, vel):
    n = int((dur + 1.0) * SR)
    t = np.arange(n) / SR
    f = midi(note)
    out = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d)
              for a, r, d in [(1.0, 1.0, 2.6), (0.5, 2.76, 1.2), (0.25, 5.4, 0.6), (0.12, 8.9, 0.3)])
    return out * env(n, 0.002, 0.6) * vel


def pad(notes, dur, swell=0.45):
    n = int((dur + 3.0) * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for note in notes:
        f = midi(note)
        for det in (-0.10, 0.0, 0.09):
            ff = f * 2 ** (det / 12)
            out += np.sin(2 * np.pi * ff * t) + 0.22 * np.sin(2 * np.pi * 2 * ff * t)
    out *= (0.85 + 0.15 * np.sin(2 * np.pi * t / 6.1)) / (len(notes) * 3)
    return out * env(n, dur * swell, 2.6)


def bass(note, dur):
    n = int((dur + 1.0) * SR)
    t = np.arange(n) / SR
    f = midi(note)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * env(n, 0.02, 0.6) * np.exp(-t / 1.2)


def tick(vel, hi=True):
    """Woodblock / clock tick: a resonant knock."""
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    f = 1850 if hi else 1250
    out = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.018) + 0.4 * rng.normal(0, 1, n) * np.exp(-t / 0.004)
    return out * vel


# chords: (bass, pad voicing, line pool)
CH = {
    'Am':    (33, [57, 60, 64], [45, 52, 57, 52]),
    'F':     (29, [57, 60, 65], [41, 48, 53, 48]),
    'Dm':    (38, [57, 62, 65], [38, 45, 50, 45]),
    'E':     (28, [56, 59, 64], [40, 47, 52, 51]),
    'A':     (33, [61, 64, 69], [69, 73]),          # B: the marimba swings between two notes
    'E/G#':  (32, [59, 64, 68], [68, 71]),
    'F#m':   (30, [61, 66, 69], [69, 73]),
    'D':     (38, [62, 66, 69], [66, 69]),
    'Esus':  (28, [59, 64, 69], []),
    'Aadd9': (33, [61, 64, 69, 71], []),
}
A_PROG = ['Am', 'Am', 'F', 'F', 'Dm', 'Dm', 'E', 'E']
B_PROG = ['A', 'E/G#', 'F#m', 'D', 'A', 'E/G#', 'D', 'E']
C_PROG = ['A', 'D', 'F#m', 'E']


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

    # ---- A: the capture and the rules
    t, i = 0.0, 0
    while t + BAR <= PAUSE + 0.01:
        name = A_PROG[i % len(A_PROG)]
        b, voicing, line = CH[name]
        if i % 2 == 0:
            add(pad(voicing, 2 * BAR), t, 0, 0.32 if i else 0.0)
        if i >= 1:
            add(bass(b, BAR), t, 0, 0.30)
        if i >= 2:                                   # the sneaky pizzicato line, eighth notes with rests
            pattern = [0, None, 1, 2, None, 3, 2, None] if i % 4 < 2 else [0, 1, None, 2, 3, None, 2, 1]
            for j, k in enumerate(pattern):
                if k is None:
                    continue
                swing = 0.06 * BEAT if j % 2 else 0.0
                add(pluck(line[k] + 12, BEAT / 2, 0.42 * rng.uniform(0.85, 1.05)), t + j * BEAT / 2 + swing,
                    rng.uniform(-0.3, 0.3))
        if i >= 4 and i % 4 == 3:
            add(tick(0.10, i % 8 == 3), t + 3.5 * BEAT, 0.5)
        t += BAR
        i += 1
    # the bar before the pause fades into the clock
    add(pad(CH['E'][1], PAUSE - t + 1.5, 0.2), t, 0, 0.22)

    # ---- P: the clock, then silence
    for k, tt in enumerate(TICKS):
        add(tick(0.34 if tt >= TICKS[2] else 0.22, k % 2 == 0), tt, 0.0)

    # ---- B: « La clé », A major, the two-note marimba ostinato
    t, i = TURN, 0
    while t + BAR <= HOLD + 0.01:
        name = B_PROG[i % len(B_PROG)]
        b, voicing, two = CH[name]
        add(pad(voicing, BAR + 0.4), t, 0, 0.30)
        add(bass(b, BAR), t, 0, 0.30)
        add(pluck(b + 12, BEAT, 0.35), t + 2 * BEAT, 0)
        if i >= 1:
            for j in range(8):
                nt = two[j % 2]
                vel = (0.30 if j % 4 == 0 else 0.20) * rng.uniform(0.85, 1.05)
                add(marimba(nt, vel), t + j * BEAT / 2 + max(0, rng.normal(0, 0.008)), -0.25 + 0.5 * (j % 2))
        if i >= 8 and i % 4 == 2:                    # a high answer every other phrase
            add(marimba(two[1] + 12, 0.14), t + 3 * BEAT, 0.4)
        t += BAR
        i += 1
    # ---- H: everything rests on you; a held suspension and a low pulse
    add(pad(CH['Esus'][1], REVEAL - t - 0.3, 0.25), t, 0, 0.34)
    k = 0
    while t + k * BEAT < REVEAL - 1.0:
        add(bass(CH['Esus'][0], 0.4), t + k * BEAT, 0, 0.22 if k % 2 == 0 else 0.12)
        k += 1
    # ---- R: the reveal
    b, voicing, _ = CH['Aadd9']
    add(pad(voicing, 3.0, 0.05), REVEAL, 0, 0.36)
    add(bass(b, 2.5), REVEAL, 0, 0.34)
    add(bell(81, 3.0, 0.22), REVEAL, 0.2)
    add(bell(76, 3.0, 0.12), REVEAL + 0.18, -0.2)

    # ---- C: the rule and the release, slower and sparser
    t, i = CLOSE + BAR / 2, 0
    while t + BAR <= END - 2 * BAR + 0.01:
        name = C_PROG[i % len(C_PROG)]
        b, voicing, two = CH[name]
        add(pad(voicing, BAR + 0.4), t, 0, 0.28)
        add(bass(b, BAR), t, 0, 0.26)
        for j in (0, 3, 5) if i % 2 == 0 else (0, 2, 6):
            add(marimba(two[j % 2], 0.20 * rng.uniform(0.85, 1.05)), t + j * BEAT / 2, -0.2 + 0.4 * (j % 2))
        t += BAR
        i += 1
    b, voicing, _ = CH['Aadd9']
    add(pad(voicing, 8.0, 0.2), t, 0, 0.36)
    add(bass(b, 6.0), t, 0, 0.30)
    for j, nt in enumerate([69, 73, 76, 81]):
        add(marimba(nt, 0.18), t + j * 0.33, -0.3 + j * 0.2)
    add(bell(81, 5.0, 0.12), t + 1.4, 0.2)

    # room
    m = int(2.2 * SR)
    tt = np.arange(m) / SR
    irs = []
    for d in (0.010, 0.015):
        ir = rng.normal(0, 1, m) * np.exp(-tt / 0.7)
        ir[:int(d * SR)] = 0
        irs.append(ir / np.sqrt((ir ** 2).sum()))
    L = 0.75 * L + 0.38 * fftconvolve(L, irs[0])[:n]
    R = 0.75 * R + 0.38 * fftconvolve(R, irs[1])[:n]
    k = np.exp(-2 * np.pi * 6000 / SR)
    L = lfilter([1 - k], [1, -k], L)
    R = lfilter([1 - k], [1, -k], R)
    out = np.stack([L, R], 1)[:int(total * SR)]
    # true silence between the last tick and « La clé », and a breath before the reveal
    for a, b in [(TICKS[-1] + 0.45, TURN - 0.05), (REVEAL - 0.8, REVEAL - 0.02)]:
        s, e = int(a * SR), int(b * SR)
        f = min(int(0.25 * SR), e - s)
        out[s:s + f] *= np.linspace(1, 0, f)[:, None]
        out[s + f:e] = 0
    fade = int(4 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    out /= np.abs(out).max() / 0.7
    return out


if __name__ == '__main__':
    import wave
    path = sys.argv[1]
    total = float(sys.argv[2]) if len(sys.argv) > 2 else END + 10.4
    a = render(total)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype('<i2').tobytes())
    print(path, f'{len(a) / SR:.1f} s')
