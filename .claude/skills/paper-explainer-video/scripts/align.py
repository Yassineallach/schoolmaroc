"""Word-level timestamps for every narration clip, computed locally (audio never leaves the machine).

Usage (from the project folder):  python align.py            -> writes timing/words.json
Needs:  pip install faster-whisper   (downloads the 'small.en' model once, ~500 MB)

audio/N.wav with an optional audio/N.txt script. The script is given to the model as a prompt so
proper nouns (Darrow, Lykos, ...) come out spelled the way the scenes reference them.
"""
import json, os, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel

PROJECT = os.environ.get('VOX_PROJECT', os.getcwd())
AUD = os.path.join(PROJECT, 'audio')
OUT = os.path.join(PROJECT, 'timing', 'words.json')
MODEL = os.environ.get('VOX_WHISPER', 'small.en')


def load(path):
    # Decode with ffmpeg ourselves: avoids PyAV version mismatches inside faster-whisper.
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


clips = sorted(int(f[:-4]) for f in os.listdir(AUD) if f.endswith('.wav') and f[:-4].isdigit())
if not clips:
    sys.exit(f'No numbered .wav clips in {AUD}')
model = WhisperModel(MODEL, device='cpu', compute_type='int8')
res = {}
for n in clips:
    txt_path = os.path.join(AUD, f'{n}.txt')
    prompt = open(txt_path, encoding='utf-8').read().strip() if os.path.exists(txt_path) else None
    segs, _ = model.transcribe(load(os.path.join(AUD, f'{n}.wav')), word_timestamps=True,
                               initial_prompt=prompt, beam_size=5, vad_filter=False)
    res[n] = [{'w': w.word.strip(), 's': round(w.start, 3), 'e': round(w.end, 3)} for s in segs for w in s.words]
    print(f'{n:>3} {len(res[n]):>3} words  ' + ' '.join(x['w'] for x in res[n])[:80], flush=True)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(res, open(OUT, 'w'), indent=1)
with open(os.path.join(os.path.dirname(OUT), 'words.txt'), 'w', encoding='utf-8') as f:
    for n in clips:
        f.write(f'== {n}\n' + ' '.join(f"{w['w']}@{w['s']:.2f}" for w in res[n]) + '\n')
print('->', OUT, '(and words.txt for picking cue phrases)')
