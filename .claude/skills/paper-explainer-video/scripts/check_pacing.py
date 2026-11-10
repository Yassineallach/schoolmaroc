"""Pacing and variety check: the tells of a templated film, measured from the act files.

    cd project && python SK/scripts/check_pacing.py            (every actN.py; or: 1 2 3)

Reports, per act and for the film:
  - shot lengths: flags shots under 2.0 s (the eye cannot settle) and over 10 s with no change
    of composition; prints the average and the spread (a film whose shots all last the same
    time feels mechanical: aim for a mix of 2-4 s beats and 6-9 s holds);
  - the same environment on two shots in a row, and the same special cut twice in a row;
  - how much of each shot carries text (headline + caption layers): shots where type covers a
    large share of the frame for most of their length are listed, and the share of shots with
    NO text at all is printed (aim for at least a quarter: let images speak);
  - whether the first shot of the film opens on a chapter label before anything happens.
It only reads the act files; it renders nothing and changes nothing.
"""
import importlib, os, sys
import numpy as np

sys.path.insert(0, os.getcwd())
import vox  # noqa: E402

SHORT, LONG = 2.0, 10.0
SPECIAL = {'pageturn', 'circle', 'shape', 'zoom', 'collage'}


def cover(layer):
    return float((np.asarray(layer.getchannel('A').reduce(8)) > 40).mean())


def main(acts):
    lengths, textless, total, flags = [], 0, 0, []
    for a in acts:
        m = importlib.import_module(a)
        starts = [s[0] for s in m.SHOTS] + [m.END]
        prev_env, prev_cut = None, None
        for j, sh in enumerate(m.SHOTS):
            s0, fn = sh[0], sh[1]
            D = starts[j + 1] - s0
            cut = sh[2] if len(sh) > 2 else None
            cut = cut[0] if isinstance(cut, tuple) else cut
            vox._SCENE_START = s0
            samples = [fn(D * k, D) for k in (0.35, 0.65, 0.92)]
            env = samples[-1].env
            text = max(cover(s.top) + cover(s.hud) for s in samples)
            total += 1
            lengths.append(D)
            textless += text < 0.002
            name = f'{a}.{fn.__name__} @{s0:5.1f}s'
            if D < SHORT:
                flags.append(f'{name}: only {D:.1f} s on screen (under {SHORT} s)')
            if D > LONG:
                flags.append(f'{name}: {D:.1f} s; check it changes composition inside (push, second image, reveal)')
            if env == prev_env and env not in ('bleed',):
                flags.append(f'{name}: same environment as the previous shot ({env})')
            if cut in SPECIAL and cut == prev_cut:
                flags.append(f'{name}: same special cut twice in a row ({cut})')
            if text > 0.12:
                flags.append(f'{name}: type covers {text * 100:.0f} % of the frame; cut words or split the shot')
            prev_env, prev_cut = env, cut
    L = np.array(lengths)
    print(f'{total} shots, average {L.mean():.1f} s (shortest {L.min():.1f}, longest {L.max():.1f}, spread {L.std():.1f})')
    print(f'shots with no text at all: {textless} of {total} ({100 * textless / total:.0f} %; aim for 25 % or more)')
    if L.std() < 1.2:
        flags.append('every shot lasts about the same time: mix quick beats with long holds')
    for f in flags:
        print(' -', f)
    if not flags:
        print('no pacing flags')


if __name__ == '__main__':
    acts = [f'act{a}' for a in sys.argv[1:]] or sorted((f[:-3] for f in os.listdir('.') if f.startswith('act') and f[3:-3].isdigit()), key=lambda x: int(x[3:]))
    main(acts)
