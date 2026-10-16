extends Node
## Dev helper: stages the Tiny Glade-style editing results (joined houses,
## curved and flared roofs, merged windows, roofs over wall rings) in an empty
## meadow and photographs them.  -- --editview=/tmp/dir
var game: Game
var out := ""


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--editview="):
			out = a.trim_prefix("--editview=")
	DirAccess.make_dir_recursive_absolute(out)
	game = get_parent()
	_run.call_deferred()


func _shot(n: String, p: Vector3, dist: float, yaw: float, pitch: float) -> void:
	game.rig.focus_on(p, dist)
	game.rig.yaw = deg_to_rad(yaw)
	game.rig.pitch_offset = pitch
	game.rig.snap()
	for i in 45:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(n + ".png"))
	print("shot ", n)


func _house(c: Vector2, size: Vector2, rot: float, floors: int, extra := {}) -> Dictionary:
	var d := {"shape": "rect", "c": c, "size": size, "rot": rot, "floors": floors, "style": "windrise", "roof": "gable",
			"pitch": 1.15, "roof_col": Catalog.ROOF_COLORS[1], "wall_col": Catalog.WALL_COLORS[0], "chimney": BuildingView.NO_CHIMNEY}
	d.merge(extra, true)
	return game.glade.add_building(d)


func _run() -> void:
	for i in 60:
		await get_tree().process_frame
	game.start_new("meadow")
	game.life.enabled = false
	game.life.clear()
	var g := game.glade
	g.data.props.clear()
	g.props.rebuild(g.data.props)
	game.hud.visible = false
	g.show_boundary(false)
	# joined houses: a wing pushed into the main house at a slight angle
	_house(Vector2(0, 0), Vector2(8.0, 5.0), 0.0, 2)
	_house(Vector2(1.2, 3.6), Vector2(4.2, 3.8), PI * 0.5 + 0.15, 1, {"roof_col": Catalog.ROOF_COLORS[1]})
	# rounded and flared roofs
	_house(Vector2(-14, 0), Vector2(6.0, 4.6), 0.0, 1, {"curve": 0.85, "roof_col": Catalog.ROOF_COLORS[2]})
	_house(Vector2(14, 0), Vector2(6.0, 4.6), 0.0, 1, {"curve": -0.85, "roof_col": Catalog.ROOF_COLORS[0]})
	# merged windows: a gallery of three and a double door on the front
	_house(Vector2(0, -14), Vector2(8.0, 4.6), 0.0, 2, {"windows": [
		{"side": 0, "u": 0.36, "f": 1, "kind": "window"}, {"side": 0, "u": 0.5, "f": 1, "kind": "window"},
		{"side": 0, "u": 0.64, "f": 1, "kind": "window"}, {"side": 0, "u": 0.45, "f": 0, "kind": "door"},
		{"side": 0, "u": 0.58, "f": 0, "kind": "door"}, {"side": 0, "u": 0.15, "f": 0, "kind": "window"}]})
	# roofs over rings of walls
	var ring := PackedVector2Array()
	for k in 25:
		var a := TAU * k / 24.0
		ring.append(Vector2(-10, 14) + Vector2(cos(a), sin(a)) * 3.0)
	g.add_wall(ring, 3.6, Catalog.STONE_COLORS[0], "stone", "glade")
	g.add_roof_over_walls(Vector2(-10, 14), "gable", 1.1, Catalog.ROOF_COLORS[2])
	var sq := PackedVector2Array([Vector2(6, 11), Vector2(14, 11), Vector2(14, 16.5), Vector2(6, 16.5), Vector2(6, 11)])
	g.add_wall(Geo.resample(sq, 1.0), 3.6, Catalog.STONE_COLORS[1], "rendered", "glade")
	g.add_roof_over_walls(Vector2(10, 13.5), "gable", 1.1, Catalog.ROOF_COLORS[0])
	await _shot("1_joined", Vector3(0.5, 0, 1.5), 17.0, 35.0, -0.05)
	await _shot("2_curved_roofs", Vector3(0, 0, 0), 34.0, 0.0, -0.08)
	await _shot("3_merged_windows", Vector3(0, 0, -16), 14.0, 180.0, 0.05)
	await _shot("4_roofs_on_walls", Vector3(1, 0, 14), 24.0, 10.0, -0.1)
	get_tree().quit()
