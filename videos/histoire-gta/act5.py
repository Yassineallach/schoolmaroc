"""Acte 5 : Le phénomène. Narration clips 10-12."""
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

CLIPS = (10, 11, 12)
cue = make_cue(CLIPS)

# ---- real material (SOURCES.md)
VC = lambda n: Image.open(asset(f'game/steam/vicecity_{n}.jpg'))                   # official Vice City screenshots (Steam)
SA = lambda n: Image.open(asset(f'game/steam/sanandreas_{n}.jpg'))                 # official San Andreas screenshots (Steam)
VC_LOGO = P.load(asset('G04_vicecity.png'), width=520)
SA_LOGO = P.load(asset('G05_sanandreas.png'), width=520)
SA_BOX = P.print_card(Image.open(asset('game/wikipedia/b05_sa_box.jpg')), 460, seed=51)
TOMMY = P.print_card(VC(6), 760, seed=52)
LIOTTA = P.print_card(Image.open(asset('P06_liotta.jpg')), 380, seed=53)          # Georges Biard, CC BY-SA 3.0
THOMPSON = P.print_card(Image.open(asset('P07_thompson.jpg')), 400, seed=54)      # Commons (Flickr)
CJ = P.print_card(SA(7), 760, seed=55)
VCQ, VCQ_BOX = G.article('A11_vc_head.png', 'A11_vc_q.png', 'IGN', '25 OCTOBRE 2002', width=1150, seed=56)
JT, JT_BOX = G.article('A12_jt_head.png', 'A12_jt_q.png', 'Game Developer', '25 SEPTEMBRE 2008', width=1150, seed=57)
ES, ES_BOX = G.article('A14_esrb_head.png', 'A14_esrb_q.png', 'ESRB · communiqué', '20 JUILLET 2005', width=1400, seed=58)
APA, APA_BOX = G.article('A15_apa_head.png', 'A15_apa_body.png', 'American Psychological Association', '3 MARS 2020', width=1050, seed=59)


def into(s, xy, card, boxes, at, dur=1.1, above=200):
    """Camera into the highlighted lines of an article placed at xy."""
    y0 = min(b[1] for b in boxes); y1 = max(b[3] for b in boxes)
    s.zoom_to((xy[0] - 10, xy[1] + y0 - above, xy[0] + card.width + 10, xy[1] + y1 + 70), at, dur=dur, fill=0.95)


def sA(t, D):
    """Rockstar transforme ensuite le succès en phénomène culturel."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, VC(3), t, -1.0, ken=(1.0, 1.08), focus=(0.5, 0.5), darken=0.3, fade=0.01)
    kicker(s.hud, t, 5, 'Le phénomène')
    return s


def sB(t, D):
    """Vice City, en 2002, plonge le joueur dans une Miami de 1986."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, VC(9), t, -1.0, ken=(1.02, 1.12), focus=(0.5, 0.5), darken=0.35, fade=0.01)
    P.drop(s.mid, VC_LOGO, W / 2, 420, t, ENTER, rot=0, spin=6, height=0.8, key='vcl')
    tag(s.hud, (W / 2 - 230, 900), '2002', 60, t, w(cue(10, 'en', 1)))
    tag(s.hud, (W / 2 + 170, 900), 'MIAMI, 1986', 60, t, w(cue(10, 'Miami')), bg=G.THIEF, fg=INK)
    return s


