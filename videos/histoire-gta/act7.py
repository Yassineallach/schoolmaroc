"""Acte 7 : L'attente. Narration clips 15-16."""
import sys
import math
from PIL import Image
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
from style import sfx, ENTER, Shot, words, tag, kicker
import gta as G

CLIPS = (15, 16)
cue = make_cue(CLIPS)

# ---- real material (SOURCES.md)
R = lambda n: Image.open(asset(f'game/rockstar/{n}.jpg'))            # Rockstar's official GTA VI art and screenshots (rockstargames.com/VI)
DUO_GAME, DUSK, DUO_ART = R('vi_ingame_duo'), R('vi_vicecity_dusk'), R('vi_duo_skyline')
GTA6_LOGO = P.load(asset('G09_gta6.png'), width=520)
TRAILER = P.print_card(R('vi_trailer1_art'), 470, seed=71)
TAKE2 = P.load(asset('L02_take2.png'), width=220)
ROCKSTAR = P.load(asset('L04_rockstar.png'), width=230)
OFFICES = P.print_card(Image.open(asset('P02_dma_offices.png')), 520, seed=72)   # DMA's original offices, Murray Barnes, CC BY-SA 4.0
GTA3_BOX = P.print_card(Image.open(asset('game/wikipedia/b03_gta3_box.jpg')), 430, seed=73)
GTA6_BOX = P.print_card(Image.open(asset('game/wikipedia/b09_gta6_cover.png')).convert('RGB'), 430, seed=74)
LOGOS = [P.load(asset(f), width=260) for f in ('G01_gta1997.png', 'G02_gta2.png', 'G03_gta3.png', 'G04_vicecity.png',
                                                'G05_sanandreas.png', 'G06_gta4.png', 'G08_online.png', 'G09_gta6.png')]
GW, GW_BOX = G.article('A19_gw6_head.png', 'A19_gw6_q.png', 'Guinness World Records', '6 DÉCEMBRE 2023', width=1250, seed=75)
GB, GB_BOX = G.article('A20_gb_head.png', 'A20_gb_q.png', 'GamesBeat', '9 NOVEMBRE 2026', width=1150, seed=76)


def sA(t, D):
    """Cette longévité a rendu l'attente immense."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, DUO_GAME, t, -1.0, ken=(1.0, 1.08), focus=(0.5, 0.5), darken=0.35, fade=0.01)
    P.drop(s.mid, GTA6_LOGO, W / 2, 470, t, w(cue(15, "'attente")) - 0.2, rot=0, spin=6, height=0.8, key='g6l')
    kicker(s.hud, t, 7, "L'attente")
    return s


def sB(t, D):
    """En décembre 2023, la première bande-annonce de GTA VI atteint 90 millions de vues en 24 heures, ..."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.04, (620, 540))
    P.drop(s.mid, TRAILER, 560, 540, t, ENTER, rot=-3, spin=10, key='tr1')
    tag(s.hud, (1300, 230), 'DÉCEMBRE 2023', 52, t, w(cue(15, '2023')))
    TY.big_number(s.top, (1300, 520), '90', t, w(cue(15, '90')), role='stat', label='MILLIONS DE VUES')
    tag(s.hud, (1300, 960), 'EN 24 HEURES', 56, t, w(cue(15, 'heures')))
    return s


GW_XY = (W / 2 - GW.width / 2, 150)


def sC(t, D):
    """... un record sur YouTube pour une vidéo qui n'est pas musicale."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.0)
    cy = GW_XY[1] + GW.height / 2
    P.slide(s.mid, GW, (W + GW.width, cy), (W / 2, cy), t, ENTER, dur=0.8, rot=0.0, lag=4.0, key='gw6')
    G.highlight(s.mid, GW_XY, GW_BOX['with 90,421,491 views'], t, ENTER + 0.5)
    G.highlight(s.mid, GW_XY, GW_BOX['most viewed YouTube video in 24 hours (non-music)'], t, w(cue(15, 'record')))
    return s


def sD(t, D):
    """Le jeu ramène la série à Vice City, dans l'État fictif de Leonida, ..."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, DUSK, t, -1.0, ken=(1.0, 1.1), focus=(0.5, 0.45), darken=0.3, fade=0.01)
    tag(s.hud, (W / 2, 420), 'VICE CITY', 84, t, w(cue(15, 'City')))
    words(s.hud, (W / 2, 600), 'LEONIDA', 64, t, [w(cue(15, 'Leonida'))], fill=CREAM)
    return s


