"""Visual identity engine: every video gets an identity art-directed for its subject, and every
scene can shift tone without leaving it.

    episode.json  {"palette": "auto"}                      # default: analyse the topic (transcript + "subject")
                  {"palette": "manga_ink"}                 # a named identity (+ variant: "manga_ink/dark")
                  {"palette": {"base": "crime", "accent_primary": "#9B1C1C"}}   # a custom one
    import palette as PL
    PL.ACTIVE            # the colour tokens every module draws with (Palette)
    PL.IDENTITY          # the whole identity: palette + texture, image treatment, type, scene preferences, why
    PL.treat(img)        # an image treated in the identity's way (sepia duotone, cold, ink...)
    s.mood = 'grief'     # a scene's tone: a grade derived from the identity

The design tokens live in identities.py (one editable block per category, HEX per role). This
module analyses the topic (category scores, sub-genre variant, a second category to blend in,
region, historical period, emotional tone), builds the identity, repairs any contrast that
fails and explains every choice in IDENTITY.why. Unknown subjects fall back to 'editorial'.

Analyse a topic without a project:
    python palette.py "the history of Japan from the Meiji restoration"     # prints the identity
    python palette.py --check                                               # contrast of every identity
"""
import os, re, json, colorsys
from dataclasses import dataclass, field, replace
import identities as ID


def _mix(a, b, k):
    return tuple(int(round(a[i] + (b[i] - a[i]) * k)) for i in range(3))


def rgb(h):
    if isinstance(h, (tuple, list)):
        return tuple(int(v) for v in h[:3])
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexs(c):
    return '#%02X%02X%02X' % tuple(c[:3])


def _sat(c, k):
    """Scale saturation by k (k < 1 drains colour)."""
    h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in c))
    r, g, b = colorsys.hls_to_rgb(h, l, max(0.0, min(1.0, s * k)))
    return (int(r * 255 + 0.5), int(g * 255 + 0.5), int(b * 255 + 0.5))


# token role -> Palette field (the short names every module already uses)
FIELD = {'bg_primary': 'paper', 'bg_secondary': 'paper2', 'bg_minimal': 'cream', 'bg_dark': 'dark', 'bg_solid': 'solid',
         'text_primary': 'ink', 'text_secondary': 'ink2', 'text_muted': 'muted', 'text_on_dark': 'light',
         'accent_primary': 'accent', 'accent_secondary': 'accent2', 'accent_on_dark': 'accent_dark', 'highlight': 'highlight',
         'border': 'line', 'divider': 'divider', 'fill_soft': 'soft', 'texture_tint': 'tint'}


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
    highlight: tuple = None
    divider: tuple = None
    chart: tuple = ()
    land: tuple = None
    coast: tuple = None
    border: tuple = None
    keywords: tuple = field(default=(), compare=False)

    def __post_init__(self):
        d = {'highlight': self.accent2, 'divider': self.muted, 'chart': (self.accent, self.accent2, self.muted),
             'land': _mix(self.soft, self.paper, 0.25), 'coast': _mix(self.ink2, self.muted, 0.4), 'border': _mix(self.muted, self.soft, 0.4)}
        for k, v in d.items():
            if not getattr(self, k):
                object.__setattr__(self, k, v)

    def tokens(self):
        """{role: '#HEX'} in the identities.py vocabulary."""
        return {role: hexs(getattr(self, f)) for role, f in FIELD.items()}


@dataclass
class Identity:
    name: str                  # e.g. 'history_archive' or 'history_archive/world_war+japan'
    base: str
    label: str
    description: str
    palette: Palette
    texture: dict
    image: tuple
    type: dict
    signature: str
    bias: dict
    why: list
    variant: str = None


def _palette(name, label, cols, chart, keywords=()):
    kw = {FIELD[r]: rgb(v) for r, v in cols.items()}
    return Palette(name=name, subject=label, chart=tuple(rgb(c) for c in chart), keywords=tuple(keywords), **kw)


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


