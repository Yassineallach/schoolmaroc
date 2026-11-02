"""Act 5: The Arrow of Time. Narration clips 11-12."""
import sys, math
import numpy as np
from PIL import Image, ImageDraw
from vox import *  # noqa: F401,F403
import style as st
import presets as P
from style import sfx, ENTER, Shot, words, tag, underline, kicker

CLIPS = (11, 12)
cue = make_cue(CLIPS)

INDIGO = (52, 52, 110)
LAV = (150, 148, 200)
TERRA = (205, 88, 48)

CUP = P.load(asset('c02_cup.png'), width=440)
SHARDS = P.load(asset('c03_shards.png'), width=440)
GLOBE = P.load(asset('c04_globe.png'), height=520)


def book_cover(w=460, h=690):
    b = Image.new('RGBA', (w, h), INDIGO + (255,))
    d = ImageDraw.Draw(b)
    d.rectangle((22, 22, w - 22, h - 22), outline=CREAM + (255,), width=3)
    for i, s in enumerate(('A BRIEF', 'HISTORY', 'OF TIME')):
        d.text((w / 2, 125 + i * 66), s, font=F_HEAD(55), fill=CREAM + (255,), anchor='mm')
    cx, cy = w / 2, 440
    for r, col in ((115, LAV), (80, CREAM), (35, INDIGO)):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col + (255,), width=4)
    d.ellipse((cx - 11, cy - 11, cx + 11, cy + 11), fill=RED + (255,))
    d.text((w / 2, h - 70), 'STEPHEN HAWKING', font=F_SERIF(30), fill=CREAM + (255,), anchor='mm')
    b.putalpha(torn_mask(w, h, 41, amp=3, step=16))
    return b


BOOK = book_cover()
QCARD = P.paper_card(900, 220, seed=121, colour=(246, 241, 229), text='THE OLDEST QUESTION', size=70)
QCARD_FLIPPED = QCARD.rotate(180)


def sA(t, D):
    """Yet the book's real subject is hidden in its title."""
    s = Shot(t, D)
    s.camera(1.0, 1.0)
    s.push(w(cue(11, 'title')), 0.12, (W / 2, 330), dur=1.2)
    P.drop(s.mid, BOOK, W / 2, 480, t, ENTER, rot=0, spin=-8, key='book5')                       # 2
    a = w(cue(11, 'title'))
    sfx('marker', a, W / 2, dur=0.55)
    marker_circle(s.mid, W / 2, 400, 200, 52, ease((t - a) / 0.55), width=9, seed=3)
    words(s.hud, (W / 2, 950), "the book's real subject", 46, t, [w(cue(11, x)) for x in ("the book's", "book's", 'real', 'subject')], font=F_TYPE)
    kicker(s.hud, t, 5, 'The arrow of time')
    return s


def sB(t, D):
    """Time, Hawking argues, is not simply a backdrop for events. It has a direction, and that
    direction needs explaining."""
    s = Shot(t, D)
    s.camera(1.0, 1.04)
    words(s.top, (W / 2, 330), 'TIME', 200, t, w(cue(11, 'Time,')))
    words(s.hud, (W / 2, 520), 'not simply a backdrop for events', 46, t,
          [w(cue(11, x)) for x in ('not simply', 'simply', 'a backdrop', 'backdrop', 'for events', 'events')], font=F_TYPE)
    a = w(cue(11, 'direction'))
    sfx('marker', a, W / 2, dur=0.8)
    marker_line(s.mid, [(360, 700), (900, 690), (1540, 700)], ease((t - a) / 0.8), width=12)
    if t > a + 0.8:
        ImageDraw.Draw(s.mid).polygon([(1540, 670), (1600, 700), (1540, 730)], fill=RED + (255,))
    words(s.top, (W / 2, 800), 'IT HAS A DIRECTION', 64, t, [w(cue(11, x)) for x in ('It has', 'has a', 'a direction', 'direction')])
    tag(s.hud, (W / 2, 950), 'THAT NEEDS EXPLAINING', 50, t, w(cue(11, 'needs')))
    return s


