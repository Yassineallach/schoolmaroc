"""Lay a music bed under a finished film without re-rendering the picture.

    python SK/scripts/music.py out/full.mp4 music.mp3 out/full_music.mp4 [--level -30] [--duck 8] [--tail 4]

The music loops to the film's length, fades in over 2 s and out over the last `tail` seconds,
sits at `level` LUFS (default -30: about 14 dB under a -16 LUFS voice) and is ducked a further
`duck` dB by the narration (sidechain), so it rises gently in the pauses. The picture stream
is copied. The result is measured and printed: integrated loudness should stay near -16 LUFS.

Only use music the user supplies or names, with a licence that covers YouTube.
"""
import argparse, subprocess, re

ap = argparse.ArgumentParser()
ap.add_argument('film'); ap.add_argument('music'); ap.add_argument('out')
ap.add_argument('--level', type=float, default=-30.0)
ap.add_argument('--duck', type=float, default=8.0)
ap.add_argument('--tail', type=float, default=4.0)
a = ap.parse_args()

dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a.film],
                           capture_output=True, text=True).stdout)
ratio = max(2.0, 10 ** (a.duck / 20) * 1.6)
fc = (f"[1:a]aloop=loop=-1:size=2e9,atrim=0:{dur:.3f},loudnorm=I={a.level}:TP=-3:LRA=7,"
      f"afade=t=in:d=2,afade=t=out:st={dur - a.tail:.3f}:d={a.tail}[m];"
      f"[0:a]asplit=2[v][key];"
      f"[m][key]sidechaincompress=threshold=0.02:ratio={ratio:.1f}:attack=40:release=600[md];"
      f"[v][md]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89[a]")
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', a.film, '-i', a.music, '-filter_complex', fc,
                '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k', '-movflags', '+faststart', a.out], check=True)
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', a.out, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
m = re.findall(r'I:\s+(-?[\d.]+) LUFS', r)
print(f'{a.out}: {dur:.1f} s, integrated loudness {m[-1] if m else "?"} LUFS (target about -16)')
