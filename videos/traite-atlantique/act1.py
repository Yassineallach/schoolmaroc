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
import annotate as A
import board as BD

CLIPS = (1, 2)
cue = make_cue(CLIPS)
LAND = 1.2                     # the camera sets off on the sentence's first word and lands just after it
ACCENT = S.PAL.accent          # the motif's ink, and only the motif's


def arrive(clip, phrase, n=1):
    return cue(clip, phrase, n) + LAND


def locked(e):
    e.lock = True
    return e


E = BD.Entry
ENTRIES = [
    E('G01', 'les mains liées', 0.0, max_dur=4.6),                      # hook: « traiter des êtres humains comme des biens »
    E('G02', 'le globe', arrive(1, 'Mais')),                            # « ampleur planétaire… traces durables »
    E('M01', "l'Atlantique", arrive(2, 'La')),                          # « La traite atlantique… trois continents… 10 millions »
    locked(E('G03', 'le registre', arrive(2, 'Ces'), max_dur=2.0)),     # « l'économie et l'histoire de vastes régions »
]
ROW = [e.code for e in ENTRIES]
PULL = E('PULL1', 'la rangée', look=True, at=None, zoom=None)
PULL.at, PULL.zoom = BD.frame_of(ROW, 1.15)
PULL.arrive = cue(2, 'monde') - 0.4
ENTRIES.append(PULL)                                                     # pull-back 1: the row in one view, 2 s

END = cue.total + 1.2          # silence before the next act
BOARD = BD.Board(ENTRIES, end=END)
G = {e.code: e for e in ENTRIES if not e.look}
DONE = {c: e.start + e.dur + 0.15 for c, e in G.items()}   # one pen at a time: words after their drawing
M01 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'M01.json')))


def route(pts, at, dur=1.4):
    """The motif: a dashed route in the accent ink, between points given as fractions of the
    drawing's image (the map's pins), drawn by the pen inside the drawing's own canvas."""
    def fn(c, lt, e):
        bx, by, bw, bh = e.d.box
        A.connect(c, [(bx + x * bw, by + y * bh) for x, y in pts], lt, at - e.start, dur=dur,
                  dashed=True, dots=False, width=8, sound=False, colour=ACCENT, arrowhead=False)
    fn.sound = (at, dur, lambda: ((0.0, 1.0),))
    return fn


def chain(code, items):
    """One pen at a time: each mark starts when the previous one is finished, never before it is said."""
    t = DONE[code]
    for make, said in items:
        at = max(t, said)
        fn = make(at)
        G[code].extras.append(fn)
        t = at + fn.sound[1] + 0.15


LIS, ELM, HIS = M01['pins']
chain('G01', [(lambda at: BD.write('des biens', 72, 1.06, 0.55, at, frac='ink', anchor='l'), cue(1, 'biens'))])
chain('G02', [(lambda at: BD.write('ampleur planétaire', 60, 1.04, 0.62, at, frac='ink', anchor='l'), cue(1, 'planetaire'))])
chain('M01', [
    (lambda at: BD.write('XVe – XIXe siècle', 62, 0.50, -0.09, at, frac='ink'), cue(2, 'XVe')),
    (lambda at: route([LIS, ELM, HIS, LIS], at, 1.6), cue(2, 'trois')),                           # the triangle: three continents
    (lambda at: BD.write('+ de 10 millions', 62, 0.50, 1.09, at, frac='ink'), cue(2, 'millions')),
])

SHOTS = [(0.0, BOARD.scene)]


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
