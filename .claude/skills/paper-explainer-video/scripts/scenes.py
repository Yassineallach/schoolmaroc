"""Scene environments and compositions: every shot its own editorial page.

A shot chooses WHERE it happens (an environment = the ground under everything) and HOW its
elements are arranged (a composition helper). Nothing forces the episode background behind
every shot: `s.env = 'theme'` (the default) keeps it; any other environment replaces it.

    s = Shot(t, D)
    s.env = 'charcoal'                  # or env(s, 'charcoal', mood='grief')
    ink = scenes.ink(s)                 # text colour that reads on this ground

ENVIRONMENTS (render_env)                         use them for
    'theme'      the episode's animated background    the default: continuity between scenes
    'paper'      warm editorial paper, no shapes      calm explanation, documents
    'cream'      minimalist cream, one hairline rule  one idea, one quote, generous space
    'charcoal'   dark charcoal with grain, vignette   drama, death, turning points, night
    'accent'     solid ground in the palette colour   a single statement or number, sparingly
    'halftone'   manga halftone dots + speed lines    action, manga and comics subjects
    'archive'    aged newsprint + faint columns       history, dates, the press, records
    'geometric'  big flat shapes, one diagonal split  comparisons, systems, structure
    'grid'       clean graph grid                     infographics, charts, timelines
    'bleed'      no ground: a full-screen image       a photograph or illustration speaks alone

COMPOSITIONS (draw onto shot layers; all keep the paper / print language)
    fullbleed(s, img, t, start, ken=(1.0, 1.08), focus=, darken=)    image fills the frame
    split(s, left, right, t, start, ratio=0.5, divide='tear'|'line'|'shape')
    type_page(s, text, t, start, role='statement', ...)              full-screen typography
    panel_grid(s, items, t, starts, cols, gutter)                    manga-panel / contact-sheet grid
    letterbox(s, img, t, start, bars='charcoal')                     cinematic wide crop with bars
    rule_of_thirds(side) -> (x_image, x_text)                        asymmetric layout anchors

Brand constants hold in every environment: the same typefaces (typo.py), the episode palette
(palette.py: every ground, ink and accent above comes from it), paper grain on every ground,
prints with torn edges, pen-drawn marks. `accent(shot)` gives the highlight that reads on the
shot's ground; `env(s, name, mood='grief')` also sets the scene's tone (palette.MOODS).
'terra' is the old name of 'accent' (a solid ground in the palette's `solid` colour).
"""
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import vox
from vox import W, H

import palette
from palette import ACTIVE as PAL, _mix

# every ground is built from the episode palette (palette.py): a manga video gets off-white and
# ink, a space video pale blue paper and deep navy, a crime video cold newsprint and charcoal.
TERRA = ACCENT = PAL.accent
SOLID = PAL.solid
CHARCOAL = DARK = PAL.dark
CREAM = PAL.cream
PAPER = PAL.paper
INK_DARK = PAL.ink
INK_LIGHT = PAL.light

DARK_ENVS = {'charcoal', 'accent', 'terra', 'bleed'}
ENVS = ('theme', 'paper', 'cream', 'charcoal', 'accent', 'halftone', 'archive', 'geometric', 'grid', 'bleed')
ALIASES = {'terra': 'accent', 'dark': 'charcoal'}          # old names keep working


def ink(shot):
    """Text colour that reads on the shot's environment."""
    return INK_LIGHT if getattr(shot, 'env', 'theme') in DARK_ENVS else INK_DARK


def accent(shot):
    """The highlight colour for this shot: the palette accent (or the one the shot's mood leans
    on), switched to the dark-ground accent on dark environments so it keeps its contrast."""
    e = getattr(shot, 'env', 'theme')
    if e in ('charcoal', 'bleed'):
        return PAL.accent_dark
    if e == 'accent':
        return PAL.light
    c = palette.lean(PAL, getattr(shot, 'mood', None))
    return c if palette.contrast(c, PAL.paper) >= 3 else PAL.accent


