"""Context-aware colour system: every video gets a palette chosen for its subject, and every
scene can shift tone (mood) without leaving that palette.

    episode.json  {"theme": "manga_ink", "palette": "manga_ink"}      # identity of the whole video
    import palette as PL
    PL.ACTIVE.accent                    # the episode accent (every module reads its colours from here)
    s.mood = 'grief'                    # a scene's emotional tone: a grade derived from the palette

Every drawing module (typo, annotate, charts, maps, timeline, objects, transitions, scenes,
presets, style, vox) takes its colours from ACTIVE at import time, so one entry in episode.json
recolours type, marks, charts, maps, environments and props together. Nothing hardcodes
terracotta or cream any more: those belong to the 'editorial' palette only.

PALETTES (pick by subject; storyboard.py suggests one from the transcript)
    editorial        warm paper, charcoal, terracotta           general explainers, book summaries
    history_archive  aged paper, sepia, oxblood, ochre          history, biography, the press, war
    science_space    pale paper / deep navy, cobalt, violet     science, space, physics, cosmology
    manga_ink        off-white, black ink, greys, blood red     manga, anime, comics
    crime            cold newsprint, charcoal, dark red, steel  crime, investigations, trials, cults
    technology       near-black, electric blue, cyan            technology, computing, AI, internet
    philosophy       warm ivory, deep green, muted gold         religion, philosophy, ethics, myth
    nature           linen, forest, moss, clay                  nature, animals, climate, geography

FIELDS
    paper paper2 cream   light grounds (main, aged/secondary, minimalist)
    dark                 dark ground (drama, night)
    ink ink2 muted       text on light grounds: primary, secondary, labels
    light                text on dark grounds
    accent accent2       highlights on light grounds (accent = the one that matters)
    accent_dark          highlight that reads on the dark ground
    solid                ground of the solid-colour environment ('accent'), light text reads on it
    soft line tint       low-emphasis fills (bar bases, land), hairlines and grids, stains/halftone
    land coast border    map colours (derived when not given)

MOODS (s.mood = ..., or scenes.env(s, name, mood=...)): a gentle whole-frame grade plus which
accent the scene leans on. Derived from the palette, never a new hue, so a mood change reads as
the same film changing tone.
    neutral calm wonder hope triumph tense mystery menace grief
"""
import os, json
from dataclasses import dataclass, field, replace


def _mix(a, b, k):
    return tuple(int(round(a[i] + (b[i] - a[i]) * k)) for i in range(3))


@dataclass(frozen=True)
class Palette:
    name: str
    subject: str
    paper: tuple
    paper2: tuple
    cream: tuple
    dark: tuple
    ink: tuple
    ink2: tuple
    muted: tuple
    light: tuple
    accent: tuple
    accent2: tuple
    accent_dark: tuple
    solid: tuple
    soft: tuple
    line: tuple
    tint: tuple
    land: tuple = None
    coast: tuple = None
    border: tuple = None
    keywords: tuple = field(default=(), compare=False)

    def __post_init__(self):
        if self.land is None:
            object.__setattr__(self, 'land', _mix(self.soft, self.paper, 0.25))
        if self.coast is None:
            object.__setattr__(self, 'coast', _mix(self.ink2, self.muted, 0.4))
        if self.border is None:
            object.__setattr__(self, 'border', _mix(self.muted, self.soft, 0.4))


