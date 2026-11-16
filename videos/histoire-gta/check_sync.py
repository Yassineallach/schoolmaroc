"""Words on screen before the narration says them.

    cd videos/histoire-gta && PYTHONPATH=<skill>/scripts:. VOX_LANG=fr python check_sync.py 1 2 3 4 5

For every words() line, tag() label and type_page() sentence, each on-screen word that the
narration also says is matched to the first time it is spoken at or after the previous matched
word (and not before the shot opens). A word shown more than TOL seconds before that time is
reported. Words the narration never says (paraphrase, translation) are not checked.
"""
import importlib, re, sys, unicodedata
import vox
import style as st
import typo as TY

TOL = 0.25


def norm(s):
    s = unicodedata.normalize('NFKD', s.lower().replace('’', "'"))
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", '', s)


def same(a, b):
    if not a or not b:
        return False
    if a == b:
        return True
    n = min(len(a), len(b))
    return n >= 4 and a[:max(4, n - 2)] == b[:max(4, n - 2)]


def spoken(clips):
    out, off = [], 0.0
    for c in clips:
        for w in vox._WORDS[c]:
            for part in re.split(r"[\s'’\-]+", w['w']):
                if norm(part):
                    out.append((norm(part), off + w['s']))
        off += vox._DUR[c]
    return out


STOP = {'le', 'la', 'les', 'de', 'des', 'du', 'un', 'une', 'et', 'a', 'au', 'aux', 'en', 'l', 'd', 'dans', 'par', 'sur', 'pour', 'son', 'sa', 'ses', 'qui', 'que'}


def check(act):
    m = importlib.import_module(f'act{act}')
    said = spoken(m.CLIPS)
    calls = []

    def rec(kind, text, times):
        calls.append((kind, text, times))

    def words_spy(layer, xy, s, size, t, times, *a, **k):
        ts = times if isinstance(times, (list, tuple)) else [times] * len(s.split())
        rec('words', s, [vox._SCENE_START + x for x in ts])
        return real_words(layer, xy, s, size, t, times, *a, **k)

    def tag_spy(layer, xy, s, size, t, start, *a, **k):
        rec('tag', s, [vox._SCENE_START + start] * len(s.split()))
        return real_tag(layer, xy, s, size, t, start, *a, **k)

    real_words, real_tag = st.words, st.tag
    real_draw = TY.Text.draw
    st.words, st.tag = words_spy, tag_spy

    def draw_spy(self, layer, xy, t, start, *a, **k):
        cues = k.get('cues')
        anim = k.get('anim', a[0] if a else 'words')
        if cues and anim != 'type':
            rec('type_page', self.s, [vox._SCENE_START + c for c in cues])
        return real_draw(self, layer, xy, t, start, *a, **k)

    TY.Text.draw = draw_spy
    starts = [s[0] for s in m.SHOTS] + [m.END]
    report = []
    for j, (s0, fn, *_) in enumerate(m.SHOTS):
        calls.clear()
        vox._SCENE_START = s0
        D = starts[j + 1] - s0
        fn(D - 0.02, D)
        seen = set()
        for kind, text, times in calls:
            if (kind, text) in seen:
                continue
            seen.add((kind, text))
            toks = text.split()
            last = s0 - 0.5
            for i, word in enumerate(toks):
                nw = norm(word)
                if not nw or nw in STOP or nw.isdigit() and len(nw) < 3:
                    continue
                shown = times[min(i, len(times) - 1)]
                hit = next((tt for (sw, tt) in said if tt >= last - 0.05 and same(nw, sw)), None)
                if hit is None:
                    continue
                last = hit
                if shown < hit - TOL:
                    report.append(f'act{act} {fn.__name__} {kind:9s} «{word}» shown {shown:6.2f}s, said {hit:6.2f}s  ({text[:60]})')
    TY.Text.draw = real_draw
    st.words, st.tag = real_words, real_tag
    return report


if __name__ == '__main__':
    acts = [int(a) for a in sys.argv[1:]] or [1, 2, 3, 4, 5]
    for a in acts:
        r = check(a)
        print('\n'.join(r) if r else f'act{a}: every checked word appears when (or after) it is said')
