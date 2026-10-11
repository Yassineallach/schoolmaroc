class_name GladeTemplates
extends RefCounted
## Ready-made starting glades.


static func build(glade: Glade, template: String) -> void:
	match template:
		"hamlet":
			glade.new_glade("meadow", "Little Hamlet")
			_hamlet(glade)
		"hills":
			glade.new_glade("hills", "Hillside Glade")
			_sprinkle_nature(glade, 18, 1)
		"lake":
			glade.new_glade("lake", "Lakeside Glade")
			_sprinkle_nature(glade, 14, 2)
		_:
			glade.new_glade("meadow", "Meadow Glade")
			_sprinkle_nature(glade, 10, 3)
	glade.undo_stack.clear()
	glade.redo_stack.clear()


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
	t.sculpt(Vector2(11, -11), 6.0, 1.4, "raise")
	t.sculpt(Vector2(11, -11), 7.0, 0.8, "smooth")
	t.flush()

	# cottages and a tower
	glade.add_building({"shape": "rect", "c": Vector2(2.0, -1.5), "size": Vector2(6.5, 4.4), "rot": 0.25,
		"floors": 2, "style": "timber", "roof": "gable", "roof_col": Catalog.ROOF_COLORS[0],
		"wall_col": Catalog.WALL_COLORS[0], "pitch": 1.05, "chimney": 0.28, "ivy": 0.5})
	glade.add_building({"shape": "rect", "c": Vector2(-5.5, -6.0), "size": Vector2(5.0, 3.8), "rot": -0.45,
		"floors": 1, "style": "plaster", "roof": "gable", "roof_col": Catalog.ROOF_COLORS[1],
		"wall_col": Catalog.WALL_COLORS[1], "pitch": 1.2, "chimney": -0.25, "ivy": 0.7})
	glade.add_building({"shape": "round", "c": Vector2(10.0, -9.5), "r": 2.3, "rot": 0.0,
		"floors": 3, "style": "stone", "roof": "cone", "roof_col": Catalog.ROOF_COLORS[2],
		"wall_col": Catalog.WALL_COLORS[2], "pitch": 1.0, "chimney": BuildingView.NO_CHIMNEY, "ivy": 0.8})
	glade.add_building({"shape": "rect", "c": Vector2(9.5, 2.0), "size": Vector2(4.6, 3.6), "rot": 1.25,
		"floors": 1, "style": "stone", "roof": "hip", "roof_col": Catalog.ROOF_COLORS[3],
		"wall_col": Catalog.WALL_COLORS[3], "pitch": 1.0, "chimney": BuildingView.NO_CHIMNEY, "ivy": 0.3})
	glade.add_building({"shape": "round", "c": Vector2(-14.0, -12.5), "r": 1.6, "rot": 0.0,
		"floors": 2, "style": "stone", "roof": "flat", "roof_col": Catalog.ROOF_COLORS[2],
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
		["well", Vector2(-1.8, 5.8), 0.3], ["lantern", Vector2(1.7, 10.0), 0.0], ["lantern", Vector2(-0.6, 14.5), 0.0],
		["lantern", Vector2(-6.0, 10.5), 0.0], ["bench", Vector2(-5.0, 4.0), 2.4], ["haystack", Vector2(16.5, 13.0), 0.0],
		["hay_bale", Vector2(13.0, 13.5), 0.4], ["cart", Vector2(6.2, 5.6), 2.2], ["barrel", Vector2(5.4, -0.2), 0.0],
		["crate", Vector2(5.0, 0.7), 0.4], ["barrel", Vector2(-2.6, -8.2), 0.0], ["log_pile", Vector2(-8.4, -7.6), 1.1],
		["banner", Vector2(3.8, -12.6), 0.0], ["scarecrow", Vector2(16.0, 9.0), 0.6], ["stump", Vector2(-12.0, -1.0), 0.0],
		["mushrooms", Vector2(-13.0, 0.0), 0.0], ["bench", Vector2(3.6, -9.0), 0.4],
	]
	for item in placed:
		var p3: Vector2 = item[1]
		glade.add_prop(item[0], Vector3(p3.x, t.height_at_v(p3) - 0.03, p3.y), item[2], 1.0, Catalog.DECOR.get(item[0], {}).get("align", false), false)
	for b in glade.data.buildings:
		b.ivy = b.get("ivy", 0.5)
	glade.rebuild_all()
