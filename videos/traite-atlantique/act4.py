"""Acte 4 : La traversée. Narration clips 7-10 (the film's turn: the music changes here).

The fort, the coffle, the branding iron, the canoes, the map M04 where the motif crosses the ocean
and part of it breaks off and never arrives, then the ship: the Brookes plan, the wake, the ledger,
resistance (the netting, the first sight of the ship, refusing food), the shackles, the forced dance.
Violence is never drawn: places, objects and the moments around it. The two narration claims the
user has not settled (« 20 % », the ears « comme preuve d'achat ») stay off screen.
Locked off: G39, G25, G29. Clip 7 is quick, so the hops between its five views are shorter (0.9 s).
Pen marks in the accent ink: the yoke (G21), the tallies (G25), the netting (G26), the leg irons
(G30). A push into the rows of the Brookes plan (G23). The mood turns colder from here.
"""
import json
import os
import sys
from vox import *  # noqa: F401,F403
import style as st
import board as BD
import act3
from ta import locked, route, chainer, write, side, over, big, under, mark

CLIPS = (7, 8, 9, 10)
cue = make_cue(CLIPS)
LAND = 1.2


def arrive(clip, phrase, n=1):
    return cue(clip, phrase, n) + LAND


E = BD.Entry


def quick(e, pan=0.9):
    """A short hop: clip 7 names five things in eight seconds (the fort, the march, the branding, the
    boarding, the crossing), so the travels between them are quicker."""
    e.fixed_pan = pan
    return e


ENTRIES = [
    E('G20', 'le fort', None, max_dur=2.2),                                       # « une brutalité inimaginable »
    E('G21', 'la marche forcée', arrive(7, 'Après'), max_dur=0.8),               # « …marche forcée jusqu'aux forts de la côte »
    locked(quick(E('G39', 'le fer', cue(7, 'rasés') + 0.9, max_dur=0.8))),       # « rasés… et marqués au fer »
    quick(E('G22', 'les pirogues', cue(7, 'embarqués') + 0.9, max_dur=0.9)),     # « ils étaient embarqués sur des navires »: no words, the image says it
    quick(E('M04', 'la traversée', cue(7, 'Environ') + 0.9, max_dur=1.0)),       # « …ne reverraient jamais la terre ferme »
    E('G23', 'le plan du Brookes', arrive(8, 'La') + 0.9, max_dur=3.0, scale=1.25),   # key drawing: « l'entassement à outrance… sous le pont »
    E('G24', 'le sillage', arrive(8, 'manque'), max_dur=1.8),                    # « maladie… jetés par-dessus bord »
    locked(E('G25', 'le registre', arrive(8, 'Les'), max_dur=1.4)),              # « garantissaient leurs profits »
    E('G26', 'le filet', arrive(9, 'Certains'), max_dur=1.0),                    # « Certains captifs ont pris leur destin en main »
    E('G27', 'le premier regard', arrive(9, 'Dans') + 0.5, max_dur=2.4),         # « …les croyaient cannibales »
    E('G28', 'le refus', arrive(9, 'Par'), max_dur=2.2),                         # « …se laissaient mourir de faim… leur âme retournerait au pays »
    locked(E('G29', 'les fers', arrive(10, 'Ceux') + 0.8, max_dur=1.0)),         # « traités comme une simple cargaison »
    E('G30', 'la danse forcée', arrive(10, 'Les') + 0.4, max_dur=3.0),           # « les hommes étaient contraints de danser… prévenir les révoltes »
]
G23 = ENTRIES[5]
a23 = G23.arrive
G23.zoomin = (a23 + 0.3, a23 + 1.4, a23 + 2.0, a23 + 2.7, 0.55, (0.47, 0.30))   # into the rows of bodies while the pen draws, then back
END = cue.total + 1.2
COLD = (0.90, -0.035, 0.80)                                                     # the crossing: darker, colder, drained (the film's turn)
BOARD = BD.Board(ENTRIES, before=act3.BOARD.before + act3.ENTRIES, end=END, mood=[(0.0, (1.0, 0.0, 1.0)), (3.5, COLD)])
G, chain = chainer(ENTRIES)
M04 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'M04.json')))
ELM, MID, HIS, BRK1, BRK2 = M04['pins']

chain('G20', [(lambda at: under('une brutalité inimaginable', at, dur=1.1), cue(7, 'inimaginable'))])
chain('G21', [(lambda at: mark('ring', (0.19, 0.14, 0.35, 0.31), at, 0.5), cue(7, 'marche')),          # the forked yoke
              (lambda at: under('marche forcée', at, dur=0.8), cue(7, 'forcée'))])
chain('G39', [(lambda at: under('marqués au fer', at, size=66, dur=0.8), cue(7, 'fer'))])
chain('M04', [(lambda at: route([ELM, MID, HIS], at, 1.0, arrow=True), cue(7, 'Environ')),       # the motif crosses the ocean…
              (lambda at: route([ELM, BRK1, BRK2], at, 0.7), cue(7, 'reverraient')),             # …and part of it never arrives
              (lambda at: under('jamais la terre ferme', at, size=60, dur=0.8), cue(7, 'ferme'))])
chain('G23', [(lambda at: big('entassés sous le pont', at, size=84, dur=1.2), max(cue(8, 'pont'), a23 + 2.7))])
chain('G24', [(lambda at: under('maladies', at, size=58, dur=0.7), cue(8, 'maladie')),
              (lambda at: under('jetés par-dessus bord', at, line=1, size=58, dur=1.2), cue(8, 'bord'))])
chain('G25', [(lambda at: mark('ring', (0.10, 0.40, 0.21, 0.77), at, 0.5), cue(8, 'profits')),         # the column of tally marks
              (lambda at: under('leurs profits', at, dur=0.9), cue(8, 'profits'))])
chain('G26', [(lambda at: mark('arrow', ((0.90, 0.36), (0.72, 0.74)), at, 0.5), cue(9, 'destin'))])   # the netting along the rail: no words
chain('G27', [(lambda at: under('ils croyaient les Blancs cannibales', at, size=58, dur=1.6), cue(9, 'cannibales'))])
chain('G28', [(lambda at: under('se laisser mourir de faim', at, size=58, dur=1.3), cue(9, 'faim')),
              (lambda at: under('l’âme retournerait au pays', at, line=1, size=58, dur=1.0), cue(9, 'pays'))])
chain('G29', [(lambda at: big('une simple cargaison', at, size=96, dur=0.9), cue(10, 'cargaison'))])
chain('G30', [(lambda at: under('forcés à danser', at, dur=1.0), cue(10, 'danser')),
              (lambda at: mark('underline', (0.10, 0.63, 0.94), at, 0.5), cue(10, 'danser')),       # the leg irons
              (lambda at: under('pour prévenir les révoltes', at, line=1, dur=1.3), cue(10, 'révoltes'))])

SHOTS = [(0.0, BOARD.scene)]


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
