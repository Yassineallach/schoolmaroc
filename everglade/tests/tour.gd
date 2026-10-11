extends Node
## Automated screenshot tour used during development and CI smoke tests:
##   godot --path . -- --tour=/tmp/shots
## Visits the menu, builds a few things with the real tools, toggles time of
## day and seasons, then writes PNGs and quits.

var game: Game
var out_dir := ""


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--tour="):
			out_dir = a.trim_prefix("--tour=")
	DirAccess.make_dir_recursive_absolute(out_dir)
	game = get_parent() as Game
	_run.call_deferred()


func _wait(frames := 30) -> void:
	for i in frames:
		await get_tree().process_frame


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(out_dir.path_join(name + ".png"))
	print("shot ", name)


func _touch(pos: Vector2, pressed: bool, index := 0) -> void:
	var e := InputEventScreenTouch.new()
	e.index = index
	e.position = pos
	e.pressed = pressed
	Input.parse_input_event(e)


func _drag_to(pos: Vector2, rel: Vector2, index := 0) -> void:
	var e := InputEventScreenDrag.new()
	e.index = index
	e.position = pos
	e.relative = rel
	Input.parse_input_event(e)


func _stroke(points: Array, hold_frames := 2) -> void:
	_touch(points[0], true)
	await _wait(hold_frames)
	var prev: Vector2 = points[0]
	for i in range(1, points.size()):
		var a: Vector2 = points[i - 1]
		var b: Vector2 = points[i]
		for k in 8:
			var p := a.lerp(b, (k + 1) / 8.0)
			_drag_to(p, p - prev)
			prev = p
			await _wait(1)
	await _wait(hold_frames)
	_touch(points[-1], false)
	await _wait(6)


func _tap(pos: Vector2) -> void:
	_touch(pos, true)
	await _wait(2)
	_touch(pos, false)
	await _wait(6)


func _check(label: String, ok: bool) -> void:
	print(("PASS " if ok else "FAIL ") + label)
	if not ok:
		failures += 1


var failures := 0


