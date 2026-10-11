class_name StrokeTool
extends BaseTool
## Freehand drawing shared by walls, fences and paths: samples the finger on
## the ground, live-previews the result and commits a smoothed polyline.

var points := PackedVector2Array()
var drawing := false
var preview: Node3D
var _preview_timer := 0.0
var _last_sound := 0.0
var min_length := 1.0


func option_defs() -> Array:
	return [{"type": "toggle", "key": "straight", "label": "Straight", "icon": "ruler"}]


func press(screen: Vector2) -> bool:
	var g = ground(screen)
	if g == null:
		return false
	points = PackedVector2Array([Vector2(g.x, g.z)])
	drawing = true
	_preview_timer = 0.0
	return true


func drag(screen: Vector2) -> void:
	if not drawing:
		return
	var g = ground(screen)
	if g == null:
		return
	var p := Vector2(g.x, g.z)
	if options.get("straight", false):
		if points.size() == 1:
			points.append(p)
		else:
			points[1] = p
	elif points[points.size() - 1].distance_to(p) > 0.35:
		points.append(p)
		var now := Time.get_ticks_msec() / 1000.0
		if now - _last_sound > 0.12:
			_last_sound = now
			stroke_sound()


func _process(delta: float) -> void:
	if not drawing:
		return
	_preview_timer -= delta
	if _preview_timer <= 0.0 and points.size() >= 2:
		_preview_timer = 0.08
		update_preview(final_points())


func release(_screen: Vector2) -> void:
	if not drawing:
		return
	drawing = false
	var pts := final_points()
	clear_preview()
	if pts.size() >= 2 and Geo.length(pts) >= min_length:
		commit(pts)


func cancel() -> void:
	drawing = false
	points = PackedVector2Array()
	clear_preview()


func final_points() -> PackedVector2Array:
	if points.size() < 2:
		return points
	if options.get("straight", false):
		return Geo.resample(PackedVector2Array([points[0], points[points.size() - 1]]), 1.0)
	var simple := Geo.simplify(points, 0.18)
	return Geo.smooth(simple, 2)


func clear_preview() -> void:
	if preview:
		preview.queue_free()
		preview = null


# overridables
func update_preview(_pts: PackedVector2Array) -> void:
	pass


func commit(_pts: PackedVector2Array) -> void:
	pass


func stroke_sound() -> void:
	Sfx.play("brush", -10.0, 0.15)
