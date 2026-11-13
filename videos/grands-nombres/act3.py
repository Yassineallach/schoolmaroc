"""Acte 3 : Compter le sable. Narration clips 6-7."""
import sys
import math
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
from gn import power

CLIPS = (6, 7)
cue = make_cue(CLIPS)

# ---- real images (Wikimedia Commons, credits in assets/credits.json) ----
FETTI = N.image('R08', (1500, 2000), 'Archimède')
SAND = N.image('R09', (1920, 1427), 'sable')
ARISTARCHUS = N.image('R10', (1920, 1401), 'Aristarque')
KASNER = N.image('H02', (782, 977), 'Kasner')
HUBBLE = N.image('R11', (1920, 1920), 'Hubble')

import os
import cutout
# Archimedes: the user's G05 drawing (a hand on a wax tablet, no likeness) when it is uploaded, else Fetti's painting
G05 = os.path.exists(asset('G05.png'))
FETTI_CARD = cutout.ink_image(asset('G05.png'), 880) if G05 else P.print_card(S.treated(FETTI), 620, seed=91)
ARIST_CARD = P.print_card(S.treated(ARISTARCHUS), 980, seed=92)
KASNER_CARD = P.print_card(S.treated(KASNER), 400, seed=93)


def sA(t, D):
    """Au IIIe siècle avant J.-C., Archimède attaque cette frontière. Il écrit au roi Gélon de
    Syracuse :"""
    s = Shot(t, D)
    S.env(s, 'archive')
    s.camera(1.0, 1.05, (W / 2, H / 2), (760, 470))
    P.mask_reveal(s.mid, FETTI_CARD, 720, 540, t, ENTER + 0.1, dur=1.4)
    TY.name_card(s.top, (1120, 420), 'Archimède', 'SYRACUSE', t, w(cue(6, 'Archimede')))
    kicker(s.hud, t, 3, 'Compter le sable', start=0.3)
    if G05:
        caption(s.hud, 'Illustration', t, ENTER + 1.4, corner='bl')
    else:
        caption(s.hud, 'Domenico Fetti, portrait d’un savant (dit Archimède), vers 1620, Dresde', t, ENTER + 1.4)
    return s


def sB(t, D):
    """« Certains pensent, roi Gélon, que le nombre des grains de sable est infini. »"""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, SAND, t, ENTER, ken=(1.02, 1.10), focus=(0.5, 0.5), focus_to=(0.45, 0.55), darken=0.55)
    TY.Text('« Certains pensent, roi Gélon, que le nombre des grains de sable est infini. »', 'quote', colour=PAL.light,
            max_w=1300, align='m').draw(s.hud, (W / 2, 760), t, w(cue(6, 'Certains')), anim='mask', anchor='m', shape='rect')
    caption(s.hud, 'Grains de sable en lumière polarisée', t, ENTER + 1.0, corner='tr', on_dark=True)
    return s


def sC(t, D):
    """Le plus grand nom de nombre grec est alors la myriade, dix mille."""
    s = Shot(t, D)
    S.env(s, 'cream')
    card = P.paper_card(1000, 360, seed=95, colour=PAL.light)            # the index card is there from the cut
    d = ImageDraw.Draw(card)
    for yy in range(90, 360, 54):
        d.line((40, yy, 960, yy), fill=PAL.soft + (255,), width=2)
    P.drop(s.mid, card, W / 2, 520, t, ENTER, rot=-1.5, spin=6, key='index')
    TY.term_card(s.top, (560, 420), 'MYRIADE', 'dix mille', t, w(cue(6, 'myriade')), width=860)
    return s


