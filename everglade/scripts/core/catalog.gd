class_name Catalog
extends RefCounted
## Static game data: prop families, colour palettes and building presets.

const FLOOR_H := 2.5
const PLINTH := 0.45

const TREES := ["tree_round_a", "tree_round_c", "tree_round_b", "tree_birch", "tree_pine_a", "tree_pine_b", "tree_cedar"]
const BROADLEAF := ["tree_round_a", "tree_round_c", "tree_birch"]
const GRAND := ["tree_round_b"]
const PINES := ["tree_pine_a", "tree_pine_b", "tree_cedar"]
const BUSHES := ["bush_a", "bush_b", "bush_berries"]
const FLOWERS := ["flowers_pink", "flowers_white", "flowers_blue", "flowers_yellow", "flowers_red"]
const ROCKS := ["rock_a", "rock_b", "rock_c", "mushrooms", "stump"]

## Nature brush families: kinds, spacing (m), scale range.
const NATURE := {
	"forest": {"label": "Forest", "kinds": TREES, "spacing": 2.4, "scale": Vector2(0.8, 1.2)},
	"broadleaf": {"label": "Leafy", "kinds": BROADLEAF, "spacing": 2.6, "scale": Vector2(0.85, 1.3)},
	"grand": {"label": "Great oak", "kinds": GRAND, "spacing": 5.0, "scale": Vector2(0.9, 1.2)},
	"pines": {"label": "Firs", "kinds": PINES, "spacing": 2.2, "scale": Vector2(0.8, 1.3)},
	"bushes": {"label": "Bushes", "kinds": BUSHES, "spacing": 1.1, "scale": Vector2(0.8, 1.3)},
	"flowers": {"label": "Flowers", "kinds": FLOWERS, "spacing": 0.55, "scale": Vector2(0.8, 1.3)},
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
}

## Props with moving parts, drawn as individual animated nodes.
const ANIMATED := ["windmill"]

const ROOF_COLORS := [
	Color(0.24, 0.56, 0.62), Color(0.86, 0.38, 0.26), Color(0.30, 0.44, 0.70),
	Color(0.34, 0.60, 0.44), Color(0.56, 0.42, 0.72), Color(0.30, 0.32, 0.38),
	Color(0.92, 0.70, 0.34), Color(0.64, 0.30, 0.22),
]

const WALL_COLORS := [
	Color(0.98, 0.96, 0.90), Color(1.0, 0.92, 0.80), Color(0.92, 0.96, 1.0),
	Color(1.0, 0.90, 0.88), Color(0.92, 0.96, 0.86), Color(0.88, 0.80, 0.68),
]

const STONE_COLORS := [
	Color(0.88, 0.85, 0.78), Color(0.92, 0.84, 0.72), Color(0.74, 0.76, 0.80),
	Color(0.86, 0.76, 0.66), Color(0.78, 0.82, 0.72),
]

const RECT_ROOFS := ["gable", "hip", "flat"]
const ROUND_ROOFS := ["cone", "flat"]
const STYLES := ["windrise", "plaster", "timber", "stone"]
const ROOF_LABELS := {"gable": "Gable", "hip": "Hipped", "flat": "Battlement", "cone": "Spire"}

const PATH_STYLES := ["dirt", "cobble", "stones"]


static func pick(arr: Array, rng: RandomNumberGenerator) -> Variant:
	return arr[rng.randi() % arr.size()]
