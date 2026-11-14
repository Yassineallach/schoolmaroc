"""Acte 5 : Empiler les opérations. Narration clips 10-11."""
import sys
import math
import numpy as np
from PIL import Image, ImageDraw
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
import timeline as TL
from style import sfx, ENTER, Shot, words, tag, kicker, caption
import gn as N

CLIPS = (10, 11)
cue = make_cue(CLIPS)

KNUTH = N.image('H03', (797, 1197), 'Knuth')
GRAHAM = N.image('H04', (779, 1195), 'Graham')
KNUTH_CARD = P.print_card(S.treated(KNUTH), 360, seed=131)
GRAHAM_CARD = P.print_card(S.treated(GRAHAM), 300, seed=132)
GOLD = (176, 132, 48)                 # gold leaf, dark enough to read on cream


def arrow_up(layer, x, y, h, t, start, colour, width=9, dur=0.35):
    """An up-arrow drawn by pen (Knuth's notation), no glyph needed."""
    p = A.pen((t - start) / dur)
    if p <= 0:
        return
    A.stroke(layer, [(x, y), (x, y - h)], p, width, colour, 1.0)
    if p > 0.7:
        q = (p - 0.7) / 0.3
        A.stroke(layer, [(x - h * 0.28, y - h * 0.7), (x, y - h), (x + h * 0.28, y - h * 0.7)], q, width, colour, 1.0)


def sA(t, D):
    """Pour aller plus loin, les mathématiciens ont empilé les opérations elles-mêmes."""
    s = Shot(t, D)
    S.env(s, 'theme')
    for i, sym in enumerate(('+', '×', '^')):
        card = P.paper_card(260, 200, seed=140 + i, colour=PAL.light)
        ImageDraw.Draw(card).text((130, 100), sym, font=F_HEAD(130), fill=(PAL.accent if i == 2 else PAL.ink) + (255,), anchor='mm')
        at = ENTER if i == 0 else w(cue(10, 'empile')) + (0, 0.0, 0.3)[i]
        P.drop(s.mid, card, 960 + (-14, 10, -4)[i], 760 - 170 * i, t, at, rot=(-4, 2, -1.5)[i], spin=8, key=f'op{i}')
    kicker(s.hud, t, 5, 'Empiler les opérations', start=0.3)
    return s


def sB(t, D):
    """La multiplication répète l'addition, la puissance répète la multiplication."""
    s = Shot(t, D)
    S.env(s, 'grid')
    a1, a2 = w(cue(10, 'multiplication')), w(cue(10, 'puissance'))
    TY.Text('3 + 3 + 3', 'stat', size=110).draw(s.top, (560, 320), t, ENTER, anim='words', anchor='m', sound=False)
    TY.Text('3 × 3', 'stat', size=110, colour=PAL.accent).draw(s.top, (1360, 320), t, a1, anim='scale', anchor='m')
    A.connect(s.mid, [(860, 380), (1140, 380)], t, a1 - 0.2, dur=0.5, arrowhead=True, dots=False)
    TY.Text('3 × 3 × 3', 'stat', size=110).draw(s.top, (560, 660), t, a2 - 0.3, anim='words', anchor='m', sound=False)
    N.power(s.top, (1360, 610), '3', '3', 130, t, a2 + 0.4, anchor='m')
    A.connect(s.mid, [(860, 720), (1140, 720)], t, a2 + 0.2, dur=0.5, arrowhead=True, dots=False)
    return s


def sC(t, D):
    """En 1947, le logicien Reuben Goodstein nomme les étapes suivantes tétration, pentation et
    hexation."""
    s = Shot(t, D)
    S.env(s, 'cream')
    TY.name_card(s.top, (180, 260), 'Reuben Goodstein', 'LOGICIEN · 1947', t, ENTER + 0.1)
    for i, (word_, ph) in enumerate((('tétration', 'tetration'), ('pentation', 'pentation'), ('hexation', 'hexation'))):
        card = P.paper_card(520, 130, seed=150 + i, colour=PAL.light)
        ImageDraw.Draw(card).text((260, 65), word_, font=F_BODY(62), fill=PAL.ink + (255,), anchor='mm')
        P.drop(s.mid, card, 1240 + (-10, 16, -4)[i], 380 + 170 * i, t, w(cue(10, ph)) - 0.1, rot=(-2.5, 2, -1)[i], spin=8, key=f'term{i}')
    return s


