"""Acte 2 : Dundee. Narration clips 4-5."""
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

CLIPS = (4, 5)
cue = make_cue(CLIPS)

# ---- real material (SOURCES.md)
OFFICES = P.print_card(Image.open(asset('P02_dma_offices.png')), 560, seed=21)         # DMA's original offices, Murray Barnes, CC BY-SA 4.0
DMA = P.load(asset('L03_dma.png'), width=330)                                          # DMA Design logo (Wikipedia)
JONES = P.print_card(Image.open(asset('P03_jones.jpg')), 420, seed=22)                 # David Jones, Gamelab 2018 (Commons)
LEMMINGS = P.print_card(Image.open(asset('B01_lemmings_box.jpg')), 480, seed=23)       # Lemmings box, Psygnosis 1991 (Wikipedia)
MOCKUP = P.print_card(Image.open(asset('R01_racenchase.jpg')), 420, seed=11)
GTA_BOX = P.print_card(Image.open(asset('B02_gta_box.jpg')), 520, seed=24)             # GTA 1997 box (Wikipedia)
GTA1_SHOT = P.print_card(Image.open(asset('game/wikipedia/s01_gta1.png')), 600, seed=26)   # GTA (1997), in-game (Wikipedia)
CITIES = [P.print_card(Image.open(asset(f)), 520, seed=30 + i)
          for i, f in enumerate(('C01_newyork.jpg', 'C02_miami.jpg', 'C03_sanfrancisco.jpg'))]
COP_Q, COP_BOX = G.article('A01_penn_head.png', 'A03_penn_cop.png', 'Game Developer (Gamasutra)', '31 JANVIER 2011', width=1380, seed=25)


def sA(t, D):
    """Le studio s'appelait DMA Design. Fondé à Dundee par David Jones, ..."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.04, (760, 540))
    P.drop(s.mid, OFFICES, 560, 560, t, ENTER, rot=-3, spin=10, key='off')
    P.drop(s.mid, DMA, 1180, 300, t, w(cue(4, 'DMA')) - 0.1, rot=4, spin=14, key='dma')
    P.drop(s.mid, JONES, 1500, 600, t, w(cue(4, 'David')) - 0.2, rot=2.5, spin=10, key='jones')
    TY.name_card(s.top, (1180, 940), 'David Jones', 'FONDATEUR DE DMA DESIGN', t, w(cue(4, 'David')))
    kicker(s.hud, t, 2, 'Dundee')
    return s



EXIT_X, FLOOR = 1640, 930


def sC(t, D):
    """... il avait connu le succès en 1991 avec Lemmings, un jeu où l'on guide de petites
    créatures qui avancent sans réfléchir vers la sortie."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.03)
    TY.big_number(s.top, (480, 330), '1991', t, w(cue(4, 'ami')), role='date', label='LE SUCCÈS')
    P.drop(s.mid, LEMMINGS, 1300, 400, t, ENTER, rot=3, spin=12, key='lem')
    go = w(cue(4, 'creature'))
    if t >= go - 0.6:
        G.exit_door(s.mid, EXIT_X, FLOOR, scale=1.8)
        ImageDraw.Draw(s.mid).line((60, FLOOR + 12, W - 60, FLOOR + 12), fill=S.ink(s) + (255,), width=4)
        for i in range(9):                                                  # they march, one after another, into the exit
            x = 160 + 150 * (t - go + 0.6) - i * 170
            if 100 < x < EXIT_X - 10:
                G.creature(s.mid, x, FLOOR, t, scale=2.6)
    return s


def sD(t, D):
    """Avec Race'n'Chase, l'équipe voulait une ville entière vue du dessus, où le joueur
    incarnerait le policier ou le voleur. Mais les missions tournaient en rond."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    s.camera(1.35, 1.0, (960, 540))
    s.mid.alpha_composite(G.city())
    P.drop(s.mid, MOCKUP, 300, 380, t, ENTER + 0.2, rot=-4, spin=10, key='mockD')
    go = w(cue(4, 'tournaient'))
    for i, kind in enumerate(('cop', 'thief')):                    # round and round the same block
        u = max(0.0, t - go) * 0.9 + i * 0.5
        a = u * 2 * math.pi
        x = 960 + 300 * math.cos(a) * (1 if t > go else 0) + (0 if t > go else (-320 if i == 0 else 340))
        y = 540 + 290 * math.sin(a) * (1 if t > go else 0) + (0 if t > go else (-290 if i == 0 else 290))
        hd = math.degrees(a) + 90 if t > go else (0 if i == 0 else 180)
        G.car(s.mid, kind, x, y, hd, t)
    return s



def sF(t, D):
    """Le bug de la police a changé l'équilibre : les testeurs préféraient semer le chaos dans les
    rues plutôt que suivre les objectifs."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    s.camera(1.0, 1.06, (960, 540))
    s.mid.alpha_composite(G.city())
    T0 = w(cue(4, 'chaos')) - 0.6
    for i in range(6):                                                     # cars spinning off in every direction
        a = i * 1.047 + 0.4
        r = 190 + 200 * P.ease_out((t - T0) / 2.2) if t > T0 else 190
        x, y = 960 + r * math.cos(a) + 30 * math.sin(t * 3 + i), 540 + r * math.sin(a) * 0.8
        G.car(s.mid, 'thief' if i % 3 == 0 else 'cop', x, y, math.degrees(a) + 40 * math.sin(t * 2 + i), t)
    card = P.paper_card(520, 130, seed=41, text='LES OBJECTIFS', size=56)
    P.drop(s.mid, card, 1400, 960, t, w(cue(4, 'suivre')) - 0.2, rot=-2, spin=8, key='obj')
    A.strike(s.mid, (1160, 925, 1640, 995), t, w(cue(4, 'objectifs')) + 0.3, scribble=False)
    return s


