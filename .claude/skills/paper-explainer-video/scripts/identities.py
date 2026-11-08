"""Visual identities: the design tokens of every video category, in one editable file.

An identity is more than colours. Each one sets:
    colours   HEX per role (see ROLES); `chart` is the ordered series for charts and infographics
    texture   how its grounds are made: paper grain, fibres, vignette, and a signature overlay
              ('fibre', 'foxing', 'stars', 'screentone', 'photocopy', 'dotgrid', 'marble', 'deckle',
              'canvas', 'ledger')
    image     how photographs and illustrations are treated: ('none'|'sepia'|'cold'|'cool'|'warm'|'ink', strength)
    type      font per typographic role (only the roles that differ from typo.py's defaults)
    scenes    which environments it favours (multipliers on scenes.CAPS) and the one it opens on
    variants  sub-identities chosen from the topic (a dark psychological manga vs a bright adventure one)

palette.py reads these, analyses the video's topic (category, sub-genre, period, region, tone),
combines them into the episode's identity and repairs any contrast that fails. Edit a value
here and every module follows: nothing else in the engine hardcodes a colour.

Colour roles (HEX):
    bg_primary     main light ground                bg_secondary  second ground: archive, folders, cards
    bg_minimal     minimalist ground (type pages)   bg_dark       dark ground: drama, night, depth
    bg_solid       bold solid ground (a statistic, one statement); light text sits on it
    text_primary   body and headlines on light      text_secondary  secondary lines, axes
    text_muted     labels, captions of lesser rank  text_on_dark  text on bg_dark and bg_solid
    accent_primary the colour of what matters       accent_secondary  the supporting colour
    accent_on_dark highlight that reads on bg_dark  highlight     marker sweeps, glows, tape, washes
    border         card edges, hairlines, grids     divider       rules, chart axes, separators
    fill_soft      quiet fills: bar bases, land     texture_tint  stains, dots, grain colour
"""

ROLES = ('bg_primary', 'bg_secondary', 'bg_minimal', 'bg_dark', 'bg_solid', 'text_primary', 'text_secondary', 'text_muted',
         'text_on_dark', 'accent_primary', 'accent_secondary', 'accent_on_dark', 'highlight', 'border', 'divider',
         'fill_soft', 'texture_tint')

