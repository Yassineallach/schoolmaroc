class_name WallTool
extends StrokeTool
## Draw stone walls freely; tall walls grow battlements, paths make arches.


func _init() -> void:
	tool_id = "wall"
	title = "Walls"
	options = {"height": 2.4, "straight": false, "color": 0}


func option_defs() -> Array:
	return [
		{"type": "slider", "key": "height", "label": "Height", "min": 0.8, "max": 7.0, "step": 0.1},
		{"type": "colors", "key": "color", "colors": Catalog.STONE_COLORS},
		{"type": "toggle", "key": "straight", "label": "Straight", "icon": "ruler"},
	]


func hint() -> String:
	return "Drag to draw a wall. Paths drawn through walls carve archways."


func update_preview(pts: PackedVector2Array) -> void:
	if preview == null:
		preview = WallView.new()
		glade.add_child(preview)
	var d := {"id": 0, "pts": pts, "h": options.height, "col": Catalog.STONE_COLORS[options.color]}
	(preview as WallView).build(d, glade.terrain, [], true)


func commit(pts: PackedVector2Array) -> void:
	glade.begin_change()
	glade.add_wall(pts, options.height, Catalog.STONE_COLORS[options.color])
	Sfx.play("place_stone")
	Settings.vibrate(18)


func stroke_sound() -> void:
	Sfx.play("stone_tick", -12.0, 0.2)
