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
GUJ = json.load(open(asset('M08.json')))['pins']           # [Dandi, Ahmedabad]


def ring(fx, fy, r, at, dur=0.6):
    """A pen circle around a spot of the drawing (fractions of its box)."""
    def fn(c, lt, e):
        import math
        x0, y0, w_, h_ = e.d.box
        cx, cy = x0 + fx * w_, y0 + fy * h_
        pts = [(cx + r * math.cos(a_), cy + r * math.sin(a_)) for a_ in [i * 2 * math.pi / 40 - 2.0 for i in range(42)]]
        A.connect(c, pts, lt, at - e.start, dur=dur, dashed=False, dots=False, width=5, sound=False, colour=INK, arrowhead=False)
    fn.sound = (at, dur, lambda: ((0.0, 1.0),))
    return fn


def box_world(code, scale_code):
    """World coordinates of a fraction point of a drawing on the board."""
    lines = BD.Entry(code, '').d.layers(BD.SIZE.get(code, 1.0) * BD.SCALE)[0]
    wx, wy = BD.world(code)
    return lambda fx, fy: (wx + (fx - 0.5) * lines.width, wy + (fy - 0.5) * lines.height)


E = BD.Entry
ENTRIES = [
    E('G21', 'salière grecque', focus=(0.5, 0.45)),                                       # « …les salières… Grèce antique »
    E('G22', 'le banquet', arrive(10, 'Selon'), focus=(0.5, 0.45)),
    E('M07', 'carte de France', arrive(11, 'Au XVIIIe'), at=BD.mid('G23', 'M07'), zoom=0.62, max_dur=1.3),   # « Au XVIIIe siècle, en France »
    E('G23', 'la gabelle', cue(11, 'un impot'), stay=True),                                # « …un impôt impopulaire »
    E('G24', 'la Révolution', arrive(11, 'contribue'), focus=(0.6, 0.4)),
    E('G25', 'la marche du sel', arrive(11, 'En 1930'), focus=(0.7, 0.4)),                  # « En 1930, la marche du sel… »
    E('G37', 'la loi britannique', arrive(11, 'lois'), at=BD.mid('G37', 'G26'), zoom=0.62, max_dur=1.2),
    E('G26', 'récolter le sel', cue(11, 'recolter'), stay=True),
    E('M05', 'carte de l’Inde', arrive(11, 'donne'), at=BD.mid('M05', 'M08'), zoom=0.6, max_dur=1.4),   # « …l'indépendance de l'Inde »
    E('M08', 'le Gujarat', None, stay=True),                                                # set below, after « Inde »
]
MARKS = []
END = cue.total + 3.5                                       # a longer hold: the close-up of the march finishes
BOARD = BD.Board(ENTRIES, before=act1.ENTRIES + act2.ENTRIES + act3.ENTRIES, end=END, marks=MARKS,
                 before_marks=act1.MARKS + act2.MARKS + act3.MARKS)
G = {e.code: e for e in ENTRIES}
DONE = {c: e.start + e.dur + 0.15 for c, e in G.items()}

# the salt cellar divides the table: a dashed line down through it on « au-dessus du sel »
G['G22'].extras.append(dashed([(0.525, 0.10), (0.525, 0.97)], max(cue(10, 'au -dessus'), DONE['G22'])))
# the tax set off the Revolution: a pen arrow from the angry peasants to the crowd at the Bastille
X23, Y23 = BD.world('G23')
X24 = BD.world('G24')[0]
MARKS += [BD.Line([(X23 - 250, Y23 + 400), (X24 + 650, Y23 + 430), (X24 + 50, Y23 + 400)], DONE['G24'])]
G['G25'].extras.append(BD.write('1930', 90, -560, -330, max(cue(11, '1930'), DONE['G25'])))
# British law forbids the Indians their own salt: from the decree to the hands
X37, Y37 = BD.world('G37')
MARKS += [BD.Line([(X37 - 610, Y37), (BD.world('G26')[0] + 610, Y37)], DONE['G26'], dur=0.5)]
# India: « Inde », a ring on Gujarat, a line out to the close-up, then the march to the sea at Dandi
t = DONE['M05']
G['M05'].extras.append(BD.write('Inde', 80, 0.55, 0.62, t, frac=True))
t += 0.6
dx, dy = IND['pin']
G['M05'].extras.append(ring(dx, dy - 0.03, 46, t))
t += 0.65
on_map = box_world('M05', None)(dx, dy - 0.03)
X8, Y8 = BD.world('M08')
MARKS += [BD.Line([(on_map[0] - 40, on_map[1] + 30), (X8 + 420, Y8 - 40)], t, dur=0.6, arrow=False)]
t += 0.65
G['M08'].arrive = t + BD.START_EARLY
G['M08'].start = t
G['M08'].dur = 1.5
(gx, gy), (ax, ay) = GUJ
G['M08'].extras.append(dashed([(ax, ay), ((ax + gx) / 2 - 0.02, (ay + gy) / 2), (gx, gy - 0.05)], t + 1.65, dur=0.9))

SHOTS = [(0.0, BOARD.scene)]


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
