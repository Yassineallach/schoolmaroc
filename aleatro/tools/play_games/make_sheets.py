"""Writes the Play Console sheets for Aleatro's Play Games achievements and
leaderboards, from scripts/achievements.gd (English) plus the translations
below:

  python3 tools/play_games/make_sheets.py

  tools/play_games/achievements.csv   one row per achievement, in list order
  tools/play_games/leaderboards.csv   one row per leaderboard
  tools/play_games/translations.csv   name and description in every language
  tools/play_games/LEADERBOARDS.md     the four leaderboards, field by field, to
                                      enter in Play Console (there's no import)
  tools/play_games/AchievementsImport.zip
      Play Console's "Import achievements" file: AchievementsMetadata.csv,
      AchievementsLocalizations.csv, AchievementsIconsMappings.csv and the
      icons, flat, with no header rows and no commas in any field
"""
import csv
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

# Play Console language codes for the game's languages
LANGS = ["zh-CN", "ja-JP", "ko-KR", "de-DE", "fr-FR", "es-ES", "pt-BR", "it-IT", "ar"]

# key -> one (name, description) per language in LANGS
T = {
    "climbing": [("攀登", "到达第 4 底注"), ("クライム", "アンティ 4 に到達する"), ("등반", "앤티 4에 도달하기"),
                 ("Aufstieg", "Erreiche Ante 4"), ("Ascension", "Atteindre la mise 4"), ("Escalada", "Llega al ante 4"),
                 ("Escalada", "Chegue ao ante 4"), ("Scalata", "Raggiungi l'ante 4"), ("التسلّق", "اصل إلى المرحلة 4")],
    "summit": [("登顶", "到达第 8 底注"), ("頂上", "アンティ 8 に到達する"), ("정상", "앤티 8에 도달하기"),
               ("Gipfel", "Erreiche Ante 8"), ("Sommet", "Atteindre la mise 8"), ("Cumbre", "Llega al ante 8"),
               ("Cume", "Chegue ao ante 8"), ("Vetta", "Raggiungi l'ante 8"), ("القمة", "اصل إلى المرحلة 8")],
    "victory_lap": [("凯旋", "赢得一局"), ("ウイニングラン", "ランに勝利する"), ("승리의 한 바퀴", "런에서 승리하기"),
                    ("Ehrenrunde", "Gewinne einen Lauf"), ("Tour d'honneur", "Gagner une partie"), ("Vuelta de honor", "Gana una partida"),
                    ("Volta da vitória", "Vença uma partida"), ("Giro d'onore", "Vinci una partita"), ("جولة النصر", "افز بجولة")],
    "red_chip": [("红色筹码", "以红色筹码或更高赌注赢得一局"), ("赤チップ", "赤チップ以上のステークでランに勝利する"), ("빨간색 칩", "빨간색 칩 이상 스테이크로 런에서 승리하기"),
                 ("Roter Chip", "Gewinne einen Lauf mit Roter Chip oder höher"), ("Jeton rouge", "Gagner une partie en Jeton rouge ou plus"), ("Ficha roja", "Gana una partida con Ficha roja o superior"),
                 ("Ficha vermelha", "Vença uma partida com Ficha vermelha ou superior"), ("Fiche rossa", "Vinci una partita con Fiche rossa o superiore"), ("الرقاقة الحمراء", "افز بجولة على رهان الرقاقة الحمراء أو أعلى")],
    "black_chip": [("黑色筹码", "以黑色筹码或更高赌注赢得一局"), ("黒チップ", "黒チップ以上のステークでランに勝利する"), ("검은색 칩", "검은색 칩 이상 스테이크로 런에서 승리하기"),
                   ("Schwarzer Chip", "Gewinne einen Lauf mit Schwarzer Chip oder höher"), ("Jeton noir", "Gagner une partie en Jeton noir ou plus"), ("Ficha negra", "Gana una partida con Ficha negra o superior"),
                   ("Ficha preta", "Vença uma partida com Ficha preta ou superior"), ("Fiche nera", "Vinci una partita con Fiche nera o superiore"), ("الرقاقة السوداء", "افز بجولة على رهان الرقاقة السوداء أو أعلى")],
    "gold_chip": [("金色筹码", "以金色筹码赌注赢得一局"), ("金チップ", "金チップのステークでランに勝利する"), ("금색 칩", "금색 칩 스테이크로 런에서 승리하기"),
                  ("Goldener Chip", "Gewinne einen Lauf mit Goldener Chip"), ("Jeton doré", "Gagner une partie en Jeton doré"), ("Ficha dorada", "Gana una partida con Ficha dorada"),
                  ("Ficha dourada", "Vença uma partida com Ficha dourada"), ("Fiche dorata", "Vinci una partita con Fiche dorata"), ("الرقاقة الذهبية", "افز بجولة على رهان الرقاقة الذهبية")],
    "card_sharp": [("老千", "打出 2500 张牌"), ("カードの達人", "カードを 2500 枚プレイする"), ("카드 달인", "카드 2500장 플레이하기"),
                   ("Kartenhai", "Spiele 2.500 Karten"), ("As des cartes", "Jouer 2 500 cartes"), ("Tahúr", "Juega 2.500 cartas"),
                   ("Mestre das cartas", "Jogue 2.500 cartas"), ("Asso delle carte", "Gioca 2.500 carte"), ("محترف الورق", "العب 2500 ورقة")],
    "clean_sweep": [("大扫除", "弃掉 2500 张牌"), ("大掃除", "カードを 2500 枚捨てる"), ("대청소", "카드 2500장 버리기"),
                    ("Großputz", "Wirf 2.500 Karten ab"), ("Grand ménage", "Défausser 2 500 cartes"), ("Limpieza total", "Descarta 2.500 cartas"),
                    ("Faxina geral", "Descarte 2.500 cartas"), ("Pulizia totale", "Scarta 2.500 carte"), ("تنظيف شامل", "تخلّص من 2500 ورقة")],
    "nest_egg": [("小金库", "同时拥有 $400"), ("へそくり", "所持金 $400 に到達する"), ("비상금", "한 번에 $400 보유하기"),
                 ("Notgroschen", "Besitze gleichzeitig $400"), ("Bas de laine", "Posséder 400 $ à la fois"), ("Hucha", "Ten $400 a la vez"),
                 ("Pé-de-meia", "Tenha $400 de uma vez"), ("Gruzzolo", "Possiedi $400 in una volta"), ("المدّخرات", "امتلك 400$ في وقت واحد")],
    "speedrun": [("速通", "在 12 回合或更少内赢得一局"), ("スピードラン", "12 ラウンド以内でランに勝利する"), ("스피드런", "12라운드 이하로 런에서 승리하기"),
                 ("Speedrun", "Gewinne einen Lauf in 12 Runden oder weniger"), ("Speedrun", "Gagner une partie en 12 manches ou moins"), ("Speedrun", "Gana una partida en 12 rondas o menos"),
                 ("Speedrun", "Vença uma partida em 12 rodadas ou menos"), ("Speedrun", "Vinci una partita in 12 round o meno"), ("الجولة السريعة", "افز بجولة في 12 دورة أو أقل")],
    "glass_cannon": [("玻璃大炮", "在一手牌中打碎 2 张玻璃牌"), ("ガラスの大砲", "1 回のハンドでガラスカードを 2 枚割る"), ("유리 대포", "한 핸드에서 유리 카드 2장 깨뜨리기"),
                     ("Glaskanone", "Zerbrich 2 Glaskarten in einer Hand"), ("Canon de verre", "Briser 2 cartes de verre en une main"), ("Cañón de cristal", "Rompe 2 cartas de cristal en una mano"),
                     ("Canhão de vidro", "Quebre 2 cartas de vidro em uma mão"), ("Cannone di vetro", "Rompi 2 carte di vetro in una mano"), ("مدفع زجاجي", "حطّم ورقتين زجاجيتين في يد واحدة")],
    "royalty": [("皇室", "打出皇家同花顺"), ("ロイヤル", "ロイヤルフラッシュをプレイする"), ("왕족", "로열 플러시 플레이하기"),
                ("Königlich", "Spiele einen Royal Flush"), ("Royauté", "Jouer une quinte flush royale"), ("Realeza", "Juega una escalera real"),
                ("Realeza", "Jogue um royal flush"), ("Regalità", "Gioca una scala reale"), ("الملكية", "العب الرويال فلاش")],
    "grandmaster": [("大师", "将任意牌型升到 10 级"), ("グランドマスター", "いずれかのポーカーハンドをレベル 10 にする"), ("그랜드마스터", "아무 포커 핸드나 레벨 10으로 올리기"),
                    ("Großmeister", "Bringe eine Pokerhand auf Stufe 10"), ("Grand maître", "Monter une main de poker au niveau 10"), ("Gran maestro", "Sube cualquier mano de póker al nivel 10"),
                    ("Grão-mestre", "Leve qualquer mão de pôquer ao nível 10"), ("Gran maestro", "Porta una mano di poker al livello 10"), ("الأستاذ الكبير", "ارفع أي يد بوكر إلى المستوى 10")],
    "collector": [("收藏家", "发现所有护符"), ("コレクター", "すべてのチャームを発見する"), ("수집가", "모든 부적 발견하기"),
                  ("Sammler", "Entdecke alle Talismane"), ("Collectionneur", "Découvrir tous les charmes"), ("Coleccionista", "Descubre todos los amuletos"),
                  ("Colecionador", "Descubra todos os amuletos"), ("Collezionista", "Scopri tutti gli amuleti"), ("الجامع", "اكتشف كل التمائم")],
    "living_legend": [("活传奇", "发现一个传奇护符"), ("生ける伝説", "伝説のチャームを発見する"), ("살아있는 전설", "전설 부적 발견하기"),
                      ("Lebende Legende", "Entdecke einen legendären Talisman"), ("Légende vivante", "Découvrir un charme légendaire"), ("Leyenda viviente", "Descubre un amuleto legendario"),
                      ("Lenda viva", "Descubra um amuleto lendário"), ("Leggenda vivente", "Scopri un amuleto leggendario"), ("أسطورة حيّة", "اكتشف تميمة أسطورية")],
    "stargazer": [("观星者", "发现所有符文"), ("星を見る者", "すべてのルーンを発見する"), ("별을 보는 자", "모든 룬 발견하기"),
                  ("Sterngucker", "Entdecke alle Runen"), ("Astronome", "Découvrir toutes les runes"), ("Astrónomo", "Descubre todas las runas"),
                  ("Astrônomo", "Descubra todas as runas"), ("Astronomo", "Scopri tutte le rune"), ("راصد النجوم", "اكتشف كل الرونات")],
    "fortune_teller": [("占卜师", "发现所有法术"), ("占い師", "すべてのスペルを発見する"), ("점술가", "모든 주문 발견하기"),
                       ("Wahrsager", "Entdecke alle Zauber"), ("Diseuse de bonne aventure", "Découvrir tous les sorts"), ("Adivino", "Descubre todos los hechizos"),
                       ("Vidente", "Descubra todos os feitiços"), ("Indovino", "Scopri tutti gli incantesimi"), ("قارئ الطالع", "اكتشف كل التعاويذ")],
    "seer": [("先知", "发现所有预兆"), ("予言者", "すべてのオーメンを発見する"), ("예언자", "모든 징조 발견하기"),
             ("Seher", "Entdecke alle Omen"), ("Voyant", "Découvrir tous les présages"), ("Profeta", "Descubre todos los augurios"),
             ("Profeta", "Descubra todos os presságios"), ("Veggente", "Scopri tutti i presagi"), ("العرّاف", "اكتشف كل النُّذُر")],
    "hex_hunter": [("咒术猎人", "遭遇所有Boss盲注"), ("ヘックスハンター", "すべてのボスブラインドと対戦する"), ("헥스 사냥꾼", "모든 보스 블라인드와 맞서기"),
                   ("Fluchjäger", "Tritt gegen jeden Boss-Blind an"), ("Chasseur de maléfices", "Affronter chaque blinde de boss"), ("Cazador de maleficios", "Enfréntate a todas las ciegas jefe"),
                   ("Caçador de maldições", "Enfrente todos os Blinds Chefes"), ("Cacciatore di malefici", "Affronta ogni buio boss"), ("صائد اللعنات", "واجه كل رهانات الزعماء")],
    "slim_pickings": [("精简", "牌组中只剩 20 张或更少的牌"), ("少数精鋭", "デッキのカードを 20 枚以下にする"), ("소수 정예", "덱에 카드 20장 이하 남기기"),
                      ("Magere Auswahl", "Habe 20 oder weniger Karten im Deck"), ("Maigre récolte", "Avoir 20 cartes ou moins dans son paquet"), ("Lo justo", "Ten 20 cartas o menos en tu baraja"),
                      ("O mínimo", "Tenha 20 cartas ou menos no baralho"), ("Il minimo", "Avere 20 carte o meno nel mazzo"), ("الحد الأدنى", "امتلك 20 ورقة أو أقل في رزمتك")],
    "overstuffed": [("塞满", "牌组中有 80 张或更多的牌"), ("ぎゅうぎゅう", "デッキのカードを 80 枚以上にする"), ("꽉 찬 덱", "덱에 카드 80장 이상 모으기"),
                    ("Vollgestopft", "Habe 80 oder mehr Karten im Deck"), ("Bourré à craquer", "Avoir 80 cartes ou plus dans son paquet"), ("A reventar", "Ten 80 cartas o más en tu baraja"),
                    ("Lotado", "Tenha 80 cartas ou mais no baralho"), ("Strapieno", "Avere 80 carte o più nel mazzo"), ("مكتظّة", "امتلك 80 ورقة أو أكثر في رزمتك")],
    "no_takebacks": [("落子无悔", "不刷新商店赢得一局"), ("後戻りなし", "ショップをリロールせずにランに勝利する"), ("무르기 없음", "상점을 새로고침하지 않고 런에서 승리하기"),
                     ("Kein Zurück", "Gewinne einen Lauf ohne Neuwürfeln im Laden"), ("Pas de retour", "Gagner une partie sans relancer la boutique"), ("Sin vuelta atrás", "Gana una partida sin renovar la tienda"),
                     ("Sem volta", "Vença uma partida sem renovar a loja"), ("Niente ripensamenti", "Vinci una partita senza rinnovare il negozio"), ("لا تراجع", "افز بجولة دون تحديث المتجر")],
    "rule_bender": [("规则变通者", "赢得一个挑战"), ("ルールを曲げる者", "チャレンジに勝利する"), ("규칙 비틀기", "도전 하나 승리하기"),
                    ("Regelbieger", "Gewinne eine Herausforderung"), ("Contourneur de règles", "Remporter un défi"), ("Saltarse las reglas", "Gana un desafío"),
                    ("Dobrando as regras", "Vença um desafio"), ("Piegare le regole", "Vinci una sfida"), ("مُطوِّع القواعد", "افز بتحدٍّ واحد")],
    "rule_breaker": [("规则破坏者", "赢得所有挑战"), ("ルールを破る者", "すべてのチャレンジに勝利する"), ("규칙 파괴자", "모든 도전 승리하기"),
                     ("Regelbrecher", "Gewinne alle Herausforderungen"), ("Briseur de règles", "Remporter tous les défis"), ("Romper las reglas", "Gana todos los desafíos"),
                     ("Quebrando as regras", "Vença todos os desafios"), ("Infrangere le regole", "Vinci tutte le sfide"), ("كاسر القواعد", "افز بكل التحديات")],
    "five_figures": [("五位数", "单手得分达到 10000"), ("5 桁", "1 回のハンドで 10000 点を獲得する"), ("다섯 자리", "한 핸드에서 10000점 얻기"),
                     ("Fünfstellig", "Erziele 10.000 Punkte mit einer Hand"), ("Cinq chiffres", "Marquer 10 000 en une main"), ("Cinco cifras", "Consigue 10.000 en una mano"),
                     ("Cinco dígitos", "Faça 10.000 em uma mão"), ("Cinque cifre", "Ottieni 10.000 in una mano"), ("خمس خانات", "سجّل 10000 في يد واحدة")],
    "millionaire": [("百万富翁", "单手得分达到 100万"), ("ミリオネア", "1 回のハンドで 100万点を獲得する"), ("백만장자", "한 핸드에서 100만 점 얻기"),
                    ("Millionär", "Erziele 1 Million Punkte mit einer Hand"), ("Millionnaire", "Marquer 1 million en une main"), ("Millonario", "Consigue 1 millón en una mano"),
                    ("Milionário", "Faça 1 milhão em uma mão"), ("Milionario", "Ottieni 1 milione in una mano"), ("المليونير", "سجّل مليون نقطة في يد واحدة")],
    "astronomical": [("天文数字", "单手得分达到 1亿"), ("天文学的", "1 回のハンドで 1億点を獲得する"), ("천문학적", "한 핸드에서 1억 점 얻기"),
                     ("Astronomisch", "Erziele 100 Millionen Punkte mit einer Hand"), ("Astronomique", "Marquer 100 millions en une main"), ("Astronómico", "Consigue 100 millones en una mano"),
                     ("Astronômico", "Faça 100 milhões em uma mão"), ("Astronomico", "Ottieni 100 milioni in una mano"), ("رقم فلكي", "سجّل 100 مليون نقطة في يد واحدة")],
    "deck_master": [("牌组大师", "用每种牌组各赢一局"), ("デッキマスター", "すべてのデッキでランに勝利する"), ("덱 마스터", "모든 덱으로 런에서 승리하기"),
                    ("Deckmeister", "Gewinne mit jedem Deck einen Lauf"), ("Maître des paquets", "Gagner une partie avec chaque paquet"), ("Maestro de barajas", "Gana una partida con cada baraja"),
                    ("Mestre dos baralhos", "Vença uma partida com cada baralho"), ("Maestro dei mazzi", "Vinci una partita con ogni mazzo"), ("سيّد الرزم", "افز بجولة بكل رزمة")],
    "five_alive": [("五连活力", "打出同花五条"), ("ファイブアライブ", "フラッシュファイブをプレイする"), ("다섯의 힘", "플러시 파이브 플레이하기"),
                   ("Fünf am Leben", "Spiele einen Flush-Fünfling"), ("Cinq en vie", "Jouer une quinte couleur"), ("Cinco con vida", "Juega un color quíntuple"),
                   ("Cinco vivos", "Jogue um flush quíntuplo"), ("Cinque vivi", "Gioca un colore quintuplo"), ("خمسة أحياء", "العب فلاش خماسي")],
    "big_spender": [("挥金如土", "在商店中花费 $2500"), ("大盤振る舞い", "ショップで $2500 使う"), ("큰손", "상점에서 $2500 쓰기"),
                    ("Großzügig", "Gib $2.500 in Läden aus"), ("Panier percé", "Dépenser 2 500 $ en boutique"), ("Derrochador", "Gasta $2.500 en tiendas"),
                    ("Gastador", "Gaste $2.500 em lojas"), ("Spendaccione", "Spendi $2.500 nei negozi"), ("المبذّر", "أنفق 2500$ في المتاجر")],
    # leaderboards
    "best_hand": [("最佳牌型", "单手最高得分"), ("ベストハンド", "1 回のハンドでの最高得点"), ("최고의 핸드", "한 핸드 최고 점수"),
                  ("Beste Hand", "Höchste Punktzahl mit einer Hand"), ("Meilleure main", "Meilleur score en une seule main"), ("Mejor mano", "Mayor puntuación en una sola mano"),
                  ("Melhor mão", "Maior pontuação em uma única mão"), ("Mano migliore", "Punteggio più alto in una sola mano"), ("أفضل يد", "أعلى نتيجة في يد واحدة")],
    "highest_ante": [("最高底注", "单局到达的最高底注"), ("最高アンティ", "1 回のランで到達した最高アンティ"), ("최고 앤티", "한 런에서 도달한 최고 앤티"),
                     ("Höchste Ante", "Höchste in einem Lauf erreichte Ante"), ("Mise la plus haute", "Mise la plus haute atteinte en une partie"), ("Ante más alto", "Ante más alto alcanzado en una partida"),
                     ("Maior ante", "Maior ante alcançado em uma partida"), ("Ante più alto", "Ante più alto raggiunto in una partita"), ("أعلى مرحلة", "أعلى مرحلة وصلت إليها في جولة")],
    "fastest_win": [("最快胜利", "赢得一局所用的最少回合"), ("最速勝利", "ランに勝利するまでの最少ラウンド数"), ("최단 승리", "런 승리까지 가장 적은 라운드"),
                    ("Schnellster Sieg", "Wenigste Runden bis zum Sieg"), ("Victoire la plus rapide", "Moins de manches pour gagner une partie"), ("Victoria más rápida", "Menos rondas para ganar una partida"),
                    ("Vitória mais rápida", "Menos rodadas para vencer uma partida"), ("Vittoria più rapida", "Meno round per vincere una partita"), ("أسرع فوز", "أقل عدد من الدورات للفوز بجولة")],
    "career_wins": [("生涯胜场", "赢得的局数"), ("通算勝利数", "勝利したランの数"), ("통산 승리", "승리한 런 수"),
                    ("Siege gesamt", "Gewonnene Läufe"), ("Victoires en carrière", "Parties gagnées"), ("Victorias totales", "Partidas ganadas"),
                    ("Vitórias na carreira", "Partidas vencidas"), ("Vittorie in carriera", "Partite vinte"), ("الانتصارات الكلية", "الجولات التي فزت بها")],
}


