"""Helpers shared by the acts of La traite atlantique."""
import annotate as A
import scenes as S
import board as BD

ACCENT = S.PAL.accent          # the motif's ink (oxblood), and only the motif's


def locked(e):
    """One drawing in three: no camera push, the pen is the only movement."""
    e.lock = True
    return e


def route(pts, at, dur=1.4, arrow=False, width=8):
    """The motif: a dashed route in the accent ink between points given as fractions of the
    drawing's image (a map's pins), drawn by the pen inside the drawing's own canvas."""
    def fn(c, lt, e):
        bx, by, bw, bh = e.d.box
        A.connect(c, [(bx + x * bw, by + y * bh) for x, y in pts], lt, at - e.start, dur=dur,
                  dashed=True, dots=False, width=width, sound=False, colour=ACCENT, arrowhead=arrow)
    fn.sound = (at, dur, lambda: ((0.0, 1.0),))
    return fn


def chainer(entries):
    """One pen at a time: each mark on a drawing starts when the drawing (or the previous mark) is
    finished, and never before its word is said."""
    G = {e.code: e for e in entries if not e.look}
    done = {c: e.start + e.dur + 0.15 for c, e in G.items()}

    def chain(code, items):
        t = done[code]
        for make, said in items:
            at = max(t, said)
            fn = make(at)
            G[code].extras.append(fn)
            t = at + fn.sound[1] + 0.15
        frame_words(G[code])
    return G, chain


def frame_words(e):
    """Centre the camera on the drawing together with the words written under (or above) it, so a
    larger drawing and its words both sit inside the frame."""
    h = 880 * e.scale
    below = [f.dy for f in e.extras if getattr(f, 'frac', None) == 'ink' and f.dy > 1]
    above = [f.dy for f in e.extras if getattr(f, 'frac', None) == 'ink' and f.dy < 0]
    e.cam_dy = (((max(below) - 1 + 0.06) * h / 2) if below else 0.0) - (((-min(above) + 0.06) * h / 2) if above else 0.0)


write = BD.write
