"""Acte 0 : la carte d'ouverture de la chaîne (brand.intro_scene), avant la narration."""
import sys
from vox import *  # noqa: F401,F403
import style as st
import brand

SHOTS, END, CLIPS = brand.intro_act()


def frame(t):
    return st.make_frame(SHOTS, END, t, CLIPS)


if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
