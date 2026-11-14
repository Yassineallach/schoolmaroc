"""Export an act to a Remotion project, so the act can be rebuilt (or finished) in React with the
same material as the Python engine: same grounds, fonts, logo, word timing and soundtrack.

    python SK/scripts/remotion_export.py 1 remotion/public/a1 [--film out/final/film.mp4]

Writes into the target folder:
  bg_<env>.jpg      every scene environment of the episode, rendered by scenes.py (the identity's grounds)
  *.ttf, logo.svg   the film's typefaces and the official logo
  act.m4a           the act's soundtrack: cut from the finished film when --film is given (voice,
                    effects and music exactly as approved), else the mastered narration alone
  words.json        {"clips": {"1": [{"w","s","e"}...]}, "offset": {"1": 0.0, ...}, "end": s}
                    word timing in act-local seconds; read it with templates/remotion/cues.ts
  data.json         the palette and the act's shot starts (seconds)
Images specific to the act (drawings, prints) are exported by the act's own code
(e.g. act1.PAINT_CARD.save(...)), since they are built there.
"""
import argparse
import importlib
import json
import os
import shutil
import subprocess

import vox
import style
import scenes as S
import brand as B

ap = argparse.ArgumentParser()
ap.add_argument('act', type=int)
ap.add_argument('out')
ap.add_argument('--film', default=None, help='the finished film; the act is cut from it (soundtrack with effects and music)')
a = ap.parse_args()

os.makedirs(a.out, exist_ok=True)
act = importlib.import_module(f'act{a.act}')

for env in S.ENVS:
    s = style.Shot(0, 5)
    S.env(s, env)
    try:
        from PIL import Image
        Image.fromarray(style.compose(s, 10.0)).save(os.path.join(a.out, f'bg_{env}.jpg'), quality=92)
    except Exception as e:
        print('skip env', env, e)

fonts = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'fonts')
for f in os.listdir(fonts):
    if f.endswith('.ttf'):
        shutil.copy(os.path.join(fonts, f), os.path.join(a.out, f))
if B.OFFICIAL:
    shutil.copy(B.OFFICIAL, os.path.join(a.out, 'logo.svg'))

# act start in the film: the intro, then every earlier act
start = 0.0
if a.film:
    if os.path.exists(os.path.join(vox.PROJECT, 'act0.py')):
        start += B.intro_seconds() if hasattr(B, 'intro_seconds') else 5.0
    for n in range(1, a.act):
        start += importlib.import_module(f'act{n}').END
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', f'{start:.3f}', '-t', f'{act.END:.3f}', '-i', a.film, '-vn',
                    '-c:a', 'aac', '-b:a', '256k', os.path.join(a.out, 'act.m4a')], check=True)
else:
    vox.master_audio(act.CLIPS, os.path.join(a.out, 'act.wav'))

offset, acc = {}, 0.0
for c in act.CLIPS:
    offset[str(c)] = round(acc, 3)
    acc += vox._DUR[c]
json.dump({'clips': {str(c): vox._WORDS[c] for c in act.CLIPS}, 'offset': offset, 'end': round(act.END, 3)},
          open(os.path.join(a.out, 'words.json'), 'w'), ensure_ascii=False)
pal = {k: '#%02x%02x%02x' % getattr(vox.PAL, k) for k in ('ink', 'ink2', 'muted', 'accent', 'accent2', 'light', 'dark', 'paper', 'solid', 'soft')}
json.dump({'pal': pal, 'shots': [round(s[0], 3) for s in act.SHOTS], 'start_in_film': round(start, 3)},
          open(os.path.join(a.out, 'data.json'), 'w'), indent=1)
print('exported act', a.act, 'to', a.out, f'({act.END:.2f} s, starts at {start:.2f} s in the film)')
