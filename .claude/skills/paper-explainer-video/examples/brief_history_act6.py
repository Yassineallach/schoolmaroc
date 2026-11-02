"""Act 6: Brief, Not Short. Narration clips 13-15 (last act: holds the end title)."""
import sys, math
import numpy as np
from PIL import Image, ImageDraw
from vox import *  # noqa: F401,F403
import style as st
import presets as P
from style import sfx, ENTER, Shot, words, tag, underline, kicker

CLIPS = (13, 14, 15)
cue = make_cue(CLIPS)

INDIGO = (52, 52, 110)
LAV = (150, 148, 200)
TERRA = (205, 88, 48)
SLATE = (70, 74, 92)

CROWD = P.load(asset('c05_crowd.png'), width=620)
SKY = P.print_card(Image.open(asset('p05_nightsky.png')), 1300, seed=151)


def title_page():
    im = P.paper_card(820, 560, seed=131, colour=(246, 241, 229))
    d = ImageDraw.Draw(im)
    d.text((410, 90), 'MANUSCRIPT', font=F_SERIF(30), fill=(110, 104, 96, 255), anchor='mm')
    d.text((410, 250), 'A Short History', font=F_TYPE(64), fill=INK + (255,), anchor='mm')
    d.text((410, 340), 'of Time', font=F_TYPE(64), fill=INK + (255,), anchor='mm')
    d.text((410, 470), 'S. W. Hawking', font=F_TYPE(30), fill=(110, 104, 96, 255), anchor='mm')
    return im


TITLE = title_page()


def cover(col, w=250, h=375, seed=0):
    b = Image.new('RGBA', (w, h), col + (255,))
    d = ImageDraw.Draw(b)
    d.rectangle((12, 12, w - 12, h - 12), outline=CREAM + (255,), width=2)
    for i, s in enumerate(('A BRIEF', 'HISTORY', 'OF TIME')):
        d.text((w / 2, 70 + i * 36), s, font=F_HEAD(30), fill=CREAM + (255,), anchor='mm')
    d.ellipse((w / 2 - 50, 210, w / 2 + 50, 310), outline=CREAM + (255,), width=3)
    d.ellipse((w / 2 - 7, 253, w / 2 + 7, 267), fill=RED + (255,) if col != TERRA else CREAM + (255,))
    b.putalpha(torn_mask(w, h, 60 + seed, amp=2, step=16))
    return b


COVERS = [cover(c, seed=i) for i, c in enumerate([INDIGO, TERRA, SLATE, LAV, INDIGO, TERRA, SLATE])]
LIST = document(560, 700, ['1.', '---', '2.', '---', '3.', '---', '4.', '---', '5.', '---'], seed=133, title='BESTSELLERS', body_size=34)
THEORY = document(620, 660, ['---', '---', '---', '---', '---', '---', '---', '---'], seed=134, title='A COMPLETE THEORY')


def spread_page(seed, lines=True):
    im = P.paper_card(440, 600, seed=seed, colour=(248, 244, 233))
    if lines:
        d = ImageDraw.Draw(im)
        r = np.random.default_rng(seed)
        for y in range(80, 540, 30):
            d.line((50, y, 50 + r.uniform(0.7, 1.0) * 340, y), fill=(160, 154, 144, 255), width=3)
    return im


LEFTP, RIGHTP, TURNP = spread_page(141), spread_page(142), spread_page(143)


