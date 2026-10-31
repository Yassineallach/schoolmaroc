"""Gentle clean for figures whose costumes are close to the paper colour."""
import sys
from PIL import Image
import numpy as np
from scipy import ndimage as nd
f = sys.argv[1]; bg = np.array([float(x) for x in sys.argv[2].split(',')])
a = np.asarray(Image.open(f).convert('RGBA')).astype(float).copy()
d = np.sqrt(((nd.uniform_filter(a[..., :3], size=(5, 5, 1)) - bg) ** 2).sum(axis=2))
# 1) enclosed paper pockets: near-exact paper colour, sizeable
cand = (d < 26) & (a[..., 3] > 0)
lab, n = nd.label(cand); s = nd.sum(cand, lab, range(1, n + 1))
pock = np.isin(lab, [i + 1 for i, v in enumerate(s) if v > 350])
pock = nd.binary_dilation(pock, iterations=2) & (d < 40)
a[pock, 3] = 0
# 2) thin fringe touching transparency, close to paper only
near = nd.binary_dilation(a[..., 3] < 30, iterations=3)
a[near & (d < 42) & (a[..., 3] > 0), 3] = 0
# 3) keep the single largest figure, drop neighbour slivers
vis = a[..., 3] > 20
lab, n = nd.label(vis); s = nd.sum(vis, lab, range(1, n + 1))
a[lab != (np.argmax(s) + 1), 3] = 0
o = Image.fromarray(a.astype(np.uint8), 'RGBA'); o.crop(o.getchannel('A').getbbox()).save(f)
