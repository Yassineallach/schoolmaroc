"""Act 4: Against the Clock. Narration clips 9-10."""
import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from vox import *  # noqa: F401,F403
import style as st
import presets as P
from style import sfx, ENTER, Shot, words, tag, underline, kicker

CLIPS = (9, 10)
cue = make_cue(CLIPS)

INDIGO = (52, 52, 110)
TERRA = (205, 88, 48)
GREYL = (120, 112, 100)

HOLE = P.print_card(Image.open(asset('p04_blackhole.png')), 900, seed=91)
CHAIR = P.print_card(Image.open(asset('hawking_wheelchair.jpg')), 430, seed=92)
GOWN = P.print_card(Image.open(asset('hawking_gown.jpg')), 430, seed=93)
def _fit_aspect(im, ref):
    """Crop im (centre, slightly high) to ref's aspect so the two prints flip at one size."""
    w_, h_ = im.size
    ta = ref.width / ref.height
    if w_ / h_ > ta:
        nw = int(h_ * ta); x0 = (w_ - nw) // 2
        return im.crop((x0, 0, x0 + nw, h_))
    nh = int(w_ / ta); y0 = int((h_ - nh) * 0.3)
    return im.crop((0, y0, w_, y0 + nh))


CHAIR_B = P.print_card(_fit_aspect(Image.open(asset('hawking_wheelchair.jpg')).convert('RGB'), GOWN), GOWN.width, seed=94).resize(GOWN.size, Image.LANCZOS)

DIAG = document(600, 640, ['Diagnosis', '---', 'Motor neurone disease', '---', 'about two years to live', '---', '---'],
                seed=95, title='MEDICAL REPORT', body_size=36)


