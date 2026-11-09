"""Acte 2 : Pierre et bois. Narration clips 5-7."""
import sys, math
import numpy as np
from PIL import Image, ImageDraw
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
import maps
import cutout
from style import sfx, ENTER, Shot, words, tag, kicker

CLIPS = (5, 6, 7)
cue = make_cue(CLIPS)


def ink(path, width=None, backed=False):
    """An ink drawing or engraving printed on the film's paper: white -> transparent, lines -> ink."""
    im = Image.open(asset(path)).convert('RGB')
    if width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    a = np.asarray(im).astype(float)
    r = cutout.ink_cut(a, cutout.paper_colour(a), backed)
    return Image.fromarray(r.clip(0, 255).astype(np.uint8), 'RGBA')


# ---- images ----
LAKE_INK = ink('P03.png', 1800)                                      # user's ChatGPT ink drawing
LAKE = Image.open(asset('P03.png'))
SPEAR_PHOTO = Image.open(asset('P02.jpg'))                           # Speer VII (CC BY-SA 3.0 de)
POINT = Image.open(asset('C02.jpg')).crop((185, 120, 730, 840))     # Levallois point (CC BY-SA 3.0)
POINT_CARD = P.print_card(S.treated(POINT), 380, seed=21)
DAGGERS = ink('C03.jpg', 640, backed=True)                           # flint daggers, Wellcome (CC BY 4.0)


def spear_strip(length=1300):
    im = S.treated(SPEAR_PHOTO)
    w_, h_ = im.size
    x0, y0, x1, y1 = (0.45, 0.13, 0.62, 0.95)
    strip = im.crop((int(x0 * w_), int(y0 * h_), int(x1 * w_), int(y1 * h_))).rotate(90, expand=True)
    strip = strip.resize((length, int(strip.height * length / strip.width)), Image.LANCZOS)
    return P.print_card(strip, length, border=10, seed=14)


STRIP = spear_strip()
M = maps.WorldMap(box=(0, 0, W, H))
SCHONINGEN = (10.95, 52.14)


def stone(layer, cx, cy, r, t, start, colour=INK):
    """A rough thrown stone, drawn in ink."""
    if t < start:
        return
    k = P.ease_out(P.clamp01((t - start) / 0.3))
    rng = np.random.default_rng(int(cx))
    pts = [(cx + r * k * (0.8 + 0.3 * rng.random()) * math.cos(a), cy + r * k * (0.7 + 0.25 * rng.random()) * math.sin(a))
           for a in np.linspace(0, 2 * math.pi, 11)[:-1]]
    ImageDraw.Draw(layer).polygon(pts, fill=colour + (255,))


