"""One-off craft pass over acts 1-6 (SKILL.md section 14): text diet, stamp budget, no shot under
2 s, fewer special cuts, no ground repeated back to back. Run once; it asserts every edit."""
import re

D = '/home/user/schoolmaroc/videos/histoire-gta/'


class F:
    def __init__(self, name):
        self.p = D + name
        self.s = open(self.p).read()

    def rep(self, a, b, count=1):
        assert self.s.count(a) >= 1, (self.p, a[:90])
        self.s = self.s.replace(a, b) if count == 0 else self.s.replace(a, b, count)

    def drop(self, a):
        self.rep(a + '\n', '')

    def fn(self, name, new):
        i = self.s.index(f'def {name}(t, D):')
        m = re.compile(r'\n(?=[^\s#])').search(self.s, i + 10)      # next top-level line
        self.s = self.s[:i] + new.strip('\n') + '\n' + self.s[m.start():]

    def save(self):
        open(self.p, 'w').write(self.s)


if False:
    # ------------------------------------------------------------------ act 1
    a = F('act1.py')
    a.drop("    tag(s.hud, (330, 120), 'LE VOLEUR', 44, t, w(cue(1, 'voleur')), bg=G.THIEF, fg=INK)")
    a.drop("    tag(s.hud, (1590, 120), 'LA POLICE', 44, t, w(cue(1, 'police')))")
    a.drop("    tag(s.hud, (W / 2, 960), 'ILS FONCENT DROIT SUR LE JOUEUR', 54, t, w(cue(1, 'droit')))")
    a.rep("    P.stamp_hit(s.top, 'CASSÉ', 1440, 760, t, w(cue(2, 'casse')), size=120, ang=-9, shot=s)",
          "    A.emphasis(s.top, (1440, 760), 'CASSÉ', 130, t, w(cue(2, 'casse')), base=S.ink(s), colour=S.accent(s))")
    a.rep("""    for word, ph, x in (('PERCUTENT', 'percutent', 470), ('POUSSENT', 'poussent', 960), ('ENCERCLENT', 'encerclent', 1450)):
            tag(s.hud, (x, 120), word, 46, t, w(cue(2, ph)))
    """, "")
    i = a.s.index("    words(s.hud, (W / 2, 975), 'une lutte pour survivre'")
    j = a.s.index('\n', a.s.index(']', i)) + 1
    a.s = a.s[:i] + a.s[j:]
    a.rep("    P.stamp_hit(s.mid, 'ABANDONNÉ', 1420, 600, t, w(cue(2, 'risquait')), size=74, ang=-12, shot=s)",
          "    tag(s.mid, (1420, 600), 'ABANDONNÉ', 60, t, w(cue(2, 'abandonne')))")
    a.rep("    A.strike(s.mid, (1210, 550, 1630, 650), t, w(cue(2, 'abandonne')) + 0.35, scribble=True)",
          "    A.strike(s.mid, (1230, 560, 1610, 640), t, w(cue(2, 'abandonne')) + 0.5, scribble=True)")
    a.rep("    S.env(s, 'paper')\n    P.flip(s.mid, MOCKUP", "    S.env(s, 'cream')\n    P.flip(s.mid, MOCKUP")
    a.rep("""    words(s.hud, (W / 2, 470), 'UNE COURSE-POURSUITE', 92, t, [w(cue(3, 'une course')), w(cue(3, 'course'))], fill=CREAM)
    """, "")
    a.rep("A.emphasis(s.hud, (W / 2, 600), 'DÉRÉGLÉE'", "A.emphasis(s.hud, (W / 2, 540), 'DÉRÉGLÉE'")
    a.rep("(cue(2, 'Le concepteur') - LEAD, sF, 'pageturn'),", "(cue(2, 'Le concepteur') - LEAD, sF, 'lr'),")
    a.save()

    # ------------------------------------------------------------------ act 2
    b = F('act2.py')
    b.fn('sA', '''def sA(t, D):
        """Le studio s'appelait DMA Design. Fondé à Dundee par David Jones, ..."""
        s = Shot(t, D)
        S.env(s, 'paper')
        s.camera(1.0, 1.04, (760, 540))
        P.drop(s.mid, OFFICES, 560, 560, t, ENTER, rot=-3, spin=10, key='off')
        P.drop(s.mid, DMA, 1180, 300, t, w(cue(4, 'DMA')) - 0.1, rot=4, spin=14, key='dma')
        P.drop(s.mid, JONES, 1500, 600, t, w(cue(4, 'David')) - 0.2, rot=2.5, spin=10, key='jones')
        TY.name_card(s.top, (1180, 940), 'David Jones', 'FONDATEUR DE DMA DESIGN', t, w(cue(4, 'David')))
        kicker(s.hud, t, 2, 'Dundee')
        return s
    ''')
    b.fn('sB', '')
    b.rep("JONES = P.print_card(Image.open(asset('P03_jones.jpg')), 520, seed=22)", "JONES = P.print_card(Image.open(asset('P03_jones.jpg')), 420, seed=22)")
    b.drop("    words(s.hud, (560, 760), 'sans réfléchir', 58, t, [w(cue(4, 'avancent')), w(cue(4, 'reflechir'))], font=F_TYPE)")
    b.fn('sD', '''def sD(t, D):
        """Avec Race'n'Chase, l'équipe voulait une ville entière vue du dessus, où le joueur
        incarnerait le policier ou le voleur. Mais les missions tournaient en rond."""
        s = Shot(t, D)
        S.env(s, 'bleed')
        s.camera(1.35, 1.0, (960, 540))
        s.mid.alpha_composite(G.city())
        P.drop(s.mid, MOCKUP, 300, 380, t, ENTER + 0.2, rot=-4, spin=10, key='mockD')
        go = w(cue(4, 'tournaient'))
        for i, kind in enumerate(('cop', 'thief')):                    # round and round the same block
            u = max(0.0, t - go) * 0.9 + i * 0.5
            a = u * 2 * math.pi
            x = 960 + 300 * math.cos(a) * (1 if t > go else 0) + (0 if t > go else (-320 if i == 0 else 340))
            y = 540 + 290 * math.sin(a) * (1 if t > go else 0) + (0 if t > go else (-290 if i == 0 else 290))
            hd = math.degrees(a) + 90 if t > go else (0 if i == 0 else 180)
            G.car(s.mid, kind, x, y, hd, t)
        return s
    ''')
    b.fn('sE', '')
    b.drop("""    tag(s.hud, (W / 2, 140), "LE BUG A CHANGÉ L'ÉQUILIBRE", 48, t, w(cue(4, 'Le bug')))""")
    b.drop("    tag(s.hud, (560, 960), 'SEMER LE CHAOS', 54, t, w(cue(4, 'chaos')))")
    b.rep("    P.drop(s.hud, card, 1400, 960, t, w(cue(4, 'suivre')) - 0.2, rot=-2, spin=8, key='obj')",
          "    P.drop(s.mid, card, 1400, 960, t, w(cue(4, 'suivre')) - 0.2, rot=-2, spin=8, key='obj')")
    b.rep("    A.strike(s.hud, (1160, 925, 1640, 995), t, w(cue(4, 'objectifs')) + 0.3, scribble=False)",
          "    A.strike(s.mid, (1160, 925, 1640, 995), t, w(cue(4, 'objectifs')) + 0.3, scribble=False)")
    b.drop("    tag(s.hud, (W / 2, 990), 'CETTE LIBERTÉ', 54, t, w(cue(4, 'liberte')))")
    i = b.s.index("""    words(s.top, (W / 2, 230), "LES JEUX D'ACTION DE L'ÉPOQUE\"""")
    j = b.s.index('\n', b.s.index(']', i)) + 1
    b.s = b.s[:i] + b.s[j:]
    i = b.s.index("    words(s.top, (W / 2, 150), 'TROIS VILLES VUES DU CIEL'")
    j = b.s.index('\n', b.s.index(']', i)) + 1
    b.s = b.s[:i] + b.s[j:]
    b.drop("""    tag(s.hud, (360, 760), "N'IMPORTE QUELLE VOITURE", 40, t, a + 0.3)""")
    b.drop("    tag(s.hud, (960, 760), 'LA RADIO', 40, t, w(cue(5, 'radio')))")
    b.drop("    tag(s.hud, (1560, 760), 'DES TÉLÉPHONES PUBLICS', 40, t, w(cue(5, 'telephones')))")
    b.drop("    (cue(4, 'Fonde') - LEAD, sB, 'rl'),")
    b.drop("    (cue(4, 'Mais') - LEAD, sE, 'lr'),")
    b.rep("(cue(4, 'Le quai') - LEAD, sG, 'pageturn'),", "(cue(4, 'Le quai') - LEAD, sG, 'rl'),")
    b.save()


