"""Acte 3 : Ce que vaut le sel. Narration clips 6-9.

The board continues from act 2's miners. Every drawing is drawn by the pen as the camera arrives; the
salt road is a pen map of north-west Africa where the pen draws the route from the Sahara mine to
West Africa. Words, all handwritten: « Sahara » on the map, « ? » for the mystery of taste, and the
etymology « salaire » then « sal » under it. No fill, no cuts.
"""
import json
import sys
from vox import *  # noqa: F401,F403
import style as st
import annotate as A
import board as BD
import act1
import act2

CLIPS = (6, 7, 8, 9)
cue = make_cue(CLIPS)
LAND = 0.35


def arrive(clip, phrase):
    return cue(clip, phrase) + LAND


PINS = json.load(open(asset('M04.json')))['pins']


def route(at):
    """The salt road: a dashed pen line with an arrowhead, from the Sahara pin down to West Africa."""
    def fn(c, lt, e):
        x0, y0, w_, h_ = e.d.box
        (ax, ay), (bx, by) = PINS
        p0 = (x0 + ax * w_ + 6, y0 + ay * h_ + 8)
        p1 = (x0 + bx * w_, y0 + by * h_)
        mid = ((p0[0] + p1[0]) / 2 - 18, (p0[1] + p1[1]) / 2)
        A.connect(c, [p0, mid, p1], lt, at - e.start, dur=1.1, dashed=True, dots=False, width=5,
                  sound=False, colour=INK)
    fn.sound = (at, 1.1, lambda: ((0.0, 1.0),))
    return fn


def tick_arrow(dx, dy, up, at, dur=0.3):
    """A small up or down pen arrow beside a word in the cell."""
    def fn(c, lt, e):
        y0, y1 = (dy + 26, dy - 26) if up else (dy - 26, dy + 26)
        A.connect(c, [(W / 2 + dx, H / 2 + y0), (W / 2 + dx, H / 2 + y1)], lt, at - e.start, dur=dur,
                  dashed=False, dots=False, width=5, sound=False, colour=INK, arrowhead=True)
    fn.sound = (at, dur, lambda: ((0.0, 1.0),))
    return fn


E = BD.Entry
ENTRIES = [
    E('G15', 'aliments conservés', focus=(0.5, 0.45)),                                   # opens on the travel from act 2
    E('G16', 'bactérie et sel', arrive(6, 'Le sel tue'), focus=(0.7, 0.5)),            # « …en aspirant l'eau de leurs cellules »
    E('G17', 'une pincée de sel', arrive(7, 'Le sel'), at=BD.mid('G17', 'G38', 40), zoom=0.62),     # frames the stew and the spoons
    E('G38', 'une pincée, une dose généreuse', cue(7, 'Une pincee'), stay=True, max_dur=1.3),
    E('M04', 'la route du sel', arrive(8, 'Partout'), focus=(0.30, 0.30)),               # « …l'échanger avec les régions qui en manquaient »
    E('G18', 'caravane de sel', arrive(8, 'Des'), focus=(0.45, 0.45)),
    E('G19', 'le sel contre l’or', arrive(8, 'La'), focus=(0.5, 0.4)),
    E('G20', 'soldats romains payés en sel', arrive(9, 'Dans'), focus=(0.45, 0.45)),
]
MARKS = []
BOARD = BD.Board(ENTRIES, before=act1.ENTRIES + act2.ENTRIES, end=cue.total + 1.2, marks=MARKS,
                 before_marks=act1.MARKS + act2.MARKS)
DONE = {e.code: e.start + e.dur + 0.15 for e in ENTRIES}
G = {e.code: e for e in ENTRIES}

# taste: under the pinch (left spoon) and the heaped spoon (right), each effect written on its word
pen = DONE['G38']
for col, word, up, spoken in ((-330, 'amer', False, cue(7, 'ameres')), (-330, 'acide', True, cue(7, 'acides')),
                              (-330, 'sucré', True, cue(7, 'sucrees')), (-330, 'umami', True, cue(7, 'umami')),
                              (330, 'sucré', False, cue(7, 'sucre')), (330, 'umami', True, cue(7, "'umami"))):
    row = sum(1 for x in G['G38'].extras if getattr(x, 'col', None) == col)
    y = 290 + row * 66
    at = max(spoken, pen)
    w_ = BD.write(word, 54, col - 40, y, at)
    w_.col = col
    G['G38'].extras.append(w_)
    G['G38'].extras.append(tick_arrow(col + 110, y, up, at + w_.sound[1]))
    pen = at + w_.sound[1] + 0.35
MARKS += [BD.Note('?', 220, BD.mid('G17', 'G38', -560), max(cue(7, 'Pourtant'), pen))]          # « Pourtant… reste un mystère »
G['M04'].extras.append(BD.write('Sahara', 64, PINS[0][0] + 0.05, PINS[0][1] - 0.02, DONE['M04'], frac=True, anchor='l'))
G['M04'].extras.append(route(DONE['M04'] + 1.0))                                                   # to « …qui en manquaient »
MARKS += [BD.Note('1er millénaire', 60, (BD.world('G18')[0], BD.world('G18')[1] - 420), DONE['G18'])]                                 # « Dès le premier millénaire de notre ère »
G['G20'].extras.append(BD.write('salaire', 110, 720, -40, max(cue(9, 'salaire'), DONE['G20'])))
G['G20'].extras.append(BD.write('sal', 110, 640, 110, cue(9, 'sal')))                               # under the first three letters

SHOTS = [(0.0, BOARD.scene)]
END = cue.total + 1.2


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
