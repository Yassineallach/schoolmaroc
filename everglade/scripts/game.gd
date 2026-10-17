class_name Game
extends Node3D
## Root controller: owns the world, camera, tools and UI; routes touch
## gestures; handles selection/inspector, autosave, photo mode and menus.

enum Mode { MENU, BUILD, PHOTO }

const TAP_TIME := 0.45
const TAP_MOVE := 16.0

var mode := Mode.MENU
var day: DayCycle
var glade: Glade
var rig: CameraRig
var life: Life
var hud: HUD
var menu: MainMenu
var settings_panel: SettingsPanel
var photo_ui: PhotoUI
var tools: Dictionary = {}
var tool: BaseTool
var selected_id := -1
var current_id := ""

var _touches: Dictionary = {} # index -> position
var _ignored: Dictionary = {} # touches that started on UI
var _press_pos := Vector2.ZERO
var _press_time := 0.0
var _press_frame := 0
var _gesture := "" # "", "tool", "pan", "orbit", "multi"
var _moved := false
var _multi_prev: Dictionary = {}
var _mouse_rotate := false
var _mouse_pan := false
var _dirty := false
var _save_timer := 0.0


func _ready() -> void:
	get_tree().quit_on_go_back = false
	get_tree().auto_accept_quit = false
	day = DayCycle.new()
	day.name = "DayCycle"
	add_child(day)
	glade = Glade.new()
	glade.name = "Glade"
	add_child(glade)
	rig = CameraRig.new()
	rig.name = "CameraRig"
	rig.terrain = glade.terrain
	rig.height_probe = glade.ceiling_at
	add_child(rig)
	day.follow = rig.camera
	var night_lights := NightLights.new()
	night_lights.name = "NightLights"
	add_child(night_lights)
	night_lights.setup(glade, rig, day)
	life = Life.new()
	life.name = "Life"
	add_child(life)
	life.setup(glade, day)
	hud = HUD.new()
	add_child(hud)
	menu = MainMenu.new()
	add_child(menu)
	settings_panel = SettingsPanel.new()
	add_child(settings_panel)
	photo_ui = PhotoUI.new()
	add_child(photo_ui)
	_make_tools()
	_connect_ui()
	glade.changed.connect(_on_glade_changed)
	glade.structure_built.connect(_on_structure_built)
	day.changed.connect(func(): hud.set_time(day.time_of_day, day.is_night()))
	enter_menu(true)
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--tour=") and ResourceLoader.exists("res://tests/tour.gd"):
			var tour: Node = load("res://tests/tour.gd").new()
			add_child(tour)
		if a.begins_with("--closeup=") and ResourceLoader.exists("res://tests/closeup.gd"):
			add_child(load("res://tests/closeup.gd").new())
		if a == "--profile" and ResourceLoader.exists("res://tests/profile.gd"):
			add_child(load("res://tests/profile.gd").new())
		if a.begins_with("--soak") and ResourceLoader.exists("res://tests/soak.gd"):
			add_child(load("res://tests/soak.gd").new())
		if a.begins_with("--wallstyles=") and ResourceLoader.exists("res://tests/wallstyles.gd"):
			add_child(load("res://tests/wallstyles.gd").new())
		if a.begins_with("--handles=") and ResourceLoader.exists("res://tests/handles.gd"):
			add_child(load("res://tests/handles.gd").new())
		if a.begins_with("--editview=") and ResourceLoader.exists("res://tests/editview.gd"):
			add_child(load("res://tests/editview.gd").new())
		if a.begins_with("--kitview=") and ResourceLoader.exists("res://tests/kitview.gd"):
			add_child(load("res://tests/kitview.gd").new())
		if a.begins_with("--showcase=") and ResourceLoader.exists("res://tests/showcase.gd"):
			add_child(load("res://tests/showcase.gd").new())
		if a.begins_with("--horizon=") and ResourceLoader.exists("res://tests/horizon.gd"):
			add_child(load("res://tests/horizon.gd").new())


