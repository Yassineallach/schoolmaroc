"""Acte 4 : Le sel et le pouvoir. Narration clips 10-11.

The board continues from act 3's Roman soldiers. Pen marks only where they explain: a dashed line
across the banquet table at the salt cellar (« au-dessus du sel… en dessous »), and on the pen map of
India the Salt March route to the sea at Dandi. Words, handwritten: « 1930 » and « Inde ».
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

CLIPS = (10, 11)
cue = make_cue(CLIPS)
LAND = 0.35


def arrive(clip, phrase):
    return cue(clip, phrase) + LAND


def dashed(points, at, dur=1.0):
    """A pen line between fractions of the drawing's box, drawn from `at` (act time)."""
    def fn(c, lt, e):
        x0, y0, w_, h_ = e.d.box
        A.connect(c, [(x0 + fx * w_, y0 + fy * h_) for fx, fy in points], lt, at - e.start, dur=dur,
                  dashed=True, dots=False, width=5, sound=False, colour=INK, arrowhead=False)
    fn.sound = (at, dur, lambda: ((0.0, 1.0),))
    return fn


IND = json.load(open(asset('M05.json')))

E = BD.Entry
ENTRIES = [
    E('G21', 'salière grecque', BD.PAN + 0.2, focus=(0.5, 0.45), scale=0.85),          # « …les salières… Grèce antique »
    E('G22', 'le banquet', arrive(10, 'Selon'), focus=(0.5, 0.45)),
    E('G23', 'la gabelle', arrive(11, 'Au XVIIIe'), focus=(0.45, 0.4)),                       # « Au XVIIIe siècle, en France… »
    E('G24', 'la Révolution', arrive(11, 'contribue'), focus=(0.6, 0.4)),
    E('G25', 'la marche du sel', arrive(11, 'En 1930'), focus=(0.7, 0.4)),                   # « En 1930, la marche du sel… »
    E('G26', 'récolter le sel', arrive(11, 'interdisant'), focus=(0.5, 0.5)),
    E('M05', 'carte de l’Inde', arrive(11, 'donne'), focus=(0.2, 0.48)),                # « …l'indépendance de l'Inde »
]
BOARD = BD.Board(ENTRIES, before=act1.ENTRIES + act2.ENTRIES + act3.ENTRIES, end=cue.total + 1.2)
DONE = {e.code: e.start + e.dur + 0.15 for e in ENTRIES}
G = {e.code: e for e in ENTRIES}

# the salt cellar divides the table: a dashed line down through it on « au-dessus du sel »
G['G22'].extras.append(dashed([(0.525, 0.10), (0.525, 0.97)], max(cue(10, 'au -dessus'), DONE['G22'])))
G['G25'].extras.append(BD.write('1930', 90, -560, -330, max(cue(11, '1930'), DONE['G25'])))
# the march: from the ashram at Ahmedabad down to the sea at Dandi, then « Inde »
(ax, ay), (dx, dy) = IND['extra'][0], IND['pin']
G['M05'].extras.append(dashed([(ax, ay - 0.02), (dx - 0.03, (ay + dy) / 2), (dx, dy - 0.06)], DONE['M05'], dur=0.8))
G['M05'].extras.append(BD.write('Inde', 80, 0.45, 0.45, DONE['M05'] + 0.9, frac=True))

SHOTS = [(0.0, BOARD.scene)]
END = cue.total + 1.2


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
