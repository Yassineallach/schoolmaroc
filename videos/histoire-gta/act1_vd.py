"""Acte 1 « Le bug »: the paper-desk design of act1.py, animated with vox-director's motion
(gta.vox_motion: fly-in + back-overshoot, breathing pieces, impact shakes, whip pans, confetti).

    python act1_vd.py sheet out/act1_vd_sheet.png 2 6 ...
    python act1_vd.py render out/act1_vd.mp4
"""
import os
import sys
from vox import contact_sheet, render_video
import gta as G
import act1 as A

G.vox_motion(A.__dict__)
frame, END, CLIPS = A.frame, A.END, A.CLIPS

if __name__ == '__main__':
    if sys.argv[1] == 'sheet':
        contact_sheet(frame, [float(x) for x in sys.argv[3:]], sys.argv[2])
    elif sys.argv[1] == 'render':
        out = sys.argv[2]
        render_video(frame, END, CLIPS, out, os.path.join(os.path.dirname(out), '_work_act1_vd'))