def sD(t, D):
    """Archimède prend la myriade de myriades, cent millions, comme nouvelle unité, et empile les
    ordres les uns sur les autres."""
    s = Shot(t, D)
    S.env(s, 'grid')
    d = ImageDraw.Draw(s.mid)
    ink, acc = PAL.ink, PAL.accent
    # a myriad: a 100 x 100 square of fine cells, which then becomes one cell of the next square
    g0 = w(cue(6, 'myriade'))
    shrink = P.ease_io(P.clamp01((t - w(cue(6, 'cent'))) / 1.0))
    size = 520 * (1 - shrink) + 26 * shrink
    cx, cy = 560 - 230 * shrink, 520 - 240 * shrink
    k = P.ease_out(P.clamp01((t - ENTER) / 0.6))
    if k > 0:
        x0, y0 = cx - size / 2, cy - size / 2
        n = 20 if size > 200 else 1
        for i in range(n + 1):
            a = int(160 * k) if i % 5 else int(230 * k)
            d.line((x0 + size * i / n, y0, x0 + size * i / n, y0 + size), fill=ink + (a,), width=1 if i % 5 else 2)
            d.line((x0, y0 + size * i / n, x0 + size, y0 + size * i / n), fill=ink + (a,), width=1 if i % 5 else 2)
        if shrink > 0.95:
            d.rectangle((x0, y0, x0 + size, y0 + size), fill=acc + (255,))
    if shrink > 0:
        big = 520
        bx0, by0 = 330 - 13, 280 - 13
        a = int(220 * P.clamp01(shrink / 0.45))
        for i in range(21):
            wd = 2 if i % 5 == 0 else 1
            d.line((bx0 + big * i / 20, by0, bx0 + big * i / 20, by0 + big), fill=ink + (a,), width=wd)
            d.line((bx0, by0 + big * i / 20, bx0 + big, by0 + big * i / 20), fill=ink + (a,), width=wd)
    # the orders, stacked one on the other: blocks that rise, each one the unit of the next
    for i in range(5):
        at = w(cue(6, 'empile')) + (0.0, 0.28, 0.5, 0.86, 1.05)[i]
        k = P.ease_out(P.clamp01((t - at) / 0.35))
        if k <= 0:
            continue
        bw_ = 360 - 34 * i
        bx = 1360 + (-8, 10, -4, 6, -2)[i] - bw_ / 2
        by = 900 - 120 * (i + 1) + (1 - k) * 60
        d.rectangle((bx, by, bx + bw_, by + 100), fill=(acc if i == 0 else PAL.soft) + (int(255 * k),), outline=ink + (int(255 * k),), width=3)
    return s


def sE(t, D):
    """Il conclut qu'il faudrait au plus dix puissance soixante-trois grains pour remplir
    l'univers tel qu'on le conçoit à son époque."""
    s = Shot(t, D)
    S.env(s, 'archive')
    s.camera(1.0, 1.04, (W / 2, H / 2), (640, 520))
    P.drop(s.mid, ARIST_CARD, 640, 520, t, ENTER, rot=-2, spin=8, key='arist')
    power(s.top, (1300, 380), '10', '63', 220, t, w(cue(6, 'dix')))
    words(s.top, (1420, 720), 'grains', 56, t, w(cue(6, 'grains', 2)), font=F_BODY)
    caption(s.hud, 'Le monde d’Aristarque et le nombre de grains de sable d’Archimède, gravure allemande', t, ENTER + 1.0)
    return s


def sF(t, D):
    """Le sable n'était pas infini, seulement innombrable pour qui manquait de mots."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, SAND, t, ENTER, ken=(1.10, 1.10), focus=(0.4, 0.45), fade=0.01)     # locked off: no move
    return s


def sG(t, D):
    """Vingt-deux siècles plus tard, un mot nouveau vient d'un enfant."""
    s = Shot(t, D)
    S.env(s, 'theme')
    tl = TL.Timeline(-300, 2000, box=(200, 560, 1720, 600), step=100)
    tl.axis(s.mid, t, ENTER, labels=False)
    TY.Text('Archimède', 'label', size=30).draw(s.mid, (tl.x(-250), tl.y + 40), t, ENTER + 0.2, anchor='m', sound=False)   # no year: none is spoken
    tl.era(s.mid, -250, 1920, '22 siècles', t, w(cue(7, 'siecles')))
    tl.event(s.mid, 1920, ' ', t, w(cue(7, 'siecles')) + 0.9, side='up')
    return s


ZERO_FONT = F_TYPE(46)
ZW = ZERO_FONT.getlength('0')


def strip(layer, x, y, t, start, n, cps=70, until=None):
    """A paper strip with '1' then n zeros typed onto it."""
    k = P.clamp01((t - start) / 0.3)
    if k <= 0:
        return 0
    typed = int(max(0, (t - start - 0.2) * cps))
    shown = min(n, typed)
    w_ = int(ZW * (shown + 1) + 80)
    card = P.paper_card(max(160, w_), 96, seed=111, colour=PAL.light)
    d = ImageDraw.Draw(card)
    d.text((40, 48), '1' + '0' * shown, font=ZERO_FONT, fill=PAL.ink + (255,), anchor='lm')
    P.put(layer, card, x + card.width / 2, y, op=k)
    sfx('type', start + 0.2, x, n=min(n, 60), cps=cps)
    return card.width


