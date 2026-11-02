"""Act 1: The Machine Stays On. Narration clips 1-4."""
import sys
from PIL import Image, ImageDraw
from vox import *  # noqa: F401,F403
import style as st
import presets as P
from style import sfx, ENTER, Shot, Photo, sheet, words, tag, underline, kicker

CLIPS = (1, 2, 3, 4)
cue = make_cue(CLIPS)

INDIGO = (52, 52, 110)
LAV = (150, 148, 200)

HOSP = Photo(Image.open(asset('p01_hospital.png')), 1240, rot=-1.2, seed=11)
HOSP_SMALL = Photo(Image.open(asset('p01_hospital.png')), 720, rot=2.0, seed=12)
WED = Photo(Image.open(asset('wedding.jpg')), 860, rot=-2.0, seed=21)
HAWK = Photo(Image.open(asset('hawking_wheelchair.jpg')), 500, rot=1.8, seed=31)

HOSP_CARD = P.print_card(Image.open(asset('p01_hospital.png')), 1240, seed=11)
WED_CARD = P.print_card(Image.open(asset('wedding.jpg')), 860, seed=21)
HAWK_CARD = P.print_card(Image.open(asset('hawking_wheelchair.jpg')), 500, seed=31)
HAWK_COVER = P.paper_card(HAWK_CARD.width + 10, HAWK_CARD.height + 10, seed=33, text='?', size=220)
CLIP = P.clipping('A Brief History of Time', w=470, h=430, seed=7, date='1988')
CHART = document(620, 720, ['Switzerland, 1985', '---', 'Pneumonia', '---', 'Paralysed', '---',
                            'Wasting disease', '---', '---'], seed=5, title='MEDICAL CHART', body_size=40)
MANU = document(640, 780, ['Chapter 1', '---', '---', '---', '---', '---', '---'], seed=8,
                title='MANUSCRIPT', typed=True, body_size=34)


def book_cover(w=500, h=750):
    b = Image.new('RGBA', (w, h), INDIGO + (255,))
    d = ImageDraw.Draw(b)
    d.rectangle((24, 24, w - 24, h - 24), outline=CREAM + (255,), width=3)
    for i, s in enumerate(('A BRIEF', 'HISTORY', 'OF TIME')):
        d.text((w / 2, 135 + i * 72), s, font=F_HEAD(60), fill=CREAM + (255,), anchor='mm')
    cx, cy = w / 2, 480
    for r, col in ((125, LAV), (86, CREAM), (38, INDIGO)):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col + (255,), width=4)
    d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=RED + (255,))
    d.text((w / 2, h - 78), 'STEPHEN HAWKING', font=F_SERIF(32), fill=CREAM + (255,), anchor='mm')
    b.putalpha(torn_mask(w, h, 41, amp=3, step=16))
    return b


BOOK = book_cover()


def pulse(c, x0, x1, y, t, start, flat_at):
    if t < start:
        return
    pts, x = [], x0
    k = max(0.0, 1.0 - max(0.0, t - flat_at) / 1.0)
    while x < x1:
        pts += [(x, y), (x + 40, y), (x + 55, y - 90 * k), (x + 70, y + 60 * k), (x + 85, y), (x + 160, y)]
        x += 160
    marker_line(c, pts, ease((t - start) / 1.6), width=7, color=INK)


