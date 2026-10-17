class_name HandTool
extends BaseTool
## Look around, pet animals, select pieces and edit them in place, the Tiny
## Glade way: a selected piece shows grab handles.
##  - walls, fences and paths: dots along the base reshape the line (nearby
##    points follow softly); walls also get a height handle on top.
##  - houses: pull the wall-top handle for floors, the roof handle for the
##    roof's pitch, the side handles to stretch the house (the far side stays
##    put), the ring handle to turn it and the low corner handle to raise it
##    onto pillars. Towers get a radius handle.
##  - roofs: the roof handle drags up/down for pitch and sideways to round
##    the roof out or flare it; roofs laid on walls get an eave handle.
##  - props: a ring handle turns them.
## With a mouse, hovering a piece already shows its handles.
## Dragging the selected piece anywhere else moves it.

const HANDLE_PX := 38.0         # touch radius of a handle on screen
const REBUILD_EVERY := 0.12     # live rebuild rate while dragging a handle
const LINE_HANDLES := 9

var moving: Dictionary = {}
var last := Vector2.ZERO
var _moved := false

var _handles: Array = []        # [{kind, pos: Vector3, ...}]
var _handle_nodes: Array[MeshInstance3D] = []
var _handle_root: Node3D
var _for_id := -2
var _drag: Dictionary = {}      # active handle drag
var _pending := false
var _since := 0.0
## id of a wall/fence/path waiting to be cut where the player taps next
var cut_id := -1
## desktop: the piece under the mouse shows its handles before it is selected
var _hover_id := -1
var _hover_t := 0.0


func _init() -> void:
	tool_id = "hand"
	title = "Explore"


func hint() -> String:
	return "Tap things to edit them: pull their handles to reshape, drag them to move. Tap animals to pet them."


func deactivate() -> void:
	cancel()
	cut_id = -1
	_hover_id = -1
	_clear_handles()
	_for_id = -2


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------
func press(screen: Vector2) -> bool:
	var sel: int = game.selected_id
	if sel < 0 and _hover_id >= 0:
		# grabbing a handle of the hovered piece selects it on the way
		_sync_handles()
		if not _handle_at(screen).is_empty():
			game.select(_hover_id)
			sel = _hover_id
			_for_id = -2
	if sel < 0:
		return false
	_sync_handles()
	var h := _handle_at(screen)
	if not h.is_empty():
		var f := glade.find(sel)
		if f.is_empty():
			return false
		glade.begin_change()
		if h.kind == "pt":
			# bend a finely sampled copy so the reshape stays smooth
			var dense := Geo.resample(f.item.pts, 0.5)
			if dense.size() > (f.item.pts as PackedVector2Array).size():
				var hp := Vector2(h.pos.x, h.pos.z)
				var bi := 0
				for k in dense.size():
					if dense[k].distance_to(hp) < dense[bi].distance_to(hp):
						bi = k
				f.item.pts = dense
				h = h.duplicate()
				h.i = bi
		_drag = {"h": h, "f": f, "start": screen, "item0": f.item.duplicate(true)}
		_moved = false
		Sfx.play("click", -8.0)
		return true
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
	if not _drag.is_empty():
		_drag_handle(screen)
		return
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
	_place_handles(moving.type, item)


func release(_screen: Vector2) -> void:
	if not _drag.is_empty():
		var f: Dictionary = _drag.f
		_drag = {}
		if not _moved:
			glade.undo_stack.pop_back()
			return
		_pending = false
		glade.refresh(f.item.id, false)
		game.select(f.item.id)   # refresh the inspector's values
		_for_id = -2
		Sfx.play("place_stone", -6.0)
		Settings.vibrate(10)
		return
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
	_for_id = -2
	Sfx.play("place_stone", -6.0)


func cancel() -> void:
	if not _drag.is_empty() or not moving.is_empty():
		release(Vector2.ZERO)


func tap(screen: Vector2) -> void:
	if cut_id >= 0:
		var target := cut_id
		cut_id = -1
		var g = ground(screen)
		if g != null:
			glade.begin_change()
			var other := glade.split_line(target, Vector2(g.x, g.z))
			if other >= 0:
				Sfx.play("erase", -2.0)
				Settings.vibrate(14)
				game.select(target)
				_for_id = -2
				return
			glade.undo_stack.pop_back()
		Sfx.play("nope", -8.0)
		return
	var hit := pick(screen)
	if hit.is_empty() or hit.kind == "terrain":
		game.select(-1)
		return
	game.select(hit.id)
	Sfx.play("click", -4.0)