def sC(t, D):
    """Son héros, Tommy Vercetti, est le premier personnage de la série à parler, ..."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.03, (700, 540))
    P.drop(s.mid, TOMMY, 640, 520, t, ENTER, rot=-2, spin=10, key='tommy')
    TY.name_card(s.top, (1080, 360), 'Tommy Vercetti', 'LE HÉROS DE VICE CITY', t, w(cue(10, 'Tommy')))
    words(s.hud, (1380, 640), 'le premier à parler', 52, t, [w(cue(10, x)) for x in ('heros', 'Tommy', 'premier', 'personnage')], font=F_TYPE)
    return s


VCQ_XY = (700, 300)


def sD(t, D):
    """... avec la voix de l'acteur Ray Liotta, ..."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.0)
    P.drop(s.mid, LIOTTA, 330, 540, t, ENTER, rot=-3, spin=10, key='liotta')
    cy = VCQ_XY[1] + VCQ.height / 2
    P.slide(s.mid, VCQ, (W + VCQ.width, cy), (VCQ_XY[0] + VCQ.width / 2, cy), t, ENTER + 0.15, dur=0.8, rot=0.0, lag=4.0, key='vcq')
    G.highlight(s.mid, VCQ_XY, VCQ_BOX[list(VCQ_BOX)[0]], t, w(cue(10, 'voix')) - 0.2)
    into(s, VCQ_XY, VCQ, VCQ_BOX[list(VCQ_BOX)[0]], ENTER + 0.4, dur=0.8)
    tag(s.hud, (W / 2, 990), 'RAY LIOTTA, LA VOIX DE TOMMY VERCETTI', 46, t, ENTER + 0.2)
    return s


def sE(t, D):
    """... et l'histoire emprunte ouvertement à Scarface et à Miami Vice."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, VC(8), t, -1.0, ken=(1.0, 1.06), focus=(0.5, 0.5), darken=0.45, fade=0.01)
    for i, (txt, ph) in enumerate((('SCARFACE', 'Scarface'), ('MIAMI VICE', 'Vice'))):
        card = P.paper_card(620, 170, seed=60 + i, text=txt, size=80)
        P.drop(s.mid, card, 560 + i * 800, 540, t, w(cue(10, ph, 1 if i == 0 else 2)) - 0.15, rot=(-4, 3)[i], spin=10, key=f'film{i}')
    return s


def sF(t, D):
    """Deux ans plus tard, San Andreas ramène Carl Johnson, dit CJ, dans son quartier de Grove
    Street en 1992."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, SA(9), t, -1.0, ken=(1.0, 1.08), focus=(0.5, 0.45), darken=0.35, fade=0.01)
    P.drop(s.mid, SA_LOGO, W / 2, 330, t, w(cue(10, 'San')) - 0.1, rot=0, spin=6, height=0.8, key='sal')
    tag(s.hud, (W / 2, 640), 'CARL JOHNSON, DIT CJ', 54, t, w(cue(10, 'Carl')))
    tag(s.hud, (W / 2, 900), 'GROVE STREET, 1992', 60, t, w(cue(10, 'Grove')), bg=G.THIEF, fg=INK)
    return s


def sG(t, D):
    """Le joueur gère sa nourriture, son entraînement et ses vêtements, comme dans un jeu de rôle."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.03)
    P.drop(s.mid, CJ, 520, 500, t, ENTER, rot=-2, spin=10, key='cj')
    for i, (txt, ph) in enumerate((('NOURRITURE', 'nourriture'), ('ENTRAÎNEMENT', 'entrainement'), ('VÊTEMENTS', 'vetements'))):
        card = P.paper_card(560, 140, seed=70 + i, text=txt, size=64)
        P.drop(s.mid, card, 1400, 300 + i * 220, t, w(cue(10, ph)) - 0.15, rot=(-3, 2, -2)[i], spin=8, key=f'rpg{i}')
    return s


def sH(t, D):
    """San Andreas devient le jeu le plus vendu de l'histoire de la PlayStation 2."""
    s = Shot(t, D)
    S.env(s, 'grid')
    s.camera(1.0, 1.03, (W / 2, 540))
    P.drop(s.mid, SA_BOX, 330, 540, t, ENTER, rot=-3, spin=10, key='sab')
    a, b = w(cue(10, 'deviant')), w(cue(10, 'PlayStation'))
    line1 = 'LE JEU LE PLUS VENDU'
    line2 = "DE L'HISTOIRE DE LA PLAYSTATION 2"
    n1, n2 = len(line1.split()), len(line2.split())
    k = (b - a) / (n1 + n2 - 1)
    words(s.top, (1250, 400), line1, 72, t, [a + k * i for i in range(n1)])
    words(s.top, (1250, 520), line2, 54, t, [a + k * (n1 + i) for i in range(n2)])
    return s


