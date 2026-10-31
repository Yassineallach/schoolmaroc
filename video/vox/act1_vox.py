"""Act 1 — The Mines, Vox editorial style. Narration clips 1-3 (0.0-57.7s)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageOps
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vox import *

E01 = Image.open(os.path.join(B2, 'E01.png'))
E02 = Image.open(os.path.join(B2, 'E02.png'))
VISOR = Image.open(os.path.join(A3, 'C01C_visor_v2.png'))

CARD_E01 = PhotoCard(E01, 700, rot=-3, seed=2, crop=(0, 0, 940, 1100))
CARD_VISOR = PhotoCard(VISOR, 860, rot=2.5, seed=5)
CARD_E02 = PhotoCard(E02, 1180, rot=-1.5, seed=7)

DARROW = Cutout(Image.open(os.path.join(A3, 'C01A_standing.png')).convert('RGBA'), 900)
NAROL = Cutout(Image.open(os.path.join(SRC, 'narol34.png')).convert('RGBA'), 880)
DARROW_SIDE = Cutout(ImageOps.mirror(Image.open(os.path.join(SRC, 'darrowside.png')).convert('RGBA')), 860)
CLIMB = Cutout(Image.open(os.path.join(A3, 'C01B_climbing.png')).convert('RGBA'), 820)
REAPER = Cutout(Image.open(os.path.join(SRC, 'reaper.png')).convert('RGBA'), 940)
FG = foreground()


cue = make_cue((1, 2, 3))


def sA(t, D):
    """Beneath the surface of Mars: the cross-section print, then the visor close-up lands on top."""
    c = background()
    pan = ease(t / 5.5)
    CARD_E01.place(c, 620, 520, t, 0.0, zoom=1.35, pan=(0.5, pan))
    typewriter(c, (300, 990), 'BENEATH THE SURFACE OF MARS', 42, t, w(cue(1, 'beneath')))
    tv = w(cue(1, 'plunges')) - 0.2
    if t > tv - 0.2:
        CARD_VISOR.place(c, 1240, 560, t, tv, zoom=lerp(1.0, 1.08, ease((t - tv) / 4)))
        marker_circle(c, 1500, 500, 170, 150, ease((t - w(cue(1, 'deadly'))) / 0.7), seed=2)
        typewriter(c, (1390, 900), 'DEADLY GAS', 40, t, w(cue(1, 'deadly')), fill=RED)
    return c


def laurel_wreath(c, cx, cy, R, prog, color=INK):
    d = ImageDraw.Draw(c)
    n = 9
    for side in (-1, 1):
        k = int(40 * min(1, prog * 1.6))
        pts = []
        for i in range(k + 1):
            a = math.radians(115 + 130 * i / 40)
            x = cx + math.cos(a) * R
            pts.append((x if side == -1 else 2 * cx - x, cy + math.sin(a) * R))
        if len(pts) > 1:
            d.line(pts, fill=color + (255,), width=5)
        for i in range(n):
            if prog * n * 1.3 - i <= 0:
                continue
            a = math.radians(122 + i * 13)
            px, py = cx + math.cos(a) * R, cy + math.sin(a) * R
            if side == 1:
                px = 2 * cx - px
            ang = a + math.pi / 2 + (0.7 if side == -1 else -0.7)
            if side == 1:
                ang = math.pi - (a + math.pi / 2) - 0.7
            L, Wd = 46, 17
            pts2 = [(px + math.cos(u) * L / 2 * math.cos(ang) - math.sin(u) * Wd / 2 * math.sin(ang),
                     py + math.cos(u) * L / 2 * math.sin(ang) + math.sin(u) * Wd / 2 * math.cos(ang)) for u in np.linspace(0, 2 * math.pi, 16)]
            d.polygon(pts2, fill=color + (255,))


NOTICE = document(640, 760, ['', 'Awarded to the clan', 'that digs the most:', '', '+ extra food', '+ extra supplies'],
                  seed=11, title='THE LAUREL', title_size=56, body_size=34, typed=True)


def sB(t, D):
    """The Laurel: a typed notice, with Darrow beside it."""
    c = background()
    pos = place_sheet(c, NOTICE, 1220, 520, t, 0.0, rot=2)
    if pos:
        laurel_wreath(c, 1220, 740, 110, ease((t - w(cue(1, 'laurel'))) / 1.4))
    DARROW.place(c, 520, H + 40, t, 0.6, side='left')
    headline(c, (520, 120), 'DARROW', 84, t, w(cue(1, 'win the')))
    typewriter(c, (520, 200), 'a young miner of Lykos', 34, t, w(cue(1, 'extra food')), anchor='mm')
    c.alpha_composite(FG)
    return c


def sC(t, D):
    """Uncle Narol warns him."""
    c = background()
    NAROL.place(c, 620, H + 60, t, 0.0, side='left')
    DARROW_SIDE.place(c, 1300, H + 60, t, 0.35, side='right')
    headline(c, (620, 110), 'UNCLE NAROL', 72, t, w(cue(2, 'narol')))
    typewriter(c, (430, 185), '"The contest is rigged."', 40, t, w(cue(2, 'the contest')), fill=RED)
    c.alpha_composite(FG)
    return c


CLANS = [('GAMMA', 0.62), ('LYKOS', 0.95), ('OMICRON', 0.48), ('UPSILON', 0.55)]


def sD(t, D):
    """The ledger: Lykos digs the most, the Laurel goes to Gamma. RIGGED."""
    c = background()
    ledger = Image.new('RGBA', (1400, 760), (245, 241, 230, 255))
    ledger.putalpha(torn_mask(1400, 760, 21, amp=4, step=14))
    pos = place_sheet(c, ledger, W / 2, 560, t, 0.0)
    headline(c, (W / 2, 110), 'WHO WINS THE LAUREL?', 70, t, 0.4)
    if pos:
        x0, y0 = pos
        d = ImageDraw.Draw(c)
        base = y0 + 600
        d.line((x0 + 90, base, x0 + 1310, base), fill=INK + (255,), width=4)
        for i, (name, v) in enumerate(CLANS):
            p = ease((t - 0.7 - i * 0.18) / 0.9)
            bx = x0 + 180 + i * 300
            h = 430 * v * p
            d.rectangle((bx, base - h, bx + 170, base), fill=(INK if name == 'LYKOS' else GREY) + (255,))
            text(c, (bx + 85, base + 50), name, F_HEAD(34))
        if t > w(cue(2, 'another clan')):
            gx = x0 + 180 + 85
            laurel_wreath(c, gx, base - 430 * 0.62 - 120, 62, ease((t - w(cue(2, 'another clan'))) / 0.6), color=RED)
        stamp(c, x0 + 980, y0 + 150, 'RIGGED', 90, t, w(cue(2, 'another clan', 1, 'e')), ang=-10)
    return c


def gauge_scribble(c, t):
    marker_circle(c, 1000, 690, 120, 105, ease((t - 0.8) / 0.6), seed=4)


def sE(t, D):
    """The reckless dive: the drill cockpit print shakes, the gas gauge is circled."""
    c = background()
    CARD_E02.place(c, W / 2, 545, t, 0.0, zoom=lerp(1.0, 1.1, ease(t / D)), pan=(0.5, 0.6))
    gauge_scribble(c, t)
    typewriter(c, (300, 120), 'NEARLY COSTS HIM HIS LIFE', 46, t, w(cue(2, 'nearly')), fill=RED)
    return shake(c, t, (w(cue(2, 'reckless')), w(cue(2, 'nearly')), w(cue(2, 'life'))))


def sF(t, D):
    """He climbs out proudly."""
    c = background()
    CLIMB.place(c, 980, H - 20, t, 0.0, rise=520, side='right')
    headline(c, (980, 110), 'UNDETERRED', 96, t, w(cue(2, 'proudly')))
    c.alpha_composite(FG)
    return c


def sG(t, D):
    """Title card: RED RISING, then brutal / defiant / soulful."""
    c = background()
    headline(c, (W / 2, 420), 'RED RISING', 230, t, 0.2, tracking=-4)
    marker_line(c, [(470, 560), (960, 548), (1450, 560)], ease((t - 1.2) / 0.8), width=14)
    for i, wd in enumerate(['BRUTAL', 'DEFIANT', 'SOULFUL']):
        typewriter(c, (W / 2 - 520 + i * 520, 690), wd, 56, t, w(cue(3, wd.lower())), anchor='mm', cursor=False)
    return c


def sH(t, D):
    """Darrow of Lykos becomes the Reaper."""
    c = background()
    if t < w(cue(3, 'who becomes')):
        DARROW.place(c, 760, H + 40, t, 0.0, side='left')
        typewriter(c, (300, 150), 'DARROW OF LYKOS', 48, t, w(cue(3, 'darrow of lykos')))
    else:
        REAPER.place(c, 1100, H + 30, t, w(cue(3, 'who becomes')), side='right')
        headline(c, (430, 470), 'THE', 90, t, w(cue(3, 'the reaper')))
        headline(c, (430, 580), 'REAPER', 150, t, w(cue(3, 'reaper')), fill=RED)
    c.alpha_composite(FG)
    return c


def sI(t, D):
    """A trilogy: from the mines of Mars to the heart of the Society."""
    c = background()
    headline(c, (W / 2, 110), 'A TRILOGY', 80, t, 0.0)
    d = ImageDraw.Draw(c)
    # Mars and the Society drawn in ink
    dy, op = arrive(t, w(cue(3, 'mines')), 200)
    if op > 0:
        d.ellipse((260, 460 + dy, 560, 760 + dy), fill=(180, 72, 48, int(255 * op)), outline=INK + (255,), width=5)
        text(c, (410, 820 + dy), 'MINES OF MARS', F_HEAD(36), alpha=op)
    dy2, op2 = arrive(t, w(cue(3, 'society')), 200)
    if op2 > 0:
        for r in (240, 170):
            d.ellipse((1560 - r, 610 - r * 0.55 + dy2, 1560 + r, 610 + r * 0.55 + dy2), outline=GREY + (255,), width=3)
        d.ellipse((1500, 550 + dy2, 1620, 670 + dy2), fill=(196, 154, 69, int(255 * op2)), outline=INK + (255,), width=5)
        text(c, (1560, 860 + dy2), 'THE SOCIETY', F_HEAD(36), alpha=op2)
    route = [(560, 610)] + [(560 + (1440 - 560) * u, 610 - 140 * math.sin(math.pi * u)) for u in np.linspace(0, 1, 50)]
    marker_line(c, route, ease((t - w(cue(3, 'travels'))) / (w(cue(3, 'society')) - w(cue(3, 'travels')))), width=10)
    for i, u in enumerate((0.2, 0.5, 0.8)):
        x, y = 560 + 880 * u, 610 - 140 * math.sin(math.pi * u)
        bk = document(110, 150, [], seed=40 + i)
        place_sheet(c, bk, x, y - 40, t, (w(cue(3, 'travels')) + u * (w(cue(3, 'society')) - w(cue(3, 'travels')))), rot=(-6, 3, -2)[i], rise=200)
        if t > (w(cue(3, 'travels')) + u * (w(cue(3, 'society')) - w(cue(3, 'travels')))):
            text(c, (x, y - 40 + arrive(t, (w(cue(3, 'travels')) + u * (w(cue(3, 'society')) - w(cue(3, 'travels')))), 200)[0]), ['I', 'II', 'III'][i], F_SERIF(54))
    return c


SHOTS = [(0.0, sA), (cue(1, 'in his eyes') - LEAD, sB), (cue(2, 'as his uncle') - LEAD, sC), (cue(2, 'the laurel always') - LEAD, sD),
         (cue(2, 'darrow is') - LEAD, sE), (cue(2, 'never discouraged') - LEAD, sF), (cue(3, 'this sequence'), sG),
         (cue(3, 'darrow of lykos') - LEAD, sH), (cue(3, 'published') - LEAD, sI)]
END = cue.total


def frame(t):
    return make_frame(SHOTS, END, t)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
    elif mode == 'video':
        render_video(frame, END, (1, 2, 3), sys.argv[2], os.path.dirname(os.path.abspath(__file__)))