func _process(delta: float) -> void:
	if game == null or game.tool != self:
		if _handle_root and _handle_root.visible:
			_handle_root.visible = false
		return
	_update_hover(delta)
	_sync_handles()
	if _pending:
		_since += delta
		if _since >= REBUILD_EVERY:
			_since = 0.0
			_pending = false
			if not _drag.is_empty():
				glade.refresh(_drag.f.item.id, false)
				glade.show_selection(_drag.f.item.id)
	# keep handles a constant size on screen
	if _handle_root and _handle_root.visible:
		var cam := camera()
		for n in _handle_nodes:
			if n.visible:
				n.scale = Vector3.ONE * cam.global_position.distance_to(n.global_position) * 0.022


# ---------------------------------------------------------------------------
# Handles
# ---------------------------------------------------------------------------
## Desktop only: show the handles of whatever is under the mouse.
func _update_hover(delta: float) -> void:
	if DisplayServer.is_touchscreen_available() or game.selected_id >= 0 or not _drag.is_empty() or not moving.is_empty():
		_hover_id = -1
		return
	_hover_t -= delta
	if _hover_t > 0.0:
		return
	_hover_t = 0.12
	var hit := pick(get_viewport().get_mouse_position())
	var id: int = -1 if hit.is_empty() or hit.kind == "terrain" else int(hit.get("id", -1))
	# keep showing while the mouse travels to one of the handles
	if id < 0 and _hover_id >= 0 and not _handle_at(get_viewport().get_mouse_position(), 70.0).is_empty():
		return
	_hover_id = id


func _sync_handles() -> void:
	var sel: int = game.selected_id if game.selected_id >= 0 else _hover_id
	if sel == _for_id and _handle_root and _handle_root.visible == (sel >= 0):
		return
	_for_id = sel
	var f := glade.find(sel) if sel >= 0 else {}
	if f.is_empty():
		_clear_handles()
		return
	_place_handles(f.type, f.item)


func _clear_handles() -> void:
	_handles.clear()
	if _handle_root:
		_handle_root.visible = false


func _place_handles(type: String, item: Dictionary) -> void:
	_handles.clear()
	var t := glade.terrain
	match type:
		"walls", "fences", "paths":
			var pts: PackedVector2Array = item.pts
			var knots: int = clampi(int(item.get("knots", LINE_HANDLES)), 2, 25)
			var step := maxi(1, int(ceil(float(pts.size() - 1) / (knots - 1))))
			var idx := range(0, pts.size(), step)
			if idx[idx.size() - 1] != pts.size() - 1:
				idx.append(pts.size() - 1)
			for i in idx:
				_handles.append({"kind": "pt", "i": i, "pos": Geo.v3(pts[i], t.height_at_v(pts[i]) + 0.25)})
			if type == "walls":
				var mid := Geo.point_at(pts, Geo.length(pts) * 0.5)
				_handles.append({"kind": "wall_h", "pos": Geo.v3(mid, t.height_at_v(mid) + float(item.get("h", 2.4)) + 0.45)})
		"buildings":
			var v: BuildingView = glade.views.get(item.id)
			var eave: float = v.eave if v else Catalog.FLOOR_H * item.floors
			var roof_h: float = v.roof_h if v else 2.0
			var ground_y: float = item.get("base", t.height_at_v(item.c))
			var base: float = ground_y + float(item.get("lift", 0.0))
			var c3 := Vector3(item.c.x, base, item.c.y)
			if not item.get("roof_only", false):
				# lift the house onto pillars
				var lpos: Vector2 = item.c + Vector2(-0.7071, -0.7071) * (float(item.get("r", 1.0)) + 0.35)
				if item.shape != "round":
					var lrot: float = item.get("rot", 0.0)
					var lx := Vector2(cos(lrot), sin(lrot))
					var lz := Vector2(-sin(lrot), cos(lrot))
					lpos = item.c - lx * (item.size.x * 0.5 + 0.3) + lz * (item.size.y * 0.5 + 0.3)
				_handles.append({"kind": "lift", "pos": Vector3(lpos.x, base + 0.15, lpos.y)})
			if item.shape == "round":
				var r: float = item.r
				_handles.append({"kind": "eave" if item.get("roof_only", false) else "floors", "pos": c3 + Vector3(r + 0.1, eave, 0)})
				_handles.append({"kind": "radius", "pos": c3 + Vector3(0, 0.3, r + 0.2)})
				if roof_h > 0.3:
					_handles.append({"kind": "pitch", "pos": c3 + Vector3.UP * (eave + roof_h + 0.3)})
			else:
				var rot: float = item.get("rot", 0.0)
				var ax := Vector2(cos(rot), sin(rot))
				var az := Vector2(-sin(rot), cos(rot))
				var s: Vector2 = item.size
				var front: Vector2 = item.c - az * (s.y * 0.5 + 0.1)
				_handles.append({"kind": "eave" if item.get("roof_only", false) else "floors", "pos": Geo.v3(front, base + eave)})
				if roof_h > 0.3:
					_handles.append({"kind": "pitch", "pos": c3 + Vector3.UP * (eave + roof_h + 0.3)})
				_handles.append({"kind": "size_x", "pos": Geo.v3(item.c + ax * (s.x * 0.5 + 0.2), base + 0.4)})
				_handles.append({"kind": "size_z", "pos": Geo.v3(item.c + az * (s.y * 0.5 + 0.2), base + 0.4)})
				var corner: Vector2 = item.c + ax * (s.x * 0.5 + 0.9) - az * (s.y * 0.5 + 0.9)
				_handles.append({"kind": "rotate", "pos": Geo.v3(corner, t.height_at_v(corner) + 0.3)})
		"props":
			var rad: float = ModelLib.radius(item.kind) * float(item.get("s", 1.0)) + 0.5
			var pr: float = item.get("r", 0.0)
			var at: Vector3 = item.p + Vector3(cos(pr), 0, sin(pr)) * rad
			at.y = t.height_at(at.x, at.z) + 0.3
			_handles.append({"kind": "rotate", "pos": at})
	_show_handles()


