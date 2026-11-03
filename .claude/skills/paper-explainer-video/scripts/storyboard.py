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


def to_markdown(rows):
    out = ['| clip | sentence | purpose | technique | weight | cue | cut |', '|---|---|---|---|---|---|---|']
    for r in rows:
        s = r['sentence'] if len(r['sentence']) < 90 else r['sentence'][:87] + '...'
        also = f" (+{', '.join(r['also'])})" if r['also'] else ''
        ct = f" @{r['cue_time']:.2f}" if r['cue_time'] is not None else ''
        out.append(f"| {r['clip']} | {s} | {r['purpose']}{also} | {r['technique']} | {r['weight']} | {r['cue']}{ct} | {r['cut']} |")
    weights = [r['weight'] for r in rows]
    out.append(f"\nPacing: {weights.count('complex')} complex, {weights.count('medium')} medium, {weights.count('simple')} simple. "
               f"Distinct techniques: {len(set(r['technique'] for r in rows))} of {len(rows)} shots.")
    return '\n'.join(out)


if __name__ == '__main__':
    project = os.environ.get('VOX_PROJECT', os.getcwd())
    args = sys.argv[1:]
    if not args or args == ['--all']:
        clips = sorted(int(f[:-4]) for f in os.listdir(os.path.join(project, 'audio')) if f.endswith('.txt') and f[:-4].isdigit())
    else:
        clips = [int(a) for a in args]
    md = to_markdown(plan(clips, project))
    print(md)
    if args == ['--all']:
        os.makedirs(os.path.join(project, 'timing'), exist_ok=True)
        open(os.path.join(project, 'timing', 'plan.md'), 'w').write(md + '\n')
