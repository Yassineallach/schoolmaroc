"""Acte 6 : Un, deux, trois, beaucoup. Narration clips 12-13, then the channel's end screen."""
import sys
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
import brand
from style import sfx, ENTER, Shot, words, tag, kicker, caption
import gn as N

CLIPS = (12, 13)
cue = make_cue(CLIPS)

MIT = N.image('R18', (1920, 1283), 'MIT')
RAYO = N.image('H06', (1280, 1715), 'Rayo')
MIT_CARD = P.print_card(S.treated(MIT), 760, seed=181)
RAYO_CARD = P.print_card(S.treated(RAYO), 300, seed=182)
BOARD, BPAD, BSQ = N.board_image(760)
GRAIN_BIG = N.grain_sprite(length=240, seed=4)

QUOTE = P.paper_card(760, 150, seed=61, colour=PAL.light)            # the same card as in act 2
ImageDraw.Draw(QUOTE).text((380, 75), '« un, deux, trois, beaucoup »', font=F_TYPE(46), fill=PAL.ink + (255,), anchor='mm')

import os
_FS = '/usr/share/fonts/truetype/freefont/FreeSerif.ttf'            # has the logic glyphs the film's faces lack
SYMBOLS = '∀∃¬∧∨→↔=∈⊂∅()xyz' if os.path.exists(_FS) else '=()xyz¬'
SYM_FONT = ImageFont.truetype(_FS, 56) if os.path.exists(_FS) else F_BODY(52)


def tree(layer, root, length, angle, depth, t, start, colour, seed=0, per=0.12):
    """A small graph-theory tree growing by pen, branch by branch."""
    rng = np.random.default_rng(seed)
    segs = []

    def grow(p, ln, ang, dep, at):
        if dep == 0:
            return
        q = (p[0] + ln * math.cos(ang), p[1] - ln * math.sin(ang))
        segs.append((p, q, at))
        n = 2 if dep > 1 else 0
        for k in range(n):
            grow(q, ln * 0.7, ang + (k - 0.5) * rng.uniform(0.6, 0.95), dep - 1, at + per)
    grow(root, length, angle, depth, start)
    d = ImageDraw.Draw(layer)
    for p, q, at in segs:
        f = A.pen((t - at) / per)
        if f <= 0:
            continue
        d.line((p[0], p[1], p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f), fill=colour + (255,), width=4)
        if f >= 1:
            d.ellipse((q[0] - 6, q[1] - 6, q[0] + 6, q[1] + 6), fill=colour + (255,))


def sA(t, D):
    """Mais le nombre de Graham a été dépassé."""
    s = Shot(t, D)
    S.env(s, 'theme')
    card = P.paper_card(520, 300, seed=191, colour=PAL.light)
    d = ImageDraw.Draw(card)
    for i in range(6):                                        # the tower of 3s, as act 5 left it
        d.text((260 + ((i * 37) % 9 - 4), 38 + 34 * i), '3', font=F_HEAD(30), fill=PAL.ink + (255,), anchor='mm')
    d.text((260, 270), 'nombre de Graham', font=F_BODY(30), fill=PAL.muted + (255,), anchor='mm')
    P.put(s.mid, card.rotate(-3, Image.BICUBIC, expand=True), W / 2, 520)
    kicker(s.hud, t, 6, 'Un, deux, trois, beaucoup', start=0.3)
    return s


def sB(t, D):
    """Le logicien Harvey Friedman a étudié une suite née de la théorie des graphes."""
    s = Shot(t, D)
    S.env(s, 'cream')
    TY.name_card(s.top, (180, 260), 'Harvey Friedman', 'LOGICIEN', t, ENTER + 0.1)
    at = w(cue(12, 'graphes')) - 0.9
    tree(s.mid, (1060, 860), 150, math.pi / 2, 4, t, at, PAL.ink, seed=1)
    tree(s.mid, (1420, 860), 120, math.pi / 2 + 0.2, 3, t, at + 0.3, PAL.accent, seed=2)
    tree(s.mid, (1700, 860), 100, math.pi / 2 - 0.15, 4, t, at + 0.55, PAL.ink, seed=3)
    return s


