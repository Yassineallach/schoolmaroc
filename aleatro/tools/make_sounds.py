"""Renders Aleatro's sound effect library to audio/sfx/*.ogg.

Every sound is synthesized here from tones, filtered noise and envelopes,
so the game ships original audio with no third-party samples. Files named
`name_1`, `name_2`, ... are variations the game picks between at random.
Ambient loops are written seamless. Run: python3 tools/make_sounds.py
(needs numpy and ffmpeg with libvorbis).
"""
import os
import subprocess
import tempfile
import wave

import numpy as np

SR = 32000
OUT = os.path.join(os.path.dirname(__file__), "..", "audio", "sfx")
rng = np.random.default_rng(1234)


# ---------------------------------------------------------------- building blocks

def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def env(dur, attack=0.003, decay=8.0, hold=0.0):
    """Fast attack, optional hold, exponential decay."""
    t = t_axis(dur)
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    d = np.exp(-np.maximum(t - attack - hold, 0) * decay)
    return a * d


def fade(x, ms_in=2, ms_out=8):
    n_in, n_out = int(SR * ms_in / 1000), int(SR * ms_out / 1000)
    x = x.copy()
    if n_in:
        x[:n_in] *= np.linspace(0, 1, n_in)
    if n_out:
        x[-n_out:] *= np.linspace(1, 0, n_out)
    return x


def sine(freq, dur, phase=0.0):
    t = t_axis(dur)
    if callable(freq):
        return np.sin(2 * np.pi * np.cumsum(freq(t)) / SR + phase)
    return np.sin(2 * np.pi * freq * t + phase)


def tri(freq, dur):
    t = t_axis(dur)
    return 2 * np.abs(2 * ((freq * t) % 1) - 1) - 1


def square(freq, dur, soft=0.6):
    return np.tanh(sine(freq, dur) * (1 + 8 * soft)) / np.tanh(1 + 8 * soft)


def saw(freq, dur, partials=12):
    t = t_axis(dur)
    return sum(np.sin(2 * np.pi * freq * k * t) / k for k in range(1, partials + 1)) * 0.6


def noise(dur):
    return rng.uniform(-1, 1, int(dur * SR))


def band(x, lo, hi):
    """Band-pass by masking the spectrum (smooth edges)."""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    mask = 1 / (1 + (lo / np.maximum(f, 1)) ** 4) / (1 + (f / hi) ** 4)
    return np.fft.irfft(spec * mask, len(x))


