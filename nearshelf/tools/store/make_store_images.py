#!/usr/bin/env python3
"""Play Store images from the raw screens StoreScreenshotTest renders.

    ./gradlew :app:testDebugUnitTest --tests '*StoreScreenshotTest*' -Pnearshelf.store=true
    python3 tools/store/make_store_images.py

Writes docs/play-listing/: phone screenshots (1080x1920, captioned) and the feature
graphic (1024x500). Needs Pillow. Fonts are the app's own (res/font).
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "app/build/outputs/store/raw"
OUT = ROOT / "docs/play-listing"
FONT = ROOT / "app/src/main/res/font"
ART = ROOT / "app/src/main/res/drawable-nodpi/home_header.webp"

CREAM, INK, INK2, OXBLOOD = (249, 240, 227), (35, 25, 21), (94, 83, 74), (92, 18, 32)
NIGHT, NIGHT_INK, NIGHT_INK2, ROSE = (23, 19, 17), (240, 232, 223), (173, 164, 155), (235, 176, 174)

SHOTS = [
    ("01_home", "All your libraries.\nOne search.", "eBooks, audiobooks and print, checked at once"),
    ("02_results_ebook", "See who has it,\nand how soon", "The quickest way to borrow comes first"),
    ("03_results_print", "Find a copy on a\nshelf near you", "Branches sorted by distance"),
    ("04_choose_book", "Same title?\nPick the right book", "Results show only the book you mean"),
    ("05_watch_dialog", "Watch only\nwhat you want", "Choose the formats and the libraries"),
    ("06_watchlist", "Know when it's\nyour turn", "A notification when it's free or on a shelf"),
    ("07_libraries", "Your libraries,\nin one place", "Pick a home branch for print copies"),
    ("08_home_dark", "Easy on the eyes,\nday or night", "A full dark theme"),
]


def serif(size, weight=600):
    f = ImageFont.truetype(str(FONT / "newsreader.ttf"), size)
    f.set_variation_by_axes([weight, 72])
    return f


def sans(size, weight=400):
    f = ImageFont.truetype(str(FONT / "instrument_sans.ttf"), size)
    f.set_variation_by_axes([100, weight])
    return f


def rounded(img, radius):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius, fill=255)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def phone_frame(screen, height, dark):
    """The screen inside a slim dark bezel, with a soft warm shadow."""
    w = round(screen.width * height / screen.height)
    s = screen.convert("RGB").resize((w, height), Image.LANCZOS)
    bezel = 14
    body = Image.new("RGB", (w + 2 * bezel, height + 2 * bezel), (28, 22, 19) if not dark else (58, 50, 45))
    body = rounded(body, 64)
    body.alpha_composite(rounded(s, 50), (bezel, bezel))
    pad = 60
    canvas = Image.new("RGBA", (body.width + 2 * pad, body.height + 2 * pad), (0, 0, 0, 0))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([pad, pad + 18, pad + body.width, pad + body.height + 18], 64,
                                             fill=(60, 20, 20, 90 if not dark else 160))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(28)))
    canvas.alpha_composite(body, (pad, pad))
    return canvas, pad


def screenshot(name, title, sub):
    dark = "dark" in name
    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), (NIGHT if dark else CREAM) + (255,))
    d = ImageDraw.Draw(img)
    tf, sf = serif(80), sans(40)
    y = 96
    for line in title.split("\n"):
        tw = d.textlength(line, font=tf)
        d.text(((W - tw) / 2, y), line, font=tf, fill=ROSE if dark else OXBLOOD)
        y += 92
    y += 14
    sw = d.textlength(sub, font=sf)
    d.text(((W - sw) / 2, y), sub, font=sf, fill=NIGHT_INK2 if dark else INK2)
    y += 70
    screen = Image.open(RAW / f"{name}.png")
    frame, pad = phone_frame(screen, H - y - 70, dark)
    img.alpha_composite(frame, ((W - frame.width) // 2, y - pad))
    img.convert("RGB").save(OUT / f"phone_{name}.png", optimize=True)


def feature_graphic():
    W, H = 1024, 500
    img = Image.new("RGBA", (W, H), CREAM + (255,))
    art = Image.open(ART).convert("RGBA")
    art = art.resize((round(art.width * H / art.height), H), Image.LANCZOS)
    fade = Image.new("L", art.size, 255)
    fd = ImageDraw.Draw(fade)
    edge = int(art.width * 0.4)
    for x in range(edge):
        fd.line([(x, 0), (x, H)], fill=int(255 * (x / edge) ** 1.4))
    art.putalpha(fade)
    img.alpha_composite(art, (W - art.width, 0))
    d = ImageDraw.Draw(img)
    x = 64
    d.text((x, 118), "Nearshelf", font=serif(112), fill=OXBLOOD)
    d.text((x, 262), "Your next book,", font=serif(40, 400), fill=INK)
    d.text((x, 310), "on a shelf near you.", font=serif(40, 400), fill=INK)
    d.rounded_rectangle([x, 378, x + 64, 383], 2, fill=OXBLOOD)
    img.convert("RGB").save(OUT / "feature_graphic_1024x500.png", optimize=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, title, sub in SHOTS:
        screenshot(name, title, sub)
    feature_graphic()
    print("Wrote", sorted(p.name for p in OUT.glob("*.png")))