def env(shot, name, mood=None, **opts):
    """Set the shot's environment (and optionally its mood, see palette.MOODS)."""
    name = ALIASES.get(name, name)
    assert name in ENVS, f'unknown environment {name!r}'
    shot.env, shot.env_opts = name, opts
    if mood is not None:
        assert mood in palette.MOODS, f'unknown mood {mood!r}'
        shot.mood = mood
    return shot


def _noise(h, w, scale, seed, amp):
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, (max(2, h // scale), max(2, w // scale))).astype(np.float32)
    n = np.asarray(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32)
    return (n - 128) / 128.0 * amp


def _ground(colour, seed, mottle=5.0, vignette=10.0, fibres=True):
    a = np.empty((H, W, 3), np.float32)
    a[:] = colour
    a += _noise(H, W, 70, seed, mottle)[..., None] + _noise(H, W, 5, seed + 1, mottle * 0.6)[..., None]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a -= (((xx / W - 0.5) ** 2 + (yy / H - 0.5) ** 2) * vignette)[..., None]
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    if fibres:
        d = ImageDraw.Draw(img)
        r = np.random.default_rng(seed + 2)
        base = np.array(colour, np.float32)
        for _ in range(900):
            x, y = r.uniform(0, W), r.uniform(0, H)
            L, ang = r.uniform(3, 9), r.uniform(0, math.pi)
            c = tuple(int(v) for v in (base * r.uniform(0.92, 1.04)).clip(0, 255))
            d.line([(x, y), (x + L * math.cos(ang), y + L * math.sin(ang))], fill=c)
    return img.filter(ImageFilter.GaussianBlur(0.5)).convert('RGBA')


@lru_cache(maxsize=16)
def _static(name):
    if name == 'paper':
        return _ground(PAPER, 201)
    if name == 'cream':
        g = _ground(CREAM, 202, mottle=3, vignette=6)
        ImageDraw.Draw(g).line((140, H - 150, W - 140, H - 150), fill=PAL.muted + (255,), width=2)
        return g
    if name == 'charcoal':
        return _ground(CHARCOAL, 203, mottle=6, vignette=-40)
    if name == 'accent':
        return _ground(SOLID, 204, mottle=7, vignette=16)
    if name == 'archive':
        g = _ground(PAL.paper2, 205, mottle=8, vignette=22)
        d = ImageDraw.Draw(g)
        r = np.random.default_rng(5)
        for c in range(5):                                         # faint newspaper columns
            x0 = 80 + c * 360
            for y in range(120, H - 80, 22):
                if r.random() < 0.85:
                    d.line((x0, y, x0 + 300 * r.uniform(0.7, 1.0), y), fill=PAL.line + (255,), width=3)
        g = g.filter(ImageFilter.GaussianBlur(1.0))
        st = Image.new('L', (W, H), 0)                             # soft foxing stains
        ds = ImageDraw.Draw(st)
        for _ in range(9):
            cx, cy, rr = r.uniform(0, W), r.uniform(0, H), r.uniform(50, 170)
            ds.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=int(r.uniform(25, 45)))
        st = st.filter(ImageFilter.GaussianBlur(45))
        tint = Image.new('RGBA', (W, H), PAL.tint + (0,))
        tint.putalpha(st)
        g.alpha_composite(tint)
        return g
    if name == 'grid':
        g = _ground(_mix(PAL.cream, (255, 255, 255), 0.2), 206, mottle=2, vignette=4)
        d = ImageDraw.Draw(g)
        for x in range(0, W, 48):
            d.line((x, 0, x, H), fill=_mix(PAL.line, PAL.cream, 0.5) + (255,), width=1)
        for y in range(0, H, 48):
            d.line((0, y, W, y), fill=_mix(PAL.line, PAL.cream, 0.5) + (255,), width=1)
        return g
    if name == 'geometric':
        g = _ground(PAPER, 207)
        d = ImageDraw.Draw(g)
        d.polygon([(0, 0), (int(W * 0.58), 0), (int(W * 0.42), H), (0, H)], fill=_mix(PAL.paper, PAL.soft, 0.45) + (255,))
        d.ellipse((W - 420, -260, W + 260, 420), fill=_mix(PAL.paper, PAL.soft, 0.75) + (255,))
        d.rectangle((W - 260, H - 90, W, H), fill=TERRA + (255,))
        return g
    if name == 'halftone':
        g = _ground(PAL.paper, 208, mottle=4)
        d = ImageDraw.Draw(g)
        for j, y in enumerate(range(0, H, 14)):                    # radial halftone from a corner
            for x in range((j % 2) * 7, W, 14):
                rr = 5.2 * max(0.0, 1 - math.hypot(x - W * 0.85, y - H * 0.2) / (W * 0.75))
                if rr > 0.6:
                    d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=PAL.tint + (255,))
        return g
    raise KeyError(name)