def sweep_band(x, lo0, lo1, width):
    """Crude moving band-pass: blend chunks filtered at moving centres."""
    out = np.zeros_like(x)
    chunks = 24
    n = len(x)
    win = np.hanning(2 * (n // chunks) + 1)
    for i in range(chunks):
        c = lo0 + (lo1 - lo0) * i / (chunks - 1)
        y = band(x, c, c + width)
        s = max(0, i * n // chunks - n // chunks)
        e = min(n, s + len(win))
        out[s:e] += y[s:e] * win[: e - s]
    return out


def bell(freq, dur, decay=4.0, bright=0.5):
    """Inharmonic struck-metal partials."""
    ratios = [1, 2.76, 5.4, 8.93]
    amps = [1, 0.5 * bright, 0.25 * bright, 0.12 * bright]
    return sum(a * sine(freq * r, dur) * env(dur, 0.001, decay * (1 + i)) for i, (r, a) in enumerate(zip(ratios, amps)))


def chip(freq):
    """Ceramic poker-chip clack."""
    dur = 0.09
    body = sum(a * sine(freq * r, dur) for r, a in [(1, 1), (1.53, 0.6), (2.41, 0.4), (3.2, 0.2)])
    click = band(noise(dur), 2500, 9000) * env(dur, 0.0005, 120)
    return body * env(dur, 0.0005, 55) * 0.5 + click * 0.6


def mix(*parts):
    n = max(len(p) for _, p in parts)
    out = np.zeros(n)
    for start, p in parts:
        s = int(start * SR)
        e = min(n, s + len(p))
        if s < n:
            out[s:e] += p[: e - s]
    return out


def place(n_dur, *events):
    """events: (time, signal) placed into a buffer of n_dur seconds."""
    out = np.zeros(int(n_dur * SR))
    for start, p in events:
        s = int(start * SR)
        e = min(len(out), s + len(p))
        if s < len(out):
            out[s:e] += p[: e - s]
    return out


def norm(x, peak=0.8):
    m = np.max(np.abs(x))
    return x / m * peak if m > 0 else x


def note(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


# ---------------------------------------------------------------- UI

def button():
    d = 0.06
    return norm(sine(1800, d) * env(d, 0.001, 70) * 0.5 + band(noise(d), 1500, 6000) * env(d, 0.0005, 200), 0.55)


def card_select(pitch=1.0):
    d = 0.07
    chirp = sine(lambda t: 900 * pitch + 2500 * pitch * t, d) * env(d, 0.001, 60)
    tick = band(noise(d), 2500, 8000) * env(d, 0.0005, 150)
    return norm(chirp * 0.4 + tick, 0.5)


def card_slide(k):
    d = 0.13 + 0.02 * k
    x = sweep_band(noise(d), 900 + 200 * k, 3800, 1800) * env(d, 0.01, 25)
    return norm(fade(x), 0.45)


def card_flip():
    d = 0.08
    a = band(noise(d), 1800, 7000) * env(d, 0.0005, 160)
    return norm(place(0.12, (0, a), (0.035, a * 0.7)), 0.5)


def card_place():
    d = 0.12
    thud = sine(lambda t: 180 - 300 * t, d) * env(d, 0.001, 45)
    slap = band(noise(d), 800, 5000) * env(d, 0.0005, 90)
    return norm(thud * 0.6 + slap, 0.6)


def shuffle():
    clicks = []
    tpos = 0.0
    gap = 0.03
    for i in range(34):
        d = 0.03
        c = band(noise(d), 2000 + rng.uniform(0, 2500), 9000) * env(d, 0.0003, 260) * rng.uniform(0.5, 1)
        clicks.append((tpos, c))
        tpos += gap * rng.uniform(0.7, 1.1)
        gap *= 0.96
    whoosh = sweep_band(noise(tpos + 0.15), 600, 2400, 1500) * env(tpos + 0.15, 0.2, 4) * 0.25
    return norm(place(tpos + 0.2, (0, whoosh), *clicks), 0.6)


def discard():
    d = 0.24
    x = sweep_band(noise(d), 3500, 700, 1600) * env(d, 0.02, 12)
    return norm(fade(x), 0.5)


def slider_tick():
    d = 0.03
    return norm(sine(2600, d) * env(d, 0.0005, 180), 0.35)


def hold_tick():
    d = 0.04
    return norm(sine(1200, d) * env(d, 0.0005, 110), 0.3)


def pause(opening):
    d = 0.28
    lo, hi = (500, 2600) if opening else (2600, 500)
    x = sweep_band(noise(d), lo, hi, 900) * env(d, 0.05, 9)
    tone = sine(lambda t: (300 + 500 * t / d) if opening else (800 - 500 * t / d), d) * env(d, 0.02, 9) * 0.3
    return norm(fade(x + tone), 0.45)


def toast():
    return norm(place(0.5, (0, bell(note(84), 0.4, 6)), (0.09, bell(note(88), 0.4, 6))), 0.5)


# ---------------------------------------------------------------- scoring

def chips(k):
    base = [2100, 2350, 1900][k]
    return norm(place(0.14, (0, chip(base)), (0.025, chip(base * 1.12) * 0.6)), 0.6)


def mult(k):
    d = 0.22
    f0 = [150, 165, 140][k]
    # a punchy pitch-dropping hit, saturated so it reads on small speakers
    body = np.tanh(3 * sine(lambda t: f0 * (1 + 1.5 * np.exp(-t * 40)), d))
    hit = band(noise(d), 200, 2500) * env(d, 0.001, 50) * 0.5
    return norm((body * env(d, 0.002, 14) + hit), 0.6)


def xmult(k):
    d = 0.6
    root = [note(76), note(78), note(74)][k]
    chord = sum(saw(root * r, d, 8) for r in (1, 1.26, 1.5)) / 3
    chord = band(chord, 300, 7000) * env(d, 0.003, 5)
    shimmer = band(noise(d), 5000, 12000) * env(d, 0.002, 9) * 0.25
    zap = sine(lambda t: 600 + 4000 * t, 0.12) * env(0.12, 0.001, 30) * 0.4
    return norm(place(d, (0, chord + shimmer), (0, zap)), 0.75)


def again():
    return norm(place(0.3, *[(i * 0.045, square(note(79 + s), 0.08, 0.3) * env(0.08, 0.001, 35)) for i, s in enumerate([0, 4, 7, 12])]), 0.5)


def score_total():
    d = 0.9
    hit = bell(note(72), d, 2.5, 0.8) + bell(note(79), d, 2.5, 0.6) * 0.7
    return norm(hit + band(noise(d), 4000, 11000) * env(d, 0.002, 12) * 0.2, 0.75)


def tally():
    d = 0.035
    return norm(sine(3000, d) * env(d, 0.0005, 150), 0.25)


def not_allowed():
    d = 0.4
    buzz = (saw(110, d, 20) + saw(113, d, 20)) * 0.5
    return norm(fade(band(buzz, 100, 3000) * env(d, 0.005, 3, 0.25), 2, 60), 0.6)


# ---------------------------------------------------------------- money

def coin(k):
    a, b = [(988, 1319), (1047, 1397), (932, 1245)][k]
    t1 = square(a, 0.06, 0.2) * env(0.06, 0.001, 30)
    t2 = square(b, 0.35, 0.2) * env(0.35, 0.001, 9)
    return norm(place(0.4, (0, t1), (0.055, t2)), 0.45)


def cash_register():
    ding = bell(note(91), 1.0, 3, 0.9)
    drawer = band(noise(0.25), 300, 3000) * env(0.25, 0.01, 10) * 0.6
    coins = [(0.25 + i * 0.06 + rng.uniform(0, 0.02), chip(2600 + rng.uniform(-300, 600)) * 0.5) for i in range(8)]
    return norm(place(1.1, (0, drawer), (0.12, ding), *coins), 0.75)


def coin_cascade():
    events = [(i * 0.05 * (0.85 ** (i / 4)) + rng.uniform(0, 0.015), coin(i % 3) * rng.uniform(0.4, 0.9)) for i in range(14)]
    return norm(place(1.1, *events), 0.7)


# ---------------------------------------------------------------- cards and charms

def glass_shatter():
    d = 0.9
    crash = band(noise(d), 3000, 14000) * env(d, 0.0005, 9)
    tinkles = [(rng.uniform(0.02, 0.6), sine(rng.uniform(3000, 7500), 0.15) * env(0.15, 0.0005, 30) * rng.uniform(0.2, 0.5)) for _ in range(30)]
    thump = sine(lambda t: 220 - 150 * t, 0.15) * env(0.15, 0.001, 30) * 0.5
    return norm(place(d, (0, crash), (0, thump), *tinkles), 0.8)


def dissolve():
    d = 0.75
    hiss = band(noise(d), 1500, 6000) * env(d, 0.05, 4) * 0.35
    crackles = [(rng.uniform(0, 0.65), band(noise(0.01), 1000, 9000) * rng.uniform(0.4, 1)) for _ in range(45)]
    return norm(fade(place(d, (0, hiss), *crackles), 5, 80), 0.6)


def charm_buy():
    pop = sine(lambda t: 400 + 1800 * np.minimum(t / 0.05, 1), 0.12) * env(0.12, 0.002, 25)
    return norm(place(0.6, (0, pop * 0.6), (0.05, bell(note(81), 0.5, 5, 0.5)), (0.12, bell(note(88), 0.5, 5, 0.5))), 0.6)


def charm_sell():
    return norm(place(0.6, (0, coin(0)), (0.1, sine(lambda t: 1200 - 900 * t / 0.3, 0.3) * env(0.3, 0.002, 10) * 0.3)), 0.6)


def reroll():
    clicks = [(i * 0.028, chip(1600 + i * 60) * 0.5) for i in range(12)]
    swish = sweep_band(noise(0.4), 800, 4000, 1500) * env(0.4, 0.05, 7) * 0.4
    return norm(place(0.5, (0, swish), *clicks), 0.6)


def rune():
    d = 0.9
    gliss = sine(lambda t: 400 * 2 ** (3 * t / d), d) * env(d, 0.02, 3) * 0.35
    sparkles = [(i * 0.07, bell(note(84 + [0, 4, 7, 12, 16, 19][i]), 0.5, 7, 0.6) * 0.5) for i in range(6)]
    return norm(place(d + 0.2, (0, gliss), *sparkles), 0.7)


def spell_cast():
    d = 1.0
    chorus = sum(sine(lambda t, f=f: f * (1 + 0.5 * t), d) for f in (523, 528, 659, 664, 784)) / 5
    chorus *= env(d, 0.08, 2.5)
    whoosh = sweep_band(noise(d), 400, 6000, 2000) * env(d, 0.15, 3) * 0.4
    sparkle = band(noise(d), 7000, 13000) * env(d, 0.3, 4) * 0.25
    return norm(fade(chorus + whoosh + sparkle, 5, 120), 0.7)


def discover():
    return norm(place(0.8, *[(i * 0.08, bell(note(m), 0.6, 5, 0.6)) for i, m in enumerate([79, 83, 86, 91])]), 0.6)


def hold_done():
    return norm(place(0.5, (0, bell(note(76), 0.4, 6)), (0.06, bell(note(83), 0.45, 6))), 0.55)


# ---------------------------------------------------------------- blinds and rounds

def boss_intro():
    d = 3.0
    gong = sum(a * sine(65 * r, d) * env(d, 0.004, dec) for r, a, dec in [(1, 1, 1.2), (2.02, 0.6, 1.6), (2.98, 0.4, 2.0), (4.17, 0.25, 2.6), (5.43, 0.15, 3.2)])
    rumble = band(noise(d), 30, 200) * env(d, 0.3, 1.5) * 0.8
    return norm(fade(gong + rumble, 3, 400), 0.85)


def boss_ping(k):
    f = [note(57), note(55), note(53), note(52)][k]
    return norm(bell(f, 0.8, 3, 0.7), 0.55)


def blind_defeat():
    events = [(i * 0.09, bell(note(88 - i * 3), 0.6, 5, 0.6) * (1 - i * 0.08)) for i in range(7)]
    return norm(place(1.3, *events), 0.65)


def round_win():
    seq = [(0, 72), (0.1, 76), (0.2, 79), (0.32, 84)]
    lead = [(t, square(note(m), 0.35, 0.3) * env(0.35, 0.002, 6) * 0.4) for t, m in seq]
    bells = [(t, bell(note(m + 12), 0.6, 4, 0.5) * 0.4) for t, m in seq]
    return norm(place(1.1, *lead, *bells), 0.75)


def game_over():
    seq = [(0, 67), (0.35, 63), (0.7, 60), (1.05, 55)]
    tones = [(t, (tri(note(m), 0.9) * 0.6 + sine(note(m) / 2, 0.9) * 0.4) * env(0.9, 0.02, 2.5)) for t, m in seq]
    return norm(fade(place(2.2, *tones), 2, 300), 0.7)


def victory():
    melody = [(0, 72), (0.12, 76), (0.24, 79), (0.36, 84), (0.6, 83), (0.72, 84), (0.84, 88)]
    lead = [(t, square(note(m), 0.4, 0.3) * env(0.4, 0.002, 5) * 0.4) for t, m in melody]
    chord = [(0.84, sum(saw(note(m), 1.4, 8) for m in (60, 64, 67, 72)) * env(1.4, 0.01, 1.8) * 0.12)]
    bells = [(0.84 + i * 0.05, bell(note(96 - i * 5), 0.8, 3, 0.6) * 0.3) for i in range(5)]
    return norm(place(2.4, *lead, *chord, *bells), 0.8)


# ---------------------------------------------------------------- Ace

def voice(f1, f2, base):
    d = 0.075
    t = t_axis(d)
    glottal = 1 - ((t * base) % 1)
    v = (np.sin(2 * np.pi * f1 * t) * 0.6 + np.sin(2 * np.pi * f2 * t) * 0.3) * glottal
    return norm(v * np.sin(np.pi * t / d), 0.4)


def ace_appear():
    d = 0.6
    poof = band(noise(d), 300, 3000) * env(d, 0.01, 9) * 0.6
    sparkle = [(rng.uniform(0.05, 0.4), bell(rng.uniform(2000, 4500), 0.3, 12, 0.3) * 0.3) for _ in range(10)]
    return norm(place(d, (0, poof), *sparkle), 0.55)


# ---------------------------------------------------------------- ambient loops

def loop_ready(x, xfade=1.0):
    """Crossfade the tail into the head so the loop has no seam."""
    n = int(xfade * SR)
    body = x[:-n].copy()
    ramp = np.linspace(0, 1, n)
    body[:n] = body[:n] * ramp + x[-n:] * (1 - ramp)
    return body


def ambient_table():
    """A quiet card room: soft air, distant chip clinks, a faint shuffle and
    light vinyl crackle. Kept above ~250 Hz so phone speakers render it cleanly."""
    d = 21.0
    n = int(d * SR)
    t = t_axis(d)
    # gently breathing room air, mid-band only
    air = band(noise(d), 300, 1800) * (0.55 + 0.45 * np.sin(2 * np.pi * t / 10.5)) * 0.10
    events = [(0, air)]
    # distant chip clinks: small stacks of 1-3 clacks every second or two
    tpos = 0.6
    while tpos < d - 1.0:
        for k in range(rng.integers(1, 4)):
            events.append((tpos + k * rng.uniform(0.04, 0.09), chip(rng.uniform(1700, 2600)) * rng.uniform(0.12, 0.25)))
        tpos += rng.uniform(1.1, 2.6)
    # one soft shuffle in the background
    events.append((9.0, shuffle() * 0.18))
    # vinyl crackle: short clean ticks, clearly audible but sparse
    for _ in range(140):
        tick = band(noise(0.004), 1500, 6000) * np.hanning(int(0.004 * SR)) * rng.uniform(0.08, 0.22)
        events.append((rng.uniform(0, d - 0.01), tick))
    out = place(d, *events)
    return norm(loop_ready(out), 0.5)


def ambient_boss():
    """A slow, uneasy drone: two close fifths beating against each other,
    pitched where small speakers can still carry it."""
    d = 21.0
    t = t_axis(d)
    drone = (np.sin(2 * np.pi * 110 * t) + 0.7 * np.sin(2 * np.pi * 110.7 * t)
             + 0.5 * np.sin(2 * np.pi * 164.8 * t) + 0.35 * np.sin(2 * np.pi * 220.4 * t)) / 2.5
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / 7.0)
    # soft saturation adds upper harmonics, so small speakers still carry the pitch
    body = band(np.tanh(2.5 * drone), 100, 3000) * swell
    eerie = (np.sin(2 * np.pi * 659.3 * t) + 0.6 * np.sin(2 * np.pi * 663.0 * t)) * (0.5 + 0.5 * np.sin(2 * np.pi * t / 10.5)) * 0.06
    air = band(noise(d), 400, 2000) * (0.5 + 0.5 * np.sin(2 * np.pi * t / 5.25)) * 0.12
    return norm(loop_ready(body + eerie + air), 0.4)


# ---------------------------------------------------------------- output

SOUNDS = {
    "button": button,
    "card_select": lambda: card_select(1.0),
    "card_deselect": lambda: card_select(0.75),
    "card_slide_1": lambda: card_slide(0), "card_slide_2": lambda: card_slide(1), "card_slide_3": lambda: card_slide(2),
    "card_flip": card_flip,
    "card_place": card_place,
    "shuffle": shuffle,
    "discard": discard,
    "slider": slider_tick,
    "hold_tick": hold_tick,
    "hold_done": hold_done,
    "pause_open": lambda: pause(True),
    "pause_close": lambda: pause(False),
    "toast": toast,
    "chips_1": lambda: chips(0), "chips_2": lambda: chips(1), "chips_3": lambda: chips(2),
    "mult_1": lambda: mult(0), "mult_2": lambda: mult(1), "mult_3": lambda: mult(2),
    "xmult_1": lambda: xmult(0), "xmult_2": lambda: xmult(1), "xmult_3": lambda: xmult(2),
    "again": again,
    "score_total": score_total,
    "tally": tally,
    "not_allowed": not_allowed,
    "coin_1": lambda: coin(0), "coin_2": lambda: coin(1), "coin_3": lambda: coin(2),
    "cash_register": cash_register,
    "coin_cascade": coin_cascade,
    "glass_shatter": glass_shatter,
    "dissolve": dissolve,
    "charm_buy": charm_buy,
    "charm_sell": charm_sell,
    "reroll": reroll,
    "rune": rune,
    "spell_cast": spell_cast,
    "discover": discover,
    "boss_intro": boss_intro,
    "boss_ping_1": lambda: boss_ping(0), "boss_ping_2": lambda: boss_ping(1),
    "boss_ping_3": lambda: boss_ping(2), "boss_ping_4": lambda: boss_ping(3),
    "blind_defeat": blind_defeat,
    "round_win": round_win,
    "game_over": game_over,
    "victory": victory,
    "ace_appear": ace_appear,
    **{f"voice_{i + 1}": (lambda a=a: voice(*a)) for i, a in enumerate([
        (500, 1500, 190), (700, 1200, 200), (400, 2000, 185), (600, 1000, 195),
        (350, 900, 180), (650, 1700, 205), (450, 1300, 190), (550, 2200, 210)])},
    "ambient_table": ambient_table,
    "ambient_boss": ambient_boss,
}


def save(name, samples):
    pcm = (np.clip(samples, -1, 1) * 32767).astype(np.int16)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        path = tmp.name
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    dest = os.path.join(OUT, f"{name}.ogg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-c:a", "libvorbis", "-q:a", "5", dest], check=True)
    os.remove(path)
    return len(samples) / SR


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in SOUNDS.items():
        dur = save(name, fn())
        print(f"{name:16s} {dur:5.2f}s")
    print(f"{len(SOUNDS)} sounds written to {os.path.normpath(OUT)}")
