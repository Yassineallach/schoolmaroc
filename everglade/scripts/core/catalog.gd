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

## Placeable decorations: picker category, label, sits on slopes aligned to ground.
const DECOR_CATS := [["clutter", "Clutter"], ["market", "Market"], ["farm", "Farm"], ["lights", "Lights"],
		["landmarks", "Landmarks"], ["ruins", "Ruins"]]
const DECOR := {
	"lantern": {"cat": "lights", "label": "Street lamp", "align": false},
	"paper_lantern": {"cat": "lights", "label": "Plaza lamp", "align": false},
	"windmill": {"cat": "landmarks", "label": "Windmill", "align": false},
	"fountain": {"cat": "landmarks", "label": "Fountain", "align": false},
	"wind_shrine": {"cat": "landmarks", "label": "Wind shrine", "align": false},
	"market_stall": {"cat": "market", "label": "Market stall", "align": false},
	"flower_cart": {"cat": "market", "label": "Flower cart", "align": true},
	"well": {"cat": "landmarks", "label": "Well", "align": false},
	"bench": {"cat": "market", "label": "Bench", "align": false},
	"banner": {"cat": "market", "label": "Banner", "align": false},
	"signpost": {"cat": "market", "label": "Signpost", "align": false},
	"notice_board": {"cat": "market", "label": "Notice board", "align": false},
	"barrel": {"cat": "farm", "label": "Wine barrels", "align": false},
	"crate": {"cat": "farm", "label": "Apples", "align": false},
	"cart": {"cat": "farm", "label": "Cart", "align": true},
	"haystack": {"cat": "farm", "label": "Haystack", "align": true},
	"hay_bale": {"cat": "farm", "label": "Hay bale", "align": true},
	"scarecrow": {"cat": "farm", "label": "Scarecrow", "align": false},
	"log_pile": {"cat": "farm", "label": "Logs", "align": true},
	"stump": {"cat": "farm", "label": "Stump", "align": true},
	"mushrooms": {"cat": "farm", "label": "Mushrooms", "align": true},
	"cafe_table": {"cat": "market", "label": "Café table", "align": false},
	"planter": {"cat": "market", "label": "Planter", "align": false},
	"ruin_arch": {"cat": "ruins", "label": "Ruin arch", "align": false},
	"ruin_wall": {"cat": "ruins", "label": "Ruin wall", "align": false},
	"ruin_pillar": {"cat": "ruins", "label": "Ruin pillar", "align": false},
	"ruin_slab": {"cat": "ruins", "label": "Fallen slab", "align": true},
	"rotunda": {"cat": "landmarks", "label": "Rotunda", "align": false},
	"rock_big": {"cat": "ruins", "label": "Boulder", "align": true},
	"stone_lantern": {"cat": "lights", "label": "Stone lantern", "align": false},
	"tea_terrace": {"cat": "landmarks", "label": "Tea terrace", "align": true},
	"bamboo_raft": {"cat": "landmarks", "label": "Bamboo raft", "align": false, "float": true},
	"pumpkins": {"cat": "clutter", "label": "Pumpkins", "align": true},
	"jack_o_lantern": {"cat": "lights", "label": "Carved pumpkin", "align": true},
	"veg_crate": {"cat": "clutter", "label": "Vegetables", "align": true},
	"bread_stall": {"cat": "market", "label": "Bread stall", "align": false},
	"anvil": {"cat": "clutter", "label": "Anvil", "align": false},
	"fabric_rolls": {"cat": "market", "label": "Fabric rolls", "align": false},
	"broom_rack": {"cat": "clutter", "label": "Broom rack", "align": false},
	"wreath": {"cat": "clutter", "label": "Wreath", "align": false},
	"wheelbarrow": {"cat": "farm", "label": "Wheelbarrow", "align": true},
	"chair": {"cat": "clutter", "label": "Chair", "align": false},
	"birdhouse": {"cat": "clutter", "label": "Birdhouse", "align": false},
	"flower_pots": {"cat": "clutter", "label": "Flower pots", "align": true},
	"doorbell": {"cat": "clutter", "label": "Doorbell", "align": false},
	"bucket": {"cat": "clutter", "label": "Bucket", "align": true},
	"sacks": {"cat": "farm", "label": "Sacks", "align": true},
	"beehive": {"cat": "farm", "label": "Beehive", "align": true},
	"table": {"cat": "clutter", "label": "Table", "align": false},
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