COP_XY = (W / 2 - COP_Q.width / 2, 200)


def sG(t, D):
    """L'équipe a abandonné le rôle du policier, adouci les forces de l'ordre et bâti le jeu autour
    de cette liberté."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.0)
    hb = COP_BOX[list(COP_BOX)[0]][0]
    s.push(w(cue(4, 'abandonne')) - 0.4, 0.35, focus=(COP_XY[0] + (hb[0] + hb[2]) / 2, COP_XY[1] + hb[1]), dur=1.4)
    cx, cy = W / 2, COP_XY[1] + COP_Q.height / 2
    P.slide(s.mid, COP_Q, (-COP_Q.width, cy), (cx, cy), t, ENTER, dur=1.0, rot=0.0, lag=5.0, key='copq')
    G.highlight(s.mid, COP_XY, COP_BOX[list(COP_BOX)[0]], t, w(cue(4, 'abandonne')))
    G.typed_quote(s.hud, (W / 2, 870), "« Personne ne veut être le flic, c'est plus drôle d'être méchant. »", t,
                  w(cue(4, 'abandonne')) + 0.4, size=40)
    return s


def sH(t, D):
    """Grand Theft Auto sort au Royaume-Uni à la fin de 1997."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.04, (700, 540))
    P.drop(s.mid, GTA_BOX, 700, 540, t, ENTER, rot=-3, spin=12, key='box')
    TY.big_number(s.top, (1380, 420), '1997', t, w(cue(5, 'Mille')), role='date', label='FIN DE')
    tag(s.hud, (1380, 720), 'ROYAUME-UNI', 50, t, w(cue(5, 'Royaume')))
    return s


def sI(t, D):
    """Contrairement aux jeux d'action de l'époque, construits niveau après niveau, ..."""
    s = Shot(t, D)
    S.env(s, 'grid')
    s.camera(1.0, 1.03)
    for i in range(3):
        card = P.paper_card(380, 220, seed=50 + i, text=f'NIVEAU {i + 1}', size=58)
        P.drop(s.mid, card, 420 + i * 540, 520, t, (ENTER, w(cue(5, 'apres')) - 0.2, w(cue(5, 'niveau', 2)) - 0.1)[i], rot=(-3, 2, -2)[i], spin=8, key=f'niv{i}')
        if i < 2:
            A.connect(s.mid, [(620 + i * 540, 520), (760 + i * 540, 520)], t, w(cue(5, 'apres')) + 0.25 * i, dur=0.4, dots=False)
    return s


def sJ(t, D):
    """... il offre trois villes vues du ciel, inspirées de New York, de Miami et de San Francisco."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.03)
    for i, (card, name, ph) in enumerate(zip(CITIES, ('NEW YORK', 'MIAMI', 'SAN FRANCISCO'), ('New', 'Miami', 'San'))):
        x = 380 + i * 580
        P.drop(s.mid, card, x, 560, t, ENTER + 0.25 * i, rot=(-3, 2, -2)[i], spin=10, key=f'city{i}')
        tag(s.hud, (x, 930), name, 48, t, w(cue(5, ph)))
    return s


def sK(t, D):
    """Le joueur y vole n'importe quelle voiture, change de station de radio et accepte ses
    missions en décrochant des téléphones publics."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.02)
    a, b, c = w(cue(5, 'vole')), w(cue(5, 'change')), w(cue(5, 'decrochant'))
    # 1. any car: the thief's car swerves in and stops
    P.drop(s.mid, GTA1_SHOT, 360, 500, t, ENTER, rot=-3, spin=10, key='g1k')
    # 2. the radio: dropped, then the needle sweeps across the stations
    P.drop(s.mid, G.radio_card(), 960, 500, t, b - 0.25, rot=0, spin=8, height=0.6, key='radio')
    if t > b + 0.5:
        G.radio_needle(s.mid, 960, 500, 0.5 + 0.45 * math.sin((t - b) * 1.6))
    # 3. the payphone: the handset lifts on « décrochant »
    P.drop(s.mid, G.payphone_card(), 1560, 470, t, w(cue(5, 'missions')) - 0.3, rot=2, spin=8, key='phone')
    if t > w(cue(5, 'missions')) + 0.4:
        lift = P.ease_out((t - c) / 0.5) if t > c else 0.0
        hs = G.handset().rotate(-20 * lift, Image.BICUBIC, expand=True)
        P.put(s.mid, hs, 1560 - 175 - 40 * lift, 460 - 60 * lift, lift=lift * 0.4)
    return s


SHOTS = [
    (0.0, sA),
    (cue(4, 'il avait') - LEAD, sC, 'up'),
    (cue(4, 'Avec Race') - LEAD, sD, ('zoom', {'at': (W / 2, H / 2)})),
    (cue(4, 'Le bug') - LEAD, sF, 'cut'),
    (cue(4, 'Le quai') - LEAD, sG, 'rl'),
    (cue(5, 'Grand') - LEAD, sH, 'rl'),
    (cue(5, 'Contrement') - LEAD, sI, 'up'),
    (cue(5, 'il offre') - LEAD, sJ, 'shape'),
    (cue(5, 'Le joueur') - LEAD, sK, 'lr'),
]
END = cue.total + 1.2          # silence before the next act


G.sync(globals())


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
