"""Demo reel: the 12 scrapbook presets, one vignette each. Edit the asset names at the top to
the current project's files, then:  python demo_presets.py sheet out/demo.png 1 5 9  or
python demo_presets.py render 0 45.6 out/presets_demo.mp4"""
import sys, subprocess
from PIL import Image
import vox
from vox import W, H, asset, contact_sheet
import style as st
from style import Shot, kicker
import presets as P
import act1

WED = P.print_card(Image.open(asset('wedding.jpg')), 760, seed=21)
GOWN = P.print_card(Image.open(asset('hawking_gown.jpg')), 470, seed=22)
CHAIR = P.print_card(Image.open(asset('hawking_wheelchair.jpg')), 470, seed=23)
HOSP = P.print_card(Image.open(asset('p01_hospital.png')), 1180, seed=24)
PAGE = P.paper_card(560, 720, seed=9)
PAGE.alpha_composite(P.print_card(Image.open(asset('hawking_gown.jpg')), 430, seed=25), (65, 70))
LEFTPAGE = P.paper_card(560, 720, seed=10, text='CHAPTER 1', size=48)
CLIP = P.clipping('A Brief History of Time', date='1 April 1988')
COVER = P.paper_card(1180, 680, seed=12, text='1985', size=150)
BOOK = act1.BOOK
CHART, MANU = act1.CHART, act1.MANU


def scene(n, name):
    def deco(fn):
        def run(t, D):
            s = Shot(t, D)
            s.camera(1.0, 1.03)
            fn(s, t)
            kicker(s.top, t, n, name, start=0.1, hold=D - 0.9)
            return s
        return run
    return deco


@scene(1, 'Page flip')
def v1(s, t):
    P.put(s.mid, LEFTPAGE, W / 2 - 280, 500)
    P.put(s.mid, P.paper_card(560, 720, seed=11), W / 2 + 280, 500)
    P.page_flip(s.mid, PAGE, W / 2, 500, t, 0.5, dur=1.2)


@scene(2, 'Photo drop')
def v2(s, t):
    P.drop(s.mid, CHAIR, W / 2, 500, t, 0.3, rot=-4, key='chair')


@scene(3, 'Document unfold')
def v3(s, t):
    P.unfold(s.mid, CHART, W / 2, 520, t, 0.7, dur=1.4)


@scene(4, 'Newspaper clipping')
def v4(s, t):
    P.slide(s.mid, CLIP, (W + 500, 460), (W / 2 + 60, 500), t, 0.3, dur=1.2, rot=-3, key='clip')


@scene(5, 'Tear reveal')
def v5(s, t):
    P.put(s.mid, HOSP, W / 2, 500)
    P.tear_reveal(s.mid, COVER, W / 2, 500, t, 0.9)


@scene(6, 'Photo stack')
def v6(s, t):
    P.stack(s.mid, [WED, GOWN, CHAIR], [(W / 2 - 160, 500), (W / 2 + 230, 470), (W / 2 + 20, 540)], t, [0.2, 0.9, 1.6])


@scene(7, 'Stamp hit')
def v7(s, t):
    P.put(s.mid, MANU, W / 2, 500)
    P.stamp_hit(s.top, 'UNFINISHED', W / 2, 560, t, 1.0, size=96, ang=-11, shot=s)


@scene(8, 'Paper mask reveal')
def v8(s, t):
    P.mask_reveal(s.mid, HOSP, W / 2, 500, t, 0.3, dur=1.6, origin=(0.45, 0.4))


@scene(9, 'Friction slide')
def v9(s, t):
    P.slide(s.mid, MANU, (-500, 520), (W / 2, 500), t, 0.3, dur=1.0, rot=2.5, key='manu')


@scene(10, 'Cut-out assembly')
def v10(s, t):
    P.assemble(s.mid, BOOK, W / 2, 500, t, 0.3, n=8)


@scene(11, 'Photo flip')
def v11(s, t):
    P.flip(s.mid, GOWN, CHAIR, W / 2, 500, t, 1.0, dur=0.9)


@scene(12, 'Zoom into an image')
def v12(s, t):
    s.zoom_to((W / 2 - 250, 500 - 330, W / 2 + 250, 500 + 330), 0.9, dur=1.4, back_at=2.7)
    P.put(s.mid, GOWN, W / 2 - 560, 520)
    P.put(s.mid, CHAIR, W / 2, 500)
    P.put(s.mid, P.rot_scale(WED, 3, 0.62), W / 2 + 590, 520)


SEG = 3.8
VIGS = [v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12]
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