TABLE_Y, EDGE_X = 560, 1000


def sC(t, D):
    """A teacup slides off a table and shatters."""
    s = Shot(t, D)
    s.camera(1.0, 1.0)
    d = ImageDraw.Draw(s.mid)
    d.rectangle((-20, TABLE_Y, EDGE_X, TABLE_Y + 34), fill=(150, 132, 112, 255))           # the table edge
    d.rectangle((-20, TABLE_Y + 34, EDGE_X - 20, TABLE_Y + 46), fill=(120, 104, 88, 255))
    d.line((0, 940, W, 940), fill=(150, 132, 112, 200), width=3)                           # the floor
    sl, off, sh = w(cue(11, 'slides')), w(cue(11, 'off a')), w(cue(11, 'shatters'))
    ch = CUP.height
    if t < sh:
        if t < off:                                                       # sliding along the table
            x = lerp(520, EDGE_X + 60, ease((t - sl) / (off - sl + 0.25)))
            y, ang = TABLE_Y - ch / 2 + 6, 0
        else:                                                             # tipping over the edge and falling
            u = min(1.0, (t - off) / (sh - off))
            x = EDGE_X + 60 + 160 * u
            y = TABLE_Y - ch / 2 + 6 + (940 - TABLE_Y) * u * u
            ang = -70 * u
        if t >= ENTER:
            P.put(s.mid, P.rot_scale(CUP, ang, 1.0), x, y, lift=0.3 if t > off else 0.0)
        sfx('slide', sl, 700, dur=off - sl + 0.3)
    else:
        P.put(s.mid, SHARDS, EDGE_X + 220, 940 - SHARDS.height / 2 + 30)
    sfx('shatter', sh, EDGE_X + 220)
    s.hit(sh)
    words(s.top, (1500, 300), 'A TEACUP', 70, t, w(cue(11, 'teacup')))
    words(s.top, (1500, 390), 'SHATTERS', 70, t, sh, fill=RED)
    return s


SH_POS = (W / 2, 560)


def sD(t, D):
    """Nothing in the laws of motion forbids the shards from leaping up and fusing back together,
    yet no one has ever seen it happen."""
    s = Shot(t, D)
    s.camera(1.0, 1.03)
    lp, yet = w(cue(11, 'leaping')), w(cue(11, 'yet no'))
    if t < lp:
        P.put(s.mid, SHARDS, *SH_POS)
    elif t < yet:
        P.assemble(s.mid, CUP, *SH_POS, t, lp, n=9, dur=0.8, stagger=0.06, seed=7)                # 10
    else:
        P.assemble(s.mid, CUP, *SH_POS, t, yet, n=9, dur=0.7, stagger=0.04, seed=7, reverse=True)
        if t > yet + 0.9:
            P.put(s.mid, P.fade_img(SHARDS, ease((t - yet - 0.9) / 0.3)), *SH_POS)
    P.stamp_hit(s.top, 'NEVER SEEN', W / 2, 560, t, w(cue(11, 'ever seen')), size=110, ang=-9, shot=s)   # 7
    words(s.hud, (W / 2, 120), 'nothing in the laws of motion forbids it', 44, t,
          [w(cue(11, x)) for x in ('Nothing', 'in the', 'the laws', 'laws', 'of motion', 'motion', 'forbids', 'forbids')], font=F_TYPE)
    return s


def sE(t, D):
    """Hawking ties this one-way arrow to the steady growth of disorder, to the way memory works,
    and to the expansion of the cosmos itself."""
    s = Shot(t, D)
    s.camera(1.0, 1.04)
    a = w(cue(11, 'arrow'))
    sfx('marker', a, W / 2, dur=0.9)
    marker_line(s.mid, [(200, 470), (W / 2, 462), (1720, 470)], ease((t - a) / 0.9), width=14)
    if t > a + 0.9:
        ImageDraw.Draw(s.mid).polygon([(1720, 434), (1790, 470), (1720, 506)], fill=RED + (255,))
    words(s.top, (W / 2, 330), 'ONE-WAY ARROW', 80, t, [w(cue(11, 'one', 2)), w(cue(11, 'arrow'))])
    for x, lab, ph in ((430, 'DISORDER', 'disorder'), (W / 2, 'MEMORY', 'memory'), (1490, 'EXPANSION', 'expansion')):
        tag(s.top, (x, 600), lab, 48, t, w(cue(11, ph)))
    words(s.hud, (W / 2, 900), 'of the cosmos itself', 44, t, [w(cue(11, x)) for x in ('of the', 'the cosmos', 'cosmos', 'itself')], font=F_TYPE)
    return s


