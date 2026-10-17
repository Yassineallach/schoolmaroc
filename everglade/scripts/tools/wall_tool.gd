class_name WallTool
extends StrokeTool
## Draw stone walls freely; tall walls grow battlements, paths make arches.


func _init() -> void:
	tool_id = "wall"
	title = "Walls"
	options = {"height": 2.4, "straight": false, "color": 0, "style": "rendered", "pattern": "glade"}


func option_defs() -> Array:
	return [
		{"type": "choice", "key": "style", "items": [
			{"id": "rendered", "label": "Rendered", "icon": "wall_rendered"},
			{"id": "stone", "label": "Bare stone", "icon": "wall"},
			{"id": "wood", "label": "Timber", "icon": "wood"}]},
		{"type": "choice", "key": "pattern", "items": [
			{"id": "glade", "label": "Hand-laid", "icon": "wall_glade"}, {"id": "kit", "label": "Rounded", "icon": "wall_kit"},
			{"id": "rubble", "label": "Fieldstone", "icon": "wall_rubble"}, {"id": "classic", "label": "Coursed", "icon": "wall"},
			{"id": "brick", "label": "Brick", "icon": "wall_brick"}, {"id": "ashlar", "label": "Ashlar", "icon": "wall_ashlar"}]},
		{"type": "slider", "key": "height", "label": "Height", "min": 0.8, "max": 7.0, "step": 0.1},
		{"type": "colors", "key": "color", "colors": Catalog.STONE_COLORS},
		{"type": "toggle", "key": "straight", "label": "Straight", "icon": "ruler"},
	]


func hint() -> String:
	return "Drag to draw a wall. Paths through walls carve archways; paths that end at a wall get a door."


func update_preview(pts: PackedVector2Array) -> void:
	if preview == null:
		preview = WallView.new()
		glade.add_child(preview)
	var d := {"id": 0, "pts": pts, "h": options.height, "col": Catalog.STONE_COLORS[options.color], "style": options.style, "pattern": options.pattern}
	(preview as WallView).build(d, glade.terrain, [], true)


func commit(pts: PackedVector2Array) -> void:
	glade.begin_change()
	glade.add_wall(pts, options.height, Catalog.STONE_COLORS[options.color], options.style, options.pattern)
	Sfx.play("place_stone")
	Settings.vibrate(18)


func stroke_sound() -> void:
	Sfx.play("stone_tick", -12.0, 0.2)
