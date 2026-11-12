"""Demo of the branding system on a project's own look (run from the project folder):

    python SK/examples/demo_brand.py out/brand            # stills: watermark, reveal, CTAs, outros
    python SK/examples/demo_brand.py out/brand --reel     # plus a 30 s reel with its sounds

Uses the official logo when SK/brand/logo.svg exists, the marked placeholder otherwise
(force=True: demos only; real renders draw no brand without the official logo).
"""
import os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
import vox, style, scenes as S, brand as B
from vox import W, H

OUT = sys.argv[1] if len(sys.argv) > 1 else 'out/brand'
os.makedirs(OUT, exist_ok=True)


def ground(env, T=3.0):
    s = style.Shot(0.0, 5.0)
    S.env(s, env)
    return Image.fromarray(style.compose(s, T)).convert('RGBA')


def save(img, name):
    img.convert('RGB').save(os.path.join(OUT, name))
    return os.path.join(OUT, name)


def act_frame(t):
    try:
        import importlib
        sys.path.insert(0, os.getcwd())
        return Image.fromarray(importlib.import_module('act1').frame(t)).convert('RGBA')
    except Exception:
        return ground('theme')


# 1. watermark: on a real frame of the film, top-right, quiet
img = act_frame(11.5)
x, y = B._corner_xy(B.CFG['watermark']['corner'], B.CFG['watermark']['margin'], 0, B.CFG['watermark']['width'])
B.place_logo(img, x, y, B.CFG['watermark']['width'], op=B.CFG['watermark']['opacity'], force=True)
save(img, '1_watermark.png')

# 2. logo reveal: three treatments, each caught at 4 moments
rows = []
for style_ in ('mask', 'scale', 'assemble'):
    row = []
    for tt in (0.35, 0.7, 1.1, 2.0):
        g = ground('cream')
        B.reveal(g, W / 2, H / 2 - 40, 520, tt, 0.0, style=style_, force=True)
        row.append(g.resize((480, 270)))
    rows.append(row)
sheet = Image.new('RGB', (480 * 4, 270 * 3), 'white')
for j, row in enumerate(rows):
    for i, im in enumerate(row):
        sheet.paste(im.convert('RGB'), (480 * i, 270 * j))
save(sheet, '2_reveal_mask_scale_assemble.png')

# 3. subscribe CTA: arriving, pressed, bell
frames = []
for tt in (0.5, 1.2, 1.7, 2.4):
    g = act_frame(22.0)
    B.cta_subscribe(g, 64, 900, tt, 0.0, 4.2, force=True)
    frames.append(g.resize((960, 540)))
sheet = Image.new('RGB', (1920, 1080))
for i, im in enumerate(frames):
    sheet.paste(im.convert('RGB'), (960 * (i % 2), 540 * (i // 2)))
save(sheet, '3_subscribe.png')

# 4. contextual comment CTA, and the like card
g = ground('paper')
B.cta_comment(g, 120, 300, 2.0, 0.0, 4.0, width=900)
B.cta_like(g, 120, 760, 1.5, 0.0, 3.2)
B.cta_share(g, 1100, 760, 1.6, 0.0, 3.0)
save(g, '4_comment_like_share.png')

# 5. outros: the three layouts on three grounds of this video's identity
for layout, env, nv in (('split', 'cream', 2), ('feature', 'theme', 1), ('centered', 'charcoal', 0)):
    B.CFG['outro']['layout'] = layout
    B.CFG['outro']['env'] = env
    B.CFG['outro']['next_videos'] = [{'title': 'Histoire des armes', 'thumbnail': None}, {'title': None, 'thumbnail': None}][:nv]
    outs = []
    for tt in (3.2, 8.5):
        s = B.outro_scene(tt, 10.0, force=True)
        outs.append(Image.fromarray(style.compose(s, tt)).convert('RGB'))
    sheet = Image.new('RGB', (1920, 540))
    for i, im in enumerate(outs):
        sheet.paste(im.resize((960, 540)), (960 * i, 0))
    save(sheet, f'5_outro_{layout}_{env}.png')
B.CFG['outro'].update(layout='auto', env='paper')
print('stills in', OUT)

if '--reel' in sys.argv:
    B.CFG['outro']['next_videos'] = [{'title': 'Histoire des armes', 'thumbnail': None}, {'title': None, 'thumbnail': None}]
    style.EVENTS.clear()
    base = act_frame(22.0)
    D = 30.0

    def frame(t):
        if t < 3.0:                                           # the reveal, on its own
            g = ground('cream', t)
            B.reveal(g, W / 2, H / 2 - 40, 520, t, 0.3, hold=1.6, force=True, T=0.3)
            return np.asarray(g.convert('RGB'))
        if t < 8.0:                                           # watermark ident on a shot of the film
            g = base.copy()
            tmp = Image.new('RGBA', g.size, (0, 0, 0, 0))
            wm = B.CFG['watermark']
            x, y = B._corner_xy(wm['corner'], wm['margin'], 0, wm['width'])
            lg = B.logo(wm['width'], force=True)
            B.reveal(tmp, x + lg.width / 2, y + lg.height / 2, wm['width'], t - 3.4, 0.0, style='mask', force=True, signature_under=False)
            g.alpha_composite(vox.alpha_mul(tmp, wm['opacity']))
            return np.asarray(g.convert('RGB'))
        if t < 13.0:
            g = base.copy()
            B.cta_subscribe(g, 64, 900, t - 8.3, 0.0, 4.4, T0=8.3, force=True)
            return np.asarray(g.convert('RGB'))
        if t < 18.5:
            g = ground('paper', t)
            B.cta_comment(g, 120, 340, t - 13.3, 0.0, 4.8, width=900, T0=13.3)
            return np.asarray(g.convert('RGB'))
        vox._SCENE_START = 18.5
        return style.compose(B.outro_scene(t - 18.5, 11.5, force=True), t)

    silent = os.path.join(OUT, 'reel_silent.mp4')
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                          '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', silent], stdin=subprocess.PIPE)
    for f in range(int(D * 30)):
        p.stdin.write(np.ascontiguousarray(frame(f / 30)).tobytes())
    p.stdin.close(); p.wait()
    import sfx
    ev = [(k[0], k[1], k[2], v) for k, v in style.EVENTS.items()]
    trk = sfx.build_track(ev, D, None, level_db=-9)
    wav = os.path.join(OUT, 'reel_sfx.wav')
    sfx.write_wav(wav, trk)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', silent, '-i', wav, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    os.path.join(OUT, 'brand_reel.mp4')], check=True)
    print('reel:', os.path.join(OUT, 'brand_reel.mp4'))
