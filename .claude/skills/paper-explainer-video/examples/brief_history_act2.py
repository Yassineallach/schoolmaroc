"""Act 2: One Equation. Narration clips 5-6."""
import sys, math
import numpy as np
from PIL import Image, ImageDraw
from vox import *  # noqa: F401,F403
import style as st
import presets as P
from style import sfx, ENTER, Shot, words, tag, underline, kicker

CLIPS = (5, 6)
cue = make_cue(CLIPS)

INDIGO = (52, 52, 110)
LAV = (150, 148, 200)

ARI = P.print_card(Image.open(asset('aristotle.jpg')), 400, seed=51)
GAL = P.print_card(Image.open(asset('galileo.jpg')), 420, seed=52)
EIN = P.print_card(Image.open(asset('einstein.jpg')), 400, seed=53)
SCOPE = P.print_card(Image.open(asset('p02_telescope.png')), 1240, seed=54)


def textbook():
    """A dense textbook page: rows of formula-like marks (texture only, no real equations)."""
    w, h = 660, 800
    im = P.paper_card(w, h, seed=61, colour=(246, 241, 229))
    d = ImageDraw.Draw(im)
    d.text((w / 2, 60), 'CHAPTER 4', font=F_SERIF(34), fill=INK + (255,), anchor='mm')
    d.line((60, 92, w - 60, 92), fill=INK + (255,), width=2)
    r = np.random.default_rng(3)
    f = F_SERIF(30)
    y = 140
    while y < h - 60:
        if r.random() < 0.45:          # a displayed "formula": letters, operators, a fraction bar
            x = 90
            for _ in range(r.integers(4, 8)):
                tok = r.choice(list('abcxyzkn') + ['=', '+', '−', '(', ')'])
                d.text((x, y), tok, font=f, fill=INK + (255,), anchor='lm')
                x += 34
            d.line((x + 10, y, x + 110, y), fill=INK + (255,), width=2)
            d.text((x + 60, y - 20), r.choice(list('abmn')), font=F_SERIF(24), fill=INK + (255,), anchor='mm')
            d.text((x + 60, y + 20), r.choice(list('xyzr')), font=F_SERIF(24), fill=INK + (255,), anchor='mm')
            y += 74
        else:
            d.line((60, y, 60 + r.uniform(0.6, 0.95) * (w - 120), y), fill=(150, 146, 140, 255), width=3)
            y += 30
    return im


BOOKPAGE = textbook()


def book_block(colour, w=360, h=54, seed=0):
    b = Image.new('RGBA', (w, h), colour + (255,))
    d = ImageDraw.Draw(b)
    d.rectangle((0, 0, w - 1, h - 1), outline=tuple(max(0, c - 40) for c in colour) + (255,), width=3)
    d.line((22, 10, 22, h - 10), fill=CREAM + (200,), width=3)
    d.line((w - 22, 10, w - 22, h - 10), fill=CREAM + (200,), width=3)
    return b


BOOKS = [book_block(c, 360 + (i % 3) * 22) for i, c in enumerate([INDIGO, (205, 88, 48), (233, 214, 187), INDIGO, (92, 82, 72), (205, 88, 48), (150, 148, 200), INDIGO])]


def sketch_sheet():
    """Thought-experiment page: a hand-inked orbit, a falling ball, arrows."""
    w, h = 760, 540
    im = P.paper_card(w, h, seed=71)
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.ellipse((90, 120, 420, 420), outline=ink, width=4)
    d.ellipse((235, 250, 275, 290), fill=(205, 88, 48, 255))
    d.ellipse((400, 250, 430, 280), fill=INDIGO + (255,))
    d.line((415, 265, 470, 200), fill=ink, width=4)
    d.polygon([(470, 200), (450, 206), (464, 220)], fill=ink)
    for i in range(6):
        y = 120 + i * 55
        d.ellipse((590, y, 616, y + 26), outline=ink, width=3)
    d.line((603, 90, 603, 470), fill=(150, 146, 140, 255), width=2)
    d.polygon([(603, 490), (590, 465), (616, 465)], fill=ink)
    for x in range(80, 700, 26):
        d.line((x, 480, x + 12, 480), fill=(150, 146, 140, 255), width=2)
    return im


SKETCH = sketch_sheet()