def sH(t, D):
    """Vers 1920, le mathématicien américain Edward Kasner demande à son neveu de neuf ans, Milton
    Sirotta, de nommer un 1 suivi de cent zéros."""
    s = Shot(t, D)
    S.env(s, 'paper')
    P.drop(s.mid, KASNER_CARD, 420, 430, t, ENTER, rot=-3, spin=9, key='kasner')
    TY.name_card(s.top, (720, 300), 'Edward Kasner', 'MATHÉMATICIEN · 1920', t, w(cue(7, 'Edward')))
    strip(s.mid, 160, 900, t, w(cue(7, '1')), 100, cps=95)
    TY.Text('googol', 'headline', size=150, upper=False).draw(s.top, (1300, 640), t, w(cue(7, 'googol')), anim='scale', anchor='m')
    caption(s.hud, 'Edward Kasner, Popular Science Monthly', t, ENTER + 1.2)
    return s


def sI(t, D):
    """L'enfant répond : googol."""
    s = Shot(t, D)
    S.env(s, 'cream')
    TY.Text('googol', 'headline', size=220, upper=False).draw(s.top, (W / 2, 400), t, w(cue(7, 'googol')), anim='scale', anchor='m')
    return s


def sJ(t, D):
    """Il invente aussi le googolplex, un 1 suivi d'un googol de zéros."""
    s = Shot(t, D)
    S.env(s, 'theme')
    start = w(cue(7, 'un', 3))
    # a strip that never ends: the camera pans along it
    pan = P.ease_io(P.clamp01((t - start + 0.6) / 2.6))
    x0 = 160 - pan * 1400
    width_ = strip(s.mid, x0, 620, t, ENTER, 400, cps=150)          # the strip is there from the cut
    TY.Text('googolplex', 'subhead', size=90, upper=False).draw(s.top, (W / 2, 330), t, w(cue(7, 'googolplex')), anim='words', anchor='m')
    return s


def sK(t, D):
    """L'univers observable ne compte qu'environ dix puissance quatre-vingts atomes, bien trop peu
    pour l'écrire en entier."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, HUBBLE, t, ENTER, ken=(1.0, 1.12), focus=(0.5, 0.5), focus_to=(0.55, 0.45), darken=0.2)
    power(s.hud, (W / 2, 420), '10', '80', 200, t, w(cue(7, 'dix')), colour=PAL.light, anchor='m')
    words(s.hud, (W / 2, 690), 'atomes', 54, t, w(cue(7, 'atomes')), fill=PAL.light, font=F_BODY)
    caption(s.hud, 'Hubble Ultra Deep Field, NASA / ESA', t, ENTER + 1.0, on_dark=True)
    return s


def sL(t, D):
    """Et le googol, mal orthographié, a donné son nom à Google."""
    s = Shot(t, D)
    S.env(s, 'cream')
    f = F_HEAD(170)
    base = 'goog'
    x0 = W / 2 - f.getlength('googol') / 2
    y = 420
    k = P.ease_out(P.clamp01((t - ENTER) / 0.5))
    d = ImageDraw.Draw(s.top)
    if k > 0:
        d.text((x0, y), base, font=f, fill=PAL.ink + (int(255 * k),), anchor='ls')
        xo = x0 + f.getlength(base)
        d.text((xo, y), 'ol', font=f, fill=PAL.ink + (int(255 * k),), anchor='ls')
        A.strike(s.top, (xo - 6, y - 110, xo + f.getlength('ol') + 6, y - 40), t, w(cue(7, 'orthographie')))
        at = w(cue(7, 'Google')) - 0.4
        n = int(P.clamp01((t - at) / 0.35) * 2)
        if n:
            d.text((xo, y + 190), 'le'[:n], font=f, fill=PAL.accent + (255,), anchor='ls')
            d.text((x0, y + 190), base, font=f, fill=PAL.accent + (int(255 * P.clamp01((t - at) / 0.3)),), anchor='ls')
    return s


SHOTS = [
    (0.0, sA),
    (cue(6, 'Certains') - LEAD, sB, ('circle', {'at': (W / 2, H / 2)})),
    (cue(6, 'Le plus') - LEAD, sC, 'lr'),
    (cue(6, 'Archimede', 2) - LEAD, sD, 'up'),
    (cue(6, 'Il conclut') - LEAD, sE, 'rl'),
    (cue(6, 'Le sable') - LEAD, sF, 'lr'),
    (cue(7, 'Vingt') - LEAD, sG, 'shape'),
    (cue(7, 'Vers') - LEAD, sH, 'rl'),
    (cue(7, 'Il invente') - LEAD, sJ, 'lr'),
    (cue(7, "'univers") - LEAD - 0.1, sK, 'up'),
    (cue(7, 'Et le') - LEAD, sL, 'rl'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