IDENTITIES = {
    'editorial': dict(
        label='Editorial', description='Vox-style explainer: warm off-white paper, ink, terracotta with a teal counterpoint and a yellow marker.',
        use='general explainers, book summaries, ideas, education',
        colours=dict(bg_primary='#F3ECDF', bg_secondary='#E9DFCC', bg_minimal='#F8F4EC', bg_dark='#1E1C1A', bg_solid='#B8412A',
                     text_primary='#1B1917', text_secondary='#3A3632', text_muted='#6E675F', text_on_dark='#F5EFE4',
                     accent_primary='#CD5830', accent_secondary='#1F6F74', accent_on_dark='#F08A5D', highlight='#F2C14E',
                     border='#CFC2AC', divider='#9E8F78', fill_soft='#DDCCB0', texture_tint='#A88B62'),
        chart=['#CD5830', '#1F6F74', '#E0A33A', '#7D8B55', '#6E675F'],
        texture=dict(kind='fibre', mottle=1.0, fibres=900, vignette=10, grain=1.0),
        image=('none', 0.0),
        type={},
        scenes=dict(signature='theme', bias={}),
        keywords=('book', 'summary', 'novel', 'author', 'idea', 'lesson', 'habit', 'psychology', 'learn', 'explain', 'why we'),
    ),
    'history_archive': dict(
        label='History Archive', description='Aged parchment and iron-gall ink, oxblood seals and brass: a document pulled from a drawer.',
        use='history, biographies, historical events, wars, documents',
        colours=dict(bg_primary='#E6D5B0', bg_secondary='#D6BF92', bg_minimal='#EFE3C8', bg_dark='#2A1D13', bg_solid='#6E1E19',
                     text_primary='#24180F', text_secondary='#4A3626', text_muted='#6E5843', text_on_dark='#EEDFC0',
                     accent_primary='#7E2219', accent_secondary='#7A5C22', accent_on_dark='#D8A657', highlight='#C8963E',
                     border='#B59C70', divider='#7E6849', fill_soft='#CDB688', texture_tint='#8E6A3A'),
        chart=['#7E2219', '#7A5C22', '#3F5A4A', '#5B4636', '#A8865A'],
        texture=dict(kind='foxing', mottle=1.6, fibres=1400, vignette=26, grain=1.3),
        image=('sepia', 0.55),
        type={'headline': 'Playfair700.ttf', 'statement': 'Playfair700.ttf', 'caption': 'SpecialElite.ttf', 'term': 'Playfair700.ttf'},
        scenes=dict(signature='archive', bias={'archive': 1.9, 'paper': 1.2, 'halftone': 0.3, 'grid': 0.6, 'geometric': 0.6}),
        keywords=('century', 'empire', 'king', 'queen', 'emperor', 'war', 'revolution', 'ancient', 'dynasty', 'battle', 'treaty', 'colonial',
                  'medieval', 'history', 'historian', 'archive', 'reign', 'kingdom', 'conquest', 'army', 'born in', 'biography', 'era'),
    ),
    'science_space': dict(
        label='Science & Space', description='Chalk-blue paper and deep-space navy, a violet nebula accent and amber starlight in the dark.',
        use='physics, astronomy, cosmology, discoveries',
        colours=dict(bg_primary='#E4E9F2', bg_secondary='#D3DBEA', bg_minimal='#EEF1F7', bg_dark='#0A0F24', bg_solid='#26227A',
                     text_primary='#0D1330', text_secondary='#2E3963', text_muted='#56618A', text_on_dark='#E6EBFA',
                     accent_primary='#5B3FD0', accent_secondary='#1F6FB2', accent_on_dark='#FFB547', highlight='#8FD8F7',
                     border='#B4C0D8', divider='#7D8BAA', fill_soft='#C3CDE2', texture_tint='#6B7DB3'),
        chart=['#5B3FD0', '#1F6FB2', '#D9822B', '#2BA59B', '#56618A'],
        texture=dict(kind='stars', mottle=0.6, fibres=150, vignette=8, grain=0.7),
        image=('cool', 0.2),
        type={'statement': 'Inter600.ttf', 'caption': 'Inter400.ttf'},
        scenes=dict(signature='charcoal', bias={'charcoal': 2.4, 'bleed': 1.3, 'grid': 1.3, 'archive': 0.4, 'halftone': 0.3, 'paper': 0.7}),
        keywords=('universe', 'galaxy', 'star', 'planet', 'black hole', 'physics', 'quantum', 'gravity', 'atom', 'space', 'cosmic',
                  'telescope', 'relativity', 'particle', 'experiment', 'scientist', 'orbit', 'theory', 'physicist', 'light year', 'energy'),
        variants={
            'cosmos': dict(keywords=('black hole', 'galaxy', 'nebula', 'universe', 'big bang', 'cosmic', 'light year', 'event horizon', 'supernova'),
                           colours=dict(bg_dark='#060918', bg_solid='#1E1A66'), note='deep cosmos: darker space, amber starlight'),
            'lab': dict(keywords=('cell', 'chemistry', 'molecule', 'dna', 'gene', 'virus', 'medicine', 'laboratory', 'brain', 'protein', 'vaccine'),
                        colours=dict(accent_primary='#0E7C86', accent_secondary='#5B3FD0', highlight='#9BE3D9', bg_dark='#0C1A22',
                                     bg_solid='#0D5E66', accent_on_dark='#5FE0C8'),
                        chart=['#0E7C86', '#5B3FD0', '#D9822B', '#C2416B', '#56618A'],
                        note='laboratory science: teal and violet instead of starlight'),
        },
    ),
    'manga_ink': dict(
        label='Manga Ink', description='Stark white manuscript paper, pure black ink and screentone greys, one vermilion hanko stamp.',
        use='manga, anime, comics, illustration, graphic storytelling',
        colours=dict(bg_primary='#F6F4EE', bg_secondary='#E2E0DA', bg_minimal='#FBFAF7', bg_dark='#0B0B0B', bg_solid='#C42A1A',
                     text_primary='#0B0B0B', text_secondary='#2C2C2C', text_muted='#5E5E5E', text_on_dark='#F6F4EE',
                     accent_primary='#C42A1A', accent_secondary='#4A4A4A', accent_on_dark='#FF5A3C', highlight='#BDBDBD',
                     border='#0B0B0B', divider='#7A7A7A', fill_soft='#D4D2CC', texture_tint='#3A3A3A'),
        chart=['#0B0B0B', '#C42A1A', '#8A8A8A', '#4A4A4A', '#BDBDBD'],
        texture=dict(kind='screentone', mottle=0.4, fibres=0, vignette=0, grain=0.6),
        image=('ink', 0.85),
        type={'statement': 'ArchivoBlack.ttf', 'caption': 'Inter400.ttf'},
        scenes=dict(signature='halftone', bias={'halftone': 2.2, 'bleed': 1.6, 'charcoal': 1.2, 'geometric': 0.6, 'grid': 0.4, 'archive': 0.5}),
        keywords=('manga', 'anime', 'chapter', 'volume', 'serialized', 'serialised', 'mangaka', 'shonen', 'seinen', 'shojo', 'panel',
                  'comic', 'comics', 'drew', 'magazine', 'otaku', 'tankobon'),
        variants={
            'dark': dict(keywords=('violence', 'violent', 'horror', 'despair', 'revenge', 'brutal', 'trauma', 'sacrifice', 'demon', 'psychological',
                                   'eclipse', 'betrayal', 'massacre', 'darkness', 'monster', 'death', 'died', 'kill',
                                   # well-known dark works: the title itself sets the tone
                                   'berserk', 'attack on titan', 'tokyo ghoul', 'chainsaw man', 'death note', 'vagabond', 'vinland saga',
                                   'akira', 'monster', 'parasyte', 'devilman', 'junji ito', 'uzumaki', 'gantz', 'hellsing', 'claymore',
                                   'dark souls', 'elden ring', 'bloodborne'),
                         colours=dict(accent_primary='#9E1B1B', bg_solid='#7A1414', accent_on_dark='#E0443A', bg_primary='#EEECE6',
                                      bg_secondary='#DAD8D2'),
                         chart=['#0B0B0B', '#9E1B1B', '#8A8A8A', '#4A4A4A', '#BDBDBD'],
                         image=('ink', 1.0), note='dark seinen: dried-blood red, greyer paper, full ink treatment'),
            'bright': dict(keywords=('adventure', 'pirate', 'friendship', 'comedy', 'journey', 'sports', 'dream', 'treasure', 'school', 'fun',
                                     'colourful', 'colorful', 'hero', 'smile',
                                     'one piece', 'naruto', 'dragon ball', 'my hero academia', 'haikyu', 'spy x family', 'slam dunk',
                                     'pokemon', 'doraemon', 'sailor moon', 'yotsuba', 'toriko', 'hunter x hunter'),
                           colours=dict(accent_primary='#E0461F', accent_secondary='#1E6FD9', highlight='#FFD23F', bg_solid='#1E6FD9',
                                        accent_on_dark='#FFB020'),
                           chart=['#E0461F', '#1E6FD9', '#FFB020', '#0B0B0B', '#8A8A8A'],
                           image=('ink', 0.3), note='bright shonen: colour-cover orange and sky blue, yellow SFX highlight'),
        },
    ),
    'crime': dict(
        label='Crime & Investigation', description='Cold case-file grey, manila folders, evidence-tape yellow, dried crimson and steel blue.',
        use='criminal investigations, mysteries, trials, historical crimes',
        colours=dict(bg_primary='#DADDDF', bg_secondary='#D9C59A', bg_minimal='#E8EAEB', bg_dark='#101418', bg_solid='#7C1717',
                     text_primary='#0F1215', text_secondary='#2F363D', text_muted='#535C65', text_on_dark='#E3E6E8',
                     accent_primary='#8C1C1C', accent_secondary='#355C7D', accent_on_dark='#F2C230', highlight='#F2C230',
                     border='#A9B0B6', divider='#6F7880', fill_soft='#C3C8CC', texture_tint='#6F7A70'),
        chart=['#8C1C1C', '#355C7D', '#D9A520', '#6F7880', '#2F363D'],
        texture=dict(kind='photocopy', mottle=1.1, fibres=0, vignette=20, grain=1.4),
        image=('cold', 0.6),
        type={'statement': 'Inter600.ttf', 'caption': 'SpecialElite.ttf', 'label': 'Inter600.ttf'},
        scenes=dict(signature='charcoal', bias={'archive': 1.9, 'charcoal': 1.9, 'bleed': 1.2, 'theme': 0.7, 'halftone': 0.3, 'geometric': 0.6}),
        keywords=('murder', 'killer', 'police', 'detective', 'crime', 'victim', 'trial', 'court', 'evidence', 'investigation', 'suspect',
                  'prison', 'fbi', 'cult', 'disappeared', 'heist', 'fraud', 'case', 'witness', 'jury', 'mystery', 'serial'),
        variants={
            'historical': dict(keywords=('1800s', 'victorian', 'whitechapel', 'gaslight', 'prohibition', 'gangster', '19th century'),
                               colours=dict(bg_primary='#DCD6CA', bg_dark='#16130F', accent_secondary='#4A5A66'), image=('sepia', 0.45),
                               note='historical crime: sepia-cold case files'),
        },
    ),
    'technology': dict(
        label='Technology', description='Cool white and graphite, electric blue, signal cyan in the dark and an acid-lime terminal highlight.',
        use='artificial intelligence, computing, engineering, digital technology',
        colours=dict(bg_primary='#EDF0F3', bg_secondary='#DDE3EA', bg_minimal='#F5F7F9', bg_dark='#0A0E14', bg_solid='#1446D8',
                     text_primary='#0B0F15', text_secondary='#2B3440', text_muted='#56616E', text_on_dark='#E6EEF7',
                     accent_primary='#1F5BE0', accent_secondary='#0B7F8A', accent_on_dark='#2FE0FF', highlight='#B8F03A',
                     border='#BCC6D1', divider='#808C9A', fill_soft='#CBD3DC', texture_tint='#4C6A8A'),
        chart=['#1F5BE0', '#0B7F8A', '#8A5CF6', '#9CCB2A', '#56616E'],
        texture=dict(kind='dotgrid', mottle=0.3, fibres=0, vignette=4, grain=0.5),
        image=('cool', 0.25),
        type={'headline': 'Inter600.ttf', 'statement': 'Inter600.ttf', 'caption': 'Inter400.ttf', 'name': 'Inter600.ttf',
              'quote': 'Inter400.ttf', 'term': 'Inter600.ttf', 'subhead': 'Inter600.ttf'},
        scenes=dict(signature='grid', bias={'grid': 2.1, 'charcoal': 1.7, 'geometric': 1.3, 'archive': 0.3, 'halftone': 0.3, 'paper': 0.6}),
        keywords=('computer', 'software', 'internet', 'algorithm', 'artificial intelligence', 'ai', 'chip', 'silicon', 'startup', 'code',
                  'data', 'network', 'digital', 'robot', 'app', 'smartphone', 'engineer', 'machine learning', 'neural', 'programming'),
        variants={
            'retro': dict(keywords=('first computer', 'eniac', 'punch card', 'mainframe', 'vacuum tube', 'turing', 'ibm', 'transistor', 'apple ii',
                                    'commodore', 'arcade', 'history of computing', 'invented', 'babbage', 'lovelace'),
                          colours=dict(bg_primary='#E8E2D3', bg_secondary='#D9D0BA', bg_minimal='#F0EBDF', bg_dark='#111510', bg_solid='#1E6B3A',
                                       accent_primary='#1E7A3C', accent_secondary='#B5542B', accent_on_dark='#33FF77', highlight='#F5C342',
                                       fill_soft='#D4CBB4', border='#C3B99F', texture_tint='#7A7258'),
                          chart=['#1E7A3C', '#B5542B', '#3A5A8C', '#C9A227', '#56616E'],
                          type={'caption': 'SpecialElite.ttf', 'headline': 'ArchivoBlack.ttf'}, image=('warm', 0.2),
                          note='history of computing: beige plastic, phosphor green, teletype captions'),
        },
    ),
    'philosophy': dict(
        label='Philosophy & Belief', description='Marble ivory, lapis blue and gold leaf, with an aubergine night for the deep questions.',
        use='religion, philosophy, ethics, mythology, abstract ideas',
        colours=dict(bg_primary='#F1ECE2', bg_secondary='#E3DACA', bg_minimal='#F7F4EE', bg_dark='#1A1730', bg_solid='#233A7A',
                     text_primary='#1A1A26', text_secondary='#3B3A4E', text_muted='#5F5C6E', text_on_dark='#F0EADB',
                     accent_primary='#2B4A9B', accent_secondary='#8A6A22', accent_on_dark='#E3C278', highlight='#E3C278',
                     border='#CBBFA9', divider='#958870', fill_soft='#DCD2BF', texture_tint='#9A8C70'),
        chart=['#2B4A9B', '#8A6A22', '#6B4A7A', '#5F5C6E', '#B8A27A'],
        texture=dict(kind='marble', mottle=0.7, fibres=300, vignette=8, grain=0.8),
        image=('warm', 0.15),
        type={'headline': 'Playfair700.ttf', 'caption': 'PTSerif.ttf', 'term': 'Playfair700.ttf'},
        scenes=dict(signature='cream', bias={'cream': 2.0, 'charcoal': 1.2, 'geometric': 1.2, 'grid': 0.4, 'halftone': 0.2}),
        keywords=('god', 'faith', 'prophet', 'religion', 'soul', 'philosopher', 'philosophy', 'ethics', 'virtue', 'meaning', 'scripture',
                  'temple', 'monk', 'stoic', 'myth', 'mythology', 'divine', 'prayer', 'truth', 'existence', 'morality', 'consciousness'),
    ),
    'nature': dict(
        label='Nature', description='Sunlit linen and deep forest, moss and clay earth, with a fresh leaf highlight.',
        use='animals, wildlife, climate, geography, the environment',
        colours=dict(bg_primary='#EEEBDD', bg_secondary='#DFDAC3', bg_minimal='#F5F3EA', bg_dark='#12201A', bg_solid='#2F5D3A',
                     text_primary='#14201A', text_secondary='#34443A', text_muted='#56635A', text_on_dark='#EEF0E4',
                     accent_primary='#2F6B3F', accent_secondary='#A0552A', accent_on_dark='#A8D86A', highlight='#C9E27A',
                     border='#C7C2A6', divider='#8E8F74', fill_soft='#D3D2B4', texture_tint='#7F7A52'),
        chart=['#2F6B3F', '#A0552A', '#3D7EA6', '#C9A227', '#56635A'],
        texture=dict(kind='deckle', mottle=1.3, fibres=1100, vignette=12, grain=1.1),
        image=('none', 0.0),
        type={'headline': 'Fraunces700.ttf', 'caption': 'PTSerif.ttf'},
        scenes=dict(signature='bleed', bias={'bleed': 2.1, 'paper': 1.2, 'archive': 0.4, 'halftone': 0.2, 'grid': 0.8}),
        keywords=('forest', 'ocean', 'animal', 'species', 'climate', 'river', 'mountain', 'evolution', 'ecosystem', 'wildlife', 'bird',
                  'plant', 'earth', 'extinct', 'habitat', 'predator', 'migration', 'glacier', 'rainforest'),
        variants={
            'ocean': dict(keywords=('ocean', 'sea', 'whale', 'coral', 'reef', 'shark', 'deep sea', 'tide', 'marine'),
                          colours=dict(accent_primary='#1D6E8C', accent_secondary='#2F8F83', bg_dark='#0B1F2A', bg_solid='#1D5C7A',
                                       highlight='#8FD3E0', accent_on_dark='#7FD8E8', bg_primary='#E9EEEC'),
                          chart=['#1D6E8C', '#2F8F83', '#E0A33A', '#3D5A80', '#56635A'], note='ocean: sea blues and kelp teal'),
            'arid': dict(keywords=('desert', 'sahara', 'drought', 'heatwave', 'dune', 'savanna', 'wildfire', 'warming'),
                         colours=dict(accent_primary='#A4471E', accent_secondary='#7A6A2A', bg_primary='#EFE4CF', bg_secondary='#E2D2B2',
                                      bg_dark='#2A1A10', bg_solid='#8E3B17', highlight='#F0C66B', accent_on_dark='#F0A35E'),
                         chart=['#A4471E', '#C08A2E', '#2F6B3F', '#7A6A2A', '#56635A'], note='arid land and heat: sand, rust and sun'),
        },
    ),
    'culture': dict(
        label='Culture', description='Warm stone and museum plum, saffron and turquoise ceramic: civilisations, art and craft.',
        use='civilisations, traditions, art, literature, architecture',
        colours=dict(bg_primary='#EFE6DA', bg_secondary='#E2D3C0', bg_minimal='#F6F0E8', bg_dark='#22151C', bg_solid='#6A2445',
                     text_primary='#1F141A', text_secondary='#43323A', text_muted='#67565E', text_on_dark='#F3E9DE',
                     accent_primary='#7A2A4E', accent_secondary='#1F7A78', accent_on_dark='#F0A93B', highlight='#F0B44C',
                     border='#CDBBA6', divider='#94806C', fill_soft='#DCC8B2', texture_tint='#9A7A5E'),
        chart=['#7A2A4E', '#1F7A78', '#E09A2D', '#3A4F8C', '#67565E'],
        texture=dict(kind='canvas', mottle=1.0, fibres=500, vignette=12, grain=1.0),
        image=('warm', 0.12),
        type={'headline': 'Playfair700.ttf', 'statement': 'Fraunces700.ttf', 'caption': 'PTSerif.ttf'},
        scenes=dict(signature='bleed', bias={'paper': 1.4, 'geometric': 1.4, 'bleed': 1.5, 'halftone': 0.5, 'grid': 0.6}),
        keywords=('art', 'artist', 'painting', 'museum', 'architecture', 'tradition', 'culture', 'civilization', 'civilisation', 'literature',
                  'poet', 'poetry', 'music', 'cuisine', 'festival', 'craft', 'cathedral', 'mosque', 'palace', 'heritage', 'language'),
    ),
    'economics': dict(
        label='Economics', description='Salmon market paper, navy ink, ledger green for gains and red for losses: the financial page.',
        use='business, finance, economics, statistics, global markets',
        colours=dict(bg_primary='#F6E7D9', bg_secondary='#EDD6C2', bg_minimal='#FBF1E8', bg_dark='#0F1A2B', bg_solid='#0F4C81',
                     text_primary='#121A26', text_secondary='#33404F', text_muted='#5A6470', text_on_dark='#F2E9E0',
                     accent_primary='#0F4C81', accent_secondary='#1E7A4C', accent_on_dark='#F0B04A', highlight='#FFD27A',
                     border='#D9C1AC', divider='#A08872', fill_soft='#E6CDB8', texture_tint='#A68A72'),
        chart=['#0F4C81', '#1E7A4C', '#C0392B', '#E3A13B', '#5A6470'],
        texture=dict(kind='ledger', mottle=0.5, fibres=200, vignette=6, grain=0.8),
        image=('warm', 0.08),
        type={'headline': 'Fraunces700.ttf', 'caption': 'Inter400.ttf'},
        scenes=dict(signature='grid', bias={'grid': 2.3, 'accent': 1.6, 'geometric': 1.2, 'archive': 0.8, 'halftone': 0.2, 'bleed': 0.6}),
        keywords=('economy', 'economic', 'market', 'stock', 'inflation', 'bank', 'money', 'price', 'trade', 'company', 'business', 'profit',
                  'gdp', 'debt', 'investor', 'billion', 'recession', 'tax', 'wealth', 'finance', 'currency'),
        variants={
            'crisis': dict(keywords=('crash', 'recession', 'depression', 'collapse', 'bankrupt', 'panic', 'hyperinflation', 'bubble', 'default'),
                           colours=dict(bg_dark='#1A1414', accent_primary='#9E2A2B', bg_solid='#7A1F1F', highlight='#F2A65A', accent_on_dark='#F2A65A'),
                           chart=['#9E2A2B', '#0F4C81', '#5A6470', '#E3A13B', '#1E7A4C'], note='crisis: losses lead, red over navy'),
        },
    ),
}

