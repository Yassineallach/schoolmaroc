"""Demo reel: scene environments and compositions (scenes.py). Each vignette is a different
editorial page; cuts use different transitions between them."""
import sys, subprocess
from PIL import Image
import vox
from vox import W, H, asset, contact_sheet
import style as st
from style import Shot, kicker, tag
import presets as P
import annotate as A
import scenes as S
import typo as TY
from typo import Text

st.KICKER_XY = (620, 1000)
NIGHT = Image.open(asset('p02_night.png'))
TEENS = Image.open(asset('p01_teens.png'))
GUTS = Image.open(asset('guts_v38.png'))
GRIFF = Image.open(asset('griffith_color.png'))
DUEL = Image.open(asset('snow_duel_departure.png'))
PANELS = [Image.open(asset(f)) for f in ('dragon_slayer_ch1.png', 'cannon_arm.png', 'guts_griffith_camaraderie.png', 'griffith_victorious.png', 'band_somber.png', 'friend_page.png')]
MIURA = P.print_card(Image.open(asset('miura_desk.png')), 560, seed=3)
CLIP = P.clipping('A new arc begins', date='2023', seed=5)


def scene(n, name, envname, dark=False):
    def deco(fn):
        def run(t, D):
            s = Shot(t, D)
            S.env(s, envname)
            fn(s, t)
            lab = Text(f'{n:02d}  {name.upper()}', 'label', size=24, colour=S.ink(s))
            lab.draw(s.hud, (64, 1020), t, 0.1, anim='words', sound=False)
            return s
        return run
    return deco


@scene(1, 'Full-screen illustration', 'bleed')
def v1(s, t):
    S.fullbleed(s, NIGHT, t, 0.0, ken=(1.02, 1.12), focus=(0.4, 0.5), focus_to=(0.5, 0.45), darken=0.45)
    S.type_page(s, 'He sleeps sitting up.', t, 1.2, role='statement', size=70, xy=(W / 2, 880), layer=s.hud)


@scene(2, 'Charcoal: dramatic type', 'charcoal')
def v2(s, t):
    S.type_page(s, 'Far from finished.', t, 0.4, role='statement', size=150, anim='words', accent={'finished.': 1.6})


@scene(3, 'Minimal cream', 'cream')
def v3(s, t):
    s.camera(1.0, 1.03)
    P.drop(s.mid, P.rot_scale(MIURA, -2, 1.0, key='m'), *(S.rule_of_thirds('left')[0], 470), t, 0.2, rot=0, spin=-6, key='md')
    TY.name_card(s.top, (S.rule_of_thirds('left')[1], 380), 'Kentaro Miura', 'The other teenager', t, 0.8)


@scene(4, 'Split screen', 'bleed')
def v4(s, t):
    S.split(s, GUTS, GRIFF, t, 0.1, ratio=0.5, divide='tear')
    tag(s.hud, (W * 0.25, 940), 'GUTS', 52, t, 1.2)
    tag(s.hud, (W * 0.75, 940), 'GRIFFITH', 52, t, 1.5, bg=S.CHARCOAL, fg=S.CREAM)


@scene(5, 'Manga halftone panels', 'halftone')
def v5(s, t):
    S.panel_grid(s, PANELS, t, [0.2 + 0.25 * i for i in range(6)], cols=3, box=(140, 120, 1780, 940))


@scene(6, 'Archive collage', 'archive')
def v6(s, t):
    s.camera(1.0, 1.04)
    P.slide(s.mid, CLIP, (-500, 520), (720, 520), t, 0.2, dur=1.0, rot=-3, key='clip')
    TY.big_number(s.top, (1400, 300), '2023', t, 1.0, label='A NEW ARC')


@scene(7, 'Solid terracotta: one number', 'terra')
def v7(s, t):
    TY.big_number(s.top, (W / 2, 330), '70M', t, 0.3, role='stat', colour=S.CREAM, label=None, accent_bar=False)
    Text('COPIES IN CIRCULATION', 'label', size=32, colour=S.CREAM).draw(s.hud, (W / 2, 640), t, 1.2, anim='words', anchor='m')


@scene(8, 'Geometric comparison', 'geometric')
def v8(s, t):
    Text('FIST OF THE NORTH STAR', 'subhead', size=56, max_w=600, align='m').draw(s.top, (W * 0.25, 420), t, 0.3, anim='slide', anchor='m')
    Text('SHOJO MANGA', 'subhead', size=56).draw(s.top, (W * 0.73, 440), t, 0.9, anim='slide', anchor='m')
    Text('+', 'headline', size=140, colour=S.TERRA).draw(s.top, (W * 0.5, 410), t, 1.4, anim='scale', anchor='m')


@scene(9, 'Infographic grid', 'grid')
def v9(s, t):
    import charts as C
    C.compare(s.mid, (520, 360), [('ENGLISH', 10), ('ALL EDITIONS', 70)], t, 0.3, width=1000, height=80, unit=' M', highlight=1)
    Text('MILLION COPIES', 'label', size=30).draw(s.hud, (520, 260), t, 0.2, anim='words')


@scene(10, 'Letterbox: cinematic', 'bleed')
def v10(s, t):
    S.letterbox(s, DUEL, t, 0.0, ken=(1.0, 1.08), focus=(0.5, 0.45))
    Text('He leaves.', 'statement', size=60, colour=S.CREAM).draw(s.hud, (W / 2, 1000), t, 1.4, anim='words', anchor='m')


SEG = 4.0
VIGS = [v1, v2, v3, v4, v5, v6, v7, v8, v9, v10]
CUTS = ['pageturn', 'circle', 'shape', 'lr', 'collage', 'up', 'rl', ('zoom', {'at': (960, 500)}), 'pageturn']
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
                              '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for f in range(int(round(a * 30)), int(round(b * 30))):
            p.stdin.write(frame(f / 30).tobytes())
        p.stdin.close(); p.wait()
