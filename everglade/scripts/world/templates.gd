class_name GladeTemplates
extends RefCounted
## Ready-made starting glades.


static func build(glade: Glade, template: String) -> void:
	glade.batch = true
	_build(glade, template)
	glade.batch = false
	glade.rebuild_all()
	glade.undo_stack.clear()
	glade.redo_stack.clear()


static func _build(glade: Glade, template: String) -> void:
	match template:
		"hamlet":
			glade.new_glade("meadow", "Windrise Town")
			_hamlet(glade)
		"hills":
			glade.new_glade("hills", "Hillside Glade")
			# rolling hills, a rocky plateau with a terrace and a cliff ridge
			glade.add_terrain_patch(PackedVector2Array([Vector2(-14, -6), Vector2(-9, -12), Vector2(-2, -15)]), 3.6, 1.6, 0.85)
			glade.add_terrain_patch(PackedVector2Array([Vector2(8, 6), Vector2(13, 11)]), 3.2, 2.4, 0.12)
			glade.add_terrain_patch(PackedVector2Array([Vector2(10.5, 8.5)]), 1.8, 1.4, 0.15, true)
			glade.add_terrain_patch(PackedVector2Array([Vector2(-12, 10)]), 4.0, 1.0, 1.0)
			glade.add_terrain_patch(PackedVector2Array([Vector2(12, -11), Vector2(16, -6)]), 2.4, 2.0, 0.35)
			_sprinkle_nature(glade, 18, 1)
		"town":
			glade.new_glade("town", "Town Plaza")
			_town(glade)
		"ruins":
			glade.new_glade("ruins", "Meadow Ruins")
			_ruins(glade)
		"village":
			glade.new_glade("village", "Jade Lake Village")
			_village(glade)
		"lake":
			glade.new_glade("lake", "Lakeside Glade")
			_sprinkle_nature(glade, 14, 2)
		_:
			glade.new_glade("meadow", "Meadow Glade")
			_sprinkle_nature(glade, 10, 3)


