"""Acte 6 : La force invisible. Narration clips 15-16."""
import sys, os
from PIL import Image, ImageDraw
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import annotate as A
import scenes as S
import typo as TY
import cutout
from style import sfx, ENTER, Shot, words, tag, kicker

CLIPS = (15, 16)
cue = make_cue(CLIPS)

# ---- images (credits in assets/credits.json) ----
HAND = Image.open(asset('P13.png'))                                    # user's ChatGPT ink drawing
HAND_INK = cutout.ink_image(asset('P13.png'), 1800)
LAKE_INK = cutout.ink_image(asset('P03.png'), 900)
SABRE = Image.open(asset('C08.jpg'))                                   # Mameluke officer sabre
SPEAR = Image.open(asset('P02.jpg'))                                    # Speer VII
HAS_DRONE = os.path.exists(asset('P12.jpg'))
DRONE = Image.open(asset('P12.jpg')) if HAS_DRONE else None             # real drone photo (pending)

SABRE_CARD = P.print_card(S.treated(SABRE), 820, border=10, seed=71)
SPEAR_CARD = P.print_card(S.treated(SPEAR).crop((430, 180, 600, 1300)).rotate(90, expand=True), 820, border=10, seed=72)
ICRC = document(760, 640, ['Comité international de la Croix-Rouge', '---', 'cette délégation peut rendre', 'les effets plus difficiles',
                           'à prévoir et à contrôler', '---', '---'], seed=12, title='AVERTISSEMENT', typed=True, body_size=34)


def grid_target(layer, cx, cy, t, start, colour=INK):
    """A cold classification box: corners closing on a point, the 'cible' of a system."""
    A.corners(layer, (cx - 120, cy - 120, cx + 120, cy + 120), t, start, colour=colour, width=6, arm=40)


def sA(t, D):
    """Cette séparation entre symbole et fonction prend une forme nouvelle avec les systèmes automatisés."""
    s = Shot(t, D)
    S.env(s, 'geometric')
    s.camera(1.0, 1.03)
    S.split(s, S.treated(SABRE.crop((1180, 0, 1920, 558))), S.treated(SPEAR).rotate(90, expand=True), t, ENTER, divide='tear')
    tag(s.hud, (480, 120), 'SYMBOLE', 56, t, w(cue(15, 'symbole')))
    tag(s.hud, (1440, 120), 'FONCTION', 56, t, w(cue(15, 'fonction')))
    tag(s.hud, (W / 2, 960), 'LES SYSTÈMES AUTOMATISÉS', 52, t, w(cue(15, 'automatises')), bg=S.PAL.cream, fg=INK)
    kicker(s.hud, t, 6, 'La force invisible')
    return s


def sB(t, D):
    """Certains dispositifs militaires peuvent détecter, sélectionner ou engager des cibles selon leur degré
    d'autonomie."""
    s = Shot(t, D)
    S.env(s, 'grid')
    s.camera(1.0, 1.02)
    steps = (('DÉTECTER', 'detecter'), ('SÉLECTIONNER', 'selectionner'), ('ENGAGER', 'engager'))
    for i, (word, ph) in enumerate(steps):
        x = 360 + i * 600
        grid_target(s.mid, x, 430, t, w(cue(15, ph)) - 0.1)
        words(s.top, (x, 620), word, 64, t, w(cue(15, ph)))
        if i:
            A.arrow(s.mid, (x - 470, 430), (x - 140, 430), t, w(cue(15, ph)) - 0.2, dur=0.35, bend=0.0, colour=INK, width=6, head=20)
    words(s.top, (W / 2, 140), 'CERTAINS DISPOSITIFS', 64, t, [w(cue(15, 'Certains')), w(cue(15, 'dispositifs'))])
    words(s.hud, (W / 2, 880), "selon leur degré d'autonomie", 48, t,
          [w(cue(15, x)) for x in ('selon', 'leur', 'degre', 'autonomie')], font=F_TYPE)
    return s