def sI(t, D):
    """Le succès attire aussi les procès."""
    s = Shot(t, D)
    S.env(s, 'charcoal', mood='tense')
    s.camera(1.03, 1.0)
    words(s.top, (W / 2, 450), 'LE SUCCÈS', 120, t, [ENTER, w(cue(11, 'succes'))], fill=S.ink(s))
    words(s.top, (W / 2, 610), 'ATTIRE LES PROCÈS', 100, t, [w(cue(11, x)) for x in ('attire', 'les', 'proces')], fill=S.accent(s))
    return s


JT_XY = (650, 300)


def sJ(t, D):
    """L'avocat américain Jack Thompson mène une longue campagne contre l'éditeur, jusqu'à sa
    radiation du barreau en 2008."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.0)
    P.drop(s.mid, THOMPSON, 330, 520, t, ENTER, rot=-3, spin=10, key='jt')
    cy = JT_XY[1] + JT.height / 2
    P.slide(s.mid, JT, (W + JT.width, cy), (JT_XY[0] + JT.width / 2, cy), t, ENTER + 0.15, dur=0.8, rot=0.0, lag=4.0, key='jtq')
    G.highlight(s.mid, JT_XY, JT_BOX[list(JT_BOX)[0]], t, w(cue(11, 'radiation')))
    into(s, JT_XY, JT, JT_BOX[list(JT_BOX)[0]], w(cue(11, 'jusqu')))
    tag(s.hud, (W / 2, 990), 'JACK THOMPSON, AVOCAT', 46, t, w(cue(11, 'Jack')))
    return s


def sK(t, D):
    """Mais le coup le plus dur vient de l'intérieur."""
    s = Shot(t, D)
    S.env(s, 'charcoal', mood='menace')
    s.camera(1.03, 1.0)
    phr = ('Mais', 'le coup', 'coup', 'le plus', 'plus', 'dur', 'vient', 'de l', "'interieur")
    S.type_page(s, "Mais le coup le plus dur vient de l'intérieur.", t, ENTER, role='statement', size=92,
                cues=[w(cue(11, x)) for x in phr])
    return s


def sL(t, D):
    """En juillet 2005, des joueurs découvrent sur le disque de San Andreas une scène sexuelle
    inachevée, débloquable par une modification amateur nommée Hot Coffee."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.04, (W / 2, 540))
    P.drop(s.mid, SA_BOX, 520, 540, t, ENTER, rot=3, spin=10, key='sab2')
    tag(s.hud, (1330, 260), 'JUILLET 2005', 56, t, w(cue(11, 'juillet')))
    words(s.top, (1330, 560), '« HOT COFFEE »', 110, t, [w(cue(11, 'Hot'))] * 2, fill=S.accent(s))
    return s


ES_XY = (W / 2 - ES.width / 2, 170)


def sM(t, D):
    """L'organisme américain de classification, l'ESRB, retire au jeu son classement réservé aux plus
    de 17 ans et le classe pour adultes uniquement. Rockstar demande aux magasins d'en suspendre la
    vente."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.0)
    cy = ES_XY[1] + ES.height / 2
    P.slide(s.mid, ES, (W + ES.width, cy), (W / 2, cy), t, ENTER, dur=0.8, rot=0.0, lag=4.0, key='es')
    keys = list(ES_BOX)
    rk = [k for k in keys if k.startswith('immediate')][0]
    sk = [k for k in keys if k.startswith('will')][0]
    G.highlight(s.mid, ES_XY, ES_BOX[rk], t, w(cue(11, 'retire')))
    P.stamp_hit(s.mid, 'AO · ADULTES UNIQUEMENT', W / 2, ES_XY[1] + ES.height + 40, t, w(cue(11, 'adultes')), size=72, ang=-5, shot=s)
    into(s, ES_XY, ES, ES_BOX[rk] + ES_BOX[sk], w(cue(11, 'classification')), above=120)
    G.highlight(s.mid, ES_XY, ES_BOX[sk], t, w(cue(11, 'Rockstar')))
    G.typed_quote(s.hud, (W / 2, 960), '« Rockstar va demander aux magasins de cesser toute vente du jeu. »', t,
                  w(cue(11, 'Rockstar')), size=40, cps=40)
    return s


