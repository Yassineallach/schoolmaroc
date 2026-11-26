"""Acte 2 : Le besoin de bras. Narration clips 3-4.

The second row of the timeline board. The act opens at rest on act 1's pull-back, then the camera
travels to the start of the row (the carriage return) and moves forward in time: the Mediterranean
galley, the Portuguese caravel, the three crops, the empty field, the Taíno village, the map M02
where the motif turns south (Europe -> Africa), then slavery in Africa before the trade (town,
cowries, farmer, family). Locked off: G06, G11.
"""
import json
import os
import sys
from vox import *  # noqa: F401,F403
import style as st
import board as BD
import act1
from ta import locked, route, chainer, write

CLIPS = (3, 4)
cue = make_cue(CLIPS)
LAND = 1.2


def arrive(clip, phrase, n=1):
    return cue(clip, phrase, n) + LAND


E = BD.Entry
ENTRIES = [
    E('G04', 'la galère', None),                                         # opens with the travel down to row 2: « contacts par la Méditerranée »
    E('G05', 'la caravelle', arrive(3, 'débuté'), max_dur=2.2),                      # « La traite… fin des années 1400… portugaises »
    locked(E('G06', 'canne, tabac, coton', arrive(3, 'Dans'))),         # « la canne à sucre, le tabac et le coton »
    E('G07', 'le champ vide', arrive(3, 'colons')),                     # « …trop peu nombreux pour cultiver… »
    E('G08', 'le village taïno', arrive(3, 'Amerindiens') - 0.5),       # « Les Amérindiens… d'autres ont résisté »
    E('M02', "vers l'Afrique", arrive(3, 'repondre'), max_dur=1.8),                  # « …les Européens se sont alors tournés vers l'Afrique »
    E('G09', 'la ville', arrive(4, 'L’esclavage')),                     # « L'esclavage y existait depuis des siècles »
    E('G10', 'les cauris', arrive(4, 'Certains')),                      # « des sortes d'engagés… racheter leur liberté »
    locked(E('G11', 'le paysan', arrive(4, 'D’autres'), max_dur=2.4)),  # « …aux serfs européens »
    E('G12', 'la famille', arrive(4, 'Dans')),                          # « …positions de pouvoir »
]
END = cue.total + 1.2
BOARD = BD.Board(ENTRIES, before=act1.ENTRIES, end=END)
G, chain = chainer(ENTRIES)
M02 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'M02.json')))

chain('G04', [(lambda at: write('Méditerranée', 62, 0.50, 1.10, at, frac='ink'), cue(3, 'Méditerranée'))])
chain('G05', [(lambda at: write('fin des années 1400', 62, 0.50, 1.10, at, frac='ink'), cue(3, '1400'))])
chain('G06', [(lambda at: write('canne à sucre', 52, 0.17, 1.08, at, frac='ink'), cue(3, 'canna')),
              (lambda at: write('tabac', 52, 0.50, 1.08, at, frac='ink'), cue(3, 'tabac')),
              (lambda at: write('coton', 52, 0.84, 1.08, at, frac='ink'), cue(3, 'coton'))])
chain('G07', [(lambda at: write('trop peu nombreux', 62, 0.50, -0.06, at, frac='ink'), cue(3, 'nombreux'))])
chain('M02', [(lambda at: route(M02['pins'], at, 1.8, arrow=True), cue(3, 'tournés'))])        # the motif turns south
chain('G10', [(lambda at: write('engagés', 60, 0.28, 1.07, at, frac='ink'), cue(4, 'd’engagés')),
              (lambda at: write('durée limitée', 56, 0.72, 1.07, at, frac='ink'), cue(4, 'limitée'))])
chain('G11', [(lambda at: write('serfs', 64, 0.50, 1.10, at, frac='ink'), cue(4, 'serfs'))])
chain('G12', [(lambda at: write('positions de pouvoir', 60, 0.50, 1.08, at, frac='ink'), cue(4, 'pouvoir'))])

SHOTS = [(0.0, BOARD.scene)]


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
