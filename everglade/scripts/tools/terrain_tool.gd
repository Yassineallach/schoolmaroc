class_name TerrainTool
extends BaseTool
## Sculpt hills and hollows. Hold to keep shaping.

var held := false
var at := Vector2.ZERO
var flatten_to := 0.0
var _brush: MeshInstance3D
var _sound_t := 0.0


func _init() -> void:
	tool_id = "terrain"
	title = "Terrain"
	options = {"mode": "raise", "size": 3.0, "strength": 1.0}


func option_defs() -> Array:
	return [
		{"type": "choice", "key": "mode", "items": [
			{"id": "raise", "label": "Raise", "icon": "raise"},
			{"id": "lower", "label": "Lower", "icon": "lower"},
			{"id": "smooth", "label": "Smooth", "icon": "smooth"},
			{"id": "flatten", "label": "Flatten", "icon": "flatten"}]},
		{"type": "slider", "key": "size", "label": "Brush", "min": 1.0, "max": 7.0, "step": 0.1},
		{"type": "slider", "key": "strength", "label": "Strength", "min": 0.2, "max": 2.0, "step": 0.1},
	]


func hint() -> String:
	return "Press and hold to sculpt the land."


func mode() -> String:
	return options.mode


func press(screen: Vector2) -> bool:
	var g = ground(screen)
	if g == null:
		return false
	glade.begin_change()
	held = true
	at = Vector2(g.x, g.z)
	flatten_to = g.y
	return true


func drag(screen: Vector2) -> void:
	var g = ground(screen)
	if g != null:
		at = Vector2(g.x, g.z)


func process_hold(delta: float) -> void:
	if not held:
		return
	var rate := 2.2 if mode() in ["raise", "lower", "dig"] else 1.0
	glade.terrain.sculpt(at, options.size, delta * rate * options.strength, mode(), flatten_to)
	_show_brush()
	_sound_t -= delta
	if _sound_t <= 0.0:
		_sound_t = 0.25
		Sfx.play("dig" if mode() == "dig" else "rumble", -12.0, 0.2)


func release(_screen: Vector2) -> void:
	if held:
		held = false
		glade.terrain_edited()
	if _brush:
		_brush.visible = false


func cancel() -> void:
	release(Vector2.ZERO)


func _show_brush() -> void:
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
	_brush.visible = true
	_brush.global_position = Vector3(at.x, glade.terrain.height_at_v(at) + 0.1, at.y)
	_brush.scale = Vector3(options.size, 1, options.size)
