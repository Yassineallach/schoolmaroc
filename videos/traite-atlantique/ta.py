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
    """Centre the camera on the drawing together with the words written under, above or beside it,
    so a larger drawing and its words both sit inside the frame."""
    h = 880 * e.scale
    words = [f for f in e.extras if getattr(f, 'frac', None) == 'ink' and hasattr(f, 'text')]
    below = [f.dy for f in words if f.dy > 1]
    above = [f.dy for f in words if f.dy < 0]
    e.cam_dy = (((max(below) - 1 + 0.06) * h / 2) if below else 0.0) - (((-min(above) + 0.06) * h / 2) if above else 0.0)
    side = [f for f in words if f.dx > 1 and f.anchor == 'l']
    e.cam_dx = max(0.45 * f.size * len(f.text) for f in side) / 2 if side else 0.0


# Text layouts (the user: « the same composition in every view »): chosen by meaning.
def under(text, at, line=0, size=62, dur=None):
    """The default: centred under the drawing (line 0, then 1 below it)."""
    return write(text, size, 0.50, 1.08 + 0.12 * line * size / 62, at, frac='ink', dur=dur)


def over(text, at, size=62, dur=None):
    """Above the drawing (a date or a heading that opens the view)."""
    return write(text, size, 0.50, -0.08, at, frac='ink', dur=dur)


def big(text, at, line=0, size=104, dur=None):
    """The key word of the sentence, large, under the drawing."""
    return write(text, size, 0.50, 1.10 + 0.16 * line, at, frac='ink', dur=dur)


def side(text, at, line=0, size=66, dur=None, y=0.42):
    """Beside a narrow drawing, on its right, read like a caption in the margin."""
    return write(text, size, 1.06, y + 0.13 * line * size / 66, at, frac='ink', anchor='l', dur=dur)


def mark(kind, geom, at, dur=0.6):
    """One pen mark in the accent ink on the drawing's key detail (the user: « the pen draws but
    never points »), in fractions of the drawing's image: ring (x0, y0, x1, y1), underline
    (x0, x1, y), arrow ((x0, y0), (x1, y1))."""
    def fn(c, lt, e):
        bx, by, bw, bh = e.d.box
        P = lambda x, y: (bx + x * bw, by + y * bh)
        st = at - e.start
        if kind == 'ring':
            (x0, y0), (x1, y1) = P(*geom[:2]), P(*geom[2:])
            A.ring(c, (x0, y0, x1, y1), lt, st, dur=dur, colour=ACCENT, width=9, sound=False)
        elif kind == 'underline':
            (x0, y), (x1, _) = P(geom[0], geom[2]), P(geom[1], geom[2])
            A.underline(c, (x0, y - 10, x1, y), lt, st, dur=dur, colour=ACCENT, width=9, sound=False)
        else:
            A.arrow(c, P(*geom[0]), P(*geom[1]), lt, st, dur=dur, colour=ACCENT, width=9, head=34, sound=False)
    fn.sound = (at, dur, lambda: ((0.0, 1.0),))
    return fn


write = BD.write