def sD(t, D):
    """En 1976, l'informaticien Donald Knuth les écrit avec des flèches."""
    s = Shot(t, D)
    S.env(s, 'paper')
    P.drop(s.mid, KNUTH_CARD, 460, 520, t, ENTER, rot=-2.5, spin=8, key='knuth')
    TY.name_card(s.top, (820, 300), 'Donald Knuth', 'INFORMATICIEN · 1976', t, w(cue(10, 'Donald')))
    at = w(cue(10, 'fleches'))
    arrow_up(s.mid, 940, 760, 150, t, at, PAL.accent)
    arrow_up(s.mid, 1010, 760, 150, t, at + 0.25, PAL.accent)
    caption(s.hud, 'Donald Knuth, Computer History Museum', t, ENTER + 1.0)
    return s


GROUPS = (('7 625', 'sept'), ('597', 'cinq', 2), ('484', 'quatre', 2), ('987', 'neuf'))


def sE(t, D):
    """Trois, deux flèches, trois, une tour de trois 3, vaut déjà 7 625 597 484 987."""
    s = Shot(t, D)
    S.env(s, 'geometric')
    P.drop(s.mid, P.paper_card(620, 240, seed=171, colour=PAL.light), 710, 300, t, ENTER, rot=-1.5, spin=5, key='kn')
    f = F_HEAD(150)
    d = ImageDraw.Draw(s.top)
    # 3 ↑↑ 3, each part on its word
    if t >= ENTER:
        d.text((560, 300), '3', font=f, fill=PAL.ink + (255,), anchor='mm')
    arrow_up(s.top, 680, 360, 120, t, w(cue(10, 'deux', 1)), PAL.accent)
    arrow_up(s.top, 740, 360, 120, t, w(cue(10, 'deux', 1)) + 0.2, PAL.accent)
    if t >= w(cue(10, 'trois', 2)):
        d.text((860, 300), '3', font=f, fill=PAL.ink + (255,), anchor='mm')
    # the tower of three 3s
    at = w(cue(10, 'tour'))
    for i in range(3):
        k = P.ease_out(P.clamp01((t - at - 0.2 * i) / 0.3))
        if k > 0:
            size = int(120 * (0.62 ** i))
            ft = F_HEAD(size)
            x = 1300 + sum(int(120 * (0.62 ** j)) * 0.62 for j in range(i))
            y = 370 - sum(int(120 * (0.62 ** j)) * 0.45 for j in range(i))
            d.text((x, y), '3', font=ft, fill=(PAL.ink if i == 0 else PAL.accent) + (int(255 * k),), anchor='ls')
    # the value, group by group as it is spoken
    fv = F_HEAD(110)
    x = W / 2 - fv.getlength('7 625 597 484 987') / 2
    for g in GROUPS:
        txt, ph = g[0], g[1]
        nth = g[2] if len(g) > 2 else 1
        a = w(cue(10, ph, nth))
        k = P.ease_out(P.clamp01((t - a) / 0.3))
        if k > 0:
            d.text((x, 820 + (1 - k) * 30), txt, font=fv, fill=PAL.ink + (int(255 * k),), anchor='ls')
        x += fv.getlength(txt + ' ')
    return s


def sF(t, D):
    """Avec trois flèches, la tour compte autant d'étages."""
    s = Shot(t, D)
    S.env(s, 'paper')
    start = ENTER
    pan = P.ease_io(P.clamp01((t - w(cue(10, 'tour', 2))) / 2.2))
    d = ImageDraw.Draw(s.mid)
    for i in range(60):                                     # floors of 3s, rising out of the frame
        y = 900 - i * 72 + pan * 2600
        if y < -100 or y > H + 100:
            continue
        k = P.ease_out(P.clamp01((t - start - 0.05 * i) / 0.3))
        if k <= 0:
            continue
        x = W / 2 + ((i * 53) % 21 - 10)
        d.text((x, y), '3', font=F_HEAD(64), fill=(PAL.accent if i % 7 == 0 else PAL.ink) + (int(255 * k),), anchor='mm')
    return s