func _make_tools() -> void:
	for t in [HandTool.new(), WallTool.new(), BuildingTool.new(), RoofTool.new(), DetailsTool.new(),
			FenceTool.new(), PathTool.new(), NatureTool.new(), DecorTool.new(), WaterTool.new(),
			TerrainTool.new(), EraserTool.new()]:
		var bt := t as BaseTool
		bt.setup(self, glade)
		add_child(bt)
		tools[bt.tool_id] = bt
	tools["building"].tool_id = "building"


func _connect_ui() -> void:
	hud.tool_selected.connect(set_tool)
	hud.option_changed.connect(func(k, v):
		if tool:
			tool.set_option(k, v))
	hud.undo_pressed.connect(do_undo)
	hud.redo_pressed.connect(do_redo)
	hud.home_pressed.connect(func(): enter_menu())
	hud.photo_pressed.connect(enter_photo)
	hud.settings_pressed.connect(func(): settings_panel.open())
	hud.time_changed.connect(_set_time)
	hud.season_pressed.connect(_cycle_season)
	hud.inspector_action.connect(_on_inspector_action)
	menu.continue_pressed.connect(func():
		var id := GladeStore.last_glade_id()
		if id != "":
			open_glade(id))
	menu.new_glade.connect(start_new)
	menu.open_glade.connect(open_glade)
	menu.settings_pressed.connect(func(): settings_panel.open())
	photo_ui.exit_photo.connect(exit_photo)
	photo_ui.shutter.connect(take_photo)
	photo_ui.time_changed.connect(_set_time)


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------
func enter_menu(first := false) -> void:
	if not first and mode == Mode.BUILD:
		await save_now(true)
	mode = Mode.MENU
	select(-1)
	if tool:
		tool.deactivate()
	hud.visible = false
	photo_ui.visible = false
	life.clear()
	GladeTemplates.build(glade, "hamlet")
	glade.show_boundary(false)
	current_id = ""
	day.season = 1
	day.time_of_day = 0.36
	rig.photo_mode = false
	rig.auto_orbit = true
	rig.focus_on(Vector3(0, 0, -1), 36.0)
	rig.pitch_offset = 0.0
	rig.snap()
	menu.open()


func start_new(template: String) -> void:
	GladeTemplates.build(glade, template)
	current_id = GladeStore.new_id()
	glade.data.time = 0.38
	glade.data.season = 1
	_enter_build()
	save_now(false)


func open_glade(id: String) -> void:
	var d := GladeStore.load_glade(id)
	if d.is_empty():
		hud.toast("Could not open glade")
		return
	glade.load_data(d)
	current_id = id
	_enter_build()


func _enter_build() -> void:
	mode = Mode.BUILD
	menu.close()
	hud.visible = true
	life.clear()
	rig.auto_orbit = false
	rig.photo_mode = false
	rig.focus_on(Vector3.ZERO, 30.0)
	day.season = glade.data.get("season", 1)
	day.time_of_day = glade.data.get("time", 0.38)
	hud.set_season(DayCycle.SEASON_NAMES[day.season])
	hud.set_time(day.time_of_day, day.is_night())
	set_tool("hand")
	_update_undo()
	hud.show_hint("Pick a tool below and draw right on the meadow. Two fingers move the camera.", "welcome")


func enter_photo() -> void:
	if mode != Mode.BUILD:
		return
	mode = Mode.PHOTO
	select(-1)
	if tool:
		tool.cancel()
	hud.visible = false
	glade.show_boundary(false)
	photo_ui.open(day.time_of_day)
	rig.photo_mode = true
	hud.show_hint("", "")


func exit_photo() -> void:
	mode = Mode.BUILD
	if tool:
		glade.show_boundary(tool.tool_id != "hand")
	photo_ui.visible = false
	hud.visible = true
	rig.photo_mode = false
	rig.pitch_offset = 0.0
	rig.zoom_by(1.0)


