# Generates the toolbar icons (a magnifier over a bar chart). Run: python3 scripts_icons.py
from PIL import Image, ImageDraw
for size in (16, 32, 48, 128):
    S = size * 4
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=S * 0.22, fill=(47, 91, 211, 255))
    w = S * 0.09
    for i, hgt in enumerate((0.22, 0.36, 0.5)):
        x = S * (0.2 + i * 0.13)
        d.rounded_rectangle([x, S * 0.78 - S * hgt, x + w, S * 0.78], radius=w * 0.3, fill=(255, 255, 255, 235))
    cx, cy, r = S * 0.62, S * 0.4, S * 0.19
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 255), width=int(S * 0.07))
    d.line([cx + r * 0.7, cy + r * 0.7, S * 0.86, S * 0.84], fill=(255, 255, 255, 255), width=int(S * 0.08))
    im.resize((size, size), Image.LANCZOS).save(f'static/icons/icon-{size}.png')
print('ok')
