class_name EraserTool
extends BaseTool
## Rub things out, with Tiny Glade's family of erasers:
##  * everything: snips walls, fences and paths, removes props and houses
##  * walls only: wears walls down into ruins (big brush)
##  * paths, trees, plants (flowers, bushes, grass, lilies): only that
##  * water: fills ponds back in to meadow
##  * hammer: tap any single thing (a house, a wall, stairs, one plant...)
##    to knock exactly that away

var erasing := false
var _brush: MeshInstance3D
var _at := Vector2.ZERO
var _water_used := false


func _init() -> void:
	tool_id = "eraser"
	title = "Eraser"
	options = {"size": 1.2, "mode": "all"}


func option_defs() -> Array:
	return [
		{"type": "choice", "key": "mode", "items": [
			{"id": "all", "label": "Everything", "icon": "eraser"},
			{"id": "walls", "label": "Walls only", "icon": "wall_rubble"},
			{"id": "paths", "label": "Paths", "icon": "path"},
			{"id": "trees", "label": "Trees", "icon": "forest"},
			{"id": "plants", "label": "Plants", "icon": "flowers"},
			{"id": "water", "label": "Water", "icon": "fill"},
			{"id": "hammer", "label": "Hammer", "icon": "hammer"}]},
		{"type": "slider", "key": "size", "label": "Size", "min": 0.4, "max": 6.0, "step": 0.1},
	]


func hint() -> String:
	match options.mode:
		"walls":
			return "Rub walls to wear them down into ruins; houses and plants are left alone."
		"water":
			return "Hold over a pond to fill it back in."
		"hammer":
			return "Tap any one thing to knock it away."
	return "Drag over things to remove them. Walls are cut where you rub."


func press(screen: Vector2) -> bool:
	if options.mode == "hammer":
		return false
	glade.begin_change()
	erasing = true
	_water_used = false
	_erase(screen)
	return true


func drag(screen: Vector2) -> void:
	if erasing:
		_erase(screen)


func release(_screen: Vector2) -> void:
	erasing = false
	if _water_used:
		_water_used = false
		glade.terrain_edited()
	if _brush:
		_brush.visible = false


func cancel() -> void:
	release(Vector2.ZERO)


func process_hold(delta: float) -> void:
	if erasing and options.mode == "water":
		glade.terrain.sculpt(_at, options.size, delta, "flatten", 0.05)
		_water_used = true


func tap(screen: Vector2) -> void:
	var hit := pick(screen)
	if hit.is_empty():
		return
	if options.mode == "hammer":
		var id: int = hit.get("id", -1)
		if id < 0 or hit.kind == "terrain":
			Sfx.play("nope", -8.0)
			return
		glade.begin_change()
		glade.remove(id)
		Sfx.play("erase")
		Settings.vibrate(14)
		return
	if hit.kind == "building" and options.mode == "all":
		glade.begin_change()
		glade.remove(hit.id)
		Sfx.play("erase")
		return


func _erase(screen: Vector2) -> void:
	var hit := pick(screen)
	if hit.is_empty():
		return
	var p: Vector3 = hit.point
	var c := Vector2(p.x, p.z)
	_at = c
	var r: float = options.size
	var n := 0
	match options.mode:
		"all":
			if hit.kind == "building":
				glade.remove(hit.id)
				n += 1
			n += glade.remove_props_near(c, r)
			n += glade.erase_lines_near(c, r)
		"walls":
			n += glade.erase_lines_near(c, r, ["walls"])
		"paths":
			n += glade.erase_lines_near(c, r, ["paths"])
		"trees":
			n += glade.remove_props_near(c, r, _kinds(func(k): return k.begins_with("tree_")))
		"plants":
			n += glade.remove_props_near(c, r, _kinds(_is_plant))
	if n > 0:
		Sfx.play("erase", -4.0, 0.2)
		Settings.vibrate(8)
	if _brush == null:
		_brush = MeshInstance3D.new()
		var torus := TorusMesh.new()
		torus.inner_radius = 0.92
		torus.outer_radius = 1.0
		_brush.mesh = torus
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.albedo_color = Color(1.0, 0.6, 0.55, 0.7)
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.no_depth_test = true
		_brush.material_override = mat
		glade.add_child(_brush)
	_brush.visible = true
	_brush.global_position = Vector3(c.x, glade.terrain.height_at_v(c) + 0.1, c.y)
	_brush.scale = Vector3(r, 1, r)


static func _is_plant(k: String) -> bool:
	return k.begins_with("flowers") or k.begins_with("bush") or k.begins_with("lily") \
			or k in ["fern", "plant_leafy", "wheat", "grass_tuft", "mushrooms", "reeds"]


## Prop kinds in the glade matching `test`.
func _kinds(test: Callable) -> Array:
	var out: Array = []
	for pr in glade.data.props:
		if not out.has(pr.kind) and test.call(String(pr.kind)):
			out.append(pr.kind)
	return out if not out.is_empty() else ["-"]