func take_photo() -> void:
	photo_ui.hide_bar(true)
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	photo_ui.hide_bar(false)
	photo_ui.flash()
	Sfx.play("shutter")
	Settings.vibrate(30)
	var path := GladeStore.save_photo(img)
	hud.toast("Photo saved")
	print("Photo saved to ", path)


func set_tool(id: String) -> void:
	if not tools.has(id):
		return
	if tool:
		tool.deactivate()
	tool = tools[id]
	tool.activate()
	hud.set_tool(id, tool)
	glade.show_boundary(id != "hand")
	if id != "hand":
		select(-1)


# ---------------------------------------------------------------------------
# Selection & inspector
# ---------------------------------------------------------------------------
func select(id: int) -> void:
	selected_id = id
	if id < 0:
		glade.hide_selection()
		hud.hide_inspector()
		return
	var f := glade.find(id)
	if f.is_empty():
		select(-1)
		return
	glade.show_selection(id)
	hud.show_inspector(_inspector_defs(f), _inspector_values(f))


func _inspector_defs(f: Dictionary) -> Array:
	var item: Dictionary = f.item
	match f.type:
		"buildings":
			var round_b: bool = item.shape == "round"
			var roofs: Array = []
			for r in (Catalog.ROUND_ROOFS if round_b else Catalog.RECT_ROOFS):
				roofs.append({"id": r, "label": Catalog.ROOF_LABELS[r], "icon": r})
			var styles: Array = []
			for s in Catalog.STYLES:
				if round_b and (s == "timber" or s == "lakeside"):
					continue
				styles.append({"id": s, "label": s.capitalize(), "icon": s})
			var size_actions: Array = [
				{"id": "bigger", "icon": "plus", "label": "Wider"}, {"id": "smaller", "icon": "minus", "label": "Narrower"}]
			if not round_b:
				size_actions = [
					{"id": "longer", "icon": "plus", "label": "Longer"}, {"id": "shorter", "icon": "minus", "label": "Shorter"},
					{"id": "wider", "icon": "plus", "label": "Deeper"}, {"id": "narrower", "icon": "minus", "label": "Shallower"},
					{"id": "rotl", "icon": "rotl", "label": "Turn"}, {"id": "rotr", "icon": "rotr", "label": "Turn"}]
			var extra: Array = [{"id": "windows", "icon": "window", "label": "Windows"}, {"id": "clear_windows", "icon": "close", "label": "No windows"}]
			if not round_b:
				extra.append({"id": "chimney", "icon": "chimney", "label": "Chimney"})
			extra.append({"id": "ivy", "icon": "ivy", "label": "Ivy"})
			extra.append({"id": "clone", "icon": "clone", "label": "Copy"})
			extra.append({"id": "delete", "icon": "trash", "label": "Remove"})
			return [
				{"type": "title", "text": "Tower" if round_b else "Cottage"},
				{"type": "stepper", "key": "floors", "label": "Floors", "value": item.floors},
				{"type": "choice", "key": "roof", "items": roofs},
				{"type": "slider", "key": "pitch", "label": "Roof", "min": 0.5, "max": 1.8, "step": 0.05},
				{"type": "colors", "key": "roof_col", "colors": Catalog.ROOF_COLORS},
				{"type": "choice", "key": "style", "items": styles},
				{"type": "colors", "key": "wall_col", "colors": Catalog.WALL_COLORS},
				{"type": "actions", "items": size_actions},
				{"type": "actions", "items": extra},
			]
		"walls":
			return [
				{"type": "title", "text": "Wall"},
				{"type": "choice", "key": "style", "items": [
					{"id": "rendered", "label": "Rendered", "icon": "wall_rendered"}, {"id": "stone", "label": "Bare stone", "icon": "wall"}]},
				{"type": "choice", "key": "pattern", "items": [
					{"id": "glade", "label": "Hand-laid", "icon": "wall_glade"}, {"id": "kit", "label": "Rounded", "icon": "wall_kit"},
					{"id": "rubble", "label": "Fieldstone", "icon": "wall_rubble"}, {"id": "classic", "label": "Coursed", "icon": "wall"},
					{"id": "brick", "label": "Brick", "icon": "wall_brick"}, {"id": "ashlar", "label": "Ashlar", "icon": "wall_ashlar"}]},
				{"type": "slider", "key": "h", "label": "Height", "min": 0.8, "max": 7.0, "step": 0.1},
				{"type": "colors", "key": "col", "colors": Catalog.STONE_COLORS},
				{"type": "actions", "items": [{"id": "more_pts", "icon": "plus", "label": "More points"}, {"id": "fewer_pts", "icon": "minus", "label": "Fewer points"}, {"id": "straighten", "icon": "ruler", "label": "Straighten"}, {"id": "cut", "icon": "cut", "label": "Cut"}]},
				{"type": "actions", "items": [{"id": "ivy", "icon": "ivy", "label": "Ivy"}, {"id": "clone", "icon": "clone", "label": "Copy"}, {"id": "delete", "icon": "trash", "label": "Remove"}]},
				{"type": "label", "text": "Pull the dots to reshape it and the top handle for height. Paths through a wall open an archway; a path ending at it adds a door."},
			]
		"fences":
			return [
				{"type": "title", "text": "Fence"},
				{"type": "choice", "key": "style", "items": [
					{"id": "wood", "label": "Rustic", "icon": "fence"}, {"id": "ornate", "label": "Ornate", "icon": "fence_ornate"}]},
				{"type": "actions", "items": [{"id": "more_pts", "icon": "plus", "label": "More points"}, {"id": "fewer_pts", "icon": "minus", "label": "Fewer points"}, {"id": "straighten", "icon": "ruler", "label": "Straighten"}, {"id": "cut", "icon": "cut", "label": "Cut"}]},
				{"type": "actions", "items": [{"id": "clone", "icon": "clone", "label": "Copy"}, {"id": "delete", "icon": "trash", "label": "Remove"}]},
				{"type": "label", "text": "Pull the dots to reshape it. Paths crossing a fence get a little gate."},
			]
		"paths":
			return [
				{"type": "title", "text": "Path"},
				{"type": "choice", "key": "style", "items": [
					{"id": "dirt", "label": "Dirt", "icon": "path"}, {"id": "cobble", "label": "Cobbles", "icon": "cobble"},
					{"id": "paved", "label": "Paved", "icon": "paved"}, {"id": "stones", "label": "Stepping", "icon": "stones"}]},
				{"type": "slider", "key": "w", "label": "Width", "min": 0.8, "max": 3.2, "step": 0.1},
				{"type": "actions", "items": [{"id": "more_pts", "icon": "plus", "label": "More points"}, {"id": "fewer_pts", "icon": "minus", "label": "Fewer points"}, {"id": "straighten", "icon": "ruler", "label": "Straighten"}, {"id": "cut", "icon": "cut", "label": "Cut"}]},
				{"type": "actions", "items": [{"id": "clone", "icon": "clone", "label": "Copy"}, {"id": "delete", "icon": "trash", "label": "Remove"}]},
			]
		"props":
			return [
				{"type": "title", "text": String(item.kind).replace("_", " ").capitalize()},
				{"type": "actions", "items": [
					{"id": "rotl", "icon": "rotl", "label": "Turn"}, {"id": "rotr", "icon": "rotr", "label": "Turn"},
					{"id": "bigger", "icon": "plus", "label": "Bigger"}, {"id": "smaller", "icon": "minus", "label": "Smaller"},
					{"id": "clone", "icon": "clone", "label": "Copy"}, {"id": "delete", "icon": "trash", "label": "Remove"}]},
				{"type": "label", "text": "Drag it to move it; pull the blue handle to turn it."},
			]
	return []


