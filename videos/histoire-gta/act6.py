"""Acte 6 : Les records. Narration clips 13-14."""
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

CLIPS = (13, 14)
cue = make_cue(CLIPS)

# ---- real material (SOURCES.md)
G4 = lambda n: Image.open(asset(f'game/steam/gta4_{n}.jpg'))       # official GTA IV screenshots (Steam)
G5 = lambda n: Image.open(asset(f'game/steam/gta5_{n}.jpg'))       # official GTA V / GTA Online screenshots (Steam)
GTA4_LOGO = P.load(asset('G06_gta4.png'), width=560)
ONLINE_LOGO = P.load(asset('G08_online.png'), width=420)
GTA5_BOX = P.print_card(Image.open(asset('game/wikipedia/b07_gta5_box.png')).convert('RGB'), 440, seed=61)
NIKO = P.print_card(G4(4), 820, seed=62)
TUMBLE = P.print_card(G4(1), 700, seed=63)
HEROES = [(P.print_card(G5(67), 560, seed=64), 'MICHAEL', 'Michael'),
          (P.print_card(G5(61), 560, seed=65), 'FRANKLIN', 'Franklin'),
          (P.print_card(G5(56), 560, seed=66), 'TREVOR', 'Trevor')]
EX, EX_BOX = G.article('A16_ex_head.png', 'A16_ex_q.png', 'Exophase', '7 MAI 2008', width=1250, seed=67)
GW, GW_BOX = G.article('A17_gw_head.png', 'A17_gw_q.png', 'Guinness World Records', '20 SEPTEMBRE 2013', width=1150, seed=68)
GD, GD_BOX = G.article('A02_gd_head.png', 'A18_gd230_q.png', 'Game Developer', '7 AOÛT 2026', width=1200, seed=69)


def into(s, xy, card, boxes, at, dur=1.0, above=200):
    y0 = min(b[1] for b in boxes); y1 = max(b[3] for b in boxes)
    s.zoom_to((xy[0] - 10, xy[1] + y0 - above, xy[0] + card.width + 10, xy[1] + y1 + 70), at, dur=dur, fill=0.95)


def sA(t, D):
    """GTA IV, en 2008, choisit un ton plus sombre."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, G4(2), t, -1.0, ken=(1.0, 1.08), focus=(0.5, 0.5), darken=0.4, fade=0.01)
    P.drop(s.mid, GTA4_LOGO, W / 2, 400, t, ENTER, rot=0, spin=6, height=0.8, key='g4l')
    tag(s.hud, (W / 2, 720), '2008', 60, t, w(cue(13, 'deux')))
    kicker(s.hud, t, 6, 'Les records')
    return s


def sB(t, D):
    """Niko Bellic, un ancien soldat venu d'Europe de l'Est, débarque à Liberty City en espérant
    y refaire sa vie."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.04, (640, 520))
    P.drop(s.mid, NIKO, 600, 500, t, ENTER, rot=-2, spin=10, key='niko')
    TY.name_card(s.top, (1150, 300), 'Niko Bellic', 'LE HÉROS DE GTA IV', t, w(cue(13, 'Niko')))
    tag(s.hud, (1480, 820), 'LIBERTY CITY', 54, t, w(cue(13, 'Liberty')))
    return s


FLOOR6 = 880
TRIP = [(c, P.paper_card(86, 116, seed=90 + k, text=c, size=78)) for k, c in enumerate('TRÉBUCHER')]
FALL = [(c, P.paper_card(96, 128, seed=100 + k, text=c, size=86, colour=G.THIEF)) for k, c in enumerate('TOMBER')]


def _pivot(layer, card, px, py, ang, lift=0.0):
    """Draw a standing card rotated by ang degrees (clockwise, falling to the right) about its
    bottom-right corner at (px, py), the way a real object tips over its edge."""
    a = math.radians(ang)
    ox, oy = -card.width / 2, -card.height / 2                   # centre, seen from the pivot
    cx = px + ox * math.cos(a) - oy * math.sin(a)
    cy = py + ox * math.sin(a) + oy * math.cos(a)
    P.put(layer, P.rot_scale(card, -ang, 1.0), cx, cy, lift=lift, sh_op=0.22)