def render_env(name, T, shot):
    """The ground for a shot (RGBA, W x H). 'theme' returns None: the caller draws the episode
    background as before."""
    if name in (None, 'theme'):
        return None
    name = ALIASES.get(name, name)
    if name == 'bleed':
        return Image.new('RGBA', (W, H), CHARCOAL + (255,))
    g = _static(name)
    if name == 'halftone':                                         # speed lines surge in from the right
        g = g.copy()
        d = ImageDraw.Draw(g)
        k = 0.5 + 0.5 * math.sin(T * 2 * math.pi / 5.0)
        r = np.random.default_rng(9)
        for i in range(18):
            y = r.uniform(0, H)
            L = r.uniform(0.25, 0.6) * W * (0.8 + 0.2 * k)
            wd = r.uniform(2, 7)
            d.polygon([(W, y - wd), (W, y + wd), (W - L, y)], fill=INK_DARK + (int(170 + 60 * k),))
    return g


# ===================================================================== compositions
def _cover(img, w, h, focus=(0.5, 0.5)):
    """Scale and crop img to fill w x h, keeping the focus point in view."""
    im = img.convert('RGB')
    s = max(w / im.width, h / im.height)
    nw, nh = int(im.width * s + 1), int(im.height * s + 1)
    im = im.resize((nw, nh), Image.LANCZOS)
    x0 = int(min(max(focus[0] * nw - w / 2, 0), nw - w))
    y0 = int(min(max(focus[1] * nh - h / 2, 0), nh - h))
    return im.crop((x0, y0, x0 + w, y0 + h))


def fullbleed(shot, img, t, start=0.0, ken=(1.0, 1.08), focus=(0.5, 0.5), focus_to=None, darken=0.0, layer=None, fade=0.4):
    """The image fills the frame edge to edge (no paper, no border): a slow Ken Burns move from
    ken[0] to ken[1] towards focus_to; darken (0-0.6) adds a bottom-heavy shade so captions read.
    Set shot.env = 'bleed' (no ground) when using it."""
    if t < start:
        return
    L = layer or shot.mid
    u = min(1.0, max(0.0, (t - start) / max(0.1, shot.D)))
    k = 0.5 - 0.5 * math.cos(math.pi * u)
    z = ken[0] + (ken[1] - ken[0]) * k
    f1 = focus_to or focus
    fx, fy = focus[0] + (f1[0] - focus[0]) * k, focus[1] + (f1[1] - focus[1]) * k
    base = _cover(img, int(W * z) + 2, int(H * z) + 2, (fx, fy))
    x0, y0 = int((base.width - W) * fx), int((base.height - H) * fy)
    frame = base.crop((x0, y0, x0 + W, y0 + H)).convert('RGBA')
    if darken > 0:
        g = np.linspace(0, 1, H, dtype=np.float32) ** 1.6
        a = np.asarray(frame).astype(np.float32)
        a[..., :3] *= (1 - darken * g)[:, None, None]
        frame = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    op = min(1.0, (t - start) / fade)
    if op < 1:
        frame.putalpha(int(255 * op))
    L.alpha_composite(frame)


