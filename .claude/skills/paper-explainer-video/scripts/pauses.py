"""Give the narration the pauses it needs: measure the real silence at every sentence end and
insert silence where the narrator ran on. The voice is never cut or stretched; word timings in
timing/words.json (and words.txt) shift with the audio, so cues stay right.

    cd videos/<project>
    python SK/scripts/pauses.py                 # report only: every sentence end and its real pause
    python SK/scripts/pauses.py --apply         # insert the missing silence (backs up audio/ first)
    python SK/scripts/pauses.py --apply --at 5:3.97:0.41   # a sentence end the matcher can't place:
                                                # clip 5, cut at 3.97 s, it already has 0.41 s of pause

Targets (narrator's real pause → at least): full stop / ! 0.60 s, ? 0.75 s, colon 0.40 s, and a
comma that runs straight on (under 0.12 s) 0.22 s. A cut is only made inside real silence; a
comma whose words are joined with no quiet gap is skipped and reported. Script words come from
audio/N.txt and are matched letter by letter to the Whisper words, so contractions (« l'avocat »)
and split words line up. Years and numbers written as digits in the script and as words by
Whisper can't be matched: check the report for 0.0x s pauses after a number and place them with --at.

Run it before building the acts (or re-check the acts after: cues move with the audio).
First used on « L'histoire de GTA »: 41 sentence ends and 12 commas, +8 s over 6½ minutes.
"""
import argparse, difflib, json, os, re, shutil, sys, unicodedata, wave
import numpy as np

TARGET = {'.': 0.60, '!': 0.60, '?': 0.75, ':': 0.40, ',': 0.22}
COMMA_MAX = 0.12          # a comma with less than this gets a short breath


def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in s if unicodedata.category(c) != 'Mn'))


def load(path):
    w = wave.open(path); sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16); w.close()
    return x, sr, ch, sw


def energy(x, sr, hop=0.005, win=0.02):
    f = x.astype(np.float32) / 32768
    h, n = int(sr * hop), int(sr * win)
    return np.array([np.sqrt(np.mean(f[i:i + n] ** 2)) for i in range(0, len(f) - n, h)]), hop


