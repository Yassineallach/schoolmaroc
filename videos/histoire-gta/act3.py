"""Acte 3 : Le scandale. Narration clips 6-7."""
import sys
import math
from PIL import Image, ImageDraw
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
from style import sfx, ENTER, Shot, words, tag, kicker
import gta as G

CLIPS = (6, 7)
cue = make_cue(CLIPS)

# ---- real material (SOURCES.md)
HANS = G.Page('hansard')                  # Hansard, House of Lords, 20 May 1997
GI = G.Page('gi')                         # GamesIndustry.biz, 22 Oct 2012
MEL = G.Page('mel')                       # MEL Magazine, 27 Jan 2022
CLIFFORD = P.print_card(Image.open(asset('P04_clifford.jpg')), 430, seed=34)          # Max Clifford, 2014, CC BY 2.0
HOUSERS = P.print_card(Image.open(asset('P05_housers.png')), 520, seed=35)            # Sam and Dan Houser, CC BY-SA 4.0
BRAZIL = P.print_card(Image.open(asset('F01_brazil.png')).convert('RGB'), 560, border=10, seed=36)
BMG = P.load(asset('L06_bmg.png'), width=380)
BMG_CARD = P.paper_card(BMG.width + 60, BMG.height + 50, seed=38, colour=CREAM)
BMG_CARD.alpha_composite(BMG, (30, 25))
TAKE2 = P.load(asset('L02_take2.png'), width=330)
ROCKSTAR = P.load(asset('L04_rockstar.png'), width=300)
GTA_LOGO = P.load(asset('G01_gta1997.png'), width=420)
GTA2_LOGO = P.load(asset('G02_gta2.png'), width=560)
GTA_BOX = Image.open(asset('B02_gta_box.jpg'))
GTA2_BOX = P.print_card(Image.open(asset('game/wikipedia/b02b_gta2_box.jpg')), 420, seed=37)
GTA2_SHOT = Image.open(asset('game/wikipedia/s02_gta2.jpg'))                           # GTA 2, in-game (Wikipedia)
GTA3_SHOT = Image.open(asset('game/steam/gta3_6.jpg'))                                 # GTA III, official screenshot (Steam)


def sA(t, D):
    """Le scandale arrive avant le jeu."""
    s = Shot(t, D)
    S.env(s, 'charcoal', mood='tense')
    s.camera(1.04, 1.0)
    words(s.top, (W / 2, 470), 'LE SCANDALE', 140, t, [ENTER, w(cue(6, 'scandale'))], fill=S.accent(s))
    words(s.top, (W / 2, 620), 'ARRIVE AVANT LE JEU', 92, t,
          [w(cue(6, x)) for x in ('arrive', 'avant', 'le jeu', 'jeu')], fill=S.ink(s))
    kicker(s.hud, t, 3, 'Le scandale')
    return s


def sB(t, D):
    """En mai 1997, Lord Campbell of Croy en dénonce le contenu à la Chambre des lords."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    q1, q2 = 'Lord Campbell of Croy', 'Whether they will take'
    G.browse(s, HANS, t, [(ENTER - 1.0, HANS.top()), (w(cue(6, 'Lord')) - 0.4, HANS.on(q2, dy=-40))],
             marks=[(q1, w(cue(6, 'Lord')) + 0.6), (q2, w(cue(6, 'denonce')))], dur=1.2)
    tag(s.hud, (1560, 130), 'MAI 1997', 52, t, w(cue(6, 'mai')))
    tag(s.hud, (W / 2, 960), 'LA CHAMBRE DES LORDS', 52, t, w(cue(6, 'Chambre')))
    return s


def sC(t, D):
    """Plutôt que d'éteindre la polémique, l'éditeur BMG Interactive engage le publicitaire Max
    Clifford pour l'entretenir."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    q = 'He designed all the outcry'
    G.browse(s, GI, t, [(ENTER - 1.0, GI.top()), (w(cue(6, 'Clifford')) - 0.3, GI.on(q))],
             marks=[(q, w(cue(6, 'Clifford')) + 0.8)], dur=1.2)
    P.drop(s.hud, BMG_CARD, 1620, 330, t, w(cue(6, 'BMG')) - 0.1, rot=3, spin=8, height=0.7, key='bmg')
    tag(s.hud, (W / 2, 140), 'MAX CLIFFORD, PUBLICITAIRE', 50, t, w(cue(6, 'Max')))
    G.typed_quote(s.hud, (W / 2, 950), '« Il a orchestré tout le scandale. »', t, w(cue(6, 'Max')) + 0.2, size=44, cps=30)
    return s


