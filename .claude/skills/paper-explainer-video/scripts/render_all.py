"""Render every act and join them into the full film. Cross-platform (Linux, macOS, Windows).

Usage (from the project folder):
  python render_all.py                    # FULL quality: CRF 12, slow, 320k audio, all acts
  python render_all.py --draft            # fast review render: CRF 18, medium, 192k
  python render_all.py --acts 3 4         # re-render some acts, then rejoin
  python render_all.py --parallel 1       # one act at a time (low-RAM machines)

Acts are the files act1.py, act2.py, ... in the project folder; each must define
frame(t), END and CLIPS (the narration clip numbers it uses).
"""
import argparse, glob, importlib.util, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT = os.path.abspath(os.environ.get('VOX_PROJECT', os.getcwd()))
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--draft', action='store_true')
ap.add_argument('--acts', type=int, nargs='*')
ap.add_argument('--parallel', type=int, default=max(1, (os.cpu_count() or 2) // 2))
ap.add_argument('--out', default=os.path.join(PROJECT, 'out'))
args = ap.parse_args()

env = dict(os.environ, VOX_PROJECT=PROJECT, PYTHONPATH=HERE + os.pathsep + os.environ.get('PYTHONPATH', ''))
env.update(VOX_CRF='18', VOX_PRESET='medium', VOX_ABR='192k') if args.draft else env.update(VOX_CRF='12', VOX_PRESET='slow', VOX_ABR='320k')

acts = sorted(int(m.group(1)) for f in glob.glob(os.path.join(PROJECT, 'act*.py')) if (m := re.search(r'act(\d+)\.py$', f)))
todo = args.acts or acts
os.makedirs(args.out, exist_ok=True)
RUNNER = ("import importlib.util,sys,os;import vox;"
          "s=importlib.util.spec_from_file_location('act',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
          "vox.render_video(m.frame,m.END,m.CLIPS,sys.argv[2],os.path.join(os.path.dirname(sys.argv[2]),'_work_'+os.path.basename(sys.argv[1])[:-3]))")


def render(n):
    t0 = time.time()
    out = os.path.join(args.out, f'act{n}.mp4')
    r = subprocess.run([sys.executable, '-c', RUNNER, os.path.join(PROJECT, f'act{n}.py'), out], env=env, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f'act {n} failed:\n{r.stderr[-3000:]}')
    return n, time.time() - t0


start = time.time()
print(f'Rendering acts {todo} ({"draft" if args.draft else "FULL quality"}, {args.parallel} at a time)...')
with ThreadPoolExecutor(args.parallel) as pool:
    for job in as_completed([pool.submit(render, n) for n in todo]):
        n, secs = job.result()
        print(f'  act {n} done in {secs / 60:.1f} min')

missing = [n for n in acts if not os.path.exists(os.path.join(args.out, f'act{n}.mp4'))]
if missing:
    sys.exit(f'Not joined: acts {missing} not rendered yet.')
lst = os.path.join(args.out, 'acts.txt')
with open(lst, 'w', encoding='utf-8') as f:
    for n in acts:
        f.write("file '" + os.path.join(args.out, f'act{n}.mp4').replace('\\', '/') + "'\n")
full = os.path.join(args.out, 'full.mp4')
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', '-movflags', '+faststart', full], check=True)
dur = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', full], capture_output=True, text=True).stdout.strip()
print(f'Done: {full}  ({float(dur):.1f} s, {os.path.getsize(full) / 1e6:.0f} MB, {(time.time() - start) / 60:.1f} min)')