# ------------------------------------------------------------------ act 3
c = F('act3.py')
c.rep("    kicker(s.hud, t, 3, 'Le scandale')\n", "    tag(s.hud, (W / 2, 820), 'MAI 1997', 56, t, w(cue(6, 'mai')))\n    kicker(s.hud, t, 3, 'Le scandale')\n")
c.drop("    tag(s.hud, (W / 2, 140), 'MAI 1997', 52, t, w(cue(6, 'mai')))")
c.drop("    tag(s.hud, (W / 2, 960), 'LA CHAMBRE DES LORDS', 52, t, w(cue(6, 'Chambre')), bg=CREAM, fg=INK)")
i = c.s.index("    tag(s.hud, (W / 2 + (90 + MEL.width / 2 - W / 2) * k, 120), 'ROYAUME-UNI")
c.s = c.s[:i] + c.s[c.s.index('\n', i) + 1:]
c.drop("    P.stamp_hit(s.mid, 'INTERDIT', 1500, 470, t, w(cue(6, 'Bresil')), size=100, ang=-12, shot=s)")
c.drop("    tag(s.hud, (W / 2, 960), 'GRANDE-BRETAGNE', 52, t, w(cue(6, 'Grande')), bg=CREAM, fg=INK)")
c.drop("    tag(s.hud, (1400, 900), 'LA LICENCE', 48, t, w(cue(7, 'licence')))")
c.drop("    tag(s.hud, (W / 2, 140), 'LE RESPECT', 60, t, w(cue(7, 'respect')))")
i = c.s.index("""    words(s.hud, (W / 2, 960), "l'idée restera au cœur de la série\"""")
j = c.s.index('\n', c.s.index(']', i)) + 1
c.s = c.s[:i] + c.s[j:]
c.rep("(cue(6, 'En mai') - LEAD, sB, 'up'),", "(cue(6, 'Lord') - LEAD, sB, 'up'),")
c.rep("(cue(7, 'En 1998') - LEAD, sG, 'pageturn'),", "(cue(7, 'En 1998') - LEAD, sG, 'up'),")
c.save()

