# Aleatro colour system: Velvet Lounge

A smoky late-night card parlour: a plum velvet table, dark violet panels,
teal Chips against rose Mult, brass for money and titles, and a four-colour
poker deck. Every role colour lives in **`scripts/palette.gd`** (`Palette.*`);
use those names instead of new hex literals.

Item art keeps its own colours on purpose: charms, vouchers, tags, boss
blinds, deck backs, packs, stake chips, seals and enhancements.

## The palette

| Role | Name | HEX |
|---|---|---|
| Table felt (primary background) | `TABLE` | `#4F3A78` |
| Table dark / menus / burn rim | `TABLE_DARK` | `#2E2440` |
| Table after a win | `TABLE_WON` | `#5E4A7A` |
| Panels (secondary background) | `PANEL` | `#2B2238` |
| Wells, shop sign | `PANEL_DEEP` | `#241D30` |
| Recessed slots | `PANEL_DEEPER` | `#1D1826` |
| Shop shelves | `PANEL_WELL` | `#352B47` |
| Panel line | `PANEL_LINE` | `#57486E` |
| Main accent: Chips, Play, Small Blind | `TEAL` | `#169488` |
| Second accent: Mult, Discard | `ROSE` | `#D63F75` |
| Money, titles' gold | `BRASS` | `#F2C14E` |
| Big Blind, Buy, Cash Out | `COPPER` | `#C9772E` |
| Sort buttons | `VIOLET` | `#8A5AD0` |
| xMult | `XMULT` | `#F07B2B` |
| The "x" between Chips and Mult | `MULT_LIGHT` | `#E86A96` |
| Omen packs | `INDIGO` | `#4A4FB8` |
| Neutral button | `BUTTON` | `#5D5373` |
| Dim button (arrows, idle tabs) | `BUTTON_DIM` | `#4A4060` |
| Option toggles | `BUTTON_OPTION` | `#6A5A9E` |
| Use / Sell / Continue / Reroll | `GO` (`JADE`) | `#2A9070` |
| Watch ad, Remove ads | `AD` | `#A8761C` |
| Challenges, Start, shop rim, card back | `WINE` | `#8E2F5E` |
| Text | `TEXT` | `#FFF8EE` (labels use white with a dark outline) |
| Secondary text | `TEXT_SUB` | `#CFC3DD` |
| Headings | `HEADING` | `#F5CB5C` |
| Text on paper | `INK` / `INK_SOFT` | `#2A2430` / `#5E5470` |
| Card face, tooltips | `PAPER` (`CARD_FACE`) | `#F6EFE3` |
| Card border | `CARD_EDGE` | `#CBBBA4` |
| Selected card, highlight | `CARD_SELECT` (`HIGHLIGHT`) | `#FFE08A` |
| Glow | `GLOW` | `#6FE3D6` |
| Success | `SUCCESS` | `#2A9070` |
| Warning | `WARNING` (`AMBER`) | `#F0A33A` |
| Danger | `DANGER` | `#C8374A` |
| Suits ♠ ♥ ♣ ♦ | `SUITS` | `#2A2733` `#D42A35` `#1D8443` `#2B6FD6` |
| Rarity: common, uncommon, rare, legendary | `RARITY` | `#5C6F8E` `#2A9070` `#C9772E` `#B04BD6` |

## Contrast (WCAG)

| Pair | Ratio |
|---|---|
| Text on panels / on the table | 14.3 : 1 / 9.8 : 1 |
| White on teal / rose / violet / jade | 3.7 / 4.4 / 4.7 / 4.0 (large outlined labels need 3) |
| Suits on the card face ♠ ♥ ♣ ♦ | 12.8 / 4.4 / 4.1 / 4.2 |

## What changed from the borrowed palette

- **15 values identical to Balatro's colour table are gone:** `#009DFF`,
  `#FE5F55`, `#374244`, `#4F6367`, `#50846E`, `#4BC292`, `#FDA200`, `#FF9A00`,
  `#8867A5`, `#A782D1`, `#13AFCE`, `#4584FA`, `#FD682B`, `#646EB7` and
  `#B26CBB`.
- **Table:** green felt became plum. The title and splash swirl went from red
  and blue to rose and teal.
- **Scoring:** blue Chips and red Mult became teal and rose. Play and Discard follow.
- **Panels:** blue-grey slate became dark violet.
- **Blinds:** blue and gold became teal and copper.
- **Sort buttons:** orange became violet.
- **Suits:** a four-colour poker deck (green clubs, blue diamonds). The 16
  painted J/Q/K/A faces were recoloured to match
  (`tools/palette/recolor_courts.py`).
- **Rarities and the tags that name them** (Uncommon, Rare, Bundle, Top-up)
  and the Charm Pack: slate, jade, copper, orchid.
- **Shaders:** new defaults for the background, flame, splash and burn edge.
- **App icon:** the swirl moved from red and blue to rose, teal and plum; the
  Ace of Hearts card is untouched (`tools/palette/recolor_icon.py`). The Play
  Games icon and feature graphic were regenerated.

## Still to redesign by hand (not colour)

- **Charm cards are printed "JOKER"** down both sides (152 images in
  `assets/charms_pixel`), and they show in the feature graphic and every
  store screenshot.
- **Stakes** (White, Red, Green, Black, Blue, Purple, Orange, Gold chips) and
  **seals** (red, gold, blue, purple) keep their colours, the same coding
  Balatro uses. Recolouring the stakes means renaming them in 10 languages.
- **Achievement icons** (`tools/play_games/make_icons.py`) were drawn in the
  old colours and are already uploaded to Play Console.
- **Logo and UI font:** m6x11plus, the same pixel font Balatro uses.
