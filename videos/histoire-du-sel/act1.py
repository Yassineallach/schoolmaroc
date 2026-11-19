"""Acte 1 : Le besoin. Narration clips 1-3.

Text rule for this film (the user's): as few kinetic-text moments as possible. Pictures carry the
narration; the only animated type in this act is « NaCl » on « chlorure de sodium ». Photo captions
are small and static.
"""
import os
import sys
from PIL import Image, ImageDraw
from vox import *  # noqa: F401,F403
import style as st
import presets as P
import scenes as S
import cutout
from style import ENTER, Shot, words, caption

CLIPS = (1, 2, 3)
cue = make_cue(CLIPS)


def placeholder(label, size=(1600, 1000)):
    """Labelled stand-in for an image still to come from Commons (swapped in when assets/<code> exists)."""
    im = Image.new('RGB', size, S.PAL.paper2)
    d = ImageDraw.Draw(im)
    d.rectangle((8, 8, size[0] - 9, size[1] - 9), outline=INK, width=6)
    d.text((size[0] / 2, size[1] / 2), label, font=F_HEAD(64), fill=INK, anchor='mm')
    return im


def img(code, label, size=(1600, 1000)):
    for ext in ('.jpg', '.png'):
        if os.path.exists(asset(code + ext)):
            return Image.open(asset(code + ext)).convert('RGB')
    return placeholder(f'{code} · {label}', size)


# ---- real images (Wikimedia Commons, credits in assets/credits.json)
GOATS = Image.open(asset('A01.jpg'))            # Mountain Goat Family, Olympic (NPS, public domain)
TRAIL = Image.open(asset('A02.jpg'))            # mountain goats and kids on a trail (NPS, public domain)
BILLY = Image.open(asset('A03.jpg'))            # male billy goat, Klahhane Ridge (NPS, public domain)
HIKERS = img('H2', 'randonneurs, Olympic')
HELI = img('H1', 'chèvre évacuée par hélicoptère')
HALITE = img('H5', 'cristaux de sel (halite)', (1000, 1400))
NEURON = img('H3', 'neurones, Ramón y Cajal', (1100, 1300))
STOMACH = img('H4', 'estomac, gravure', (1600, 1050))

TRAIL_CARD = P.print_card(S.treated(TRAIL), 1180, seed=11)
HIKERS_CARD = P.print_card(S.treated(HIKERS), 1100, seed=12)
HALITE_CARD = P.print_card(S.treated(HALITE), 900, seed=13)
def _clean_paper(im, crop):
    """Lift the old paper tone to white so only Cajal's ink lines are kept."""
    from PIL import ImageOps
    g = ImageOps.grayscale(im.crop(crop))
    g = g.point(lambda v: 255 if v > 150 else int(v * 255 / 150))
    return g.convert('RGB')


NEURON_INK = (cutout.ink_image(_clean_paper(NEURON, (140, 12, NEURON.width - 30, NEURON.height - 10)), 640)
              if os.path.exists(asset('H3.jpg')) else NEURON)
STOMACH_CARD = P.print_card(S.treated(STOMACH), 600, seed=14)   # 1686 engraving (Wellcome Collection)


def sA(t, D):
    """En 2018, le parc national Olympic, aux États-Unis, avait un problème de chèvres.
    (Hook: the strongest image, full frame, nothing before it.)"""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, GOATS, t, 0.0, ken=(1.0, 1.07), focus=(0.55, 0.5), focus_to=(0.6, 0.55), fade=0.01)
    caption(s.hud, 'Chèvres des montagnes, parc national Olympic', t, 1.2, on_dark=True)
    return s


def sB(t, D):
    """Des chèvres des montagnes, une espèce invasive dans la région, chargeaient les visiteurs et
    piétinaient des plantes rares."""
    s = Shot(t, D)
    S.env(s, 'theme')
    s.camera(1.0, 1.0)                                    # locked off: one print arrives, then stillness
    P.drop(s.mid, TRAIL_CARD, W / 2 + 40, H / 2 + 10, t, ENTER, rot=-2.5, spin=12, key='trail')
    return s


