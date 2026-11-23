"""Acte 0 : l'ouverture de la chaîne (le logo colorié à la main), avant la narration.
La sortie (brand.json intro.exit, ou VOX_INTRO_EXIT) : 'tear' (déchirure vers la première image du
film) ou 'glide' (le logo glisse vers le coin du filigrane)."""
import os
import sys
from vox import *  # noqa: F401,F403
import brand
import brand_intro as BI

CLIPS = ()
END = BI.END
EXIT_KIND = os.environ.get('VOX_INTRO_EXIT') or brand.CFG['intro'].get('exit', 'tear')
_FIRST = {}


def _first_frame():
    if 'f' not in _FIRST:
        import act1
        import style
        wm = brand.CFG['watermark']
        was, wm['enabled'] = wm['enabled'], False   # the gliding logo is the only logo until it lands
        saved = dict(style.EVENTS)                  # act 1's sounds belong to act 1, not to the intro
        first = act1.ENTRIES[0]
        start, first.start = first.start, 1e9       # the user: « the drawing starts before the intro finishes »:
        try:                                        # the intro ends on the bare board; the pen starts with act 1
            _FIRST['f'] = act1.frame(0.05)
        finally:
            first.start = start
            wm['enabled'] = was
            style.EVENTS.clear(); style.EVENTS.update(saved)
    return _FIRST['f']


def frame(t):
    return BI.intro_frame(t, _first_frame, EXIT_KIND)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
