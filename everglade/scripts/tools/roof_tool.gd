class_name RoofTool
extends BaseTool
## Restyle roofs: tap a building to apply the chosen shape, pitch and colour,
## or tap inside a ring of your own walls to roof it over (Tiny Glade style).


func _init() -> void:
	tool_id = "roof"
	title = "Roofs"
	options = {"roof": "gable", "color": 0, "pitch": 1.2}


func option_defs() -> Array:
	return [
		{"type": "choice", "key": "roof", "items": [
			{"id": "gable", "label": "Gable", "icon": "gable"},
			{"id": "hip", "label": "Hipped", "icon": "hip"},
			{"id": "flat", "label": "Battlement", "icon": "flat"},
			{"id": "cone", "label": "Spire", "icon": "cone"}]},
		{"type": "slider", "key": "pitch", "label": "Steepness", "min": 0.5, "max": 1.8, "step": 0.05},
		{"type": "colors", "key": "color", "colors": Catalog.ROOF_COLORS},
	]


func hint() -> String:
	return "Tap a building to give it this roof, or tap inside a ring of walls to roof it over."


func tap(screen: Vector2) -> void:
	var hit := pick(screen, 8)
	if hit.is_empty() or hit.kind != "building":
		var g = ground(screen)
		if g != null:
			glade.begin_change()
			var made := glade.add_roof_over_walls(Vector2(g.x, g.z), options.roof, options.pitch, Catalog.ROOF_COLORS[options.color])
			if not made.is_empty():
				Sfx.play("place_wood")
				Settings.vibrate(14)
				return
			glade.undo_stack.pop_back()
		Sfx.play("nope", -8.0)
		return
	var b: Dictionary = glade.find(hit.id).item
	glade.begin_change()
	var roof: String = options.roof
	if b.shape == "round":
		b.roof = "flat" if roof == "flat" else "cone"
	else:
		b.roof = "gable" if roof == "cone" else roof
	b.roof_col = Catalog.ROOF_COLORS[options.color]
	b.pitch = options.pitch
	glade.refresh(b.id)
	Sfx.play("place_wood")
	Settings.vibrate(12)
