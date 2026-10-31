class_name Palette
extends RefCounted

## Aleatro's colour system, "Velvet Lounge": a plum card-room table, dark
## violet panels, teal Chips against rose Mult, brass for money and titles,
## and a four-colour poker deck. Every role colour the UI uses lives here;
## item art (charms, tags, bosses, decks, packs) keeps its own colours.

# ---------------------------------------------------------------- table
## The felt during a blind; the swirl shader brightens and darkens it.
const TABLE := Color("4f3a78")
## The dark the table falls back to (menus, packs, boss blends).
const TABLE_DARK := Color("2e2440")
## The table after winning a run.
const TABLE_WON := Color("5e4a7a")

# ---------------------------------------------------------------- accents
const TEAL := Color("169488")  # main accent: Chips, Play, Small Blind
const ROSE := Color("d63f75")  # second accent: Mult, Discard
const BRASS := Color("f2c14e")  # money, titles, rewards
const COPPER := Color("c9772e")  # Big Blind, buying, cashing out
const VIOLET := Color("8a5ad0")  # sorting, secondary actions
const AMBER := Color("f0a33a")  # xMult, warnings, sparks
const INDIGO := Color("4a4fb8")  # omen packs
const JADE := Color("2a9070")  # confirm, success

# ---------------------------------------------------------------- scoring
const CHIPS := TEAL
const MULT := ROSE
const MULT_LIGHT := Color("e86a96")  # the "x" between the boxes
const XMULT := Color("f07b2b")
const MONEY := BRASS

# ---------------------------------------------------------------- panels
const PANEL := Color("2b2238")  # modal and info boxes
const PANEL_DEEP := Color("241d30")  # wells, shop sign
const PANEL_DEEPER := Color("1d1826")  # recessed slots
const PANEL_WELL := Color("352b47")  # shop shelves
const PANEL_LINE := Color("57486e")

# ---------------------------------------------------------------- buttons
const BUTTON := Color("5d5373")  # neutral: Close, Back, Menu
const BUTTON_DIM := Color("4a4060")  # paging arrows, idle tabs
const BUTTON_OPTION := Color("6a5a9e")  # option toggles
const PLAY := TEAL
const DISCARD := ROSE
const SORT := VIOLET
const GO := JADE  # Use, Sell, Continue, Reroll
const BUY := COPPER
const AD := Color("a8761c")  # watch-an-ad and Remove ads
const WINE := Color("8e2f5e")  # Challenges, Start, the shop sign's rim

# ---------------------------------------------------------------- text
const TEXT := Color("fff8ee")
const TEXT_SUB := Color("cfc3dd")
const HEADING := Color("f5cb5c")
const HEADING_RIM := WINE  # outline under the logo and the shop title
## Text on paper (tooltips, the mascot's speech).
const INK := Color("2a2430")
const INK_SOFT := Color("5e5470")
const PAPER := Color("f6efe3")

# ---------------------------------------------------------------- cards
const CARD_FACE := PAPER
const CARD_EDGE := Color("cbbba4")
const CARD_SELECT := Color("ffe08a")
const CARD_BACK := WINE
## A four-colour poker deck: black spades, red hearts, green clubs, blue diamonds.
const SUITS := [Color("2a2733"), Color("d42a35"), Color("1d8443"), Color("2b6fd6")]

# ---------------------------------------------------------------- blinds
const SMALL_BLIND := TEAL
const BIG_BLIND := COPPER

# ---------------------------------------------------------------- rarity
## common, uncommon, rare, legendary
const RARITY := [Color("5c6f8e"), JADE, COPPER, Color("b04bd6")]

# ---------------------------------------------------------------- states and light
const SUCCESS := JADE
const WARNING := AMBER
const DANGER := Color("c8374a")
const HIGHLIGHT := CARD_SELECT
const GLOW := Color("6fe3d6")
## A card burning away: rim and glow.
const BURN_RIM := TABLE_DARK
const BURN_GLOW := AMBER
