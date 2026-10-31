"""Leftover check for cut-outs. Renders each PNG on magenta (paper leftovers jump out) and on the
dark film background, and flags visible pixels close to paper colour near the outline.

Usage: python check_cutout.py OUT_PREVIEW.png a.png b.png ...
Then LOOK at the preview. The number is a hint, the eye is the test: pale costumes trigger
flags without being paper, and shadowed paper can hide from the numbers.
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd

PAPER_GUESS = np.array([239, 220, 186.])

out, files = sys.argv[1], sys.argv[2:]
tiles = []
for f in files:
    im = Image.open(f).convert('RGBA')
    a = np.asarray(im).astype(float)
    d = np.sqrt(((a[..., :3] - PAPER_GUESS) ** 2).sum(axis=2))
    near = nd.binary_dilation(a[..., 3] < 30, iterations=4)
    flag = near & (a[..., 3] > 60) & (d < 60)
    print(f'{f}: {im.size[0]}x{im.size[1]}  near-outline paper-like px: {int(flag.sum())}')
    for bg in ((255, 0, 255), (42, 30, 26)):
        c = Image.new('RGBA', im.size, bg + (255,))
        c.alpha_composite(im)
        t = c.convert('RGB')
        t.thumbnail((520, 900))
        tiles.append(t)
W = sum(t.width for t in tiles) + 10 * len(tiles)
H = max(t.height for t in tiles)
sheet = Image.new('RGB', (W, H), (255, 255, 255))
x = 0
for t in tiles:
    sheet.paste(t, (x, 0))
    x += t.width + 10
sheet.save(out)
print('preview ->', out)