def sA(t, D):
    """Au début, les humains ne disposent ni de griffes puissantes ni de grandes canines."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.05, (W / 2, H / 2), (760, 560))
    P.mask_reveal(s.mid, LAKE_INK, W / 2, H / 2 + 20, t, 0.05, dur=1.8, origin=(0.3, 0.5), lip=False)
    for i, (word, ph) in enumerate((('GRIFFES PUISSANTES', 'griffes'), ('GRANDES CANINES', 'grandes canines'))):
        tag(s.hud, (1480, 110 + i * 90), word, 44, t, w(cue(5, ph)))
        box = A.text_box((1480, 110 + i * 90), word, 44)
        A.strike(s.hud, A.grow(box, 30, -6), t, w(cue(5, ph)) + 0.5)
    kicker(s.hud, t, 2, 'Pierre et bois')
    return s


def sB(t, D):
    """Leur survie dépend de l'observation, de la coopération, de la fuite et de l'usage d'objets trouvés."""
    s = Shot(t, D)
    s.camera(1.0, 1.03)
    words(s.top, (W / 2, 150), 'LEUR SURVIE DÉPEND DE…', 72, t,
          [w(cue(5, x)) for x in ('Leur', 'survie', 'depend', 'depend')])
    items = (("L'OBSERVATION", "l'observation"), ('LA COOPÉRATION', 'cooperation'), ('LA FUITE', 'fuite'), ('OBJETS TROUVÉS', "d'objets"))
    for i, (txt, ph) in enumerate(items):
        card = P.paper_card(640, 170, seed=50 + i, text=txt, size=54)
        x, y = (560, 1360)[i % 2], (430, 720)[i // 2]
        P.drop(s.mid, card, x, y, t, w(cue(5, ph)) - 0.1, rot=(-3, 2, 3, -2)[i], spin=12, key=f'surv{i}')
    return s


def sC(t, D):
    """Une pierre lancée garde un animal à distance. Un bâton prolonge le bras."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, LAKE, t, ENTER, ken=(1.0, 1.0))
    # the camera goes to the stone in the hand, then back out to the spear held at arm's length
    s.zoom_to((900, 720, 1380, 1000), w(cue(5, 'pierre')), dur=1.0, fill=0.9, back_at=w(cue(5, 'Un baton')) - 0.2)
    tag(s.hud, (W / 2, 120), 'UNE PIERRE LANCÉE', 50, t, w(cue(5, 'pierre')))
    tag(s.hud, (W / 2, 200), 'À DISTANCE', 44, t, w(cue(5, 'distance')), bg=S.PAL.cream, fg=INK)
    s.push(w(cue(5, 'prolonge')), 0.10, (560, 420), dur=1.2)
    tag(s.hud, (W / 2, 960), 'UN BÂTON PROLONGE LE BRAS', 50, t, w(cue(5, 'prolonge')))
    return s


def sD(t, D):
    """Le bois disparaît souvent avec le temps, tandis que la pierre demeure. Les traces archéologiques
    donnent donc une image incomplète de ces premiers outils."""
    s = Shot(t, D)
    S.env(s, 'archive')
    s.camera(1.0, 1.03)
    gone = w(cue(5, 'disparait'))
    if t < gone:
        P.put(s.mid, STRIP, 640, 480)
    P.assemble(s.mid, STRIP, 640, 480, t, gone, n=9, reverse=True)
    P.put(s.mid, POINT_CARD, 1500, 470)
    A.ring(s.mid, (1290, 220, 1710, 730), t, w(cue(5, 'demeure')), until=w(cue(5, 'Les traces')))
    words(s.top, (640, 640), 'LE BOIS DISPARAÎT', 60, t, [w(cue(5, x)) for x in ('Le bois', 'bois', 'disparait')])
    words(s.top, (1500, 790), 'LA PIERRE DEMEURE', 60, t, [w(cue(5, x)) for x in ('la pierre', 'pierre', 'demeure')])
    words(s.hud, (W / 2, 960), 'une image incomplète', 50, t,
          [w(cue(5, x)) for x in ('une image', 'image', 'incomplete')], font=F_TYPE)
    return s


def sE(t, D):
    """À Schöningen, en Allemagne, les fouilles de Thieme ont révélé plusieurs armes en bois associées à
    des restes de chevaux."""
    s = Shot(t, D)
    S.env(s, 'cream')
    eu = M.around((10.0, 50.5), 2600)
    near = M.around(SCHONINGEN, 1500)
    a = w(cue(6, 'Allemagne'))
    view = M.zoom(t, [(0.0, eu), (a - 0.2, eu), (a + 1.8, near)])
    M.draw(s.mid, view, t, highlight={'DEU': a})
    M.marker(s.mid, view, SCHONINGEN, 'SCHÖNINGEN', t, w(cue(6, 'fouilles')))
    tag(s.hud, (W / 2, 960), 'PLUSIEURS ARMES EN BOIS', 48, t, w(cue(6, 'plusieurs')))
    return s


def sF(t, D):
    """Les datations longtemps retenues situaient ces objets autour de 300 000 ans. Une étude publiée en
    2025 propose plutôt environ 200 000 ans, une révision qui rappelle que même les objets les plus
    anciens peuvent changer de place dans la chronologie."""
    s = Shot(t, D)
    S.env(s, 'grid')
    s.camera(1.0, 1.03)
    words(s.top, (W / 2, 110), 'LES DATATIONS LONGTEMPS RETENUES', 52, t,
          [w(cue(6, x)) for x in ('Les datations', 'datations', 'longtemps', 'retenues')])
    TY.big_number(s.top, (W / 2, 230), '300 000', t, w(cue(6, '300')), role='stat', label='ANS', colour=INK)
    A.strike(s.top, (520, 300, 1400, 420), t, w(cue(6, '200')), width=12)
    P.stamp_hit(s.mid, 'ÉTUDE 2025', 1640, 470, t, w(cue(6, '2025')), size=56, ang=-8, shot=s)
    TY.big_number(s.top, (W / 2, 560), '200 000', t, w(cue(6, '200')), role='stat', label='ANS · RÉVISION', colour=S.accent(s))
    return s


def sH(t, D):
    """Ces vestiges indiquent une chasse organisée, qui exigeait anticipation et coopération."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, SPEAR_PHOTO.rotate(90, expand=True), t, ENTER, ken=(1.04, 1.14), focus=(0.5, 0.5), focus_to=(0.45, 0.4), darken=0.3)
    tag(s.hud, (W / 2, 860), 'UNE CHASSE ORGANISÉE', 56, t, w(cue(6, 'chasse')))
    tag(s.hud, (640, 960), 'ANTICIPATION', 44, t, w(cue(6, 'anticipation')), bg=S.PAL.cream, fg=INK)
    tag(s.hud, (1280, 960), 'COOPÉRATION', 44, t, w(cue(6, 'cooperation')), bg=S.PAL.cream, fg=INK)
    return s


def sI(t, D):
    """La pointe transforme ensuite le bâton en outil spécialisé."""
    s = Shot(t, D)
    s.camera(1.0, 1.04, (W / 2, H / 2), (1300, 480))
    P.slide(s.mid, STRIP, (-800, 480), (760, 480), t, ENTER, dur=1.0, rot=0.0, lag=6.0, key='stripI')
    P.drop(s.mid, POINT_CARD, 1560, 470, t, w(cue(7, 'pointe')), rot=-90 + 4, spin=10, key='ptI')
    A.ring(s.mid, (1330, 250, 1790, 690), t, w(cue(7, 'outil')))
    words(s.top, (W / 2, 830), 'UN OUTIL SPÉCIALISÉ', 90, t, [w(cue(7, x)) for x in ('en outil', 'outil', 'specialise')])
    return s


def sJ(t, D):
    """Les humains associent le bois à des éléments de pierre taillée, tandis que les lames de pierre
    annoncent des formes de couteaux et de poignards."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.03)
    P.put(s.mid, P.rot_scale(POINT_CARD, -4, 0.8, key='ptJ'), 420, 380)
    words(s.top, (420, 640), 'BOIS + PIERRE TAILLÉE', 54, t,
          [w(cue(7, x)) for x in ('le bois', 'bois', 'pierre taillee', 'taillee')])
    P.slide(s.mid, DAGGERS, (W + 500, 520), (1340, 500), t, w(cue(7, 'les lames')) - 0.1, dur=1.1, rot=2, key='dagJ')
    words(s.top, (1340, 980), 'COUTEAUX · POIGNARDS', 54, t, [w(cue(7, 'couteaux')), w(cue(7, 'couteaux')), w(cue(7, 'poignards'))])
    return s


def sK(t, D):
    """Le principe est simple. Une matière dure concentre l'effort sur une petite surface."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.0)
    big = P.print_card(S.treated(POINT), 470, seed=22)
    P.put(s.mid, big, 1240, 560)
    s.push(w(cue(7, 'petite')), 0.18, (1240, 330), dur=1.2)
    words(s.top, (520, 300), 'LE PRINCIPE', 76, t, [w(cue(7, 'Le principe')), w(cue(7, 'principe'))])
    words(s.top, (520, 400), 'EST SIMPLE', 76, t, [w(cue(7, 'est simple')), w(cue(7, 'simple'))])
    words(s.hud, (520, 620), 'une matière dure', 48, t, [w(cue(7, x)) for x in ('Une matiere', 'matiere', 'dure')], font=F_TYPE)
    words(s.hud, (520, 690), "concentre l'effort", 48, t, [w(cue(7, 'concentre')), w(cue(7, "l'effort"))], font=F_TYPE)
    A.ring(s.mid, (1160, 250, 1320, 420), t, w(cue(7, 'petite')))
    words(s.hud, (520, 820), 'UNE PETITE SURFACE', 64, t, [w(cue(7, 'petite')), w(cue(7, 'petite surface')), w(cue(7, 'surface'))], fill=S.PAL.accent)
    return s


def sL(t, D):
    """Mais les matériaux et les savoir-faire varient selon les régions. Il n'existe pas une seule ligne
    d'évolution, identique partout."""
    s = Shot(t, D)
    S.env(s, 'cream')
    M.draw(s.mid, M.WORLD, t, ENTER, alpha=0.55)
    tag(s.hud, (600, 140), 'LES MATÉRIAUX', 44, t, w(cue(7, 'materiaux')))
    tag(s.hud, (1320, 140), 'LES SAVOIR-FAIRE', 44, t, w(cue(7, 'savoir')))
    words(s.top, (W / 2, 240), 'VARIENT SELON LES RÉGIONS', 56, t, [w(cue(7, x)) for x in ('varient', 'selon', 'les regions', 'regions')])
    l0 = w(cue(7, 'Il'))
    A.arrow(s.top, (300, 620), (1620, 620), t, l0, dur=0.8, bend=0.0, colour=INK, width=10)
    words(s.top, (W / 2, 660), 'UNE SEULE LIGNE', 60, t, [w(cue(7, x)) for x in ('une seule', 'seule', 'ligne')])
    A.strike(s.top, (260, 580, 1680, 740), t, w(cue(7, 'identique')), scribble=True)
    return s


SHOTS = [
    (0.0, sA),
    (cue(5, 'Leur') - LEAD, sB, 'up'),
    (cue(5, 'Une pierre') - LEAD, sC, 'lr'),
    (cue(5, 'Le bois') - LEAD, sD, 'pageturn'),
    (cue(6, 'A Schoningen') - LEAD, sE, ('circle', {'at': (W / 2, H / 2)})),
    (cue(6, 'Les datations') - LEAD, sF, 'rl'),
    (cue(6, 'Ces vestiges') - LEAD, sH, ('zoom', {'at': (W / 2, H / 2)})),
    (cue(7, 'La pointe') - LEAD, sI, 'up'),
    (cue(7, 'Les humains') - LEAD, sJ, 'lr'),
    (cue(7, 'Le principe') - LEAD, sK, 'shape'),
    (cue(7, 'Mais') - LEAD, sL, 'rl'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
