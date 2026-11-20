"""Preview the whole board under alternative layouts (out/layout_<name>.png)."""
import math, json, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '.')
import board as BD
from vox import W, H

ACTS = [['M01', 'G01', 'G02', 'G03', 'G04', 'G05', 'G06', 'G07', 'G08'],
        ['G09', 'G10', 'G33', 'G11', 'G12', 'M06', 'G13', 'G14', 'G32'],
        ['G15', 'G16', 'G17', 'G38', 'M04', 'G18', 'G19', 'G20'],
        ['G21', 'G22', 'M07', 'G23', 'G24', 'G25', 'G37', 'G26', 'M05', 'M08'],
        ['C01', 'G27', 'G34', 'G35', 'G28', 'G29', 'G36', 'G30', 'M09', 'G31']]
ORDER = [c for a in ACTS for c in a]
DX, DY = 1450, 1050


def islands():
    """Each act its own block (4 per row), blocks on a 3 x 2 grid read like a page."""
    pos, cols = {}, 4
    origins = [(0, 0), (6600, 0), (13200, 0), (0, 4600), (6600, 4600)]
    for (ox, oy), act in zip(origins, ACTS):
        for i, c in enumerate(act):
            pos[c] = (ox + (i % cols) * DX, oy + (i // cols) * DY)
    return pos


def trail():
    """One winding trail, always moving forward, S-bends at the ends of each row."""
    pos, per = {}, 9
    for i, c in enumerate(ORDER):
        r, k = divmod(i, per)
        x = k * DX if r % 2 == 0 else (per - 1 - k) * DX
        y = r * 1350 + 180 * math.sin(k * 0.9 + r)
        pos[c] = (x, y)
    return pos


def spiral():
    """From the goats in the centre, spiralling outward; the last goat comes back to the centre."""
    pos, s, theta = {}, 0.0, 0.0
    a = 1500 / (2 * math.pi)
    for i, c in enumerate(ORDER[:-1]):
        r = max(1, a * theta)
        pos[c] = (r * math.cos(theta) * 1.25, r * math.sin(theta))
        theta += (1550 / max(r, 1300))
    pos['G31'] = (0, -1100)
    return pos


GEO = {   # where each scene happened (lon, lat); scenes with no place sit in the nearest ocean margin
    'M01': (-122, 47), 'G01': (-113, 52), 'G02': (-104, 47), 'G03': (-113, 41), 'G04': (-104, 39), 'G05': (-95, 45),
    'G06': (-150, 28), 'G07': (-158, 15), 'G08': (-142, 15),
    'G09': (-40, 30), 'G10': (-30, 22), 'G33': (-40, 40), 'G11': (-30, 32), 'G12': (-12, 40),
    'M06': (60, 70), 'G13': (105, 30), 'G14': (14, 52), 'G32': (22, 62),
    'G15': (-40, 6), 'G16': (-30, -4), 'G17': (-40, -14), 'G38': (-30, -24),
    'M04': (10, 8), 'G18': (2, 22), 'G19': (-8, 12), 'G20': (12, 42),
    'G21': (24, 36), 'G22': (6, 50), 'M07': (-8, 56), 'G23': (-4, 47), 'G24': (2, 58),
    'G25': (72, 20), 'G37': (60, 10), 'G26': (78, 8), 'M05': (85, 22), 'M08': (70, 30),
    'C01': (-70, -30), 'G27': (-60, -40), 'G34': (-75, -48), 'G35': (-50, -50), 'G28': (-40, -40),
    'G29': (-110, 10), 'G36': (-120, 20), 'G30': (-100, 22), 'M09': (-60, 55), 'G31': (-125, 52),
}


def world_map():
    return {c: (lon * 260, -lat * 330) for c, (lon, lat) in GEO.items()}


def render(pos, name, title, trail_line=False, underlay=None):
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    x0, y0, x1, y1 = min(xs) - 900, min(ys) - 600, max(xs) + 900, max(ys) + 600
    z = min(W / (x1 - x0), (H - 90) / (y1 - y0))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    img = BD.ground(cx, cy, z)
    def S(p): return ((p[0] - cx) * z + W / 2, (p[1] - cy) * z + H / 2 + 45)
    d = ImageDraw.Draw(img)
    if underlay:
        underlay(d, S, z)
    if trail_line:
        pts = [S(pos[c]) for c in ORDER]
        for a, b in zip(pts[:-1], pts[1:]):
            n = int(math.hypot(b[0] - a[0], b[1] - a[1]) / 8)
            for k in range(0, n, 2):
                d.line([(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n),
                        (a[0] + (b[0] - a[0]) * (k + 1) / n, a[1] + (b[1] - a[1]) * (k + 1) / n)], fill=(90, 70, 50), width=2)
    for c in ORDER:
        lines = BD.Entry(c, c).d.layers(BD.SIZE.get(c, 1.0) * BD.SCALE)[0]
        t = lines.resize((max(1, int(lines.width * z)), max(1, int(lines.height * z))), Image.LANCZOS)
        sx, sy = S(pos[c])
        img.alpha_composite(t, (int(sx - t.width / 2), int(sy - t.height / 2)))
    f = ImageFont.truetype(os.path.join(os.path.dirname(BD.__file__), '..', '..', '.claude', 'skills', 'paper-explainer-video', 'assets', 'fonts', 'ArchivoBlack.ttf'), 40)
    d.text((40, 24), title, font=f, fill=(36, 24, 15))
    img.convert('RGB').save(f'out/layout_{name}.png')
    print(name, round(z, 3))


def world_underlay(d, S, z):
    geo = json.load(open('../../.claude/skills/paper-explainer-video/assets/geo/countries_110m.json'))
    for c in geo:
        for poly in c['polys']:
            for ring in poly[:1]:
                d.line([S((x * 260, -y * 330)) for x, y in ring], fill=(150, 125, 95), width=1)


if __name__ == '__main__' and len(sys.argv) == 1:
    render(islands(), 'A_islands', 'A · Îlots par chapitre')
    render(trail(), 'B_trail', 'B · Un sentier qui serpente', trail_line=True)
    render(spiral(), 'C_spiral', 'C · Une spirale', trail_line=True)
    render(world_map(), 'D_world', 'D · Sur la carte du monde', underlay=world_underlay)


def mindmap():
    """E: salt at the centre (the NaCl crystals); the five chapters sit around it like a constellation,
    each a small block read left to right, clockwise from the top left."""
    pos = {}
    centres = [(-6200, -3300), (0, -3600), (6200, -3300), (6200, 3300), (-6200, 3300)]
    for (ox, oy), act in zip(centres, ACTS):
        cols = 4 if len(act) > 9 else 3
        rows = (len(act) + cols - 1) // cols
        for i, c in enumerate(act):
            pos[c] = (ox + (i % cols - (cols - 1) / 2) * DX, oy + (i // cols - (rows - 1) / 2) * DY)
    pos['G06'] = (0, 0)
    return pos


def staircase():
    """F: a staircase going down to the right: every row reads left to right, each new act one step lower."""
    pos = {}
    for a_i, act in enumerate(ACTS):
        for i, c in enumerate(act):
            pos[c] = (a_i * 2900 + i * DX, a_i * 1500 + (i % 2) * 260)
    return pos


def notebook():
    """G: like lines in a notebook: each act is one line, always read left to right, the next act starts on the line below."""
    pos = {}
    for a_i, act in enumerate(ACTS):
        for i, c in enumerate(act):
            pos[c] = (i * DX, a_i * 1300)
    return pos


def river():
    """H: a river of time across the board: the story flows along it, each act a block growing above or below it."""
    pos, x = {}, 0
    for a_i, act in enumerate(ACTS):
        sgn = -1 if a_i % 2 == 0 else 1
        cols = 4
        for i, c in enumerate(act):
            col, row = i % cols, i // cols
            pos[c] = (x + col * DX, sgn * (800 + row * DY))
        x += cols * DX * 0.62
    return pos


def river_underlay(pos):
    xs = [p[0] for p in pos.values()]
    def draw(d, S, z):
        a, b = S((min(xs) - 600, 0)), S((max(xs) + 600, 0))
        for k in range(0, 3):
            y = a[1] + (k - 1) * 6
            d.line([(a[0], y), (b[0], y)], fill=(90, 70, 50), width=2)
    return draw


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'more':
    render(mindmap(), 'E_mindmap', 'E · Carte mentale autour du sel', trail_line=True)
    render(staircase(), 'F_stairs', 'F · Un escalier qui descend', trail_line=True)
    render(notebook(), 'G_notebook', 'G · Les lignes d’un carnet', trail_line=True)
    pr = river()
    render(pr, 'H_river', 'H · Le fleuve du temps', underlay=river_underlay(pr))


def organic(seed, spread=1.0, sizes=True):
    """A random, organic board: each drawing lands near the previous one in a random direction
    (any angle), at a random distance, never overlapping; acts drift as loose clusters. Returns
    positions and a per-drawing size, so the board looks hand-placed rather than gridded."""
    r = np.random.default_rng(seed)
    pos, size = {}, {}
    boxes = []
    heading = r.uniform(0, 2 * math.pi)
    x, y = 0.0, 0.0
    for a_i, act in enumerate(ACTS):
        if a_i:
            heading += r.uniform(-1.6, 1.6)                     # each act sets off in a new direction
        for i, c in enumerate(act):
            s = r.uniform(0.75, 1.2) if sizes else 1.0
            w, h = 1300 * s, 800 * s
            for _ in range(400):
                ang = heading + r.normal(0, 0.9)
                d = r.uniform(1100, 1700) * spread * (0.5 + s / 2)
                nx, ny = (x + math.cos(ang) * d, y + math.sin(ang) * d) if pos else (0.0, 0.0)
                if all(abs(nx - bx) > (w + bw) / 2 + 60 or abs(ny - by) > (h + bh) / 2 + 60 for bx, by, bw, bh in boxes):
                    break
                heading += r.uniform(-0.4, 0.4)
            x, y = nx, ny
            pos[c], size[c] = (x, y), s
            boxes.append((x, y, w, h))
    return pos, size


def render_sized(pos, size, name, title):
    old = dict(BD.SIZE)
    for c, s in size.items():
        BD.SIZE[c] = old.get(c, 1.0) * s
    try:
        render(pos, name, title, trail_line=True)
    finally:
        BD.SIZE.clear(); BD.SIZE.update(old)


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'random':
    seeds = [int(x) for x in sys.argv[2:]] or [3, 17, 42, 1930]
    for k, sd in enumerate(seeds):
        p, s = organic(sd)
        render_sized(p, s, f'R{k + 1}_{sd}', f'R{k + 1} · Aléatoire (graine {sd})')


def organic2(seed, cols=10, rows=6):
    """Random but compact: the board is a loose field of slots filling a 16:9 page; the pen wanders
    from slot to a random free neighbouring slot (any direction), jumping to the nearest free slot
    when cornered. Slots are jittered and drawings vary in size, so it looks hand-placed."""
    r = np.random.default_rng(seed)
    sx, sy = 1500, 1080
    slots = {(i, j): (i * sx + r.uniform(-260, 260), j * sy + r.uniform(-200, 200)) for i in range(cols) for j in range(rows)}
    free = set(slots)
    cur = (int(r.integers(0, cols)), int(r.integers(0, rows)))
    pos, size = {}, {}
    for c in ORDER:
        pos[c] = slots[cur]; size[c] = r.uniform(0.8, 1.15)
        free.discard(cur)
        if not free:
            break
        nb = [(cur[0] + a, cur[1] + b) for a in (-1, 0, 1) for b in (-1, 0, 1) if (a or b) and (cur[0] + a, cur[1] + b) in free]
        if nb:
            # prefer neighbours with few free neighbours themselves, so the walk does not strand empty pockets
            deg = [sum((n[0] + a, n[1] + b) in free for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b) for n in nb]
            m = min(deg)
            cand = [n for n, d in zip(nb, deg) if d <= m + 1]
            cur = cand[int(r.integers(0, len(cand)))]
        else:
            cur = min(free, key=lambda n: (n[0] - cur[0]) ** 2 + (n[1] - cur[1]) ** 2)
    return pos, size


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'random2':
    seeds = [int(x) for x in sys.argv[2:]] or [3, 17, 42, 1930]
    for k, sd in enumerate(seeds):
        p, s = organic2(sd, cols=9, rows=6)
        render_sized(p, s, f'S{k + 1}_{sd}', f'{"ABCDEF"[k]} · Aléatoire (graine {sd})')
