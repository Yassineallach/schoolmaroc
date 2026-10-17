class_name TerrainTool
extends BaseTool
## Paint the land the Tiny Glade way: drag (or tap) on the meadow to paint a
## patch of raised ground. Press on an existing patch and drag up/down to
## change its height (drag it to the ground to remove it) and left/right to
## morph it between a rocky cliff and a soft grassy hill. "Stack" paints new
## patches on top of the ground you start on, building terraces.

const PAINT_SPACING := 0.45
const ADJUST_HEIGHT_PER_PX := 0.018
const ADJUST_FALL_PER_PX := 0.004

var _mode := ""            # "", "paint", "adjust"
var _patch: Dictionary = {}
var _old_bounds := Rect2()
var _start_screen := Vector2.ZERO
var _start_h := 0.0
var _start_fall := 0.0
var _moved := false
var _pending := false
var _since := 0.0
var _brush: MeshInstance3D
var _sound_t := 0.0


func _init() -> void:
	tool_id = "terrain"
	title = "Terrain"
	options = {"shape": "hill", "size": 2.2, "stack": false, "move": false}


func option_defs() -> Array:
	return [
		{"type": "choice", "key": "shape", "items": [
			{"id": "hill", "label": "Hill", "icon": "raise"},
			{"id": "cliff", "label": "Cliff", "icon": "cliff"}]},
		{"type": "slider", "key": "size", "label": "Brush", "min": 0.8, "max": 6.0, "step": 0.1},
		{"type": "toggle", "key": "stack", "label": "Stack", "icon": "stack"},
		{"type": "toggle", "key": "move", "label": "Move", "icon": "hand"},
	]


func hint() -> String:
	return "Paint land on the meadow. Press a hill and drag up/down for height, left/right for cliff ↔ hill. With Move, drag a hill somewhere else."


var _last_ground := Vector2.ZERO


func _default_height() -> float:
	return 1.4 if options.shape == "hill" else 2.0


func _default_fall() -> float:
	return 0.75 if options.shape == "hill" else 0.08


func press(screen: Vector2) -> bool:
	var g = ground(screen)
	if g == null:
		return false
	var at := Vector2(g.x, g.z)
	glade.begin_change()
	_start_screen = screen
	_moved = false
	var hit: Dictionary = {} if options.stack else glade.terrain.patch_at(at)
	if options.get("move", false):
		if hit.is_empty():
			glade.undo_stack.pop_back()
			return false
		_mode = "move"
		_patch = hit
		_last_ground = at
		_old_bounds = Terrain.patch_bounds(_patch)
		Sfx.play("rumble", -10.0, 0.2)
		return true
	if not hit.is_empty():
		_mode = "adjust"
		_patch = hit
		_start_h = float(hit.h)
		_start_fall = float(hit.get("fall", 0.6))
	else:
		_mode = "paint"
		_patch = glade.add_terrain_patch(PackedVector2Array([at]), options.size, _default_height(), _default_fall(), options.stack)
	_old_bounds = Terrain.patch_bounds(_patch)
	_show_brush(at)
	Sfx.play("rumble", -10.0, 0.2)
	return true


func drag(screen: Vector2) -> void:
	if _mode == "":
		return
	if screen.distance_to(_start_screen) > 10.0:
		_moved = true
	if _mode == "move":
		var gm = ground(screen)
		if gm == null:
			return
		var to := Vector2(gm.x, gm.z)
		var dlt := to - _last_ground
		if dlt.length() > 0.2:
			_last_ground = to
			var mp: PackedVector2Array = _patch.pts
			for i in mp.size():
				mp[i] = glade.terrain.clamp_to_play(mp[i] + dlt)
			_patch.pts = mp
			_pending = true
		return
	if _mode == "adjust":
		var d := screen - _start_screen
		_patch.h = clampf(_start_h - d.y * ADJUST_HEIGHT_PER_PX, 0.0, Terrain.PATCH_MAX_H)
		_patch.fall = clampf(_start_fall + d.x * ADJUST_FALL_PER_PX, 0.0, 1.0)
		_pending = true
		return
	var g = ground(screen)
	if g == null:
		return
	var at := Vector2(g.x, g.z)
	var pts: PackedVector2Array = _patch.pts
	if at.distance_to(pts[pts.size() - 1]) >= PAINT_SPACING:
		pts.append(glade.terrain.clamp_to_play(at))
		_patch.pts = pts
		_pending = true
	_show_brush(at)


func process_hold(delta: float) -> void:
	if _mode == "":
		return
	_since += delta
	# reshape the ground at most ~12 times a second while dragging
	if _pending and _since > 0.08:
		_since = 0.0
		_pending = false
		var nb := Terrain.patch_bounds(_patch)
		glade.update_terrain_patch(_patch, _old_bounds)
		_old_bounds = nb
		_sound_t -= delta
		if _sound_t <= 0.0:
			_sound_t = 0.22
			Sfx.play("rumble", -14.0, 0.2)


func release(_screen: Vector2) -> void:
	if _mode == "":
		return
	if _pending:
		glade.update_terrain_patch(_patch, _old_bounds)
		_pending = false
	if _mode == "adjust" and float(_patch.h) < 0.12:
		glade.remove_terrain_patch(_patch)
	_mode = ""
	_patch = {}
	if _brush:
		_brush.visible = false
	glade.terrain_edited()
	Settings.vibrate(15)


func cancel() -> void:
	release(Vector2.ZERO)


func tap(_screen: Vector2) -> void:
	pass # press already painted a round patch


func _show_brush(at: Vector2) -> void:
	if _brush == null:
		_brush = MeshInstance3D.new()
		var torus := TorusMesh.new()
		torus.inner_radius = 0.95
		torus.outer_radius = 1.0
		torus.rings = 40
		torus.ring_segments = 4
		_brush.mesh = torus
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.albedo_color = Color(1, 1, 1, 0.6)
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.no_depth_test = true
		_brush.material_override = mat
		glade.add_child(_brush)
	_brush.visible = _mode == "paint"
	_brush.global_position = Vector3(at.x, glade.terrain.height_at_v(at) + 0.1, at.y)
	_brush.scale = Vector3(options.size, 1, options.size)
