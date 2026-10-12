class_name DecorTool
extends BaseTool
## Place lanterns, wells, carts, benches, banners and other cosy details.
## Tap to drop; drag after pressing to turn it to face a direction.

var placing: Dictionary = {}
var anchor := Vector2.ZERO


func _init() -> void:
	tool_id = "decor"
	title = "Decorations"
	options = {"kind": "lantern"}


func option_defs() -> Array:
	var items: Array = []
	for key in Catalog.DECOR:
		items.append({"id": key, "label": Catalog.DECOR[key].label, "icon": key})
	return [{"type": "choice", "key": "kind", "items": items}]


func hint() -> String:
	return "Tap to place. Press and drag to turn it as you place it."


func press(screen: Vector2) -> bool:
	var g = ground(screen)
	if g == null:
		return false
	var floats: bool = Catalog.DECOR[options.kind].get("float", false)
	if floats:
		# rafts and boats sit on the water (or wherever the shore is)
		g.y = maxf(g.y, Terrain.WATER_LEVEL - 0.04)
	elif glade.is_blocked(Vector2(g.x, g.z)):
		return false
	glade.begin_change()
	anchor = Vector2(g.x, g.z)
	var kind: String = options.kind
	placing = glade.add_prop(kind, g, game.rig.yaw, 1.0, Catalog.DECOR[kind].align)
	Sfx.play("place_wood", -3.0)
	Settings.vibrate(10)
	return true


func drag(screen: Vector2) -> void:
	if placing.is_empty():
		return
	var g = ground(screen)
	if g == null:
		return
	var d := Vector2(g.x, g.z) - anchor
	if d.length() > 0.4:
		placing.r = atan2(d.x, d.y)
		glade.props.rebuild(glade.data.props)


func release(_screen: Vector2) -> void:
	placing = {}


func cancel() -> void:
	placing = {}


func tap(_screen: Vector2) -> void:
	pass # press already placed it
