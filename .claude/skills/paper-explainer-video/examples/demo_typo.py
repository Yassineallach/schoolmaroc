"""Demo reel: editorial typography (typo.py). English vignettes 1-11, Arabic 12-13."""
import sys, subprocess
from PIL import Image
import vox
from vox import W, H, asset, contact_sheet
import style as st
from style import Shot, kicker
import presets as P
import annotate as A
import typo as TY
from typo import Text

HOLE = P.print_card(Image.open(asset('p04_blackhole.png')), 760, seed=26)
CHAIR = P.print_card(Image.open(asset('hawking_wheelchair.jpg')), 380, seed=23)
GOWN = P.print_card(Image.open(asset('hawking_gown.jpg')), 360, seed=22)

# English
H1 = Text('THE UNIVERSE IS EXPANDING', 'headline', max_w=1100)
ROLES = [Text('Headline', 'headline', size=110), Text('Secondary headline', 'subhead'), Text('An important statement.', 'statement'),
         Text('Stephen Hawking', 'name'), Text('a typed explanatory caption', 'caption'), Text('“A quotation in italic”', 'quote'),
         Text('Cambridge · England', 'label')]
BH = Text('BLACK HOLE', 'headline', size=150)
EH = Text('EVENT HORIZON', 'subhead', size=70)
PB = Text('Physics breaks.', 'statement', size=120)
ST = Text('Squeeze the universe small enough, and both apply at once.', 'statement', size=64, max_w=900)
SL = Text('NOTHING ESCAPES NOT EVEN LIGHT', 'subhead', size=84, max_w=1300, align='m')
AS = Text('A FAINT GLOW', 'headline', size=140)
SP = Text('TWO THEORIES REFUSE TO COOPERATE', 'subhead', size=80, max_w=1500, align='m')
CU = Text('A SHORT HISTORY OF TIME', 'subhead', size=90, max_w=1500, align='m')
BR = Text('BRIEF', 'headline', size=110)
TW = Text('Written by a man who had lost his voice', 'caption', size=50, max_w=1200)
QU = Text('“know the mind of God”', 'quote', size=96, max_w=1400, align='m')
DIS = Text('THE UNIVERSE IS NOT ENTIRELY DARK', 'headline', size=96, max_w=1100)

# Arabic
AH = Text('الكون يتمدد', 'headline', size=150)
AQ = Text('«أن نعرف عقل الله»', 'quote', size=100)
AC = Text('كتبه رجل فقد صوته', 'caption', size=60)
AS2 = Text('الضوء لا يفلت أبداً', 'statement', size=90)


def scene(n, name):
    def deco(fn):
        def run(t, D):
            s = Shot(t, D)
            s.camera(1.0, 1.02)
            fn(s, t)
            kicker(s.hud, t, n, name, start=0.1, hold=D - 0.9)
            return s
        return run
    return deco


@scene(1, 'Hierarchy')
def v1(s, t):
    y = 110
    for i, T in enumerate(ROLES):
        T.draw(s.top, (200, y), t, 0.2 + i * 0.28, anim='lines')
        Text(T.role.upper(), 'label', size=20, colour=TY.TERRA).draw(s.top, (1780, y + T.h / 2 - 12), t, 0.2 + i * 0.28, anchor='r', anim='words', sound=False)
        y += T.h + 18


@scene(2, 'Word by word, accent, marker')
def v2(s, t):
    xy = (200, 330)
    A.sweep(s.top, H1.box('EXPANDING', xy), t, 2.3, alpha=0.32)
    H1.draw(s.top, xy, t, 0.3, anim='words', stagger=0.32, accent={'EXPANDING': 2.0})
    A.underline(s.top, H1.box('UNIVERSE', xy), t, 3.0, until=4.0)
    P.put(s.mid, P.rot_scale(HOLE, 4, 0.7, key='h7'), 1500, 820)


@scene(3, 'Letters and letter spacing')
def v3(s, t):
    BH.draw(s.top, (W / 2, 300), t, 0.3, anim='letters', anchor='m')
    EH.draw(s.top, (W / 2, 560), t, 1.6, anim='tracking', anchor='m', dur=1.6)


@scene(4, 'Scale and line reveal')
def v4(s, t):
    PB.draw(s.top, (180, 230), t, 0.3, anim='scale', stagger=0.25)
    ST.draw(s.top, (180, 520), t, 1.6, anim='lines')
    P.put(s.mid, P.rot_scale(CHAIR, -3, 1.0, key='c3'), 1480, 520)