def sC(t, D):
    """TREE(1) vaut 1, TREE(2) vaut 3, et TREE(3) écrase le nombre de Graham."""
    s = Shot(t, D)
    S.env(s, 'grid')
    a1, a2, a3 = w(cue(12, 'TREE')), w(cue(12, 'TREE', 2)), w(cue(12, '3'))
    words(s.top, (520, 260), 'TREE(1) = 1', 64, t, a1)
    words(s.top, (520, 380), 'TREE(2) = 3', 64, t, a2)
    # the Graham card, crushed under TREE(3)
    crush = P.ease_io(P.clamp01((t - w(cue(12, 'ecrase'))) / 0.8))
    card = P.paper_card(380, 220, seed=192, colour=PAL.light)
    ImageDraw.Draw(card).text((190, 110), 'Graham', font=F_BODY(46), fill=PAL.muted + (255,), anchor='mm')
    sq = card.resize((380, max(6, int(220 * (1 - 0.88 * crush)))), Image.LANCZOS)
    P.put(s.mid, sq, 1360, 900 - sq.height / 2)
    TY.Text('TREE(3)', 'headline', size=200).draw(s.top, (1360, 420 + 200 * crush), t, a3, anim='scale', anchor='m')
    return s


def sD(t, D):
    """Le 26 janvier 2007, au MIT, les philosophes Agustín Rayo et Adam Elga s'affrontent en duel
    pour nommer le plus grand nombre."""
    s = Shot(t, D)
    S.env(s, 'geometric')
    P.drop(s.mid, MIT_CARD, 620, 420, t, ENTER, rot=-2, spin=8, key='mit')
    TY.big_number(s.top, (620, 700), '2007', t, w(cue(12, '26')), role='date', label='26 JANVIER · MIT')
    P.drop(s.mid, RAYO_CARD, 1300, 380, t, w(cue(12, 'Agustin')), rot=2.5, spin=9, key='rayo')
    TY.name_card(s.top, (1180, 600), 'Agustín Rayo', 'PHILOSOPHE', t, w(cue(12, 'Rayo')))
    TY.name_card(s.top, (1180, 800), 'Adam Elga', 'PHILOSOPHE', t, w(cue(12, 'Adam')))
    caption(s.hud, 'Great Dome, MIT ; Agustín Rayo, MIT, 2025', t, ENTER + 1.0, corner='tl')
    return s


