import sys
from PIL import Image
import numpy as np
from scipy import ndimage as nd
f, it = sys.argv[1], int(sys.argv[2])
a = np.asarray(Image.open(f)).copy(); vis = a[..., 3] > 20
pad = it + 2
v = np.pad(vis, pad)
closed = nd.binary_closing(v, structure=np.ones((3, 3)), iterations=it)[pad:-pad, pad:-pad]
closed = nd.binary_fill_holes(closed)
add = closed & ~vis
a[add, 3] = 255
Image.fromarray(a, 'RGBA').save(f); print(f.split('/')[-1], int(add.sum()))
