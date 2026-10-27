"""Makes the Play Games icons (512x512 PNG, as Play Console asks) from the
game's own art: a pixel-art medal in the achievement's tier colour with the
achievement's emblem inside the circle Play Games crops to.

  python3 tools/play_games/make_icons.py

Writes tools/play_games/icons/{achievements,leaderboards}/<key>.png and a
contact sheet, tools/play_games/icons/sheet.png.
"""
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "assets"
OUT = Path(__file__).resolve().parent / "icons"
SIZE = 512
PX = 4  # one art pixel = 4 icon pixels, like the game's art
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"

# tier by points: bronze, silver, gold, legendary
TIERS = [(20, "c97b3c"), (30, "aeb8c4"), (50, "e0a526"), (1000, "b26cbb")]

# key -> (emblem art under assets/, or "text:..."), points
ACHIEVEMENTS = {
    "climbing": ("blinds/big.png", 10),
    "summit": ("blinds/eclipse.png", 20),
    "victory_lap": ("tags/star.png", 30),
    "red_chip": ("stakes/2.png", 30),
    "black_chip": ("stakes/4.png", 50),
    "gold_chip": ("stakes/8.png", 100),
    "card_sharp": ("decks/crimson.png", 20),
    "clean_sweep": ("vouchers/wastebin.png", 20),
    "nest_egg": ("vouchers/nestbox.png", 30),
    "speedrun": ("tags/haste.png", 50),
    "glass_cannon": ("enhancements/glass.png", 20),
    "royalty": ("charms_pixel/foolking.png", 20),
    "grandmaster": ("vouchers/runebaron.png", 30),
    "collector": ("vouchers/showcase.png", 50),
    "living_legend": ("charms_pixel/bonecrown.png", 20),
    "stargazer": ("packs/celestial.png", 20),
    "fortune_teller": ("packs/arcana.png", 20),
    "seer": ("packs/spectral.png", 20),
    "hex_hunter": ("blinds/abyss.png", 30),
    "slim_pickings": ("decks/bare.png", 20),
    "overstuffed": ("packs/standard_mega.png", 20),
    "no_takebacks": ("tags/dice.png", 30),
    "rule_bender": ("vouchers/rewrite.png", 30),
    "rule_breaker": ("vouchers/antimatter.png", 80),
    "five_figures": ("text:10K", 10),
    "millionaire": ("text:1M", 30),
    "astronomical": ("text:100M", 50),
    "deck_master": ("decks/star.png", 100),
    "five_alive": ("enhancements/wild.png", 20),
    "big_spender": ("vouchers/goldtree.png", 20),
}
LEADERBOARDS = {
    "best_hand": "charms_pixel/jester.png",
    "highest_ante": "blinds/big.png",
    "fastest_win": "tags/haste.png",
    "career_wins": "tags/star.png",
}
LEADERBOARD_COLOUR = "009dff"  # G.C.BLUE


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def tier_colour(points):
    for limit, colour in TIERS:
        if points <= limit:
            return hex_rgb(colour)
    return hex_rgb(TIERS[-1][1])


def medal(colour):
    """The frame on a 128x128 pixel grid: dark field, glow, stepped rings."""
    n = SIZE // PX
    im = Image.new("RGBA", (n, n))
    px = im.load()
    c = (n - 1) / 2
    dark = (29, 42, 51)
    for y in range(n):
        for x in range(n):
            d = math.hypot(x - c, y - c) / (n / 2)
            # soft rays turning round the centre, quantised for the pixel look
            a = math.atan2(y - c, x - c)
            ray = 0.5 + 0.5 * math.cos(a * 8)
            glow = max(0.0, 1.0 - d) ** 1.6
            t = min(1.0, glow * (0.55 + 0.25 * ray))
            t = round(t * 6) / 6
            px[x, y] = mix(dark, colour, t) + (255,)
    draw = ImageDraw.Draw(im)
    light = mix(colour, (255, 255, 255), 0.45)
    shade = mix(colour, (0, 0, 0), 0.45)
    r = n / 2 - 5
    draw.ellipse([c - r - 2, c - r - 2, c + r + 2, c + r + 2], outline=shade, width=3)
    draw.ellipse([c - r, c - r, c + r, c + r], outline=colour, width=3)
    draw.ellipse([c - r + 3, c - r + 3, c + r - 3, c + r - 3], outline=light, width=1)
    # little studs round the ring
    for i in range(12):
        a = i * math.tau / 12
        sx, sy = c + math.cos(a) * (r - 1), c + math.sin(a) * (r - 1)
        draw.rectangle([sx - 1, sy - 1, sx + 1, sy + 1], fill=light)
    return im.resize((SIZE, SIZE), Image.NEAREST)


def emblem_from_art(path, box):
    art = Image.open(ART / path).convert("RGBA")
    bbox = art.getbbox()
    if bbox:
        art = art.crop(bbox)
    scale = min(box / art.width, box / art.height)
    w, h = max(1, round(art.width * scale)), max(1, round(art.height * scale))
    resample = Image.NEAREST if scale >= 1 else Image.LANCZOS
    return art.resize((w, h), resample)


def emblem_text(text, colour):
    font_size = {2: 190, 3: 160, 4: 128}.get(len(text), 120)
    font = ImageFont.truetype(FONT, font_size)
    im = Image.new("RGBA", (SIZE, SIZE))
    d = ImageDraw.Draw(im)
    bb = d.textbbox((0, 0), text, font=font, stroke_width=10)
    x = (SIZE - (bb[2] - bb[0])) / 2 - bb[0]
    y = (SIZE - (bb[3] - bb[1])) / 2 - bb[1]
    d.text((x, y), text, font=font, fill=(255, 255, 255), stroke_width=10, stroke_fill=mix(colour, (0, 0, 0), 0.6))
    return im.crop(im.getbbox())


def compose(colour, emblem):
    im = medal(colour)
    # drop shadow, then the emblem, centred in the inner circle
    x, y = (SIZE - emblem.width) // 2, (SIZE - emblem.height) // 2
    shadow = Image.new("RGBA", im.size)
    sil = Image.new("RGBA", emblem.size, (0, 0, 0, 150))
    shadow.paste(sil, (x + 10, y + 14), emblem)
    im.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(6)))
    im.alpha_composite(emblem, (x, y))
    return im


def main():
    made = []
    for key, (art, points) in ACHIEVEMENTS.items():
        colour = tier_colour(points)
        emblem = emblem_text(art[5:], colour) if art.startswith("text:") else emblem_from_art(art, 300)
        out = OUT / "achievements" / f"{key}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        compose(colour, emblem).convert("RGB").save(out)
        made.append(out)
    for key, art in LEADERBOARDS.items():
        out = OUT / "leaderboards" / f"{key}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        compose(hex_rgb(LEADERBOARD_COLOUR), emblem_from_art(art, 300)).convert("RGB").save(out)
        made.append(out)
    # contact sheet
    cols, cell = 8, 160
    rows = math.ceil(len(made) / cols)
    sheet = Image.new("RGB", (cols * cell, rows * cell), (20, 26, 30))
    for i, p in enumerate(made):
        sheet.paste(Image.open(p).resize((cell - 8, cell - 8), Image.LANCZOS), ((i % cols) * cell + 4, (i // cols) * cell + 4))
    sheet.save(OUT / "sheet.png")
    print(f"{len(made)} icons in {OUT}")


if __name__ == "__main__":
    main()
