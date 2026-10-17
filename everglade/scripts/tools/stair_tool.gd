class_name StairTool
extends StrokeTool
## Draw stairs (Tiny Glade's stair tool): start on the ground, a wall top or
## a flat roof and draw to where they should arrive; they climb from the
## height under your first touch to the height under your last. Drawn round
## a tower they spiral up it. Gentle rises make steps, steep ones a ladder,
## level ones a landing. Pull the end handles afterwards to raise or lower
## either end.

var _y0 := 0.0


func _init() -> void:
	tool_id = "stairs"
	title = "Stairs"
	options = {"mat": "stone", "w": 1.2, "straight": false, "rise": 0.0}
	min_length = 0.5


func option_defs() -> Array:
	return [
		{"type": "choice", "key": "mat", "items": [
			{"id": "stone", "label": "Stone", "icon": "stairs"},
			{"id": "wood", "label": "Timber", "icon": "stairs_wood"}]},
		{"type": "slider", "key": "w", "label": "Width", "min": 0.6, "max": 3.0, "step": 0.1},
		{"type": "slider", "key": "rise", "label": "Extra rise", "min": 0.0, "max": 8.0, "step": 0.1},
		{"type": "toggle", "key": "straight", "label": "Straight", "icon": "ruler"},
	]


func hint() -> String:
	return "Draw from where the stairs start to where they arrive (a wall top, a flat roof...). Round a tower they spiral. Steep makes a ladder."


func press(screen: Vector2) -> bool:
	var hit := pick(screen)
	if hit.is_empty():
		return false
	var hp: Vector3 = hit.point
	var p := glade.terrain.clamp_to_play(Vector2(hp.x, hp.z))
	points = PackedVector2Array([p])
	_y0 = glade.surface_at(p)
	drawing = true
	_preview_timer = 0.0
	return true


func drag(screen: Vector2) -> void:
	if not drawing:
		return
	var hit := pick(screen)
	if hit.is_empty():
		return
	var hp: Vector3 = hit.point
	var p := glade.terrain.clamp_to_play(Vector2(hp.x, hp.z))
	if options.get("straight", false):
		if points.size() == 1:
			points.append(p)
		else:
			points[1] = p
	elif points[points.size() - 1].distance_to(p) > 0.3:
		points.append(p)
		var now := Time.get_ticks_msec() / 1000.0
		if now - _last_sound > 0.12:
			_last_sound = now
			stroke_sound()


func _end_height(pts: PackedVector2Array) -> float:
	return glade.surface_at(pts[pts.size() - 1]) + float(options.rise)


func update_preview(pts: PackedVector2Array) -> void:
	if preview == null:
		preview = StairView.new()
		glade.add_child(preview)
	var d := {"id": 0, "pts": pts, "y0": _y0, "y1": _end_height(pts), "w": options.w, "mat": options.mat, "rail": true}
	(preview as StairView).build(d, glade.terrain, true)


func commit(pts: PackedVector2Array) -> void:
	glade.begin_change()
	glade.add_stairs(pts, _y0, _end_height(pts), options.w, options.mat)
	Sfx.play("place_stone")
	Settings.vibrate(12)


func stroke_sound() -> void:
	Sfx.play("brush", -11.0, 0.2)
