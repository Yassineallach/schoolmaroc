class_name PathTool
extends StrokeTool
## Paint winding paths. They open doors, arches and gates, become bridges or
## stepping stones over water and steps on steep hills.

var _ribbon: MeshInstance3D


func _init() -> void:
	tool_id = "path"
	title = "Paths"
	options = {"width": 1.4, "style": "dirt", "straight": false}
	min_length = 0.6


func option_defs() -> Array:
	return [
		{"type": "choice", "key": "style", "items": [
			{"id": "dirt", "label": "Dirt", "icon": "path"},
			{"id": "cobble", "label": "Cobbles", "icon": "cobble"},
			{"id": "paved", "label": "Paved", "icon": "paved"},
			{"id": "stones", "label": "Stepping", "icon": "stones"}]},
		{"type": "slider", "key": "width", "label": "Width", "min": 0.8, "max": 3.2, "step": 0.1},
		{"type": "toggle", "key": "straight", "label": "Straight", "icon": "ruler"},
	]


func hint() -> String:
	return "Drag to lay a path. Lead it into houses for doors, across ponds for bridges."


func update_preview(pts: PackedVector2Array) -> void:
	if preview == null:
		preview = MeshInstance3D.new()
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.72, 0.6, 0.44, 0.85)
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		(preview as MeshInstance3D).material_override = mat
		glade.add_child(preview)
	var mb := MeshBuilder.new()
	var w: float = options.width * 0.5
	var dense := Geo.resample(pts, 0.3)
	for i in dense.size() - 1:
		var a := dense[i]
		var b := dense[i + 1]
		var t := (b - a).normalized()
		var n := Vector2(-t.y, t.x) * w
		var ya := maxf(glade.terrain.height_at_v(a), Terrain.WATER_LEVEL) + 0.06
		var yb := maxf(glade.terrain.height_at_v(b), Terrain.WATER_LEVEL) + 0.06
		mb.quad(Vector3(a.x + n.x, ya, a.y + n.y), Vector3(b.x + n.x, yb, b.y + n.y), Vector3(b.x - n.x, yb, b.y - n.y), Vector3(a.x - n.x, ya, a.y - n.y), Color.WHITE)
	(preview as MeshInstance3D).mesh = mb.commit()


func commit(pts: PackedVector2Array) -> void:
	glade.begin_change()
	glade.add_path(pts, options.width, options.style)
	Sfx.play("place_path")
	Settings.vibrate(10)


func stroke_sound() -> void:
	Sfx.play("brush", -11.0, 0.2)