# Regions shift the supporting colours (and, for history, culture, editorial and philosophy, the
# accent) towards the visual culture of the place. They never replace the identity.
REGIONS = {
    'japan':    dict(keywords=('japan', 'japanese', 'tokyo', 'kyoto', 'samurai', 'shogun', 'edo', 'meiji', 'osaka'),
                     accent='#B7282E', accent_secondary='#1F3A5F', highlight='#E8B04B', note='Japanese beni red and ai indigo'),
    'china':    dict(keywords=('china', 'chinese', 'beijing', 'ming', 'qing', 'han dynasty', 'mao', 'shanghai'),
                     accent='#A3201B', accent_secondary='#2E7D63', highlight='#D9A53F', note='cinnabar and jade'),
    'korea':    dict(keywords=('korea', 'korean', 'seoul', 'joseon'), accent='#B8322A', accent_secondary='#2A5CAA', highlight='#E8C25A',
                     note='Korean red and blue'),
    'maghreb':  dict(keywords=('morocco', 'moroccan', 'marrakech', 'fes', 'fez', 'casablanca', 'rabat', 'algeria', 'tunisia', 'maghreb', 'berber', 'amazigh'),
                     accent='#1F6B4F', accent_secondary='#2E4CB3', highlight='#E8B44A', note='zellige green, Majorelle blue and saffron'),
    'islamic':  dict(keywords=('islam', 'islamic', 'caliph', 'caliphate', 'ottoman', 'arab', 'arabic', 'baghdad', 'mecca', 'quran', 'persia', 'persian', 'andalus'),
                     accent='#156B70', accent_secondary='#8A5F15', highlight='#E2BE6A', note='turquoise tile and gold'),
    'egypt':    dict(keywords=('egypt', 'egyptian', 'pharaoh', 'pyramid', 'nile', 'cairo'),
                     accent='#1F4E9C', accent_secondary='#8C6A1E', highlight='#E9C46A', note='lapis lazuli and gold'),
    'classical': dict(keywords=('rome', 'roman', 'greece', 'greek', 'athens', 'sparta', 'caesar', 'byzantine'),
                      accent='#8C2F1E', accent_secondary='#3B5A7A', highlight='#D9B86A', note='Pompeian red and Aegean blue'),
    'india':    dict(keywords=('india', 'indian', 'mughal', 'delhi', 'hindu', 'bengal', 'gandhi'),
                     accent='#B8471F', accent_secondary='#146B6B', highlight='#F4A93B', note='saffron and peacock'),
    'africa':   dict(keywords=('africa', 'african', 'mali', 'ghana', 'nigeria', 'kenya', 'ethiopia', 'zulu', 'congo'),
                     accent='#A9471F', accent_secondary='#2F6F4F', highlight='#E8B33E', note='ochre, earth red and green'),
    'russia':   dict(keywords=('russia', 'russian', 'soviet', 'ussr', 'moscow', 'tsar', 'stalin', 'kremlin'),
                     accent='#A61C1C', accent_secondary='#3B4A5A', highlight='#D9B44A', note='Soviet red and steel'),
    'americas': dict(keywords=('aztec', 'maya', 'mayan', 'inca', 'mexico', 'peru', 'andes', 'mesoamerica'),
                     accent='#1E7F7A', accent_secondary='#B5482B', highlight='#E3B04B', note='turquoise jade and cochineal'),
    'nordic':   dict(keywords=('viking', 'vikings', 'norse', 'scandinavia', 'iceland', 'norway', 'sweden'),
                     accent='#2F4D63', accent_secondary='#7A5E30', highlight='#C9D6DF', note='slate, iron and frost'),
    'usa':      dict(keywords=('america', 'american', 'united states', 'washington', 'new york', 'civil war', 'president'),
                     accent='#1F3B73', accent_secondary='#B22234', highlight='#E8C35A', note='federal navy and flag red'),
}

