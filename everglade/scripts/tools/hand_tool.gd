class_name HandTool
extends BaseTool
## Look around, pet animals, select pieces to edit them in the inspector and
## drag a selected piece to move it.

var moving: Dictionary = {}
var last := Vector2.ZERO
var _moved := false


func _init() -> void:
	tool_id = "hand"
	title = "Explore"


func hint() -> String:
	return "Tap things to edit them, tap animals to pet them. Drag to look around."


func press(screen: Vector2) -> bool:
	var sel: int = game.selected_id
	if sel < 0:
		return false
	var hit := pick(screen)
	if hit.is_empty() or hit.get("id", -1) != sel:
		return false
	var g = ground(screen)
	if g == null:
		return false
	glade.begin_change()
	moving = glade.find(sel)
	last = Vector2(g.x, g.z)
	_moved = false
	return true


func drag(screen: Vector2) -> void:
	if moving.is_empty():
		return
	var g = ground(screen)
	if g == null:
		return
	var p := Vector2(g.x, g.z)
	var delta := p - last
	last = p
	_moved = true
	var item: Dictionary = moving.item
	match moving.type:
		"props":
			var pp: Vector3 = item.p
			pp.x += delta.x
			pp.z += delta.y
			pp.y = glade.terrain.height_at(pp.x, pp.z) - 0.03
			item.p = pp
			glade.props.rebuild(glade.data.props)
		"buildings":
			item.c += delta
			var v: BuildingView = glade.views.get(item.id)
			if v:
				v.position += Vector3(delta.x, 0, delta.y)
		_:
			var pts: PackedVector2Array = item.pts
			for i in pts.size():
				pts[i] += delta
			item.pts = pts
			var v2 = glade.views.get(item.id)
			if v2:
				v2.position += Vector3(delta.x, 0, delta.y)
	glade.show_selection(item.id)


func release(_screen: Vector2) -> void:
	if moving.is_empty():
		return
	var item: Dictionary = moving.item
	var type: String = moving.type
	moving = {}
	if not _moved:
		glade.undo_stack.pop_back() # nothing changed: drop the snapshot taken on press
		return
	if type != "props":
		var v = glade.views.get(item.id)
		if v and type != "buildings":
			v.position = Vector3.ZERO
		glade.refresh(item.id, false)
	glade.show_selection(item.id)
	Sfx.play("place_stone", -6.0)


func cancel() -> void:
	if not moving.is_empty():
		release(Vector2.ZERO)


func tap(screen: Vector2) -> void:
	var hit := pick(screen)
	if hit.is_empty() or hit.kind == "terrain":
		game.select(-1)
		return
	game.select(hit.id)
	Sfx.play("click", -4.0)