func _inspector_values(f: Dictionary) -> Dictionary:
	var item: Dictionary = f.item
	var v := item.duplicate()
	if item.has("roof_col"):
		v.roof_col = _closest_index(Catalog.ROOF_COLORS, item.roof_col)
	if item.has("wall_col"):
		v.wall_col = _closest_index(Catalog.WALL_COLORS, item.wall_col)
	if f.type == "walls":
		v.col = _closest_index(Catalog.STONE_COLORS, item.get("col", Catalog.STONE_COLORS[0]))
		v.pattern = item.get("pattern", "classic")
	return v


func _closest_index(arr: Array, c: Color) -> int:
	var best := 0
	var bd := INF
	for i in arr.size():
		var o: Color = arr[i]
		var d := Vector3(o.r - c.r, o.g - c.g, o.b - c.b).length()
		if d < bd:
			bd = d
			best = i
	return best


func _on_inspector_action(action: String, value: Variant) -> void:
	var f := glade.find(selected_id)
	if f.is_empty():
		return
	var item: Dictionary = f.item
	var rebuild_panel := false
	glade.begin_change()
	match action:
		"delete":
			glade.remove(selected_id)
			Sfx.play("erase")
			select(-1)
			return
		"cut":
			glade.undo_stack.pop_back()
			(tools["hand"] as HandTool).cut_id = selected_id
			hud.toast("Tap the spot to cut")
			return
		"more_pts", "fewer_pts":
			var k: int = item.get("knots", HandTool.LINE_HANDLES)
			item.knots = clampi(k + (3 if action == "more_pts" else -3), 3, 24)
			(tools["hand"] as HandTool)._for_id = -2
			_update_undo()
			return
		"straighten":
			var pts: PackedVector2Array = item.pts
			item.pts = Geo.resample(PackedVector2Array([pts[0], pts[pts.size() - 1]]), 1.0)
		"clone":
			var copy := glade.clone(selected_id)
			if copy >= 0:
				Sfx.play("place_stone", -4.0)
				Settings.vibrate(12)
				select(copy)
			else:
				glade.undo_stack.pop_back()
			_update_undo()
			return
		"floors":
			item.floors = clampi(item.floors + int(value), 1, 6)
			rebuild_panel = true
		"roof":
			item.roof = value
		"pitch":
			item.pitch = value
		"roof_col":
			item.roof_col = Catalog.ROOF_COLORS[value]
		"wall_col":
			item.wall_col = Catalog.WALL_COLORS[value]
		"style":
			item.style = value
		"pattern":
			item.pattern = value
		"col":
			item.col = Catalog.STONE_COLORS[value]
		"h":
			item.h = value
		"w":
			item.w = value
		"longer", "shorter", "wider", "narrower":
			var s: Vector2 = item.size
			match action:
				"longer": s.x = minf(s.x + 0.8, 16.0)
				"shorter": s.x = maxf(s.x - 0.8, 3.0)
				"wider": s.y = minf(s.y + 0.5, 8.0)
				"narrower": s.y = maxf(s.y - 0.5, 2.8)
			item.size = s
		"bigger", "smaller":
			var k := 1.12 if action == "bigger" else 1.0 / 1.12
			if f.type == "props":
				item.s = clampf(item.get("s", 1.0) * k, 0.4, 2.5)
			else:
				item.r = clampf(item.r * k, 1.2, 5.0)
		"rotl", "rotr":
			var d := 0.2618 * (1.0 if action == "rotl" else -1.0)
			if f.type == "props":
				item.r = item.get("r", 0.0) + d
			else:
				item.rot = item.get("rot", 0.0) + d
		"chimney":
			item.chimney = 0.3 if item.get("chimney", BuildingView.NO_CHIMNEY) <= BuildingView.NO_CHIMNEY + 1.0 else BuildingView.NO_CHIMNEY
		"windows":
			item.windows = BuildingView.default_windows(item)
		"clear_windows":
			item.windows = []
		"ivy":
			var cur: float = item.get("ivy", 0.0)
			item.ivy = 0.0 if cur > 0.5 else 1.0
	glade.refresh(selected_id, false)
	Sfx.play("place_wood", -6.0)
	Settings.vibrate(8)
	glade.show_selection(selected_id)
	if rebuild_panel:
		hud.show_inspector(_inspector_defs(f), _inspector_values(f))