def sA(t, D):
    """Hawking had wanted to call the book "A Short History of Time." His editor changed one word."""
    s = Shot(t, D)
    s.camera(1.0, 1.0)
    s.push(w(cue(13, 'changed')), 0.12, (W / 2, 420), dur=1.4)
    P.drop(s.mid, TITLE, W / 2, 480, t, ENTER, rot=-1, spin=-6, key='title')                      # 2
    a = w(cue(13, 'changed'))
    sfx('marker', a, W / 2, dur=0.4)
    strike(s.mid, W / 2 - 200, W / 2 + 25, 450, ease((t - a) / 0.4), width=12)       # through "Short"
    b = w(cue(13, 'one word'))
    sfx('marker', b, W / 2, dur=0.5)
    if t > b:
        br = P.rot_scale(P.text_item('Brief', 64, fill=RED), -6, 1.0, key='brief')
        k = ease((t - b) / 0.45)
        P.put(s.mid, P.fade_img(br, k), W / 2 - 95, 372, shadow=False)
    words(s.hud, (W / 2, 960), 'his editor changed one word', 44, t, [w(cue(13, x)) for x in ('His editor', 'editor', 'changed', 'one word', 'word.')], font=F_TYPE)
    kicker(s.hud, t, 6, 'Brief, not short')
    return s


def sB(t, D):
    """The result spent a record 237 weeks on Britain's Sunday Times bestseller list,"""
    s = Shot(t, D)
    s.camera(1.0, 1.03)
    P.slide(s.mid, LIST, (-420, 560), (560, 500), t, ENTER, dur=1.0, rot=-3, key='list')        # 9
    P.stamp_hit(s.mid, 'RECORD', 560, 300, t, w(cue(13, 'record')), size=86, ang=-8, shot=s)      # 7
    a, b = w(cue(13, '237')), w(cue(13, 'weeks'))
    if t > a - 0.3:
        n = int(237 * ease((t - a + 0.3) / (b - a + 0.3)))
        k = a - 0.3
        while k < b:
            sfx('tick', k, 1350)
            k += 0.09
        P.put(s.top, P.text_item(str(n), 220), 1350, 440, shadow=False)
    words(s.top, (1350, 610), 'WEEKS', 90, t, b)
    words(s.hud, (W / 2, 960), "Britain's Sunday Times bestseller list", 42, t,
          [w(cue(13, x)) for x in ("Britain's", 'Sunday', 'Times', 'bestseller', 'list,')], font=F_TYPE)
    return s


def sC(t, D):
    """and has sold more than 10 million copies in dozens of languages."""
    s = Shot(t, D)
    s.camera(1.04, 1.0)
    st_ = w(cue(13, 'sold'))
    spots = [(420, 470), (700, 430), (980, 480), (1260, 440), (1540, 470), (560, 640), (1400, 650)]
    P.stack(s.mid, COVERS, spots, t, [st_ + 0.18 * i for i in range(len(COVERS))], rots=[-6, 4, -3, 5, -4, 3, -5])   # 6
    tag(s.hud, (W / 2, 880), 'MORE THAN 10 MILLION COPIES', 56, t, w(cue(13, '10 million')))
    words(s.hud, (W / 2, 975), 'in dozens of languages', 44, t, [w(cue(13, x)) for x in ('in dozens', 'dozens', 'of languages', 'languages.')], font=F_TYPE)
    return s


def sD(t, D):
    """It also earned a less flattering reputation, as one of the most bought and least finished
    books ever printed."""
    s = Shot(t, D)
    s.camera(1.0, 1.05, (W / 2, 470))
    cx, cy = W / 2, 470
    P.put(s.mid, LEFTP, cx - 220, cy)
    P.put(s.mid, RIGHTP, cx + 220, cy)
    P.page_flip(s.mid, TURNP, cx, cy, t, w(cue(13, 'bought')) - 0.2, dur=1.0, opening=True)         # 1
    d = ImageDraw.Draw(s.mid)
    d.line((cx, cy - 300, cx, cy + 300), fill=(150, 140, 125, 255), width=3)
    d.polygon([(cx - 120, cy - 300), (cx - 90, cy - 300), (cx - 90, cy - 150), (cx - 105, cy - 170), (cx - 120, cy - 150)], fill=TERRA + (255,))   # the bookmark, stuck near the start
    tag(s.hud, (W / 2 - 290, 880), 'MOST BOUGHT', 52, t, w(cue(13, 'most')))
    tag(s.hud, (W / 2 + 290, 880), 'LEAST FINISHED', 52, t, w(cue(13, 'least')), bg=INK)
    words(s.hud, (W / 2, 120), 'a less flattering reputation', 44, t, [w(cue(13, x)) for x in ('a less', 'less', 'flattering', 'reputation')], font=F_TYPE)
    return s


