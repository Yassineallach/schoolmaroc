"""Acte 2 : Avant l'épée. Narration clips 4-6.

The board continues from act 1 (its drawings stay where they were drawn). One drawing per view.
Maps (M01 Germany, M02 Turkey) and the empty dashed sword (C01) are drawn in code (tools/make_maps.py).
Words written by the pen: Schöningen, 200 000 ans, portée, contrôle, Arslantepe, vers 3300 av. J.-C., 45-60 cm.
"""
import json
import sys
from vox import *  # noqa: F401,F403
import style as st
import board as BD
import act1

CLIPS = (4, 5, 6)
cue = make_cue(CLIPS)
LAND = 1.2


def arrive(clip, phrase, n=1):
    return cue(clip, phrase, n) + LAND


E = BD.Entry
ENTRIES = [
    E('G08', 'humain et lion des cavernes', arrive(4, 'Les')),                # « …pas plus vite que leurs prédateurs »
    E('G09', 'saisir, aiguiser, prolonger', arrive(4, 'Leur')),               # « saisir une pierre, l'aiguiser… un bâton »
    E('M01', 'carte de l’Allemagne', arrive(4, 'Il'), max_dur=1.5),                       # « Il y a 200 000 ans, à Schöningen… »
    E('G10', 'Néandertaliens et lances', cue(4, 'lances') + 0.9),       # « …taillaient des lances en bois au bord d'un lac »
    E('G11', 'pierre, massue, lance, poignard', cue(5, 'Pierres') + 0.3),   # the camera leaves in the pause before the list
    E('G12', 'la balance', arrive(5, 'Chaque')),                              # held through « La lance offrait la portée… »
    E('C01', 'l’épée qui manque', cue(5, 'Il') + 0.5),                        # « Il manquait une arme… » held through « Cette arme exigeait un matériau qui n'existait pas encore »
    E('G13', 'lame de pierre brisée', cue(6, 'car') + 0.2),               # « …car une lame de pierre trop longue se brise »
    E('M02', 'carte de la Turquie', cue(6, 'Vers') + 1.6, max_dur=1.5),
    E('G14', 'épée d’Arslantepe', cue(6, 'anciennes') + 1.4),
    E('G15', 'le bronze coulé', arrive(6, 'bronze')),
    E('G16', 'les épées de fer', arrive(6, 'fer')),
]
MARKS = []
END = cue.total + 1.2
BOARD = BD.Board(ENTRIES, before=act1.ENTRIES, end=END, marks=MARKS, before_marks=act1.MARKS)
G = {e.code: e for e in ENTRIES}
DONE = {c: e.start + e.dur + 0.15 for c, e in G.items()}
W_ = lambda code, text, size, dx, dy, at, **k: G[code].extras.append(BD.write(text, size, dx, dy, max(at, DONE[code]), **k))
_p1 = json.load(open(asset('M01.json')))['pin']
_p2 = json.load(open(asset('M02.json')))['pin']
# one pen at a time: each word starts when the previous one is finished, and never before it is said
def chain(code, items):
    t = DONE[code]
    for text, size, dx, dy, said, kw in items:
        at = max(t, said)
        fn = BD.write(text, size, dx, dy, at, **kw)
        G[code].extras.append(fn)
        t = at + fn.sound[1] + 0.15


chain('M01', [('Schöningen', 60, _p1[0] + 0.05, _p1[1] - 0.04, cue(4, 'Schoningen'), dict(frac=True, anchor='l')),
              ('200 000 ans', 56, 0.5, 1.08, cue(4, '000'), dict(frac='ink'))])
chain('G12', [('portée', 64, 0.17, 1.02, cue(5, 'portee'), dict(frac='ink')),
              ('contrôle', 64, 0.84, 1.02, cue(5, 'controle'), dict(frac='ink'))])
chain('M02', [('3300 av. J.-C.', 56, 0.5, 1.12, cue(6, '3300'), dict(frac='ink')),
              ('Arslantepe', 60, _p2[0] + 0.03, _p2[1] - 0.06, cue(6, 'Arslantepe'), dict(frac=True, anchor='l'))])
W_('G14', '45 à 60 cm', 64, 0.5, 1.45, cue(6, '45'), frac='ink')

SHOTS = [(0.0, BOARD.scene)]


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