def split(shot, left, right, t, start=0.0, ratio=0.5, divide='tear', stagger=0.25, colour=None, layer=None, seed=4):
    """Two images side by side, each filling its half. divide: 'tear' (torn paper seam),
    'line' (a rule in the accent colour), 'shape' (a diagonal seam). Halves slide in from their sides."""
    import presets as P
    L = layer or shot.mid
    xm = int(W * ratio)
    for i, (img, x0, x1) in enumerate(((left, 0, xm), (right, xm, W))):
        st = start + i * stagger
        if img is None or t < st:
            continue
        u = P.damped((t - st) / 0.9, zeta=0.7, cycles=1.0)
        half = _cover(img, x1 - x0, H).convert('RGBA')
        if divide == 'shape':
            m = Image.new('L', half.size, 255)
            off = 90
            if i == 0:
                ImageDraw.Draw(m).polygon([(half.width - off, 0), (half.width, 0), (half.width, H)], fill=0)
            else:
                ImageDraw.Draw(m).polygon([(0, 0), (off, H), (0, H)], fill=0)
            half.putalpha(m)
        dx = (-1 if i == 0 else 1) * (1 - u) * (x1 - x0) * 0.6
        P.comp(L, half, x0 + dx, 0)
    if t > start + 0.5:
        d = ImageDraw.Draw(L)
        if divide == 'line':
            d.rectangle((xm - 4, 0, xm + 4, H), fill=(colour or TERRA) + (255,))
        elif divide == 'tear':
            r = np.random.default_rng(seed)
            pts = [(xm + r.normal(0, 5), y) for y in range(-10, H + 20, 18)]
            d.line(pts, fill=(250, 245, 232, 255), width=12)
            d.line([(x + 5, y) for x, y in pts], fill=(40, 26, 14, 70), width=4)


def type_page(shot, text, t, start, role='statement', size=None, anchor='m', xy=None, max_w=1500, colour=None, anim='words', cues=None,
              accent=None, until=None, layer=None, accent_colour=None):
    """Full-screen typography: one line or sentence owns the frame. Colour follows the
    environment (cream on dark grounds) unless given."""
    import typo as TY
    T = TY.Text(text, role, size=size, max_w=max_w, align='m' if anchor == 'm' else ('r' if anchor == 'r' else 'l'), colour=colour or ink(shot))
    if xy is None:
        xy = (W / 2, H / 2 - T.h / 2)
    T.draw(layer or shot.top, xy, t, start, anim=anim, anchor=anchor, cues=cues, accent=accent, accent_colour=accent_colour or globals()['accent'](shot), until=until)
    return T


def panel_grid(shot, items, t, starts, cols=3, gutter=18, box=(120, 110, 1800, 970), border=6, layer=None, seed=11):
    """A manga page / contact sheet: images in panels with ink borders; each panel drops in on
    its cue. Panels widths vary slightly per row so it never looks like a spreadsheet."""
    import presets as P
    L = layer or shot.mid
    x0, y0, x1, y1 = box
    rows = math.ceil(len(items) / cols)
    ph = (y1 - y0 - gutter * (rows - 1)) / rows
    r = np.random.default_rng(seed)
    k = 0
    for row in range(rows):
        n = min(cols, len(items) - k)
        ws = r.uniform(0.8, 1.2, n)
        ws = ws / ws.sum() * (x1 - x0 - gutter * (n - 1))
        x = x0
        for c in range(n):
            img, st = items[k], starts[k]
            pw = ws[c]
            y = y0 + row * (ph + gutter)
            if t >= st:
                cell = _cover(img, int(pw), int(ph)).convert('RGBA')
                ImageDraw.Draw(cell).rectangle((0, 0, cell.width - 1, cell.height - 1), outline=INK_DARK + (255,), width=border)
                u = P.damped((t - st) / 0.6, zeta=0.6, cycles=1.0)
                sc = 1.06 - 0.06 * u
                item = cell.resize((int(cell.width * sc), int(cell.height * sc)), Image.BICUBIC)
                P.put(L, P.fade_img(item, min(1.0, (t - st) / 0.2)), x + pw / 2, y + ph / 2, lift=0.25 * (1 - u))
            x += pw + gutter
            k += 1


def letterbox(shot, img, t, start=0.0, bars='charcoal', bar_h=135, ken=(1.0, 1.06), focus=(0.5, 0.5)):
    """Cinematic wide crop: the image between two bars that close in, for a dramatic beat."""
    fullbleed(shot, img, t, start, ken=ken, focus=focus)
    u = min(1.0, max(0.0, (t - start) / 0.6))
    h = int(bar_h * (1 - (1 - u) ** 3))
    col = CHARCOAL if bars == 'charcoal' else CREAM
    d = ImageDraw.Draw(shot.hud)
    d.rectangle((0, 0, W, h), fill=col + (255,))
    d.rectangle((0, H - h, W, H), fill=col + (255,))


