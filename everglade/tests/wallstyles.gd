extends Node
## Dev helper: builds the same arched stone wall in every Masonry pattern and
## photographs each.  -- --wallstyles=/tmp/dir
var game: Game
var out := ""
const PATTERNS := ["classic", "glade", "kit", "rubble", "brick", "ashlar"]


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--wallstyles="):
			out = a.trim_prefix("--wallstyles=")
	DirAccess.make_dir_recursive_absolute(out)
	game = get_parent()
	_run.call_deferred()


func _shot(n: String) -> void:
	for i in 40:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(n + ".png"))
	print("shot ", n)


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
	var views: Array = []
	for i in PATTERNS.size():
		Masonry.pattern = PATTERNS[i]
		var v := WallView.new()
		g.add_child(v)
		var z := -12.0 + i * 6.0
		var d := {"id": 900 + i, "pts": PackedVector2Array([Vector2(-5, z), Vector2(5, z)]), "h": 2.8,
				"col": Catalog.STONE_COLORS[0], "style": "stone", "pattern": PATTERNS[i]}
		v.build(d, g.terrain, [{"s": 6.5, "w": 1.6}])
		v.visible = false
		views.append(v)
		var mi := v.find_child("*", true, false)
		print(PATTERNS[i], " triangles ", _tris(v))
	Masonry.pattern = "classic"
	for i in PATTERNS.size():
		for j in views.size():
			views[j].visible = j == i
		var z := -12.0 + i * 6.0
		game.rig.focus_on(Vector3(0.5, 1.4, z), 8.5)
		game.rig.yaw = deg_to_rad(-18)
		game.rig.pitch_offset = -0.32
		game.rig.snap()
		await _shot("%d_%s" % [i, PATTERNS[i]])
		game.rig.focus_on(Vector3(3.5, 1.2, z), 3.6)
		game.rig.snap()
		await _shot("%d_%s_close" % [i, PATTERNS[i]])
	get_tree().quit()


func _tris(n: Node) -> int:
	var t := 0
	if n is MeshInstance3D and (n as MeshInstance3D).mesh:
		var m: Mesh = (n as MeshInstance3D).mesh
		for s in m.get_surface_count():
			t += m.surface_get_array_index_len(s) / 3
	for c in n.get_children():
		t += _tris(c)
	return t
