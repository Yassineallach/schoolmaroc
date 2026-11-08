"""Find real, freely licensed images on Wikimedia Commons for a storyboard, and keep the credits.

    python commons.py search sources.json out/commons        # contact sheet per slot (+ candidates.json)
    python commons.py get P02 "File:Name.jpg" [--w 2400]    # download into assets/ + credits.json
    python commons.py links [picks.json]                     # table of picks: page + direct file link
    python commons.py credit P02 "File:Name.jpg"             # record the credit of a file the user saved

sources.json: {"P02": ["Schöningen Speer im Sediment", "Schöningen spear"], ...}  (queries per slot)

Only files whose licence is public domain, CC0, CC BY or CC BY-SA are kept. Every download is
recorded in assets/credits.json (title, author, licence, URL) so the film's end card and video
description can credit them. Never use a photo of a real person's face without the user's OK.
"""
import json, os, re, sys, io, time, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFont

API = 'https://commons.wikimedia.org/w/api.php'
UA = {'User-Agent': os.environ.get('VOX_UA', 'paper-explainer-video/1.0 (https://github.com/yassineallach/schoolmaroc; educational video) python-urllib')}
OK = re.compile(r'^(public domain|pd|cc0|cc[ -]by(-sa)?([ -]\d\.\d)?)', re.I)
PROJECT = os.environ.get('VOX_PROJECT', os.getcwd())


def _get(params):
    url = API + '?' + urllib.parse.urlencode({**params, 'format': 'json'})
    time.sleep(1.5)
    for k in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.load(r)
        except Exception as e:
            ra = getattr(e, 'headers', None) and e.headers.get('Retry-After')
            wait = max(float(ra or 0) * 2, min(120, 10 * 2 ** k))
            print(f'[commons] {getattr(e, "code", e)}; retry in {wait:.0f}s', flush=True)
            time.sleep(wait)
    raise RuntimeError(url)


def _fetch(url):
    time.sleep(1.5)
    for k in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception as e:
            print(f'[commons] {getattr(e, "code", e)}; retry in {5 * 2 ** k}s', flush=True)
            time.sleep(min(120, 10 * 2 ** k))
    raise RuntimeError(url)


def _clean(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html or '')).strip()


def info(titles, width=400):
    d = _get({'action': 'query', 'titles': '|'.join(titles), 'prop': 'imageinfo',
              'iiprop': 'url|size|mime|extmetadata', 'iiurlwidth': width})
    out = []
    for p in d.get('query', {}).get('pages', {}).values():
        if 'imageinfo' not in p:
            continue
        ii = p['imageinfo'][0]
        m = ii.get('extmetadata', {})
        lic = _clean(m.get('LicenseShortName', {}).get('value', ''))
        out.append(dict(title=p['title'], thumb=ii.get('thumburl'), url=ii['url'], page=ii.get('descriptionurl'),
                        w=ii.get('width'), h=ii.get('height'), mime=ii.get('mime'), licence=lic,
                        author=_clean(m.get('Artist', {}).get('value', ''))[:120],
                        credit=_clean(m.get('Credit', {}).get('value', ''))[:160],
                        desc=_clean(m.get('ImageDescription', {}).get('value', ''))[:200],
                        free=bool(OK.match(lic))))
    return out


def search(query, n=10):
    d = _get({'action': 'query', 'list': 'search', 'srsearch': query + ' filetype:bitmap', 'srnamespace': 6, 'srlimit': n})
    return [r['title'] for r in d.get('query', {}).get('search', [])]


