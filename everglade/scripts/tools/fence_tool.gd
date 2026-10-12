class_name FenceTool
extends StrokeTool
## Draw rustic wooden fences; gates appear where paths cross.


func _init() -> void:
	tool_id = "fence"
	title = "Fences"
	options = {"style": "wood", "straight": false}
	min_length = 0.8


func option_defs() -> Array:
	return [
		{"type": "choice", "key": "style", "items": [
			{"id": "wood", "label": "Rustic", "icon": "fence"},
			{"id": "ornate", "label": "Ornate", "icon": "fence_ornate"}]},
		{"type": "toggle", "key": "straight", "label": "Straight", "icon": "ruler"},
	]


func hint() -> String:
	return "Drag to draw a fence. Cross it with a path to add a gate."


func update_preview(pts: PackedVector2Array) -> void:
	if preview == null:
		preview = FenceView.new()
		glade.add_child(preview)
	(preview as FenceView).build({"id": 0, "pts": pts, "style": options.style}, glade.terrain, [], true)


func commit(pts: PackedVector2Array) -> void:
	glade.begin_change()
	glade.add_fence(pts, options.style)
	Sfx.play("place_wood")
	Settings.vibrate(14)


func stroke_sound() -> void:
	Sfx.play("wood_tick", -12.0, 0.2)
