extends Node
## Dev helper: close-ups of doors and windows set into house walls, one
## house per style.  -- --woodview=/tmp/dir
var game: Game
var out := ""


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--woodview="):
			out = a.trim_prefix("--woodview=")
	DirAccess.make_dir_recursive_absolute(out)
	game = get_parent()
	_run.call_deferred()


func _shot(n: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(n + ".png"))


func _house(c: Vector2, style: String, floors: int, wt: String, extra: Array = []) -> void:
	var b := {"shape": "rect", "c": c, "size": Vector2(6.4, 4.4), "rot": 0.0, "floors": floors, "style": style, "roof": "gable",
		"roof_col": Catalog.ROOF_COLORS[0], "wall_col": Catalog.WALL_COLORS[0], "pitch": 1.0, "chimney": -99.0, "seed": 5}
	var ws: Array = [{"side": 0, "u": 0.5, "f": 0, "kind": "door"}]
	for f in floors:
		for u in [0.18, 0.82]:
			ws.append({"side": 0, "u": u, "f": f, "kind": "window", "wt": wt})
	if floors > 1:
		ws.append({"side": 0, "u": 0.5, "f": 1, "kind": "window", "wt": wt, "deco": 3})
	b.windows = ws + extra
	game.glade.add_building(b)


func _run() -> void:
	for i in 60:
		await get_tree().process_frame
	game.start_new("meadow")
	game.life.enabled = false
	game.life.clear()
	var g := game.glade
	_house(Vector2(-16, 0), "plaster", 2, "plain")
	_house(Vector2(-8, 0), "stone", 2, "gothic")
	_house(Vector2(0, 0), "timber", 2, "plain")
	_house(Vector2(8, 0), "wood", 1, "arched")
	_house(Vector2(16, 0), "windrise", 2, "plain")
	g.add_building({"shape": "round", "c": Vector2(24, 0), "r": 2.2, "rot": 0.0, "floors": 3, "style": "stone", "roof": "cone",
		"roof_col": Catalog.ROOF_COLORS[2], "wall_col": Catalog.WALL_COLORS[0], "pitch": 1.0, "chimney": -99.0, "seed": 3,
		"windows": [{"side": 0, "u": 0.75, "f": 0, "kind": "door"}, {"side": 0, "u": 0.7, "f": 1, "kind": "window", "wt": "gothic"},
			{"side": 0, "u": 0.8, "f": 2, "kind": "window"}]})
	game.hud.visible = false
	var i := 0
	for shot in [[-8.0, 26.0, 198.0], [20.0, 24.0, 160.0]]:
		game.rig.focus_on(Vector3(shot[0], 2.2, -1.0), shot[1])
		game.rig.yaw = deg_to_rad(shot[2])
		game.rig.snap()
		for k in 30:
			await get_tree().process_frame
		await _shot("%d_wide" % i)
		i += 1
	get_tree().quit()