# ------------------------------------------------------------------ act 4
d = F('act4.py')
d.rep("    P.drop(s.hud, GTA3_LOGO, W / 2, 540,", "    P.drop(s.mid, GTA3_LOGO, W / 2, 540,")
i = d.s.index("    words(s.top, (W / 2, 330), 'QUELQUES SEMAINES AVANT SA SORTIE'")
j = d.s.index('\n', d.s.index(']', i)) + 1
d.s = d.s[:i] + d.s[j:]
d.drop("    tag(s.hud, (W / 2, 150), 'REPOUSSÉ', 60, t, w(cue(8, 'repousse')) + 0.2)")
d.drop("    tag(s.hud, (W / 2, 960), 'TROP PROCHES DES VOITURES DU NYPD', 46, t, w(cue(8, 'trop')))")
d.rep("    tag(s.mid, (W / 2 - 560, 330), 'AVANT', 44, t, w(cue(8, 'repeint')) + 0.3, anchor='r')",
      "    tag(s.mid, (W / 2 - 560, 330), 'AVANT', 44, t, ENTER + 0.4, anchor='r')")
d.rep("    tag(s.mid, (W / 2 - 560, 680), 'APRÈS', 44, t, w(cue(8, 'police')), bg=G.THIEF, fg=INK, anchor='r')",
      "    tag(s.mid, (W / 2 - 560, 680), 'APRÈS', 44, t, w(cue(8, 'celles')), bg=G.THIEF, fg=INK, anchor='r')")