def sheet(slot, cands, path):
    cols, tw, th = 4, 420, 300
    rows = max(1, (len(cands) + cols - 1) // cols)
    c = Image.new('RGB', (cols * tw, rows * (th + 60) + 50), (238, 232, 218))
    d = ImageDraw.Draw(c)
    try:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
        fb = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
    except OSError:
        f = fb = ImageFont.load_default()
    d.text((12, 12), slot, font=fb, fill=(40, 30, 20))
    for i, cd in enumerate(cands):
        x, y = (i % cols) * tw, 50 + (i // cols) * (th + 60)
        try:
            im = Image.open(io.BytesIO(_fetch(cd['thumb']))).convert('RGB')
            im.thumbnail((tw - 16, th - 8))
            c.paste(im, (x + 8, y + 4))
        except Exception:
            d.text((x + 10, y + 100), 'no preview', font=f, fill=(120, 0, 0))
        d.text((x + 8, y + th), f"{i + 1}. {cd['title'][5:60]}", font=f, fill=(30, 20, 10))
        d.text((x + 8, y + th + 20), f"{cd['licence']} · {cd['w']}x{cd['h']}", font=f, fill=(90, 70, 50))
    c.save(path)


def search_info(query, n=12, width=400):
    d = _get({'action': 'query', 'generator': 'search', 'gsrsearch': query + ' filetype:bitmap', 'gsrnamespace': 6,
              'gsrlimit': n, 'prop': 'imageinfo', 'iiprop': 'url|size|mime|extmetadata', 'iiurlwidth': width})
    pages = sorted(d.get('query', {}).get('pages', {}).values(), key=lambda p: p.get('index', 0))
    out = []
    for p in pages:
        if 'imageinfo' not in p:
            continue
        ii = p['imageinfo'][0]
        m = ii.get('extmetadata', {})
        lic = _clean(m.get('LicenseShortName', {}).get('value', ''))
        out.append(dict(title=p['title'], thumb=ii.get('thumburl'), url=ii['url'], page=ii.get('descriptionurl'),
                        w=ii.get('width'), h=ii.get('height'), mime=ii.get('mime'), licence=lic,
                        author=_clean(m.get('Artist', {}).get('value', ''))[:120],
                        credit=_clean(m.get('Credit', {}).get('value', ''))[:160],
                        desc=_clean(m.get('ImageDescription', {}).get('value', ''))[:200],
                        free=bool(OK.match(lic))))
    return out


def cmd_search(src, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    plan = json.load(open(src, encoding='utf-8'))
    old = os.path.join(out_dir, 'candidates.json')
    allc = json.load(open(old, encoding='utf-8')) if os.path.exists(old) else {}
    for slot, queries in plan.items():
        if slot in allc:
            continue
        cands, seen = [], set()
        time.sleep(float(os.environ.get('VOX_COMMONS_PAUSE', 20)))
        for q in queries:
            try:
                found = search_info(q)
            except RuntimeError:
                print(f'[commons] gave up on query {q!r}', flush=True)
                found = []
            for cd in found:
                if cd['title'] not in seen:
                    seen.add(cd['title']); cands.append(cd)
        cands = [cd for cd in cands if cd['free'] and cd['mime'] in ('image/jpeg', 'image/png', 'image/tiff', 'image/webp')
                 and min(cd['w'] or 0, cd['h'] or 0) >= 700][:12]
        allc[slot] = cands
        sheet(slot, cands, os.path.join(out_dir, f'{slot}.jpg'))
        print(slot, len(cands), 'candidates', flush=True)
        json.dump(allc, open(old, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(allc, open(os.path.join(out_dir, 'candidates.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def cmd_get(slot, title, width=2400):
    cd = info([title], width)[0]
    if not cd['free']:
        sys.exit(f'not a free licence: {cd["licence"]}')
    data = _fetch(cd['thumb'] if (cd['w'] or 0) > width else cd['url'])
    im = Image.open(io.BytesIO(data)).convert('RGB')
    os.makedirs(os.path.join(PROJECT, 'assets'), exist_ok=True)
    out = os.path.join(PROJECT, 'assets', f'{slot}.jpg')
    im.save(out, quality=95)
    cpath = os.path.join(PROJECT, 'assets', 'credits.json')
    credits = json.load(open(cpath, encoding='utf-8')) if os.path.exists(cpath) else {}
    credits[slot] = {k: cd[k] for k in ('title', 'author', 'credit', 'licence', 'page')}
    json.dump(credits, open(cpath, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{out}: {im.size[0]}x{im.size[1]}  {cd["licence"]}  {cd["author"][:60]}')


def cmd_links(picks_path='picks.json'):
    """Print the picks as a table the user can download from by hand (when Commons rate-limits
    this machine): code to save as, the file page, and the direct link to the original file."""
    picks = json.load(open(picks_path, encoding='utf-8'))
    cpath = os.path.join(PROJECT, 'out', 'commons', 'candidates.json')
    known = {}
    if os.path.exists(cpath):
        known = {x['title']: x for v in json.load(open(cpath, encoding='utf-8')).values() for x in v}
    have = set(os.listdir(os.path.join(PROJECT, 'assets'))) if os.path.isdir(os.path.join(PROJECT, 'assets')) else set()
    print('| Save as | File page | Direct file | Licence |\n|---|---|---|---|')
    for code, title in picks.items():
        if any(h.startswith(code + '.') for h in have):
            continue
        x = known.get(title)
        page = 'https://commons.wikimedia.org/wiki/' + urllib.parse.quote(title.replace(' ', '_'))
        direct = x['url'].split('?')[0] if x else ''
        print(f"| `{code}.jpg` | [page]({page}) | [file]({direct}) | {x['licence'] if x else '?'} |")


def cmd_credit(slot, title):
    """Record the credit for a file the user downloaded by hand (no image download here)."""
    cpath = os.path.join(PROJECT, 'out', 'commons', 'candidates.json')
    known = {x['title']: x for v in json.load(open(cpath, encoding='utf-8')).values() for x in v} if os.path.exists(cpath) else {}
    cd = known.get(title) or info([title])[0]
    apath = os.path.join(PROJECT, 'assets', 'credits.json')
    credits = json.load(open(apath, encoding='utf-8')) if os.path.exists(apath) else {}
    credits[slot] = {k: cd[k] for k in ('title', 'author', 'credit', 'licence', 'page')}
    json.dump(credits, open(apath, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(slot, cd['licence'], cd['author'][:60])


if __name__ == '__main__':
    if sys.argv[1] == 'search':
        cmd_search(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'links':
        cmd_links(sys.argv[2] if len(sys.argv) > 2 else 'picks.json')
    elif sys.argv[1] == 'credit':
        cmd_credit(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'get':
        w = int(sys.argv[sys.argv.index('--w') + 1]) if '--w' in sys.argv else 2400
        cmd_get(sys.argv[2], sys.argv[3], w)
