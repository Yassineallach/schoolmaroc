extends Node
## Dev helper: lines up the Quaternius kit props, plants and wildlife in an
## empty meadow and saves a few shots.  -- --kitview=/tmp/dir
var game: Game
var out := ""

const ROW_A := ["flowers_white", "flowers_pink", "flowers_blue", "flowers_yellow", "flowers_red", "fern", "plant_leafy", "wheat", "mushrooms"]
const ROW_B := ["bush_b", "bush_berries", "crate", "cart", "stepping_stone"]


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--kitview="):
			out = a.trim_prefix("--kitview=")
	DirAccess.make_dir_recursive_absolute(out)
	game = get_parent()
	_run.call_deferred()


func _shot(n: String) -> void:
	for i in 50:
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
	for i in ROW_A.size():
		var x := -4.0 + i * 1.0
		g.add_prop(ROW_A[i], Vector3(x, g.terrain.height_at(x, 0.0), 0.0), 0.5 * i, 1.0, true, false)
	for i in ROW_B.size():
		var x2 := -4.0 + i * 2.2
		g.add_prop(ROW_B[i], Vector3(x2, g.terrain.height_at(x2, 3.0), 3.0), 0.6, 1.0, true, false)
	g.add_fence(PackedVector2Array([Vector2(-5, -3), Vector2(0, -3.5), Vector2(4, -3)]), "wood")
	g.add_fence(PackedVector2Array([Vector2(-5, -5.5), Vector2(4, -5.5)]), "ornate")
	var animals := ["q_deer", "q_fox", "q_donkey", "q_alpaca"]
	for i in animals.size():
		var w := Wildlife.new()
		w.setup(g, animals[i], i + 1)
		game.life.add_child(w)
		var p := Vector2(-4.0 + i * 2.6, 7.0)
		w.global_position = Vector3(p.x, g.terrain.height_at_v(p), p.y)
		w.rotation.y = 0.5
		w.set_process(false)
		w._play("Idle")
	game.rig.focus_on(Vector3(0, 0.4, 0.5), 9.0)
	game.rig.yaw = 0.0
	game.rig.pitch_offset = -0.25
	game.rig.snap()
	await _shot("1_plants")
	game.rig.focus_on(Vector3(0, 0.6, 3.5), 9.0)
	game.rig.snap()
	await _shot("2_props")
	game.rig.focus_on(Vector3(-0.5, 0.6, -4.2), 9.0)
	game.rig.snap()
	await _shot("3_fences")
	game.rig.focus_on(Vector3(0, 0.8, 7.0), 6.0)
	game.rig.snap()
	await _shot("4_animals")
	get_tree().quit()
