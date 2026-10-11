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
	get_tree().quit()
