"""Demo reel: maps, timeline, charts, objects, camera and layered compositions; every cut is one of
the new transitions. Chart values in vignette 3 are illustrative (labelled DEMO DATA)."""
import sys, subprocess
from PIL import Image
import vox
from vox import W, H, asset, contact_sheet, F_TYPE
import style as st
from style import Shot, kicker, words, tag
import presets as P
import annotate as A
import maps, timeline as TL, charts as C, objects as O

M = maps.WorldMap(box=(120, 90, 1800, 990))
EU = M.around((4, 49), 2600)
TLN = TL.Timeline(1940, 2000, box=(220, 600, 1700, 640), step=10)
LETTER = O.letter(['Dear Stephen,', '---', '---', '---', '---', '---'], signature='J.')
PAPER = O.newspaper('A brief history of time is published', date='1 April 1988', photo=Image.open(asset('hawking_wheelchair.jpg')))
POLA = O.polaroid(Image.open(asset('hawking_gown.jpg')), 'Cambridge')
NOTE = O.sticky_note('ask why time has a direction')
HOSP = P.print_card(Image.open(asset('p01_hospital.png')), 900, seed=24)
PLANET = P.load(asset('c01_planet.png'), height=300)
CUP = P.load(asset('c02_cup.png'), width=420)
WED = P.print_card(Image.open(asset('wedding.jpg')), 520, seed=27)


def scene(n, name, cam=True):
    def deco(fn):
        def run(t, D):
            s = Shot(t, D)
            if cam:
                s.camera(1.0, 1.02)
            fn(s, t)
            kicker(s.hud, t, n, name, start=0.1, hold=D - 0.9)
            return s
        return run
    return deco


@scene(1, 'Map: zoom, route, marker, border', cam=False)
def v1(s, t):
    view = M.zoom(t, [(0.3, M.WORLD), (2.0, EU)])
    M.draw(s.mid, view, t, highlight={'GBR': 2.2})
    M.route(s.mid, view, [M.city('London'), M.city('Paris'), M.city('Geneva')], t, 2.4, dur=1.4)
    M.marker(s.mid, view, M.city('Geneva'), 'GENEVA', t, 3.6)
    M.border(s.mid, view, 'Italy', t, 3.0, dur=1.2)


@scene(2, 'Timeline: axis, events, era, counter')
def v2(s, t):
    TLN.axis(s.mid, t, 0.2)
    TLN.event(s.mid, 1963, 'Diagnosis', t, 1.2, side='up', until=3.2)
    TLN.event(s.mid, 1985, 'Pneumonia', t, 2.0, side='down')
    TLN.era(s.mid, 1963, 1985, 'two decades of work', t, 2.8)
    TL.year_counter(s.top, (W / 2, 230), 1963, 1988, t, 3.2, dur=1.3, size=150)


@scene(3, 'Charts: line, comparison, unit grid')
def v3(s, t):
    C.line_chart(s.mid, (180, 260, 820, 700), [(1980, 2), (1984, 3), (1986, 2.6), (1988, 8), (1992, 6.5), (1996, 7)], t, 0.3, mark=(1988, 'PEAK'), ylabel='DEMO DATA')
    C.compare(s.mid, (1180, 330), [('A', 237), ('B', 90), ('C', 41)], t, 1.4, width=520, height=56, unit=' wk')
    C.unit_grid(s.mid, (1150, 700), 50, 17, t, 2.6, cols=10, cell=30)


@scene(4, 'Counter and flow diagram')
def v4(s, t):
    C.counter(s.top, (W / 2, 230), 0, 10_000_000, t, 0.3, dur=1.6, size=130, suffix='+')
    C.flow(s.mid, [((420, 640), 'STAR'), ((960, 640), 'COLLAPSE'), ((1500, 640), 'BLACK HOLE')], t, [2.0, 2.6, 3.2])


@scene(5, 'Objects: envelope, polaroid, tape, pin, note')
def v5(s, t):
    O.envelope(s.mid, LETTER, 620, 720, t, 0.4)
    P.drop(s.mid, P.rot_scale(POLA, 4, 1.0, key='pola'), 1380, 470, t, 1.8, rot=0, spin=10, key='pola_d')
    O.tape(s.mid, 1300, 200, t, 2.5, angle=-20)
    P.drop(s.mid, NOTE, 1560, 820, t, 3.0, rot=-6, spin=-8, height=0.4, key='note')
    O.pushpin(s.mid, 1560, 700, t, 3.5)


@scene(6, 'Newspaper spinning in')
def v6(s, t):
    O.spin_in(s.mid, P.rot_scale(PAPER, 0, 0.72, key='np'), W / 2, 540, t, 0.5, dur=1.1)
    A.ring(s.mid, (W / 2 - 300, 270, W / 2 + 300, 400), t, 2.4)


@scene(7, 'Camera: depth layers, pan, rack focus', cam=False)
def v7(s, t):
    s.camera(1.0, 1.05)
    s.pan(0.4, 160, 0, dur=3.6)
    s.rack(2.2, sharp='mid', amount=6, before='top')
    s.drift(3)
    P.put(s.layer(0.6), PLANET, 1500, 300)                 # far plane
    P.put(s.mid, HOSP, 820, 500)                             # the subject
    P.put(s.mid, P.rot_scale(WED, -5, 1.0, key='w5'), 1350, 640)
    P.put(s.top, CUP, 1640, 930)                             # near plane (foreground prop)
    tag(s.hud, (W / 2, 120), 'FOCUS SHIFTS TO THE PRINTS', 40, t, 2.2)


SEG = 5.0
VIGS = [v1, v2, v3, v4, v5, v6, v7]
CUTS = [None, 'pageturn', 'circle', 'shape', ('zoom', {'at': (620, 640)}), 'collage', 'lr']
SHOTS = [(i * SEG, fn) if CUTS[i] is None else (i * SEG, fn, CUTS[i]) for i, fn in enumerate(VIGS)]
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
