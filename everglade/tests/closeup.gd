extends Node
## Dev helper: renders close-ups of single buildings.  -- --closeup=/tmp/dir
var game: Game
var out := ""


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--closeup="):
			out = a.trim_prefix("--closeup=")
	DirAccess.make_dir_recursive_absolute(out)
	game = get_parent()
	_run.call_deferred()


func _shot(n: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(n + ".png"))


func _run() -> void:
	for i in 60:
		await get_tree().process_frame
	game.start_new("meadow")
	game.life.enabled = false
	game.life.clear()
	var g := game.glade
	g.add_building({"shape": "rect", "c": Vector2(-4, 0), "size": Vector2(7.0, 4.6), "rot": 0.0, "floors": 2, "style": "windrise", "roof": "gable",
		"roof_col": Catalog.ROOF_COLORS[0], "wall_col": Catalog.WALL_COLORS[0], "pitch": 1.0, "chimney": -99.0})
	g.add_building({"shape": "round", "c": Vector2(5, 0), "r": 2.2, "rot": 0.0, "floors": 3, "style": "windrise", "roof": "cone",
		"roof_col": Catalog.ROOF_COLORS[0], "wall_col": Catalog.WALL_COLORS[0], "pitch": 1.0, "chimney": -99.0})
	g.add_prop("tree_round_b", Vector3(0, 0, 6), 0.0, 1.0, false, false)
	g.add_prop("windmill", Vector3(-9, 0, 5), 0.5, 1.0, false, false)
	g.add_prop("fountain", Vector3(-2, 0, 7), 0.0, 1.0, false, false)
	g.add_prop("lantern", Vector3(2, 0, 6), 0.0, 1.0, false, false)
	g.add_prop("market_stall", Vector3(4, 0, 7), 0.4, 1.0, false, false)
	game.hud.visible = false
	game.rig.focus_on(Vector3(0, 0, 1), 16.0)
	game.rig.yaw = deg_to_rad(10)
	game.rig.snap()
	for i in 60:
		await get_tree().process_frame
	await _shot("a_front")
	game.rig.focus_on(Vector3(-4, 0, 0), 9.0)
	game.rig.yaw = deg_to_rad(40)
	game.rig.snap()
	for i in 30:
		await get_tree().process_frame
	await _shot("b_house")
	# freehand stone wall with a path arch through it
	var wall := g.add_wall(PackedVector2Array([Vector2(-9, -10.2), Vector2(-3, -10.6), Vector2(4, -10.2)]), 3.4, Catalog.STONE_COLORS[1])
	wall.ivy = 1.0
	# a path running up to the wall (door) and one passing through (arch)
	g.add_path(PackedVector2Array([Vector2(-6.5, -4.5), Vector2(-6.0, -9.4)]), 1.3, "dirt")
	g.add_path(PackedVector2Array([Vector2(1.5, -4), Vector2(1.2, -16)]), 1.4, "dirt")
	g.rebuild_all()
	game.rig.focus_on(Vector3(-2.5, 1.4, -10), 8.5)
	game.rig.yaw = deg_to_rad(12)
	game.rig.snap()
	for i in 40:
		await get_tree().process_frame
	await _shot("c_wall")
	game.day.time_of_day = 0.9
	for i in 40:
		await get_tree().process_frame
	await _shot("d_wall_night")
	# plastered cottage and round tower (worn render, stone courses)
	game.day.time_of_day = 0.4
	g.add_building({"shape": "round", "c": Vector2(9, 6), "r": 2.2, "rot": 0.0, "floors": 2, "style": "plaster", "roof": "cone",
		"roof_col": Catalog.ROOF_COLORS[1], "wall_col": Catalog.WALL_COLORS[1], "pitch": 0.75, "chimney": -99.0, "ivy": 1.0})
	g.add_building({"shape": "rect", "c": Vector2(4.5, 7.5), "size": Vector2(4.4, 3.6), "rot": 0.3, "floors": 2, "style": "plaster", "roof": "gable",
		"roof_col": Catalog.ROOF_COLORS[1], "wall_col": Catalog.WALL_COLORS[1], "pitch": 1.1, "chimney": -99.0, "ivy": 0.8})
	g.rebuild_all()
	game.rig.focus_on(Vector3(7, 1.6, 7), 10.0)
	game.rig.yaw = deg_to_rad(-15)
	game.rig.snap()
	for i in 40:
		await get_tree().process_frame
	await _shot("e_plaster")
	get_tree().quit()