def sN(t, D):
    """Ces affaires relancent un débat ancien : les jeux vidéo violents rendent-ils violents ?"""
    s = Shot(t, D)
    S.env(s, 'charcoal', mood='tense')
    s.camera(1.03, 1.0)
    words(s.top, (W / 2, 330), 'UN DÉBAT ANCIEN', 70, t, [ENTER, ENTER + 0.25, w(cue(12, 'ancien'))], fill=S.ink(s))
    S.type_page(s, 'Les jeux vidéo violents rendent-ils violents ?', t, w(cue(12, 'les')), role='statement', size=86,
                xy=(W / 2, 560), cues=[w(cue(12, x)) for x in ('les', 'jeux', 'video', 'violents', 'rendent', "-ils", 'violents', 'violents')][:3] + [w(cue(12, 'violents')), w(cue(12, 'rendent')), w(cue(12, 'violents', 2)), w(cue(12, 'violents', 2))])
    return s


APA_XY = (W / 2 - APA.width / 2, 90)


def sO(t, D):
    """En 2020, l'Association américaine de psychologie a conclu que les preuves restaient
    insuffisantes pour relier ces jeux à des comportements violents, même si un lien avec une
    agressivité légère existe."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.0)
    cy = APA_XY[1] + APA.height / 2
    P.slide(s.mid, APA, (-APA.width, cy), (W / 2, cy), t, ENTER, dur=0.8, rot=0.0, lag=4.0, key='apa')
    k1 = [k for k in APA_BOX if k.startswith('There')][0]
    k2 = [k for k in APA_BOX if k.startswith('there')][0]
    G.highlight(s.mid, APA_XY, APA_BOX[k1], t, w(cue(12, 'preuves')))
    G.highlight(s.mid, APA_XY, APA_BOX[k2], t, w(cue(12, 'meme')), colour=(170, 200, 230))
    into(s, APA_XY, APA, APA_BOX[k1] + APA_BOX[k2], w(cue(12, "'Association")), above=100)
    tag(s.hud, (W / 2, 1010), '2020 · PREUVES INSUFFISANTES', 46, t, w(cue(12, 'insuffisantes')))
    return s


def sP(t, D):
    """Entre-temps, chaque scandale avait fait connaître GTA bien au-delà des joueurs."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.05, 1.0)
    for i, (card, x, y, r) in enumerate(((JT, 420, 330, -6), (ES, 1300, 300, 4), (APA, 700, 700, -2), (VCQ, 1450, 760, 5))):
        small = card.resize((int(card.width * 0.55), int(card.height * 0.55)), Image.LANCZOS)
        P.drop(s.mid, small, x, y, t, ENTER + 0.25 * i, rot=r, spin=10, key=f'col{i}')
    return s


SHOTS = [
    (0.0, sA),
    (cue(10, 'Vice') - LEAD, sB, 'cut'),
    (cue(10, 'Son') - LEAD, sC, 'lr'),
    (cue(10, 'avec la') - LEAD, sD, 'up'),
    (cue(10, 'ouvertement') - LEAD, sE, 'rl'),
    (cue(10, 'Deux') - LEAD, sF, 'lr'),
    (cue(10, 'Le joueur', 2) - LEAD, sG, 'lr'),
    (cue(10, 'San', 2) - LEAD, sH, 'up'),
    (cue(11, 'Le succes') - LEAD, sI, 'pageturn'),
    (cue(11, "L 'avocat") - LEAD, sJ, 'rl'),
    (cue(11, 'Mais') - LEAD, sK, 'cut'),
    (cue(11, 'En juillet') - LEAD, sL, 'lr'),
    (cue(11, "L 'organisme") - LEAD, sM, 'up'),
    (cue(12, 'debat') - LEAD, sN, 'pageturn'),
    (cue(12, 'En 2020') - LEAD, sO, 'rl'),
    (cue(12, 'Entre') - LEAD, sP, 'shape'),
]
END = cue.total + 1.2


G.sync(globals())


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
