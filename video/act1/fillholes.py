import sys
from PIL import Image
import numpy as np
from scipy import ndimage as nd
for f in sys.argv[1:]:
    a = np.asarray(Image.open(f)).copy(); vis = a[..., 3] > 20
    holes = nd.binary_fill_holes(vis) & ~vis
    lab, n = nd.label(holes); s = nd.sum(holes, lab, range(1, n + 1))
    small = np.isin(lab, [i + 1 for i, v in enumerate(s) if v < 2500])
    a[small, 3] = 255
    Image.fromarray(a, 'RGBA').save(f); print(f.split('/')[-1], int(small.sum()))