@scene(5, 'Slide from all sides, assemble')
def v5(s, t):
    SL.draw(s.top, (W / 2, 200), t, 0.3, anim='slide', anchor='m', stagger=0.14)
    AS.draw(s.top, (W / 2, 560), t, 2.0, anim='assemble', anchor='m', dur=0.9)


@scene(6, 'Split for a contradiction')
def v6(s, t):
    if t < 1.4:                                   # revealed by bars, then the same line splits
        SP.draw(s.top, (W / 2, 470), t, 0.0, anim='mask', shape='bars', anchor='m', dur=0.6)
    else:
        SP.draw(s.top, (W / 2, 470), t, 1.4, anim='split', anchor='m', dur=1.6)


@scene(7, 'Paper cut-out words, strike, stamp')
def v7(s, t):
    xy = (W / 2, 420)
    CU.draw(s.mid, xy, t, 0.3, anim='cutout', anchor='m')
    A.strike(s.top, CU.box('SHORT', xy, anchor='m'), t, 2.0)
    BR.draw(s.top, (CU.box('SHORT', xy, anchor='m')[0] - 20, 220), t, 2.7, anim='stamp', shot=s)


@scene(8, 'Newspaper headline')
def v8(s, t):
    TY.press(s.mid, (210, 230), 'A brief history of time is published', t, 0.3, width=1500, dateline='1 April 1988 · London', size=100)


@scene(9, 'Oversized numbers')
def v9(s, t):
    TY.big_number(s.top, (560, 250), '1963', t, 0.3, label='DIAGNOSIS · AGE 21')
    TY.big_number(s.top, (1420, 250), '237', t, 1.8, role='stat', label='WEEKS ON THE LIST', colour=TY.WARM_BLACK)


@scene(10, 'Typewriter and geometric mask')
def v10(s, t):
    TW.typewriter(s.top, (240, 260), t, 0.3, cps=22)
    QU.draw(s.top, (W / 2, 520), t, 2.4, anim='mask', shape='circle', anchor='m', dur=0.9)


@scene(11, 'Term card and name card')
def v11(s, t):
    TY.term_card(s.top, (160, 260), 'EVENT HORIZON', 'the point of no return around a black hole', t, 0.4)
    P.put(s.mid, P.rot_scale(GOWN, -3, 1.0, key='g3'), 820, 600)
    TY.name_card(s.top, (1080, 560), 'Stephen Hawking', 'Physicist · 1942 – 2018', t, 1.6)


@scene(12, 'Arabic: headline, name, date')
def v12(s, t):
    AH.draw(s.top, (1760, 160), t, 0.3, anim='words', anchor='r', stagger=0.4, accent={'يتمدد': 1.4})
    TY.name_card(s.top, (1760, 470), 'ستيفن هوكينغ', 'عالم فيزياء نظرية', t, 1.4, anchor='r')
    TY.big_number(s.top, (480, 420), '١٩٨٨', t, 2.4, label='نُشر الكتاب', lang='ar')


@scene(13, 'Arabic: typewriter, quote, newspaper')
def v13(s, t):
    TY.press(s.mid, (260, 110), 'تاريخ موجز للزمن', t, 0.2, width=1400, dateline='١ أبريل ١٩٨٨', size=110)
    AC.typewriter(s.top, (1660 - AC.w, 560), t, 1.4, cps=12)
    AQ.draw(s.top, (W / 2, 720), t, 2.8, anim='mask', shape='diagonal', anchor='m', dur=0.9)


SEG = 4.6
VIGS = [v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13]
CUTS = ['lr', 'up', 'rl', 'shape', 'lr', 'circle', 'up', 'pageturn', 'rl', 'up', 'lr', 'collage']
SHOTS = [(0.0, VIGS[0])] + [(i * SEG, fn, CUTS[i - 1]) for i, fn in enumerate(VIGS) if i > 0]
END = SEG * len(VIGS)


def frame(t):
    return st.make_frame(SHOTS, END, t, (1,))


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
    else:
        a, b, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                              '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for f in range(int(round(a * 30)), int(round(b * 30))):
            p.stdin.write(frame(f / 30).tobytes())
        p.stdin.close(); p.wait()
