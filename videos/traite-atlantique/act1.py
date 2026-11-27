"""Acte 1 : Un système à part. Narration clips 1-2.

One continuous shot on the board (board.py), laid out as a timeline (tools/make_layout.py): the hook
G01 (bound hands), the globe G02, the Atlantic map M01 where the film's motif is first drawn (the
dashed route in oxblood, a triangle between three continents), the ledger G03. Words written by the pen: « des biens », « ampleur planétaire »,
« XVe – XIXe siècle », « + de 10 millions ».
"""
import json
import os
import sys
from vox import *  # noqa: F401,F403
import style as st
import scenes as S
import board as BD
from ta import locked, route, chainer, write, side, over, big, under

CLIPS = (1, 2)
cue = make_cue(CLIPS)
LAND = 1.2                     # the camera sets off on the sentence's first word and lands just after it


def arrive(clip, phrase, n=1):
    return cue(clip, phrase, n) + LAND


E = BD.Entry
ENTRIES = [
    E('G01', 'les mains liées', 0.0, max_dur=3.6),                      # hook: « traiter des êtres humains comme des biens »
    E('G02', 'le globe', arrive(1, 'Mais'), max_dur=1.5),                            # « ampleur planétaire… traces durables »
    E('M01', "l'Atlantique", arrive(2, 'atlantique'), max_dur=2.0),                          # « La traite atlantique… trois continents… 10 millions »
    locked(E('G03', 'le registre', arrive(2, 'Ces'), max_dur=1.4)),     # « l'économie et l'histoire de vastes régions »
]
END = cue.total + 1.2          # silence before the next act (no pull-back: the user removed it)
BOARD = BD.Board(ENTRIES, end=END)
G, chain = chainer(ENTRIES)
M01 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'M01.json')))


LIS, ELM, HIS = M01['pins']
# the key information of each sentence, its layout chosen by meaning (side, over, big, under)
chain('G01', [(lambda at: side('des êtres humains', at, size=66, y=0.36), cue(1, 'humains')),
              (lambda at: side('comme des biens', at, size=94, y=0.56), cue(1, 'biens'))])
chain('G02', [(lambda at: side('ampleur', at, size=72, y=0.40, dur=0.8), cue(1, 'planetaire')),
              (lambda at: side('planétaire', at, size=72, y=0.56, dur=0.9), cue(1, 'planetaire'))])
chain('M01', [
    (lambda at: over('fin XVe – milieu XIXe siècle', at, size=72, dur=1.9), cue(2, 'XIXe')),
    (lambda at: route([LIS, ELM, HIS, LIS], at, 1.4), cue(2, 'trois')),                           # the motif: three continents
    (lambda at: write('3 continents', 56, 1.03, 0.45, at, frac='ink', anchor='l', dur=1.0), cue(2, 'trois')),
    (lambda at: big("+ de 10 millions d'Africains", at, size=84, dur=2.3), cue(2, 'millions')),
])
chain('G03', [(lambda at: under("l'économie et l'histoire", at, dur=1.9), cue(2, 'l’économie'))])

SHOTS = [(0.0, BOARD.scene)]


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
