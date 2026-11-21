"""Acte 2 : Récolter. Narration clips 4-5.

The board continues from act 1's NaCl triangle. Farming: the fire, the basket with the meat-and-plants
balance above it (conceptual), the farmer, and a pen timeline under the row with « ~11 000 ans ».
The three methods in a row (salt pans, brine pans, miners) with one world map above them where the
pen pins China then Hallstatt; under the miners, the cross-section of a buried ancient sea, which
the camera drops into on « enfoui ». No cuts, no fill; words handwritten.
"""
import json
import sys
from vox import *  # noqa: F401,F403
import style as st
import board as BD
import act1

CLIPS = (4, 5)
cue = make_cue(CLIPS)
LAND = 1.2                     # the camera sets off on the sentence's first word and lands just after it


def arrive(clip, phrase):
    return cue(clip, phrase) + LAND


WORLD = json.load(open(asset('M06.json')))['pins']          # [China, Hallstatt]
E = BD.Entry
ENTRIES = [
    E('G09', 'chasseurs-cueilleurs', focus=(0.45, 0.45)),                                   # opens on the travel from act 1
    E('G10', 'panier de plantes', arrive(4, 'Les plantes')),                                 # (the meat-and-plants balance, G33, is left out: too quick)
    E('G11', 'premier agriculteur', arrive(4, 'developpee'), focus=(0.55, 0.45)),          # « Lorsque l'agriculture s'est développée… »
    E('G12', 'bassins d’eau de mer', arrive(5, 'Les civilisations'), focus=(0.6, 0.55)),
    BD.cluster(E('M06', 'carte : Chine et Autriche', arrive(5, 'Dans')), 'G13'),          # « …du centre de la Chine »
    E('G13', 'saumure bouillie en Chine', cue(5, 'faisaient'), stay=True),
    E('M06', 'carte', arrive(5, 'Pendant'), look=True, at=BD.world('M06'), zoom=0.75),      # back to the map: « Hallstatt »
    BD.cluster(E('G14', 'mineurs de Hallstatt', arrive(5, 'creusaient')), 'G32'),           # the miners and the buried sea
    E('G32', 'mer ancienne enfouie', cue(5, 'enfoui'), stay=True),                           # « …sel gemme, enfoui… »
]
MARKS = []
BOARD = BD.Board(ENTRIES, before=act1.ENTRIES, end=cue.total + 1.2, marks=MARKS, before_marks=act1.MARKS)
G = {e.code: e for e in ENTRIES if not e.look}
DONE = {c: e.start + e.dur + 0.15 for c, e in G.items()}

# farming timeline: from the basket to the farmer, a tick at the farmer, « ~11 000 ans »
t11 = max(cue(4, '11'), DONE['G11'])
_x11, _y11 = BD.world('G11')
_y = _y11 + 880 * BD.SIZE.get('G11', 1.0) * BD.SCALE / 2 + 30
# a date, not a diagram: one handwritten line under the farmer (a one-point « timeline » explained nothing)
MARKS += [BD.Note('il y a ~11 000 ans', 60, (_x11, _y + 40), t11)]
G['M06'].extras.append(BD.write('Chine', 64, WORLD[0][0] + 0.10, WORLD[0][1] + 0.02, max(cue(5, 'Chine'), DONE['M06']), frac=True, anchor='l'))
G['M06'].extras.append(BD.write('Hallstatt', 64, WORLD[1][0] - 0.17, WORLD[1][1] + 0.12, cue(5, 'Hallstatt'), frac=True))

SHOTS = [(0.0, BOARD.scene)]
END = cue.total + 1.2


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
