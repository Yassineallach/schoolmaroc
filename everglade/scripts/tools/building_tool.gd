class_name BuildingTool
extends BaseTool
## Drag out cottages (rectangles) or towers (circles). The terrain levels
## itself under the footprint and the building rises from the ground.

var start := Vector3.ZERO
var current := Vector3.ZERO
var dragging := false
var preview: BuildingView
var _preview_timer := 0.0


func _init() -> void:
	tool_id = "building"
	title = "Buildings"
	options = {"shape": "house", "floors": 2, "style": "windrise", "roof_color": 0, "wall_color": 0}


func option_defs() -> Array:
	return [
		{"type": "choice", "key": "shape", "items": [
			{"id": "house", "label": "Cottage", "icon": "house"},
			{"id": "tower", "label": "Tower", "icon": "tower"}]},
		{"type": "choice", "key": "style", "items": [
			{"id": "windrise", "label": "Windrise", "icon": "windrise"},
			{"id": "plaster", "label": "Plaster", "icon": "plaster"},
			{"id": "timber", "label": "Timber", "icon": "timber"},
			{"id": "stone", "label": "Stone", "icon": "stone"}]},
		{"type": "slider", "key": "floors", "label": "Floors", "min": 1, "max": 5, "step": 1},
		{"type": "colors", "key": "roof_color", "colors": Catalog.ROOF_COLORS},
	]


func hint() -> String:
	return "Drag to shape a cottage, or pick Tower and drag out its radius. Tap to drop one."


func press(screen: Vector2) -> bool:
	var g = ground(screen)
	if g == null:
		return false
	start = g
	current = g
	dragging = true
	_preview_timer = 0.0
	return true


func drag(screen: Vector2) -> void:
	var g = ground(screen)
	if g != null:
		current = g


func _process(delta: float) -> void:
	if not dragging:
		return
	_preview_timer -= delta
	if _preview_timer > 0.0:
		return
	_preview_timer = 0.07
	var d := make_data(start, current)
	if d.is_empty():
		return
	if preview == null:
		preview = BuildingView.new()
		glade.add_child(preview)
	d.base = glade.terrain.average_height(BuildingView.footprint(d))
	d.windows = BuildingView.default_windows(d)
	preview.build(d, [], true)


func make_data(a: Vector3, b: Vector3) -> Dictionary:
	var a2 := Vector2(a.x, a.z)
	var b2 := Vector2(b.x, b.z)
	var ab := b2 - a2
	var yaw: float = game.rig.yaw
	var d := {
		"floors": int(options.floors), "style": options.style,
		"roof_col": Catalog.ROOF_COLORS[options.roof_color],
		"wall_col": Catalog.WALL_COLORS[0] if options.style == "windrise" else Catalog.WALL_COLORS[(int(options.roof_color) + 1) % Catalog.WALL_COLORS.size()],
		"pitch": 1.2, "ivy": 0.0, "id": 0, "chimney": BuildingView.NO_CHIMNEY,
	}
	if options.shape == "tower":
		d.shape = "round"
		d.c = a2
		d.r = clampf(ab.length(), 1.3, 4.5) if ab.length() > 0.6 else 2.0
		d.roof = "cone"
		d.style = "stone" if options.style == "timber" else options.style
		d.floors = maxi(int(options.floors), 2)
		d.rot = 0.0
		return d
	d.shape = "rect"
	d.roof = "gable"
	if ab.length() < 1.2:
		d.c = a2
		d.size = Vector2(5.0, 3.8)
		d.rot = -yaw
	else:
		var length := clampf(ab.length(), 3.0, 16.0)
		d.size = Vector2(length, clampf(length * 0.62, 3.2, 6.5))
		d.rot = atan2(ab.y, ab.x)
		d.c = a2 + ab.normalized() * length * 0.5
	if int(options.floors) >= 1 and d.size.x > 4.5:
		d.chimney = 0.3
	return d


func release(_screen: Vector2) -> void:
	if not dragging:
		return
	dragging = false
	_clear_preview()
	var d := make_data(start, current)
	_place(d)


func tap(screen: Vector2) -> void:
	var g = ground(screen)
	if g == null:
		return
	_place(make_data(g, g))


func _place(d: Dictionary) -> void:
	if not glade.terrain.in_play_area(d.c, 1.0):
		return
	d.erase("id")
	glade.begin_change()
	var b := glade.add_building(d)
	Sfx.play("build")
	Settings.vibrate(25)
	game.rig.shake(0.5)


func cancel() -> void:
	dragging = false
	_clear_preview()


func _clear_preview() -> void:
	if preview:
		preview.queue_free()
		preview = null