def sE(t, D):
    """... avec deux héros, Lucia et Jason."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, DUO_ART, t, -1.0, ken=(1.0, 1.05), focus=(0.5, 0.45), darken=0.15, fade=0.01)
    tag(s.hud, (W / 2 + 230, 960), 'LUCIA', 64, t, w(cue(15, 'Lucia')))
    tag(s.hud, (W / 2 - 230, 960), 'JASON', 64, t, w(cue(15, 'Jason')), bg=CREAM, fg=INK)
    return s


DATES = [('2025', 'Annoncee', 'puis'), ('MAI 2026', 'mai', 'la sortie'), ('19 NOVEMBRE 2026', '19', None)]


def sF(t, D):
    """Annoncée pour 2025, puis pour mai 2026, la sortie a été fixée au 19 novembre 2026, ..."""
    s = Shot(t, D)
    S.env(s, 'grid')
    s.camera(1.0, 1.04)
    for i, (txt, said, gone) in enumerate(DATES):
        wd, size = (430, 64) if i < 2 else (980, 68)
        card = P.paper_card(wd, 170, seed=80 + i, text=txt, size=size, colour=CREAM if i < 2 else G.THIEF)
        at = w(cue(15, said)) + (0.35 if i == 0 else -0.1)
        x, y = ((560, 360), (1360, 360), (W / 2, 720))[i]
        P.drop(s.mid, card, x, y, t, at, rot=(-3, 2, -1)[i], spin=8, key=f'date{i}')
        if gone:
            A.strike(s.mid, (x - wd / 2 + 30, y - 40, x + wd / 2 - 30, y + 40), t, w(cue(15, gone)) - 0.1, scribble=True)
    A.underline(s.top, (W / 2 - 420, 790, W / 2 + 420, 810), t, w(cue(15, 'novembre')) + 0.4)
    return s


GB_XY = (W / 2 - GB.width / 2, 170)


def sG(t, D):
    """... une date que Take-Two a confirmée début novembre."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.0)
    cy = GB_XY[1] + GB.height / 2
    P.slide(s.mid, GB, (-GB.width, cy), (W / 2, cy), t, ENTER, dur=0.8, rot=0.0, lag=4.0, key='gb')
    P.drop(s.mid, TAKE2, GB_XY[0] + GB.width - 140, GB_XY[1] - 40, t, w(cue(15, 'Take')), rot=0, spin=8, height=0.6, key='t2')
    G.highlight(s.mid, GB_XY, GB_BOX[list(GB_BOX)[0]], t, w(cue(15, 'confirmee')))
    return s


def sH(t, D):
    """Tout est parti d'une erreur de programmation que quelques développeurs écossais ont eu
    l'intelligence de garder."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    s.camera(1.12, 1.0, (960, 540))
    s.mid.alpha_composite(G.city())
    tx, ty = 960, 540
    G.car(s.mid, 'thief', tx, ty, 0, t)
    for i in range(3):                                       # the bug: the police close in and circle the thief
        a = math.radians(200 + i * 120) + 0.8 * max(0.0, t - ENTER - 0.6)
        r = 360 - 180 * P.ease_io((t - ENTER) / 1.4)
        G.car(s.mid, 'cop', tx + r * math.cos(a), ty + r * math.sin(a), math.degrees(a) + 90, t)
    P.drop(s.mid, OFFICES, 1480, 700, t, w(cue(16, 'developpeurs')) - 0.2, rot=3, spin=10, key='off7')
    return s


def sI(t, D):
    """Après près de trois décennies, une question demeure :"""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.03)
    a, b = ENTER, w(cue(16, 'demeure'))
    for i, logo in enumerate(LOGOS):                         # 1997 -> 2026, one logo after the other
        x = 250 + (i % 4) * 473
        y = 360 + (i // 4) * 380
        P.drop(s.mid, logo, x, y, t, a + (b - a) * i / len(LOGOS), rot=(-3, 2, -2, 3)[i % 4], spin=8, height=0.7, key=f'lg{i}')
    return s


def sJ(t, D):
    """Rockstar peut-il encore créer un jeu qui transforme l'industrie comme GTA III l'avait fait ?"""
    s = Shot(t, D)
    S.env(s, 'charcoal', mood='tense')
    s.camera(1.0, 1.04)
    P.drop(s.mid, ROCKSTAR, W / 2, 230, t, w(cue(16, 'Rockstar')) - 0.1, rot=0, spin=6, height=0.6, key='rs')
    P.drop(s.mid, GTA6_BOX, 1440, 520, t, w(cue(16, 'creer')) - 0.1, rot=3, spin=10, key='b6')
    P.drop(s.mid, GTA3_BOX, 480, 520, t, w(cue(16, 'GTA')) - 0.1, rot=-3, spin=10, key='b3')
    A.emphasis(s.top, (W / 2, 520), '?', 300, t, w(cue(16, 'fait')), base=CREAM, colour=G.THIEF)
    return s


SHOTS = [
    (0.0, sA),
    (cue(15, 'En decembre') - LEAD, sB, 'lr'),
    (cue(15, 'un record') - LEAD, sC, 'rl'),
    (cue(15, 'Le jeu') - LEAD, sD, 'pageturn'),
    (cue(15, 'avec deux') - LEAD, sE, 'cut'),
    (cue(15, 'Annoncee') - LEAD, sF, 'up'),
    (cue(15, 'une date') - LEAD, sG, 'rl'),
    (cue(16, 'Tout') - LEAD, sH, ('circle', {'at': (W / 2, H / 2)})),
    (cue(16, 'Apres') - LEAD, sI, 'lr'),
    (cue(16, 'Rockstar') - LEAD, sJ, 'cut'),
]
END = cue.total + 2.5          # the last question hangs a moment before the end

G.sync(globals())


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