def read_gd():
    src = (ROOT / "scripts" / "achievements.gd").read_text()
    entry = re.compile(r'\{"key": "(\w+)", "name": "([^"]+)", "desc": "([^"]+)"(.*?)\},?\n')
    achs, boards = [], []
    lb_start = src.index("const LEADERBOARDS")
    for m in entry.finditer(src):
        key, name, desc, rest = m.groups()
        row = {"key": key, "name": name, "desc": desc}
        if m.start() < lb_start:
            row["points"] = int(re.search(r'"points": (\d+)', rest).group(1))
            steps = '"steps": true' in rest
            row["steps"] = int(re.search(r'"n": (\d+)', rest).group(1)) if steps else 0
            achs.append(row)
        else:
            row["low"] = '"low": true' in rest
            boards.append(row)
    return achs, boards


def res_name(prefix, name):
    n = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return prefix + n


def main():
    achs, boards = read_gd()
    assert sum(a["points"] for a in achs) <= 1000
    with open(HERE / "achievements.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order", "key", "name", "description", "points", "incremental steps", "initial state", "icon", "resource name"])
        for i, a in enumerate(achs, 1):
            w.writerow([i, a["key"], a["name"], a["desc"], a["points"], a["steps"] or "", "Revealed",
                        f"icons/achievements/{a['key']}.png", res_name("achievement_", a["name"])])
    with open(HERE / "leaderboards.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key", "name", "description", "score format", "ordering", "icon", "resource name"])
        for b in boards:
            w.writerow([b["key"], b["name"], b["desc"], "Numeric (no decimals)",
                        "Smaller is better" if b["low"] else "Larger is better",
                        f"icons/leaderboards/{b['key']}.png", res_name("leaderboard_", b["name"])])
    with open(HERE / "translations.csv", "w", newline="") as f:
        w = csv.writer(f)
        head = ["key", "en-US name", "en-US description"]
        for lang in LANGS:
            head += [f"{lang} name", f"{lang} description"]
        w.writerow(head)
        for a in achs + boards:
            row = [a["key"], a["name"], a["desc"]]
            tr = T[a["key"]]
            assert len(tr) == len(LANGS), a["key"]
            for name, desc in tr:
                assert len(name) <= 100 and len(desc) <= 500
                row += [name, desc]
            w.writerow(row)
    print(f"{len(achs)} achievements ({sum(a['points'] for a in achs)} points), {len(boards)} leaderboards, {len(LANGS)} languages")
    build_import(achs)
    write_leaderboards_md(boards)