def sD(t, D):
    """Le jeu est interdit aux moins de 18 ans au Royaume-Uni ..."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    q = 'classification by the BBFC'
    G.browse(s, MEL, t, [(ENTER - 1.0, MEL.top()), (w(cue(6, 'jeu')) + 0.1, MEL.on(q))],
             marks=[(q, w(cue(6, 'moins')) + 0.2)], dur=1.1)
    P.stamp_hit(s.hud, '18', 1640, 300, t, w(cue(6, 'moins')) + 0.4, size=140, ang=-8, shot=s)
    tag(s.hud, (W / 2, 960), 'ROYAUME-UNI : INTERDIT AUX MOINS DE 18 ANS', 46, t, w(cue(6, 'Royaume')))
    return s


def sD2(t, D):
    """... et interdit tout court au Brésil."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.05)
    P.drop(s.mid, BRAZIL, W / 2, 470, t, ENTER, rot=3, spin=10, key='br')
    P.stamp_hit(s.mid, 'INTERDIT', W / 2, 480, t, w(cue(6, 'Bresil')) - 0.2, size=120, ang=-12, shot=s)
    tag(s.hud, (W / 2, 900), 'BRÉSIL', 56, t, ENTER + 0.2)
    return s


def sE(t, D):
    """Le programmeur principal, Keith Hamilton, résumera : « On n'aurait jamais cru que ça
    poserait autant de problèmes. »"""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.03)
    TY.name_card(s.top, (260, 300), 'Keith Hamilton', 'PROGRAMMEUR PRINCIPAL, DMA DESIGN', t, ENTER)
    G.typed_quote(s.top, (W / 2, 580), "« On n'aurait jamais cru que ça poserait autant de problèmes. »", t,
                  w(cue(6, 'Keith')) + 0.5, size=64, width=1500, cps=19)
    return s


def sF(t, D):
    """Ce Noël-là, environ un demi-million d'exemplaires se vendent en Grande-Bretagne."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.05, (W / 2, 560))
    for i in range(7):                                             # copies pile up on the shop counter
        box = P.print_card(GTA_BOX, 300, seed=60 + i)
        P.drop(s.mid, box, 380 + i * 195, 560 + (i % 2) * 40, t, ENTER + 0.22 * i,
               rot=(-6, 4, -3, 5, -4, 3, -2)[i], spin=10, key=f'cp{i}')
    tag(s.hud, (W / 2, 160), 'NOËL 1997', 56, t, w(cue(6, 'Noel')))
    tag(s.hud, (W / 2, 960), 'GRANDE-BRETAGNE', 52, t, w(cue(6, 'Grande')), bg=CREAM, fg=INK)
    return s


def sG(t, D):
    """En 1998, Take-Two rachète BMG Interactive, et avec lui la licence."""
    s = Shot(t, D)
    S.env(s, 'grid')
    s.camera(1.0, 1.02)
    TY.big_number(s.top, (W / 2, 190), '1998', t, w(cue(7, '1998')), role='date')
    P.drop(s.mid, TAKE2, 520, 600, t, ENTER, rot=0, spin=8, height=0.7, key='t2')
    k = P.ease_io((t - w(cue(7, 'rachete'))) / 0.9)               # BMG slides into Take-Two
    if t > w(cue(7, 'BMG')) - 0.3:
        bx = 1380 + (720 - 1380) * k
        P.put(s.mid, P.rot_scale(BMG, 0, 1.0 - 0.45 * k, None), bx, 600, lift=0.1 * (1 - k), op=1.0 - 0.6 * k)
    P.drop(s.mid, P.print_card(GTA_LOGO.convert('RGBA'), 440, border=20, seed=71), 1400, 640, t, w(cue(7, 'licence')) - 0.2,
           rot=3, spin=10, key='lic')
    tag(s.hud, (1400, 900), 'LA LICENCE', 48, t, w(cue(7, 'licence')))
    return s


def sH(t, D):
    """La même année, les frères Sam et Dan Houser participent à la création d'un nouveau label à
    New York : Rockstar Games."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.04, (620, 540))
    P.drop(s.mid, HOUSERS, 620, 520, t, ENTER, rot=-2, spin=10, key='hous')
    TY.name_card(s.top, (980, 330), 'Sam et Dan Houser', 'LES FRÈRES', t, w(cue(7, 'Sam')))
    P.drop(s.mid, ROCKSTAR, 1330, 680, t, w(cue(7, 'Rockstar')) - 0.15, rot=0, spin=8, height=0.7, key='rs')
    tag(s.hud, (1640, 860), 'NEW YORK', 48, t, w(cue(7, 'New')))
    return s


