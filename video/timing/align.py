import json, os, sys, subprocess
import numpy as np
def load(f):
    raw = subprocess.run(['ffmpeg','-v','error','-i',f,'-f','f32le','-ac','1','-ar','16000','-'],capture_output=True,check=True).stdout
    return np.frombuffer(raw, np.float32)
from faster_whisper import WhisperModel
AUD = sys.argv[1]; out = sys.argv[2]
m = WhisperModel('small.en', device='cpu', compute_type='int8')
res = {}
for n in range(1, 27):
    text = open(os.path.join(AUD, f'{n}.txt')).read().strip()
    segs, _ = m.transcribe(load(os.path.join(AUD, f'{n}.wav')), word_timestamps=True, initial_prompt=text, beam_size=5, vad_filter=False)
    words = [{'w': w.word.strip(), 's': round(w.start, 3), 'e': round(w.end, 3)} for s in segs for w in s.words]
    res[n] = words
    print(n, len(words), ' '.join(x['w'] for x in words)[:90], flush=True)
json.dump(res, open(out, 'w'), indent=1)
