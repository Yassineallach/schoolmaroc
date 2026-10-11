class_name EraserTool
extends BaseTool
## Rub things out: snips walls, fences and paths, removes props and buildings.

var erasing := false
var _brush: MeshInstance3D


func _init() -> void:
	tool_id = "eraser"
	title = "Eraser"
	options = {"size": 1.2}


func option_defs() -> Array:
	return [{"type": "slider", "key": "size", "label": "Size", "min": 0.4, "max": 4.0, "step": 0.1}]


func hint() -> String:
	return "Drag over anything to remove it. Walls are cut where you rub."


func press(screen: Vector2) -> bool:
	glade.begin_change()
	erasing = true
	_erase(screen)
	return true


func drag(screen: Vector2) -> void:
	if erasing:
		_erase(screen)


func release(_screen: Vector2) -> void:
	erasing = false
	if _brush:
		_brush.visible = false


func cancel() -> void:
	release(Vector2.ZERO)


func tap(screen: Vector2) -> void:
	var hit := pick(screen)
	if hit.is_empty():
		return
	if hit.kind == "building":
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
	var r: float = options.size
	var n := 0
	if hit.kind == "building":
		glade.remove(hit.id)
		n += 1
	n += glade.remove_props_near(c, r)
	n += glade.erase_lines_near(c, r)
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