def ends(clip, words):
    """[(script word, punctuation, measured pause s, cut time s)] for one clip."""
    txt = open(f'audio/{clip}.txt', encoding='utf-8').read().split()
    ws = words[str(clip)]
    A, aend = '', []
    for t in txt:
        A += norm(t); aend.append(len(A) - 1)
    B, own = '', []
    for k, w in enumerate(ws):
        n = norm(w['w']); B += n; own += [k] * len(n)
    blocks = difflib.SequenceMatcher(None, A, B, autojunk=False).get_matching_blocks()

    def amap(p):
        best = None
        for bl in blocks:
            if bl.size == 0:
                continue
            if bl.a <= p < bl.a + bl.size:
                return bl.b + p - bl.a
            d = p - (bl.a + bl.size - 1)
            if d > 0:
                best = bl.b + bl.size - 1 + d
        return min(best if best is not None else 0, len(B) - 1)

    x, sr, *_ = load(f'audio/{clip}.wav')
    e, hop = energy(x, sr)
    quiet = e < max(0.006, np.percentile(e, 95) * 0.06)
    out = []
    for i, t in enumerate(txt[:-1]):
        p = re.search(r'([.!?:;,…])\W*$', t)
        if not p or not B:
            continue
        pu = ';' if p.group(1) == ';' else p.group(1)
        if pu not in TARGET:
            continue
        j = own[amap(aend[i])]
        if j + 1 >= len(ws):
            continue
        lo, hi = max(ws[j]['s'], ws[j]['e'] - 0.5), ws[j + 1]['e'] + 0.5
        a0, a1 = max(0, int(lo / hop)), min(len(e), int(hi / hop))
        best, k = (0, None), a0
        while k < a1:                                  # longest quiet run near the boundary
            if quiet[k]:
                l = k
                while l > 0 and quiet[l - 1]:
                    l -= 1
                r = k
                while r + 1 < len(e) and quiet[r + 1]:
                    r += 1
                if r - l + 1 > best[0]:
                    best = (r - l + 1, (l, r))
                k = r + 1
            else:
                k += 1
        if best[1] is None:                            # no quiet run: the quietest point, if quiet enough
            b0, b1 = int((ws[j]['e'] - 0.15) / hop), int((ws[j]['e'] + 0.15) / hop)
            m = b0 + int(np.argmin(e[b0:b1])) if b1 > b0 else b0
            out.append((t, pu, 0.0, round(m * hop + 0.01, 3) if e[m] <= 0.012 else None))
        else:
            l, r = best[1]
            gap = round(best[0] * hop, 2)
            if pu == ',' and gap < 0.03:              # 10-20 ms of quiet can be a stop consonant inside a word
                out.append((t, pu, gap, None)); continue
            out.append((t, pu, gap, round((l + r) / 2 * hop + 0.01, 3)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--clips', type=int, nargs='*')
    ap.add_argument('--at', action='append', default=[], help='CLIP:CUT_S:MEASURED_S for an end the matcher missed')
    ap.add_argument('--no-commas', action='store_true')
    a = ap.parse_args()
    words = json.load(open('timing/words.json', encoding='utf-8'))
    clips = a.clips or sorted(int(c) for c in words)
    manual = {}
    for s in a.at:
        c, cut, have = s.split(':')
        manual.setdefault(int(c), []).append((float(cut), float(have)))
    if a.apply and not os.path.isdir('audio/_before_pauses'):
        shutil.copytree('audio', 'audio/_before_pauses', ignore=shutil.ignore_patterns('_before_pauses'))
        shutil.copy('timing/words.json', 'audio/_before_pauses/words.json')
    total = 0.0
    for c in clips:
        ins = []
        for t, pu, pause, cut in ends(c, words):
            if pu == ',' and (a.no_commas or pause >= COMMA_MAX):
                continue
            need = round(TARGET[pu] - pause, 2)
            flag = ''
            if cut is None:
                flag = '  SKIPPED: no quiet gap between the words'
            elif re.search(r'\d', t) and pause < 0.1:
                cut, flag = None, '  CHECK: a number (digits in the script, words in Whisper); place it with --at'
            elif need > 0.06:
                ins.append((cut, need)); flag = f'  +{need:.2f}s'
            if flag or pu != ',':
                print(f'clip {c:2d}  {"?" if cut is None else f"{cut:6.2f}"}s  {t:<22} pause {pause:.2f}s{flag}')
        for cut, have in manual.get(c, []):
            need = max(TARGET['.'] - have, 0)
            if need > 0.06:
                ins.append((cut, round(need, 2))); print(f'clip {c:2d}  {cut:6.2f}s  (--at)  pause {have:.2f}s  +{need:.2f}s')
        total += sum(n for _, n in ins)
        if not (a.apply and ins):
            continue
        x, sr, ch, sw = load(f'audio/{c}.wav')
        parts, last = [], 0
        for cut, need in sorted(ins):
            k = int(cut * sr) * ch
            parts += [x[last:k], np.zeros(int(need * sr) * ch, np.int16)]
            last = k
        parts.append(x[last:])
        o = wave.open(f'audio/{c}.wav', 'wb'); o.setnchannels(ch); o.setsampwidth(sw); o.setframerate(sr)
        o.writeframes(np.concatenate(parts).tobytes()); o.close()
        for wd in words[str(c)]:
            wd['s'] = round(wd['s'] + sum(n for cu, n in ins if wd['s'] >= cu - 0.02), 3)
            wd['e'] = max(wd['s'], round(wd['e'] + sum(n for cu, n in ins if wd['e'] > cu + 0.02), 3))
    print(f'{"inserted" if a.apply else "would insert"} {total:.2f} s of silence')
    if a.apply:
        json.dump(words, open('timing/words.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        with open('timing/words.txt', 'w', encoding='utf-8') as f:
            for c in sorted(words, key=int):
                f.write(f'== {c}\n' + ' '.join(f"{w['w']}@{w['s']:.2f}" for w in words[c]) + '\n')
        print('backup of the untouched audio: audio/_before_pauses/')


if __name__ == '__main__':
    main()