def sE(t, D):
    """Its final pages imagine a day when a complete theory is found, and when ordinary people, not
    only scientists, can join the debate about why the universe exists at all."""
    s = Shot(t, D)
    s.camera(1.0, 1.0)
    P.unfold(s.mid, THEORY, 640, 470, t, w(cue(14, 'complete')) - 0.25, dur=1.0)                 # 3
    P.drop(s.mid, CROWD, 1360, 600, t, w(cue(14, 'ordinary')), rot=0, spin=0, height=0.5, key='crowd')
    words(s.hud, (W / 2, 110), 'a day when a complete theory is found', 42, t,
          [w(cue(14, x)) for x in ('a day', 'day', 'when a', 'a complete', 'complete', 'theory', 'is found', 'found,')], font=F_TYPE)
    tag(s.hud, (1360, 960), 'NOT ONLY SCIENTISTS', 48, t, w(cue(14, 'not only')))
    words(s.hud, (640, 960), 'why the universe exists at all', 40, t, [w(cue(14, x)) for x in ('why', 'the universe', 'universe', 'exists', 'at all', 'all.')], font=F_TYPE)
    return s


def sF(t, D):
    """If that answer arrives, Hawking writes, humanity would "know the mind of God.\""""
    s = Shot(t, D)
    s.camera(1.0, 1.06)
    words(s.hud, (W / 2, 330), 'if that answer arrives', 46, t, [w(cue(14, x)) for x in ('If that', 'that answer', 'answer', 'arrives,')], font=F_TYPE)
    words(s.top, (W / 2, 520), '"know the mind of God"', 96, t,
          [w(cue(14, x)) for x in ('know', 'the mind', 'mind', 'of God', 'God.')], font=F_TYPE)
    underline(s.top, W / 2 - 560, W / 2 + 560, 600, t, w(cue(14, 'God.')) + 0.3, width=10)
    words(s.hud, (W / 2, 720), 'HAWKING WRITES', 44, t, w(cue(14, 'writes,')))
    return s


def sG(t, D):
    """Written by a man who had lost his voice, the book invited millions into the oldest question
    humans have ever asked of the night sky."""
    s = Shot(t, D)
    s.camera(1.0, 1.10, (W / 2, 470), (W / 2 + 40, 430))
    P.mask_reveal(s.mid, SKY, W / 2, 500, t, ENTER, dur=2.2, origin=(0.5, 0.75))                  # 8
    words(s.hud, (W / 2, 990), 'written by a man who had lost his voice', 42, t,
          [w(cue(15, x)) for x in ('Written', 'by a', 'a man', 'man', 'who', 'had lost', 'lost', 'his voice')], font=F_TYPE) if t < w(cue(15, 'the book')) else None
    tag(s.hud, (W / 2, 990), 'THE OLDEST QUESTION', 48, t, w(cue(15, 'oldest'))) if t >= w(cue(15, 'the book')) else None
    end = w(cue(15, 'sky.', 1, 'e'))
    tag(s.hud, (W / 2, 120), 'A BRIEF HISTORY OF TIME', 72, t, end + 0.4)
    tag(s.hud, (W / 2, 205), 'STEPHEN HAWKING, 1988', 40, t, end + 0.9, bg=CREAM, fg=INK)
    return s


SHOTS = [
    (0.0, sA),
    (cue(13, 'The result') - LEAD, sB, 'up'),
    (cue(13, 'and has') - LEAD, sC, 'lr'),
    (cue(13, 'It also') - LEAD, sD, 'rl'),
    (cue(14, 'Its final') - LEAD, sE, 'up'),
    (cue(14, 'If that') - LEAD, sF, 'lr'),
    (cue(15, 'Written') - LEAD, sG, 'up'),
]
END = cue.total + 3.0        # hold the end title in silence


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
