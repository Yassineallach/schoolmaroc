#!/usr/bin/env python3
"""Build locale/<lang>.json from the translation tables here.

keys.tsv      id <TAB> English key, ids fixed once given (new keys are added
              at the end from ui_keys.txt and data_keys.txt).
<lang>.tsv    id <TAB> translation. Templates use {0}, {1}... for the key's
              %d / %s parts in order.

Run from the project root: python3 tools/locale/build.py
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGS = ["zh_CN", "ja", "ko", "de", "fr", "es", "pt_BR", "it", "ar"]
SPECIAL = {"{comma}": ", ", "{semicolon}": "; "}


def source_keys():
    out = []
    for name in ["ui_keys.txt", "data_keys.txt"]:
        for line in open(os.path.join(HERE, name), encoding="utf8").read().split("\n"):
            if line.startswith("#") or not line.strip():
                continue
            out.append(SPECIAL.get(line, line))
    return out


def load_keys():
    path = os.path.join(HERE, "keys.tsv")
    keys = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf8").read().split("\n"):
            if line:
                i, k = line.split("\t", 1)
                keys[int(i)] = k.replace("\\n", "\n")
    known = set(keys.values())
    nxt = max(keys, default=0) + 1
    for k in source_keys():
        if k not in known:
            keys[nxt] = k
            known.add(k)
            nxt += 1
    with open(path, "w", encoding="utf8") as f:
        for i in sorted(keys):
            f.write("%d\t%s\n" % (i, keys[i]))
    return keys


def main():
    keys = load_keys()
    live = set(source_keys())
    ok = True
    for lang in LANGS:
        path = os.path.join(HERE, lang + ".tsv")
        if not os.path.exists(path):
            print(lang, "no table yet")
            continue
        msgs = {}
        for n, line in enumerate(open(path, encoding="utf8").read().split("\n"), 1):
            if not line.strip() or line.startswith("#"):
                continue
            i, t = line.split("\t", 1)
            k = keys.get(int(i))
            if k is None:
                print("%s:%d unknown id %s" % (lang, n, i)); ok = False
                continue
            parts = len(re.findall(r"%[ds]", k))
            have = sorted(set(int(x) for x in re.findall(r"\{(\d)\}", t)))
            if have != list(range(parts)):
                print("%s:%d id %s placeholders %s for %r -> %r" % (lang, n, i, have, k, t)); ok = False
            # editors drop trailing spaces: give list separators theirs back,
            # except the full-width CJK ones, which carry their own spacing
            if k in SPECIAL.values() and not t.endswith(" ") and ord(t[-1]) < 0x3000:
                t += " "
            msgs[k] = t
        missing = [k for k in live if k not in msgs]
        if missing:
            print(lang, len(missing), "untranslated, e.g.", missing[:3])
        os.makedirs(os.path.join(ROOT, "locale"), exist_ok=True)
        with open(os.path.join(ROOT, "locale", lang + ".json"), "w", encoding="utf8") as f:
            json.dump({"messages": msgs}, f, ensure_ascii=False, indent=0, sort_keys=True)
        print(lang, len(msgs), "messages")
    sys.exit(0 if ok else 1)


main()