LANG_NAMES = {"zh-CN": "Chinese (Simplified)", "ja-JP": "Japanese", "ko-KR": "Korean", "de-DE": "German",
              "fr-FR": "French", "es-ES": "Spanish (Spain)", "pt-BR": "Portuguese (Brazil)",
              "it-IT": "Italian", "ar": "Arabic"}

# Play Console fields the game's data doesn't hold. A run is won after 8
# antes; skipped blinds don't count as rounds and Boss Blinds can't be
# skipped, so no win takes fewer than 8 rounds. Endless mode goes past ante 8.
BOARD_LIMITS = {
    "best_hand": ("1", "", "The best single-hand score of your career (Career stats: Best hand)."),
    "highest_ante": ("1", "", "The highest ante reached, endless mode included."),
    "fastest_win": ("8", "", "Rounds played in your fastest winning run. Skipped blinds don't count."),
    "career_wins": ("1", "", "Every run you've won."),
}


def write_leaderboards_md(boards):
    lines = ["# Leaderboards for Play Console", "",
             "Play Console has no import for leaderboards, so add these four by hand:",
             "**Play Games Services > Setup and management > Leaderboards > Add leaderboard**.",
             "Enter them in this order. That makes it the list order.", "",
             "Every leaderboard uses the same settings:", "",
             "- **Score formatting**: Numeric, 0 decimal places, no custom unit.",
             "- **Enable tamper protection**: on.",
             "- **Icon**: the file named below, from `icons/leaderboards/` (512×512, no text).", "",
             "The game sends each score when you sign in and whenever it improves.", "",
             "Keep each **English name** exactly as written. The game finds the",
             "leaderboard's ID by its resource name (shown below) in the Get resources file.", ""]
    for n, b in enumerate(boards, 1):
        low, high, note = BOARD_LIMITS[b["key"]]
        lines += [f"## {n}. {b['name']}", "",
                  "| Field | Value |", "|---|---|",
                  f"| Name | {b['name']} |",
                  f"| Description | {b['desc']} |",
                  f"| Icon | `{b['key']}.png` |",
                  f"| Ordering | {'Smaller is better' if b['low'] else 'Larger is better'} |",
                  f"| Score format | Numeric, 0 decimal places |",
                  f"| Lower limit | {low} |",
                  f"| Upper limit | {high or '(none)'} |",
                  f"| Tamper protection | On |",
                  f"| List order | {n} |",
                  f"| Resource name | `{res_name('leaderboard_', b['name'])}` |", "",
                  f"What it records: {note}", "",
                  "**Translations** (Add translation, then one per language):", "",
                  "| Language | Name | Description |", "|---|---|---|"]
        for li, lang in enumerate(LANGS):
            name, desc = T[b["key"]][li]
            lines.append(f"| {LANG_NAMES[lang]} `{lang}` | {name} | {desc} |")
        lines.append("")
    lines += ["## After adding them", "",
              "Click **Get resources > Android** (on the Leaderboards or Achievements page; it's the",
              "same file) and paste it into `res://pgs/games-ids.xml`. Then build.", ""]
    (HERE / "LEADERBOARDS.md").write_text("\n".join(lines), encoding="utf-8")


