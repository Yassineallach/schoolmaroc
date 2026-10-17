class_name PaintTool
extends BaseTool
## Tiny Glade's palette tool and style picker in one:
##  * Copy style: tap a house, wall, fence, path or stairs to pick up its
##    look (colours, style, roof shape, pattern, material, trims)
##  * Paste style: tap other pieces to give them that look (whatever of it
##    suits them)
##  * Wall / roof / stone / wood / trim / window-light colour: tap a piece to
##    paint it (wood tones the doors, sills and beams; trims are the
##    shutters and window frames)

const STYLE_KEYS := ["wall_col", "roof_col", "style", "roof", "pitch", "curve", "pattern", "col", "mat", "bands",
		"merlons", "peel", "glass", "smoke", "links", "level", "rail", "wood_tone", "trim_col"]
const GLASS_COLORS := [Color(1.0, 0.86, 0.6), Color(1.0, 0.97, 0.9), Color(0.6, 0.8, 1.0), Color(0.6, 1.0, 0.7),
		Color(1.0, 0.6, 0.75), Color(0.78, 0.62, 1.0)]

var clipboard: Dictionary = {}


func _init() -> void:
	tool_id = "paint"
	title = "Paint"
	options = {"mode": "pick", "color": 0}


func option_defs() -> Array:
	var defs: Array = [{"type": "choice", "key": "mode", "items": [
		{"id": "pick", "label": "Copy style", "icon": "pipette"},
		{"id": "apply", "label": "Paste style", "icon": "brush"},
		{"id": "wall_col", "label": "Walls", "icon": "plaster"},
		{"id": "roof_col", "label": "Roofs", "icon": "roof"},
		{"id": "col", "label": "Stone", "icon": "wall"},
		{"id": "wood_tone", "label": "Wood", "icon": "boards"},
		{"id": "trim_col", "label": "Trims", "icon": "win_plain"},
		{"id": "glass", "label": "Window light", "icon": "window"}]}]
	var palette := _palette()
	if not palette.is_empty():
		defs.append({"type": "colors", "key": "color", "colors": palette})
	return defs


func _palette() -> Array:
	match options.mode:
		"wall_col":
			return Catalog.WALL_COLORS
		"roof_col":
			return Catalog.ROOF_COLORS
		"col":
			return Catalog.STONE_COLORS
		"wood_tone":
			return Catalog.WOOD_TONES
		"trim_col":
			return Catalog.TRIM_COLORS
		"glass":
			return GLASS_COLORS
	return []


func set_option(key: String, value: Variant) -> void:
	super.set_option(key, value)
	if key == "mode" and game:
		options.color = 0
		game.hud.set_tool(tool_id, self)


func hint() -> String:
	match options.mode:
		"pick":
			return "Tap a house, wall, fence, path or stairs to copy its style."
		"apply":
			return "Tap pieces to give them the copied style." if not clipboard.is_empty() else "Copy a style first, then tap pieces to paste it."
	return "Pick a colour, then tap pieces to paint them."


func tap(screen: Vector2) -> void:
	var hit := pick(screen)
	var id: int = hit.get("id", -1) if not hit.is_empty() else -1
	var f := glade.find(id) if id >= 0 else {}
	if f.is_empty() or f.type == "props":
		Sfx.play("nope", -8.0)
		return
	var item: Dictionary = f.item
	match options.mode:
		"pick":
			clipboard = {}
			for k in STYLE_KEYS:
				if item.has(k):
					clipboard[k] = item[k]
			clipboard._type = f.type
			clipboard._shape = item.get("shape", "")
			game.hud.toast("Style copied")
			Sfx.play("click", -4.0)
			return
		"apply":
			if clipboard.is_empty():
				game.hud.toast("Copy a style first")
				return
			glade.begin_change()
			for k in clipboard:
				if String(k).begins_with("_"):
					continue
				# style names and roof shapes only carry over between like pieces
				if k in ["style", "roof", "pattern"] and (clipboard._type != f.type or clipboard._shape != item.get("shape", "")):
					continue
				if _suits(f.type, String(k), item):
					item[k] = clipboard[k] if not (clipboard[k] is Array or clipboard[k] is Dictionary) else clipboard[k].duplicate(true)
		_:
			var key: String = options.mode
			if not _suits(f.type, key, item):
				Sfx.play("nope", -8.0)
				return
			glade.begin_change()
			var pal := _palette()
			item[key] = pal[clampi(int(options.color), 0, pal.size() - 1)]
	glade.refresh(id, false)
	Sfx.play("brush", -4.0)
	Settings.vibrate(8)


## Whether a style key means something for a piece of this type.
static func _suits(type: String, key: String, item: Dictionary) -> bool:
	match type:
		"buildings":
			if key == "roof":
				return true
			return key in ["wall_col", "roof_col", "style", "pitch", "curve", "bands", "merlons", "peel", "glass", "smoke", "links",
					"wood_tone", "trim_col"]
		"walls":
			return key in ["col", "style", "pattern", "merlons", "level"]
		"fences":
			return key == "style"
		"paths":
			return key == "style"
		"stairs":
			return key in ["mat", "rail"]
	return false