def sC(t, D):
    """Tous les drones armés ne sont pas autonomes."""
    s = Shot(t, D)
    if HAS_DRONE:
        S.env(s, 'bleed')
        S.fullbleed(s, DRONE, t, ENTER, ken=(1.0, 1.08), focus=(0.5, 0.55), darken=0.0)
    else:
        S.env(s, 'cream')
        s.camera(1.0, 1.03)
    ty = 380 if not HAS_DRONE else 70
    words(s.top, (W / 2, ty), 'TOUS LES DRONES ARMÉS', 92, t,
          [w(cue(15, x)) for x in ('Tous', 'les drones', 'drones', 'armes')], fill=INK)
    tag(s.hud, (W / 2, 620 if not HAS_DRONE else 980), 'NE SONT PAS AUTONOMES', 64, t, w(cue(15, 'autonomes')))
    A.strike(s.top, A.grow(A.words_box((W / 2, ty), 'TOUS LES DRONES ARMÉS', 92, 'TOUS'), 14, -30), t, w(cue(15, 'ne sont')), width=10)
    return s


def sD(t, D):
    """La distinction dépend de la capacité d'un système à choisir lui-même une cible et à appliquer la force."""
    s = Shot(t, D)
    S.env(s, 'cream')
    s.camera(1.0, 1.03)
    TY.term_card(s.top, (200, 300), 'AUTONOMIE', 'choisir lui-même une cible et appliquer la force', t, w(cue(15, 'distinction')), width=1100)
    grid_target(s.mid, 1560, 640, t, w(cue(15, 'cible')))
    tag(s.hud, (1560, 820), 'LUI-MÊME', 46, t, w(cue(15, 'lui')))
    return s


def sE(t, D):
    """Le Comité international de la Croix-Rouge avertit que cette délégation peut rendre les effets plus
    difficiles à prévoir et à contrôler."""
    s = Shot(t, D)
    S.env(s, 'archive')
    s.camera(1.0, 1.03, (W / 2, 520), (1100, 520))
    P.unfold(s.mid, ICRC, 1100, 520, t, ENTER, dur=1.2)
    A.ring(s.mid, (850, 528, 1000, 588), t, w(cue(15, 'prevoir')))
    A.ring(s.mid, (1040, 528, 1225, 588), t, w(cue(15, 'controler')))
    words(s.hud, (380, 300), 'LE CICR', 72, t, [w(cue(15, 'Le Comite')), w(cue(15, 'Comite'))])
    words(s.hud, (380, 390), 'avertit', 48, t, w(cue(15, 'avertit')), font=F_TYPE)
    return s


def sF(t, D):
    """La décision s'éloigne alors de la personne qui en subit les conséquences."""
    s = Shot(t, D)
    S.env(s, 'geometric')
    s.camera(1.0, 1.03)
    d0 = w(cue(15, "s'eloigne"))
    k = P.ease_out(P.clamp01((t - d0) / 1.8))
    xa, xb = 860 - 520 * k, 1060 + 520 * k
    d = ImageDraw.Draw(s.mid)
    for x, label in ((xa, 'LA DÉCISION'), (xb, 'LES CONSÉQUENCES')):
        d.ellipse((x - 44, 520 - 44, x + 44, 520 + 44), outline=S.ink(s) + (255,), width=7)
        TY.Text(label, 'label', colour=S.ink(s)).draw(s.mid, (x, 590), t, ENTER, anchor='m', sound=False)
    A.connect(s.mid, [(xa + 60, 520), (xb - 60, 520)], t, ENTER + 0.2, dur=0.4, arrowhead=False, dots=False, colour=S.accent(s))
    words(s.top, (W / 2, 220), "LA DÉCISION S'ÉLOIGNE", 84, t,
          [w(cue(15, x)) for x in ('La decision', 'decision', "s'eloigne")], fill=S.ink(s))
    return s


