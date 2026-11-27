"""Acte 4 : La traversée. Narration clips 7-10 (the film's turn: the music changes here).

The fort, the coffle, the map M04 where the motif crosses the ocean
and part of it breaks off and never arrives, then the ship: the Brookes plan, the wake, the ledger,
resistance (the netting, the first sight of the ship, refusing food), the shackles, the forced dance.
Violence is never drawn: places, objects and the moments around it. The two narration claims the
user has not settled (« 20 % », the ears « comme preuve d'achat ») stay off screen.
Locked off: G25, G29. G22 (canoes) and G39 (branding iron) are not used: clip 7 is too quick for
them to get a view of 2 s each; the coffle carries « marqués au fer ».
"""
import json
import os
import sys
from vox import *  # noqa: F401,F403
import style as st
import board as BD
import act3
from ta import locked, route, chainer, write

CLIPS = (7, 8, 9, 10)
cue = make_cue(CLIPS)
LAND = 1.2


def arrive(clip, phrase, n=1):
    return cue(clip, phrase, n) + LAND


E = BD.Entry
ENTRIES = [
    E('G20', 'le fort', None, max_dur=2.2),                              # « une brutalité inimaginable »
    E('G21', 'la marche forcée', arrive(7, 'Après') + 0.6, max_dur=0.8),  # « …marche forcée jusqu'aux forts… rasés… marqués au fer »
    E('M04', 'la traversée', arrive(7, 'ils', 2) + 1.0, max_dur=1.0),    # « ils étaient embarqués… ne reverraient jamais la terre ferme »
    E('G23', 'le plan du Brookes', arrive(8, 'La') + 0.9, max_dur=3.0, scale=1.25),          # key drawing: « l'entassement à outrance… sous le pont »
    E('G24', 'le sillage', arrive(8, 'manque'), max_dur=1.8),                 # « maladie… jetés par-dessus bord »
    locked(E('G25', 'le registre', arrive(8, 'Les'), max_dur=1.4)),       # « garantissaient leurs profits »
    E('G26', 'le filet', arrive(9, 'Certains'), max_dur=1.0),       # « Certains captifs ont pris leur destin en main »
    E('G27', 'le premier regard', arrive(9, 'Dans') + 0.5, max_dur=2.4),        # « …les croyaient cannibales »
    E('G28', 'le refus', arrive(9, 'Par'), max_dur=2.2),                  # « …se laissaient mourir de faim… leur âme retournerait au pays »
    locked(E('G29', 'les fers', arrive(10, 'Ceux') + 0.8, max_dur=1.0)),        # « traités comme une simple cargaison »
    E('G30', 'la danse forcée', arrive(10, 'Les') + 0.4, max_dur=3.0),          # « les hommes étaient contraints de danser… prévenir les révoltes »
]
END = cue.total + 1.2
BOARD = BD.Board(ENTRIES, before=act3.BOARD.before + act3.ENTRIES, end=END)
G, chain = chainer(ENTRIES)
M04 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'M04.json')))
ELM, MID, HIS, BRK1, BRK2 = M04['pins']

chain('G20', [(lambda at: write('une brutalité inimaginable', 62, 0.50, 1.08, at, frac='ink', dur=1.1), cue(7, 'inimaginable'))])
chain('G21', [(lambda at: write('marche forcée', 62, 0.50, 1.08, at, frac='ink', dur=0.8), cue(7, 'forcée')),
              (lambda at: write('rasés, marqués au fer', 62, 0.50, 1.20, at, frac='ink', dur=1.1), cue(7, 'fer'))])
chain('M04', [(lambda at: write('embarqués vers les Amériques', 56, 0.50, -0.08, at, frac='ink', dur=1.2), cue(7, 'Amériques')),
              (lambda at: route([ELM, MID, HIS], at, 1.0, arrow=True), cue(7, 'Environ')),       # the motif crosses the ocean…
              (lambda at: route([ELM, BRK1, BRK2], at, 0.7), cue(7, 'reverraient')),             # …and part of it never arrives
              (lambda at: write('jamais la terre ferme', 58, 0.50, 1.09, at, frac='ink', dur=0.8), cue(7, 'ferme'))])
chain('G23', [(lambda at: write('entassés sous le pont', 64, 0.50, 1.17, at, frac='ink', dur=1.4), cue(8, 'pont'))])
chain('G24', [(lambda at: write('maladies', 58, 0.50, 1.08, at, frac='ink', dur=0.7), cue(8, 'maladie')),
              (lambda at: write('jetés par-dessus bord', 58, 0.50, 1.20, at, frac='ink', dur=1.2), cue(8, 'bord'))])
chain('G25', [(lambda at: write('leurs profits', 62, 0.50, 1.08, at, frac='ink', dur=0.9), cue(8, 'profits'))])
chain('G26', [(lambda at: write('leur destin en main', 60, 0.50, 1.08, at, frac='ink', dur=1.0), cue(9, 'main'))])
chain('G27', [(lambda at: write('ils croyaient les Blancs cannibales', 58, 0.50, 1.08, at, frac='ink', dur=1.6), cue(9, 'cannibales'))])
chain('G28', [(lambda at: write('se laisser mourir de faim', 58, 0.50, 1.08, at, frac='ink', dur=1.3), cue(9, 'faim')),
              (lambda at: write('l’âme retournerait au pays', 58, 0.50, 1.20, at, frac='ink', dur=1.0), cue(9, 'pays'))])
chain('G29', [(lambda at: write('une simple cargaison', 62, 0.50, 1.08, at, frac='ink', dur=0.8), cue(10, 'cargaison'))])
chain('G30', [(lambda at: write('forcés à danser', 60, 0.50, 1.08, at, frac='ink', dur=1.0), cue(10, 'danser')),
              (lambda at: write('pour prévenir les révoltes', 60, 0.50, 1.20, at, frac='ink', dur=1.3), cue(10, 'révoltes'))])

SHOTS = [(0.0, BOARD.scene)]


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
