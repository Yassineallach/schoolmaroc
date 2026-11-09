"""Demo reel: editorial annotations (annotate.py), one vignette per family, staged one at a time
the way they would be cued to narration."""
import sys, subprocess
from PIL import Image
import vox
from vox import W, H, asset, contact_sheet, document, F_TYPE, F_HEAD
import style as st
from style import Shot, kicker, words, tag
import presets as P
import annotate as A

HOSP = P.print_card(Image.open(asset('p01_hospital.png')), 1100, seed=24)
SCOPE = P.print_card(Image.open(asset('p02_telescope.png')), 1100, seed=25)
HOLE = P.print_card(Image.open(asset('p04_blackhole.png')), 1100, seed=26)
WED = P.print_card(Image.open(asset('wedding.jpg')), 700, seed=27)
DIAG = document(640, 700, ['Diagnosis', '---', 'Motor neurone disease', '---', 'about two years to live', '---', '---'],
                seed=95, title='MEDICAL REPORT', body_size=36)


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


@scene(1, 'Marker sweep and underline')
def v1(s, t):
    line, xy, sz = 'THE UNIVERSE IS EXPANDING', (W / 2, 440), 92
    A.sweep(s.top, A.words_box(xy, line, sz, 'EXPANDING'), t, 1.0)              # behind the word: draw first
    words(s.top, xy, line, sz, t, 0.2)
    A.underline(s.top, A.words_box(xy, line, sz, 'UNIVERSE'), t, 2.2, until=3.4)
    cap, cxy = 'distant galaxies are rushing away', (W / 2, 640)
    A.sweep(s.hud, A.text_box(cxy, cap, 46, F_TYPE), t, 2.9, colour=A.BEIGE, alpha=0.9)
    words(s.hud, cxy, cap, 46, t, 0.4, font=F_TYPE)


@scene(2, 'Circle, box and strike')
def v2(s, t):
    line, xy, sz = 'A SHORT HISTORY OF TIME', (W / 2, 360), 96
    words(s.top, xy, line, sz, t, 0.2)
    A.strike(s.top, A.words_box(xy, line, sz, 'SHORT'), t, 0.9)
    A.emphasis(s.top, (A.words_box(xy, line, sz, 'SHORT')[0] + 120, 250), 'BRIEF', 70, t, 1.4, colour=A.TERRA, base=A.TERRA)
    l2, xy2 = 'its point of no return is the event horizon', (W / 2, 620)
    words(s.top, xy2, l2, 48, t, 0.3, font=F_TYPE)
    A.ring(s.top, A.words_box(xy2, l2, 48, 'event horizon', F_TYPE), t, 2.2, until=3.6)
    A.outline(s.top, A.text_box((W / 2, 780), 'NOTHING ESCAPES', 56), t, 2.9)
    words(s.top, (W / 2, 780), 'NOTHING ESCAPES', 56, t, 0.4)


@scene(3, 'Emphasis and statistics')
def v3(s, t):
    line, xy, sz = 'GIVEN ABOUT TWO YEARS', (W / 2, 330), 80
    b1, b2 = A.words_box(xy, line, sz, 'GIVEN ABOUT'), A.words_box(xy, line, sz, 'TWO YEARS')
    words(s.top, ((b1[0] + b1[2]) / 2, xy[1]), 'GIVEN ABOUT', sz, t, 0.2)
    A.emphasis(s.top, ((b2[0] + b2[2]) / 2, xy[1]), 'TWO YEARS', sz, t, 1.0, before=True)
    A.stat(s.top, (W / 2, 600), '237 WEEKS', 150, t, 2.0)
    P.stamp_hit(s.top, 'RECORD', W / 2 + 430, 700, t, 3.0, size=70, ang=-10, shot=s)


SC = (426, 199, 0.639)                       # plate image origin and scale on the placed print


def pt(x, y):
    return (SC[0] + x * SC[2], SC[1] + y * SC[2])