def sC(t, D):
    """Elles ne cherchaient qu'une chose : du sel."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, BILLY, t, ENTER, ken=(1.04, 1.04), focus=(0.55, 0.42), fade=0.01)
    s.push(w(cue(1, 'du sel')), 0.06, focus=(W * 0.55, H * 0.42), dur=1.6)
    caption(s.hud, 'Bouc, crête de Klahhane, parc national Olympic', t, ENTER + 0.6, on_dark=True)
    return s


def sD(t, D):
    """En transpirant ou en se soulageant le long des sentiers, les randonneurs laissaient derrière eux
    une tentation irrésistible pour ces animaux affamés de sel."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.04, (W / 2, H / 2), (W * 0.52, H * 0.48))
    P.slide(s.mid, HIKERS_CARD, (-700, H / 2), (W / 2 - 60, H / 2), t, ENTER, dur=1.1, rot=1.5, key='hikers')
    caption(s.hud, 'Randonneurs à Hurricane Ridge, parc national Olympic', t, ENTER + 0.8)
    return s


def sE(t, D):
    """La situation est devenue si dangereuse que des équipes ont dû capturer des centaines de chèvres
    et les évacuer du parc par hélicoptère."""
    s = Shot(t, D)
    S.env(s, 'bleed')
    S.fullbleed(s, HELI, t, ENTER, ken=(1.0, 1.08), focus=(0.5, 0.55), focus_to=(0.5, 0.4), fade=0.01)
    caption(s.hud, 'Évacuation par hélicoptère, parc national Olympic, 2018', t, ENTER + 0.6, on_dark=True)
    return s


def sF(t, D):
    """Le comportement de ces chèvres peut sembler exceptionnel, mais tous les animaux dépendent du sel,
    ou chlorure de sodium, pour de nombreuses fonctions biologiques essentielles."""
    s = Shot(t, D)
    S.env(s, 'charcoal')
    s.camera(1.0, 1.03, (W * 0.4, H / 2), (W * 0.4, H / 2))
    P.mask_reveal(s.mid, HALITE_CARD, 700, H / 2, t, ENTER, dur=1.4, origin=(0.5, 0.6))
    # the film's one typed term: the formula is the picture of the word
    words(s.top, (1520, H / 2 - 10), 'NaCl', 200, t, w(cue(3, 'chlorure')), fill=S.ink(s), font=F_SERIF)
    caption(s.hud, 'Cristaux de sel', t, ENTER + 0.8, on_dark=True)
    return s


def sG(t, D):
    """Un afflux de sodium, par exemple, déclenche l'activité des cellules nerveuses et leur permet de
    transmettre des messages."""
    s = Shot(t, D)
    S.env(s, 'theme')
    s.camera(1.0, 1.0)
    P.mask_reveal(s.mid, NEURON_INK, W / 2, H / 2 + 20, t, ENTER, dur=1.3, lip=False)
    # the camera follows the message down the cell, from the branches to the long fibre
    s.push(w(cue(3, 'transmettre')) - 0.4, 0.14, focus=(W / 2 + 20, H / 2 + 200), dur=2.2)
    caption(s.hud, 'Neurones du cervelet, dessin de Santiago Ramón y Cajal, 1899', t, ENTER + 0.8)
    return s


def sH(t, D):
    """Le chlore, lui, est un composant clé de l'acide gastrique, qui aide à digérer les aliments."""
    s = Shot(t, D)
    S.env(s, 'paper')
    s.camera(1.0, 1.0)
    P.slide(s.mid, STOMACH_CARD, (W + 500, H / 2), (W / 2, H / 2), t, ENTER, dur=1.1, rot=-1.5, key='stomach')
    # the camera comes down onto the stomach drawn at the top of the plate
    s.push(w(cue(3, 'gastrique')) - 0.3, 0.30, focus=(W / 2 + 10, H / 2 - 250), dur=2.0)
    caption(s.hud, 'L’estomac, gravure, 1686', t, ENTER + 0.8)
    return s


SHOTS = [
    (0.0, sA),
    (cue(1, 'Des chevres') - LEAD, sB, 'lr'),
    (cue(1, 'Elles') - LEAD, sC, 'rl'),
    (cue(2, 'En transpirant') - LEAD, sD, 'up'),
    (cue(2, 'La situation') - LEAD, sE, 'lr'),
    (cue(3, 'Le comportement') - LEAD, sF, 'pageturn'),
    (cue(3, 'Un afflux') - LEAD, sG, 'rl'),
    (cue(3, 'Le chlore') - LEAD, sH, 'up'),
]
END = cue.total + 1.2          # silence before the next act


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
