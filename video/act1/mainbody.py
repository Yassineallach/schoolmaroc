import sys
from PIL import Image
import numpy as np
from scipy import ndimage as nd
for f in sys.argv[1:]:
    a = np.asarray(Image.open(f)).copy(); vis = a[..., 3] > 20
    core = nd.binary_erosion(vis, iterations=4)
    lab, n = nd.label(core); s = nd.sum(core, lab, range(1, n + 1))
    keep = nd.binary_dilation(lab == (np.argmax(s) + 1), iterations=6) & vis
    a[~keep, 3] = 0
    o = Image.fromarray(a, 'RGBA'); o.crop(o.getchannel('A').getbbox()).save(f)
