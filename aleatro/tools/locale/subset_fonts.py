"""Subset the Noto fonts to the characters the locale files use.

Usage: python3 tools/locale/subset_fonts.py <dir holding fonts/Noto*.ttf> <project dir>

Each font is pinned to weight 600 and its line metrics are set to the game
font's (ascent 1.06 em, descent 0.28 em), so a fallback glyph never makes a
line taller than the English text around it (Noto Sans Arabic is ~2.1 em).
"""
import json,sys,glob,os
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset
SP=sys.argv[1]; proj=sys.argv[2]
NATIVE='简体中文日本語한국어العربية'  # Loc.NATIVE, the ones outside Latin
chars={}
for f in glob.glob(proj+'/locale/*.json'):
    lang=os.path.basename(f)[:-5]
    d=json.load(open(f))['messages']
    chars[lang]=set(''.join(d.values()))
fonts={'sc':('NotoSansSC',['zh_CN','ja']),'jp':('NotoSansJP',['ja']),'kr':('NotoSansKR',['ko']),'arabic':('NotoSansArabic',['ar'])}
os.makedirs(proj+'/assets/fonts',exist_ok=True)
for key,(name,langs) in fonts.items():
    src=[p for p in glob.glob(SP+'/fonts/*') if os.path.basename(p).startswith(name)][0]
    text=set()
    for l in langs: text|=chars.get(l,set())
    # japanese text might borrow han from SC font only if JP lacks; keep just own langs
    text={c for c in text if ord(c)>0x024F}
    # the language picker shows every language's own name
    text|={c for c in NATIVE if ord(c)>0x024F}
    f=TTFont(src)
    axes={'wght':600}
    if 'fvar' in f and any(a.axisTag=='wdth' for a in f['fvar'].axes): axes['wdth']=100
    f=instancer.instantiateVariableFont(f,axes)
    opts=subset.Options(); opts.layout_features=['*']; opts.name_IDs=['*']
    s=subset.Subsetter(opts); s.populate(text=''.join(sorted(text))+'0123456789'); s.subset(f)
    out=proj+f'/assets/fonts/noto_{key}.ttf'
    upm=f['head'].unitsPerEm
    asc,desc=round(1.06*upm),round(0.28*upm)
    f['hhea'].ascent,f['hhea'].descent,f['hhea'].lineGap=asc,-desc,0
    os2=f['OS/2']
    os2.sTypoAscender,os2.sTypoDescender,os2.sTypoLineGap=asc,-desc,0
    os2.usWinAscent,os2.usWinDescent=asc,desc
    f.save(out); print(key,len(text),os.path.getsize(out))
