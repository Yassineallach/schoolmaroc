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
from ta import locked, chainer, write

CLIPS = (13, 14)
cue = make_cue(CLIPS)
LAND = 1.2


def arrive(clip, phrase, n=1):
    return cue(clip, phrase, n) + LAND


E = BD.Entry
ENTRIES = [
    E('G34', 'la presse', None, max_dur=1.4),                            # « …l'essor de l'idéologie raciste »
    locked(E('G35', 'bâton et lance', arrive(13, 'En'), max_dur=1.4)),  # « En Afrique… sanction pénale ou guerre entre tribus »
    E('G36', "l'église", arrive(13, 'Mais'), max_dur=2.6),              # « …religion universelle… idéaux d'égalité »
    E('G37', 'la fausse science', arrive(13, 'Ils') + 0.4, max_dur=2.0),      # « …biologiquement inférieurs… étayer cette théorie »
    locked(E('G38', 'la porte', arrive(13, 'C') + 0.6, max_dur=1.8)),         # « …un fondement racial… l'égalité »
    E('G44', 'les mains libres', arrive(14, 'A'), max_dur=5.0),         # the last drawing: « …bien après son abolition »
]
HOLD = 1.8                                                              # a short hold on the hands after the last word
END = cue.total + HOLD
BOARD = BD.Board(ENTRIES, before=act5.BOARD.before + act5.ENTRIES, end=END)
G, chain = chainer(ENTRIES)

chain('G34', [(lambda at: write("l'idéologie raciste", 64, 0.50, 1.08, at, frac='ink', dur=1.0), cue(13, 'raciste'))])
chain('G35', [(lambda at: write('en Afrique : sanction ou guerre', 60, 0.50, 1.07, at, frac='ink', dur=1.3), cue(13, 'sanction'))])
chain('G36', [(lambda at: write('une religion universelle', 60, 0.50, 1.08, at, frac='ink', dur=1.3), cue(13, 'universelle')),
              (lambda at: write("contraire à l'égalité", 60, 0.50, 1.20, at, frac='ink', dur=0.8), cue(13, "'égalité"))])
chain('G37', [(lambda at: write('« biologiquement inférieurs »', 60, 0.50, 1.08, at, frac='ink', dur=1.3), cue(13, 'inferieurs')),
              (lambda at: write('pour étayer une théorie', 60, 0.50, 1.20, at, frac='ink', dur=1.0), cue(13, 'théorie'))])
chain('G38', [(lambda at: write('un fondement racial', 62, 0.50, 1.07, at, frac='ink', dur=1.1), cue(13, 'racial')),
              (lambda at: write("l'égalité interdite", 62, 0.50, 1.18, at, frac='ink', dur=1.0), cue(13, '\'égalité', 2))])
chain('G44', [(lambda at: write('une injustice immense', 64, 0.50, 1.07, at, frac='ink', dur=1.2), cue(14, 'immense')),
              (lambda at: write('bien après son abolition', 64, 0.50, 1.19, at, frac='ink', dur=1.3), cue(14, 'abolition'))])

SHOTS = [(0.0, BOARD.scene)]
if brand.CFG['outro']['enabled']:                     # the channel outro after the closing hold
    SHOTS.append((END, brand.outro_scene, 'up'))
    END = END + brand.outro_seconds()


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
