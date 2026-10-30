"""Strict leftover check: any visible pixel within colour distance 70 of the paper colour,
outside the protected head zone, is flagged. Writes a magenta preview."""
import sys
from PIL import Image
import numpy as np
from scipy import ndimage as nd
out = sys.argv[1]; items = sys.argv[2:]
tiles = []
for it in items:
    f, hf, bg = it.split(':'); hf = float(hf); bgc = np.array([float(x) for x in bg.split(',')])
    im = Image.open(f).convert('RGBA'); a = np.asarray(im).astype(float); h = a.shape[0]
    d = np.sqrt(((nd.uniform_filter(a[..., :3], size=(3, 3, 1)) - bgc) ** 2).sum(axis=2))
    flag = (d < 70) & (a[..., 3] > 80); flag[:int(hf * h)] = False
    lab, k = nd.label(flag); s = nd.sum(flag, lab, range(1, k + 1))
    flag = np.isin(lab, [i + 1 for i, v in enumerate(s) if v > 6])
    print(f.split('/')[-1], 'flagged', int(flag.sum()))
    c = Image.new('RGBA', im.size, (40, 40, 40, 255)); c.alpha_composite(im); arr = np.array(c)
    arr[nd.binary_dilation(flag, iterations=3)] = [255, 0, 255, 255]
    t = Image.fromarray(arr); t.thumbnail((520, 900)); tiles.append(t)
W = sum(t.width for t in tiles) + 10 * len(tiles); H = max(t.height for t in tiles)
c = Image.new('RGB', (W, H), (255, 255, 255)); x = 0
for t in tiles: c.paste(t.convert('RGB'), (x, 0)); x += t.width + 10
c.save(out)