# (foreground, background, minimum, which side to move): body text 7, secondary 4.5, accents and
# large type 3; the highlight must keep body ink readable when swept behind it.
CHECKS = (('ink', 'paper', 7.0, 'fg'), ('ink', 'paper2', 7.0, 'fg'), ('ink', 'cream', 7.0, 'fg'), ('ink2', 'paper', 4.5, 'fg'),
          ('muted', 'paper', 3.0, 'fg'), ('light', 'dark', 7.0, 'fg'), ('accent', 'paper', 3.0, 'fg'), ('accent', 'cream', 3.0, 'fg'),
          ('accent2', 'paper', 3.0, 'fg'), ('accent_dark', 'dark', 3.0, 'fg'), ('light', 'solid', 4.5, 'bg'), ('light', 'accent', 3.0, 'fg2'),
          ('ink', 'highlight', 4.5, 'bg'))


def validate(p):
    """List of (fg, bg, ratio, minimum) pairs that fail. Empty = the palette reads everywhere."""
    out = []
    for fg, bg, lo, _ in CHECKS:
        c = contrast(getattr(p, fg), getattr(p, bg))
        if c < lo:
            out.append((fg, bg, round(c, 2), lo))
    return out


def repair(p):
    """Nudge the failing colours (never the grounds) until every check passes; returns (palette, notes)."""
    vals = {f: getattr(p, f) for f in FIELD.values()}
    notes = []
    for _ in range(3):
        for fg, bg, lo, side in CHECKS:
            if contrast(vals[fg], vals[bg]) >= lo:
                continue
            if side == 'fg2':                              # light text on an accent label: darken the accent
                move, target = bg, (0, 0, 0)
            else:
                move = bg if side == 'bg' else fg
                other = fg if side == 'bg' else bg
                target = (0, 0, 0) if luminance(vals[other]) > 0.3 else (255, 255, 255)
            before = vals[move]
            for _k in range(40):
                if contrast(vals[fg], vals[bg]) >= lo:
                    break
                vals[move] = _mix(vals[move], target, 0.06)
            notes.append(f'{move} {hexs(before)} -> {hexs(vals[move])} for {fg} on {bg} >= {lo}:1')
    return replace(p, **vals), notes


# ------------------------------------------------------------------ base identities
def _base(name):
    d = ID.IDENTITIES[name]
    return _palette(name, d['label'], d['colours'], d['chart'], d.get('keywords', ()))


PALETTES = {n: _base(n) for n in ID.IDENTITIES}
PALETTES['crime_investigation'] = PALETTES['crime']
THEME_PALETTE = ID.THEME_IDENTITY


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


# ------------------------------------------------------------------ analysis
def _count(low, words):
    n = 0
    for w in words:
        n += len(re.findall(r'(?<![a-z])' + re.escape(w) + r"(?:s|es|'s)?(?![a-z])", low))
    return n


PERIOD_FAMILIES = {'history_archive', 'culture', 'crime', 'economics', 'philosophy', 'editorial'}
REGION_ACCENT = {'history_archive', 'culture', 'editorial', 'philosophy'}