# ---------------------------------------------------------------------------
# Undo, time, seasons, saving
# ---------------------------------------------------------------------------
func do_undo() -> void:
	if glade.can_undo():
		glade.undo()
		Sfx.play("undo")
		select(-1)
	_update_undo()


func do_redo() -> void:
	if glade.can_redo():
		glade.redo()
		Sfx.play("undo", 0.0, 0.0)
		select(-1)
	_update_undo()


func _update_undo() -> void:
	hud.update_undo(glade.can_undo(), glade.can_redo())


func _set_time(v: float) -> void:
	day.time_of_day = v
	glade.data.time = v


func _cycle_season() -> void:
	day.season = (day.season + 1) % 4
	glade.data.season = day.season
	hud.set_season(DayCycle.SEASON_NAMES[day.season])
	hud.toast(DayCycle.SEASON_NAMES[day.season])
	Sfx.play("season")
	_on_glade_changed()


func _on_glade_changed() -> void:
	_update_undo()
	if mode != Mode.MENU:
		_dirty = true
		_save_timer = 2.0


func _on_structure_built(_kind: String, pos: Vector3) -> void:
	if mode == Mode.MENU:
		return
	var p := CPUParticles3D.new()
	p.one_shot = true
	p.amount = 24
	p.lifetime = 0.9
	p.explosiveness = 0.9
	p.direction = Vector3.UP
	p.spread = 70.0
	p.initial_velocity_min = 1.0
	p.initial_velocity_max = 2.5
	p.gravity = Vector3(0, -2.0, 0)
	p.scale_amount_min = 0.5
	p.scale_amount_max = 1.2
	var m := SphereMesh.new()
	m.radius = 0.12
	m.height = 0.24
	m.radial_segments = 6
	m.rings = 3
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.92, 0.88, 0.8, 0.8)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.material = mat
	p.mesh = m
	add_child(p)
	p.global_position = pos + Vector3.UP * 0.3
	p.emitting = true
	get_tree().create_timer(1.5).timeout.connect(p.queue_free)