d.drop("    tag(s.hud, (W / 2, 150), 'LIBERTY CITY EN TROIS DIMENSIONS', 52, t, w(cue(8, 'Liberty')))")
d.rep("""    if t < w(cue(8, 'volant')) - 0.2:
        tag(s.hud, (W / 2, 960), 'À PIED', 50, t, w(cue(8, 'pied')))
    elif t < w(cue(8, 'chaque')) - 0.2:
        tag(s.hud, (W / 2, 960), 'AU VOLANT', 50, t, w(cue(8, 'volant')))
    tag(s.hud, (W / 2, 960), "CHAQUE MISSION, PLUSIEURS FAÇONS", 50, t, w(cue(8, 'plusieurs')), bg=G.THIEF, fg=INK)
""", "")
d.rep("    tag(s.hud, (W / 2, 150), 'EN MÉMOIRE : QUELQUES PÂTÉS DE MAISONS À LA FOIS', 46, t, w(cue(9, 'memoire')))",
      "    tag(s.hud, (W / 2, 150), 'QUELQUES PÂTÉS DE MAISONS À LA FOIS', 46, t, w(cue(9, 'fois')))")
d.drop("    tag(s.hud, (330, 990), 'LA PRESSE', 52, t, w(cue(9, 'presse')))")
d.rep("    P.stamp_hit(s.top, '« CLONES DE GTA »', W / 2, 900, t, w(cue(9, 'clones')), size=100, ang=-6, shot=s)",
      "    tag(s.hud, (W / 2, 960), '« CLONES DE GTA »', 64, t, w(cue(9, 'clones')))")
d.rep("(cue(8, 'Quelques') - LEAD, sB, 'cut'),", "(cue(8, 'les attentats') - LEAD, sB, 'cut'),")
d.rep("(cue(8, 'repeint') - LEAD, sD, 'lr'),", "(cue(8, 'trop') - LEAD, sD, 'lr'),")
d.rep("(cue(8, 'GTA III', 2) - LEAD, sF, 'pageturn'),", "(cue(8, 'GTA III', 2) - LEAD, sF, 'rl'),")
d.save()

# ------------------------------------------------------------------ act 5
e = F('act5.py')
i = e.s.index("    words(s.hud, (W / 2, 470), 'UN PHÉNOMÈNE CULTUREL'")
j = e.s.index('\n', e.s.index(']', i)) + 1
e.s = e.s[:i] + e.s[j:]
e.rep("    P.drop(s.hud, VC_LOGO,", "    P.drop(s.mid, VC_LOGO,")
e.rep("        P.drop(s.hud, card, 560 + i * 800, 540,", "        P.drop(s.mid, card, 560 + i * 800, 540,")
e.drop("""    tag(s.hud, (W / 2, 160), "L'HISTOIRE EMPRUNTE OUVERTEMENT À…", 46, t, w(cue(10, 'ouvertement')) - 0.4)""")
e.rep("    P.drop(s.hud, SA_LOGO,", "    P.drop(s.mid, SA_LOGO,")
e.drop("    tag(s.hud, (W / 2, 990), 'COMME DANS UN JEU DE RÔLE', 52, t, w(cue(10, 'How')))")
e.rep("    P.stamp_hit(s.mid, 'N° 1', 1250, 760, t, w(cue(10, 'le jeu')) + 0.2, size=150, ang=-8, shot=s)\n", "")
i = e.s.index("    P.stamp_hit(s.mid, 'RADIÉ · 2008'")
j = e.s.index('\n', i) + 1
e.s = e.s[:i] + e.s[j:]
i = e.s.index("    words(s.hud, (1330, 450), 'une scène cachée sur le disque'")
j = e.s.index('\n', e.s.index(']', i)) + 1
e.s = e.s[:i] + e.s[j:]
i = e.s.index("    words(s.hud, (1330, 520), 'débloquée par un mod amateur'")
j = e.s.index('\n', e.s.index(']', i)) + 1
e.s = e.s[:i] + e.s[j:]
e.rep("    P.stamp_hit(s.top, '« HOT COFFEE »', 1330, 760, t, w(cue(11, 'Hot')), size=110, ang=-6, shot=s)",
      "    words(s.top, (1330, 560), '« HOT COFFEE »', 110, t, [w(cue(11, 'Hot'))] * 2, fill=S.accent(s))")