def sC(t, D):
    """Un nouveau système d'animation fait trébucher et tomber les personnages de façon crédible."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.03, (W / 2, 540))
    P.drop(s.mid, TUMBLE, 520, 500, t, ENTER, rot=-3, spin=10, key='tum')
    said_tr, said_tb = w(cue(13, 'trebucher')), w(cue(13, 'ton', 2))
    tr, tb = said_tr + 0.3, said_tb + 0.25                       # the words land as they are said, then the physics
    # TRÉBUCHER: the letters walk on a line; on the word, each one catches its toe in turn,
    # pitches forward and stumbles back upright (a damped wobble about its front corner)
    if t >= said_tr:
        k_in = P.ease_out((t - said_tr) / 0.3)
        ImageDraw.Draw(s.mid).line((990, 470, 990 + 900 * k_in, 470), fill=S.ink(s) + (255,), width=4)
        for i, (c, card) in enumerate(TRIP):
            px = 1000 + 96 * i + card.width
            u = t - tr - 0.06 * i
            ang, hop = 0.0, 0.0
            if u > 0:
                ang = 32 * math.sin(min(u, 0.16) / 0.16 * math.pi / 2) if u < 0.16 else 32 * math.exp(-(u - 0.16) * 5.5) * math.cos((u - 0.16) * 16)
                hop = 10 * math.sin(min(1.0, u / 0.25) * math.pi)
                if i % 3 == 0:
                    sfx('tick', tr + 0.06 * i + 0.16, px, gain=0.3)
            if t >= said_tr + 0.02 * i:
                _pivot(s.mid, card, px, 470 - hop, max(-8.0, ang), lift=0.05)
    # TOMBER: dominoes; each letter tips over its front edge, gravity speeds it up, it slams flat
    # on the floor, bounces a little and settles
    if t >= said_tb:
        k_in = P.ease_out((t - said_tb) / 0.3)
        ImageDraw.Draw(s.mid).line((870, FLOOR6, 870 + 980 * k_in, FLOOR6), fill=S.ink(s) + (255,), width=4)
        for i, (c, card) in enumerate(FALL):
            px = 880 + 142 * i + card.width
            if t < said_tb + 0.02 * i:
                continue
            u = t - tb - 0.11 * i
            if u <= 0:
                ang = 0.0
            elif u < 0.42:
                ang = 90 * (u / 0.42) ** 2
            else:
                v = u - 0.42
                ang = 90 - 9 * math.exp(-v * 7) * abs(math.sin(v * 15))
                sfx('drop', tb + 0.11 * i + 0.42, px, gain=0.35)
            _pivot(s.mid, card, px, FLOOR6, ang)
    return s


EX_XY = (W / 2 - EX.width / 2, 140)


def sD(t, D):
    """En une semaine, le jeu rapporte 500 millions de dollars."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.0)
    cy = EX_XY[1] + EX.height / 2
    P.slide(s.mid, EX, (W + EX.width, cy), (W / 2, cy), t, ENTER, dur=0.8, rot=0.0, lag=4.0, key='ex')
    G.highlight(s.mid, EX_XY, EX_BOX[list(EX_BOX)[0]], t, w(cue(13, 'rapporte')), dark=True)
    TY.big_number(s.top, (W / 2, 690), '500', t, w(cue(13, 'rapporte')) + 0.3, role='stat', label='MILLIONS DE DOLLARS · EN UNE SEMAINE')
    return s


def sE(t, D):
    """GTA V va plus loin."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, G5(65), t, -1.0, ken=(1.0, 1.1), focus=(0.5, 0.5), darken=0.35, fade=0.01)
    tag(s.hud, (W / 2, 940), 'SEPTEMBRE 2013', 60, t, w(cue(14, 'septembre')))
    return s


def sF(t, D):
    """Sorti en septembre 2013, il permet de passer à tout moment d'un héros à l'autre parmi trois :"""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.03)
    P.drop(s.mid, GTA5_BOX, 420, 540, t, ENTER, rot=-3, spin=10, key='g5b')
    A.emphasis(s.top, (1250, 540), 'PARMI TROIS', 120, t, w(cue(14, 'trois')))
    return s


def sG(t, D):
    """Michael, Franklin et Trevor ..."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.02)
    for i, (card, name, ph) in enumerate(HEROES):
        x = 340 + i * 620
        P.drop(s.mid, card, x + (-30, 10, 40)[i], 460 + (0, 30, -20)[i], t, ENTER + (0.0, 0.25, 0.7)[i], rot=(-3.5, 1.5, -2)[i], spin=10, key=f'hero{i}')
        tag(s.hud, (x, 820), name, 60, t, w(cue(14, ph)))
    return s


