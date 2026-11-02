"""Act 3: Where Physics Breaks. Narration clips 7-8."""
import sys, math, os
import numpy as np
from PIL import Image, ImageDraw
from vox import *  # noqa: F401,F403
import style as st
import presets as P
from style import sfx, ENTER, Shot, words, tag, underline, kicker

CLIPS = (7, 8)
cue = make_cue(CLIPS)

INDIGO = (52, 52, 110)
LAV = (150, 148, 200)
TERRA = (205, 88, 48)
GREYL = (120, 112, 100)

COLLAPSE = P.print_card(Image.open(asset('p03_collapse.png')), 1240, seed=71)
BLACKHOLE = P.print_card(Image.open(asset('p04_blackhole.png')), 1240, seed=71)
HOLE_C, HOLE_R = (957, 475), 127          # black disc of P04 on the placed print, frame px


def planet_item(d=230):
    """The C01 cut-out when it exists; until then a flat banded disc in the background's style."""
    if os.path.exists(asset('c01_planet.png')):
        return P.load(asset('c01_planet.png'), height=d)
    s = 3
    im = Image.new('RGBA', (d * s, d * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.ellipse((0, 0, d * s - 1, d * s - 1), fill=TERRA + (255,))
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).ellipse((0, 0, d * s - 1, d * s - 1), fill=255)
    bands = Image.new('RGBA', im.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(bands)
    for i, (y, h, c) in enumerate(((0.28, 0.07, (230, 150, 105)), (0.47, 0.10, (172, 66, 34)), (0.68, 0.06, (230, 150, 105)))):
        bd.rectangle((0, int(y * d * s), d * s, int((y + h) * d * s)), fill=c + (255,))
    im = Image.composite(bands, im, Image.fromarray(np.minimum(np.asarray(bands.getchannel('A')), np.asarray(m))))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((d * s * 0.35, -d * s * 0.05, d * s * 1.25, d * s * 1.05), fill=(40, 20, 10, 70))
    im = Image.composite(sh, im, Image.fromarray(np.minimum(np.asarray(sh.getchannel('A')), np.asarray(m))))
    return im.resize((d, d), Image.LANCZOS)


PLANET = planet_item()


def theory_card(title1, title2, icon, seed):
    c = P.paper_card(560, 380, seed=seed, colour=(246, 241, 229))
    d = ImageDraw.Draw(c)
    d.text((280, 70), title1, font=F_HEAD(44), fill=INK + (255,), anchor='mm')
    d.text((280, 125), title2, font=F_HEAD(44), fill=INK + (255,), anchor='mm')
    d.line((70, 165, 490, 165), fill=INK + (255,), width=2)
    icon(d)
    return c


def _grid_icon(d):
    for i in range(7):
        y = 200 + i * 22
        d.line([(110 + j * 20, y + 26 * math.exp(-((110 + j * 20 - 280) ** 2) / 4000) * (1 - abs(i - 3) / 4)) for j in range(18)], fill=GREYL + (255,), width=2)
    d.ellipse((262, 238, 298, 274), fill=TERRA + (255,))


def _atom_icon(d):
    for a in (0, 60, 120):
        pts = [(280 + 120 * math.cos(u) * math.cos(math.radians(a)) - 40 * math.sin(u) * math.sin(math.radians(a)),
                270 + 120 * math.cos(u) * math.sin(math.radians(a)) + 40 * math.sin(u) * math.cos(math.radians(a))) for u in np.linspace(0, 2 * math.pi, 60)]
        d.line(pts + [pts[0]], fill=GREYL + (255,), width=2)
    d.ellipse((268, 258, 292, 282), fill=TERRA + (255,))


GR = theory_card('GENERAL', 'RELATIVITY', _grid_icon, 81)
QM = theory_card('QUANTUM', 'MECHANICS', _atom_icon, 82)
PHYS = P.paper_card(820, 300, seed=83, colour=(246, 241, 229), text='PHYSICS', size=130)


def sA(t, D):
    """But at that point, physics breaks."""
    s = Shot(t, D)
    s.camera(1.0, 1.05)
    P.tear_reveal(s.mid, PHYS, W / 2, 470, t, w(cue(7, 'breaks')), spread=820)                     # 5
    tag(s.hud, (W / 2, 760), 'PHYSICS BREAKS', 60, t, w(cue(7, 'breaks')) + 0.35)
    kicker(s.hud, t, 3, 'Where physics breaks')
    return s


def sB(t, D):
    """Its two great theories refuse to cooperate."""
    s = Shot(t, D)
    s.camera(1.0, 1.03)
    P.slide(s.mid, GR, (-400, 520), (600, 480), t, ENTER, dur=1.0, rot=-3, key='gr')               # 9
    P.slide(s.mid, QM, (W + 400, 500), (1320, 470), t, ENTER + 0.25, dur=1.0, rot=3, key='qm')
    words(s.top, (W / 2, 160), 'TWO GREAT THEORIES', 64, t, [w(cue(7, 'two')), w(cue(7, 'great')), w(cue(7, 'theories'))])
    tag(s.hud, (W / 2, 860), 'REFUSE TO COOPERATE', 52, t, w(cue(7, 'refuse')))
    return s


def sC(t, D):
    """General relativity, Einstein's picture of gravity as the bending of space and time,
    governs planets and galaxies."""
    s = Shot(t, D)
    s.camera(1.0, 1.06, (W / 2, 560))
    bend = w(cue(7, 'bending'))
    k = ease((t - bend + 0.2) / 1.6)
    cx, cy = W / 2, 560
    d = ImageDraw.Draw(s.mid)
    op = int(255 * P.ease_out((t + 0.4) / 0.6))
    for gy in range(320, 840, 52):                                       # space-time sheet
        pts = []
        for gx in range(300, 1640, 20):
            r2 = (gx - cx) ** 2 + (gy - cy) ** 2
            f = math.exp(-r2 / 70000)
            pts.append((gx + (cx - gx) * 0.18 * f * k, gy + 150 * f * k))
        d.line(pts, fill=GREYL + (op,), width=2)
    for gx in range(300, 1660, 52):
        pts = []
        for gy in range(320, 840, 20):
            r2 = (gx - cx) ** 2 + (gy - cy) ** 2
            f = math.exp(-r2 / 70000)
            pts.append((gx + (cx - gx) * 0.18 * f * k, gy + 150 * f * k))
        d.line(pts, fill=GREYL + (op,), width=2)
    P.drop(s.mid, PLANET, cx, cy - 10 + 130 * k, t, w(cue(7, 'gravity')), rot=0, spin=0, key='planet', from_y=-260)
    words(s.top, (W / 2, 160), 'GENERAL RELATIVITY', 70, t, [w(cue(7, 'General')), w(cue(7, 'relativity'))])
    words(s.hud, (W / 2, 950), 'gravity as the bending of space and time', 42, t,
          [w(cue(7, x)) for x in ('gravity', 'as the', 'the bending', 'bending', 'of space', 'space', 'and time', 'time')], font=F_TYPE)
    return s


RA = np.random.default_rng(7)
CLOUD = RA.normal(0, 1, (420, 2)) * np.array([170, 110])


def sD(t, D):
    """Quantum mechanics, the rules of the very small, where certainty dissolves into
    probability, governs atoms."""
    s = Shot(t, D)
    s.camera(1.08, 1.0, (W / 2, 520))
    cx, cy = W / 2, 520
    dis = w(cue(7, 'dissolves'))
    k = ease((t - dis) / 1.4)                                            # 0 = crisp orbits, 1 = cloud
    d = ImageDraw.Draw(s.mid)
    op_orb = int(255 * (1 - k) * P.ease_out((t + 0.4) / 0.6))
    for i, a in enumerate((0, 60, 120)):
        ar = math.radians(a)
        pts = [(cx + 300 * math.cos(u) * math.cos(ar) - 100 * math.sin(u) * math.sin(ar),
                cy + 300 * math.cos(u) * math.sin(ar) + 100 * math.sin(u) * math.cos(ar)) for u in np.linspace(0, 2 * math.pi, 90)]
        if op_orb > 3:
            d.line(pts + [pts[0]], fill=GREYL + (op_orb,), width=3)
            u = t * 2.2 + i * 2.1
            ex = cx + 300 * math.cos(u) * math.cos(ar) - 100 * math.sin(u) * math.sin(ar)
            ey = cy + 300 * math.cos(u) * math.sin(ar) + 100 * math.sin(u) * math.cos(ar)
            d.ellipse((ex - 12, ey - 12, ex + 12, ey + 12), fill=INDIGO + (op_orb,))
    n = int(len(CLOUD) * k)
    for x, y in CLOUD[:n]:
        jx, jy = math.sin(t * 3 + x) * 3, math.cos(t * 2.6 + y) * 3
        d.ellipse((cx + x + jx - 3, cy + y + jy - 3, cx + x + jx + 3, cy + y + jy + 3), fill=INDIGO + (int(200 * k),))
    d.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=TERRA + (255,))
    words(s.top, (W / 2, 160), 'QUANTUM MECHANICS', 70, t, [w(cue(7, 'Quantum')), w(cue(7, 'mechanics'))])
    words(s.hud, (W / 2, 900), 'the rules of the very small', 42, t, [w(cue(7, x)) for x in ('the rules', 'rules', 'of the very', 'the very', 'very', 'small')], font=F_TYPE)
    tag(s.hud, (W / 2, 985), 'FROM CERTAINTY TO PROBABILITY', 44, t, dis)
    return s


def sE(t, D):
    """Each works brilliantly on its own territory. Squeeze the universe small enough, and both
    apply at once."""
    s = Shot(t, D)
    s.camera(1.0, 1.0)
    sq, both = w(cue(7, 'Squeeze')), w(cue(7, 'both'))
    s.push(both, 0.08, (W / 2, 480), dur=1.0)
    if t < sq:
        P.drop(s.mid, P.rot_scale(GR, -3, 1.0, key='gr3'), 520, 480, t, ENTER, rot=0, spin=-6, height=0.6, key='e_gr')
        P.drop(s.mid, P.rot_scale(QM, 3, 1.0, key='qm3'), 1400, 480, t, ENTER + 0.2, rot=0, spin=6, height=0.6, key='e_qm')
    else:                                                                # squeezed together until they collide
        P.slide(s.mid, GR, (520, 480), (790, 480), t, sq, dur=both - sq + 0.1, rot=-6, lag=4, key='sq_gr')
        P.slide(s.mid, QM, (1400, 480), (1130, 470), t, sq, dur=both - sq + 0.1, rot=7, lag=4, key='sq_qm')
    s.hit(both + 0.1)
    if t > both:
        sfx('marker', both + 0.1, W / 2, dur=0.5)
        marker_line(s.mid, [(960, 300), (930, 360), (990, 420), (925, 480), (995, 540), (935, 600), (975, 660)], ease((t - both - 0.1) / 0.5), width=10)
    words(s.top, (520, 790), 'ITS OWN TERRITORY', 34, t, w(cue(7, 'territory')), font=F_TYPE) if t < sq else None
    words(s.top, (1400, 790), 'ITS OWN TERRITORY', 34, t, w(cue(7, 'territory')) + 0.1, font=F_TYPE) if t < sq else None
    tag(s.hud, (W / 2, 900), 'BOTH APPLY AT ONCE', 56, t, both)
    return s


def sF(t, D):
    """The same collision happens in one other place."""
    s = Shot(t, D)
    s.camera(1.0, 1.06)
    words(s.top, (W / 2, 450), 'THE SAME COLLISION', 104, t, [w(cue(8, 'same')), w(cue(8, 'collision'))])
    words(s.hud, (W / 2, 600), 'in one other place', 50, t, [w(cue(8, x)) for x in ('in one', 'one', 'other', 'place')], font=F_TYPE)
    return s


def sG(t, D):
    """When a massive star burns out, it can collapse under its own weight, crushing matter so
    tightly that nothing escapes, not even light."""
    s = Shot(t, D)
    s.camera(1.0, 1.0)
    s.push(w(cue(8, 'collapse')), 0.22, HOLE_C, dur=4.5)
    P.drop(s.mid, COLLAPSE, W / 2, 500, t, ENTER, rot=0, spin=-5, height=0.5, key='col')        # 2
    words(s.hud, (W / 2, 990), 'a massive star burns out', 46, t, [w(cue(8, x)) for x in ('a massive', 'massive', 'star', 'burns', 'out')], font=F_TYPE)
    tag(s.hud, (W / 2, 120), 'NOTHING ESCAPES', 52, t, w(cue(8, 'nothing')))
    tag(s.hud, (W / 2, 205), 'NOT EVEN LIGHT', 52, t, w(cue(8, 'not even')))
    return s


def sH(t, D):
    """This is a black hole, and its point of no return is called the event horizon."""
    s = Shot(t, D)
    s.camera(1.0, 1.0)
    fl = 0.05
    P.flip(s.mid, COLLAPSE, BLACKHOLE, W / 2, 500, t, fl, dur=0.9)                                 # 11
    r = HOLE_R + 14
    s.zoom_to((HOLE_C[0] - 520, HOLE_C[1] - 290, HOLE_C[0] + 520, HOLE_C[1] + 290), w(cue(8, 'point of')), dur=1.8, fill=1.0)   # 12
    ev = w(cue(8, 'event'))
    sfx('marker', ev, HOLE_C[0], dur=0.6)
    marker_circle(s.mid, HOLE_C[0], HOLE_C[1], r, r, ease((t - ev) / 0.6), width=8, seed=5)
    tag(s.hud, (W / 2, 120), 'BLACK HOLE', 84, t, w(cue(8, 'black')))
    tag(s.hud, (W / 2, 895), 'THE POINT OF NO RETURN', 42, t, w(cue(8, 'point of')), bg=CREAM, fg=INK)
    tag(s.hud, (W / 2, 985), 'EVENT HORIZON', 56, t, ev)
    return s


SHOTS = [
    (0.0, sA),
    (cue(7, 'Its two') - LEAD, sB, 'up'),
    (cue(7, 'General') - LEAD, sC, 'rl'),
    (cue(7, 'Quantum') - LEAD, sD, 'lr'),
    (cue(7, 'Each works') - LEAD, sE, 'up'),
    (cue(8, 'The same') - LEAD, sF, 'rl'),
    (cue(8, 'When a') - LEAD, sG, 'lr'),
    (cue(8, 'This is') - LEAD, sH, 'up'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
