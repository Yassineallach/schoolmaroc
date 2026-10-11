class_name WaterTool
extends TerrainTool
## Dig ponds (water fills anything below the waterline) or fill them back in.


func _init() -> void:
	tool_id = "water"
	title = "Ponds"
	options = {"mode": "dig", "size": 2.5, "strength": 1.0}


func option_defs() -> Array:
	return [
		{"type": "choice", "key": "mode", "items": [
			{"id": "dig", "label": "Dig pond", "icon": "water"},
			{"id": "fill", "label": "Fill in", "icon": "fill"}]},
		{"type": "slider", "key": "size", "label": "Brush", "min": 1.0, "max": 6.0, "step": 0.1},
	]


func hint() -> String:
	return "Hold to dig a pond; ducks will find it. Paths across become bridges."


func mode() -> String:
	return "dig" if options.mode == "dig" else "flatten"


func press(screen: Vector2) -> bool:
	var ok := super.press(screen)
	if ok and options.mode == "fill":
		flatten_to = 0.05
	if ok and options.mode == "dig":
		Sfx.play("splash", -6.0)
	return ok
