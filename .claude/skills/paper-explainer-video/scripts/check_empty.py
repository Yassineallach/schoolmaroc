"""No empty screens: flag every stretch where a shot shows only its ground.

    cd project && python SK/scripts/check_empty.py 1 2 3        (acts; none = every actN.py)

For each shot it calls the scene function every `step` seconds (no compositing, so it is fast)
and measures how much of the frame the shot's own layers cover (mid, top, hud and extra
planes; the background / environment ground is ignored). A run of at least `min_gap` seconds
under `min_cover` is reported with its time range and the shot's first docstring line.

Fix every hit before rendering: put something on screen from the cut (ENTER): the print the
sentence is about, a diagram that draws in, the typed line itself, a label. Never leave the
viewer waiting on a bare background for the cue word.
"""
import importlib, os, sys
import numpy as np

sys.path.insert(0, os.getcwd())
import vox  # noqa: E402

STEP = float(os.environ.get('VOX_EMPTY_STEP', 0.25))
MIN_COVER = float(os.environ.get('VOX_EMPTY_COVER', 0.004))   # share of the frame with visible content
MIN_GAP = float(os.environ.get('VOX_EMPTY_GAP', 0.75))        # seconds
SETTLE = 0.45                                                   # skip the cut itself (transition)


def coverage(shot):
    tot = 0.0
    for lay in [shot.mid, shot.top, shot.hud] + list(shot.extra.values()):
        a = np.asarray(lay.getchannel('A').reduce(8))
        tot += float((a > 40).mean())
    return tot


def check(act_name):
    m = importlib.import_module(act_name)
    starts = [s[0] for s in m.SHOTS] + [m.END]
    hits = []
    for j, sh in enumerate(m.SHOTS):
        s0, fn = sh[0], sh[1]
        D = starts[j + 1] - s0
        vox._SCENE_START = s0
        run = None
        tt = SETTLE if j else 0.0
        while tt < D - 0.1:
            empty = coverage(fn(tt, D)) < MIN_COVER
            if empty and run is None:
                run = tt
            if (not empty or tt + STEP >= D - 0.1) and run is not None:
                end = tt if not empty else D
                if end - run >= MIN_GAP:
                    doc = (fn.__doc__ or fn.__name__).strip().splitlines()[0][:70]
                    hits.append((s0 + run, s0 + end, fn.__name__, doc))
                run = None
            tt += STEP
    return hits


if __name__ == '__main__':
    acts = [f'act{a}' for a in sys.argv[1:]] or sorted(f[:-3] for f in os.listdir('.') if f.startswith('act') and f[3:-3].isdigit())
    bad = 0
    for a in acts:
        hits = check(a)
        bad += len(hits)
        for s, e, name, doc in hits:
            print(f'{a} {name}  {s:6.2f}-{e:6.2f}s  EMPTY ({e - s:.1f}s)  {doc}')
        if not hits:
            print(f'{a}: no empty screens')
    sys.exit(1 if bad else 0)
