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
from ta import locked, route, chainer, write, side, over, big, under

CLIPS = (3, 4)
cue = make_cue(CLIPS)
LAND = 1.2


def arrive(clip, phrase, n=1):
    return cue(clip, phrase, n) + LAND


E = BD.Entry
ENTRIES = [
    E('G04', 'la galère', None, max_dur=1.6),                           # opens with the travel down to row 2: « contacts par la Méditerranée »
    E('G05', 'la caravelle', arrive(3, 'débuté'), max_dur=2.2),        # « …fin des années 1400… portugaises… espagnole aux Amériques »
    locked(E('G06', 'canne, tabac, coton', arrive(3, 'Dans'), max_dur=1.8)),   # « …exigeaient une main-d'œuvre abondante »
    E('G07', 'le champ vide', arrive(3, 'colons'), max_dur=1.6),        # « …trop peu nombreux pour cultiver… »
    E('G08', 'le village taïno', arrive(3, 'Amerindiens') - 0.5),       # « Les Amérindiens… maladies… d'autres ont résisté »
    E('M02', "vers l'Afrique", arrive(3, 'repondre'), max_dur=1.8),     # « …les Européens se sont alors tournés vers l'Afrique »
    E('G09', 'la ville', arrive(4, 'L’esclavage'), max_dur=1.2),        # « L'esclavage y existait depuis des siècles »
    E('G10', 'les cauris', arrive(4, 'sortes'), max_dur=1.5),           # « …durée limitée… racheter leur liberté »
    locked(E('G11', 'le paysan', arrive(4, 'D’autres'), max_dur=1.4)),  # « …aux serfs européens »
    E('G12', 'la famille', arrive(4, 'esclave'), max_dur=2.4),          # « …famille de son maître, posséder des terres… pouvoir »
]
END = cue.total + 1.2
BOARD = BD.Board(ENTRIES, before=act1.ENTRIES, end=END)
G, chain = chainer(ENTRIES)
M02 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'M02.json')))

# the key information of each sentence (the user: « put the important texts, the information »)
chain('G04', [(lambda at: under('des siècles de contacts', at, dur=1.9), cue(3, 'contacts'))])
chain('G05', [(lambda at: over('fin des années 1400', at, size=84), cue(3, '1400')),
              (lambda at: under('Portugal, puis Espagne', at, dur=1.6), cue(3, 'espagnole'))])
chain('G06', [(lambda at: under("besoin de main-d'œuvre", at, size=70, dur=2.0), cue(3, 'exigeaient'))])
chain('G07', [(lambda at: over('trop peu de colons', at, size=70, dur=1.7), cue(3, 'nombreux'))])
chain('G08', [(lambda at: under('Amérindiens : maladies', at, size=58), cue(3, 'maladies')),
              (lambda at: under('et résistance', at, line=1, size=58), cue(3, 'résisté'))])
chain('M02', [(lambda at: route(M02['pins'], at, 1.6, arrow=True), cue(3, 'tournés'))])        # the motif turns south; no words: the arrow says it
chain('G09', [(lambda at: under("l'esclavage existait déjà", at, dur=2.2), cue(4, 'existait'))])
chain('G10', [(lambda at: under('liberté rachetable', at, dur=1.3), cue(4, 'racheter'))])
chain('G11', [(lambda at: under('comme des serfs', at, dur=1.4), cue(4, 'serfs'))])
chain('G12', [(lambda at: write('famille', 58, 0.20, 1.08, at, frac='ink', dur=0.7), cue(4, 'famille')),
              (lambda at: write('terres', 58, 0.50, 1.08, at, frac='ink', dur=0.6), cue(4, 'terres')),
              (lambda at: write('pouvoir', 58, 0.80, 1.08, at, frac='ink', dur=0.7), cue(4, 'pouvoir'))])

SHOTS = [(0.0, BOARD.scene)]


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
