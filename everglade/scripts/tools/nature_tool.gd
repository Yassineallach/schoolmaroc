class_name NatureTool
extends BaseTool
## Paint forests, bushes, flowers and rocks with a soft brush.

var painting := false
var _last := Vector2.INF
var _rng := RandomNumberGenerator.new()
var _brush: MeshInstance3D


func _init() -> void:
	tool_id = "nature"
	title = "Nature"
	options = {"family": "forest", "size": 2.0}
	_rng.randomize()


func option_defs() -> Array:
	var items: Array = []
	for key in Catalog.NATURE:
		items.append({"id": key, "label": Catalog.NATURE[key].label, "icon": key})
	return [
		{"type": "choice", "key": "family", "items": items},
		{"type": "slider", "key": "size", "label": "Brush", "min": 0.5, "max": 5.0, "step": 0.1},
	]


func hint() -> String:
	return "Drag to paint nature. Tap to place a single plant."


func press(screen: Vector2) -> bool:
	var g = ground(screen)
	if g == null:
		return false
	glade.begin_change()
	painting = true
	_last = Vector2.INF
	_paint_at(Vector2(g.x, g.z))
	return true


func drag(screen: Vector2) -> void:
	if not painting:
		return
	var g = ground(screen)
	if g != null:
		_paint_at(Vector2(g.x, g.z))


func release(_screen: Vector2) -> void:
	painting = false
	_hide_brush()


func cancel() -> void:
	if painting:
		painting = false
		glade.undo()
		glade.redo_stack.clear()
	_hide_brush()


func tap(screen: Vector2) -> void:
	var g = ground(screen)
	if g == null:
		return
	glade.begin_change()
	var fam: Dictionary = Catalog.NATURE[options.family]
	_place(fam, Vector2(g.x, g.z), true)


func _paint_at(c: Vector2) -> void:
	_show_brush(c)
	var fam: Dictionary = Catalog.NATURE[options.family]
	var spacing: float = fam.spacing
	if _last != Vector2.INF and _last.distance_to(c) < spacing * 0.6:
		return
	_last = c
	var radius: float = options.size
	var tries := int(clampf(radius * radius / (spacing * spacing) * 2.0, 1.0, 10.0))
	for i in tries:
		var a := _rng.randf() * TAU
		var r := sqrt(_rng.randf()) * radius
		_place(fam, c + Vector2(cos(a), sin(a)) * r, false)


func _place(fam: Dictionary, p: Vector2, force: bool) -> void:
	var t := glade.terrain
	if not t.in_play_area(p, 0.3):
		return
	if t.height_at_v(p) < Terrain.WATER_LEVEL + 0.05:
		return
	if glade.is_blocked(p):
		return
	var kinds: Array = fam.kinds
	var spacing: float = fam.spacing
	if not force:
		for other in glade.data.props:
			var op: Vector3 = other.p
			if kinds.has(other.kind) and Vector2(op.x, op.z).distance_to(p) < spacing:
				return
	var kind: String = kinds[_rng.randi() % kinds.size()]
	var sr: Vector2 = fam.scale
	var pos := Vector3(p.x, t.height_at_v(p) - 0.03, p.y)
	glade.add_prop(kind, pos, _rng.randf() * TAU, _rng.randf_range(sr.x, sr.y), options.family in ["rocks", "flowers"])
	Sfx.play("plant", -6.0, 0.25)
	Settings.vibrate(6)


func _show_brush(c: Vector2) -> void:
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
		_brush.material_override = mat
		glade.add_child(_brush)
	_brush.visible = true
	_brush.global_position = Vector3(c.x, glade.terrain.height_at_v(c) + 0.08, c.y)
	_brush.scale = Vector3(options.size, 1, options.size)


func _hide_brush() -> void:
	if _brush:
		_brush.visible = false
