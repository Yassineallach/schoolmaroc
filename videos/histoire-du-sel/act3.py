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
        p1 = (x0 + bx * w_ + 2, y0 + by * h_ - 78)
        mid = ((p0[0] + p1[0]) / 2 - 40, (p0[1] + p1[1]) / 2)
        A.connect(c, [p0, mid, p1], lt, at - e.start, dur=1.1, dashed=True, dots=False, width=5,
                  sound=False, colour=INK)
    fn.sound = (at, 1.1, lambda: ((0.0, 1.0),))
    return fn


E = BD.Entry
ENTRIES = [
    E('G15', 'aliments conservés', BD.PAN + 0.2, focus=(0.5, 0.45)),                   # opens on the travel from the miners
    E('G16', 'bactérie et sel', arrive(6, 'Le sel tue'), focus=(0.7, 0.5)),            # « …en aspirant l'eau de leurs cellules »
    E('G17', 'une pincée de sel', arrive(7, 'Le sel'), focus=(0.45, 0.45), offset=(-140, 0)),
    E('M04', 'la route du sel', arrive(8, 'Partout'), focus=(0.35, 0.55)),               # « …l'échanger avec les régions qui en manquaient »
    E('G18', 'caravane de sel', arrive(8, 'Des'), focus=(0.45, 0.45)),
    E('G19', 'le sel contre l’or', arrive(8, 'La'), focus=(0.5, 0.4)),
    E('G20', 'soldats romains payés en sel', arrive(9, 'Dans'), focus=(0.45, 0.45), offset=(-170, 0)),
]
BOARD = BD.Board(ENTRIES, before=act1.ENTRIES + act2.ENTRIES, end=cue.total + 1.2)
DONE = {e.code: e.start + e.dur + 0.15 for e in ENTRIES}
G = {e.code: e for e in ENTRIES}

G['G17'].extras.append(BD.write('?', 220, 560, -40, max(cue(7, 'Pourtant'), DONE['G17'])))          # « Pourtant… reste un mystère »
G['M04'].extras.append(BD.write('Sahara', 64, PINS[0][0] + 0.05, PINS[0][1] - 0.02, DONE['M04'], frac=True, anchor='l'))
G['M04'].extras.append(route(DONE['M04'] + 1.0))                                                   # to « …qui en manquaient »
G['G20'].extras.append(BD.write('salaire', 110, 720, -40, max(cue(9, 'salaire'), DONE['G20'])))
G['G20'].extras.append(BD.write('sal', 110, 640, 110, cue(9, 'sal')))                               # under the first three letters

SHOTS = [(0.0, BOARD.scene)]
END = cue.total + 1.2


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