func _show_handles() -> void:
	if _handle_root == null:
		_handle_root = Node3D.new()
		_handle_root.name = "EditHandles"
		glade.add_child(_handle_root)
	_handle_root.visible = true
	while _handle_nodes.size() < _handles.size():
		var mi := MeshInstance3D.new()
		var sphere := SphereMesh.new()
		sphere.radius = 0.5
		sphere.height = 1.0
		sphere.radial_segments = 16
		sphere.rings = 8
		mi.mesh = sphere
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_handle_root.add_child(mi)
		_handle_nodes.append(mi)
	for i in _handle_nodes.size():
		var n := _handle_nodes[i]
		n.visible = i < _handles.size()
		if not n.visible:
			continue
		var h: Dictionary = _handles[i]
		n.global_position = h.pos
		n.material_override = _handle_material(h.kind)


static var _mats: Dictionary = {}


static func _handle_material(kind: String) -> Material:
	var col := Color(1.0, 0.98, 0.92)          # reshape points
	match kind:
		"wall_h", "floors", "pitch", "eave", "lift":
			col = Color(1.0, 0.78, 0.3)        # heights
		"size_x", "size_z", "radius":
			col = Color(0.55, 0.85, 0.55)      # stretch
		"rotate":
			col = Color(0.5, 0.75, 1.0)        # turn
	if not _mats.has(col):
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.albedo_color = col
		m.no_depth_test = true
		m.render_priority = 10
		_mats[col] = m
	return _mats[col]


func _handle_at(screen: Vector2, radius := HANDLE_PX) -> Dictionary:
	var cam := camera()
	var best: Dictionary = {}
	var best_d := radius
	for h in _handles:
		if cam.is_position_behind(h.pos):
			continue
		var d := cam.unproject_position(h.pos).distance_to(screen)
		if d < best_d:
			best_d = d
			best = h
	return best


