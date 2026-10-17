class_name DecorTool
extends BaseTool
## Place lanterns, wells, carts, benches, banners and other cosy details.
## Tap to drop; drag after pressing to turn it to face a direction.

var placing: Dictionary = {}
var anchor := Vector2.ZERO


func _init() -> void:
	tool_id = "decor"
	title = "Decorations"
	options = {"kind": "lantern", "cat": "lights"}


func option_defs() -> Array:
	var cats: Array = []
	for c in Catalog.DECOR_CATS:
		cats.append({"id": c[0], "label": c[1], "icon": _first_of(c[0])})
	var items: Array = []
	for key in Catalog.DECOR:
		if Catalog.DECOR[key].get("cat", "clutter") == options.cat:
			items.append({"id": key, "label": Catalog.DECOR[key].label, "icon": key})
	return [{"type": "choice", "key": "cat", "items": cats}, {"type": "choice", "key": "kind", "items": items}]


func _first_of(cat: String) -> String:
	for key in Catalog.DECOR:
		if Catalog.DECOR[key].get("cat", "clutter") == cat:
			return key
	return "decor"


func set_option(key: String, value: Variant) -> void:
	super.set_option(key, value)
	if key == "cat" and game:
		options.kind = _first_of(value)
		game.hud.set_tool(tool_id, self)


func hint() -> String:
	return "Pick a group, then tap to place (on the ground, a flat roof, a wall top or stairs). Press and drag to turn it as you place it."


func press(screen: Vector2) -> bool:
	var g = ground(screen)
	if g == null:
		return false
	var floats: bool = Catalog.DECOR[options.kind].get("float", false)
	var up_high := false
	var hit := pick(screen)
	if not hit.is_empty() and hit.kind in ["building", "wall", "stairs"]:
		# clutter can stand on flat roofs, wall tops and stairs too
		var hp: Vector3 = hit.point
		var top := glade.surface_at(Vector2(hp.x, hp.z))
		if top > glade.terrain.height_at(hp.x, hp.z) + 0.3 and absf(top - hp.y) < 0.6:
			g = Vector3(hp.x, top, hp.z)
			up_high = true
	if floats:
		# rafts and boats sit on the water (or wherever the shore is)
		g.y = maxf(g.y, Terrain.WATER_LEVEL - 0.04)
	elif not up_high and glade.is_blocked(Vector2(g.x, g.z)):
		return false
	glade.begin_change()
	anchor = Vector2(g.x, g.z)
	var kind: String = options.kind
	placing = glade.add_prop(kind, g, game.rig.yaw, 1.0, Catalog.DECOR[kind].align and not up_high)
	if up_high:
		placing.on = true   # stays put when the ground under it is reshaped
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