# Periods change the atmosphere: paper, darkness, saturation and the supporting colour.
# Applied to identities where a period makes sense (history, culture, crime, economics, philosophy, editorial).
PERIODS = {
    'ancient':      dict(keywords=('ancient', 'bc', 'bce', 'bronze age', 'pharaoh', 'empire of', 'antiquity'), years=(-3000, 500),
                         colours=dict(accent_secondary='#7E5E24', bg_primary='#E8DCC2'), desaturate=0.0, note='antiquity: stone and bronze'),
    'medieval':     dict(keywords=('medieval', 'middle ages', 'crusade', 'knight', 'feudal', 'castle'), years=(500, 1450),
                         colours=dict(accent_secondary='#2C4A8C', highlight='#D9B25A'), desaturate=0.05, note='medieval: illumination lapis and gold'),
    'early_modern': dict(keywords=('renaissance', 'reformation', 'enlightenment', 'colonial', 'baroque'), years=(1450, 1800),
                         colours=dict(), desaturate=0.1, note='early modern: sepia print'),
    'industrial':   dict(keywords=('industrial', 'victorian', 'steam', 'railway', 'factory'), years=(1800, 1914),
                         colours=dict(bg_dark='#1E1B19'), desaturate=0.15, note='industrial age: soot and smoke'),
    'world_war':    dict(keywords=('world war', 'wwi', 'wwii', 'nazi', 'trench', 'allied', 'axis', 'holocaust', 'blitz', 'pearl harbor', 'd-day', 'hiroshima'),
                         years=(1914, 1945), colours=dict(accent_secondary='#5B5E2E', bg_primary='#DDD6C1', bg_secondary='#CEC5AA', bg_dark='#1B1E1F',
                                                         highlight='#C9B27A', fill_soft='#C9C0A3'),
                         desaturate=0.3, image=('sepia', 0.35), note='world wars: khaki, olive drab and gunmetal, drained colour'),
    'cold_war':     dict(keywords=('cold war', 'iron curtain', 'nuclear arms', 'cuban missile', 'berlin wall', 'kgb', 'cia'), years=(1947, 1991),
                         colours=dict(accent_secondary='#3E4A55', bg_dark='#15191C'), desaturate=0.2, note='cold war: concrete grey and propaganda red'),
    'contemporary': dict(keywords=('today', 'modern', 'social media', 'smartphone', '21st century'), years=(2000, 2100),
                         colours=dict(), desaturate=0.0, texture=0.7, note='contemporary: cleaner paper, less ageing'),
}

# the background theme an identity uses when episode.json names none
DEFAULT_THEME = {'history_archive': 'astrolabe', 'science_space': 'cosmic_atlas', 'technology': 'circuit',
                 'economics': 'ledger', 'manga_ink': 'manga_ink', 'culture': 'album'}

# when a project names a background theme and no palette, this is the identity it implies
THEME_IDENTITY = {'editorial': 'editorial', 'album': 'culture', 'cosmic_atlas': 'science_space', 'deep_space': 'science_space',
                  'laboratory': 'science_space', 'clinic': 'science_space', 'circuit': 'technology', 'archive': 'history_archive', 'astrolabe': 'history_archive',
                  'ledger': 'economics', 'ink_studio': 'manga_ink', 'manga_ink': 'manga_ink'}
