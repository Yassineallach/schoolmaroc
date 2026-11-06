"""Demo: the same six scenes under each subject palette (palette.py), one sheet per palette.

    python demo_palettes.py <palette> <out.png>          # renders with episode.json {"palette": <palette>}
    python demo_palettes.py --all <out_dir>              # every palette + palettes_overview.png

The palette is read at import time, so each palette renders in its own process with its own
VOX_PROJECT folder holding only an episode.json.
"""
import os, sys, json, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), 'scripts')


def render(name, out):
    sys.path.insert(0, SCRIPTS)
    from PIL import Image, ImageDraw
    import vox
    from vox import W, H
    import style as st
    from style import Shot, tag
    import scenes as S
    import typo as TY
    from typo import Text
    import charts as C
    import palette as PL
    pal = PL.ACTIVE
    st.KICKER_XY = (620, 1000)

    def v_paper(s, t):
        S.env(s, 'paper')
        TY.big_number(s.top, (560, 260), '1987', t, 0.0, label='THE FIRST CHAPTER')
        Text('a story begins', 'caption', size=46).draw(s.hud, (1300, 700), t, 0.0, anim='words', anchor='m')

    def v_dark(s, t):
        S.env(s, 'charcoal', mood='grief')
        S.type_page(s, 'Far from finished.', t, 0.0, role='statement', size=140, anim='words', accent={'finished.': 0.1})

    def v_accent(s, t):
        S.env(s, 'accent', mood='triumph')
        TY.big_number(s.top, (W / 2, 330), '70M', t, 0.0, role='stat', colour=pal.light, label=None, accent_bar=False)
        Text('COPIES IN CIRCULATION', 'label', size=32, colour=pal.light).draw(s.hud, (W / 2, 640), t, 0.0, anim='words', anchor='m')

    def v_archive(s, t):
        S.env(s, 'archive')
        TY.press(s.mid, (220, 260), 'The editors turned it down', t, 0.0, width=1300, dateline='Tokyo · 1982', size=96, sound=False)

    def v_grid(s, t):
        S.env(s, 'grid')
        C.compare(s.mid, (520, 380), [('ENGLISH', 10), ('ALL EDITIONS', 70)], t, 0.0, width=1000, height=80, unit=' M', highlight=1)
        Text('MILLION COPIES', 'label', size=30).draw(s.hud, (520, 280), t, 0.0, anim='words')

    def v_halftone(s, t):
        S.env(s, 'halftone', mood='tense')
        Text('THE STRUGGLE', 'headline', size=150).draw(s.top, (W / 2, 380), t, 0.0, anim='words', anchor='m')
        tag(s.hud, (W / 2, 720), 'A HIGHLIGHT', 52, t, 0.0, bg=S.accent(s), fg=pal.light)

    tiles = []
    for fn in (v_paper, v_dark, v_accent, v_archive, v_grid, v_halftone):
        s = Shot(4.0, 6.0)
        fn(s, 4.0)
        tiles.append(Image.fromarray(st.compose(s, 4.0)).convert('RGB').resize((W // 3, H // 3)))
    sheet = Image.new('RGB', (W, H // 3 * 2 + 70), pal.dark)
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % 3) * (W // 3), 70 + (i // 3) * (H // 3)))
    d = ImageDraw.Draw(sheet)
    d.text((24, 35), f'{pal.name.upper()}  ·  {pal.subject}', font=vox.F_HEAD(30), fill=pal.light, anchor='lm')
    x = W - 24
    for c in (pal.accent_dark, pal.accent2, pal.accent, pal.soft, pal.paper2, pal.paper, pal.ink):
        d.rectangle((x - 46, 14, x, 56), fill=c, outline=pal.light)
        x -= 56
    sheet.save(out)


if __name__ == '__main__':
    if sys.argv[1] == '--all':
        sys.path.insert(0, SCRIPTS)
        import palette as PL
        from PIL import Image
        outdir = sys.argv[2]
        os.makedirs(outdir, exist_ok=True)
        sheets = []
        for name in PL.PALETTES:
            proj = tempfile.mkdtemp()
            json.dump({'palette': name}, open(os.path.join(proj, 'episode.json'), 'w'))
            out = os.path.join(outdir, f'palette_{name}.png')
            subprocess.run([sys.executable, __file__, name, out], check=True, env=dict(os.environ, VOX_PROJECT=proj, _DEMO_PALETTE_CHILD='1'))
            sheets.append(Image.open(out))
        w, h = sheets[0].size
        cols = 2
        rows = (len(sheets) + 1) // 2
        ov = Image.new('RGB', (w * cols // 2, h * rows // 2), (0, 0, 0))
        for i, im in enumerate(sheets):
            ov.paste(im.resize((w // 2, h // 2)), ((i % cols) * w // 2, (i // cols) * h // 2))
        ov.save(os.path.join(outdir, 'palettes_overview.png'))
    elif os.environ.get('_DEMO_PALETTE_CHILD'):
        render(sys.argv[1], sys.argv[2])
    else:                                    # a temporary project, so the named palette is the one loaded
        proj = tempfile.mkdtemp()
        json.dump({'palette': sys.argv[1]}, open(os.path.join(proj, 'episode.json'), 'w'))
        subprocess.run([sys.executable, __file__] + sys.argv[1:], check=True, env=dict(os.environ, VOX_PROJECT=proj, _DEMO_PALETTE_CHILD='1'))