def sA(t, D):
    """Unlike the textbooks covering the same ground, the book contains almost no mathematics."""
    s = Shot(t, D)
    s.camera(1.0, 1.05, (900, 500))
    P.slide(s.mid, BOOKPAGE, (-500, 560), (760, 500), t, ENTER, dur=1.1, rot=-2, key='tb')        # 9
    for i, y in enumerate((222, 370, 518, 666)):
        a = w(cue(5, 'no mathematics')) + 0.12 * i
        if t > a:
            sfx('marker', a, 760, dur=0.25)
        strike(s.mid, 470, 1010, y, ease((t - a) / 0.3), width=10)
    words(s.top, (1440, 420), 'ALMOST NO', 76, t, [w(cue(5, 'almost')), w(cue(5, 'no mathematics'))])
    words(s.top, (1440, 520), 'MATHEMATICS', 76, t, w(cue(5, 'mathematics')))
    kicker(s.hud, t, 2, 'One equation')
    return s


def sB(t, D):
    """Hawking was warned that every equation would cut his sales in half,"""
    s = Shot(t, D)
    s.camera(1.0, 1.04, (700, 520))
    half = w(cue(5, 'half'))
    for i, b in enumerate(BOOKS):
        y = 860 - i * 58
        st_ = ENTER + 0.07 * i
        if i >= 4 and t > half:                                         # the top half slides away
            P.slide(s.mid, b, (640, y), (2400, y - 40), t, half + 0.06 * (i - 4), dur=0.9, rot=0, lag=6)
        else:
            P.drop(s.mid, b, 640, y, t, st_, rot=(-2, 1.5, -1, 2)[i % 4], spin=4, height=0.4, key=('bk', i))
    words(s.top, (1380, 380), 'EVERY EQUATION', 70, t, [w(cue(5, 'every')), w(cue(5, 'equation'))])
    tag(s.hud, (1380, 520), 'SALES ÷ 2', 64, t, half)
    return s


def sC(t, D):
    """so he kept exactly one: Einstein's E equals m c squared."""
    s = Shot(t, D)
    s.camera(1.0, 1.06)
    words(s.top, (W / 2, 300), 'exactly one', 54, t, [w(cue(5, 'exactly')), w(cue(5, 'one'))], font=F_TYPE)
    words(s.top, (W / 2, 560), 'E = mc²', 220, t, [w(cue(5, 'E')), w(cue(5, 'equals')), w(cue(5, 'm'))])
    sq = w(cue(5, 'squared'))
    sfx('marker', sq, W / 2, dur=0.5)
    marker_circle(s.top, W / 2 + 40, 565, 420, 170, ease((t - sq) / 0.6), seed=4)
    words(s.hud, (W / 2, 820), "Einstein's", 40, t, w(cue(5, "Einstein's")), font=F_TYPE)
    return s


def sD(t, D):
    """In place of formulas, he builds his arguments from diagrams, thought experiments,"""
    s = Shot(t, D)
    s.camera(1.0, 1.05, (760, 500))
    P.drop(s.mid, SKETCH, 760, 500, t, ENTER, rot=-2.5, spin=-10, key='sk')                         # 2
    words(s.top, (1500, 380), 'diagrams', 56, t, w(cue(5, 'diagrams')), font=F_TYPE)
    underline(s.top, 1380, 1620, 420, t, w(cue(5, 'diagrams')) + 0.3)
    words(s.top, (1500, 560), 'thought', 56, t, w(cue(5, 'thought')), font=F_TYPE)
    words(s.top, (1500, 630), 'experiments', 56, t, w(cue(5, 'experiments')), font=F_TYPE)
    underline(s.top, 1330, 1670, 670, t, w(cue(5, 'experiments')) + 0.4, seed=2)
    return s


def sE(t, D):
    """and the stories of the thinkers who came before him, from Aristotle to Galileo to Einstein."""
    s = Shot(t, D)
    s.camera(1.0, 1.03)
    names = (('ARISTOTLE', 'Aristotle', 520), ('GALILEO', 'Galileo', 960), ('EINSTEIN', 'Einstein.', 1400))
    starts = [w(cue(5, ph)) - 0.25 for _, ph, _ in names]
    P.stack(s.mid, [ARI, GAL, EIN], [(520, 470), (960, 450), (1400, 480)], t, starts, rots=[-4, 2.5, -2])   # 6
    x0 = 300
    for i, (lab, ph, x) in enumerate(names):
        a = w(cue(5, ph))
        marker_line(s.mid, [(x0, 860), (x, 860)], ease((t - a + 0.4) / 0.5), width=6, seed=i)
        x0 = x
        words(s.top, (x, 920), lab, 46, t, a)
    words(s.hud, (W / 2, 120), 'the thinkers who came before him', 40, t, w(cue(5, 'thinkers')), font=F_TYPE)
    return s


