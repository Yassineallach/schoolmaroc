"""Acte 1 : Le besoin. Narration clips 1-3.

One continuous shot on the big board (board.py): every drawing has its place on one long parchment,
the pen draws it as the camera arrives, then the camera travels on to the next one. No cuts.
Pictures: ChatGPT drawings in one black ink-sketch style (PROMPTS.md).
Text: as few moments as possible; the only word on screen in this act is « NaCl », written by the pen.
No fill: lines only, on the parchment.
"""
import sys
from vox import *  # noqa: F401,F403
import style as st
import annotate as A
import board as BD

CLIPS = (1, 2, 3)
cue = make_cue(CLIPS)
LAND = 0.35                    # the camera lands this long after the sentence's first word


def arrive(clip, phrase):
    return cue(clip, phrase) + LAND


def message(c, lt, e):
    """The nerve message travelling down the fibre to the next cell, on « transmettre »."""
    x0, y0, w_, h_ = e.d.box
    pts = [(x0 + (x - 0.05) * w_, y0 + y * h_) for x, y in ((0.29, 0.33), (0.31, 0.43), (0.37, 0.50), (0.42, 0.57), (0.45, 0.64))]
    A.connect(c, pts, lt, cue(3, 'transmettre') - e.start, dur=1.0, dashed=True, dots=False, width=5, sound=False, colour=INK)


E = BD.Entry
# one pen at a time: a label is written only once its drawing is finished (DONE)
DONE = lambda code: next(e for e in ENTRIES if e.code == code).start + next(e for e in ENTRIES if e.code == code).dur + 0.15
ENTRIES = [
    E('M01', 'carte des États-Unis', 0.0, focus=(0.15, 0.25)),                       # « le parc national Olympic, aux États-Unis »
    E('G01', 'chèvres sur la crête', arrive(1, 'avait'), focus=(0.55, 0.40)),          # « …avait un problème de chèvres »
    E('G02', 'chèvres chargeant des randonneurs', arrive(1, 'chargeaient'), focus=(0.40, 0.55)),
    E('G03', 'chèvre léchant le sol', arrive(1, 'Elles'), focus=(0.28, 0.62)),
    E('G04', 'randonneurs sur le sentier', arrive(2, 'En transpirant'), focus=(0.55, 0.25)),
    E('G05', 'chèvre évacuée par hélicoptère', arrive(2, 'La situation'), focus=(0.40, 0.45)),
    # the NaCl triangle: crystals on top, the two organs below, framed wide enough to see the split
    E('G06', 'cristaux de sel', arrive(3, 'Le comportement')),
    E('G07', 'cellules nerveuses', arrive(3, 'Un afflux'), at=(8750, 220), zoom=0.62),
    E('G08', 'l’estomac', arrive(3, 'Le chlore'), at=(9750, 220), zoom=0.62),
]
MARKS = []
BOARD = BD.Board(ENTRIES, end=cue.total + 1.2, marks=MARKS)
import json as _json
_pin = _json.load(open(asset('M01.json')))['pin']
ENTRIES[0].extras.append(BD.write('Parc national Olympic', 52, _pin[0] + 0.05, _pin[1] + 0.08, DONE('M01'), frac=True, anchor='l'))
# words, written by the same pen, once their drawing is done
ENTRIES[6].extras.append(BD.write('NaCl', 140, 0, 335, max(cue(3, 'chlorure'), DONE('G06'))))
# NaCl splits in two: a branch to the nerve cells (« Na »), then one to the stomach (« Cl »)
MARKS += [BD.Line([(9120, -110), (8550, 60), (8070, 320)], DONE('G07')),
          BD.Note('Na', 110, (7960, 400), DONE('G07') + 0.95),
          BD.Line([(9300, -110), (9900, 60), (10480, 320)], DONE('G08')),
          BD.Note('Cl', 110, (10600, 400), DONE('G08') + 0.95)]
ENTRIES[7].extras.append(message)                                                  # « transmettre des messages »


SHOTS = [(0.0, BOARD.scene)]
END = cue.total + 1.2          # silence before the next act


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
