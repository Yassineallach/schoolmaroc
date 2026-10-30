import sys
from PIL import Image
import numpy as np
from scipy import ndimage as nd
f, hf, bg = sys.argv[1], float(sys.argv[2]), np.array([float(x) for x in sys.argv[3].split(',')])
a = np.asarray(Image.open(f).convert('RGBA')).astype(float).copy(); h = a.shape[0]
for _ in range(3):
    d = np.sqrt(((a[..., :3] - bg) ** 2).sum(axis=2))
    lum = a[..., :3].mean(axis=2); sat = a[..., :3].max(axis=2) - a[..., :3].min(axis=2)
    near = nd.binary_dilation(a[..., 3] < 30, iterations=5)
    k = near & (a[..., 3] > 0) & ((d < 95) | ((lum > 185) & (sat < 90)))
    k[:int(hf * h)] = False
    a[k, 3] = 0
Image.fromarray(a.astype(np.uint8), 'RGBA').save(f)
