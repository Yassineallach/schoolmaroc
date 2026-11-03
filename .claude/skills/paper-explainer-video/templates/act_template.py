"""Act N: <title>. Narration clips <a>-<b>.

Copy this to <project>/actN.py. Every scene is a function sX(t, D) -> Shot, where t is
scene-local seconds and D the scene length. Every reveal, camera move and cut is tied to a
SPOKEN WORD via cue(clip, 'phrase'), never to a hand-typed second. The first run of this file
creates the timing for CLIPS automatically; then pick phrases from timing/words.txt.

  cue(clip, 'phrase')            act-local start of the phrase's first occurrence in that clip
  cue(clip, 'phrase', 2)         ... its 2nd occurrence
  cue(clip, 'phrase', 1, 'e')    ... the END of its last word
  w(cue(...))                    the same moment in scene-local time (use inside scenes)
  cue(...) - LEAD                a cut, placed just before the word so the wipe lands on it

Layers (style.py):  s.mid = paper on the desk + marks made on it (stamps, marker circles)
                    s.top = headline type in the composition      s.hud = captions / labels
Presets (presets.py) and annotations (annotate.py): pick ONE per beat, chosen by what the
narration is doing.
"""
import sys
from PIL import Image
from vox import *  # noqa: F401,F403  (render_all.py puts the skill's scripts on the path)
import style as st
import presets as P
import annotate as A
from style import ENTER, Shot, words, tag, underline, kicker

CLIPS = (1, 2)            # narration clips of this act, in order
cue = make_cue(CLIPS)

# ---- assets: approved, leftover-checked files only (SKILL.md phase 4) ----
PLATE = P.print_card(Image.open(asset('E01.png')), 1240, seed=11)          # painted plate as a torn print
PHOTO = P.print_card(Image.open(asset('person.jpg')), 520, seed=21)        # user-supplied photograph
COVER = P.paper_card(PHOTO.width + 10, PHOTO.height + 10, seed=33, text='?', size=200)
NOTE = document(620, 720, ['Line one of the record', '---', 'Line two', '---', '---'], seed=5, title='THE RECORD')
CLIP = P.clipping('Words the narration says', date='1988')                # only facts that are spoken


def sA(t, D):
    """<the exact sentence(s) this scene covers, copied from the transcript>"""
    s = Shot(t, D)
    s.camera(1.0, 1.06, (W / 2, H / 2), (760, 480))                         # slow push across the shot
    P.mask_reveal(s.mid, PLATE, W / 2, 500, t, 0.1, dur=2.0)                 # opening image through a torn hole
    P.stamp_hit(s.mid, '1985', 520, 250, t, w(cue(1, 'nineteen')), size=96, shot=s)
    tag(s.hud, (W / 2, 975), 'A SHORT RED LABEL', 44, t, w(cue(1, 'label words')))
    kicker(s.hud, t, 1, 'Act title')                                         # chapter label, first shot only
    return s


def sB(t, D):
    """<sentence>"""
    s = Shot(t, D)
    s.zoom_to((1000, 90, 1660, 850), w(cue(2, 'record')), dur=2.2, fill=0.86) # travel into the document
    P.unfold(s.mid, NOTE, 1330, 470, t, ENTER + 0.15)                        # present at the cut: ENTER
    A.ring(s.mid, (1040, 345, 1300, 405), t, w(cue(2, 'line one')), until=w(cue(2, 'big')))      # settles when the narration moves on
    A.sweep(s.top, A.words_box((520, 300), 'BIG WORDS', 96, 'WORDS'), t, w(cue(2, 'words')))   # behind the word: draw first
    words(s.top, (520, 300), 'BIG WORDS', 96, t, [w(cue(2, 'big')), w(cue(2, 'words'))])
    return s


def sC(t, D):
    """<sentence>"""
    s = Shot(t, D)
    s.camera(1.03, 1.03)
    P.put(s.mid, PHOTO, 520, 470)
    P.tear_reveal(s.mid, COVER, 520, 470, t, w(cue(2, 'name')) - 0.15)       # the reveal of who it is
    words(s.top, (520, 950), 'FULL NAME', 72, t, w(cue(2, 'name')))
    P.slide(s.mid, CLIP, (W + 400, 700), (1300, 560), t, w(cue(2, 'published')), rot=4, key='clip')
    return s


SHOTS = [
    (0.0, sA),
    (cue(2, 'first words of clip two') - LEAD, sB, 'up'),     # 'up' = new sheet slides over; 'lr' / 'rl' = torn wipe
    (cue(2, 'later words') - LEAD, sC, 'lr'),
]
END = cue.total            # last act: cue.total + 3.0 to hold the end title in silence


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    # python actN.py sheet preview.png 1.0 4.5 9.0   -> contact sheet of those moments (QC)
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