def sH(t, D):
    """... dans Los Santos, une version de Los Angeles."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, G5(57), t, -1.0, ken=(1.0, 1.08), focus=(0.5, 0.5), darken=0.3, fade=0.01)
    tag(s.hud, (W / 2, 420), 'LOS SANTOS', 80, t, ENTER + 0.1)
    words(s.hud, (W / 2, 600), 'UNE VERSION DE LOS ANGELES', 60, t,
          [w(cue(14, x)) for x in ('une', 'version', 'de', 'Los', 'Angeles')], fill=CREAM)
    return s


GW_XY = (W / 2 - GW.width / 2, 120)


def sI(t, D):
    """Il rapporte un milliard de dollars en trois jours, un record mondial pour un produit de
    divertissement."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.0)
    cy = GW_XY[1] + GW.height / 2
    P.slide(s.mid, GW, (-GW.width, cy), (W / 2, cy), t, ENTER, dur=0.8, rot=0.0, lag=4.0, key='gw')
    G.highlight(s.mid, GW_XY, GW_BOX[list(GW_BOX)[0]], t, w(cue(14, 'milliard')))
    TY.big_number(s.top, (W / 2 - 300, 790), '3', t, w(cue(14, 'jours')) - 0.3, role='stat', label='JOURS · 1 MILLIARD DE DOLLARS')
    P.stamp_hit(s.mid, 'RECORD MONDIAL', W / 2 + 360, 900, t, w(cue(14, 'record')), size=84, ang=-7, shot=s)
    return s


def sJ(t, D):
    """Deux semaines plus tard, Rockstar lance GTA Online, un monde partagé que le studio alimente
    en mises à jour pendant plus de dix ans."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, G5(1), t, -1.0, ken=(1.0, 1.08), focus=(0.45, 0.5), darken=0.4, fade=0.01)
    P.drop(s.mid, ONLINE_LOGO, W / 2, 450, t, w(cue(14, 'Online')) - 0.2, rot=0, spin=6, height=0.8, key='onl')
    return s


GD_XY = (W / 2 - GD.width / 2, 110)


def sK(t, D):
    """Mi-2026, GTA V dépassait les 230 millions d'exemplaires."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.0)
    cy = GD_XY[1] + GD.height / 2
    P.slide(s.mid, GD, (W + GD.width, cy), (W / 2, cy), t, ENTER, dur=0.8, rot=0.0, lag=4.0, key='gd')
    G.highlight(s.mid, GD_XY, GD_BOX[list(GD_BOX)[0]], t, w(cue(14, '230')) - 0.2)
    TY.big_number(s.top, (W / 2, 760), '230', t, w(cue(14, '230')), role='stat', label="MILLIONS D'EXEMPLAIRES · MI-2026")
    return s


SHOTS = [
    (0.0, sA),
    (cue(13, 'Niko') - LEAD, sB, 'lr'),
    (cue(13, 'Un nouveau') - LEAD, sC, 'up'),
    (cue(13, 'En une') - LEAD, sD, 'rl'),
    (cue(14, 'GTA') - LEAD, sE, 'pageturn'),
    (cue(14, 'il permet') - LEAD, sF, 'cut'),
    (cue(14, 'Michael') - LEAD, sG, 'lr'),
    (cue(14, 'Los') - LEAD, sH, 'cut'),
    (cue(14, 'Il rapporte') - LEAD, sI, 'cut'),
    (cue(14, 'Deux') - LEAD, sJ, 'rl'),
    (cue(14, 'GTA', 3) - LEAD, sK, 'shape'),
]
END = cue.total + 1.2

G.sync(globals())


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
