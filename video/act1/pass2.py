import sys
from PIL import Image
import numpy as np
from scipy import ndimage as nd
f, hf, bg = sys.argv[1], float(sys.argv[2]), np.array([float(x) for x in sys.argv[3].split(',')])
a = np.asarray(Image.open(f).convert('RGBA')).astype(float).copy(); h = a.shape[0]
for _ in range(3):
    d = np.sqrt(((nd.uniform_filter(a[..., :3], size=(3, 3, 1)) - bg) ** 2).sum(axis=2))
    flag = (d < 82) & (a[..., 3] > 0); flag[:int(hf * h)] = False
    lab, k = nd.label(flag); s = nd.sum(flag, lab, range(1, k + 1))
    flag = np.isin(lab, [i + 1 for i, v in enumerate(s) if v > 6])
    grow = nd.binary_dilation(flag, iterations=2) & (d < 105); grow[:int(hf * h)] = False
    a[grow, 3] = 0
vis = a[..., 3] > 20; l, n = nd.label(nd.binary_dilation(vis, iterations=2)); s = nd.sum(vis, l, range(1, n + 1))
a[l != (np.argmax(s) + 1), 3] = 0
o = Image.fromarray(a.astype(np.uint8), 'RGBA'); o.crop(o.getchannel('A').getbbox()).save(f)
