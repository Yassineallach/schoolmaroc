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
LAND = 0.35


def arrive(clip, phrase):
    return cue(clip, phrase) + LAND


WORLD = json.load(open(asset('M06.json')))['pins']          # [China, Hallstatt]
E = BD.Entry
ENTRIES = [
    E('G09', 'chasseurs-cueilleurs', focus=(0.45, 0.45)),                                   # opens on the travel from act 1
    E('G10', 'panier de plantes', arrive(4, 'Les plantes'), at=(13000, -420), zoom=0.62),   # frames the basket and the balance above
    E('G33', 'viande contre plantes', cue(4, 'mais'), stay=True, max_dur=1.2),              # « …mais beaucoup moins »
    E('G11', 'premier agriculteur', arrive(4, 'Lorsque'), at=(14000, 180), zoom=0.7),
    E('G12', 'bassins d’eau de mer', arrive(5, 'Les civilisations'), focus=(0.6, 0.55)),
    E('M06', 'carte : Chine et Autriche', arrive(5, 'Dans'), focus=(0.75, 0.45)),            # « …du centre de la Chine »
    E('G13', 'saumure bouillie en Chine', arrive(5, 'faisaient'), focus=(0.3, 0.55)),
    E('M06', 'carte', arrive(5, 'Pendant'), look=True, at=(16700, -820), zoom=0.8),         # back to the map: Hallstatt
    E('G14', 'mineurs de Hallstatt', arrive(5, 'creusaient'), focus=(0.65, 0.5)),
    E('G32', 'mer ancienne enfouie', arrive(5, 'enfoui'), focus=(0.5, 0.75)),               # the camera drops into the mountain
]
MARKS = []
BOARD = BD.Board(ENTRIES, before=act1.ENTRIES, end=cue.total + 1.2, marks=MARKS, before_marks=act1.MARKS)
G = {e.code: e for e in ENTRIES if not e.look}
DONE = {c: e.start + e.dur + 0.15 for c, e in G.items()}

# farming timeline: from the basket to the farmer, a tick at the farmer, « ~11 000 ans »
t11 = max(cue(4, '11'), DONE['G11'])
MARKS += [BD.Line([(12500, 470), (14400, 470)], t11, dur=0.8),
          BD.Line([(14400, 430), (14400, 520)], t11 + 0.8, dur=0.25, dashed=False, arrow=False),
          BD.Note('~11 000 ans', 60, (14400, 590), t11 + 1.1)]
G['M06'].extras.append(BD.write('Chine', 64, WORLD[0][0] + 0.03, WORLD[0][1] + 0.07, max(cue(5, 'Chine'), DONE['M06']), frac=True, anchor='l'))
G['M06'].extras.append(BD.write('Hallstatt', 64, WORLD[1][0] + 0.03, WORLD[1][1] + 0.07, cue(5, 'Hallstatt'), frac=True, anchor='l'))

SHOTS = [(0.0, BOARD.scene)]
END = cue.total + 1.2


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
