"""Acte 2 : Récolter. Narration clips 4-5.

The board continues (board.py): the camera leaves act 1's stomach drawing and travels on. Every
drawing is drawn by the pen as the camera arrives; the maps of China and Austria are drawn by the pen
(tools/make_maps.py) and their place names are handwritten on the spoken word. No cuts, no fill.
Text: only the two place names, « Chine » and « Hallstatt ».
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


def pin(code):
    return json.load(open(asset(code + '.json')))['pin']


E = BD.Entry
ENTRIES = [
    E('G09', 'chasseurs-cueilleurs', BD.PAN + 0.2, focus=(0.45, 0.45)),     # the act opens on the travel from act 1's last drawing
    E('G10', 'panier de plantes', arrive(4, 'Les plantes'), focus=(0.5, 0.5)),
    E('G11', 'premier agriculteur', arrive(4, 'Lorsque'), focus=(0.55, 0.45)),            # « …ajouter du sel aux aliments »
    E('G12', 'bassins d’eau de mer', arrive(5, 'Les civilisations'), focus=(0.6, 0.55)),
    E('M02', 'carte de la Chine', arrive(5, 'Dans'), focus=(0.55, 0.6)),                   # « …du centre de la Chine »
    E('G13', 'saumure bouillie en Chine', arrive(5, 'faisaient'), focus=(0.3, 0.55)),
    E('M03', 'carte de l’Autriche', arrive(5, 'Pendant'), focus=(0.55, 0.45)),             # « …Hallstatt, en Autriche »
    E('G14', 'mineurs de Hallstatt', arrive(5, 'creusaient'), focus=(0.65, 0.5)),
]
BOARD = BD.Board(ENTRIES, before=act1.ENTRIES, end=cue.total + 1.2)
DONE = {e.code: e.start + e.dur + 0.15 for e in ENTRIES}
_c, _a = pin('M02'), pin('M03')
ENTRIES[4].extras.append(BD.write('Chine', 70, _c[0] + 0.04, _c[1] + 0.10, max(cue(5, 'Chine'), DONE['M02']), frac=True, anchor='l'))
ENTRIES[6].extras.append(BD.write('Hallstatt', 70, _a[0] + 0.04, _a[1] + 0.10, max(cue(5, 'Hallstatt'), DONE['M03']), frac=True, anchor='l'))

SHOTS = [(0.0, BOARD.scene)]
END = cue.total + 1.2


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
