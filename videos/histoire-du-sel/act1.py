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
    A.connect(c, pts, lt, cue(3, 'transmettre') - e.start, dur=1.0, dashed=True, dots=False, width=6, sound=False)


E = BD.Entry
BOARD = BD.Board([
    E('G01', 'chèvres sur la crête', 0.0, focus=(0.55, 0.45)),
    E('G02', 'chèvres chargeant des randonneurs', arrive(1, 'Des chevres'), focus=(0.45, 0.55)),
    E('G03', 'chèvre léchant le sol', arrive(1, 'Elles'), focus=(0.3, 0.6)),
    E('G04', 'randonneurs sur le sentier', arrive(2, 'En transpirant'), focus=(0.5, 0.3)),
    E('G05', 'chèvre évacuée par hélicoptère', arrive(2, 'La situation'), focus=(0.4, 0.45)),
    E('G06', 'cristaux de sel', arrive(3, 'Le comportement'), scale=0.75, offset=(-150, 0),
      extras=[BD.write('NaCl', 170, 560, 0, cue(3, 'chlorure'))]),     # written by the pen on « chlorure »
    E('G07', 'cellules nerveuses', arrive(3, 'Un afflux'), focus=(0.5, 0.72), extras=[message]),
    E('G08', 'l’estomac', arrive(3, 'Le chlore'), focus=(0.62, 0.62)),
], end=cue.total + 1.2)


SHOTS = [(0.0, BOARD.scene)]
END = cue.total + 1.2          # silence before the next act


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
