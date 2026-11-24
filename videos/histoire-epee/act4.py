"""Acte 4 : La distance. Narration clips 10-11.

The board continues. One drawing per view. The film's returning motif starts here: a dashed pen
line from the one who strikes toward the one who is struck. Between the two swordsmen it is short
(eye to eye); from the rifle it runs past the drawing; from the gun, further; from the drone it
leaves the frame. Words written by the pen: IXe siècle, On Killing.
"""
import sys
from vox import *  # noqa: F401,F403
import style as st
import annotate as A
import board as BD
import plates as PL
import act1
import act2
import act3

CLIPS = (10, 11)
cue = make_cue(CLIPS)
LAND = 1.2


def arrive(clip, phrase, n=1):
    return cue(clip, phrase, n) + LAND


E = BD.Entry
ENTRIES = [
    E('G30', 'la poudre noire', 0.8),                                         # « Mais un autre mélange… La poudre noire, connue en Chine dès le IXe siècle »
    # (the China map, M03, is left out: the opening is too quick for two views; the pen writes « IXe siècle » beside the powder)
    E('G31', 'deux escrimeurs', 7.3),                    # « Former un chevalier ou un escrimeur prenait des années »
    E('G32', 'le mousquetaire', 10.8),                      # « …un fantassin apprend bien plus vite à charger et à tirer »
    E('G33', 'l’armure abandonnée', 14.3),                       # « Les armées grossissent… l'armure… perdent leur valeur »
    E('G34', 'l’officier et son épée', 17.9),              # « …une arme d'apparat… cérémonies »
    E('G35', 'deux épéistes face à face', arrive(11, 'Ce')),                  # « …à portée de bras… voir le visage de l'adversaire »
    E('G36', 'le fusil', cue(11, 'fusil') + 0.27),                                                # « Le fusil éloigne la cible à des centaines de mètres »
    E('G37', 'l’artillerie', cue(11, 'fusil') + 2.37, stay=True),                                 # « l'artillerie à des kilomètres » (a short hop: +1 s)
    E('G38', 'le drone armé', cue(11, 'fusil') + 5.47, stay=True),                               # « les drones armés… à des continents de distance »
    E('G39', 'le livre', arrive(11, 'Dans')),                                 # « Dans son livre On Killing… Dave Grossman »
]
MARKS = []
END = cue.total + 1.2
BEFORE = act1.ENTRIES + act2.ENTRIES + act3.ENTRIES
BOARD = BD.Board(ENTRIES, before=BEFORE, end=END, marks=MARKS, before_marks=act1.MARKS + act2.MARKS + act3.MARKS)
G = {e.code: e for e in ENTRIES}
DONE = {c: e.start + e.dur + 0.15 for c, e in G.items()}


def distance(p0, x1, at, dur=0.8):
    """The distance line: a dashed pen line from p0 (fractions of the drawing's image) to x1 (a
    fraction of the image's width, beyond 1 runs past the drawing, off the canvas = off the frame)."""
    def fn(c, lt, e):
        bx, by, bw, bh = e.d.box
        y = by + p0[1] * bh
        A.connect(c, [(bx + p0[0] * bw, y), (min(c.width - 4, bx + x1 * bw), y)], lt, at - e.start, dur=dur,
                  dashed=True, dots=False, width=7, sound=False, colour=INK, arrowhead=False)
    fn.sound = (at, dur, lambda: ((0.0, 1.0),))
    return fn


def chain(code, items):
    """One pen at a time: each mark starts when the previous one is finished, never before it is said."""
    t = DONE[code]
    for make, said in items:
        at = max(t, said)
        fn = make(at)
        G[code].extras.append(fn)
        t = at + fn.sound[1] + 0.15


chain('G30', [(lambda at: BD.write('IXe siècle', 64, 0.5, 1.10, at, frac='ink'), cue(10, 'IXe'))])
chain('G35', [(lambda at: distance((0.37, 0.235), 0.63, at, 0.5), cue(11, 'bras'))])            # « à portée de bras »: eye to eye
chain('G36', [(lambda at: distance((0.77, 0.497), 0.93, at, 0.6), cue(11, 'centaines'))])            # short of the drawing's edge
chain('G37', [(lambda at: distance((0.70, 0.30), 0.97, at, 0.6), cue(11, 'kilometres'))])            # further
chain('G38', [(lambda at: distance((0.63, 0.45), 1.02, at, 1.0), cue(11, 'continents'))])       # the longest line, stopping short of the turret's view (its neighbour)
chain('G39', [(lambda at: BD.write('On Killing', 72, 0.5, 1.12, at, frac='ink'), cue(11, 'Killing'))])

SHOTS = [(0.0, BOARD.scene)]


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
