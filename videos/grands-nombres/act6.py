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


import cutout


def drawing(code, width, label):
    """The user's engraving-style drawing (PROMPTS.md), printed on the film's paper; a labelled
    placeholder until the file is uploaded."""
    pth = asset(f'{code}.png')
    if os.path.exists(pth):
        return cutout.ink_image(pth, width)
    return P.print_card(N.image(code, (1600, 900), label), int(width * 0.8), seed=200)


BOARD_DUEL = drawing('G08', 1700, 'le tableau du duel (à générer)')


def tower(layer, cx, base_y, n, t, start, size=60, step=66):
    """The tower of 3s from act 5, floor by floor."""
    d = ImageDraw.Draw(layer)
    for i in range(n):
        k = P.ease_out(P.clamp01((t - start - 0.04 * i) / 0.3))
        if k <= 0:
            continue
        y = base_y - i * step
        x = cx + ((i * 53) % 21 - 10)
        d.text((x, y), '3', font=F_HEAD(size), fill=(PAL.accent if i % 7 == 0 else PAL.ink) + (int(255 * k),), anchor='mm')


def sA(t, D):
    """Mais le nombre de Graham a été dépassé."""
    s = Shot(t, D)
    S.env(s, 'paper')
    climb = P.ease_io(P.clamp01((t - ENTER) / max(D, 0.1)))
    tower(s.mid, W / 2, 1000 + 1400 * climb, 40, t, ENTER - 9.0)    # the floors slide down: we climb the tower of 3s of act 5
    kicker(s.hud, t, 6, 'Un, deux, trois, beaucoup', start=0.3)
    return s


def sB(t, D):
    """Le logicien Harvey Friedman a étudié une suite née de la théorie des graphes."""
    s = Shot(t, D)
    S.env(s, 'cream')
    TY.name_card(s.top, (180, 300), 'Harvey Friedman', 'LOGICIEN', t, ENTER + 0.1)
    at = w(cue(12, 'graphes')) - 1.2
    tree(s.mid, (1160, 880), 160, math.pi / 2, 5, t, at, PAL.ink, seed=1, per=0.10)
    tree(s.mid, (1560, 880), 130, math.pi / 2 + 0.15, 4, t, at + 0.35, PAL.accent, seed=2, per=0.10)
    return s


def sC(t, D):
    """TREE 1 vaut 1, TREE 2 vaut 3,"""
    s = Shot(t, D)
    S.env(s, 'grid')
    for (n, val, k, x) in ((1, '1', 1, 640), (2, '3', 2, 1280)):
        a = w(cue(12, 'TREE', k))
        TY.Text(f'TREE({n})', 'stat', size=110).draw(s.top, (x, 300), t, a, anim='scale', anchor='m', sound=False)
        words(s.top, (x, 520), f'= {val}', 120, t, w(cue(12, 'vaut', k)) + 0.15, fill=PAL.accent)
        tree(s.mid, (x, 900), 90, math.pi / 2, 1 + 2 * (n - 1), t, a + 0.2, PAL.ink, seed=10 + n, per=0.08)
    return s


TREE_COLOURS = None


def math_tree(d, x, y, size, seed, k=1.0):
    """A small rooted tree from graph theory: nodes in the three colours of TREE(3), joined by lines."""
    rng = np.random.default_rng(seed)
    cols = (PAL.ink, PAL.accent, (176, 132, 48))
    nodes = [(x, y)]
    edges = []
    for n in range(int(2 + rng.integers(1, 5))):
        px, py = nodes[int(rng.integers(0, len(nodes)))]
        nx_, ny_ = px + rng.uniform(-0.6, 0.6) * size, py - rng.uniform(0.5, 0.9) * size
        nodes.append((nx_, ny_))
        edges.append(((px, py), (nx_, ny_)))
    a = int(255 * k)
    for p0, p1 in edges:
        d.line((*p0, *p1), fill=PAL.ink + (a,), width=max(2, int(size / 12)))
    r = max(3, size / 7)
    for q, (nx_, ny_) in enumerate(nodes):
        c = cols[int(rng.integers(0, 3))]
        d.ellipse((nx_ - r, ny_ - r, nx_ + r, ny_ + r), fill=c + (a,))


def sC2(t, D):
    """et TREE 3 écrase le nombre de Graham."""
    s = Shot(t, D)
    S.env(s, 'cream')
    d = ImageDraw.Draw(s.mid)
    # trees of three colours appear in ever greater numbers while the camera pulls back
    grow = P.ease_io(P.clamp01((t - ENTER) / max(D, 0.1)))
    n = int(3 + 900 * grow ** 2.2)
    rng = np.random.default_rng(31)
    pos = [(W / 2, 640, 150), (W / 2 - 330, 620, 110), (W / 2 + 330, 660, 110)] + \
          [(rng.uniform(-900, W + 900), rng.uniform(-500, H + 400), rng.uniform(40, 80)) for _ in range(903)]
    for i in range(n):
        x, y, sz = pos[i]
        math_tree(d, x, y, sz, 100 + i, k=min(1.0, (n - i) / 30))
    s.zoom = 1.8 - 0.8 * grow
    s.lx, s.ly = W / 2, H / 2
    tag(s.hud, (W / 2, 975), 'TREE(3)', 64, t, w(cue(12, 'TREE', 3)) + 0.1, bg=PAL.accent, fg=CREAM)
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
    s.camera(1.0, 1.14, (W / 2, 520), (W / 2, 440))               # slowly into the board
    P.put(s.mid, BOARD_DUEL, W / 2, 540)
    tag(s.hud, (W / 2, 975), 'Le nombre de Rayo', 52, t, w(cue(12, 'propose')), bg=PAL.accent, fg=CREAM)
    caption(s.hud, 'Illustration', t, ENTER + 0.8, corner='bl')
    return s