def bubble(c, cx, cy, t, start):
    if t < start:
        return
    p, op = st.sp(t, start), st.fade(t, start, 0.3)
    s = lerp(0.6, 1.0, min(p, 1.05))
    a = int(255 * op)
    tile = Image.new('RGBA', (420, 340), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.ellipse((40, 20, 380, 240), fill=CREAM + (a,), outline=INK + (a,), width=7)
    d.polygon([(120, 190), (60, 300), (180, 212)], fill=CREAM + (a,))
    d.line([(118, 198), (60, 300), (174, 216)], fill=INK + (a,), width=7)
    for i in (-1, 0, 1):
        d.ellipse((210 + i * 70 - 16, 114, 210 + i * 70 + 16, 146), fill=INK + (a,))
    tile = tile.resize((int(420 * s), int(340 * s)), Image.BICUBIC)
    c.alpha_composite(tile, (int(cx - tile.width / 2), int(cy - tile.height / 2)))


def sA(t, D):
    """In 1985, a man lies unconscious in a Swiss hospital, kept alive by a ventilator."""
    s = Shot(t, D)
    s.camera(1.0, 1.07, (W / 2, H / 2), (700, 470))
    P.mask_reveal(s.mid, HOSP_CARD, W / 2, 500, t, 0.1, dur=2.0, origin=(0.33, 0.42))     # 8
    P.stamp_hit(s.mid, '1985', 520, 250, t, w(cue(1, '1985')), size=96, ang=-7, shot=s)       # 7
    P.stamp_hit(s.mid, 'SWITZERLAND', 1380, 250, t, w(cue(1, 'Swiss hospital')), size=62, ang=5, shot=s)
    tag(s.hud, (W / 2, 975), 'KEPT ALIVE BY A VENTILATOR', 44, t, w(cue(1, 'kept alive')))
    kicker(s.hud, t, 1, 'The machine stays on')
    return s


def sB(t, D):
    """Pneumonia has flooded his lungs, and his body, already paralysed by a wasting disease,
    can no longer fight it alone."""
    s = Shot(t, D)
    s.camera(1.0, 1.0)
    s.zoom_to((1000, 90, 1660, 850), w(cue(1, 'his body')), dur=2.4, fill=0.86)              # 12
    HOSP_SMALL.place(s.mid, 560, 470, t, ENTER, frm='left')
    P.unfold(s.mid, CHART, 1330, 470, t, ENTER + 0.15, dur=1.0)                                 # 3
    for ph in ('flooded', 'paralysed', 'wasting'):
        sfx('marker', w(cue(1, ph)), 1200, dur=0.5)
    marker_circle(s.mid, 1170, 375, 135, 38, ease((t - w(cue(1, 'flooded'))) / 0.5), seed=1)
    marker_circle(s.mid, 1160, 470, 125, 38, ease((t - w(cue(1, 'paralysed'))) / 0.5), seed=2)
    marker_circle(s.mid, 1215, 566, 180, 38, ease((t - w(cue(1, 'wasting'))) / 0.5), seed=3)
    words(s.hud, (W / 2, 975), 'can no longer fight it alone', 46, t,
          [w(cue(1, x)) for x in ('can', 'no longer', 'longer', 'fight', 'it alone', 'alone')], font=F_TYPE)
    return s


def sC(t, D):
    """His doctors raise an unthinkable option: switching the machine off."""
    s = Shot(t, D)
    s.camera(1.0, 1.06)
    words(s.top, (W / 2, 260), 'an unthinkable option', 52, t,
          [w(cue(1, 'an unthinkable')), w(cue(1, 'unthinkable')), w(cue(1, 'option'))], font=F_TYPE)
    pulse(s.mid, 160, 1760, 690, t, ENTER, w(cue(1, 'off', 1, 'e')))
    k = 0.15
    while k < w(cue(1, 'off', 1, 'e')):          # monitor beeps that stop as the line flattens
        sfx('beep', k, 960)
        k += 0.8
    words(s.top, (W / 2, 470), 'SWITCH IT OFF?', 150, t,
          [w(cue(1, 'switching')), w(cue(1, 'machine')), w(cue(1, 'off'))])
    return s


def sD(t, D):
    """His wife refuses. Surgeons cut an opening in his windpipe, and he survives."""
    s = Shot(t, D)
    s.camera(1.03, 1.0, (640, 470))
    P.drop(s.mid, WED_CARD, 640, 470, t, ENTER, rot=-2, spin=-12, key='wed')                    # 2
    P.stamp_hit(s.mid, 'REFUSED', 640, 770, t, w(cue(2, 'refuses')), size=110, ang=-6, shot=s)
    words(s.top, (1520, 330), 'AN OPENING', 84, t, [w(cue(2, 'an opening')), w(cue(2, 'opening'))])
    words(s.top, (1520, 430), 'IN THE WINDPIPE', 62, t, [w(cue(2, 'in his')), w(cue(2, 'his windpipe')), w(cue(2, 'windpipe'))])
    tag(s.top, (1520, 640), 'HE SURVIVES', 80, t, w(cue(2, 'survives')))
    return s


def sE(t, D):
    """But the operation takes what little remained of his voice."""
    s = Shot(t, D)
    s.camera(1.08, 1.0)
    bubble(s.mid, W / 2, 440, t, ENTER)
    sfx('marker', w(cue(2, 'voice')), W / 2, dur=0.4)
    strike(s.top, W / 2 - 240, W / 2 + 240, 400, ease((t - w(cue(2, 'voice'))) / 0.4), width=14)
    words(s.top, (W / 2, 790), 'what little remained of his voice', 52, t,
          [w(cue(2, x)) for x in ('what', 'little', 'remained', 'of his', 'his voice', 'voice')], font=F_TYPE)
    return s


def sF(t, D):
    """Back in England sits an unfinished manuscript. Its author can no longer speak a word of it."""
    s = Shot(t, D)
    s.camera(1.0, 1.05, (700, 480), (1000, 480))
    P.slide(s.mid, MANU, (W + 420, 560), (700, 480), t, ENTER, dur=1.15, rot=-3, key='manu')    # 9
    words(s.top, (1430, 300), 'ENGLAND', 96, t, w(cue(3, 'England')))
    P.stamp_hit(s.mid, 'UNFINISHED', 700, 560, t, w(cue(3, 'unfinished')), size=92, ang=-12, shot=s)
    words(s.top, (1430, 520), 'can no longer', 46, t, [w(cue(3, 'can')), w(cue(3, 'no longer')), w(cue(3, 'longer'))], font=F_TYPE)
    words(s.top, (1430, 590), 'speak a word of it', 46, t, [w(cue(3, x)) for x in ('speak', 'a word', 'word', 'of it', 'it')], font=F_TYPE)
    return s


def sG(t, D):
    """The man is Stephen Hawking, and that manuscript would become A Brief History of Time."""
    s = Shot(t, D)
    s.camera(1.04, 1.04, (520, 480), (520, 480))
    s.push(w(cue(4, 'become')), -0.04, (W / 2, 480), dur=1.4)
    P.put(s.mid, P.rot_scale(HAWK_CARD, 1.8, 1.0, key='hawk'), 520, 470)
    P.tear_reveal(s.mid, P.rot_scale(HAWK_COVER, 1.8, 1.0, key='hcov'), 520, 470, t, w(cue(4, 'Stephen')) - 0.15)   # 5
    P.drop(s.mid, BOOK, 1480, 470, t, w(cue(4, 'become')), rot=3, spin=14, key='book')
    words(s.top, (520, 950), 'STEPHEN HAWKING', 72, t, [w(cue(4, 'Stephen')), w(cue(4, 'Hawking'))])
    underline(s.top, 230, 810, 1000, t, w(cue(4, 'Hawking')) + 0.3)
    return s


def sH(t, D):
    """Published on April Fool's Day, 1988, it set out to explain the birth, structure, and possible
    fate of the universe to readers with no training in physics."""
    s = Shot(t, D)
    s.camera(1.0, 1.0)
    s.push(w(cue(4, 'birth')), 0.06, (1340, 450), dur=3.0)
    sheet(s.mid, BOOK, 470, 470, t, ENTER, rot=-2, frm='left')
    P.slide(s.mid, CLIP, (W + 400, 760), (790, 640), t, -0.05, dur=1.1, rot=4, key='clip')      # 4
    P.stamp_hit(s.mid, '1 APRIL 1988', 790, 720, t, w(cue(4, 'April')), size=52, ang=-8, shot=s)
    for i, (word, ph) in enumerate((('BIRTH', 'birth'), ('STRUCTURE', 'structure'), ('FATE', 'fate'))):
        y = 260 + i * 170
        words(s.top, (1340, y), word, 100, t, w(cue(4, ph)))
        underline(s.top, 1340 - 210, 1340 + 210, y + 62, t, w(cue(4, ph)) + 0.2, seed=i)
    words(s.hud, (1340, 790), 'for readers with no training in physics', 34, t, w(cue(4, 'readers')), font=F_TYPE)
    return s


SHOTS = [
    (0.0, sA),
    (cue(1, 'Pneumonia') - LEAD, sB, 'up'),
    (cue(1, 'His doctors') - LEAD, sC, 'lr'),
    (cue(2, 'His wife') - LEAD, sD, 'rl'),
    (cue(2, 'But the operation') - LEAD, sE, 'up'),
    (cue(3, 'Back in England') - LEAD, sF, 'lr'),
    (cue(4, 'The man is') - LEAD, sG, 'up'),
    (cue(4, 'Published') - LEAD, sH, 'rl'),
]
END = cue.total


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
