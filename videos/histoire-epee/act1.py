"""Acte 1 : Le choc. Narration clips 1-3.

One continuous shot on the big board (board.py): every drawing has its place on one parchment, the
pen draws it as the camera arrives, then the camera travels on to the next one. No cuts.
One drawing per view. Words written by the pen: « Philippe V », « Tite-Live », « gladius ».
Violence implied only: the body stays under its cloak (G04) while clip 2 is spoken.
"""
import sys
from vox import *  # noqa: F401,F403
import style as st
import board as BD

CLIPS = (1, 2, 3)
cue = make_cue(CLIPS)
LAND = 1.2                     # the camera sets off on the sentence's first word and lands just after it


def arrive(clip, phrase, n=1):
    return cue(clip, phrase, n) + LAND


E = BD.Entry
ENTRIES = [
    E('G01', 'soldats portant leur mort', 0.0),                               # hook: « des soldats macédoniens rapportent leurs morts »
    E('G02', 'le bûcher et le roi', arrive(1, 'Leur')),                       # « Leur roi, Philippe V… funérailles dignes »
    E('G03', 'lance, flèche, javelot', arrive(1, 'Ces')),                     # « …blessures de lance, de flèche et de javelot »
    E('G04', 'les soldats glacés', arrive(1, 'Ce')),                          # « Ce qu'ils découvrent les glace. » held through clip 2's first line
    E('G05', 'Tite-Live écrit', arrive(2, 'D')),                              # « D'après l'historien romain Tite-Live… »
    E('G06', 'le glaive', arrive(3, 'Les')),                                  # « …le glaive, l'épée courte… d'Hispanie »
    E('G07', 'main et patte', arrive(3, 'Mais')),                             # « …ni griffes ni crocs »
]
MARKS = []
END = cue.total + 1.2          # silence before the next act
BOARD = BD.Board(ENTRIES, end=END, marks=MARKS)
G = {e.code: e for e in ENTRIES}
DONE = {c: e.start + e.dur + 0.15 for c, e in G.items()}   # one pen at a time: words after their drawing
# words, written by the same pen, beside the drawn part (frac='ink': fractions of the ink's own box)
G['G02'].extras.append(BD.write('Philippe V', 64, 0.02, -0.06, max(cue(1, 'Philippe'), DONE['G02']), frac='ink', anchor='l'))
G['G05'].extras.append(BD.write('Tite-Live', 64, 0.80, -0.08, max(cue(2, 'Tite'), DONE['G05']), frac='ink'))
G['G06'].extras.append(BD.write('gladius', 72, 0.55, 1.30, max(cue(3, 'glaive'), DONE['G06']), frac='ink'))

SHOTS = [(0.0, BOARD.scene)]


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