def sF(t, D):
    """That history leads to a puzzle."""
    s = Shot(t, D)
    s.camera(1.0, 1.08)
    words(s.top, (W / 2, 470), 'A PUZZLE', 150, t, [w(cue(6, 'a puzzle')), w(cue(6, 'puzzle'))])
    tag(s.hud, (W / 2, 640), 'THAT HISTORY LEADS TO…', 40, t, w(cue(6, 'history')))
    return s


GAL_RECT = (505, 226, 1098, 553)          # the galaxies, in frame pixels of the placed plate


def sG(t, D):
    """In the 1920s, astronomers discovered that distant galaxies are rushing away from Earth."""
    s = Shot(t, D)
    s.camera(1.0, 1.0)
    s.zoom_to(GAL_RECT, w(cue(6, 'distant')), dur=2.4, fill=0.9)                                     # 12
    P.mask_reveal(s.mid, SCOPE, W / 2, 500, t, ENTER, dur=1.6, origin=(0.6, 0.45))                  # 8
    P.stamp_hit(s.mid, '1920s', 1420, 820, t, w(cue(6, '1920s')), size=96, ang=-6, shot=s)          # 7
    words(s.hud, (W / 2, 990), 'rushing away from Earth', 46, t,
          [w(cue(6, x)) for x in ('rushing', 'away', 'from Earth', 'Earth')], font=F_TYPE)
    return s


R = np.random.default_rng(12)
GX = [(math.cos(a) * r, math.sin(a) * r * 0.62, R.uniform(5, 12), R.integers(0, 3)) for a, r in
      zip(R.uniform(0, 2 * math.pi, 46), np.sqrt(R.uniform(0.05, 1.0, 46)) * 760)]


def sH(t, D):
    """The universe is expanding. Run that expansion backward, and everything converges on a single
    point of unimaginable density: the Big Bang."""
    s = Shot(t, D)
    s.camera(1.0, 1.0)
    cx, cy = W / 2, 540
    run, point, bang = w(cue(6, 'Run')), w(cue(6, 'single point')), w(cue(6, 'Big Bang'))
    if t < run:
        k = lerp(0.42, 1.0, ease((t + 0.3) / (run + 0.3)))
    else:
        k = lerp(1.0, 0.0, ease((t - run - 0.2) / (point - run - 0.2)))
    d = ImageDraw.Draw(s.mid)
    for x, y, r, c in GX:
        px, py = cx + x * k, cy + y * k
        col = (INDIGO, (150, 148, 200), (205, 88, 48))[c]
        if t < run and k > 0.5:                                         # motion streaks pointing outward
            n = math.hypot(x, y) or 1
            d.line((px - x / n * 30 * k, py - y / n * 30 * k, px, py), fill=(150, 132, 112, 160), width=2)
        rr = r * (0.6 + 0.4 * k)
        d.ellipse((px - rr, py - rr, px + rr, py + rr), fill=col + (255,))
    sfx('zoom', run + 0.2, None, dur=point - run)
    if t > bang - 0.05:                                                 # the point flares
        u = ease((t - bang + 0.05) / 0.6)
        rad = 14 + 110 * u
        d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=(205, 88, 48, int(255 * (1 - 0.6 * u))))
    elif t > point - 0.2:
        d.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=INK + (255,))
    sfx('stamp', bang, cx)
    words(s.top, (W / 2, 150), 'THE UNIVERSE IS EXPANDING', 70, t,
          [w(cue(6, x)) for x in ('The universe', 'universe', 'is expanding', 'expanding')])
    words(s.hud, (W / 2, 900), 'run it backward', 46, t, [w(cue(6, 'Run')), w(cue(6, 'expansion')), w(cue(6, 'backward'))], font=F_TYPE)
    tag(s.hud, (W / 2, 990), 'THE BIG BANG', 64, t, bang)
    return s


SHOTS = [
    (0.0, sA),
    (cue(5, 'Hawking was') - LEAD, sB, 'up'),
    (cue(5, 'so he kept') - LEAD, sC, 'lr'),
    (cue(5, 'In place') - LEAD, sD, 'rl'),
    (cue(5, 'and the stories') - LEAD, sE, 'up'),
    (cue(6, 'That history') - LEAD, sF, 'lr'),
    (cue(6, 'In the 1920s') - LEAD, sG, 'rl'),
    (cue(6, 'The universe') - LEAD, sH, 'up'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