func _process(delta: float) -> void:
	if _dirty:
		_save_timer -= delta
		if _save_timer <= 0.0:
			_dirty = false
			save_now(false)
	if (_gesture == "tool") and tool:
		tool.process_hold(delta)
	if mode != Mode.MENU:
		_keyboard_camera(delta)


func save_now(with_thumb: bool) -> void:
	if current_id == "" or mode == Mode.MENU:
		return
	var thumb: Image = null
	if with_thumb:
		var hud_was := hud.visible
		hud.visible = false
		glade.hide_selection()
		await RenderingServer.frame_post_draw
		thumb = get_viewport().get_texture().get_image()
		hud.visible = hud_was
		if thumb:
			thumb.resize(384, 216, Image.INTERPOLATE_BILINEAR)
	GladeStore.save(current_id, glade.to_data(), thumb)


func _notification(what: int) -> void:
	match what:
		NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_APPLICATION_FOCUS_OUT:
			if mode != Mode.MENU and current_id != "":
				GladeStore.save(current_id, glade.to_data())
		NOTIFICATION_WM_CLOSE_REQUEST:
			if mode != Mode.MENU and current_id != "":
				GladeStore.save(current_id, glade.to_data())
			get_tree().quit()
		NOTIFICATION_WM_GO_BACK_REQUEST:
			_on_back()