PALETTES = {p.name: p for p in (
    Palette('editorial', 'general explainers, book summaries',
            paper=(246, 229, 202), paper2=(236, 226, 202), cream=(244, 236, 222), dark=(34, 31, 30),
            ink=(28, 24, 22), ink2=(44, 42, 40), muted=(110, 104, 96), light=(244, 238, 224),
            accent=(205, 88, 48), accent2=(222, 140, 80), accent_dark=(232, 120, 78), solid=(176, 70, 36),
            soft=(221, 200, 170), line=(206, 194, 168), tint=(176, 140, 92),
            keywords=('book', 'summary', 'novel', 'author', 'idea', 'lesson')),
    Palette('history_archive', 'history, biography, the press, war',
            paper=(236, 224, 198), paper2=(226, 210, 178), cream=(240, 232, 214), dark=(40, 31, 24),
            ink=(36, 27, 20), ink2=(70, 55, 42), muted=(112, 94, 74), light=(240, 230, 208),
            accent=(136, 40, 30), accent2=(150, 108, 44), accent_dark=(214, 160, 92), solid=(118, 38, 28),
            soft=(208, 186, 150), line=(190, 170, 136), tint=(150, 112, 64),
            keywords=('century', 'empire', 'king', 'queen', 'war', 'revolution', 'ancient', 'dynasty', 'battle', 'treaty',
                      'colonial', 'medieval', 'history', 'historian', 'archive', 'born in', 'died in', 'reign')),
    Palette('science_space', 'science, space, physics, cosmology',
            paper=(230, 234, 242), paper2=(214, 220, 234), cream=(238, 240, 246), dark=(12, 16, 38),
            ink=(14, 18, 42), ink2=(38, 46, 80), muted=(86, 94, 128), light=(232, 236, 250),
            accent=(52, 82, 214), accent2=(126, 74, 200), accent_dark=(255, 196, 92), solid=(30, 44, 120),
            soft=(194, 202, 226), line=(176, 186, 214), tint=(90, 110, 180),
            keywords=('universe', 'galaxy', 'star', 'planet', 'black hole', 'physics', 'quantum', 'gravity', 'atom',
                      'light', 'space', 'cosmic', 'telescope', 'relativity', 'particle', 'experiment', 'scientist', 'orbit')),
    Palette('manga_ink', 'manga, anime, comics',
            paper=(243, 236, 222), paper2=(230, 222, 206), cream=(246, 242, 234), dark=(20, 18, 18),
            ink=(18, 16, 16), ink2=(50, 46, 44), muted=(104, 100, 96), light=(244, 240, 232),
            accent=(170, 26, 34), accent2=(92, 88, 84), accent_dark=(222, 58, 58), solid=(150, 22, 30),
            soft=(214, 208, 198), line=(190, 184, 174), tint=(120, 112, 104),
            keywords=('manga', 'anime', 'chapter', 'volume', 'serialized', 'serialised', 'mangaka', 'shonen', 'seinen',
                      'shojo', 'panel', 'comic', 'artist', 'drew', 'magazine', 'studio')),
    Palette('crime', 'crime, investigations, trials',
            paper=(226, 226, 222), paper2=(208, 210, 208), cream=(234, 234, 232), dark=(22, 24, 28),
            ink=(20, 22, 26), ink2=(50, 54, 60), muted=(96, 102, 110), light=(232, 234, 236),
            accent=(146, 26, 28), accent2=(56, 88, 122), accent_dark=(222, 70, 62), solid=(122, 22, 24),
            soft=(196, 198, 198), line=(170, 174, 178), tint=(118, 122, 118),
            keywords=('murder', 'killer', 'police', 'detective', 'crime', 'victim', 'trial', 'court', 'evidence',
                      'investigation', 'suspect', 'prison', 'fbi', 'cult', 'disappeared', 'body', 'heist', 'fraud')),
    Palette('technology', 'technology, computing, AI',
            paper=(234, 240, 245), paper2=(218, 228, 236), cream=(240, 244, 247), dark=(10, 15, 24),
            ink=(12, 20, 30), ink2=(38, 52, 68), muted=(86, 102, 118), light=(224, 240, 250),
            accent=(0, 100, 196), accent2=(0, 128, 150), accent_dark=(56, 214, 255), solid=(0, 70, 150),
            soft=(196, 212, 224), line=(176, 196, 212), tint=(60, 120, 160),
            keywords=('computer', 'software', 'internet', 'algorithm', 'ai', 'artificial intelligence', 'chip', 'silicon',
                      'startup', 'code', 'data', 'network', 'digital', 'robot', 'app', 'smartphone', 'engineer')),
    Palette('philosophy', 'religion, philosophy, ethics, myth',
            paper=(244, 238, 222), paper2=(232, 223, 200), cream=(247, 243, 232), dark=(20, 38, 30),
            ink=(28, 32, 26), ink2=(54, 62, 50), muted=(100, 102, 86), light=(242, 236, 218),
            accent=(30, 88, 62), accent2=(140, 108, 40), accent_dark=(218, 186, 108), solid=(26, 74, 54),
            soft=(214, 206, 180), line=(194, 186, 160), tint=(150, 132, 90),
            keywords=('god', 'faith', 'prophet', 'religion', 'soul', 'philosopher', 'philosophy', 'ethics', 'virtue',
                      'meaning', 'scripture', 'temple', 'monk', 'stoic', 'myth', 'divine', 'prayer', 'truth')),
    Palette('nature', 'nature, animals, climate, geography',
            paper=(238, 234, 220), paper2=(224, 218, 196), cream=(244, 241, 230), dark=(22, 34, 28),
            ink=(24, 30, 24), ink2=(52, 62, 50), muted=(98, 104, 88), light=(238, 240, 228),
            accent=(46, 106, 64), accent2=(166, 92, 52), accent_dark=(150, 210, 120), solid=(40, 90, 56),
            soft=(206, 204, 176), line=(186, 184, 156), tint=(128, 120, 84),
            keywords=('forest', 'ocean', 'animal', 'species', 'climate', 'river', 'mountain', 'evolution', 'ecosystem',
                      'wildlife', 'bird', 'plant', 'earth', 'extinct')),
)}