e.rep("    tag(s.hud, (W / 2, 540), 'BIEN AU-DELÀ DES JOUEURS', 64, t, w(cue(12, 'dela')) - 0.3)\n", "")
i = e.s.index('def sP(t, D):')
e.s = e.s[:i] + e.s[i:].replace("S.env(s, 'paper')", "S.env(s, 'cream')", 1)
e.rep("(cue(10, 'et l') - LEAD, sE, 'rl'),", "(cue(10, 'ouvertement') - LEAD, sE, 'rl'),")
e.rep("(cue(10, 'Deux') - LEAD, sF, ('circle', {'at': (W / 2, H / 2)})),", "(cue(10, 'Deux') - LEAD, sF, 'lr'),")
e.save()

# ------------------------------------------------------------------ act 6
f = F('act6.py')
f.rep("    P.drop(s.hud, GTA4_LOGO,", "    P.drop(s.mid, GTA4_LOGO,")
f.drop("    words(s.hud, (W / 2, 900), 'UN TON PLUS SOMBRE', 76, t, [w(cue(13, x)) for x in ('un', 'ton', 'plus', 'sombre')], fill=CREAM)")
f.drop("""    words(s.hud, (1480, 560), "un ancien soldat", 50, t, [w(cue(13, x)) for x in ('un', 'ancien', 'soldat')], font=F_TYPE)""")
i = f.s.index("""    words(s.hud, (1480, 630), "venu d'Europe de l'Est\"""")
j = f.s.index('\n', i) + 1
f.s = f.s[:i] + f.s[j:]
f.drop("""    words(s.top, (1380, 330), "UN NOUVEAU SYSTÈME", 60, t, [w(cue(13, x)) for x in ('Un', 'nouveau', 'systeme')])""")
f.drop("""    words(s.top, (1380, 410), "D'ANIMATION", 60, t, w(cue(13, "'animation")))""")
f.rep("""    words(s.hud, (W / 2, 470), 'GTA V VA PLUS LOIN', 110, t, [w(cue(14, x)) for x in ('GTA', 'V', 'va', 'plus', 'loin')], fill=CREAM)
    kicker(s.hud, t, 6, 'Les records')
""", """    tag(s.hud, (W / 2, 940), 'SEPTEMBRE 2013', 60, t, w(cue(14, 'septembre')))
""")
f.drop("    tag(s.hud, (1250, 260), 'SEPTEMBRE 2013', 56, t, w(cue(14, 'septembre')))")
f.drop("""    words(s.top, (1250, 520), "PASSER D'UN HÉROS", 84, t, [w(cue(14, x)) for x in ('passer', 'heros', 'heros')])""")
f.drop("""    words(s.top, (1250, 640), "À L'AUTRE", 84, t, [w(cue(14, x)) for x in ('a', "'autre")])""")
f.rep("    A.emphasis(s.top, (1250, 800), 'PARMI TROIS', 96, t, w(cue(14, 'trois')))",
      "    A.emphasis(s.top, (1250, 540), 'PARMI TROIS', 120, t, w(cue(14, 'trois')))")
f.rep("        P.drop(s.mid, card, x, 460, t, w(cue(14, ph)) - 0.25 if i else ENTER, rot=(-3, 2, -2)[i], spin=10, key=f'hero{i}')",
      "        P.drop(s.mid, card, x + (-30, 10, 40)[i], 460 + (0, 30, -20)[i], t, ENTER + (0.0, 0.25, 0.7)[i], rot=(-3.5, 1.5, -2)[i], spin=10, key=f'hero{i}')")
f.rep("(cue(14, 'Sorti') - LEAD, sF, 'cut'),", "(cue(14, 'il permet') - LEAD, sF, 'cut'),")
f.rep("(cue(14, 'une', 1) - LEAD, sH, ('circle', {'at': (W / 2, H / 2)})),", "(cue(14, 'Los') - LEAD, sH, 'cut'),")
f.rep("    tag(s.hud, (W / 2, 420), 'LOS SANTOS', 80, t, ENTER)", "    tag(s.hud, (W / 2, 420), 'LOS SANTOS', 80, t, ENTER + 0.1)")
f.save()
print('craft pass applied')