def sG(t, D):
    """Ces flèches ont servi un vrai problème. La théorie de Ramsey montre que, dans un ensemble assez
    grand, le désordre complet est impossible."""
    s = Shot(t, D)
    S.env(s, 'cream')
    card = P.paper_card(1100, 330, seed=161, colour=PAL.light)
    P.drop(s.mid, card, W / 2, 520, t, ENTER, rot=-1, spin=5, key='ramsey')
    TY.term_card(s.top, (500, 420), 'THÉORIE DE RAMSEY', 'le désordre complet est impossible', t, w(cue(11, 'Ramsey')), width=920)
    return s


SIX = [(W / 2 + 300 * math.cos(math.radians(-90 + 60 * i)), 540 + 300 * math.sin(math.radians(-90 + 60 * i))) for i in range(6)]
# a colouring of the 15 links: lapis = know each other, gold = do not; triangle 0-2-4 all lapis, 1-3-5 all gold
KNOW = {(0, 2), (2, 4), (0, 4), (0, 1), (2, 3), (4, 5)}


def sH(t, D):
    """Parmi six personnes, il y en a toujours trois qui se connaissent toutes, ou trois qui ne se
    connaissent pas du tout."""
    s = Shot(t, D)
    S.env(s, 'grid')
    d = ImageDraw.Draw(s.mid)
    pairs = [(i, j) for i in range(6) for j in range(i + 1, 6)]
    a0 = w(cue(11, 'personnes'))
    for n, (i, j) in enumerate(pairs):
        at = a0 + 0.07 * n
        k = P.clamp01((t - at) / 0.25)
        if k <= 0:
            continue
        know = (i, j) in KNOW
        col = PAL.accent if know else GOLD
        x0, y0 = SIX[i]
        x1, y1 = SIX[j]
        d.line((x0, y0, x0 + (x1 - x0) * k, y0 + (y1 - y0) * k), fill=col + (150,), width=4)
    for tri, ph, col in (((0, 2, 4), 'toutes', PAL.accent), ((1, 3, 5), 'tout', GOLD)):
        at = w(cue(11, ph))
        k = P.ease_out(P.clamp01((t - at) / 0.4))
        if k > 0:
            pts = [SIX[v] for v in tri]
            d.polygon(pts, fill=col + (int(70 * k),))
            d.line(pts + [pts[0]], fill=col + (255,), width=int(4 + 5 * k))
    for i, (x, y) in enumerate(SIX):
        k = P.ease_out(P.clamp01((t - ENTER - 0.06 * i) / 0.3))
        if k > 0:
            r = 30 * k
            d.ellipse((x - r, y - r, x + r, y + r), fill=PAL.ink + (255,))
    return s


def _hypercube(t, cx, cy, size):
    pts = np.array([[(i >> b) & 1 for b in range(4)] for i in range(16)], np.float32) * 2 - 1
    a, b = t * 0.6, t * 0.35
    xw = np.array([[math.cos(a), 0, 0, -math.sin(a)], [0, 1, 0, 0], [0, 0, 1, 0], [math.sin(a), 0, 0, math.cos(a)]])
    yz = np.array([[1, 0, 0, 0], [0, math.cos(b), -math.sin(b), 0], [0, math.sin(b), math.cos(b), 0], [0, 0, 0, 1]])
    p = pts @ xw.T @ yz.T
    w4 = 1 / (2.6 - p[:, 3])
    p3 = p[:, :3] * w4[:, None]
    z = 1 / (3.2 - p3[:, 2])
    xy = p3[:, :2] * z[:, None] * size + np.array([cx, cy])
    edges = [(i, j) for i in range(16) for j in range(i + 1, 16) if bin(i ^ j).count('1') == 1]
    return xy, edges


def sI(t, D):
    """Ronald Graham a étudié une question de ce type sur des cubes à plusieurs dimensions."""
    s = Shot(t, D)
    S.env(s, 'cream')
    xy, edges = _hypercube(t + 3.0, 1360, 500, 1050)
    d = ImageDraw.Draw(s.mid)
    k = P.ease_out(P.clamp01((t - w(cue(11, 'cubes')) + 0.6) / 0.8))
    if k > 0:
        for i, j in edges:
            d.line((*xy[i], *xy[j]), fill=GOLD + (int(220 * k),), width=3)
        for x, y in xy:
            d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=GOLD + (int(255 * k),))
    P.drop(s.mid, GRAHAM_CARD, 420, 400, t, ENTER, rot=-2, spin=8, key='graham')
    TY.name_card(s.top, (180, 700), 'Ronald Graham', 'MATHÉMATICIEN', t, w(cue(11, 'Ronald')), accent=GOLD)
    caption(s.hud, 'Ronald Graham, photographie de Cheryl Graham', t, ENTER + 1.0)
    return s