func _tool_tests() -> void:
	game.start_new("meadow")
	game.rig.focus_on(Vector3.ZERO, 30.0)
	game.rig.yaw = 0.0
	game.rig.snap()
	await _wait(20)
	var g := game.glade
	var n0: int = g.data.walls.size()
	game.set_tool("wall")
	await _stroke([Vector2(380, 200), Vector2(640, 170), Vector2(900, 220)])
	_check("wall drawn", g.data.walls.size() == n0 + 1)
	game.set_tool("path")
	await _stroke([Vector2(640, 460), Vector2(650, 300), Vector2(640, 120)])
	await _wait(10)
	_check("path drawn", g.data.paths.size() == 1)
	var wid: int = g.data.walls[-1].id
	_check("path opened an arch in the wall", not g._openings.get(wid, []).is_empty())
	game.set_tool("building")
	await _stroke([Vector2(300, 300), Vector2(430, 320)])
	_check("cottage built", g.data.buildings.size() == 1)
	game.tools["building"].set_option("shape", "tower")
	await _tap(Vector2(960, 330))
	_check("tower built", g.data.buildings.size() == 2 and g.data.buildings[-1].shape == "round")
	game.set_tool("fence")
	await _stroke([Vector2(480, 395), Vector2(640, 405), Vector2(800, 395)])
	_check("fence drawn", g.data.fences.size() == 1)
	await _wait(10)
	_check("gate where the path crosses the fence", not g._openings.get(g.data.fences[0].id, []).is_empty())
	game.set_tool("nature")
	var p0: int = g.data.props.size()
	await _stroke([Vector2(150, 300), Vector2(250, 420)])
	_check("nature brush planted", g.data.props.size() > p0)
	game.set_tool("decor")
	var p1: int = g.data.props.size()
	await _tap(Vector2(1000, 300))
	_check("decoration placed", g.data.props.size() == p1 + 1)
	game.set_tool("details")
	var b: Dictionary = g.data.buildings[0]
	var before: int = b.windows.size()
	var v: BuildingView = g.views[b.id]
	var wp := v.global_transform * Vector3(0, Catalog.PLINTH + 1.3, -b.size.y * 0.5)
	await _tap(game.rig.camera.unproject_position(wp))
	_check("window tool changed windows", b.windows.size() != before)
	game.set_tool("roof")
	game.tools["roof"].set_option("roof", "hip")
	v = g.views[b.id]
	var rp := v.global_transform * Vector3(0, v.eave + v.roof_h * 0.5, 0)
	var sp := game.rig.camera.unproject_position(rp)
	var dbg := g.pick(game.rig.camera, sp)
	print("roof tap at ", sp, " hits ", dbg.get("kind"), " id ", dbg.get("id"), " want ", b.id, " pitch ", b.get("pitch"))
	await _tap(sp)
	_check("roof restyled", g.find(b.id).item.roof == "hip")
	game.set_tool("water")
	var h_before := g.terrain.height_at(-6, 3)
	_touch(game.rig.camera.unproject_position(Vector3(-6, 0, 3)), true)
	await _wait(45)
	_touch(game.rig.camera.unproject_position(Vector3(-6, 0, 3)), false)
	await _wait(5)
	_check("pond dug", g.terrain.height_at(-6, 3) < h_before - 0.3)
	game.set_tool("terrain")
	var h2 := g.terrain.height_at(12, 10)
	_touch(game.rig.camera.unproject_position(Vector3(12, 0, 10)), true)
	await _wait(30)
	_touch(game.rig.camera.unproject_position(Vector3(12, 0, 10)), false)
	await _wait(5)
	_check("hill raised", g.terrain.height_at(12, 10) > h2 + 0.3)
	var walls_before: int = g.data.walls.size()
	game.set_tool("eraser")
	await _stroke([Vector2(470, 175), Vector2(540, 180)])
	_check("eraser cut the wall", g.data.walls.size() != walls_before or Geo.length(g.data.walls[0].pts) < 20.0)
	var undo_depth := g.undo_stack.size()
	game.do_undo()
	await _wait(5)
	_check("undo works", g.undo_stack.size() == undo_depth - 1 and g.redo_stack.size() == 1)
	game.do_redo()
	await _wait(5)
	_check("redo works", g.redo_stack.is_empty())
	# selection + inspector edit through the hand tool
	game.set_tool("hand")
	var bb: Dictionary = g.data.buildings[0]
	var cv: BuildingView = g.views[bb.id]
	await _tap(game.rig.camera.unproject_position(cv.global_transform * Vector3(0, 1.5, 0)))
	_check("tap selects building", game.selected_id == bb.id)
	var floors_before: int = bb.floors
	game._on_inspector_action("floors", 1)
	_check("inspector adds a floor", g.find(bb.id).item.floors == floors_before + 1)
	# save / load round trip
	await game.save_now(false)
	var loaded := GladeStore.load_glade(game.current_id)
	_check("glade saved & loaded", loaded.get("buildings", []).size() == g.data.buildings.size())
	# camera gestures
	var d0 := game.rig.distance
	_touch(Vector2(500, 300), true, 0)
	_touch(Vector2(780, 300), true, 1)
	await _wait(2)
	for k in 10:
		_drag_to(Vector2(500 - k * 8, 300), Vector2(-8, 0), 0)
		_drag_to(Vector2(780 + k * 8, 300), Vector2(8, 0), 1)
		await _wait(1)
	_touch(Vector2(420, 300), false, 0)
	_touch(Vector2(860, 300), false, 1)
	await _wait(5)
	_check("pinch zooms", game.rig.distance < d0)
	game.rig.focus_on(Vector3.ZERO, 26.0)
	game.rig.yaw = deg_to_rad(-35)
	game.rig.snap()
	await _wait(60)
	await _shot("15b_tool_test_result")
	print("TOOL TESTS: %d failure(s)" % failures)


