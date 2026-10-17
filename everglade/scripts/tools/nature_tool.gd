class_name NatureTool
extends BaseTool
## Paint forests, bushes, flowers, meadow, grain and rocks with a soft
## brush, as in Tiny Glade: painting over flowers again makes them fuller
## and turns some into bushes; flowers painted on water become lilies and a
## tree planted in a pond gets lily pads round it. Hold Ctrl to rub plants
## of the chosen kind away.

const BLOOMS := ["flowers", "lavender", "meadow", "grain", "ferns"]

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
	return "Drag to paint nature; paint flowers again to thicken them into bushes, or onto water for lilies. Tap for a single plant. Ctrl rubs plants out."


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
	if Input.is_key_pressed(KEY_CTRL):
		if glade.remove_props_near(c, options.size, fam.kinds) > 0:
			Sfx.play("erase", -10.0, 0.2)
		return
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
	var kinds: Array = fam.kinds
	var spacing: float = fam.spacing
	if t.height_at_v(p) < Terrain.WATER_LEVEL + 0.05:
		_place_wet(fam, p, force)
		return
	if glade.is_blocked(p):
		return
	if not force:
		for other in glade.data.props:
			var op: Vector3 = other.p
			if kinds.has(other.kind) and Vector2(op.x, op.z).distance_to(p) < spacing:
				_thicken(other)
				return
	var kind: String = kinds[_rng.randi() % kinds.size()]
	var sr: Vector2 = fam.scale
	var pos := Vector3(p.x, t.height_at_v(p) - 0.03, p.y)
	glade.add_prop(kind, pos, _rng.randf() * TAU, _rng.randf_range(sr.x, sr.y), options.family in ["rocks", "flowers"])
	Sfx.play("plant", -6.0, 0.25)
	Settings.vibrate(6)


## Painting over flowers again: they grow fuller, and the fullest become
## little flowering bushes.
func _thicken(other: Dictionary) -> void:
	if not options.family in BLOOMS or _rng.randf() > 0.25:
		return
	var s: float = other.get("s", 1.0)
	if s < 1.5:
		other.s = s * 1.15
	elif options.family != "grain" and not String(other.kind).begins_with("bush"):
		other.kind = "bush_berries" if _rng.randf() < 0.5 else "bush_b"
		other.s = _rng.randf_range(0.5, 0.7)
	else:
		return
	glade.props.rebuild(glade.data.props)
	Sfx.play("plant", -10.0, 0.3)


## On water, flowers become lilies; trees stand in the pond with lily pads
## floating round them.
func _place_wet(fam: Dictionary, p: Vector2, force: bool) -> void:
	var t := glade.terrain
	var water_y := Terrain.WATER_LEVEL + 0.01
	if options.family in BLOOMS:
		if not force:
			for other in glade.data.props:
				var op: Vector3 = other.p
				if String(other.kind).begins_with("lily") and Vector2(op.x, op.z).distance_to(p) < 0.7:
					return
		glade.add_prop("lily_pad_a" if _rng.randf() < 0.6 else "lily_pad_b", Vector3(p.x, water_y, p.y), _rng.randf() * TAU, _rng.randf_range(0.8, 1.3))
		Sfx.play("splash", -14.0, 0.3)
		return
	if options.family in ["forest", "broadleaf", "golden", "blossom", "grand"]:
		if t.height_at_v(p) < Terrain.WATER_LEVEL - 1.2:
			return
		if not force:
			for other in glade.data.props:
				var op2: Vector3 = other.p
				if (fam.kinds as Array).has(other.kind) and Vector2(op2.x, op2.z).distance_to(p) < fam.spacing:
					return
		var kind: String = fam.kinds[_rng.randi() % fam.kinds.size()]
		glade.add_prop(kind, Vector3(p.x, t.height_at_v(p) - 0.03, p.y), _rng.randf() * TAU, _rng.randf_range(fam.scale.x, fam.scale.y))
		for k in 3:
			var a := _rng.randf() * TAU
			var q := p + Vector2(cos(a), sin(a)) * _rng.randf_range(0.9, 1.8)
			if t.height_at_v(q) < Terrain.WATER_LEVEL - 0.05:
				glade.add_prop("lily_pad_a" if k % 2 == 0 else "lily_pad_b", Vector3(q.x, water_y, q.y), _rng.randf() * TAU, _rng.randf_range(0.8, 1.2))
		Sfx.play("plant", -6.0, 0.25)


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
