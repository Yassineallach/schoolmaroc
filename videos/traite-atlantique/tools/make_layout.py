"""The board's layout for L'histoire de l'épée: a compact random walk (the arrangement the user
chose for L'histoire du sel): every next drawing sits in a free cell next to the previous one, in
any direction, never back over earlier work; cells jittered by hand; then spread x1.4.
    python tools/make_layout.py   ->  layout.json
"""
import json, random
ORDER = ['G01', 'G02', 'G03', 'G04', 'G05', 'G06', 'G07',
         'G08', 'G09', 'M01', 'G10', 'G11', 'G12', 'C01', 'G13', 'M02', 'G14', 'G15', 'G16',
         'G17', 'G18', 'G19', 'G20', 'G21', 'G22', 'G23', 'G24', 'G25', 'G26', 'G27', 'G28', 'G29',
         'G30', 'M03', 'G31', 'G32', 'G33', 'G34', 'G35', 'G36', 'G37', 'G38', 'G39',
         'G40', 'G41', 'G42', 'M04', 'G43', 'G44', 'G45']
SX, SY, JX, JY, SPREAD = 1380, 880, 70, 50, 1.4
COLS, ROWS = 10, 6
NB = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def walk(seed):
    rnd = random.Random(seed)
    def go(path, used):
        if len(path) == len(ORDER):
            return path
        x, y = path[-1]
        opts = [(x + dx, y + dy) for dx, dy in NB if 0 <= x + dx < COLS and 0 <= y + dy < ROWS and (x + dx, y + dy) not in used]
        # prefer straight steps and cells with free neighbours left (no dead ends)
        rnd.shuffle(opts)
        opts.sort(key=lambda c: (sum((c[0] + a, c[1] + b) not in used and 0 <= c[0] + a < COLS and 0 <= c[1] + b < ROWS for a, b in NB) < 2,
                                 abs(c[0] - x) + abs(c[1] - y) > 1))
        for c in opts:
            r = go(path + [c], used | {c})
            if r:
                return r
        return None
    s = (rnd.randrange(3), rnd.randrange(2))
    return go([s], {s})


if __name__ == '__main__':
    path = walk(1795)
    rnd = random.Random(7)
    out = {c: (round((x * SX + rnd.uniform(-JX, JX)) * SPREAD), round((y * SY + rnd.uniform(-JY, JY)) * SPREAD))
           for c, (x, y) in zip(ORDER, path)}
    json.dump(out, open('layout.json', 'w'), indent=0)
    print(len(out), 'placed')