def analyse(text, subject=''):
    """What the topic is: {'scores', 'primary', 'secondary', 'variant', 'region', 'period', 'tone'}.
    The subject line (episode.json "subject", or a title) weighs five times the transcript."""
    low = ' ' + (text + (' ' + subject) * 5).lower() + ' '
    words = max(1, len(low.split()))
    scores = {n: _count(low, d.get('keywords', ())) for n, d in ID.IDENTITIES.items()}
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    primary = ranked[0][0] if ranked[0][1] >= 2 else 'editorial'
    secondary = None
    if ranked[0][1] >= 2 and ranked[1][1] >= max(3, 0.4 * ranked[0][1]):
        secondary = ranked[1][0]
    # "the history of X": X leads when it has a historical variant (history of computers -> retro technology)
    HIST_VARIANTS = {'technology': 'retro', 'crime': 'historical'}
    if primary == 'history_archive' and secondary in HIST_VARIANTS and scores[secondary] >= 0.5 * scores[primary]:
        primary, secondary = secondary, primary
    variant, vbest = None, 0
    for vn, v in ID.IDENTITIES[primary].get('variants', {}).items():
        k = _count(low, v['keywords'])
        if k > vbest and k >= 2:
            variant, vbest = vn, k
    region, rbest = None, 0
    for rn, r in ID.REGIONS.items():
        k = _count(low, r['keywords'])
        if k > rbest and k >= 2:
            region, rbest = rn, k
    if primary == 'manga_ink' and region == 'japan':
        region = None                                  # manga already speaks Japanese visual culture
    period, pbest = None, 0
    years = [int(y) for y in re.findall(r'(?<!\d)(1[0-9]{3}|20[0-9]{2})(?!\d)', low)]
    for pn, pd in ID.PERIODS.items():
        k = 2 * _count(low, pd['keywords'])
        y0, y1 = pd['years']
        k += sum(1 for y in years if y0 <= y < y1) // 3
        if k > pbest and k >= 2:
            period, pbest = pn, k
    dark = _count(low, MOOD_WORDS['grief'] + MOOD_WORDS['menace'] + MOOD_WORDS['mystery'])
    bright = _count(low, MOOD_WORDS['hope'] + MOOD_WORDS['triumph'] + MOOD_WORDS['wonder'])
    tone = 'dark' if dark > 1.4 * bright and dark * 1000 / words > 6 else ('bright' if bright > 1.6 * dark and bright * 1000 / words > 8 else 'balanced')
    return dict(scores=dict(ranked[:5]), primary=primary, secondary=secondary, variant=variant, region=region, period=period, tone=tone)