# palette that suits each background theme when episode.json names a theme but no palette
THEME_PALETTE = {'editorial': 'editorial', 'album': 'editorial', 'cosmic_atlas': 'science_space', 'deep_space': 'science_space',
                 'laboratory': 'science_space', 'clinic': 'science_space', 'circuit': 'technology', 'archive': 'history_archive',
                 'ledger': 'history_archive', 'ink_studio': 'manga_ink', 'manga_ink': 'manga_ink'}


# ------------------------------------------------------------------ contrast
def luminance(c):
    def ch(v):
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(float(x)) for x in c[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# (foreground, background, minimum): body text 7, secondary 4.5, accents / large type 3
CHECKS = (('ink', 'paper', 7.0), ('ink', 'paper2', 7.0), ('ink', 'cream', 7.0), ('ink2', 'paper', 4.5),
          ('muted', 'paper', 3.0), ('light', 'dark', 7.0), ('accent', 'paper', 3.0), ('accent', 'cream', 3.0),
          ('accent_dark', 'dark', 3.0), ('light', 'solid', 4.5), ('light', 'accent', 3.0))


def validate(p):
    """List of (fg, bg, ratio, minimum) pairs that fail. Empty = the palette reads everywhere."""
    out = []
    for fg, bg, lo in CHECKS:
        c = contrast(getattr(p, fg), getattr(p, bg))
        if c < lo:
            out.append((fg, bg, round(c, 2), lo))
    return out


# ------------------------------------------------------------------ moods
# grade: (saturation, warmth -1..1, contrast, lift 0..1 towards paper, darken 0..1); lean: which accent
MOODS = {
    'neutral': dict(grade=(1.00, 0.00, 1.00, 0.00, 0.00), lean='accent'),
    'calm':    dict(grade=(0.92, 0.04, 0.96, 0.03, 0.00), lean='accent2'),
    'wonder':  dict(grade=(1.06, -0.04, 1.04, 0.00, 0.00), lean='accent'),
    'hope':    dict(grade=(1.04, 0.07, 1.00, 0.04, 0.00), lean='accent2'),
    'triumph': dict(grade=(1.10, 0.06, 1.06, 0.00, 0.00), lean='accent'),
    'tense':   dict(grade=(0.88, -0.06, 1.08, 0.00, 0.04), lean='accent'),
    'mystery': dict(grade=(0.80, -0.08, 1.04, 0.00, 0.08), lean='accent2'),
    'menace':  dict(grade=(0.78, -0.04, 1.12, 0.00, 0.10), lean='accent'),
    'grief':   dict(grade=(0.62, -0.03, 0.94, 0.02, 0.06), lean='muted'),
}

MOOD_WORDS = {
    'grief':   ('died', 'death', 'dies', 'funeral', 'mourning', 'grief', 'loss', 'lost', 'memorial', 'killed', 'passed away', 'last chapter'),
    'menace':  ('murder', 'massacre', 'betray', 'sacrifice', 'eclipse', 'demon', 'horror', 'violence', 'torture', 'war'),
    'tense':   ('but', 'however', 'refused', 'rejected', 'crisis', 'struggle', 'fight', 'danger', 'conflict', 'risk'),
    'mystery': ('unknown', 'secret', 'mystery', 'nobody knew', 'hidden', 'disappeared', 'strange', 'why'),
    'triumph': ('won', 'award', 'million', 'success', 'record', 'bestselling', 'prize', 'victory', 'became'),
    'hope':    ('began', 'continue', 'promise', 'dream', 'new', 'friend', 'together', 'hope'),
    'wonder':  ('universe', 'infinite', 'vast', 'galaxy', 'beautiful', 'stars', 'imagine'),
    'calm':    ('quiet', 'slowly', 'peace', 'home', 'sleep'),
}


def detect_mood(text):
    """The strongest mood the words of a line carry, or 'neutral'."""
    low = ' ' + text.lower() + ' '
    best, score = 'neutral', 0
    weight = {'grief': 3, 'menace': 3, 'mystery': 2, 'triumph': 2, 'tense': 1, 'hope': 1, 'wonder': 2, 'calm': 1}
    for m, words in MOOD_WORDS.items():
        s = sum(weight[m] for wd in words if f' {wd} ' in low or f' {wd},' in low or f' {wd}.' in low)
        if s > score:
            best, score = m, s
    return best


def plan_moods(rows, hold=2):
    """Mood per planned shot, smoothed so the tone never flickers: a strong mood (grief, menace)
    starts on its line and holds for `hold` neutral lines after; a single weak cue between
    neutral lines is ignored. Returns rows with r['mood']."""
    raw = [detect_mood(r.get('sentence', r.get('text', ''))) for r in rows]
    strong = {'grief', 'menace', 'triumph', 'mystery', 'wonder'}
    out, cur, left = [], 'neutral', 0
    for i, m in enumerate(raw):
        nxt = raw[i + 1] if i + 1 < len(raw) else 'neutral'
        if m == 'neutral':                       # neutral lines inherit the held tone, then let it go
            if left > 0:
                left -= 1
            else:
                cur = 'neutral'
        elif cur in ('grief', 'menace') and m not in strong and left > 0:
            left -= 1                            # a heavy tone is not broken by a passing 'but'
        elif m in strong or cur != 'neutral' or nxt == m:
            cur, left = m, hold                  # a named tone switches; a lone weak cue does not
        out.append(cur)
    for r, m in zip(rows, out):
        r['mood'] = m
    return rows


def lean(p, mood):
    """The highlight colour a scene of this mood should use."""
    return getattr(p, MOODS.get(mood or 'neutral', MOODS['neutral'])['lean'])


def grade(img, mood, p=None, amount=1.0):
    """Whole-frame tone grade for a mood (RGB/RGBA PIL image in, same mode out)."""
    if not mood or mood == 'neutral' or mood not in MOODS:
        return img
    import numpy as np
    from PIL import Image
    p = p or ACTIVE
    sat, warm, con, lift, dark = MOODS[mood]['grade']
    sat, con = 1 + (sat - 1) * amount, 1 + (con - 1) * amount
    warm, lift, dark = warm * amount, lift * amount, dark * amount
    mode = img.mode
    a = np.asarray(img.convert('RGB'), np.float32)
    g = (a @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
    a = g + (a - g) * sat
    a = (a - 128.0) * con + 128.0
    a += np.array([1.0, 0.25, -1.0], np.float32) * warm * 40
    a = a * (1 - lift) + np.array(p.paper, np.float32) * lift
    a = a * (1 - dark) + np.array(p.dark, np.float32) * dark
    out = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGB')
    if mode == 'RGBA':
        out = out.convert('RGBA')
        out.putalpha(img.getchannel('A'))
    return out


# ------------------------------------------------------------------ choosing
def suggest(text, top=3):
    """[(palette, score)] ranked by how strongly the transcript's words point at each subject."""
    low = ' ' + text.lower() + ' '
    scores = []
    for p in PALETTES.values():
        s = sum(low.count(' ' + k) for k in p.keywords)
        scores.append((p.name, s))
    scores.sort(key=lambda x: -x[1])
    if scores[0][1] == 0:
        return [('editorial', 0)]
    return scores[:top]


def custom(base='editorial', **fields):
    """A video's own palette: start from the nearest subject palette and change fields, e.g.
    custom('manga_ink', accent=(196, 132, 40)) for a manga whose identity colour is gold.
    Raises if the result fails the contrast checks."""
    p = replace(PALETTES[base], name=fields.pop('name', base + '_custom'), land=None, coast=None, border=None, **fields)
    bad = validate(p)
    if bad:
        raise ValueError(f'palette fails contrast: {bad}')
    return p


def _load():
    cfg = os.path.join(os.environ.get('VOX_PROJECT', os.getcwd()), 'episode.json')
    data = json.load(open(cfg)) if os.path.exists(cfg) else {}
    pal = data.get('palette')
    if isinstance(pal, dict):                            # {"base": "manga_ink", "accent": [196,132,40]}
        base = pal.get('base', 'editorial')
        return custom(base, **{k: tuple(v) for k, v in pal.items() if k != 'base'})
    if pal:
        return PALETTES[pal]
    return PALETTES[THEME_PALETTE.get(data.get('theme', 'editorial'), 'editorial')]


ACTIVE = _load()


if __name__ == '__main__':
    for p in PALETTES.values():
        print(f'{p.name:16s}', 'ok' if not validate(p) else validate(p))