static func _sprinkle_nature(glade: Glade, trees: int, seed_value: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	# a few trees near the edges so the glade feels framed
	for i in trees:
		var a := rng.randf() * TAU
		var r := rng.randf_range(13.0, 20.0)
		var p := Vector2(cos(a), sin(a)) * r
		if glade.is_blocked(p):
			continue
		var kind: String = Catalog.TREES[rng.randi() % Catalog.TREES.size()]
		glade.add_prop(kind, Vector3(p.x, glade.terrain.height_at_v(p) - 0.03, p.y), rng.randf() * TAU, rng.randf_range(0.85, 1.25), false, false)
	for i in trees / 2:
		var p2 := Vector2(rng.randf_range(-18, 18), rng.randf_range(-18, 18))
		if glade.is_blocked(p2):
			continue
		var kind2: String = Catalog.BUSHES[rng.randi() % Catalog.BUSHES.size()] if i % 2 == 0 else Catalog.ROCKS[rng.randi() % 3]
		glade.add_prop(kind2, Vector3(p2.x, glade.terrain.height_at_v(p2) - 0.03, p2.y), rng.randf() * TAU, rng.randf_range(0.8, 1.2), true, false)


static func _pts(arr: Array) -> PackedVector2Array:
	var out := PackedVector2Array()
	for p in arr:
		out.append(p)
	return Geo.smooth(out, 2)


static func _hamlet(glade: Glade) -> void:
	var t := glade.terrain
	var rng := RandomNumberGenerator.new()
	rng.seed = 77
	# pond
	for i in 14:
		var a := TAU * i / 14.0
		t.sculpt(Vector2(-9.5, 8.5) + Vector2(cos(a) * 2.2, sin(a) * 1.6), 2.6, 1.0, "dig")
	t.sculpt(Vector2(-9.5, 8.5), 3.0, 1.0, "dig")
	t.sculpt(Vector2(-9.5, 8.5), 6.0, 0.6, "smooth")
	# a gentle hill behind the tower
	glade.add_terrain_patch(PackedVector2Array([Vector2(9.5, -12.0), Vector2(13.0, -10.5)]), 3.4, 1.3, 0.8)
	t.flush()

	# timbered town houses over stone, a tall spire tower and an old watchtower
	glade.add_building({"shape": "rect", "c": Vector2(2.0, -1.8), "size": Vector2(7.0, 4.6), "rot": 0.25,
		"floors": 3, "style": "windrise", "roof": "gable", "roof_col": Catalog.ROOF_COLORS[0],
		"wall_col": Catalog.WALL_COLORS[0], "pitch": 1.25, "chimney": 0.3, "ivy": 0.25})
	glade.add_building({"shape": "rect", "c": Vector2(-5.5, -6.0), "size": Vector2(5.4, 4.0), "rot": -0.45,
		"floors": 2, "style": "windrise", "roof": "gable", "roof_col": Catalog.ROOF_COLORS[1],
		"wall_col": Catalog.WALL_COLORS[1], "pitch": 1.3, "chimney": -0.25, "ivy": 0.4})
	glade.add_building({"shape": "round", "c": Vector2(10.0, -9.5), "r": 2.3, "rot": 0.0,
		"floors": 4, "style": "windrise", "roof": "cone", "roof_col": Catalog.ROOF_COLORS[0],
		"wall_col": Catalog.WALL_COLORS[0], "pitch": 1.1, "chimney": BuildingView.NO_CHIMNEY, "ivy": 0.3})
	glade.add_building({"shape": "rect", "c": Vector2(9.5, 2.0), "size": Vector2(4.8, 3.8), "rot": 1.25,
		"floors": 2, "style": "windrise", "roof": "hip", "roof_col": Catalog.ROOF_COLORS[1],
		"wall_col": Catalog.WALL_COLORS[0], "pitch": 1.1, "chimney": BuildingView.NO_CHIMNEY, "ivy": 0.2})
	glade.add_building({"shape": "round", "c": Vector2(-14.0, -12.5), "r": 1.7, "rot": 0.0,
		"floors": 3, "style": "stone", "roof": "flat", "roof_col": Catalog.ROOF_COLORS[2],
		"wall_col": Catalog.WALL_COLORS[2], "pitch": 1.0, "chimney": BuildingView.NO_CHIMNEY, "ivy": 0.9})

	# old castle wall curving along the north
	var wall := glade.add_wall(_pts([Vector2(-12.6, -13.5), Vector2(-5, -15.5), Vector2(3, -15.2), Vector2(8.5, -12.0)]), 3.8, Catalog.STONE_COLORS[0])
	wall.ivy = 0.8
	var low_wall := glade.add_wall(_pts([Vector2(-17, 2), Vector2(-15.5, -4), Vector2(-15.6, -10.8)]), 1.4, Catalog.STONE_COLORS[1])
	low_wall.ivy = 0.6

	# paths
	glade.add_path(_pts([Vector2(-1.0, 18.0), Vector2(0.0, 9.0), Vector2(1.4, 3.0), Vector2(2.6, 0.9)]), 1.6, "cobble")
	glade.add_path(_pts([Vector2(1.6, -3.8), Vector2(0.5, -9.0), Vector2(-1.0, -14.0), Vector2(-2.0, -20.0)]), 1.5, "dirt")
	glade.add_path(_pts([Vector2(0.0, 9.0), Vector2(-5.0, 9.0), Vector2(-9.5, 8.8), Vector2(-15.0, 9.5), Vector2(-19.0, 9.0)]), 1.3, "dirt")
	glade.add_path(_pts([Vector2(1.0, 6.0), Vector2(5.0, 4.0), Vector2(8.0, 2.8)]), 1.2, "stones")
	glade.add_path(_pts([Vector2(-3.8, -4.2), Vector2(-2.0, 0.5), Vector2(0.4, 5.0)]), 1.1, "dirt")
	glade.add_path(_pts([Vector2(9.0, -7.0), Vector2(6.0, -4.5), Vector2(3.5, -3.5)]), 1.2, "dirt")

	# sheep paddock with a gate where the stepping stones pass
	glade.add_fence(PackedVector2Array([Vector2(12, 6), Vector2(18.5, 6.5), Vector2(19, 15), Vector2(11, 15.5), Vector2(10.5, 9.5)]))
	glade.add_path(_pts([Vector2(8.6, 4.4), Vector2(11.0, 7.5), Vector2(14.0, 10.0)]), 1.1, "dirt")

	# nature
	var forest := [Vector2(-17, -3), Vector2(-18, 3), Vector2(-14, 14), Vector2(-19, 16), Vector2(16, -17),
		Vector2(18, -4), Vector2(-8, -18), Vector2(-19, -17), Vector2(5, 17), Vector2(17, 18), Vector2(-3, 14),
		Vector2(14, -2), Vector2(-11, 1), Vector2(6, -18), Vector2(19, 1)]
	# the town's great oak and a few birches by the pond
	for c in [Vector2(-11.0, -1.5)]:
		glade.add_prop("tree_round_b", Vector3(c.x, t.height_at_v(c) - 0.03, c.y), 0.4, 1.1, false, false)
	for c in [Vector2(-13.5, 6.0), Vector2(-6.0, 13.0), Vector2(-14.5, 10.5)]:
		glade.add_prop("tree_birch", Vector3(c.x, t.height_at_v(c) - 0.03, c.y), rng.randf() * TAU, 1.0, false, false)
	for c in forest:
		for k in 3:
			var p: Vector2 = c + Vector2(rng.randf_range(-2.5, 2.5), rng.randf_range(-2.5, 2.5))
			if glade.is_blocked(p):
				continue
			var kind: String = Catalog.TREES[rng.randi() % Catalog.TREES.size()]
			glade.add_prop(kind, Vector3(p.x, t.height_at_v(p) - 0.03, p.y), rng.randf() * TAU, rng.randf_range(0.85, 1.3), false, false)
	var flower_spots := [Vector2(4.5, 2.5), Vector2(-2.5, -3.5), Vector2(-7, -2.5), Vector2(6.5, -6), Vector2(-6, 12), Vector2(3, 12)]
	for c in flower_spots:
		for k in 5:
			var p2: Vector2 = c + Vector2(rng.randf_range(-1.5, 1.5), rng.randf_range(-1.5, 1.5))
			if glade.is_blocked(p2):
				continue
			glade.add_prop(Catalog.FLOWERS[rng.randi() % Catalog.FLOWERS.size()], Vector3(p2.x, t.height_at_v(p2), p2.y), rng.randf() * TAU, rng.randf_range(0.9, 1.3), true, false)
	for c in [Vector2(-6, 5), Vector2(5, -8.5), Vector2(-12, 12), Vector2(13, -6), Vector2(-3, 3)]:
		var kind3: String = Catalog.BUSHES[rng.randi() % Catalog.BUSHES.size()]
		glade.add_prop(kind3, Vector3(c.x, t.height_at_v(c), c.y), rng.randf() * TAU, 1.0, false, false)
	for c in [Vector2(-12.5, 5.5), Vector2(-7, 12.5), Vector2(15, -12)]:
		glade.add_prop("rock_a" if rng.randf() < 0.5 else "rock_c", Vector3(c.x, t.height_at_v(c), c.y), rng.randf() * TAU, 1.0, true, false)
	# props
	var placed := [
		["fountain", Vector2(-2.6, 5.6), 0.0], ["lantern", Vector2(-2.4, 15.0), 0.0], ["lantern", Vector2(1.4, 15.0), 0.0],
		["paper_lantern", Vector2(1.9, 9.6), 0.0], ["lantern", Vector2(-0.6, 2.4), 0.0], ["lantern", Vector2(-6.0, 10.5), 0.0],
		["market_stall", Vector2(3.6, 8.2), -1.2], ["market_stall", Vector2(-6.0, 6.0), 1.3], ["flower_cart", Vector2(-3.8, 11.8), 2.6],
		["notice_board", Vector2(-3.2, 2.6), 0.6], ["signpost", Vector2(0.6, 12.6), 0.0], ["bench", Vector2(-5.0, 4.0), 2.4],
		["barrel", Vector2(5.4, -0.2), 0.0], ["crate", Vector2(5.0, 0.9), 0.4], ["well", Vector2(-8.0, -1.6), 0.3],
		["windmill", Vector2(15.5, 12.5), 2.3], ["windmill", Vector2(18.0, -3.5), 1.4], ["wind_shrine", Vector2(-15.5, 13.5), 0.0],
		["haystack", Vector2(16.5, 15.5), 0.0], ["hay_bale", Vector2(13.0, 13.5), 0.4], ["cart", Vector2(6.2, 5.6), 2.2],
		["scarecrow", Vector2(16.0, 9.0), 0.6], ["log_pile", Vector2(-8.4, -7.6), 1.1], ["stump", Vector2(-12.0, -4.5), 0.0],
		["mushrooms", Vector2(-13.0, -4.0), 0.0], ["banner", Vector2(8.0, -6.6), 0.0], ["banner", Vector2(3.8, -12.6), 0.0],
		["banner", Vector2(-2.6, -13.6), 0.0],
	]
	for item in placed:
		var p3: Vector2 = item[1]
		glade.add_prop(item[0], Vector3(p3.x, t.height_at_v(p3) - 0.03, p3.y), item[2], 1.0, Catalog.DECOR.get(item[0], {}).get("align", false), false)
	for b in glade.data.buildings:
		b.ivy = b.get("ivy", 0.5)
	glade.rebuild_all()


# ---------------------------------------------------------------------------
# Showcase glades matching the three reference environments
# ---------------------------------------------------------------------------
static func _prop(glade: Glade, kind: String, p: Vector2, rot := 0.0, s := 1.0, sink := 0.03) -> void:
	var align: bool = Catalog.DECOR.get(kind, {}).get("align", false)
	glade.add_prop(kind, Vector3(p.x, glade.terrain.height_at_v(p) - sink, p.y), rot, s, align, false)


static func _scatter(glade: Glade, rng: RandomNumberGenerator, kinds: Array, center: Vector2, radius: float, count: int, scale_range := Vector2(0.85, 1.25), align := true) -> void:
	for i in count:
		var a := rng.randf() * TAU
		var p: Vector2 = center + Vector2(cos(a), sin(a)) * sqrt(rng.randf()) * radius
		if glade.is_blocked(p) or not glade.terrain.in_play_area(p, 0.5):
			continue
		var kind: String = kinds[rng.randi() % kinds.size()]
		glade.add_prop(kind, Vector3(p.x, glade.terrain.height_at_v(p) - 0.03, p.y), rng.randf() * TAU, rng.randf_range(scale_range.x, scale_range.y), align, false)


## Paved plaza ringed by timbered houses with red roofs, a fountain, café
## tables, market stalls, windmills, golden trees and an ornate fence.
static func _town(glade: Glade) -> void:
	var t := glade.terrain
	var rng := RandomNumberGenerator.new()
	rng.seed = 501
	# a rocky bluff behind the town with a grassy shoulder
	glade.add_terrain_patch(PackedVector2Array([Vector2(-17, -12), Vector2(-14, -15), Vector2(-10, -17)]), 3.2, 1.2, 0.85)
	glade.add_terrain_patch(PackedVector2Array([Vector2(-16, -15.5), Vector2(-13, -17.5)]), 2.0, 1.6, 0.1, true)
	t.flush()
	var red: Color = Catalog.ROOF_COLORS[1]
	var teal: Color = Catalog.ROOF_COLORS[0]
	var houses := [
		[Vector2(-6.5, -7.5), Vector2(6.4, 4.4), 0.08, 3, red, "gable", 0.3],
		[Vector2(1.8, -9.0), Vector2(5.2, 4.2), -0.05, 2, teal, "gable", -0.3],
		[Vector2(9.2, -6.0), Vector2(5.6, 4.2), -0.75, 3, red, "hip", 99.0],
		[Vector2(-11.5, 1.0), Vector2(5.8, 4.2), 1.5, 2, red, "gable", 0.25],
		[Vector2(11.0, 3.5), Vector2(5.0, 4.0), 1.65, 2, red, "gable", -0.25],
	]
	for h in houses:
		var d := {"shape": "rect", "c": h[0], "size": h[1], "rot": h[2], "floors": h[3], "style": "windrise",
			"roof": h[5], "roof_col": h[4], "wall_col": Catalog.WALL_COLORS[0], "pitch": 1.3,
			"chimney": h[6] if h[6] < 10.0 else BuildingView.NO_CHIMNEY, "ivy": 0.15}
		var b := glade.add_building(d)
		# a dormer on each slope of the big red roofs
		if h[5] == "gable" and h[1].x > 5.0:
			b.windows.append({"side": 0, "u": 0.5, "f": h[3], "kind": "dormer"})
			b.windows.append({"side": 2, "u": 0.5, "f": h[3], "kind": "dormer"})
	glade.add_building({"shape": "round", "c": Vector2(-12.0, -11.0), "r": 2.1, "rot": 0.0, "floors": 4, "style": "windrise",
		"roof": "cone", "roof_col": teal, "wall_col": Catalog.WALL_COLORS[0], "pitch": 1.1, "chimney": BuildingView.NO_CHIMNEY, "ivy": 0.2})
	# the plaza: one very wide paved stroke plus streets leading off it
	glade.add_path(_pts([Vector2(-5.5, 0.5), Vector2(5.5, 0.0)]), 8.5, "paved")
	glade.add_path(_pts([Vector2(0.5, 5.2), Vector2(0.0, 11.0), Vector2(-1.0, 20.0)]), 2.4, "paved")
	glade.add_path(_pts([Vector2(-6.4, -3.6), Vector2(-6.5, -4.9)]), 1.6, "paved")
	glade.add_path(_pts([Vector2(1.8, -3.9), Vector2(1.8, -6.6)]), 1.6, "paved")
	glade.add_path(_pts([Vector2(9.8, 0.5), Vector2(10.8, 1.2)]), 1.4, "paved")
	glade.add_path(_pts([Vector2(5.0, 10.0), Vector2(11.0, 12.0), Vector2(17.0, 15.5)]), 1.3, "dirt")
	# ornate fence along the southern lawn with a gate on the street
	glade.add_fence(PackedVector2Array([Vector2(-15.0, 7.5), Vector2(-7.0, 7.6), Vector2(0.5, 7.8), Vector2(8.0, 7.6), Vector2(14.0, 7.2)]), "ornate")
	var placed := [
		["fountain", Vector2(0.0, 0.2), 0.0], ["paper_lantern", Vector2(-4.6, 3.4), 0.0], ["paper_lantern", Vector2(4.6, 3.4), 0.0],
		["paper_lantern", Vector2(-4.6, -2.8), 0.0], ["paper_lantern", Vector2(4.8, -2.8), 0.0],
		["cafe_table", Vector2(-3.4, -2.2), 0.3], ["cafe_table", Vector2(-1.3, -3.0), -0.2], ["cafe_table", Vector2(3.6, 2.6), 0.6],
		["planter", Vector2(-2.2, -3.6), 0.0], ["planter", Vector2(2.8, -3.4), 0.0], ["planter", Vector2(-5.8, 2.6), 1.57],
		["market_stall", Vector2(6.8, 2.8), -1.5], ["market_stall", Vector2(-7.6, 3.4), 1.3], ["crate", Vector2(7.6, 4.6), 0.3],
		["crate", Vector2(-8.4, 5.0), 0.8], ["barrel", Vector2(8.4, -1.6), 0.0], ["barrel", Vector2(-9.0, -2.2), 0.5],
		["flower_cart", Vector2(3.4, 5.6), 2.8], ["bench", Vector2(-3.0, 4.6), 3.14], ["notice_board", Vector2(5.6, -3.4), -0.3],
		["windmill", Vector2(15.5, -13.5), 2.4], ["windmill", Vector2(17.0, 13.0), 2.0], ["haystack", Vector2(14.0, 16.5), 0.0],
		["hay_bale", Vector2(18.5, 10.5), 0.5], ["banner", Vector2(-2.8, -7.0), 0.0], ["banner", Vector2(4.8, -7.4), 0.0],
		["lantern", Vector2(-2.2, 9.0), 0.0], ["lantern", Vector2(2.2, 14.0), 0.0], ["signpost", Vector2(2.4, 9.4), 0.4],
		["well", Vector2(-13.0, 4.8), 0.4], ["cart", Vector2(-16.5, -3.5), 1.2], ["wind_shrine", Vector2(-17.0, 14.0), 0.0],
	]
	for item in placed:
		_prop(glade, item[0], item[1], item[2])
	for c in [Vector2(-9.5, -2.8), Vector2(7.6, -10.5), Vector2(14.5, -1.5), Vector2(-4.5, 11.5), Vector2(6.5, 12.5)]:
		_prop(glade, "tree_golden" if rng.randf() < 0.6 else "tree_orange", c, rng.randf() * TAU, rng.randf_range(0.95, 1.2))
	_scatter(glade, rng, ["tree_golden", "tree_orange", "tree_round_a", "tree_birch"], Vector2(-14, -16), 7.0, 10, Vector2(0.9, 1.3), false)
	_scatter(glade, rng, ["tree_golden", "tree_round_c", "tree_round_a"], Vector2(18, -4), 5.0, 6, Vector2(0.9, 1.3), false)
	_scatter(glade, rng, ["tree_orange", "tree_golden", "tree_round_a"], Vector2(-17, 14), 5.0, 6, Vector2(0.9, 1.3), false)
	_scatter(glade, rng, ["bush_golden", "bush_a", "bush_b"], Vector2(-8, 11), 7.0, 10)
	_scatter(glade, rng, Catalog.FLOWERS, Vector2(-7, 10.5), 6.0, 24)
	_scatter(glade, rng, Catalog.FLOWERS, Vector2(8, 10.5), 6.0, 20)
	glade.rebuild_all()


## Ancient ruins in a golden meadow: a carved archway, broken walls with
## pointed niches, pillars, a fallen slab and a glowing broken-dome rotunda.
static func _ruins(glade: Glade) -> void:
	var t := glade.terrain
	var rng := RandomNumberGenerator.new()
	rng.seed = 733
	# the rotunda crowns a low rocky knoll
	glade.add_terrain_patch(PackedVector2Array([Vector2(9.0, -9.0)]), 4.2, 1.2, 0.3)
	glade.add_terrain_patch(PackedVector2Array([Vector2(-15.0, 9.0), Vector2(-11.0, 14.0)]), 3.0, 0.9, 0.85)
	t.flush()
	var placed := [
		["ruin_arch", Vector2(0.0, -2.0), 0.0, 1.15], ["ruin_wall", Vector2(-5.6, -2.6), -0.12, 1.0],
		["ruin_wall", Vector2(5.4, -1.6), 0.25, 0.9], ["ruin_pillar", Vector2(-9.2, -3.2), 0.3, 1.0],
		["ruin_pillar", Vector2(8.6, -0.4), 0.0, 0.85], ["ruin_pillar", Vector2(-3.0, 3.0), 1.0, 0.7],
		["ruin_slab", Vector2(3.6, 3.4), 0.6, 1.0], ["ruin_slab", Vector2(-7.0, 2.4), 2.2, 0.8],
		["rotunda", Vector2(9.0, -9.0), 0.3, 1.0], ["rock_big", Vector2(-10.5, 5.5), 0.4, 1.0],
		["rock_big", Vector2(12.0, 4.0), 2.0, 0.8], ["rock_big", Vector2(-2.5, -8.5), 1.0, 0.7],
		["wind_shrine", Vector2(-13.0, -10.0), 0.0, 1.0], ["stump", Vector2(5.0, 7.0), 0.0, 1.0],
		["mushrooms", Vector2(-9.5, 6.5), 0.0, 1.0],
	]
	for item in placed:
		_prop(glade, item[0], item[1], item[2], item[3], 0.08)
	# an old trail through the arch
	glade.add_path(_pts([Vector2(-1.0, 20.0), Vector2(0.5, 9.0), Vector2(0.0, 1.0), Vector2(0.0, -6.0), Vector2(4.0, -10.0), Vector2(7.0, -13.0)]), 1.2, "dirt")
	# framing trees: broad leafy crowns with a few golden ones
	for c in [Vector2(-14.0, -6.0), Vector2(-16.0, 2.0), Vector2(15.0, -2.0), Vector2(-8.0, -15.0), Vector2(16.0, 10.0), Vector2(-15.0, 13.0), Vector2(2.0, -16.0)]:
		_scatter(glade, rng, ["tree_round_a", "tree_round_c", "tree_golden", "tree_round_a"], c, 3.0, 3, Vector2(0.95, 1.35), false)
	_prop(glade, "tree_round_b", Vector2(-11.0, -1.0), 0.6, 1.15)
	# lavender drifts and wildflowers in the tall grass
	for c in [Vector2(-5.0, 6.0), Vector2(6.0, 9.0), Vector2(-9.0, -8.0), Vector2(12.0, -4.0), Vector2(-3.0, 13.0)]:
		_scatter(glade, rng, Catalog.LAVENDER, c, 3.2, 26, Vector2(0.9, 1.4))
	_scatter(glade, rng, Catalog.FLOWERS, Vector2(0, 4), 15.0, 40)
	_scatter(glade, rng, ["bush_a", "bush_golden", "bush_b"], Vector2(0, 0), 17.0, 12)
	glade.rebuild_all()


## Lake village: whitewashed houses with dark curved roofs and stepped
## gables, a stone causeway over a jade lake, bamboo rafts, tea terraces,
## blossom and ginkgo trees, with karst peaks in the haze.
static func _village(glade: Glade) -> void:
	var t := glade.terrain
	var rng := RandomNumberGenerator.new()
	rng.seed = 919
	# stacked tea terraces climbing both hillsides
	glade.add_terrain_patch(PackedVector2Array([Vector2(-18, -9), Vector2(-14, -12), Vector2(-9, -16)]), 3.6, 0.8, 0.12)
	glade.add_terrain_patch(PackedVector2Array([Vector2(-17.5, -12), Vector2(-14, -15.5)]), 2.6, 0.8, 0.12, true)
	glade.add_terrain_patch(PackedVector2Array([Vector2(-16.8, -15), Vector2(-15, -17)]), 1.6, 0.8, 0.12, true)
	glade.add_terrain_patch(PackedVector2Array([Vector2(13, -10), Vector2(17, -14)]), 3.4, 0.9, 0.12)
	glade.add_terrain_patch(PackedVector2Array([Vector2(15, -12.5), Vector2(17.5, -15)]), 2.0, 0.9, 0.12, true)
	t.flush()
	var dark: Color = Catalog.ROOF_COLORS[5]
	var houses := [
		[Vector2(-6.0, -5.0), Vector2(6.0, 4.0), 0.05, 2], [Vector2(1.5, -6.5), Vector2(5.0, 3.8), -0.05, 2],
		[Vector2(8.5, -4.5), Vector2(5.4, 3.8), -0.3, 1], [Vector2(-12.0, -2.0), Vector2(4.6, 3.6), 0.4, 1],
		[Vector2(-3.0, -12.5), Vector2(5.6, 4.0), 0.0, 2], [Vector2(5.5, -13.5), Vector2(4.8, 3.6), 0.1, 1],
		[Vector2(14.5, 2.5), Vector2(4.6, 3.6), 1.4, 1],
	]
	for h in houses:
		glade.add_building({"shape": "rect", "c": h[0], "size": h[1], "rot": h[2], "floors": h[3], "style": "lakeside",
			"roof": "gable", "roof_col": dark, "wall_col": Catalog.WALL_COLORS[0], "pitch": 0.9,
			"chimney": BuildingView.NO_CHIMNEY, "ivy": 0.1})
	# lanes and the stone causeway across the lake
	glade.add_path(_pts([Vector2(-14.0, 0.2), Vector2(-6.0, -1.8), Vector2(1.5, -2.6), Vector2(9.0, -1.0), Vector2(16.0, 0.0)]), 1.8, "paved")
	glade.add_path(_pts([Vector2(1.5, -2.6), Vector2(1.2, 4.0), Vector2(1.0, 12.0), Vector2(0.5, 20.0)]), 1.7, "paved")
	glade.add_path(_pts([Vector2(-3.0, -2.2), Vector2(-3.0, -9.6)]), 1.4, "paved")
	glade.add_path(_pts([Vector2(-14.0, -12.0), Vector2(-10.0, -8.0), Vector2(-6.0, -4.0)]), 1.1, "stones")
	var placed := [
		["bamboo_raft", Vector2(-5.5, 8.0), 0.4], ["bamboo_raft", Vector2(7.0, 10.0), -0.9], ["bamboo_raft", Vector2(-1.5, 12.5), 1.8],
		["stone_lantern", Vector2(-1.2, -1.0), 0.0], ["stone_lantern", Vector2(4.2, -1.2), 0.0], ["stone_lantern", Vector2(-9.0, 0.4), 0.0],
		["tea_terrace", Vector2(-14.5, -12.5), 0.3], ["tea_terrace", Vector2(-10.5, -15.5), 1.1], ["tea_terrace", Vector2(15.5, -13.5), -0.4],
		["tea_terrace", Vector2(17.5, -9.0), 0.9], ["crate", Vector2(-8.4, -1.4), 0.2], ["barrel", Vector2(5.2, -3.6), 0.0],
		["rock_big", Vector2(-10.0, 5.0), 0.5], ["rock_big", Vector2(12.0, 7.5), 2.0], ["bench", Vector2(10.0, 0.8), 3.0],
		["haystack", Vector2(17.0, -3.5), 0.0],
	]
	for item in placed:
		var p: Vector2 = item[1]
		var y := maxf(t.height_at_v(p), Terrain.WATER_LEVEL - 0.04) if item[0] == "bamboo_raft" else t.height_at_v(p) - 0.03
		glade.add_prop(item[0], Vector3(p.x, y, p.y), item[2], 1.0, Catalog.DECOR.get(item[0], {}).get("align", false), false)
	for c in [Vector2(-9.0, -8.5), Vector2(11.5, -9.0), Vector2(-16.0, 4.0), Vector2(5.0, 1.8)]:
		_prop(glade, "tree_blossom", c, rng.randf() * TAU, rng.randf_range(0.95, 1.2))
	for c in [Vector2(12.0, -1.5), Vector2(-13.0, -6.5), Vector2(-1.5, -16.5)]:
		_prop(glade, "tree_golden", c, rng.randf() * TAU, rng.randf_range(1.0, 1.25))
	_scatter(glade, rng, ["tree_teal", "tree_round_c", "tree_blossom", "tree_teal"], Vector2(-17, -16), 5.0, 8, Vector2(0.9, 1.3), false)
	_scatter(glade, rng, ["tree_teal", "tree_golden", "tree_birch"], Vector2(18, -17), 4.0, 6, Vector2(0.9, 1.3), false)
	_scatter(glade, rng, ["tree_teal", "tree_blossom", "tree_round_c"], Vector2(-17, 12), 5.0, 6, Vector2(0.9, 1.3), false)
	_scatter(glade, rng, ["tree_teal", "tree_golden"], Vector2(17, 13), 5.0, 6, Vector2(0.9, 1.3), false)
	_scatter(glade, rng, ["bush_a", "bush_b", "bush_golden"], Vector2(0, -9), 14.0, 12)
	_scatter(glade, rng, Catalog.FLOWERS, Vector2(-8, -9), 8.0, 20)
	glade.rebuild_all()
