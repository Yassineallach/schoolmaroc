import sys
def apply(path, pairs, header):
    s = open(path).read()
    for old, new in pairs:
        n = s.count(old)
        if n != 1:
            raise SystemExit(f'{path}: expected 1 match, found {n}: {old!r}')
        s = s.replace(old, new)
    if 'cue = make_cue' not in s:
        s = s.replace('\ndef ', '\n' + header + '\n\n\ndef ', 1)
    open(path, 'w').write(s)
    print(path, 'ok', len(pairs), 'edits')
