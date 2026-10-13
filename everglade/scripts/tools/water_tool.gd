class_name WaterTool
extends BaseTool
## Dig ponds (water fills anything below the waterline) or fill them back in.
## This is the one tool that goes below the meadow's base level.

var held := false
var at := Vector2.ZERO
var _brush: MeshInstance3D
var _sound_t := 0.0


func _init() -> void:
	tool_id = "water"
	title = "Ponds"
	options = {"mode": "dig", "size": 2.5, "strength": 1.0}


func option_defs() -> Array:
	return [
		{"type": "choice", "key": "mode", "items": [
			{"id": "dig", "label": "Dig pond", "icon": "water"},
			{"id": "fill", "label": "Fill in", "icon": "fill"}]},
		{"type": "slider", "key": "size", "label": "Brush", "min": 1.0, "max": 6.0, "step": 0.1},
	]


func hint() -> String:
	return "Hold to dig a pond; ducks will find it. Paths across become bridges."


func press(screen: Vector2) -> bool:
	var g = ground(screen)
	if g == null:
		return false
	glade.begin_change()
	held = true
	at = Vector2(g.x, g.z)
	if options.mode == "dig":
		Sfx.play("splash", -6.0)
	return true


func drag(screen: Vector2) -> void:
	var g = ground(screen)
	if g != null:
		at = Vector2(g.x, g.z)


func process_hold(delta: float) -> void:
	if not held:
		return
	if options.mode == "dig":
		glade.terrain.sculpt(at, options.size, delta * 2.2 * options.strength, "dig")
	else:
		glade.terrain.sculpt(at, options.size, delta * options.strength, "flatten", 0.05)
	_show_brush()
	_sound_t -= delta
	if _sound_t <= 0.0:
		_sound_t = 0.25
		Sfx.play("dig", -12.0, 0.2)


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
		mat.albedo_color = Color(0.7, 0.9, 1.0, 0.6)
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.no_depth_test = true
		_brush.material_override = mat
		glade.add_child(_brush)
	_brush.visible = true
	_brush.global_position = Vector3(at.x, glade.terrain.height_at_v(at) + 0.1, at.y)
	_brush.scale = Vector3(options.size, 1, options.size)
