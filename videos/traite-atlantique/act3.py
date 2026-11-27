"""Acte 3 : Le prix d'un être humain. Narration clips 5-6.

Row 3 of the timeline board. Trade goods, the king and the captain, the captives sold as
outsiders, the map M03 where the motif splits in two (goods in from the sea, captives out), then the
consequences in Africa: the coastal market, the raid, the muskets, the two towns in an arms race.
Each drawing carries its sentence's key information. Locked off: G15, G18.
"""
import json
import os
import sys
from vox import *  # noqa: F401,F403
import style as st
import board as BD
import act2
from ta import locked, route, chainer, write, side, over, big, under

CLIPS = (5, 6)
cue = make_cue(CLIPS)
LAND = 1.2


def arrive(clip, phrase, n=1):
    return cue(clip, phrase, n) + LAND


E = BD.Entry
ENTRIES = [
    E('G13', 'les marchandises', None, max_dur=1.6),                    # « produits manufacturés, des armes et du rhum en échange d'esclaves »
    E('G14', 'le roi et le capitaine', arrive(5, 'marchands'), max_dur=2.0),   # « …n'avaient guère de raisons d'hésiter »
    locked(E('G15', 'les captifs vendus', arrive(5, 'criminels'), max_dur=1.6)),   # « des criminels, des débiteurs ou des prisonniers de guerre »
    E('M03', 'la côte', arrive(5, 'souverains'), max_dur=1.4),          # « En les vendant, les souverains enrichissaient leur royaume »
    E('G16', 'le marché', arrive(6, 'mais'), max_dur=1.6),              # « …une concurrence acharnée »
    E('G17', 'le raid de nuit', arrive(6, 'L’esclavage'), max_dur=2.5), # « la capture d'esclaves… en est devenue le mobile »
    locked(E('G18', 'les fusils', arrive(6, 'defendre'), max_dur=1.2)), # « …d'armes à feu européennes, qu'ils achetaient… avec des esclaves »
    E('G19', 'deux villes armées', arrive(6, 'traite', 2), max_dur=3.0),    # « une course aux armements »
]
END = cue.total + 1.2
BOARD = BD.Board(ENTRIES, before=act2.BOARD.before + act2.ENTRIES, end=END)
G, chain = chainer(ENTRIES)
M03 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'M03.json')))
SEA_W, GOLD, BENIN, SEA_S = M03['pins']
IN = [SEA_W, (GOLD[0] - 0.02, GOLD[1] + 0.05)]                           # goods come in from the sea
OUT = [(BENIN[0] - 0.02, BENIN[1] + 0.07), SEA_S]                         # captives go out

chain('G13', [(lambda at: under('armes et rhum', at, dur=1.2), cue(5, 'rhum')),
              (lambda at: under('contre des esclaves', at, line=1, dur=1.2), cue(5, 'd’esclaves'))])
chain('G14', [(lambda at: under("les rois n'hésitent pas", at, dur=1.9), cue(5, 'd’hésiter'))])
chain('G15', [(lambda at: under('criminels, débiteurs', at, size=60, dur=1.2), cue(5, 'débiteurs')),
              (lambda at: under('prisonniers de guerre', at, line=1, size=60, dur=1.2), cue(5, 'guerre'))])
chain('M03', [(lambda at: route(IN, at, 0.9, arrow=True), cue(5, 'vendant')),                 # the motif splits: in…
              (lambda at: route(OUT, at, 0.9, arrow=True), cue(5, 'vendant')),                # …and out
              (lambda at: write('armes, rhum', 50, 0.22, 0.83, at, frac='ink', dur=0.9), cue(5, 'vendant')),
              (lambda at: write('captifs', 50, 0.47, 0.86, at, frac='ink', anchor='l', dur=0.7), cue(5, 'vendant')),
              (lambda at: over('royaumes enrichis et renforcés', at, size=58, dur=1.4), cue(5, 'renforçaient'))])
chain('G16', [(lambda at: under('une concurrence acharnée', at, dur=1.6), cue(6, 'concurrence'))])
chain('G17', [(lambda at: under('la capture devient le mobile', at, size=60, dur=1.0), cue(6, 'mobile'))])
chain('G18', [(lambda at: side('armes à feu', at, size=70, y=0.38, dur=1.0), cue(6, 'feu')),
              (lambda at: side('payées en esclaves', at, size=70, y=0.54, dur=1.2), cue(6, 'esclaves'))])
chain('G19', [(lambda at: big('une course aux armements', at, size=88, dur=1.8), cue(6, 'armements'))])

SHOTS = [(0.0, BOARD.scene)]


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