func _drag_handle(screen: Vector2) -> void:
	var h: Dictionary = _drag.h
	var f: Dictionary = _drag.f
	var item: Dictionary = f.item
	var item0: Dictionary = _drag.item0
	var dy: float = (_drag.start as Vector2).y - screen.y   # up = positive
	if screen.distance_to(_drag.start) > 6.0:
		_moved = true
	match h.kind:
		"pt":
			var g = ground(screen)
			if g == null:
				return
			item.pts = _soft_move(item0.pts, h.i, Vector2(g.x, g.z) - (item0.pts as PackedVector2Array)[h.i],
					clampi(int(item.get("knots", LINE_HANDLES)), 2, 25))
		"wall_h":
			item.h = snappedf(clampf(float(item0.get("h", 2.4)) + dy * 0.012, 0.8, 7.0), 0.1)
		"floors":
			var nf := clampi(int(item0.floors) + int(round(dy / 55.0)), 1, 6)
			if nf != item.floors:
				var old: int = item.floors
				item.floors = nf
				if nf > old:
					# fresh windows on the new storeys
					for w in BuildingView.default_windows(item):
						if w.f >= old and w.get("kind", "window") == "window":
							item.windows.append(w)
		"pitch":
			# up/down: steeper or flatter; left/right: rounder or more flared
			var dx: float = screen.x - (_drag.start as Vector2).x
			item.pitch = clampf(float(item0.get("pitch", 1.2)) + dy * 0.006, 0.5, 1.8)
			item.curve = clampf(float(item0.get("curve", 0.0)) + dx * 0.006, -1.0, 1.0)
			if absf(item.curve) < 0.06:
				item.curve = 0.0
		"eave":
			item.eave = clampf(float(item0.get("eave", 2.4)) + dy * 0.012, 0.8, 9.0)
		"lift":
			item.lift = snappedf(clampf(float(item0.get("lift", 0.0)) + dy * 0.012, 0.0, 6.0), 0.1)
			if item.lift < 0.2:
				item.lift = 0.0
		"size_x", "size_z":
			var g2 = ground(screen)
			if g2 == null:
				return
			var rot: float = item0.get("rot", 0.0)
			var axis := Vector2(cos(rot), sin(rot)) if h.kind == "size_x" else Vector2(-sin(rot), cos(rot))
			var s0: Vector2 = item0.size
			var half: float = s0.x * 0.5 if h.kind == "size_x" else s0.y * 0.5
			var far: Vector2 = (item0.c as Vector2) - axis * half       # opposite side stays put
			var reach := (Vector2(g2.x, g2.z) - far).dot(axis) - 0.2
			var s := s0
			if h.kind == "size_x":
				s.x = clampf(snappedf(reach, 0.1), 3.0, 16.0)
				item.c = far + axis * s.x * 0.5
			else:
				s.y = clampf(snappedf(reach, 0.1), 2.8, 8.0)
				item.c = far + axis * s.y * 0.5
			item.size = s
		"radius":
			var g3 = ground(screen)
			if g3 == null:
				return
			item.r = clampf(Vector2(g3.x, g3.z).distance_to(item0.c) - 0.2, 1.2, 5.0)
		"rotate":
			var g4 = ground(screen)
			if g4 == null:
				return
			var centre: Vector2 = item0.c if f.type == "buildings" else Vector2((item0.p as Vector3).x, (item0.p as Vector3).z)
			var a0 := (Vector2(h.pos.x, h.pos.z) - centre).angle()
			var a1 := (Vector2(g4.x, g4.z) - centre).angle()
			var da := wrapf(a1 - a0, -PI, PI)
			if f.type == "buildings":
				item.rot = float(item0.get("rot", 0.0)) + da
			else:
				item.r = float(item0.get("r", 0.0)) + da
	if f.type == "props":
		glade.props.rebuild(glade.data.props)
	else:
		_pending = true
	_place_handles(f.type, item)
	# keep the grabbed handle under the finger for point drags
	for i in _handles.size():
		if _handles[i].kind == h.kind and _handles[i].get("i", -1) == h.get("i", -1):
			_drag.h = _handles[i] if h.kind != "rotate" else h
	glade.show_selection(item.id)


## Moves point i by `d`, dragging neighbours along with a smooth falloff so
## the line bends instead of kinking.
static func _soft_move(src: PackedVector2Array, i: int, d: Vector2, knots := LINE_HANDLES) -> PackedVector2Array:
	var pts := src.duplicate()
	var n := pts.size()
	var reach := maxf(2.0, float(n - 1) / (knots - 1))
	for j in n:
		var k := absf(j - i) / reach
		if k >= 1.0:
			continue
		var w := 0.5 + 0.5 * cos(PI * k)
		pts[j] += d * w
	return pts
