"""Acte 5 : La décision. Narration clips 12-14, then the closing hold and the channel outro.

The board continues. One drawing per view. The distance line returns twice: from the turret it runs
to no one (« sans qu'un humain valide chaque frappe »), and between the two faces it is short again
(« …à regarder celui qui meurt »). The film ends on a human hand resting on a sword (answers G07, the
open hand of act 1): once it is drawn, the camera moves in slowly on the hand and holds, then the outro.
Words written by the pen: ?, 21 novembre 2026, Genève, 163.
"""
import json
import sys
from vox import *  # noqa: F401,F403
import style as st
import annotate as A
import board as BD
import act1
import act2
import act3
import act4
import brand

CLIPS = (12, 13, 14)
cue = make_cue(CLIPS)
LAND = 1.2


def arrive(clip, phrase, n=1):
    return cue(clip, phrase, n) + LAND


E = BD.Entry
ENTRIES = [
    E('G40', 'la tourelle automatique', 0.0),                                 # « L'intelligence artificielle… sans qu'un humain valide chaque frappe »
    E('G41', 'la table vide', arrive(12, 'Les')),                             # « Les États-Unis et la Russie… règles non contraignantes »
    E('G42', 'le traité non signé', cue(12, 'Comite') + 1.0),                 # « …réclament un traité… Qui répond d'une erreur commise par une machine ? »
    E('M04', 'carte de la Suisse', cue(13, '2026') + 1.0),                         # « Le 21 novembre 2026, à Genève… »
    E('G43', 'la salle de l’assemblée', cue(13, 'Un') + 2.4),                    # « Un mois plus tôt, 163 États… »
    E('G44', 'face à face', arrive(14, 'Pendant')),                           # « …l'épée a obligé celui qui tue à regarder celui qui meurt »
    E('G45', 'la main sur l’épée', arrive(14, 'Le'), scale=1.4),             # « …la place qui reste à un être humain dans la décision »
]
MARKS = []
BEFORE = act1.ENTRIES + act2.ENTRIES + act3.ENTRIES + act4.ENTRIES
BEFORE_MARKS = act1.MARKS + act2.MARKS + act3.MARKS + act4.MARKS
# the ending: once the last word is said, the camera moves in slowly on the hand and holds 3 s
_gx, _gy = BD.world('G45')
CLOSE = E('CLOSE', 'gros plan sur la main', cue.total + 0.6 + BD.CLOSE_PAN, look=True, at=(_gx, _gy - 300), zoom=1.45)
ENTRIES.append(CLOSE)
END = CLOSE.arrive + 3.0
BOARD = BD.Board(ENTRIES, before=BEFORE, end=END, marks=MARKS, before_marks=BEFORE_MARKS)
G = {e.code: e for e in ENTRIES}
DONE = {c: e.start + e.dur + 0.15 for c, e in G.items() if not e.look}


def distance(p0, x1, at, dur=0.8):
    """The film's distance line (see act4), from p0 to x1, fractions of the drawing's image."""
    def fn(c, lt, e):
        bx, by, bw, bh = e.d.box
        y = by + p0[1] * bh
        A.connect(c, [(bx + p0[0] * bw, y), (bx + x1 * bw, y)], lt, at - e.start, dur=dur,
                  dashed=True, dots=False, width=7, sound=False, colour=INK, arrowhead=False)
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


_p4 = json.load(open(asset('M04.json')))['pin']
chain('G40', [(lambda at: distance((0.79, 0.31), 0.98, at, 0.7), cue(12, 'humain'))])          # a line to no one
chain('G42', [(lambda at: BD.write('?', 170, 0.90, 0.68, at, frac=True), cue(12, 'machine'))])  # beside the unsigned treaty
chain('M04', [(lambda at: BD.write('21 novembre 2026', 56, 0.5, 1.10, at, frac='ink'), cue(13, '2026')),
              (lambda at: BD.write('Genève', 60, _p4[0] + 0.03, _p4[1] - 0.06, at, frac=True, anchor='l'), cue(13, 'Geneve'))])
chain('G43', [(lambda at: BD.write('163', 96, 0.5, -0.12, at, frac='ink'), cue(13, '163'))])
chain('G44', [(lambda at: distance((0.40, 0.19), 0.585, at, 0.5), cue(14, 'regarder'))])        # eye to eye, short again

SHOTS = [(0.0, BOARD.scene)]
if brand.CFG['outro']['enabled']:                     # the channel outro after the closing hold
    SHOTS.append((END, brand.outro_scene, 'up'))
    END = END + brand.outro_seconds()


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