func _run() -> void:
	await _wait(90)
	await _shot("01_menu")
	game.menu._show_templates()
	await _wait(10)
	await _shot("02_menu_new")
	game.start_new("hamlet")
	game.rig.focus_on(Vector3(0, 0, -2), 34.0)
	game.rig.yaw = deg_to_rad(20)
	game.rig.snap()
	await _wait(120)
	await _shot("03_hamlet_day")
	game.rig.focus_on(Vector3(2, 0, -2), 12.0)
	game.rig.yaw = deg_to_rad(-25)
	game.rig.snap()
	await _wait(40)
	await _shot("04_closeup_cottage")
	game.rig.focus_on(Vector3(-9, 0, 8), 13.0)
	game.rig.yaw = deg_to_rad(150)
	game.rig.snap()
	await _wait(40)
	await _shot("05_pond_bridge")
	game.rig.focus_on(Vector3(-1, 0, -14), 13.0)
	game.rig.yaw = deg_to_rad(0)
	game.rig.snap()
	await _wait(40)
	await _shot("06_wall_arch")
	# tools
	game.set_tool("wall")
	await _wait(10)
	await _shot("07_wall_tool_ui")
	game.set_tool("building")
	await _wait(20)
	await _shot("08_building_tool_ui")
	game.set_tool("decor")
	await _wait(60)
	await _shot("09_decor_tool_thumbs")
	game.set_tool("hand")
	var b: Dictionary = game.glade.data.buildings[0]
	game.select(b.id)
	game.rig.focus_on(Vector3(b.c.x, 0, b.c.y), 20.0)
	game.rig.snap()
	await _wait(30)
	await _shot("10_inspector")
	game.select(-1)
	# evening, night, seasons
	game.rig.focus_on(Vector3(0, 0, -2), 30.0)
	game.rig.yaw = deg_to_rad(35)
	game.rig.snap()
	game._set_time(0.72)
	await _wait(40)
	await _shot("11_sunset")
	game._set_time(0.93)
	await _wait(40)
	await _shot("12_night")
	game._set_time(0.4)
	game._cycle_season() # autumn
	await _wait(120)
	await _shot("13_autumn")
	game._cycle_season() # winter
	await _wait(120)
	await _shot("14_winter")
	game._cycle_season()
	game._cycle_season()
	# build things procedurally with the glade API on an empty meadow
	game.start_new("meadow")
	await _wait(30)
	var g := game.glade
	g.add_wall(Geo.smooth(PackedVector2Array([Vector2(-8, -4), Vector2(-2, -7), Vector2(5, -5), Vector2(9, 0)]), 2), 4.2, Catalog.STONE_COLORS[0])
	g.add_path(Geo.smooth(PackedVector2Array([Vector2(0, 8), Vector2(0, 0), Vector2(-1, -10)]), 2), 1.6, "cobble")
	g.add_building({"shape": "rect", "c": Vector2(4, 4), "size": Vector2(6, 4), "rot": 0.5, "floors": 2, "style": "timber",
		"roof": "hip", "roof_col": Catalog.ROOF_COLORS[4], "wall_col": Catalog.WALL_COLORS[2], "pitch": 1.0, "chimney": 0.2})
	g.add_building({"shape": "round", "c": Vector2(-6, 3), "r": 2.0, "rot": 0.0, "floors": 3, "style": "stone",
		"roof": "flat", "roof_col": Catalog.ROOF_COLORS[2], "wall_col": Catalog.WALL_COLORS[0], "pitch": 1.0, "chimney": -99.0})
	g.add_fence(PackedVector2Array([Vector2(-12, 8), Vector2(-4, 10), Vector2(4, 9)]))
	game.rig.focus_on(Vector3(0, 0, 0), 26.0)
	game.rig.yaw = deg_to_rad(-30)
	game.rig.snap()
	await _wait(90)
	await _shot("15_built_meadow")
	await _tool_tests()
	game.enter_photo()
	game.rig.focus_on(Vector3(3, 0, 1), 10.0)
	game.rig.yaw = deg_to_rad(200)
	game.rig.snap()
	await _wait(40)
	await _shot("16_photo_mode")
	print("tour done")
	get_tree().quit()