def derive(a, name=None):
    """Build the episode's Identity from an analysis (or from a forced base/variant)."""
    base = a['primary']
    d = ID.IDENTITIES[base]
    cols = dict(d['colours'])
    chart = list(d['chart'])
    texture, image, typ = dict(d['texture']), tuple(d['image']), dict(d['type'])
    bias = dict(d['scenes']['bias'])
    why = [f"{d['label']}: {d['description']}"]
    if a.get('scores'):
        why[0] += f" (topic words: {', '.join(f'{k} {v}' for k, v in a['scores'].items() if v)})"
    tag = base
    signature = d['scenes']['signature']
    v = d.get('variants', {}).get(a.get('variant'))
    if v:
        cols.update(v.get('colours', {}))
        chart = list(v.get('chart', chart))
        image = tuple(v.get('image', image))
        typ.update(v.get('type', {}))
        why.append(f"variant {a['variant']}: {v['note']}")
        tag += '/' + a['variant']
    sec = a.get('secondary')
    if sec and sec != base:
        s2 = ID.IDENTITIES[sec]
        cols['accent_secondary'] = s2['colours']['accent_primary']
        chart[1] = s2['chart'][0]
        why.append(f"second subject {s2['label']}: its accent becomes the supporting colour")
        if sec == 'history_archive':
            # "the history of X": X's identity, printed on the archive's paper
            for k in ('bg_primary', 'bg_secondary', 'bg_minimal'):
                cols[k] = hexs(_mix(rgb(cols[k]), rgb(s2['colours'][k]), 0.45))
            texture = dict(texture, kind='foxing', fibres=max(texture['fibres'], 700), vignette=max(texture['vignette'], 18))
            image = ('sepia', 0.35)
            signature = 'archive'
            bias['archive'] = max(bias.get('archive', 1.0), 1.6)
            why.append('a history of the subject: archive paper, foxing and sepia prints, opening on a document')
        tag += '+' + sec
    r = ID.REGIONS.get(a.get('region'))
    if r:
        cols['accent_secondary'] = r['accent_secondary']
        cols['highlight'] = r['highlight']
        if base in REGION_ACCENT:
            cols['accent_primary'] = r['accent']
            chart[0] = r['accent']
        chart[1] = r['accent_secondary']
        why.append(f"region {a['region']}: {r['note']}")
        tag += '+' + a['region']
    p = ID.PERIODS.get(a.get('period'))
    if p and base in PERIOD_FAMILIES:
        cols.update(p.get('colours', {}))
        if p.get('desaturate'):
            for k in ('accent_primary', 'accent_secondary', 'highlight', 'bg_solid', 'accent_on_dark'):
                cols[k] = hexs(_sat(rgb(cols[k]), 1 - p['desaturate']))
            chart = [hexs(_sat(rgb(c), 1 - p['desaturate'])) for c in chart]
        if 'image' in p:
            image = tuple(p['image'])
        if 'texture' in p:
            texture['mottle'] *= p['texture']
            texture['fibres'] = int(texture['fibres'] * p['texture'])
        why.append(f"period {a['period']}: {p['note']}")
        tag += '+' + a['period']
    tone = a.get('tone', 'balanced')
    if tone == 'dark':
        bias['charcoal'] = bias.get('charcoal', 1.0) * 1.35
        bias['bleed'] = bias.get('bleed', 1.0) * 1.15
        bias['cream'] = bias.get('cream', 1.0) * 0.8
        for k in ('accent_primary', 'highlight'):
            cols[k] = hexs(_sat(rgb(cols[k]), 0.9))
        why.append('tone dark: more dark compositions, slightly quieter accents')
    elif tone == 'bright':
        bias['charcoal'] = bias.get('charcoal', 1.0) * 0.75
        bias['cream'] = bias.get('cream', 1.0) * 1.2
        why.append('tone bright: lighter compositions lead')
    pal = _palette(name or tag, d['label'], cols, chart, d.get('keywords', ()))
    pal, notes = repair(pal)
    if notes:
        why.append('contrast repaired: ' + '; '.join(notes))
    return Identity(name=name or tag, base=base, label=d['label'], description=d['description'], palette=pal, texture=texture,
                    image=image, type=typ, signature=signature, bias=bias, why=why, variant=a.get('variant'))


def named(spec):
    """'manga_ink' or 'manga_ink/dark' -> Identity, with no topic analysis."""
    base, _, variant = spec.partition('/')
    base = 'crime' if base == 'crime_investigation' else base
    return derive(dict(primary=base, variant=variant or None, tone='balanced'), name=spec)


def suggest(text, top=3, subject=''):
    """[(identity, score)] ranked by how strongly the topic's words point at each category."""
    sc = analyse(text, subject)['scores']
    out = [(k, v) for k, v in sc.items() if v][:top]
    return out or [('editorial', 0)]


def custom(base='editorial', **fields):
    """A video's own palette: start from the nearest identity and change roles, e.g.
    custom('manga_ink', accent_primary='#C4842A'). Token role names or Palette field names both
    work, HEX or RGB. Raises if the result fails contrast (use repair() to auto-fix instead)."""
    name = fields.pop('name', base + '_custom')
    kw = {FIELD.get(k, k): rgb(v) for k, v in fields.items() if k not in ('chart',)}
    if 'chart' in fields:
        kw['chart'] = tuple(rgb(c) for c in fields['chart'])
    p = replace(PALETTES[base], name=name, land=None, coast=None, border=None, **kw)
    bad = validate(p)
    if bad:
        raise ValueError(f'palette fails contrast: {bad}')
    return p


