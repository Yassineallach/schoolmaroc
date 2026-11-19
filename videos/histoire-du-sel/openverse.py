"""Image search through Openverse (indexes Wikimedia Commons, Flickr, museums) for when the
Wikimedia APIs answer 429 to this machine.

    python openverse.py search sources.json out/ov [SLOT ...]   contact sheet per slot + out/ov/candidates.json
    python openverse.py get SLOT N                              download candidate N of SLOT to assets/SLOT.jpg

Only public domain, CC0, CC BY and CC BY-SA. Credits go to assets/credits.json like commons.py.
"""
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from PIL import Image, ImageDraw, ImageFont

UA = {'User-Agent': 'paper-explainer/1.0'}
LIC = 'cc0,pdm,by,by-sa'
PROJECT = os.environ.get('VOX_PROJECT', os.getcwd())


def _get(url, tries=4):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(3 + 4 * k)


def search(q, n=8):
    url = 'https://api.openverse.org/v1/images/?' + urllib.parse.urlencode(
        {'q': q, 'license': LIC, 'page_size': n, 'mature': 'false'})
    out = []
    for r in json.loads(_get(url))['results']:
        out.append({'id': r['id'], 'title': r['title'], 'url': r['url'], 'page': r['foreign_landing_url'],
                    'author': r.get('creator') or '', 'licence': f"{r['license'].upper()} {r.get('license_version') or ''}".strip(),
                    'source': r.get('source'), 'w': r.get('width'), 'h': r.get('height'),
                    'thumb': f"https://api.openverse.org/v1/images/{r['id']}/thumb/"})
    return out


def sheet(slot, cands, path):
    cols, tw, th = 4, 400, 300
    rows = (len(cands) + cols - 1) // cols
    im = Image.new('RGB', (cols * (tw + 20) + 20, rows * (th + 70) + 60), (238, 230, 218))
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype('DejaVuSans.ttf', 15)
        fb = ImageFont.truetype('DejaVuSans-Bold.ttf', 26)
    except OSError:
        f = fb = ImageFont.load_default()
    d.text((12, 10), slot, font=fb, fill=(40, 30, 20))
    for i, c in enumerate(cands):
        x, y = 20 + (i % cols) * (tw + 20), 50 + (i // cols) * (th + 70)
        try:
            t = Image.open(io.BytesIO(_get(c['thumb']))).convert('RGB')
            t.thumbnail((tw, th))
            im.paste(t, (x, y))
        except Exception:  # noqa: BLE001
            d.rectangle((x, y, x + tw, y + th), outline=(120, 0, 0))
        d.text((x, y + th + 4), f"{i + 1}. {c['title'][:44]}", font=f, fill=(30, 20, 10))
        d.text((x, y + th + 24), f"{c['licence']} · {c['source']} · {c['w']}x{c['h']}", font=f, fill=(90, 70, 50))
    im.save(path, quality=88)


def cmd_search(src, out_dir, only=()):
    os.makedirs(out_dir, exist_ok=True)
    cpath = os.path.join(out_dir, 'candidates.json')
    allc = json.load(open(cpath)) if os.path.exists(cpath) else {}
    for slot, queries in json.load(open(src)).items():
        if only and slot not in only:
            continue
        seen, cands = set(), []
        for q in queries:
            for c in search(q):
                if c['id'] not in seen:
                    seen.add(c['id']); cands.append(c)
        cands = cands[:16]
        allc[slot] = cands
        json.dump(allc, open(cpath, 'w'), ensure_ascii=False, indent=1)
        sheet(slot, cands, os.path.join(out_dir, f'{slot}.jpg'))
        print(slot, len(cands), flush=True)


def cmd_get(slot, n, out_dir='out/ov', width=2400):
    c = json.load(open(os.path.join(out_dir, 'candidates.json')))[slot][int(n) - 1]
    im = Image.open(io.BytesIO(_get(c['url']))).convert('RGB')
    if max(im.size) > width:
        im.thumbnail((width, width), Image.LANCZOS)
    os.makedirs(os.path.join(PROJECT, 'assets'), exist_ok=True)
    out = os.path.join(PROJECT, 'assets', f'{slot}.jpg')
    im.save(out, quality=95)
    apath = os.path.join(PROJECT, 'assets', 'credits.json')
    cr = json.load(open(apath)) if os.path.exists(apath) else {}
    cr[slot] = {'title': c['title'], 'author': c['author'], 'credit': c['author'], 'licence': c['licence'], 'page': c['page']}
    json.dump(cr, open(apath, 'w'), ensure_ascii=False, indent=1)
    print(f'{out}: {im.size[0]}x{im.size[1]}  {c["licence"]}  {c["page"]}')


if __name__ == '__main__':
    if sys.argv[1] == 'search':
        cmd_search(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif sys.argv[1] == 'get':
        cmd_get(sys.argv[2], sys.argv[3])
