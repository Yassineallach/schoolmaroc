"""Acte 1 : Le besoin. Narration clips 1-3.

One unified artwork (the user's choice): every picture is a ChatGPT drawing in the same black
ink-sketch style (PROMPTS.md), printed in the film's ink on the same parchment, revealed
the same way, under the same slow camera push, joined by the same torn-paper cut (plates.py).
Text: as few kinetic moments as possible; the only animated type in this act is « NaCl ».
"""
import sys
from vox import *  # noqa: F401,F403
import style as st
import plates as PL
from style import Shot, words, caption

CLIPS = (1, 2, 3)
cue = make_cue(CLIPS)

G = {k: PL.drawing(k, label, backed=(k != 'G07')) for k, label in (
    ('G01', 'chèvres sur la crête'), ('G02', 'chèvres chargeant des randonneurs'),
    ('G03', 'chèvre léchant le sol'), ('G04', 'randonneurs sur le sentier'),
    ('G05', 'chèvre évacuée par hélicoptère'), ('G06', 'cristaux de sel'),
    ('G07', 'cellules nerveuses'), ('G08', 'l’estomac'))}


def sA(t, D):
    """En 2018, le parc national Olympic, aux États-Unis, avait un problème de chèvres. (Hook)"""
    s = Shot(t, D)
    PL.plate(s, G['G01'], t, start=0.0, focus_to=(0.55, 0.45))
    return s


def sB(t, D):
    """Des chèvres des montagnes, une espèce invasive dans la région, chargeaient les visiteurs et
    piétinaient des plantes rares."""
    s = Shot(t, D)
    PL.plate(s, G['G02'], t, focus_to=(0.45, 0.55))
    caption(s.hud, 'Illustrations', t, 1.0, corner='bl')
    return s


def sC(t, D):
    """Elles ne cherchaient qu'une chose : du sel."""
    s = Shot(t, D)
    PL.plate(s, G['G03'], t, focus_to=(0.5, 0.6))
    return s


def sD(t, D):
    """En transpirant ou en se soulageant le long des sentiers, les randonneurs laissaient derrière eux
    une tentation irrésistible pour ces animaux affamés de sel."""
    s = Shot(t, D)
    PL.plate(s, G['G04'], t, focus_to=(0.6, 0.35))
    return s


def sE(t, D):
    """La situation est devenue si dangereuse que des équipes ont dû capturer des centaines de chèvres
    et les évacuer du parc par hélicoptère."""
    s = Shot(t, D)
    PL.plate(s, G['G05'], t, focus_to=(0.5, 0.5))
    return s


def sF(t, D):
    """Le comportement de ces chèvres peut sembler exceptionnel, mais tous les animaux dépendent du sel,
    ou chlorure de sodium, pour de nombreuses fonctions biologiques essentielles."""
    s = Shot(t, D)
    PL.plate(s, G['G06'], t, focus_to=(0.5, 0.5), scale=0.75, cx=W * 0.38)
    # the act's one typed term: the formula is the picture of the word
    words(s.top, (1540, H / 2), 'NaCl', 190, t, w(cue(3, 'chlorure')), fill=INK, font=F_SERIF)
    return s


def sG(t, D):
    """Un afflux de sodium, par exemple, déclenche l'activité des cellules nerveuses et leur permet de
    transmettre des messages."""
    s = Shot(t, D)
    PL.plate(s, G['G07'], t, focus_to=(0.5, 0.72))
    return s


def sH(t, D):
    """Le chlore, lui, est un composant clé de l'acide gastrique, qui aide à digérer les aliments."""
    s = Shot(t, D)
    PL.plate(s, G['G08'], t, focus_to=(0.62, 0.62))
    return s


SHOTS = PL.cuts([
    (0.0, sA),
    (cue(1, 'Des chevres') - LEAD, sB),
    (cue(1, 'Elles') - LEAD, sC),
    (cue(2, 'En transpirant') - LEAD, sD),
    (cue(2, 'La situation') - LEAD, sE),
    (cue(3, 'Le comportement') - LEAD, sF),
    (cue(3, 'Un afflux') - LEAD, sG),
    (cue(3, 'Le chlore') - LEAD, sH),
])
END = cue.total + 1.2          # silence before the next act


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