def plain_row(values):
    """One import CSV line: Play Console's format has no quoting, so no field may hold a comma."""
    for v in values:
        assert "," not in str(v) and "\n" not in str(v), v
    return ",".join(str(v) for v in values) + "\n"


def build_import(achs):
    out = HERE / "achievements_import"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    names = [a["name"] for a in achs]
    assert len(set(names)) == len(names)
    with open(out / "AchievementsMetadata.csv", "w", encoding="utf-8", newline="") as f:
        for i, a in enumerate(achs, 1):
            assert len(a["name"]) <= 100 and len(a["desc"]) <= 500
            assert a["points"] % 5 == 0 and 5 <= a["points"] <= 200
            assert a["steps"] <= 10000
            f.write(plain_row([a["name"], a["desc"], "True" if a["steps"] else "False", a["steps"] or "",
                               "Revealed", a["points"], i]))
    with open(out / "AchievementsLocalizations.csv", "w", encoding="utf-8", newline="") as f:
        for li, lang in enumerate(LANGS):
            seen = set()
            for a in achs:
                name, desc = T[a["key"]][li]
                assert name not in seen, (lang, name)
                seen.add(name)
                f.write(plain_row([a["name"], name, desc, lang]))
    with open(out / "AchievementsIconsMappings.csv", "w", encoding="utf-8", newline="") as f:
        for a in achs:
            icon = f"{a['key']}.png"
            shutil.copy(HERE / "icons" / "achievements" / icon, out / icon)
            assert (out / icon).stat().st_size < 1_000_000
            f.write(plain_row([a["name"], icon]))
    # with translations (every locale must first be added to the game's
    # Play Games configuration), and without, for importing before that
    for zname, skip in (("AchievementsImport.zip", None),
                        ("AchievementsImport-no-translations.zip", "AchievementsLocalizations.csv")):
        zpath = HERE / zname
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(out.iterdir()):
                if p.name != skip:
                    z.write(p, p.name)  # flat: no folders inside the zip
        files = len(z.namelist())
        assert files <= 403
        print(f"{zpath.name}: {files} files, {zpath.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