DIGITS = '2464195387'
DIG_CUES = (('2', 1), ('4', 1), ('6', 1), ('4', 2), ('1', 1), ('9', 1), ('5', 1), ('3', 1), ('8', 1), ('7', 1))
STRIP_FONT = F_TYPE(64)
DW = STRIP_FONT.getlength('0')


def sF(t, D):
    """Les mathématiciens savent définir ces géants, prouver leurs propriétés, parfois calculer leurs
    derniers chiffres : le nombre de Graham se termine par 2, 4, 6, 4, 1, 9, 5, 3, 8, 7."""
    s = Shot(t, D)
    S.env(s, 'paper')
    # the endless strip of the googolplex returns, made of the digits of Graham's number; it runs
    # past until it reaches its end, where the last ten digits land one by one, as they are spoken
    rng = np.random.default_rng(7)
    body = ''.join(str(v) for v in rng.integers(0, 10, 120))
    reach = w(cue(13, 'calculer'))
    run = P.ease_io(P.clamp01((t - ENTER) / max(reach - ENTER + 1.2, 0.1)))
    end_x = W * 0.78                                              # where the strip's last digit sits once it has arrived
    shift = (1 - run) * 2600
    strip_w = int(STRIP_FONT.getlength(body + '…') + DW * 10 + 120)
    card = P.paper_card(strip_w, 120, seed=211, colour=PAL.light)
    cd = ImageDraw.Draw(card)
    cd.text((40, 60), body + '…', font=STRIP_FONT, fill=PAL.muted + (255,), anchor='lm')
    x0 = 40 + STRIP_FONT.getlength(body + '…') + 6
    for i, (ch, nth) in enumerate(DIG_CUES):
        if t >= w(cue(13, ch, nth)):
            cd.text((x0 + DW * i, 60), DIGITS[i], font=STRIP_FONT, fill=(PAL.accent if i == 9 else PAL.ink) + (255,), anchor='lm')
            sfx('tick', w(cue(13, ch, nth)), end_x)
    P.put(s.mid, card, end_x - strip_w / 2 + 70 + shift, 560)
    TY.Text('nombre de Graham', 'label', size=28).draw(s.hud, (end_x - DW * 10 + 10, 650), t, w(cue(13, 'Le nombre')), anchor='l', sound=False)
    return s


HEAD = cutout.ink_image(asset('G06.png'), 1400) if os.path.exists(asset('G06.png')) else None


def sH(t, D):
    """Aucun esprit, en revanche, ne peut se représenter leur taille."""
    s = Shot(t, D)
    S.env(s, 'cream', mood='calm')
    if HEAD is not None:                                         # locked off: the head of act 5, no push this time
        P.put(s.mid, HEAD, W / 2, 540)
    caption(s.hud, 'Illustration', t, ENTER + 0.6, corner='bl')
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
    S.env(s, 'grid')
    d = ImageDraw.Draw(s.mid)
    for k, ph in enumerate(('Un', 'deux', 'trois')):            # the dots of act 2, counted one by one
        a = P.ease_out(P.clamp01((t - w(cue(13, ph))) / 0.25))
        if a > 0:
            x = W / 2 - 160 + 160 * k
            r = 34 * a
            d.ellipse((x - r, 540 - r, x + r, 540 + r), fill=PAL.ink + (255,))
    at = w(cue(13, 'beaucoup'))                                  # then « beaucoup »: past counting, the dots fill the frame
    if t > at:
        rng = np.random.default_rng(99)
        n = int(min(1.0, (t - at) / 2.6) ** 1.6 * 2600)
        for i in range(n):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            if abs(y - 540) < 50 and abs(x - W / 2) < 210:
                continue
            r = rng.uniform(6, 16)
            d.ellipse((x - r, y - r, x + r, y + r), fill=(PAL.accent if i % 9 == 0 else PAL.ink) + (230,))
        sfx('assemble', at + 0.1, W / 2, n=8)
    return s


SHOTS = [
    (0.0, sA),
    (cue(12, 'Le logicien') - LEAD, sB, 'lr'),
    (cue(12, 'TREE') - LEAD, sC, 'up'),
    (cue(12, 'et TREE') - LEAD, sC2, ('zoom', {'at': (W / 2, 620)})),
    (cue(12, 'Le 26') - LEAD, sD, 'rl'),
    (cue(12, 'Rayo propose') - LEAD, sE, 'up'),
    (cue(13, 'Les mathematiciens') - LEAD, sF, 'pageturn'),
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
