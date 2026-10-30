"""Robust cut-out: removes paper by colour distance to the sheet's own paper colour.
Border-connected paper always goes; enclosed paper patches go everywhere below the head zone
(head_frac of the height), where eye whites and lamp glass are protected."""
import sys
from PIL import Image, ImageFilter
import numpy as np
from scipy import ndimage as nd

def cut(src, dst, head_frac, tol=62):
    im = Image.open(src).convert('RGB'); a = np.asarray(im).astype(float); h, w = a.shape[:2]
    border = np.concatenate([a[:4].reshape(-1, 3), a[-4:].reshape(-1, 3), a[:, :4].reshape(-1, 3), a[:, -4:].reshape(-1, 3)])
    bgc = np.median(border, axis=0)
    sm = nd.uniform_filter(a, size=(3, 3, 1))
    dist = np.sqrt(((sm - bgc) ** 2).sum(axis=2))
    cand = dist < tol
    lab, n = nd.label(cand)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    sizes = nd.sum(cand, lab, range(1, n + 1))
    cy = nd.center_of_mass(cand, lab, range(1, n + 1))
    keep = np.zeros(n + 1, bool)
    for i in range(1, n + 1):
        if i in edge or (sizes[i - 1] > 25 and cy[i - 1][0] > head_frac * h):
            keep[i] = True
    bg = keep[lab]
    fg = nd.binary_opening(~bg, iterations=1)
    l2, n2 = nd.label(fg); s2 = nd.sum(fg, l2, range(1, n2 + 1))
    fg = np.isin(l2, [i + 1 for i, s in enumerate(s2) if s >= 0.02 * s2.max()])
    core = nd.binary_erosion(fg, iterations=2)
    band = fg & ~core
    d_raw = np.sqrt(((a - bgc) ** 2).sum(axis=2))
    alpha = core.astype(float)
    alpha[band] = np.clip((d_raw[band] - 45) / 70, 0, 1)
    _, idx = nd.distance_transform_edt(~core, return_indices=True)
    rgb = np.where(band[..., None], a[idx[0], idx[1]], a)
    a8 = np.array(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)))
    out = Image.fromarray(np.dstack([rgb.astype(np.uint8), a8]), 'RGBA')
    out.crop(Image.fromarray(a8).getbbox()).save(dst)
    return bgc

if __name__ == '__main__':
    src, dst, hf = sys.argv[1], sys.argv[2], float(sys.argv[3])
    print(dst.split('/')[-1], cut(src, dst, hf).round())
