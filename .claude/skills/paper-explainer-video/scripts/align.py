"""Word-level timestamps for narration clips, computed locally (audio never leaves the machine).

You normally never run this by hand: when an act calls make_cue(CLIPS), any clip without timing
is aligned on the spot and saved into timing/words.json (and words.txt). So timing is created
together with the act that uses it.

Manual use (from the project folder):
  python align.py            # align every clip that has no timing yet
  python align.py 3 4        # (re)align these clips
Needs: pip install faster-whisper   (downloads the 'small.en' model once, ~500 MB)

audio/N.wav with an optional audio/N.txt transcript. The transcript is given to the model as a
prompt so proper nouns come out spelled the way the scenes reference them.
"""
import json, os, subprocess, sys
import numpy as np

PROJECT = os.environ.get('VOX_PROJECT', os.getcwd())
AUD = os.path.join(PROJECT, 'audio')
OUT = os.path.join(PROJECT, 'timing', 'words.json')
MODEL = os.environ.get('VOX_WHISPER', 'small.en')
_model = None


def load_audio(path):
    # Decode with ffmpeg ourselves: avoids PyAV version mismatches inside faster-whisper.
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def load_timing():
    return {int(k): v for k, v in json.load(open(OUT)).items()} if os.path.exists(OUT) else {}


def save_timing(res):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({str(k): res[k] for k in sorted(res)}, open(OUT, 'w'), indent=1)
    with open(os.path.join(os.path.dirname(OUT), 'words.txt'), 'w', encoding='utf-8') as f:
        for n in sorted(res):
            f.write(f'== {n}\n' + ' '.join(f"{w['w']}@{w['s']:.2f}" for w in res[n]) + '\n')


def align(clips):
    """Align the given clip numbers, merge them into timing/words.json, return the full timing dict."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(MODEL, device='cpu', compute_type='int8')
    res = load_timing()
    for n in clips:
        txt_path = os.path.join(AUD, f'{n}.txt')
        prompt = open(txt_path, encoding='utf-8').read().strip() if os.path.exists(txt_path) else None
        segs, _ = _model.transcribe(load_audio(os.path.join(AUD, f'{n}.wav')), word_timestamps=True,
                                    initial_prompt=prompt, beam_size=5, vad_filter=False)
        res[n] = [{'w': w.word.strip(), 's': round(w.start, 3), 'e': round(w.end, 3)} for s in segs for w in s.words]
        print(f'[timing] clip {n}: {len(res[n])} words  ' + ' '.join(x['w'] for x in res[n])[:70], flush=True)
    save_timing(res)
    return res


if __name__ == '__main__':
    every = sorted(int(f[:-4]) for f in os.listdir(AUD) if f.endswith('.wav') and f[:-4].isdigit())
    if not every:
        sys.exit(f'No numbered .wav clips in {AUD}')
    todo = [int(x) for x in sys.argv[1:]] or [n for n in every if n not in load_timing()]
    if todo:
        align(todo)
    print('->', OUT, '(and words.txt for picking cue phrases)')
