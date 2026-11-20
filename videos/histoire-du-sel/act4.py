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
    BD.cluster(E('M07', 'carte de France', arrive(11, 'Au XVIIIe')), 'G23', 'G24'),     # France, the tax, the Revolution on one frame
    E('G23', 'la gabelle', cue(11, 'un impot'), stay=True),                                # « …un impôt impopulaire »
    E('G24', 'la Révolution', cue(11, 'a contribue'), stay=True),
    BD.cluster(E('G25', 'la marche du sel', arrive(11, 'En 1930')), 'G37', 'G26'),        # the march, the law, the forbidden harvest
    E('G37', 'la loi britannique', cue(11, 'lois'), stay=True),
    E('G26', 'récolter le sel', cue(11, 'recolter'), stay=True),
    E('M05', 'carte de l’Inde', arrive(11, 'donne'), at=BD.frame_of(['M05', 'M08'])[0], zoom=BD.frame_of(['M05', 'M08'])[1], max_dur=1.4),   # « …l'indépendance de l'Inde »
    E('M08', 'le Gujarat', None, stay=True),                                                # set below, after « Inde »
]
MARKS = []
END = cue.total + 3.5                                       # a longer hold: the close-up of the march finishes
BOARD = BD.Board(ENTRIES, before=act1.ENTRIES + act2.ENTRIES + act3.ENTRIES, end=END, marks=MARKS,
                 before_marks=act1.MARKS + act2.MARKS + act3.MARKS)
G = {e.code: e for e in ENTRIES}
DONE = {c: e.start + e.dur + 0.15 for c, e in G.items()}
G['G22'].extras.append(BD.write('au-dessus du sel', 50, 0.27, -0.06, max(cue(10, 'au -dessus'), DONE['G22']) + 1.1, frac=True))
G['G22'].extras.append(BD.write('en dessous', 50, 0.78, -0.06, max(cue(10, 'dessous'), DONE['G22'] + 3.0), frac=True))

# the salt cellar divides the table: a dashed line down through it on « au-dessus du sel »
G['G22'].extras.append(dashed([(0.525, 0.10), (0.525, 0.97)], max(cue(10, 'au -dessus'), DONE['G22'])))
# the tax set off the Revolution: a pen arrow from the angry peasants to the crowd at the Bastille
MARKS += [BD.Line(list(BD.edge('G23', 'G24', 0.2)), DONE['G24'], dashed=False, width=6)]          # the tax set off the Revolution
G['G25'].extras.append(BD.write('1930', 90, -560, -330, max(cue(11, '1930'), DONE['G25'])))
# British law forbids the Indians their own salt: from the decree to the hands
MARKS += [BD.Line(list(BD.edge('G37', 'G26', 0.2)), DONE['G26'], dur=0.6, dashed=False, width=6)]   # the law forbids the harvest
# India: « Inde », a ring on Gujarat, then the close-up beside it: the march to the sea, « Dandi »
# (no connector line: it crossed the whole country; the ring and the close-up side by side are enough)
t = DONE['M05']
t += 0.6
dx, dy = IND['pin']
G['M05'].extras.append(ring(dx, dy - 0.03, 46, t))
t += 0.65
G['M08'].arrive = t + BD.START_EARLY
G['M08'].start = t
G['M08'].dur = 1.5
(gx, gy), (ax, ay) = GUJ
G['M08'].extras.append(ring(ax, ay, 12, t + 1.6, dur=0.3))                                   # the start, inland
G['M08'].extras.append(dashed([(ax, ay + 0.03), ((ax + gx) / 2 - 0.03, (ay + gy) / 2), (gx, gy - 0.07)], t + 1.95, dur=0.9))
G['M08'].extras.append(BD.write('Dandi', 64, gx + 0.04, gy + 0.03, t + 2.95, frac=True, anchor='l'))

SHOTS = [(0.0, BOARD.scene)]


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