# ------------------------------------------------------------------ image treatment
def treat(img, kind=None, strength=None, p=None):
    """Photograph / illustration treated in the identity's way. 'sepia' and 'cold' are duotones
    built from the identity's own dark and light grounds, so prints belong to the palette.
    kind: none | sepia | cold | cool | warm | ink. Keeps alpha."""
    import numpy as np
    from PIL import Image
    p = p or ACTIVE
    kind = kind or IDENTITY.image[0]
    k = IDENTITY.image[1] if strength is None else strength
    if kind == 'none' or k <= 0:
        return img
    mode = img.mode
    a = np.asarray(img.convert('RGB'), np.float32)
    g = (a @ np.array([0.299, 0.587, 0.114], np.float32))[..., None] / 255.0
    if kind in ('sepia', 'cold'):
        lo, hi = (np.array(p.dark, np.float32), np.array(p.paper, np.float32)) if kind == 'sepia' else \
                 (np.array(_mix(p.dark, p.accent2, 0.25), np.float32), np.array(p.cream, np.float32))
        lo = lo * 0.6
        b = lo + (hi - lo) * g
    elif kind == 'ink':
        c = np.clip((g - 0.5) * 1.25 + 0.5, 0, 1)
        b = np.repeat(c * 255.0, 3, axis=2)
    else:
        sh = np.array([-1.0, 0.1, 1.0] if kind == 'cool' else [1.0, 0.3, -1.0], np.float32) * 22
        b = g * 255.0 + (a - g * 255.0) * 0.8 + sh
    out = a * (1 - k) + b * k
    res = Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGB')
    if mode == 'RGBA':
        res = res.convert('RGBA')
        res.putalpha(img.getchannel('A'))
    return res


# ------------------------------------------------------------------ loading
def _project_text(proj):
    aud = os.path.join(proj, 'audio')
    if not os.path.isdir(aud):
        return ''
    return ' '.join(open(os.path.join(aud, f), encoding='utf-8').read() for f in sorted(os.listdir(aud)) if f.endswith('.txt'))


def _load():
    spec = os.environ.get('VOX_PALETTE')                 # override for previews and boards
    proj = os.environ.get('VOX_PROJECT', os.getcwd())
    cfg = os.path.join(proj, 'episode.json')
    data = json.load(open(cfg)) if os.path.exists(cfg) else {}
    if spec:
        data = dict(data, **json.loads(spec)) if spec.startswith('{') else dict(data, palette=spec)
    pal = data.get('palette', 'auto')
    if isinstance(pal, dict):                            # {"base": "manga_ink", "accent_primary": "#C4842A"}
        idn = named(pal.get('base', 'editorial'))
        over = {FIELD.get(k, k): rgb(v) for k, v in pal.items() if k not in ('base', 'chart')}
        if 'chart' in pal:
            over['chart'] = tuple(rgb(c) for c in pal['chart'])
        p, notes = repair(replace(idn.palette, name=idn.name + '_custom', land=None, coast=None, border=None, **over))
        idn.palette, idn.name = p, idn.name + '_custom'
        idn.why.append('custom roles: ' + ', '.join(k for k in pal if k != 'base') + (('; repaired: ' + '; '.join(notes)) if notes else ''))
        return idn
    if pal and pal != 'auto':
        return named(pal)
    text, subject = data.get('text') or _project_text(proj), data.get('subject', '')
    if text.strip() or subject.strip():
        return derive(analyse(text, subject))
    return named(THEME_PALETTE.get(data.get('theme', 'editorial'), 'editorial'))


IDENTITY = _load()
ACTIVE = IDENTITY.palette


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        for n in ID.IDENTITIES:
            print(f'{n:16s}', validate(PALETTES[n]) or 'ok')
    else:
        topic = ' '.join(sys.argv[1:]) or _project_text(os.environ.get('VOX_PROJECT', os.getcwd()))
        a = analyse('', topic) if len(sys.argv) > 1 else analyse(topic)
        idn = derive(a)
        print(json.dumps({k: v for k, v in a.items()}, indent=1))
        print('identity:', idn.name)
        for w in idn.why:
            print(' -', w)
        print(json.dumps(idn.palette.tokens(), indent=1))
