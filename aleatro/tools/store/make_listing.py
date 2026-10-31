"""Check the store listing text and lay it out for Play Console.

Usage: python3 tools/store/make_listing.py <out dir> [<screenshots dir>]

Reads tools/store/listing/<locale>.txt (sections #title, #short, #full) and
writes, under <out dir>:
  listings.csv              one row per language: locale, title, short, full
  metadata/android/<locale>/title.txt, short_description.txt,
      full_description.txt and images/ (fastlane "supply" layout, which the
      Play Developer API tools import as is)
The screenshots dir is compose.gd's output (<lang>/<set>/NN_name.png).
"""
import csv, glob, os, shutil, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))
LIMITS = {"title": 30, "short": 80, "full": 4000}
# Play locale -> the game's language code (screenshots)
GAME_LANG = {"en-US": "en", "zh-CN": "zh_CN", "ja-JP": "ja", "ko-KR": "ko", "de-DE": "de",
             "fr-FR": "fr", "es-ES": "es", "pt-BR": "pt_BR", "it-IT": "it", "ar": "ar"}
BANNED = ["best", "#1", "top ", "free download", "download now", "install now", "play now", "★", "☆"]


def read(path):
    out, key = {}, None
    for line in open(path, encoding="utf-8").read().split("\n"):
        if line.startswith("#") and line[1:] in LIMITS:
            key = line[1:]
            out[key] = []
        elif key:
            out[key].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def main():
    out = sys.argv[1]
    shots = sys.argv[2] if len(sys.argv) > 2 else None
    rows, bad = [], False
    for loc in GAME_LANG:
        d = read(os.path.join(HERE, "listing", loc + ".txt"))
        for k, lim in LIMITS.items():
            n = len(d[k])
            if n > lim:
                print(f"{loc} {k}: {n} > {lim}")
                bad = True
            if k != "full" and "\n" in d[k]:
                print(f"{loc} {k}: line break")
                bad = True
        low = (d["title"] + " " + d["short"]).lower()
        for b in BANNED:
            if b in low:
                print(f"{loc}: avoid '{b}'")
                bad = True
        print(f"{loc:6} title {len(d['title']):2}/30  short {len(d['short']):2}/80  full {len(d['full']):4}/4000")
        rows.append([loc, d["title"], d["short"], d["full"]])
        m = os.path.join(out, "metadata", "android", loc)
        os.makedirs(m, exist_ok=True)
        for k, name in [("title", "title.txt"), ("short", "short_description.txt"), ("full", "full_description.txt")]:
            open(os.path.join(m, name), "w", encoding="utf-8").write(d[k] + "\n")
        img = os.path.join(m, "images")
        os.makedirs(img, exist_ok=True)
        shutil.copy(os.path.join(PROJ, "tools/play_games/properties/feature_1024x500.png"), os.path.join(img, "featureGraphic.png"))
        shutil.copy(os.path.join(PROJ, "icon.png"), os.path.join(img, "icon.png"))
        if shots:
            lang = GAME_LANG[loc]
            for set_name, folder in [("phone", "phoneScreenshots"), ("phone", "sevenInchScreenshots"), ("tablet", "tenInchScreenshots")]:
                dst = os.path.join(img, folder)
                os.makedirs(dst, exist_ok=True)
                for i, f in enumerate(sorted(glob.glob(os.path.join(shots, lang, set_name, "*.png"))), 1):
                    # JPEG keeps the kit small; Play takes JPEG or 24-bit PNG
                    Image.open(f).convert("RGB").save(os.path.join(dst, f"{i}_{loc}.jpg"), quality=92, subsampling=0)
    with open(os.path.join(out, "listings.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["language", "title", "short_description", "full_description"])
        w.writerows(rows)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