@scene(4, 'Photo: circle and arrow')
def v4(s, t):
    P.put(s.mid, SCOPE, W / 2, 500)
    gx, gy = pt(380, 130)
    A.ring(s.mid, (gx - 70, gy - 45, gx + 70, gy + 45), t, 0.8, until=2.6)
    tag(s.hud, (1560, 200), 'A DISTANT GALAXY', 40, t, 0.9)
    tx, ty = pt(900, 300)
    A.arrow(s.mid, (1560, 860), (tx + 40, ty + 60), t, 2.4)
    tag(s.hud, (1560, 900), 'THE TELESCOPE', 40, t, 2.4)


@scene(5, 'Photo: frame, corners, spotlight')
def v5(s, t):
    P.put(s.mid, HOSP, W / 2, 500)
    x0, y0 = pt(520, 170)
    x1, y1 = pt(790, 370)
    A.corners(s.mid, (x0, y0, x1, y1), t, 0.7, until=1.9, exit='fade')
    A.frame(s.mid, (x0, y0, x1, y1), t, 1.6, until=2.6, exit='fade')
    A.spotlight(s.mid, ((x0 + x1) / 2, (y0 + y1) / 2), 150, t, 2.4)
    tag(s.hud, (W / 2, 870), 'KEPT ALIVE BY A VENTILATOR', 42, t, 2.6)


@scene(6, 'Photo: magnify and focus')
def v6(s, t):
    P.put(s.mid, HOLE, W / 2, 500)
    cx, cy = pt(832, 436)
    edge = (cx + 112, cy - 10)
    A.magnify(s.mid, s.mid.copy(), edge, 150, 2.6, (1560, 330), t, 0.8, until=2.4)
    tag(s.hud, (1560, 540), 'THE EDGE', 40, t, 1.1)
    A.focus(s, (cx - 260, cy - 150, cx + 260, cy + 150), 2.5, hold=1.0)
    A.ring(s.mid, (cx - 120, cy - 120, cx + 120, cy + 120), t, 2.9)


@scene(7, 'Document: marks, bracket, connector')
def v7(s, t):
    P.put(s.mid, DIAG, 760, 520)
    A.mark(s.mid, (470, 340), 'dash', t, 0.6)
    A.mark(s.mid, (470, 429), 'star', t, 1.0)
    A.ring(s.mid, (500, 405, 905, 455), t, 1.2, tilt=-2)
    A.bracket(s.mid, 1100, 400, 545, t, 1.9, side='right')
    A.connect(s.mid, [(1140, 472), (1260, 440), (1380, 470)], t, 2.5)
    words(s.top, (1560, 470), 'his deadline', 46, t, 2.9, font=F_TYPE)
    A.mark(s.mid, (470, 518), 'tick', t, 3.3)


@scene(8, 'Stamp on a document')
def v8(s, t):
    P.put(s.mid, DIAG, 760, 520)
    A.underline(s.mid, (500, 498, 860, 520), t, 0.6, double=True)
    P.stamp_hit(s.mid, '1963', 760, 720, t, 1.6, size=100, ang=-7, shot=s)
    A.arrow(s.mid, (1420, 300), (900, 690), t, 2.6, bend=-0.25)
    tag(s.hud, (1480, 260), 'AGE 21', 52, t, 2.6)


@scene(9, 'Charts: bars and sections')
def v9(s, t):
    A.bars(s.mid, (260, 300, 860, 780), [3, 5, 4, 9, 6], t, 0.3, highlight=(3,), labels=['A', 'B', 'C', 'D', 'E'], fill_at=1.8)
    A.wedge(s.mid, (1380, 540), 230, 0, 115, t, 1.2)
    A.connect(s.mid, [(1500, 360), (1620, 250), (1700, 250)], t, 2.6, arrowhead=False)
    tag(s.hud, (1720, 210), 'ONE THIRD', 40, t, 2.9)


SEG = 4.4
VIGS = [v1, v2, v3, v4, v5, v6, v7, v8, v9]
SHOTS = [(i * SEG, fn, ('lr', 'up', 'rl')[i % 3]) for i, fn in enumerate(VIGS)]
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
