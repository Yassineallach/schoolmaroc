"""Act N: <title>. Narration clips <a>-<b>.

Copy this to <project>/actN.py. Every scene is a function sX(t, D) -> RGBA canvas, where t is
scene-local seconds and D the scene length. Every reveal and every cut is tied to a SPOKEN WORD
via cue(clip, 'phrase'), never to a hand-typed second. The first run of this file creates the
timing for CLIPS automatically; then pick phrases from timing/words.txt.

  cue(clip, 'phrase')            act-local start of the phrase's first occurrence in that clip
  cue(clip, 'phrase', 2)         ... its 2nd occurrence
  cue(clip, 'phrase', 1, 'e')    ... the END of its last word
  w(cue(...))                    the same moment in scene-local time (use inside scenes)
  cue(...) - LEAD                a cut, placed just before the word so the crossfade lands on it
"""
import os, sys
from PIL import Image
from vox import *  # noqa: F401,F403  (render_all.py puts the skill's scripts on the path)

CLIPS = (1, 2)            # narration clips of this act, in order
cue = make_cue(CLIPS)

# ---- assets: approved, leftover-checked cut-outs and plates only (see SKILL.md, phase 4) ----
def cut(name, h, **k):
    return Cutout(Image.open(asset(name)).convert('RGBA'), h, **k)


HERO = cut('hero_standing.png', 900)          # transparent cut-out -> gets the red stroke + shadow
FG = foreground()                             # torn-paper strip that hides the lower bodies
PLATE = PhotoCard(Image.open(asset('E01.png')), 1250, rot=-1.5, seed=11)  # 16:9 plate as a torn print
# (portrait/square plates: use width ~700 so the card stays inside the 1080 frame)
NOTE = document(620, 760, ['Line one of the record', '---', 'Line two', '---', '---'], seed=5, title='THE RECORD')


def sA(t, D):
    """<the exact sentence(s) this scene covers, copied from the transcript>"""
    c = background()
    headline(c, (W / 2, 140), 'BIG TITLE WORD', 110, t, w(cue(1, 'title word')))
    HERO.place(c, 620, H + 40, t, 0.0, side='left')     # 0.0 = on screen from the cut
    c.alpha_composite(FG)                                # foreground goes over the cut-outs
    typewriter(c, (1120, 420), 'a typed caption', 46, t, w(cue(1, 'caption')), cursor=False)
    return c


def sB(t, D):
    """<sentence>"""
    c = background()
    PLATE.place(c, W / 2, 500, t, 0.0, zoom=lerp(1.0, 1.08, ease(t / D)))   # slow push-in
    place_sheet(c, NOTE, 1500, 560, t, w(cue(2, 'record')), rot=3)
    stamp(c, 1500, 640, 'RIGGED', 90, t, w(cue(2, 'rigged')))
    marker_circle(c, 1500, 420, 240, 70, ease((t - w(cue(2, 'line one'))) / 0.5))
    return c


SHOTS = [(0.0, sA), (cue(2, 'first words of clip two') - LEAD, sB)]
END = cue.total            # last act: cue.total + 3.0 to hold the end title in silence


def frame(t):
    return make_frame(SHOTS, END, t)


if __name__ == '__main__':
    # python actN.py sheet preview.png 1.0 4.5 9.0   -> contact sheet of those moments (QC)
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