def rule_of_thirds(side='left'):
    """(x of the image centre, x where text starts) for an asymmetric layout."""
    return (W * 0.68, W * 0.08) if side == 'left' else (W * 0.32, W * 0.56)


# ===================================================================== planning
PURPOSE_ENVS = {
    'emotion':    ['charcoal', 'cream', 'bleed'],
    'date':       ['archive', 'cream', 'accent'],
    'number':     ['grid', 'accent', 'cream'],
    'fraction':   ['grid', 'geometric'],
    'place':      ['theme', 'archive'],
    'journey':    ['theme', 'grid'],
    'person':     ['bleed', 'paper', 'theme'],
    'people':     ['halftone', 'archive', 'theme'],
    'quote':      ['cream', 'charcoal'],
    'comparison': ['geometric', 'grid'],
    'comparison_text': ['geometric', 'paper'],
    'process':    ['grid', 'paper'],
    'list':       ['halftone', 'paper'],
    'correction': ['cream', 'paper'],
    'document':   ['archive', 'paper'],
    'reveal':     ['charcoal', 'bleed', 'theme'],
    'detail':     ['bleed', 'theme'],
    'action':     ['halftone', 'bleed'],
    'idea':       ['theme', 'cream', 'paper'],
}

LAYOUT_FOR_ENV = {'bleed': 'fullbleed or letterbox', 'charcoal': 'type_page or a single lit print', 'cream': 'type_page / one print, lots of space',
                  'accent': 'type_page or big_number only', 'halftone': 'panel_grid or cut-out action', 'archive': 'clippings, documents, stack',
                  'geometric': 'split / two sides', 'grid': 'charts / timeline / flow', 'paper': 'documents and prints', 'theme': 'collage on the episode background'}


# environments a mood prefers (palette.plan_moods sets r['mood']): they move up the purpose list
MOOD_ENVS = {'grief': ['charcoal', 'cream', 'bleed'], 'menace': ['charcoal', 'bleed', 'halftone'], 'mystery': ['charcoal', 'archive'],
             'triumph': ['accent', 'grid'], 'wonder': ['bleed', 'theme'], 'tense': ['geometric', 'halftone'], 'calm': ['cream', 'paper'],
             'hope': ['cream', 'theme']}


# share of shots each environment may take at most (variety without losing cohesion)
CAPS = {'theme': 0.40, 'bleed': 0.14, 'paper': 0.14, 'cream': 0.12, 'charcoal': 0.08, 'accent': 0.04,
        'halftone': 0.12, 'archive': 0.12, 'geometric': 0.10, 'grid': 0.10}


def plan_environments(rows):
    """Give every planned shot an environment from its purpose: never the same environment as
    either of the two previous shots, each environment within its share (CAPS), the episode
    theme as the most common ground for continuity, dark or solid grounds only for short,
    strong moments (simple/medium weight)."""
    used = {e: 0 for e in ENVS}
    hist = []
    n = max(1, len(rows))
    for i, r in enumerate(rows):
        opts = list(PURPOSE_ENVS.get(r['purpose'], ['theme', 'paper']))
        opts = [e for e in MOOD_ENVS.get(r.get('mood'), []) if e in opts] + [e for e in opts if e not in MOOD_ENVS.get(r.get('mood'), [])]
        opts += [e for e in MOOD_ENVS.get(r.get('mood'), []) if e not in opts] + ['theme', 'paper', 'cream', 'geometric']
        best = None
        for rank, o in enumerate(opts):
            if o in hist[-2:]:
                continue
            if o in ('accent', 'charcoal') and r['weight'] == 'complex':
                continue
            over = used[o] / (CAPS[o] * n)
            score = rank * 0.6 + over * 3
            if best is None or score < best[0]:
                best = (score, o)
        pick = best[1] if best else 'paper'
        r['env'] = pick
        r['layout'] = LAYOUT_FOR_ENV[pick]
        used[pick] += 1
        hist.append(pick)
    return rows
