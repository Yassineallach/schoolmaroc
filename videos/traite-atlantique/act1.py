"""Acte 1 : Un système à part. Narration clips 1-2.

One continuous shot on the board (board.py), laid out as a timeline (tools/make_layout.py): the hook
G01 (bound hands), the globe G02, the Atlantic map M01 where the film's motif is first drawn (the
dashed route in oxblood, a triangle between three continents), the ledger G03; then a short
pull-back over the row. Words written by the pen: « des biens », « ampleur planétaire »,
« XVe – XIXe siècle », « + de 10 millions ».
"""
import json
import os
import sys
from vox import *  # noqa: F401,F403
import style as st
import scenes as S
import board as BD
from ta import locked, route, chainer, write

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
ROW = [e.code for e in ENTRIES]
PULL = E('PULL1', 'la rangée', look=True, at=None, zoom=None)
PULL.at, PULL.zoom = BD.frame_of(ROW, 1.15)
PULL.arrive = cue(2, 'monde') + 1.0
ENTRIES.append(PULL)                                                     # pull-back 1: the row in one view, 2 s

END = cue.total + 2.2          # silence before the next act: the pull-back holds 1.5 s
BOARD = BD.Board(ENTRIES, end=END)
G, chain = chainer(ENTRIES)
M01 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'M01.json')))


LIS, ELM, HIS = M01['pins']
# the key information of each sentence, written by the pen beside the drawing (the user: « put the
# important texts, the information »): the definition, the scale, the dates, the number, the stakes.
chain('G01', [(lambda at: write('des êtres humains', 64, 0.50, 1.07, at, frac='ink'), cue(1, 'humains')),
              (lambda at: write('traités comme des biens', 64, 0.50, 1.19, at, frac='ink'), cue(1, 'biens'))])
chain('G02', [(lambda at: write('ampleur planétaire', 62, 1.04, 0.55, at, frac='ink', anchor='l', dur=1.6), cue(1, 'planetaire'))])
chain('M01', [
    (lambda at: write('fin XVe – milieu XIXe siècle', 58, 0.50, -0.09, at, frac='ink', dur=1.9), cue(2, 'XIXe')),
    (lambda at: route([LIS, ELM, HIS, LIS], at, 1.4), cue(2, 'trois')),                           # the motif: three continents
    (lambda at: write('3 continents', 56, 1.03, 0.45, at, frac='ink', anchor='l', dur=1.0), cue(2, 'trois')),
    (lambda at: write("+ de 10 millions d'Africains", 58, 0.50, 1.09, at, frac='ink', dur=2.3), cue(2, 'millions')),
])
chain('G03', [(lambda at: write("l'économie et l'histoire", 60, 0.50, 1.10, at, frac='ink', dur=1.9), cue(2, 'l’économie'))])

SHOTS = [(0.0, BOARD.scene)]


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