def sI(t, D):
    """GTA 2 sort en 1999, dans une ville rétrofuturiste nommée Anywhere City."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.03)
    P.drop(s.mid, GTA2_BOX, 330, 560, t, ENTER, rot=-3, spin=10, key='g2b')
    P.drop(s.mid, GTA2_LOGO, 1150, 200, t, w(cue(7, 'GTA')), rot=0, spin=6, height=0.6, key='g2l')
    shot = P.print_card(GTA2_SHOT, 820, seed=72)
    P.drop(s.mid, shot, 1150, 620, t, w(cue(7, 'ville')) - 0.2, rot=2, spin=8, key='g2s')
    tag(s.hud, (600, 140), '1999', 56, t, w(cue(7, 'sort')))
    tag(s.hud, (1150, 960), 'ANYWHERE CITY', 56, t, w(cue(7, 'Anywhere')))
    return s


def meter(layer, x, y, label, value, colour, t, start):
    """A respect bar: label, empty track, fill to value (0-1)."""
    if t < start - 0.3:
        return
    d = ImageDraw.Draw(layer)
    d.text((x, y - 40), label, font=F_HEAD(38), fill=INK + (255,), anchor='ls')
    d.rounded_rectangle((x, y, x + 600, y + 50), radius=12, outline=INK + (255,), width=4)
    if value > 0.01:
        d.rounded_rectangle((x + 6, y + 6, x + 6 + 588 * value, y + 44), radius=8, fill=colour + (255,))


def sJ(t, D):
    """Le jeu ajoute des gangs rivaux et un système de respect : travailler pour une bande fait
    monter sa cote auprès d'elle, mais attire la colère de ses ennemis."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.02)
    P.put(s.mid, P.print_card(GTA2_SHOT, 600, seed=73), 430, 560)
    tag(s.hud, (W / 2, 140), 'LE RESPECT', 60, t, w(cue(7, 'respect')))
    up = P.ease_out((t - w(cue(7, 'monter'))) / 1.0)
    down = P.ease_out((t - w(cue(7, 'colere'))) / 1.0)
    meter(s.mid, 1000, 360, 'TA BANDE', 0.35 + 0.55 * up, (40, 150, 70), t, ENTER)
    meter(s.mid, 1000, 560, 'SES ENNEMIS', 0.55 - 0.5 * down, PAL.accent, t, ENTER)
    meter(s.mid, 1000, 760, 'SES ENNEMIS', 0.5 - 0.45 * down, PAL.accent, t, ENTER)
    return s


def sK(t, D):
    """L'idée restera au cœur de la série, même si le jeu, encore en 2D, arrive au moment où les
    consoles basculent vers la 3D."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.04, (W / 2, 520))
    front = P.print_card(GTA2_SHOT, 900, seed=74)
    back = P.print_card(GTA3_SHOT, 900, seed=75)
    back = back.resize((front.width, front.height), Image.LANCZOS)
    P.flip(s.mid, front, back, W / 2, 500, t, w(cue(7, 'arrive', 1)) - 0.2)
    tag(s.hud, (330, 500), 'EN 2D', 60, t, w(cue(7, '2D')))
    tag(s.hud, (1590, 500), 'LA 3D', 60, t, w(cue(7, 'consoles')), bg=G.THIEF, fg=INK)
    words(s.hud, (W / 2, 960), "l'idée restera au cœur de la série", 50, t,
          [w(cue(7, x)) for x in ("l", "'idee", 'restera', 'au', 'cœur', 'de la', 'serie')], font=F_TYPE)
    return s


SHOTS = [
    (0.0, sA),
    (cue(6, 'En mai') - LEAD, sB, 'up'),
    (cue(6, 'Plutot') - LEAD, sC, 'lr'),
    (cue(6, 'Le jeu est') - LEAD, sD, 'rl'),
    (cue(6, 'interdit', 2) - 0.25, sD2, 'cut'),
    (cue(6, 'Le programmeur') - LEAD, sE, 'up'),
    (cue(6, 'Ce Noel') - LEAD, sF, 'shape'),
    (cue(7, 'En 1998') - LEAD, sG, 'pageturn'),
    (cue(7, 'La meme') - LEAD, sH, 'rl'),
    (cue(7, 'GTA 2') - LEAD, sI, 'up'),
    (cue(7, 'Le jeu ajoute') - LEAD, sJ, 'lr'),
    (cue(7, "L 'idee") - LEAD, sK, 'cut'),
]
END = cue.total + 1.2          # hold the GTA III image a moment after the last word


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
