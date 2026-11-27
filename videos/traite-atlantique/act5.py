"""Acte 5 : Ce que l'Afrique a perdu. Narration clips 11-12.

The books (what is well known), Africa alone with the question, the village left without its men,
the fallen palace, then Africa partitioned (M06), where the motif ends: the sea route is cut, the
gun arrows stay inside the continent. « des dizaines de millions » stays off screen (unsettled).
Locked off: G31.
"""
import json
import os
import sys
from vox import *  # noqa: F401,F403
import style as st
import board as BD
import act4
from ta import locked, route, chainer, write

CLIPS = (11, 12)
cue = make_cue(CLIPS)
LAND = 1.2


def arrive(clip, phrase, n=1):
    return cue(clip, phrase, n) + LAND


E = BD.Entry
ENTRIES = [
    locked(E('G31', 'les livres', None, max_dur=1.6)),                  # « …sont assez bien connus »
    E('M05', "l'Afrique", arrive(11, 'On') + 0.6, max_dur=1.4),               # « …beaucoup moins les conséquences… sur l'avenir de l'Afrique »
    E('G32', 'le village', arrive(12, 'Non') + 0.8, max_dur=4.0),             # key drawing: « …perdu… personnes valides… des hommes »
    E('G33', 'le palais', arrive(12, 'Lorsque'), max_dur=2.4),          # « …interdite… les royaumes… se sont effondrés »
    E('M06', 'le partage', arrive(12, 'devenant') + 0.8, max_dur=1.6),        # « …la conquête et la colonisation… guerres… aujourd'hui »
]
END = cue.total + 1.2
BOARD = BD.Board(ENTRIES, before=act4.BOARD.before + act4.ENTRIES, end=END)
G, chain = chainer(ENTRIES)
M06 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'M06.json')))['pins']
GOLD, SEA, CUT, *GUNS = M06

chain('G31', [(lambda at: write('le Nouveau Monde', 60, 0.50, 1.08, at, frac='ink', dur=1.0), cue(11, 'Monde')),
              (lambda at: write('bien connu', 60, 0.50, 1.20, at, frac='ink', dur=0.6), cue(11, 'connus'))])
chain('M05', [(lambda at: write("et l'avenir de l'Afrique ?", 62, 0.50, 1.07, at, frac='ink', dur=1.3), cue(11, 'l’Afrique'))])
chain('G32', [(lambda at: write('des personnes valides perdues', 60, 0.50, 1.08, at, frac='ink', dur=1.6), cue(12, 'valides')),
              (lambda at: write('surtout des hommes', 60, 0.50, 1.20, at, frac='ink', dur=1.2), cue(12, 'hommes'))])
chain('G33', [(lambda at: write('traite interdite', 60, 0.50, 1.08, at, frac='ink', dur=1.0), cue(12, 'interdite')),
              (lambda at: write('royaumes effondrés', 60, 0.50, 1.20, at, frac='ink', dur=0.9), cue(12, 'effondrés'))])
chain('M06', [(lambda at: write('conquête et colonisation', 58, 0.50, -0.06, at, frac='ink', dur=1.4), cue(12, 'colonisation')),
              (lambda at: route([GOLD, SEA], at, 0.6), cue(12, 'Quant')),                                   # the old sea route…
              (lambda at: route([(CUT[0] - 0.02, CUT[1] - 0.03), (CUT[0] + 0.02, CUT[1] + 0.03)], at, 0.3, width=10), cue(12, 'Quant')),   # …cut
              (lambda at: route(GUNS[0:2], at, 0.5, arrow=True), cue(12, '\'armes')),                        # the guns stay inside
              (lambda at: route(GUNS[2:4], at, 0.5, arrow=True), cue(12, '\'armes')),
              (lambda at: route(GUNS[4:6], at, 0.5, arrow=True), cue(12, 'guerres')),
              (lambda at: write("guerres et instabilité, encore aujourd'hui", 54, 0.50, 1.06, at, frac='ink', dur=2.0), cue(12, 'aujourd'))])

SHOTS = [(0.0, BOARD.scene)]


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
