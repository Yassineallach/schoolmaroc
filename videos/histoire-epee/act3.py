"""Acte 3 : Le prix d'une lame. Narration clips 7-9.

The board continues (acts 1-2 stay where they were drawn). One drawing per view.
The gladius of act 1 returns in the legionary's hand (G23).
Words written by the pen: 65 cm, plus de 70 noms, Dhou al-Fiqar, 838, Amorium.
Ali ibn Abi Talib is never depicted: only the sword Dhou al-Fiqar is drawn.
"""
import sys
from vox import *  # noqa: F401,F403
import style as st
import board as BD
import act1
import act2

CLIPS = (7, 8, 9)
cue = make_cue(CLIPS)
LAND = 1.2


def arrive(clip, phrase, n=1):
    return cue(clip, phrase, n) + LAND


E = BD.Entry
# clip 7 is dense (five sentences in 16 s): the camera sets off in the pause before each sentence
# and lands on its first words, so every view keeps at least 2 s
ENTRIES = [
    E('G17', 'le forgeron', arrive(7, 'Mais')),                               # « …minerai, charbon, des heures de forge… »
    E('G18', 'le chasseur et sa lance', cue(7, 'Contrairement') + 0.4),          # « …la lance, qui sert aussi à chasser »
    # G19 (the sword on its cushion) is left out: « …un signe de rang » is too quick for its own view;
    # the hunter holds through it and the palace swords (G20) carry the idea of rank
    E('G20', 'trois lames incrustées', cue(7, 'Arslantepe') + 0.3),           # « À Arslantepe déjà, trois des lames… un palais »
    E('G21', 'le gisant du roi', cue(7, 'Plus') + 0.1),                          # « des rois se font enterrer avec leur épée »
    E('G22', 'l’adoubement', cue(7, 'chevaliers') + 0.6),                     # « …un coup de plat de lame »
    E('G23', 'le légionnaire', cue(8, 'glaive') + 1.0, scale=1.3),   # a tall portrait drawing: drawn larger                              # « Le glaive romain… 65 centimètres »
    E('G24', 'le coup de pointe', arrive(8, 'Plutot')),                       # « …frapper de la pointe depuis l'abri… »
    E('G25', 'épaule contre épaule', arrive(8, 'Serres')),
    E('G26', 'l’épée arabe', arrive(9, 'Dans')),                              # « …plus de soixante-dix noms »
    E('G27', 'Dhou al-Fiqar', cue(9, 'Dhou') + 1.8),
    E('G28', 'les murs d’Amorium', cue(9, 'apres') + 0.6),                          # « En 838, après la prise… d'Amorium »
    E('G29', 'l’épée et les livres', cue(9, 'dit') + 0.9),                    # « L'épée dit plus vrai que les livres. »
]
MARKS = []
END = cue.total + 1.2
BEFORE = act1.ENTRIES + act2.ENTRIES
BOARD = BD.Board(ENTRIES, before=BEFORE, end=END, marks=MARKS, before_marks=act1.MARKS + act2.MARKS)
G = {e.code: e for e in ENTRIES}
DONE = {c: e.start + e.dur + 0.15 for c, e in G.items()}


def chain(code, items):
    """One pen at a time: each word starts when the previous one is finished, never before it is said."""
    t = DONE[code]
    for text, size, dx, dy, said, kw in items:
        at = max(t, said)
        fn = BD.write(text, size, dx, dy, at, **kw)
        G[code].extras.append(fn)
        t = at + fn.sound[1] + 0.15


chain('G23', [('65 cm', 64, -0.32, 0.66, cue(8, '65'), dict(frac='ink'))])
chain('G26', [('plus de 70 noms', 60, 0.5, -0.28, cue(9, 'noms'), dict(frac='ink'))])
chain('G27', [('Dhou al-Fiqar', 64, 0.5, 1.45, cue(9, 'Dhou') + 0.35, dict(frac='ink'))])
chain('G28', [('838', 72, 0.5, -0.12, cue(9, '838'), dict(frac='ink')),
              ('Amorium', 64, 0.5, 1.12, cue(9, "'Amorium"), dict(frac='ink'))])

SHOTS = [(0.0, BOARD.scene)]


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
