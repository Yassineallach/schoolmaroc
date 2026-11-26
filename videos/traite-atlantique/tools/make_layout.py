"""The board's layout for La traite atlantique: a timeline (rule 46). Each act is a row read left
to right, so every travel moves forward in time; the next act's row starts again on the left, one
step lower. Act 1 sits on the right of the top row, so the hook G01 is directly above the last
drawing G44, which closes act 6 on its own row, set further down (« another world »).
    python tools/make_layout.py   ->  layout.json
"""
import json, random
ROWS = [
    ['G01', 'G02', 'M01', 'G03'],
    ['G04', 'G05', 'G06', 'G07', 'G08', 'M02', 'G09', 'G10', 'G11', 'G12'],
    ['G13', 'G14', 'G15', 'M03', 'G16', 'G17', 'G18', 'G19'],
    ['G20', 'G21', 'G39', 'G22', 'M04', 'G23', 'G24', 'G25', 'G26', 'G27', 'G28', 'G29', 'G30'],
    ['G31', 'M05', 'G32', 'G33', 'M06'],
    ['G34', 'G35', 'G36', 'G37', 'G38', 'G44'],
]
FIRST_COL = [5, 0, 0, 0, 0, 0]            # act 1 starts above G44's column
SX, SY, JX, JY = 1930, 1400, 90, 70
GAP_LAST = 500                            # act 6 sits apart

if __name__ == '__main__':
    rnd = random.Random(1482)
    out = {}
    for r, row in enumerate(ROWS):
        y0 = r * SY + (GAP_LAST if r == len(ROWS) - 1 else 0)
        for i, c in enumerate(row):
            out[c] = (round((FIRST_COL[r] + i) * SX + rnd.uniform(-JX, JX)), round(y0 + rnd.uniform(-JY, JY)))
    json.dump(out, open('layout.json', 'w'), indent=0)
    print(len(out), 'placed')
