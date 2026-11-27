"""Acte 6 : Une idéologie. Narration clips 13-14, the slowest act, then the closing hold and the
channel outro.

The printing press (racist ideology), the staff and the spear (slavery in Africa: penalty or war),
the church (equality preached), the « race science » desk (the false theory), the locked door
(equality forbidden), and the last drawing: the free hands, the rope marks still on the wrists,
answering the bound hands of the hook. A short hold after the last word (no closing zoom), then the
outro. Locked off: G35, G38.
"""
import sys
from vox import *  # noqa: F401,F403
import style as st
import board as BD
import brand
import act5
from ta import locked, chainer, write, side, over, big, under, mark

CLIPS = (13, 14)
cue = make_cue(CLIPS)
LAND = 1.2


def arrive(clip, phrase, n=1):
    return cue(clip, phrase, n) + LAND


E = BD.Entry

# The closing loop (the user chose it): the free hands are drawn beside the bound hands of the hook.
# The camera travels back across the whole board to the beginning, and the last view frames both.
gx, gy = BD.LAYOUT['G01']
BD.LAYOUT['G44'] = (gx - 1180, gy)
LOOP_AT = ((gx - 250, gy + 150), 0.66)                     # both pairs of hands and the words beside the first

ENTRIES = [
    E('G34', 'la presse', None, max_dur=1.4),                            # « …l'essor de l'idéologie raciste »
    locked(E('G35', 'bâton et lance', arrive(13, 'En'), max_dur=1.4)),  # « En Afrique… sanction pénale ou guerre entre tribus »
    E('G36', "l'église", arrive(13, 'Mais'), max_dur=2.6),              # « …religion universelle… idéaux d'égalité »
    E('G37', 'la fausse science', arrive(13, 'Ils') + 0.4, max_dur=2.0),   # « …biologiquement inférieurs… étayer cette théorie »
    locked(E('G38', 'la porte', arrive(13, 'C') + 0.6, max_dur=1.8)),   # « …un fondement racial… l'égalité »
    E('G44', 'les mains libres', cue(14, 'A') + 2.6, max_dur=4.0),      # the last drawing, beside the first: « …bien après son abolition »
]
ENTRIES[-1].keep_at = LOOP_AT
HOLD = 2.5                                                              # a short hold on the two pairs of hands after the last word
END = cue.total + HOLD
BOARD = BD.Board(ENTRIES, before=act5.BOARD.before + act5.ENTRIES, end=END,
                 mood=[(0.0, act5.QUIET), (cue(14, 'A'), act5.QUIET), (cue(14, 'A') + 4.0, (1.0, 0.0, 0.92))])   # lifts a little at the end
G, chain = chainer(ENTRIES)
G['G44'].cam_dx = G['G44'].cam_dy = 0.0

chain('G34', [(lambda at: under("l'idéologie raciste", at, size=68, dur=1.0), cue(13, 'raciste'))])
chain('G35', [(lambda at: side('en Afrique :', at, size=66, y=0.36, dur=0.8), cue(13, 'sanction')),
              (lambda at: side('sanction ou guerre', at, size=66, y=0.52, dur=1.0), cue(13, 'guerre'))])
chain('G36', [(lambda at: under('une religion universelle', at, dur=1.3), cue(13, 'universelle')),
              (lambda at: under("contraire à l'égalité", at, line=1, dur=0.8), cue(13, "'égalité"))])
chain('G37', [(lambda at: under('« biologiquement inférieurs »', at, size=64, dur=1.3), cue(13, 'inferieurs')),
              (lambda at: under('pour étayer une théorie', at, line=1, size=60, dur=1.0), cue(13, 'théorie'))])
chain('G38', [(lambda at: side('un fondement racial', at, size=80, y=0.40, dur=1.1), cue(13, 'racial')),
              (lambda at: side("l'égalité interdite", at, size=62, y=0.58, dur=1.0), cue(13, "'égalité", 2))])
chain('G44', [(lambda at: under('une injustice immense', at, size=76, dur=1.2), cue(14, 'immense')),
              (lambda at: mark('ring', (0.08, 0.26, 0.42, 0.40), at, 0.5), cue(14, 'répercussions')),   # the rope marks…
              (lambda at: mark('ring', (0.53, 0.26, 0.87, 0.40), at, 0.5), cue(14, 'répercussions')),   # …on both wrists
              (lambda at: under('bien après son abolition', at, line=1, size=76, dur=1.3), cue(14, 'abolition'))])

SHOTS = [(0.0, BOARD.scene)]
if brand.CFG['outro']['enabled']:                     # the channel outro after the closing hold
    SHOTS.append((END, brand.outro_scene, 'up'))
    END = END + brand.outro_seconds()


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
