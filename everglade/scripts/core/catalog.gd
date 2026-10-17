class_name Catalog
extends RefCounted
## Static game data: prop families, colour palettes and building presets.

const FLOOR_H := 2.5
const PLINTH := 0.45

const TREES := ["tree_round_a", "tree_round_c", "tree_round_b", "tree_birch", "tree_golden", "tree_teal"]
const BROADLEAF := ["tree_round_a", "tree_round_c", "tree_birch"]
const GRAND := ["tree_round_b"]
const GOLDEN := ["tree_golden", "tree_orange", "tree_golden", "bush_golden"]
const BLOSSOM := ["tree_blossom", "tree_teal", "tree_blossom"]
const BUSHES := ["bush_a", "bush_b", "bush_berries", "bush_golden"]
const FLOWERS := ["flowers_pink", "flowers_white", "flowers_blue", "flowers_yellow", "flowers_red", "flowers_lavender"]
const LAVENDER := ["flowers_lavender", "flowers_lavender", "flowers_white", "flowers_yellow"]
const FERNS := ["fern", "fern", "plant_leafy", "wheat"]
const ROCKS := ["rock_a", "rock_b", "rock_c", "rock_big", "mushrooms", "stump"]
const MEADOW := ["flowers_red", "flowers_yellow", "flowers_blue", "flowers_white", "flowers_pink", "wheat"]
const GRAIN := ["wheat", "wheat", "wheat", "flowers_red"]

## Nature brush families: kinds, spacing (m), scale range.
const NATURE := {
	"forest": {"label": "Forest", "kinds": TREES, "spacing": 2.4, "scale": Vector2(0.8, 1.2)},
	"broadleaf": {"label": "Leafy", "kinds": BROADLEAF, "spacing": 2.6, "scale": Vector2(0.85, 1.3)},
	"grand": {"label": "Great oak", "kinds": GRAND, "spacing": 5.0, "scale": Vector2(0.9, 1.2)},
	"golden": {"label": "Golden", "kinds": GOLDEN, "spacing": 2.8, "scale": Vector2(0.85, 1.25)},
	"blossom": {"label": "Blossom", "kinds": BLOSSOM, "spacing": 2.8, "scale": Vector2(0.85, 1.2)},
	"bushes": {"label": "Bushes", "kinds": BUSHES, "spacing": 1.1, "scale": Vector2(0.8, 1.3)},
	"flowers": {"label": "Flowers", "kinds": FLOWERS, "spacing": 0.55, "scale": Vector2(0.8, 1.3)},
	"lavender": {"label": "Lavender", "kinds": LAVENDER, "spacing": 0.5, "scale": Vector2(0.9, 1.4)},
	"ferns": {"label": "Ferns", "kinds": FERNS, "spacing": 0.7, "scale": Vector2(0.8, 1.3)},
	"meadow": {"label": "Meadow", "kinds": MEADOW, "spacing": 0.45, "scale": Vector2(0.8, 1.3)},
	"grain": {"label": "Grain", "kinds": GRAIN, "spacing": 0.4, "scale": Vector2(0.9, 1.3)},
	"rocks": {"label": "Rocks", "kinds": ROCKS, "spacing": 1.2, "scale": Vector2(0.6, 1.4)},
}

## Placeable decorations: label, sits on slopes aligned to ground.
const DECOR := {
	"lantern": {"label": "Street lamp", "align": false},
	"paper_lantern": {"label": "Plaza lamp", "align": false},
	"windmill": {"label": "Windmill", "align": false},
	"fountain": {"label": "Fountain", "align": false},
	"wind_shrine": {"label": "Wind shrine", "align": false},
	"market_stall": {"label": "Market stall", "align": false},
	"flower_cart": {"label": "Flower cart", "align": true},
	"well": {"label": "Well", "align": false},
	"bench": {"label": "Bench", "align": false},
	"banner": {"label": "Banner", "align": false},
	"signpost": {"label": "Signpost", "align": false},
	"notice_board": {"label": "Notice board", "align": false},
	"barrel": {"label": "Wine barrels", "align": false},
	"crate": {"label": "Apples", "align": false},
	"cart": {"label": "Cart", "align": true},
	"haystack": {"label": "Haystack", "align": true},
	"hay_bale": {"label": "Hay bale", "align": true},
	"scarecrow": {"label": "Scarecrow", "align": false},
	"log_pile": {"label": "Logs", "align": true},
	"stump": {"label": "Stump", "align": true},
	"mushrooms": {"label": "Mushrooms", "align": true},
	"cafe_table": {"label": "Café table", "align": false},
	"planter": {"label": "Planter", "align": false},
	"ruin_arch": {"label": "Ruin arch", "align": false},
	"ruin_wall": {"label": "Ruin wall", "align": false},
	"ruin_pillar": {"label": "Ruin pillar", "align": false},
	"ruin_slab": {"label": "Fallen slab", "align": true},
	"rotunda": {"label": "Rotunda", "align": false},
	"rock_big": {"label": "Boulder", "align": true},
	"stone_lantern": {"label": "Stone lantern", "align": false},
	"tea_terrace": {"label": "Tea terrace", "align": true},
	"bamboo_raft": {"label": "Bamboo raft", "align": false, "float": true},
}

## Props with moving parts, drawn as individual animated nodes.
const ANIMATED := ["windmill"]

# muted, natural palette: slate, terracotta, warm brown, moss, ochre...
const ROOF_COLORS := [
	Color(0.40, 0.46, 0.50), Color(0.64, 0.34, 0.26), Color(0.50, 0.38, 0.28),
	Color(0.44, 0.50, 0.40), Color(0.50, 0.44, 0.50), Color(0.21, 0.23, 0.27),
	Color(0.70, 0.56, 0.34), Color(0.54, 0.30, 0.22),
]

# warm off-white, cream, pale grey, blush, sage and ochre limewash
const WALL_COLORS := [
	Color(0.96, 0.91, 0.80), Color(0.95, 0.86, 0.68), Color(0.89, 0.87, 0.82),
	Color(0.94, 0.84, 0.76), Color(0.88, 0.89, 0.78), Color(0.88, 0.76, 0.56),
]

# pale limestone, warm sandstone, light grey, weathered dark, honey stone
const STONE_COLORS := [
	Color(0.79, 0.75, 0.65), Color(0.73, 0.65, 0.52), Color(0.66, 0.65, 0.62),
	Color(0.47, 0.46, 0.43), Color(0.76, 0.69, 0.56),
]

const RECT_ROOFS := ["gable", "hip", "flat"]
const ROUND_ROOFS := ["cone", "flat"]
const STYLES := ["windrise", "lakeside", "plaster", "timber", "stone", "wood", "boards"]
const ROOF_LABELS := {"gable": "Gable", "hip": "Hipped", "flat": "Battlement", "cone": "Spire"}

const PATH_STYLES := ["dirt", "cobble", "paved", "stones"]


static func pick(arr: Array, rng: RandomNumberGenerator) -> Variant:
	return arr[rng.randi() % arr.size()]
