# Leaderboards for Play Console

Play Console has no import for leaderboards, so add these four by hand:
**Play Games Services > Setup and management > Leaderboards > Add leaderboard**.
Enter them in this order. That makes it the list order.

Every leaderboard uses the same settings:

- **Score formatting**: Numeric, 0 decimal places, no custom unit.
- **Enable tamper protection**: on.
- **Icon**: the file named below, from `icons/leaderboards/` (512×512, no text).

The game sends each score when you sign in and whenever it improves.

Keep each **English name** exactly as written. The game finds the
leaderboard's ID by its resource name (shown below) in the Get resources file.

## 1. Best Hand

| Field | Value |
|---|---|
| Name | Best Hand |
| Description | Highest score in a single hand |
| Icon | `best_hand.png` |
| Ordering | Larger is better |
| Score format | Numeric, 0 decimal places |
| Lower limit | 1 |
| Upper limit | (none) |
| Tamper protection | On |
| List order | 1 |
| Resource name | `leaderboard_best_hand` |

What it records: The best single-hand score of your career (Career stats: Best hand).

**Translations** (Add translation, then one per language):

| Language | Name | Description |
|---|---|---|
| Chinese (Simplified) `zh-CN` | 最佳牌型 | 单手最高得分 |
| Japanese `ja-JP` | ベストハンド | 1 回のハンドでの最高得点 |
| Korean `ko-KR` | 최고의 핸드 | 한 핸드 최고 점수 |
| German `de-DE` | Beste Hand | Höchste Punktzahl mit einer Hand |
| French `fr-FR` | Meilleure main | Meilleur score en une seule main |
| Spanish (Spain) `es-ES` | Mejor mano | Mayor puntuación en una sola mano |
| Portuguese (Brazil) `pt-BR` | Melhor mão | Maior pontuação em uma única mão |
| Italian `it-IT` | Mano migliore | Punteggio più alto in una sola mano |
| Arabic `ar` | أفضل يد | أعلى نتيجة في يد واحدة |

## 2. Highest Ante

| Field | Value |
|---|---|
| Name | Highest Ante |
| Description | Highest ante reached in a run |
| Icon | `highest_ante.png` |
| Ordering | Larger is better |
| Score format | Numeric, 0 decimal places |
| Lower limit | 1 |
| Upper limit | (none) |
| Tamper protection | On |
| List order | 2 |
| Resource name | `leaderboard_highest_ante` |

What it records: The highest ante reached, endless mode included.

**Translations** (Add translation, then one per language):

| Language | Name | Description |
|---|---|---|
| Chinese (Simplified) `zh-CN` | 最高底注 | 单局到达的最高底注 |
| Japanese `ja-JP` | 最高アンティ | 1 回のランで到達した最高アンティ |
| Korean `ko-KR` | 최고 앤티 | 한 런에서 도달한 최고 앤티 |
| German `de-DE` | Höchste Ante | Höchste in einem Lauf erreichte Ante |
| French `fr-FR` | Mise la plus haute | Mise la plus haute atteinte en une partie |
| Spanish (Spain) `es-ES` | Ante más alto | Ante más alto alcanzado en una partida |
| Portuguese (Brazil) `pt-BR` | Maior ante | Maior ante alcançado em uma partida |
| Italian `it-IT` | Ante più alto | Ante più alto raggiunto in una partita |
| Arabic `ar` | أعلى مرحلة | أعلى مرحلة وصلت إليها في جولة |

## 3. Fastest Win

| Field | Value |
|---|---|
| Name | Fastest Win |
| Description | Fewest rounds to win a run |
| Icon | `fastest_win.png` |
| Ordering | Smaller is better |
| Score format | Numeric, 0 decimal places |
| Lower limit | 8 |
| Upper limit | (none) |
| Tamper protection | On |
| List order | 3 |
| Resource name | `leaderboard_fastest_win` |

What it records: Rounds played in your fastest winning run. Skipped blinds don't count.

**Translations** (Add translation, then one per language):

| Language | Name | Description |
|---|---|---|
| Chinese (Simplified) `zh-CN` | 最快胜利 | 赢得一局所用的最少回合 |
| Japanese `ja-JP` | 最速勝利 | ランに勝利するまでの最少ラウンド数 |
| Korean `ko-KR` | 최단 승리 | 런 승리까지 가장 적은 라운드 |
| German `de-DE` | Schnellster Sieg | Wenigste Runden bis zum Sieg |
| French `fr-FR` | Victoire la plus rapide | Moins de manches pour gagner une partie |
| Spanish (Spain) `es-ES` | Victoria más rápida | Menos rondas para ganar una partida |
| Portuguese (Brazil) `pt-BR` | Vitória mais rápida | Menos rodadas para vencer uma partida |
| Italian `it-IT` | Vittoria più rapida | Meno round per vincere una partita |
| Arabic `ar` | أسرع فوز | أقل عدد من الدورات للفوز بجولة |

## 4. Career Wins

| Field | Value |
|---|---|
| Name | Career Wins |
| Description | Runs won |
| Icon | `career_wins.png` |
| Ordering | Larger is better |
| Score format | Numeric, 0 decimal places |
| Lower limit | 1 |
| Upper limit | (none) |
| Tamper protection | On |
| List order | 4 |
| Resource name | `leaderboard_career_wins` |

What it records: Every run you've won.

**Translations** (Add translation, then one per language):

| Language | Name | Description |
|---|---|---|
| Chinese (Simplified) `zh-CN` | 生涯胜场 | 赢得的局数 |
| Japanese `ja-JP` | 通算勝利数 | 勝利したランの数 |
| Korean `ko-KR` | 통산 승리 | 승리한 런 수 |
| German `de-DE` | Siege gesamt | Gewonnene Läufe |
| French `fr-FR` | Victoires en carrière | Parties gagnées |
| Spanish (Spain) `es-ES` | Victorias totales | Partidas ganadas |
| Portuguese (Brazil) `pt-BR` | Vitórias na carreira | Partidas vencidas |
| Italian `it-IT` | Vittorie in carriera | Partite vinte |
| Arabic `ar` | الانتصارات الكلية | الجولات التي فزت بها |

## After adding them

Click **Get resources > Android** (on the Leaderboards or Achievements page; it's the
same file) and paste it into `res://pgs/games-ids.xml`. Then build.
