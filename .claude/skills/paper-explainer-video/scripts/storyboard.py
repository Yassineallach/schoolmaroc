"""Storytelling intelligence: read the narration, decide what each sentence is DOING, and pick a
technique from the whole toolkit for it, with variety and pacing.

    python storyboard.py 1 2 3 4          (from the project folder; clips of one act)
    python storyboard.py --all            (every clip)  -> also writes timing/plan.md

For each sentence it reports:
  purpose     what the sentence does (date, number, place, person, quote, comparison, process,
              list, correction, document, reveal, emotion, idea)
  technique   the visual from the toolkit that serves that purpose, never the same one twice in
              a row, and never the same special technique within three shots
  weight      complex / medium / simple, alternated so the film breathes: emotional lines are
              always simple (slow push, one image, few words)
  cue         the word the main action should land on
  cut         a suggested transition into the shot
  typography  whether the sentence earns a typographic moment (role + animation + word), within a
              budget of about 40 % of sentences: discoveries -> headline, dates -> oversized
              numerals, names -> name card, contradictions -> split / strike, short dramatic
              lines -> word by word, technical terms -> term card, quotes -> mask reveal

It is a planning aid, not an autopilot: read the plan, then write the act by hand; the user's
storyboard and their notes always win.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEO = os.path.join(os.path.dirname(HERE), 'assets', 'geo')

# purpose -> candidate techniques (first = preferred), each tagged with its weight
TECH = {
    'date':       [('timeline.event + Timeline.axis', 'medium'), ('timeline.year_counter', 'medium'), ('presets.stamp_hit (date)', 'simple')],
    'number':     [('charts.counter', 'medium'), ('annotate.stat', 'simple'), ('charts.compare', 'complex'), ('charts.unit_grid', 'complex')],
    'fraction':   [('charts.unit_grid', 'complex'), ('annotate.wedge', 'medium'), ('annotate.bars (fill_at)', 'medium')],
    'place':      [('maps.zoom + maps.marker', 'complex'), ('maps.border', 'complex'), ('maps.map_card + presets.unfold', 'medium')],
    'journey':    [('maps.route', 'complex')],
    'person':     [('presets.drop (photo print)', 'medium'), ('presets.tear_reveal (who)', 'complex'), ('objects.polaroid + objects.tape', 'medium')],
    'people':     [('presets.stack (portraits on a timeline)', 'complex'), ('transition collage', 'complex')],
    'quote':      [('style.words typed quote + annotate.underline', 'simple'), ('objects.letter + annotate.sweep', 'medium')],
    'comparison': [('charts.compare', 'complex'), ('charts.scale', 'complex'), ('two prints side by side + annotate.ring', 'medium')],
    'process':    [('charts.flow', 'complex'), ('annotate.connect / annotate.arrow', 'medium')],
    'list':       [('presets.stack', 'complex'), ('tags dropping one per item', 'medium')],
    'correction': [('annotate.strike + annotate.emphasis', 'simple'), ('presets.flip (before -> after)', 'medium')],
    'document':   [('presets.unfold + annotate.ring', 'medium'), ('presets.slide (friction) + stamp', 'medium'), ('objects.envelope', 'complex'), ('objects.newspaper + objects.spin_in', 'complex'), ('presets.page_flip', 'medium')],
    'reveal':     [('presets.mask_reveal', 'medium'), ('presets.tear_reveal', 'complex'), ('annotate.spotlight', 'simple')],
    'detail':     [('annotate.magnify', 'complex'), ('annotate.focus (camera into detail)', 'medium'), ('annotate.ring + annotate.arrow', 'simple')],
    'emotion':    [('one image, slow camera push, few words', 'simple'), ('style.words on paper, nothing else', 'simple')],
    'action':     [('cut-out with physical motion (drop / slide / assemble reverse)', 'complex'), ('plate + camera push on the verb', 'medium')],
    'comparison_text': [('two prints side by side + annotate.ring', 'medium'), ('transition shape between the two sides', 'medium'), ('annotate.strike + annotate.emphasis', 'simple')],
    'idea':       [('style.words headline + annotate.sweep', 'simple'), ('plate + slow push + typed caption', 'simple'), ('annotate.emphasis', 'simple')],
}

KEYWORDS = {
    'journey':    r'\b(travel(l?ed|s)?|journey|voyage|moved? (from|to)|flew|sailed|route|from \w+ to \w+)\b',
    'comparison': r'\b(than|versus|vs\.?|unlike|compared|bigger|smaller|more than|less than|twice|times (as|more|larger))\b',
    'process':    r'\b(leads? to|led to|because|therefore|so that|which (meant|caused)|caus(e|es|ed)|result(s|ed)? in|turns? into|became|becomes)\b',
    'correction': r'\b(changed|instead|not \w+ but|rather than|wrong|actually|corrected|replaced)\b',
    'document':   r'\b(manuscript|letter|book|report|diagnos\w*|newspaper|headline|list|record|page|pages|document|paper|card|chart|title)\b',
    'reveal':     r'\b(is|was) (called|named)\b|\bthe man is\b|\bdiscovered\b|\bshowed\b|\bfound\b|\brevealed\b',
    'emotion':    r'\b(died|death|dying|lost|alone|grief|afraid|fear|love|wife|husband|mother|father|child|voice|hope|deadline)\b',
    'detail':     r'\b(edge|detail|tiny|corner|point of)\b',
    'action':     r'\b(shatter\w*|slides?|falls?|fell|breaks?|broke|crash\w*|explod\w*|collaps\w*|spins?|drops?|tears?|burns?)\b',
    'fraction':   r'\b(half|third|quarter|one in \w+|per ?cent|%|percent)\b',
}


def _places():
    try:
        countries = json.load(open(os.path.join(GEO, 'countries_110m.json')))
        cities = json.load(open(os.path.join(GEO, 'cities_110m.json')))
    except FileNotFoundError:
        return set()
    names = {c['name'] for c in countries} | {c['long'] for c in countries if c.get('long')} | {c['name'] for c in cities}
    names |= {'England', 'Britain', 'Scotland', 'Wales', 'Europe', 'Africa', 'Asia', 'America', 'Antarctica', 'Switzerland', 'Swiss'}
    return {n for n in names if n and len(n) > 3}


PLACES = _places()
YEAR = re.compile(r'\b(1[0-9]{3}|20[0-9]{2})s?\b')
NUMBER = re.compile(r'\b\d[\d,\.]*\b|\b(million|billion|thousand|hundred|dozens)\b', re.I)
QUOTE = re.compile(r'["“][^"”]{3,}["”]')
CAP = re.compile(r'(?<![.!?]\s)(?<!^)\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)')
STOP = {'The', 'A', 'An', 'In', 'It', 'Its', 'He', 'His', 'She', 'Her', 'They', 'Their', 'But', 'And', 'Yet', 'When', 'Then', 'This',
        'That', 'Time', 'Big', 'Bang', 'God', 'Einstein\'s', 'Day', 'Pole', 'North', 'Sunday', 'Times', 'Fool\'s', 'April'}


def sentences(text):
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z"“])', text.strip())
    return [p.strip() for p in parts if p.strip()]


def analyse(s):
    """Return (purposes in priority order, cue word, details)."""
    found = []
    low = s.lower()
    places = sorted({p for p in PLACES if re.search(r'\b' + re.escape(p) + r'\b', s)}, key=s.find)
    people = [m for m in CAP.findall(s) if m.split()[0] not in STOP and m not in places and not YEAR.match(m)]
    years = YEAR.findall(s)
    if QUOTE.search(s):
        found.append(('quote', QUOTE.search(s).group(0).strip('"“”')))
    if len(places) >= 2 or (places and re.search(KEYWORDS['journey'], low)):
        found.append(('journey', places[0]))
    place_late = bool(places)
    for k in ('fraction',):
        m = re.search(KEYWORDS[k], low)
        if m:
            found.append((k, m.group(0)))
    nums = [n for n in NUMBER.findall(s) if n and not YEAR.fullmatch(str(n))]
    if any(re.search(r'\d', n) or n.lower() in ('million', 'billion', 'thousand', 'dozens') for n in nums if isinstance(n, str)):
        m = re.search(r'\b\d[\d,\.]*\b(\s\w+)?|\b(million|billion|thousand)\b', s)
        if m and not YEAR.fullmatch(m.group(0).split()[0]):
            found.append(('number', m.group(0)))
    if years:
        found.append(('date', years[0]))
    if place_late and not any(f[0] == 'journey' for f in found):
        found.append(('place', places[0]))
    if len(people) >= 3 or (len(people) >= 2 and ' to ' in s):
        found.append(('people', ', '.join(people[:3])))
    elif people:
        found.append(('person', people[0]))
    has_number = any(f[0] in ('number', 'fraction') for f in found)
    for k in ('comparison', 'correction', 'action', 'process', 'reveal', 'document', 'detail', 'emotion'):
        m = re.search(KEYWORDS[k], low)
        if m:
            found.append(('comparison' if (k != 'comparison' or has_number) else 'comparison_text', m.group(0)) if k == 'comparison' else (k, m.group(0)))
    if s.count(',') >= 3 and not any(f[0] in ('people',) for f in found):
        found.append(('list', s.split(',')[0][-20:]))
    if not found:
        found.append(('idea', max(re.findall(r"[A-Za-z']+", s), key=len)))
    # emotional sentences are kept simple: emotion wins when it is the only strong signal
    strong = [f for f in found if f[0] not in ('document', 'detail', 'emotion', 'reveal', 'process')]
    if any(f[0] == 'emotion' for f in found) and not strong:
        found.sort(key=lambda f: f[0] != 'emotion')
    return found


def plan(clips, project='.'):
    timing = {}
    tp = os.path.join(project, 'timing', 'words.json')
    if os.path.exists(tp):
        timing = {int(k): v for k, v in json.load(open(tp)).items()}
    rows, recent, last_weight = [], [], 'simple'
    for c in clips:
        text = open(os.path.join(project, 'audio', f'{c}.txt'), encoding='utf-8').read()
        for i, s in enumerate(sentences(text)):
            found = analyse(s)
            purpose, cue = found[0]
            options = TECH[purpose]
            best = None
            for tech, weight in options:              # variety + pacing
                score = 0
                if tech in recent[-3:]:
                    score -= 5
                if recent and tech == recent[-1]:
                    score -= 10
                if weight == 'complex' and last_weight == 'complex':
                    score -= 3
                if purpose == 'emotion' and weight != 'simple':
                    score -= 10
                if best is None or score > best[0]:
                    best = (score, tech, weight)
            _, tech, weight = best
            recent.append(tech)
            last_weight = weight
            cut = ('pageturn' if (i == 0 and c == clips[0]) else
                   'zoom' if purpose in ('place', 'detail') else
                   'collage' if purpose in ('people', 'list') else
                   'shape' if purpose in ('comparison', 'comparison_text', 'correction') else
                   'circle' if purpose == 'reveal' else ('lr', 'rl', 'up')[len(rows) % 3])
            t0 = None
            if c in timing and cue:
                first = re.findall(r"[A-Za-z0-9']+", str(cue).lower())
                for w in timing[c]:
                    if first and re.sub(r"[^a-z0-9']", '', w['w'].lower()).startswith(first[0]):
                        t0 = w['s']
                        break
            rows.append(dict(clip=c, sentence=s, purpose=purpose, also=[f[0] for f in found[1:4]], technique=tech,
                             weight=weight, cue=str(cue), cue_time=t0, cut=cut))
    return rows


# ---------------------------------------------------------------- typography pass
TERMS = ['event horizon', 'general relativity', 'quantum mechanics', 'black hole', 'big bang', 'motor neurone disease',
         'tracheotomy', 'synthesizer', 'probability', 'entropy', 'disorder', 'space-time', 'spacetime', 'gravity']
CONTRA = r"\b(but|yet|however|instead|refuse\w*|not \w+ but|although|despite|rather than|never)\b"
DISCOVERY = r"\b(discover\w*|showed|found|realis\w*|realiz\w*|proved|revealed|invented)\b"


def typography(rows, budget=0.4):
    """Mark the sentences where typography should carry the explanation, and how. Candidates are
    scored across the whole film, the strongest kept within `budget` (share of sentences), never
    two big type moments in a row, names only at their first mention, and the type animation is
    varied so no pattern repeats within three moments. Everything else stays with images."""
    cands, seen_names = [], set()
    for i, r in enumerate(rows):
        s, low = r['sentence'], r['sentence'].lower()
        words = re.findall(r"[\w'’-]+", s)
        c = None
        if r['purpose'] == 'emotion' and len(words) <= 9:
            c = (5, 'statement', 'words', words[-1])                         # quiet, word by word
        elif r['purpose'] == 'date' and YEAR.search(s):
            c = (5, 'date', 'big_number', YEAR.search(s).group(0))
        elif r['purpose'] in ('number', 'fraction') and re.search(r'\d', s):
            c = (5, 'stat', 'big_number', re.search(r'\d[\d,\.]*', s).group(0))
        elif r['purpose'] == 'correction' or ('correction' in r.get('also', []) and QUOTE.search(s)):
            c = (5, 'subhead', 'strike', r['cue'])
        elif r['purpose'] == 'quote':
            c = (4, 'quote', 'mask', r['cue'])
        elif re.search(DISCOVERY, low):
            c = (4, 'headline', 'scale', re.search(DISCOVERY, low).group(0))
        elif any(term in low for term in TERMS):
            c = (3, 'term', 'term_card', next(term for term in TERMS if term in low))
        elif r['purpose'] in ('person', 'people') and r['cue'] not in seen_names:
            c = (3, 'name', 'name_card', r['cue'])
        elif re.search(CONTRA, low) and len(words) <= 10:
            c = (2, 'subhead', 'split', re.search(CONTRA, low).group(0))
        elif len(words) <= 6 and r['purpose'] in ('idea', 'action'):
            c = (2, 'statement', 'words', words[-1])
        if c and c[1] == 'name':
            seen_names.add(r['cue'])
        if c:
            cands.append((c[0], i, c[1:]))
    n_max = max(1, int(len(rows) * budget))
    chosen = {}
    big = lambda role: role in ('headline', 'date', 'stat')
    for score, i, (role, anim, cue_) in sorted(cands, key=lambda c: (-c[0], c[1])):
        if len(chosen) >= n_max:
            break
        if big(role) and any(big(chosen[j][0]) for j in (i - 1, i + 1) if j in chosen):
            continue
        if (i - 1) in chosen and (i + 1) in chosen:               # never three type moments in a row
            continue
        chosen[i] = (role, anim, cue_)
    recent = []
    alt = {'words': 'letters', 'letters': 'slide', 'scale': 'lines', 'lines': 'tracking', 'mask': 'type', 'split': 'assemble', 'strike': 'split'}
    for i, r in enumerate(rows):
        if i not in chosen:
            r['type'] = ''
            continue
        role, anim, cue_ = chosen[i]
        while anim in recent[-3:] and anim in alt and alt[anim] not in recent[-3:]:
            anim = alt[anim]
        recent.append(anim)
        r['type'] = f'{role}: {anim} on "{cue_}"'
    return rows


def to_markdown(rows):
    out = ['| clip | sentence | purpose | mood | environment | technique | weight | cue | cut | typography |', '|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        s = r['sentence'] if len(r['sentence']) < 90 else r['sentence'][:87] + '...'
        also = f" (+{', '.join(r['also'])})" if r['also'] else ''
        ct = f" @{r['cue_time']:.2f}" if r['cue_time'] is not None else ''
        out.append(f"| {r['clip']} | {s} | {r['purpose']}{also} | {r.get('mood', '')} | {r.get('env', '')} | {r['technique']} | {r['weight']} | {r['cue']}{ct} | {r['cut']} | {r.get('type', '')} |")
    weights = [r['weight'] for r in rows]
    envs = [r.get('env') for r in rows if r.get('env')]
    if envs:
        rep = sum(1 for a, b in zip(envs, envs[1:]) if a == b)
        out.append(f"\nEnvironments: {', '.join(f'{e} {envs.count(e)}' for e in sorted(set(envs), key=envs.count, reverse=True))}; repeated back to back: {rep}.")
    moods = [r.get('mood') for r in rows if r.get('mood')]
    if moods:
        runs = [moods[0]] + [b for a, b in zip(moods, moods[1:]) if a != b]
        out.append(f"Moods (tone grades, palette.MOODS): {' > '.join(runs)}.")
    nt = sum(1 for r in rows if r.get('type'))
    out.append(f"\nTypography: {nt} of {len(rows)} sentences get a typographic moment; the rest are carried by images.")
    out.append(f"Pacing: {weights.count('complex')} complex, {weights.count('medium')} medium, {weights.count('simple')} simple. "
               f"Distinct techniques: {len(set(r['technique'] for r in rows))} of {len(rows)} shots.")
    return '\n'.join(out)


if __name__ == '__main__':
    project = os.environ.get('VOX_PROJECT', os.getcwd())
    args = sys.argv[1:]
    if not args or args == ['--all']:
        clips = sorted(int(f[:-4]) for f in os.listdir(os.path.join(project, 'audio')) if f.endswith('.txt') and f[:-4].isdigit())
    else:
        clips = [int(a) for a in args]
    import scenes, palette
    text = ' '.join(open(os.path.join(project, 'audio', f'{c}.txt'), encoding='utf-8').read() for c in clips)
    idn = palette.IDENTITY
    head = (f"Visual identity: {idn.name}\n" + ''.join(f"  - {w}\n" for w in idn.why)
            + "  Override in episode.json: \"palette\": \"<identity>[/variant]\" or {\"base\": ..., \"accent_primary\": \"#HEX\"}.\n\n")
    md = head + to_markdown(scenes.plan_environments(palette.plan_moods(typography(plan(clips, project)))))
    print(md)
    if args == ['--all']:
        os.makedirs(os.path.join(project, 'timing'), exist_ok=True)
        open(os.path.join(project, 'timing', 'plan.md'), 'w').write(md + '\n')