def sG(t, D):
    """Pendant des millénaires, une arme prolongeait le corps et rendait visible celui qui l'employait."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.0)
    P.mask_reveal(s.mid, HAND_INK, W / 2, H / 2, t, 0.05, dur=1.8, origin=(0.5, 0.45), lip=False)
    s.push(w(cue(16, 'prolongeait')), 0.10, (840, 480), dur=2.2)
    words(s.hud, (W / 2, 70), 'pendant des millénaires', 46, t, [w(cue(16, x)) for x in ('Pendant', 'des', 'millenaires')], font=F_TYPE)
    tag(s.hud, (560, 990), 'PROLONGEAIT LE CORPS', 46, t, w(cue(16, 'prolongeait')))
    tag(s.hud, (1360, 990), 'RENDAIT VISIBLE', 46, t, w(cue(16, 'visible')), bg=S.PAL.cream, fg=INK)
    return s


def sH(t, D):
    """Aujourd'hui, la force peut être déclenchée à distance, par des systèmes dont les décisions restent
    difficiles à expliquer."""
    s = Shot(t, D)
    S.env(s, 'charcoal')
    s.camera(1.03, 1.0)
    phr = ("Aujourd'hui", 'la force', 'force', 'peut', 'etre', 'declenchee', 'a', 'distance')
    S.type_page(s, "Aujourd'hui, la force peut être déclenchée à distance", t, ENTER, role='statement', size=78, xy=(W / 2, 330),
                cues=[w(cue(16, x)) for x in phr], accent={'distance': w(cue(16, 'distance')) + 0.1})
    words(s.hud, (W / 2, 720), 'des décisions difficiles à expliquer', 48, t,
          [w(cue(16, x)) for x in ('des systemes', 'decisions', 'difficiles', 'a expliquer', 'expliquer')], font=F_TYPE, fill=S.ink(s))
    return s


def sI(t, D):
    """Entre la main qui tenait le bois au bord d'un lac et l'algorithme qui classe une cible ..."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    right = Image.new('RGB', (1000, 1080), S.PAL.cream)
    S.split(s, HAND, right, t, ENTER, divide='tear')
    for i, y in enumerate(range(200, 900, 120)):
        for j, x in enumerate(range(1080, 1840, 120)):
            grid_target(s.mid, x + 60, y + 60, t, w(cue(16, "l'algorithme")) + 0.03 * (i + j)) if (i + j) % 3 == 0 else None
    tag(s.hud, (480, 100), 'LA MAIN', 52, t, w(cue(16, 'main')))
    tag(s.hud, (1440, 100), "L'ALGORITHME", 52, t, w(cue(16, "l'algorithme")))
    return s


def sJ(t, D):
    """... demeure une question : qui répond de la force, quand celui qui l'exerce devient invisible ?"""
    s = Shot(t, D)
    S.env(s, 'charcoal', mood='mystery')
    s.camera(1.03, 1.0)
    P.put(s.mid, P.print_card(S.treated(Image.open(asset('P03.png'))), 620, seed=73), W / 2, 220)
    phr = ('qui', 'repond', 'de la', 'force', 'quand', 'celui', 'qui', "l'exerce", 'devient', 'invisible')
    times = [w(cue(16, 'qui', 2)), w(cue(16, 'repond')), w(cue(16, 'de la')), w(cue(16, 'force', 2)), w(cue(16, 'quand')),
             w(cue(16, 'celui')), w(cue(16, 'qui', 3)), w(cue(16, "l'exerce")), w(cue(16, 'devient')), w(cue(16, 'invisible'))]
    S.type_page(s, "Qui répond de la force, quand celui qui l'exerce devient invisible ?", t, ENTER, role='statement', size=74,
                xy=(W / 2, 560), max_w=1500, cues=times, accent={'invisible': w(cue(16, 'invisible')) + 0.2})
    words(s.hud, (W / 2, 470), 'demeure une question', 44, t, [w(cue(16, x)) for x in ('demeure', 'une question', 'question')],
          font=F_TYPE, fill=S.ink(s))
    return s


SHOTS = [
    (0.0, sA),
    (cue(15, 'Certains') - LEAD, sB, 'up'),
    (cue(15, 'Tous') - LEAD, sC, 'lr'),
    (cue(15, 'La distinction') - LEAD, sD, 'rl'),
    (cue(15, 'Le Comite') - LEAD, sE, 'pageturn'),
    (cue(15, 'La decision') - LEAD, sF, 'shape'),
    (cue(16, 'Pendant') - LEAD, sG, ('circle', {'at': (W / 2, H / 2)})),
    (cue(16, "Aujourd'hui") - LEAD, sH, 'lr'),
    (cue(16, 'Entre') - LEAD, sI, 'up'),
    (cue(16, 'demeure') - LEAD, sJ, 'lr'),
]
END = cue.total + 3.0


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
