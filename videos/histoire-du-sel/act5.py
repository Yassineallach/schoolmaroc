"""Acte 5 : L'abondance. Narration clips 12-13, then the closing view of the whole board.

The camera flies back across the board to the bottom row, under act 2's three methods: the industrial
salt works and the two trends crossing (production up, price down; illustrative, no numbers), then a
wide look over the ancient methods above while « les mêmes méthodes » is said, then their modern
counterparts drawn under them (salt pond, evaporator, dynamite). Then Morton's free-flowing salt
(« 1911 », the clumping diagram), the shakers and the map of North America and Europe. After the last
word the camera goes home: the last goat is drawn under the first goats, and the camera pulls back
until the whole board is in view.
"""
import json
import sys
from vox import *  # noqa: F401,F403
import style as st
import board as BD
import act1
import act2
import act3
import act4
import brand

CLIPS = (12, 13)
cue = make_cue(CLIPS)
LAND = 0.35


def arrive(clip, phrase):
    return cue(clip, phrase) + LAND


CURVE = json.load(open(asset('C01.json')))
E = BD.Entry
T_LAST = cue.total + 0.6                     # after « …d'Europe. »
ENTRIES = [
    BD.cluster(E('C01', 'production et prix', None), 'G27'),                            # « Au tournant du XXe siècle… la production… »
    E('G27', 'salines industrielles', cue(12, 'Les producteurs'), stay=True),            # « …des millions de tonnes de sel chaque année »
    BD.cluster(E('G34', 'bassin salant moderne', arrive(12, 'avec les memes')), 'G35', 'G28'),   # « …les mêmes méthodes, perfectionnées… »
    E('G35', 'évaporateur industriel', cue(12, 'mais'), stay=True),                      # « …aidés d'outils plus sophistiqués »
    E('G28', 'explosifs dans la mine', cue(12, "'explosifs"), stay=True),
    E('G29', 'la boîte de sel', arrive(13, 'abondant'), focus=(0.5, 0.5)),
    E('G36', 'le sel qui ne colle plus', arrive(13, 'ajouter'), focus=(0.5, 0.5)),
    E('G30', 'salière et poivrière', arrive(13, 'les salieres'), focus=(0.5, 0.5)),
    E('M09', 'Amérique du Nord et Europe', arrive(13, 'trone'), focus=(0.5, 0.5)),
    E('G31', 'la chèvre et la salière', T_LAST + 4.2, focus=(0.5, 0.5), max_dur=3.0),     # home: under the first goats
]
MARKS = []
BEFORE = act1.ENTRIES + act2.ENTRIES + act3.ENTRIES + act4.ENTRIES
BEFORE_MARKS = act1.MARKS + act2.MARKS + act3.MARKS + act4.MARKS
# the ending (the user's choice): no pull-back over the board; once the last goat is drawn, the
# camera moves in on it, the goat and the salt shaker, and holds
_gx, _gy = BD.world('G31')
_gw, _gh = 1500 * BD.SIZE.get('G31', 1.0) * BD.SCALE, 880 * BD.SIZE.get('G31', 1.0) * BD.SCALE
CLOSE = E('CLOSE', 'gros plan sur la chèvre', ENTRIES[-1].arrive + 3.0 + 1.2 + BD.CLOSE_PAN, look=True,
          at=(_gx - 0.12 * _gw, _gy + 0.12 * _gh), zoom=1.45)
ENTRIES.append(CLOSE)
END = CLOSE.arrive + 3.0                       # hold on the goat and the shaker
BOARD = BD.Board(ENTRIES, before=BEFORE, end=END, marks=MARKS, before_marks=BEFORE_MARKS)
G = {e.code: e for e in ENTRIES}
DONE = {c: e.start + e.dur + 0.15 for c, e in G.items()}
G['G29'].extras.append(BD.write('Morton Salt', 64, 0.5, 1.07, max(cue(13, 'Morton'), DONE['G29']), frac=True))
G['G36'].extras.append(BD.write('carbonate de magnésium', 56, 0.5, 1.07, max(cue(13, 'carbonate'), DONE['G36']), frac=True))
_P9 = json.load(open(asset('M09.json')))['pins']
G['M09'].extras.append(BD.write('Amérique du Nord', 56, 0.25, 1.05, max(cue(13, "'Amerique"), DONE['M09']), frac=True))
G['M09'].extras.append(BD.write('Europe', 56, 0.82, 1.05, max(cue(13, "'Europe"), DONE['M09']) + 1.6, frac=True))

# the chart: « production » on the rising line, « prix » on the falling one, then the quantity
cw, ch = BD.Entry('C01', '').d.layers(BD.SCALE)[0].size
cx0, cy0 = BD.world('C01')
up = (cx0 + (CURVE['up_end'][0] - 0.5) * cw, cy0 + (CURVE['up_end'][1] - 0.5) * ch)
down = (cx0 + (CURVE['down_end'][0] - 0.5) * cw, cy0 + (CURVE['down_end'][1] - 0.5) * ch)
MARKS += [BD.Note('production', 54, (up[0] - 330, up[1] - 50), max(cue(12, 'explose'), DONE['C01'])),
          BD.Note('prix', 54, (down[0] - 120, down[1] - 50), cue(12, "'est effondre")),
          BD.Note('des millions de tonnes', 58, (BD.world('G27')[0], BD.world('G27')[1] + 420), max(cue(12, 'millions'), DONE['G27']), dur=0.9)]
G['G29'].extras.append(BD.write('1911', 90, 0.18, 0.12, max(cue(13, '1911'), DONE['G29']), frac=True))

SHOTS = [(0.0, BOARD.scene)]
if brand.CFG['outro']['enabled']:                     # the channel outro after the whole-board view
    SHOTS.append((END, brand.outro_scene, 'up'))
    END = END + brand.outro_seconds()


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