def sF(t, D):
    """He then turns the oldest question of all on its head. Asking what came before the Big Bang,
    he suggests,"""
    s = Shot(t, D)
    s.camera(1.0, 1.0)
    P.drop(s.mid, QCARD, W / 2, 420, t, ENTER, rot=0, spin=4, height=0.5, key='qcard')
    P.flip(s.mid, QCARD, QCARD_FLIPPED, W / 2, 420, t, w(cue(12, 'head')) - 0.3, dur=0.8, axis='x')   # 11
    words(s.top, (W / 2, 720), 'WHAT CAME BEFORE', 84, t, [w(cue(12, 'what came')), w(cue(12, 'came')), w(cue(12, 'before'))])
    words(s.top, (W / 2, 830), 'THE BIG BANG?', 84, t, [w(cue(12, 'the Big')), w(cue(12, 'Big')), w(cue(12, 'Bang,'))], fill=RED)
    return s


GC = (W / 2, 560)


def sG(t, D):
    """may be like asking what lies north of the North Pole."""
    s = Shot(t, D)
    s.camera(1.0, 1.04, GC)
    P.drop(s.mid, GLOBE, *GC, t, ENTER, rot=0, spin=10, key='globe')                              # 2
    a = w(cue(12, 'north'))
    sfx('marker', a, W / 2, dur=0.7)
    marker_line(s.mid, [(GC[0], GC[1] + 40), (GC[0] + 4, GC[1] - 120), (GC[0], GC[1] - 262)], ease((t - a) / 0.7), width=10)
    q = w(cue(12, 'Pole.'))
    words(s.top, (GC[0], GC[1] - 330), '?', 120, t, q, fill=RED)
    words(s.hud, (W / 2, 990), 'north of the North Pole', 48, t, [w(cue(12, x)) for x in ('north', 'of the', 'the North', 'North', 'Pole.')], font=F_TYPE)
    return s


def sH(t, D):
    """The universe could be finite and still have no edge, no starting line where something had
    to set it going."""
    s = Shot(t, D)
    s.camera(1.04, 1.0, GC)
    P.put(s.mid, GLOBE, *GC)
    a = w(cue(12, 'no edge'))
    sfx('marker', a, W / 2, dur=1.2)
    pts = [(GC[0] + 300 * math.cos(u), GC[1] + 300 * 0.93 * math.sin(u)) for u in np.linspace(-math.pi / 2, 1.5 * math.pi, 90)]
    marker_line(s.mid, pts, ease((t - a) / 1.4), width=8, seed=6)                 # round and round, never an edge
    tag(s.hud, (W / 2, 110), 'FINITE', 64, t, w(cue(12, 'finite')))
    tag(s.hud, (W / 2, 950), 'BUT NO EDGE', 64, t, a)
    words(s.hud, (W / 2, 1035), 'no starting line', 40, t, [w(cue(12, x)) for x in ('no starting', 'starting', 'line')], font=F_TYPE)
    return s


SHOTS = [
    (0.0, sA),
    (cue(11, 'Time,') - LEAD, sB, 'up'),
    (cue(11, 'A teacup') - LEAD, sC, 'rl'),
    (cue(11, 'Nothing') - LEAD, sD, 'up'),
    (cue(11, 'Hawking ties') - LEAD, sE, 'lr'),
    (cue(12, 'He then') - LEAD, sF, 'rl'),
    (cue(12, 'may be') - LEAD, sG, 'up'),
    (cue(12, 'The universe') - LEAD, sH, 'lr'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