func _on_back() -> void:
	if settings_panel.visible:
		settings_panel.close()
	elif mode == Mode.PHOTO:
		exit_photo()
	elif mode == Mode.BUILD:
		if selected_id >= 0:
			select(-1)
		elif tool and tool.tool_id != "hand":
			set_tool("hand")
		else:
			enter_menu()
	else:
		if menu._panel.visible:
			menu._panel.visible = false
		else:
			get_tree().quit()


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------
func _unhandled_input(event: InputEvent) -> void:
	if settings_panel.visible:
		return
	if event is InputEventScreenTouch:
		_on_touch(event)
	elif event is InputEventScreenDrag:
		_on_drag(event)
	elif event is InputEventMouseButton:
		_on_mouse_button(event)
	elif event is InputEventMouseMotion:
		var mm := event as InputEventMouseMotion
		if _mouse_rotate:
			rig.rotate_by(-mm.relative.x * 0.006)
			rig.tilt_by(mm.relative.y * 0.004)
		elif _mouse_pan:
			rig.pan_screen(mm.relative)
	elif event is InputEventKey and event.pressed and not event.echo:
		_on_key(event)
	elif event is InputEventMagnifyGesture:
		rig.zoom_by(1.0 / (event as InputEventMagnifyGesture).factor)
	elif event is InputEventPanGesture:
		rig.pan_screen(-(event as InputEventPanGesture).delta * 8.0)


func _over_ui(pos: Vector2) -> bool:
	if mode == Mode.MENU:
		return true
	if mode == Mode.PHOTO:
		return photo_ui.is_over_ui(pos)
	return hud.is_over_ui(pos)


func _on_touch(e: InputEventScreenTouch) -> void:
	if e.pressed:
		if _over_ui(e.position):
			_ignored[e.index] = true
			return
		_touches[e.index] = e.position
		if _touches.size() == 1:
			_press_pos = e.position
			_press_time = Time.get_ticks_msec() / 1000.0
			_press_frame = Engine.get_process_frames()
			_moved = false
			_gesture = ""
			if mode == Mode.BUILD and tool and tool.press(e.position):
				_gesture = "tool"
			else:
				_gesture = "orbit" if mode == Mode.PHOTO else "pan"
		elif _touches.size() == 2:
			if _gesture == "tool":
				tool.cancel()
			_gesture = "multi"
			_multi_prev = _touches.duplicate()
	else:
		if _ignored.has(e.index):
			_ignored.erase(e.index)
			return
		if not _touches.has(e.index):
			return
		_touches.erase(e.index)
		if _gesture == "multi":
			if _touches.is_empty():
				_gesture = ""
			return
		if _touches.is_empty():
			var held := Time.get_ticks_msec() / 1000.0 - _press_time
			# a still finger is a tap; drawing tools need it to be quick so
			# a long press that never moved does not lose a stroke
			# a release within a couple of frames is always a tap, even when a
			# slow device stretches those frames past TAP_TIME
			var quick := Engine.get_process_frames() - _press_frame <= 2
			var is_tap := not _moved and (held < TAP_TIME or quick or (_gesture != "tool" and held < 1.0))
			if _gesture == "tool":
				if is_tap:
					tool.cancel()
					_handle_tap(e.position)
				else:
					tool.release(e.position)
			elif is_tap:
				_handle_tap(e.position)
			_gesture = ""
			_update_undo()


func _handle_tap(pos: Vector2) -> void:
	# animals respond to a tap whatever the tool
	var cam := rig.camera
	var creature := life.pick(cam.project_ray_origin(pos), cam.project_ray_normal(pos))
	if creature and (mode == Mode.PHOTO or tool == null or tool.tool_id in ["hand", "nature", "decor", "details", "roof"]):
		creature.pet()
		return
	if mode == Mode.BUILD and tool:
		tool.tap(pos)