def sE(t, D):
    """Rayo propose le plus petit nombre supérieur à tout nombre qu'on peut nommer avec un googol de
    symboles en théorie des ensembles."""
    s = Shot(t, D)
    S.env(s, 'cream')
    # a ribbon of logic symbols that never ends (the googolplex strip returns, made of symbols)
    pan = (t - ENTER) * 140
    f = SYM_FONT
    d = ImageDraw.Draw(s.mid)
    rib = P.paper_card(W + 200, 96, seed=193, colour=PAL.light)
    rd = ImageDraw.Draw(rib)
    x = 40 - (pan % 52)
    i = int(pan // 52)
    while x < W + 160:
        rd.text((x, 48), SYMBOLS[i % len(SYMBOLS)], font=f, fill=PAL.ink + (255,), anchor='lm')
        x += 52
        i += 1
    P.put(s.mid, rib, W / 2, 820)
    TY.term_card(s.top, (440, 330), 'LE NOMBRE DE RAYO', 'un googol de symboles', t, w(cue(12, 'propose')), width=1000)
    return s


def sF(t, D):
    """Les mathématiciens savent définir ces géants, prouver leurs propriétés, parfois calculer leurs
    derniers chiffres."""
    s = Shot(t, D)
    S.env(s, 'paper')
    card = P.paper_card(900, 520, seed=194, colour=PAL.light)
    d = ImageDraw.Draw(card)
    for yy in range(90, 520, 70):
        d.line((50, yy, 850, yy), fill=PAL.soft + (255,), width=2)
    P.put(s.mid, card.rotate(-1.5, Image.BICUBIC, expand=True), W / 2, 540)
    for i, ph in enumerate(('definir', 'prouver', 'calculer')):
        A.mark(s.mid, (W / 2 - 340, 410 + 110 * i), 'tick', t, w(cue(13, ph)), size=44)
        k = A.pen((t - w(cue(13, ph)) - 0.15) / 0.6)
        if k > 0:
            A.stroke(s.mid, [(W / 2 - 270, 412 + 110 * i), (W / 2 - 270 + 560 * (0.6 + 0.3 * (i % 2)), 412 + 110 * i)], k, 6, PAL.muted, 1.0)
    return s


DIGITS = '2464195387'


def sG(t, D):
    """Le nombre de Graham se termine par 2464195387."""
    s = Shot(t, D)
    S.env(s, 'cream')
    f = F_HEAD(130)
    at = w(cue(13, 'par')) + 0.2
    total = f.getlength('…' + DIGITS)
    x0 = W / 2 - total / 2
    d = ImageDraw.Draw(s.top)
    d.text((x0, 560), '…', font=f, fill=PAL.muted + (255,), anchor='ls')
    x = x0 + f.getlength('…')
    n = int(max(0, (t - at) / 0.33))
    for i, ch in enumerate(DIGITS[:n]):
        d.text((x, 560), ch, font=f, fill=(PAL.accent if i == len(DIGITS) - 1 else PAL.ink) + (255,), anchor='ls')
        x += f.getlength(ch)
    sfx('type', at, W / 2, n=10, cps=3)
    TY.Text('nombre de Graham', 'label', size=28).draw(s.top, (x0, 620), t, ENTER + 0.2, anchor='l', sound=False)
    return s


def sH(t, D):
    """Aucun esprit, en revanche, ne peut se représenter leur taille."""
    s = Shot(t, D)
    S.env(s, 'charcoal', mood='calm')
    k = P.ease_out(P.clamp01((t - ENTER) / 1.2))                # locked off: one grain, lit, in the dark
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r, a in ((260, 18), (180, 24), (110, 30)):
        gd.ellipse((W / 2 - r, 520 - r, W / 2 + r, 520 + r), fill=(230, 190, 120, int(a * k)))
    from PIL import ImageFilter
    s.mid.alpha_composite(glow.filter(ImageFilter.GaussianBlur(60)))
    P.put(s.mid, alpha_mul(GRAIN_BIG, k), W / 2, 520, shadow=False)
    return s


def sI(t, D):
    """Devant TREE(3), le savant le mieux armé retrouve la position que Gamow prêtait à tort aux
    Khoïkhoïs :"""
    s = Shot(t, D)
    S.env(s, 'paper')
    TY.Text('TREE(3)', 'headline', size=110, colour=PAL.muted).draw(s.top, (W / 2, 220), t, ENTER + 0.1, anim='words', anchor='m', sound=False)
    at = w(cue(13, 'Gamow')) - 0.3
    P.slide(s.mid, QUOTE, (W + 500, 560), (W / 2, 560), t, at, dur=1.1, rot=-3, key='callback')
    A.strike(s.mid, (W / 2 - 330, 535, W / 2 + 330, 590), t, at + 1.2, sound=False)    # struck again once it has landed, as in act 2
    return s


def sJ(t, D):
    """un, deux, trois, puis seulement, beaucoup."""
    s = Shot(t, D)
    S.env(s, 'theme')
    cx, cy = W / 2, 540
    P.put(s.mid, BOARD, cx, cy)
    for k, ph in ((1, 'Un'), (2, 'deux'), (3, 'trois')):
        x, y = N.square_centre(cx, cy, 760, k)
        N.scatter(s.mid, x, y, 1, 8, t, w(cue(13, ph)), seed=10 + k, dur=0.1)
    # « beaucoup »: grains pour onto the board and off the frame
    at = w(cue(13, 'beaucoup'))
    if t > at:
        rng = np.random.default_rng(99)
        n = int(min(1, (t - at) / 2.4) * 900)
        for i in range(n):
            ang = rng.uniform(0, 2 * math.pi)
            rad = 520 * math.sqrt(rng.uniform(0, 1)) * (0.35 + 0.65 * min(1, (t - at) / 2.4))
            gx, gy = cx + rad * math.cos(ang), cy + rad * math.sin(ang) * 0.9
            N.scatter(s.mid, gx, gy, 1, 0, t, at + i * 0.0026, seed=200 + i, dur=0.0, size=0.55)
        sfx('assemble', at + 0.1, cx, n=8)
    return s


SHOTS = [
    (0.0, sA),
    (cue(12, 'Le logicien') - LEAD, sB, 'lr'),
    (cue(12, 'TREE') - LEAD, sC, 'up'),
    (cue(12, 'Le 26') - LEAD, sD, 'rl'),
    (cue(12, 'Rayo propose') - LEAD, sE, 'up'),
    (cue(13, 'Les mathematiciens') - LEAD, sF, 'pageturn'),
    (cue(13, 'Le nombre') - LEAD, sG, 'lr'),
    (cue(13, 'Aucun') - LEAD, sH, 'rl'),
    (cue(13, 'Devant') - LEAD, sI, 'up'),
    (cue(13, 'Un,') - LEAD, sJ, 'lr'),
]
HOLD = 3.0                                                   # the last image holds before the end screen
if brand.CFG['outro']['enabled']:
    SHOTS.append((cue.total + HOLD, brand.outro_scene, 'up'))
END = cue.total + HOLD + brand.outro_seconds()


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
