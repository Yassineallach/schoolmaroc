class_name Catalog
extends RefCounted
## Static game data: prop families, colour palettes and building presets.

const FLOOR_H := 2.5
const PLINTH := 0.45

const TREES := ["tree_round_a", "tree_round_b", "tree_round_c", "tree_birch", "tree_pine_a", "tree_pine_b"]
const BROADLEAF := ["tree_round_a", "tree_round_b", "tree_round_c", "tree_birch"]
const PINES := ["tree_pine_a", "tree_pine_b"]
const BUSHES := ["bush_a", "bush_b", "bush_berries"]
const FLOWERS := ["flowers_pink", "flowers_white", "flowers_blue", "flowers_yellow", "flowers_red"]
const ROCKS := ["rock_a", "rock_b", "rock_c", "mushrooms", "stump"]

## Nature brush families: kinds, spacing (m), scale range.
const NATURE := {
	"forest": {"label": "Forest", "kinds": TREES, "spacing": 2.4, "scale": Vector2(0.8, 1.25)},
	"broadleaf": {"label": "Oaks", "kinds": BROADLEAF, "spacing": 2.6, "scale": Vector2(0.85, 1.3)},
	"pines": {"label": "Pines", "kinds": PINES, "spacing": 2.0, "scale": Vector2(0.8, 1.3)},
	"bushes": {"label": "Bushes", "kinds": BUSHES, "spacing": 1.1, "scale": Vector2(0.8, 1.3)},
	"flowers": {"label": "Flowers", "kinds": FLOWERS, "spacing": 0.55, "scale": Vector2(0.8, 1.3)},
	"rocks": {"label": "Rocks", "kinds": ROCKS, "spacing": 1.2, "scale": Vector2(0.6, 1.4)},
}

## Placeable decorations: label, base scale, sits on slopes aligned to ground.
const DECOR := {
	"lantern": {"label": "Lantern", "align": false},
	"well": {"label": "Well", "align": false},
	"bench": {"label": "Bench", "align": false},
	"haystack": {"label": "Haystack", "align": true},
	"hay_bale": {"label": "Hay bale", "align": true},
	"barrel": {"label": "Barrel", "align": false},
	"crate": {"label": "Crate", "align": false},
	"cart": {"label": "Cart", "align": true},
	"banner": {"label": "Banner", "align": false},
	"scarecrow": {"label": "Scarecrow", "align": false},
	"log_pile": {"label": "Logs", "align": true},
	"stump": {"label": "Stump", "align": true},
	"mushrooms": {"label": "Mushrooms", "align": true},
}

const ROOF_COLORS := [
	Color(0.70, 0.33, 0.25), Color(0.80, 0.50, 0.30), Color(0.33, 0.45, 0.62),
	Color(0.36, 0.52, 0.36), Color(0.52, 0.40, 0.58), Color(0.42, 0.40, 0.40),
	Color(0.86, 0.72, 0.40), Color(0.55, 0.30, 0.22),
]

const WALL_COLORS := [
	Color(0.96, 0.92, 0.83), Color(0.98, 0.86, 0.72), Color(0.90, 0.93, 0.95),
	Color(0.95, 0.85, 0.85), Color(0.86, 0.90, 0.80), Color(0.82, 0.76, 0.66),
]

const STONE_COLORS := [
	Color(0.78, 0.75, 0.70), Color(0.85, 0.80, 0.70), Color(0.66, 0.66, 0.68),
	Color(0.80, 0.68, 0.58), Color(0.72, 0.74, 0.66),
]

const RECT_ROOFS := ["gable", "hip", "flat"]
const ROUND_ROOFS := ["cone", "flat"]
const STYLES := ["plaster", "timber", "stone"]

const PATH_STYLES := ["dirt", "cobble", "stones"]


static func pick(arr: Array, rng: RandomNumberGenerator) -> Variant:
	return arr[rng.randi() % arr.size()]