func _on_drag(e: InputEventScreenDrag) -> void:
	if _ignored.has(e.index) or not _touches.has(e.index):
		return
	_touches[e.index] = e.position
	if e.position.distance_to(_press_pos) > TAP_MOVE:
		_moved = true
	match _gesture:
		"tool":
			if _moved:
				tool.drag(e.position)
		"pan":
			if _moved:
				rig.pan_screen(e.relative)
		"orbit":
			rig.rotate_by(-e.relative.x * 0.006)
			rig.tilt_by(e.relative.y * 0.004)
		"multi":
			_multi_gesture()


func _multi_gesture() -> void:
	var keys := _touches.keys()
	if keys.size() < 2:
		return
	var a: Vector2 = _touches[keys[0]]
	var b: Vector2 = _touches[keys[1]]
	if not _multi_prev.has(keys[0]) or not _multi_prev.has(keys[1]):
		_multi_prev = _touches.duplicate()
		return
	var pa: Vector2 = _multi_prev[keys[0]]
	var pb: Vector2 = _multi_prev[keys[1]]
	var c := (a + b) * 0.5
	var pc := (pa + pb) * 0.5
	rig.pan_screen(c - pc)
	var d := a.distance_to(b)
	var pd := pa.distance_to(pb)
	if pd > 10.0 and d > 10.0:
		rig.zoom_by(pd / d)
	var ang := (b - a).angle()
	var pang := (pb - pa).angle()
	var twist := angle_difference(pang, ang)
	rig.rotate_by(-twist if not Settings.invert_rotate else twist)
	_multi_prev = _touches.duplicate()


func _on_mouse_button(e: InputEventMouseButton) -> void:
	match e.button_index:
		MOUSE_BUTTON_WHEEL_UP:
			if e.pressed:
				rig.zoom_by(0.9)
		MOUSE_BUTTON_WHEEL_DOWN:
			if e.pressed:
				rig.zoom_by(1.1)
		MOUSE_BUTTON_RIGHT:
			_mouse_rotate = e.pressed
		MOUSE_BUTTON_MIDDLE:
			_mouse_pan = e.pressed


func _on_key(e: InputEventKey) -> void:
	var ctrl := e.ctrl_pressed or e.meta_pressed
	if ctrl and e.keycode == KEY_Z:
		if e.shift_pressed:
			do_redo()
		else:
			do_undo()
		return
	if ctrl and e.keycode == KEY_Y:
		do_redo()
		return
	match e.keycode:
		KEY_ESCAPE:
			_on_back()
		KEY_DELETE, KEY_BACKSPACE:
			if selected_id >= 0:
				_on_inspector_action("delete", true)
		KEY_P:
			if mode == Mode.BUILD:
				enter_photo()
			elif mode == Mode.PHOTO:
				exit_photo()
		KEY_F12:
			take_photo()
	if mode == Mode.BUILD and e.keycode >= KEY_1 and e.keycode <= KEY_9:
		var idx := int(e.keycode - KEY_1)
		if idx < HUD.TOOLS.size():
			set_tool(HUD.TOOLS[idx].id)
	if mode == Mode.BUILD and e.keycode == KEY_0:
		set_tool("terrain")
	if mode == Mode.BUILD and e.keycode == KEY_MINUS:
		set_tool("eraser")


func _keyboard_camera(delta: float) -> void:
	if get_viewport().gui_get_focus_owner() != null:
		return
	var v := Vector2.ZERO
	if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
		v.y += 1
	if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
		v.y -= 1
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
		v.x -= 1
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
		v.x += 1
	if v != Vector2.ZERO:
		var right := Vector3(cos(rig.yaw), 0, -sin(rig.yaw))
		var fwd := Vector3(-sin(rig.yaw), 0, -cos(rig.yaw))
		rig.pan_world((right * v.x + fwd * v.y) * delta * rig.distance * 0.6)
	if Input.is_key_pressed(KEY_Q):
		rig.rotate_by(delta * 1.2)
	if Input.is_key_pressed(KEY_E):
		rig.rotate_by(-delta * 1.2)