def sJ(t, D):
    """Et la borne qu'il a décrite, publiée par Martin Gardner en 1977, est entrée en 1980 dans le
    Livre Guinness des records comme le plus grand nombre utilisé dans une démonstration."""
    s = Shot(t, D)
    S.env(s, 'archive')
    tl = TL.Timeline(1970, 1990, box=(220, 600, 1700, 640), step=5)
    tl.axis(s.mid, t, ENTER)
    tl.event(s.mid, 1977, 'Martin Gardner', t, w(cue(11, 'Gardner')), side='up')
    tl.event(s.mid, 1980, 'Guinness des records', t, w(cue(11, '1980')), side='down')
    P.stamp_hit(s.mid, 'RECORD', 1440, 260, t, w(cue(11, 'records')), size=96, ang=-7, shot=s)
    return s


def _head(scale=1.0):
    """A head in profile, drawn as an ink line (an illustration, captioned as such)."""
    pts = [(0.30, 0.95), (0.30, 0.78), (0.20, 0.70), (0.16, 0.60), (0.10, 0.56), (0.15, 0.50), (0.12, 0.44), (0.16, 0.40),
           (0.15, 0.30), (0.22, 0.16), (0.38, 0.06), (0.56, 0.05), (0.72, 0.12), (0.82, 0.26), (0.84, 0.42), (0.78, 0.58),
           (0.70, 0.68), (0.66, 0.80), (0.68, 0.95)]
    return [(x * 520 * scale, y * 620 * scale) for x, y in pts]


import os
import cutout
# the head that would collapse into a black hole: the user's engraving-style drawing G06
# (PROMPTS.md), a labelled placeholder until it is uploaded
HEAD = (cutout.ink_image(asset('G06.png'), 1500) if os.path.exists(asset('G06.png'))
        else P.print_card(N.image('G06', (1600, 900), 'la tête et le trou noir (à générer)'), 1300, seed=171))


def sK(t, D):
    """Une image répandue par la chaîne Numberphile affirme qu'une tête qui en retiendrait tous les
    chiffres s'effondrerait en trou noir,"""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.0)
    hw, hh = HEAD.size
    sphere = (W / 2 - hw / 2 + 0.478 * hw, 540 - hh / 2 + 0.372 * hh)          # the black sphere in G06
    s.push(w(cue(11, "'effondreraient")) - 0.3, 0.6, sphere, dur=1.6)   # into the sphere as it is spoken
    P.put(s.mid, HEAD, W / 2, 540)
    caption(s.hud, 'Illustration', t, ENTER + 0.6, corner='bl')
    return s


def sL(t, D):
    """une simplification que le site IFLScience juge fausse."""
    s = Shot(t, D)
    S.env(s, 'cream')
    small = HEAD.resize((HEAD.width * 2 // 3, HEAD.height * 2 // 3), Image.LANCZOS)
    P.put(s.mid, small, 700, 520)
    sx, sy = 700 - small.width / 2 + 0.478 * small.width, 520 - small.height / 2 + 0.372 * small.height
    A.strike(s.mid, (sx - 190, sy - 25, sx + 190, sy + 25), t, w(cue(11, 'fausse')) - 0.2, scribble=True)
    TY.Text('simplification', 'caption', size=50).draw(s.top, (1260, 760), t, w(cue(11, 'simplification')), anim='type', anchor='l')
    return s


SHOTS = [
    (0.0, sA),
    (cue(10, 'La multiplication') - LEAD, sB, 'lr'),
    (cue(10, 'En', 1) - LEAD, sC, 'up'),
    (cue(10, 'En', 2) - LEAD, sD, 'rl'),
    (cue(10, 'Trois') - LEAD, sE, 'shape'),
    (cue(10, 'Avec trois') - LEAD, sF, 'up'),
    (cue(11, 'Ces') - LEAD, sG, 'lr'),
    (cue(11, 'Parmi') - LEAD, sH, 'rl'),
    (cue(11, 'Ronald') - LEAD, sI, 'up'),
    (cue(11, 'Et la') - LEAD, sJ, 'pageturn'),
    (cue(11, 'Une image') - LEAD, sK, 'lr'),
    (cue(11, 'Une simplification') - LEAD, sL, 'rl'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