def shapes_item():
    """Shapes held in the head: circle, triangle, a light-cone hourglass, an orbit."""
    s = 3
    im = Image.new('RGBA', (560 * s, 420 * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((30 * s, 40 * s, 230 * s, 240 * s), fill=INDIGO + (255,))
    d.polygon([(300 * s, 240 * s), (520 * s, 240 * s), (410 * s, 40 * s)], fill=TERRA + (255,))
    d.polygon([(120 * s, 280 * s), (280 * s, 280 * s), (200 * s, 350 * s)], fill=(150, 148, 200, 255))
    d.polygon([(120 * s, 420 * s), (280 * s, 420 * s), (200 * s, 350 * s)], fill=(150, 148, 200, 255))
    d.ellipse((330 * s, 290 * s, 520 * s, 400 * s), outline=INK + (255,), width=6 * s)
    d.ellipse((410 * s, 330 * s, 440 * s, 360 * s), fill=TERRA + (255,))
    return im.resize((560, 420), Image.LANCZOS)


SHAPES = shapes_item()


def equation_sheet():
    im = P.paper_card(520, 600, seed=96, colour=(246, 241, 229))
    d = ImageDraw.Draw(im)
    r = np.random.default_rng(5)
    y = 70
    while y < 560:
        x = 50
        for _ in range(r.integers(4, 8)):
            d.text((x, y), r.choice(list('abcxyzkn=+−()')), font=F_SERIF(30), fill=INK + (255,), anchor='lm')
            x += 32
        y += 62
    return im


EQS = equation_sheet()


def letter_card():
    im = P.paper_card(760, 520, seed=97, colour=(246, 241, 229))
    d = ImageDraw.Draw(im)
    for i, ch in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
        r, c = divmod(i, 7)
        d.text((95 + c * 95, 90 + r * 110), ch, font=F_HEAD(62), fill=INK + (255,), anchor='mm')
    return im


LETTERS = letter_card()
LPOS = [(95 + (i % 7) * 95, 90 + (i // 7) * 110) for i in range(26)]


def screen_item():
    im = Image.new('RGBA', (560, 420), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 559, 419), radius=28, fill=(70, 66, 60, 255))
    d.rounded_rectangle((26, 26, 533, 360), radius=14, fill=(28, 34, 40, 255))
    d.rectangle((240, 370, 320, 400), fill=(90, 86, 80, 255))
    return im


SCREEN = screen_item()
WORDLIST = ['THE', 'UNIVERSE', 'TIME', 'BLACK', 'HOLE', 'LIGHT']


def sA(t, D):
    """Hawking made his name at that edge."""
    s = Shot(t, D)
    s.camera(1.0, 1.04)
    P.drop(s.mid, HOLE, 1180, 470, t, ENTER, rot=2, spin=8, key='hole')
    P.drop(s.mid, CHAIR, 470, 500, t, ENTER + 0.35, rot=-4, spin=-12, key='chair')
    a = w(cue(9, 'edge'))
    sfx('marker', a, 820, dur=0.6)
    marker_line(s.mid, [(640, 380), (760, 330), (900, 360), (1030, 420)], ease((t - a) / 0.6), width=8)
    words(s.top, (1180, 900), 'AT THAT EDGE', 56, t, [w(cue(9, 'at that')), w(cue(9, 'that edge')), w(cue(9, 'edge'))])
    kicker(s.hud, t, 4, 'Against the clock')
    return s


def _glow(r, strength):
    n = int(r * 4)
    g = Image.new('L', (n, n), 0)
    ImageDraw.Draw(g).ellipse((n / 2 - r * 1.45, n / 2 - r * 1.45, n / 2 + r * 1.45, n / 2 + r * 1.45), fill=int(235 * strength))
    g = g.filter(ImageFilter.GaussianBlur(r * 0.28))
    im = Image.new('RGBA', (n, n), (226, 112, 64, 0))           # warm terracotta glow: reads on cream paper
    im.putalpha(g)
    return im


RP = np.random.default_rng(4)
PARTS = [(RP.uniform(0, 2 * math.pi), RP.uniform(0, 1), RP.uniform(0.6, 1.2)) for _ in range(70)]


def hole_on_paper(layer, cx, cy, r, glow, t, leak):
    if r > 1:
        g = _glow(r, glow)
        P.comp(layer, g, cx - g.width / 2, cy - g.height / 2)
        ImageDraw.Draw(layer).ellipse((cx - r, cy - r, cx + r, cy + r), fill=(18, 16, 30, 255))
    d = ImageDraw.Draw(layer)
    for a, ph, sp in PARTS:                        # the faint glow leaking away
        u = ((t * 0.35 * sp + ph) % 1.0)
        rr = r * 1.1 + u * 380
        k = leak * (1 - u)
        if k > 0.03:
            x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.9
            d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(205, 88, 48, int(220 * k)))


def sB(t, D):
    """Applying quantum rules to it, he showed that black holes are not entirely black."""
    s = Shot(t, D)
    s.camera(1.0, 1.06)
    nb = w(cue(9, 'not entirely'))
    hole_on_paper(s.mid, W / 2, 470, 190, 0.85 * ease((t - nb) / 1.0), t, 0.0)
    words(s.hud, (W / 2, 120), 'applying quantum rules', 46, t, [w(cue(9, x)) for x in ('Applying', 'quantum', 'rules')], font=F_TYPE)
    tag(s.hud, (W / 2, 880), 'NOT ENTIRELY BLACK', 64, t, nb)
    return s


def sC(t, D):
    """They leak a faint glow, and over immense stretches of time, they slowly evaporate."""
    s = Shot(t, D)
    s.camera(1.0, 1.0)
    s.push(w(cue(9, 'slowly')), 0.10, (W / 2, 470), dur=1.6)
    ev = w(cue(9, 'evaporate'))
    r = 190 * (1 - ease((t - w(cue(9, 'immense'))) / (ev + 0.9 - w(cue(9, 'immense')))))
    hole_on_paper(s.mid, W / 2, 470, r, 0.85, t, min(1.0, max(0.0, (t - w(cue(9, 'leak'))) / 0.5)))
    words(s.top, (W / 2, 120), 'A FAINT GLOW', 70, t, [w(cue(9, 'a faint')), w(cue(9, 'faint')), w(cue(9, 'glow'))])
    words(s.hud, (W / 2, 880), 'over immense stretches of time', 46, t, [w(cue(9, x)) for x in ('over', 'immense', 'stretches', 'of time', 'time')], font=F_TYPE)
    tag(s.hud, (W / 2, 975), 'THEY SLOWLY EVAPORATE', 56, t, w(cue(9, 'slowly')))
    return s


def sD(t, D):
    """He did this work against his own deadline."""
    s = Shot(t, D)
    s.camera(1.0, 1.05)
    k = 0.3
    while k < D:
        sfx('tick', k, W / 2)
        k += 0.5
    words(s.top, (W / 2, 470), 'AGAINST HIS OWN', 96, t, [w(cue(10, x)) for x in ('against', 'his own', 'own')])
    words(s.top, (W / 2, 590), 'DEADLINE', 130, t, w(cue(10, 'deadline')), fill=RED)
    return s


def sE(t, D):
    """In 1963, at the age of 21, Hawking was diagnosed with motor neurone disease and given
    about two years to live."""
    s = Shot(t, D)
    s.camera(1.0, 1.0)
    s.push(w(cue(10, 'diagnosed')), 0.07, (1330, 470), dur=2.5)
    P.drop(s.mid, GOWN, 520, 480, t, ENTER, rot=-3, spin=-10, key='gown')                        # 2
    P.stamp_hit(s.mid, '1963', 520, 770, t, w(cue(10, '1963')), size=84, ang=-7, shot=s)          # 7
    words(s.top, (520, 120), 'AGE 21', 72, t, w(cue(10, '21')))
    P.unfold(s.mid, DIAG, 1330, 480, t, w(cue(10, 'diagnosed')) - 0.2, dur=1.0)                  # 3
    a = w(cue(10, 'motor'))
    sfx('marker', a, 1300, dur=0.5)
    marker_circle(s.mid, 1250, 438, 235, 40, ease((t - a) / 0.5), seed=2)
    underline(s.mid, 1090, 1420, 520, t, w(cue(10, 'two years')))
    return s


def sF(t, D):
    """As his hands failed, he learned to solve problems as shapes in his head rather than
    equations on paper."""
    s = Shot(t, D)
    s.camera(1.0, 1.03)
    rt = w(cue(10, 'rather'))
    if t < rt:
        P.drop(s.mid, EQS, 1420, 500, t, ENTER, rot=3, spin=8, height=0.5, key='eqs')
    else:                                                                # the paper is pushed aside
        P.slide(s.mid, P.rot_scale(EQS, 3, 1.0, key='eqs3'), (1420, 500), (W + 420, 560), t, rt, dur=1.0, rot=0, lag=6)
    P.assemble(s.mid, SHAPES, 640, 480, t, w(cue(10, 'shapes')), n=9, dur=0.9, stagger=0.07)    # 10
    words(s.hud, (640, 860), 'shapes in his head', 50, t, [w(cue(10, x)) for x in ('shapes', 'in his', 'his head', 'head')], font=F_TYPE)
    words(s.hud, (1420, 900), 'not equations on paper', 40, t, [w(cue(10, x)) for x in ('rather', 'than', 'equations', 'paper')], font=F_TYPE)
    return s


def sG(t, D):
    """After the tracheotomy, he spelled out words by raising his eyebrows at letters on a card,"""
    s = Shot(t, D)
    s.camera(1.0, 1.05, (W / 2, 500))
    cx, cy = W / 2, 470
    P.drop(s.mid, LETTERS, cx, cy, t, ENTER, rot=-1.5, spin=-6, key='letters')
    a0 = w(cue(10, 'letters'))
    if t > a0 - 0.6:                                                     # the highlight hops letter to letter
        seq = [7, 0, 22, 10, 8, 13, 6, 18]
        i = int((t - a0 + 0.6) / 0.42)
        idx = seq[i % len(seq)]
        x, y = LPOS[idx]
        x, y = cx - LETTERS.width / 2 + x, cy - LETTERS.height / 2 + y
        ImageDraw.Draw(s.mid).rounded_rectangle((x - 40, y - 46, x + 40, y + 46), radius=10, outline=RED + (255,), width=7)
        k = a0 - 0.6
        while k < D:
            sfx('tick', k, x)
            k += 0.42
    words(s.hud, (W / 2, 900), 'raising his eyebrows at letters on a card', 40, t,
          [w(cue(10, x)) for x in ('raising', 'his eyebrows', 'eyebrows', 'at letters', 'letters', 'on a', 'a card', 'card')], font=F_TYPE)
    tag(s.hud, (W / 2, 120), 'AFTER THE TRACHEOTOMY', 46, t, w(cue(10, 'tracheotomy')))
    return s


def sH(t, D):
    """until a computer program let him pick words from a screen and speak them through a
    synthesizer."""
    s = Shot(t, D)
    s.camera(1.0, 1.04)
    P.flip(s.mid, GOWN, CHAIR_B, 520, 480, t, w(cue(10, 'computer')), dur=0.9)                   # 11
    P.drop(s.mid, SCREEN, 1330, 470, t, ENTER, rot=0, spin=0, height=0.5, key='screen')
    d = ImageDraw.Draw(s.mid)
    pick = w(cue(10, 'pick'))
    sel = min(len(WORDLIST) - 1, max(0, int((t - pick) / 0.35))) if t > pick else -1
    for i, wd in enumerate(WORDLIST):
        y = 330 + i * 46
        if i == sel:
            d.rectangle((1100, y - 20, 1560, y + 20), fill=(205, 88, 48, 255))
        d.text((1120, y), wd, font=F_TYPE(34), fill=(236, 232, 222, 255), anchor='lm')
    if pick < t < pick + 0.35 * len(WORDLIST):
        sfx('tick', pick + 0.35 * max(0, sel), 1330)
    sp = w(cue(10, 'speak'))
    for j in range(3):                                                   # the voice leaves the screen
        a = sp + j * 0.25
        sfx('marker', a, 1700, dur=0.3) if j == 0 else None
        r = 60 + j * 50
        marker_line(s.mid, [(1620 + r * math.cos(u), 470 + r * math.sin(u)) for u in np.linspace(-0.7, 0.7, 12)], ease((t - a) / 0.4), width=7, seed=j)
    words(s.hud, (W / 2, 900), 'pick words from a screen', 44, t, [w(cue(10, x)) for x in ('pick', 'words from', 'from a', 'a screen', 'screen')], font=F_TYPE)
    tag(s.hud, (W / 2, 985), 'SPOKEN THROUGH A SYNTHESIZER', 48, t, w(cue(10, 'synthesizer')))
    return s


SHOTS = [
    (0.0, sA),
    (cue(9, 'Applying') - LEAD, sB, 'up'),
    (cue(9, 'They leak') - LEAD, sC, 'lr'),
    (cue(10, 'He did') - LEAD, sD, 'rl'),
    (cue(10, 'In 1963') - LEAD, sE, 'up'),
    (cue(10, 'As his') - LEAD, sF, 'lr'),
    (cue(10, 'After the') - LEAD, sG, 'rl'),
    (cue(10, 'until a') - LEAD, sH, 'up'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
