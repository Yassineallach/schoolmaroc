"""YouTube Shorts cut from the finished film: vertical 1080x1920, the film in the middle on the
episode's paper, a hook headline above, word-synced subtitles below (most Shorts play muted),
the channel's logo and a call to the full video at the foot.

    python SK/scripts/shorts.py out/final/film.mp4 out/shorts shorts.json

shorts.json: [{"name": "s1_echiquier", "start": 5.0, "end": 37.63, "title": "...", "clips": [1, 2]}]
start / end are film times; clips are the narration clips the segment covers (for the subtitles).
Headlines and subtitles come from the narration only (rule 1). The subtitle words are the
transcript's own words placed on Whisper's timing, grouped 3 to 5 words per line.
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw

import vox
import brand as B
from vox import PAL, font

W9, H9 = 1080, 1920
VID_Y, VID_H = 560, 608
FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'fonts')


def _wrap(s, f, width):
    out, cur = [], ''
    for w in s.split(' '):
        nxt = (cur + ' ' + w).strip()
        if f.getlength(nxt) <= width or not cur:
            cur = nxt
        else:
            out.append(cur)
            cur = w
    return out + [cur]


def frame_png(title, path):
    """The still parts of the layout: paper, headline, logo, call to the full video."""
    im = Image.new('RGB', (W9, H9), PAL.light)
    d = ImageDraw.Draw(im)
    f = font('Playfair700.ttf', 76)
    lines = _wrap(title, f, W9 - 140)
    y = VID_Y - 70 - 94 * len(lines)
    for ln in lines:
        d.text((W9 / 2, y), ln, font=f, fill=PAL.ink, anchor='ma')
        y += 94
    d.rectangle((W9 / 2 - 60, VID_Y - 40, W9 / 2 + 60, VID_Y - 34), fill=PAL.accent)
    lg = B.tile(150) if B._logo_path('tile') else B.logo(260)
    if lg is not None:
        im.paste(lg, (int(W9 / 2 - lg.width / 2), 1560), lg)
    cf = font('Inter600.ttf', 40)
    d.text((W9 / 2, 1750), B.TXT.get('short_cta', 'Vidéo complète sur la chaîne'), font=cf, fill=PAL.ink, anchor='ma')
    im.save(path)


def ass_subs(clips, start, end, path):
    """Word-synced subtitles from timing/words.json, offset to the short's own clock."""
    acc, off = 5.0 if os.path.exists(os.path.join(vox.PROJECT, 'act0.py')) else 0.0, {}
    for c in sorted(vox._DUR):
        off[c] = acc
        acc += vox._DUR[c]
    words = [(off[c] + w['s'], off[c] + w['e'], w['w']) for c in clips for w in vox._WORDS[c]]
    words = [(s - start, e - start, t) for s, e, t in words if start - 0.05 <= s < end]
    merged = []                                             # Whisper splits « soixante-quatre », « d'or »: join them back
    for s, e, t in words:
        if merged and (t.startswith('-') or t.startswith("'") or t.startswith('’') or merged[-1][2].endswith(("'", '’'))):
            ps, pe, pt = merged[-1]
            joiner = '' if not t.startswith(("'", '’')) else ''
            merged[-1] = (ps, e, pt + joiner + t.replace("'", '’'))
        elif merged and merged[-1][2] in ('l', 'd', 'n', 's', 'c', 'j', 'm', 'qu', 'L', 'D', 'N', 'S', 'C', 'J', 'M', 'Qu') and t[:1].isalpha():
            ps, pe, pt = merged[-1]
            merged[-1] = (ps, e, pt + '’' + t)
        else:
            merged.append((s, e, t))
    words = merged
    groups, cur = [], []
    for wd in words:
        cur.append(wd)
        if len(cur) >= 5 or (len(cur) >= 3 and wd[2][-1:] in ',.;:?!»'):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)

    def ts(x):
        x = max(0.0, x)
        return f'{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}'
    ink = '&H00{:02X}{:02X}{:02X}'.format(*PAL.ink[::-1])
    acc_c = '&H00{:02X}{:02X}{:02X}'.format(*PAL.accent[::-1])
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W9}
PlayResY: {H9}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Playfair Display,70,{ink},{acc_c},&H00FFFFFF,&H00000000,1,0,0,0,100,100,0,0,1,0,0,8,70,70,{VID_Y + VID_H + 90},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for i, g in enumerate(groups):
        s0 = g[0][0]
        e0 = groups[i + 1][0][0] if i + 1 < len(groups) else g[-1][1] + 0.6
        text = ''
        for j, (s, e, t) in enumerate(g):
            dur = int(max(1, ((g[j + 1][0] if j + 1 < len(g) else e) - s) * 100))
            text += f'{{\\k{dur}}}' + t.replace('{', '').replace('}', '') + ' '
        lines.append(f'Dialogue: 0,{ts(s0)},{ts(e0)},Sub,,0,0,0,,{text.strip()}')
    open(path, 'w', encoding='utf-8').write(head + '\n'.join(lines) + '\n')


def make(film, out_dir, spec):
    os.makedirs(out_dir, exist_ok=True)
    name, start, end = spec['name'], float(spec['start']), float(spec['end'])
    end_pad = end + 0.6
    bg = os.path.join(out_dir, f'{name}_bg.png')
    subs = os.path.join(out_dir, f'{name}.ass')
    frame_png(spec['title'], bg)
    ass_subs(spec['clips'], start, end_pad, subs)
    out = os.path.join(out_dir, f'{name}.mp4')
    fc = (f"[1:v]scale={W9}:{VID_H}[v];[0:v][v]overlay=0:{VID_Y}:shortest=1[c];"
          f"[c]ass='{subs}':fontsdir='{FONTS}'[o];"
          f"[1:a]afade=t=in:d=0.25,afade=t=out:st={end_pad - start - 0.6:.3f}:d=0.6[a]")
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-loop', '1', '-i', bg, '-ss', f'{start:.3f}', '-to', f'{end_pad:.3f}', '-i', film,
                    '-filter_complex', fc, '-map', '[o]', '-map', '[a]', '-t', f'{end_pad - start:.3f}', '-r', '30',
                    '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', out], check=True)
    return out


if __name__ == '__main__':
    film, out_dir, spec_path = sys.argv[1], sys.argv[2], sys.argv[3]
    for spec in json.load(open(spec_path, encoding='utf-8')):
        print(make(film, out_dir, spec))
