class_name Glade
extends Node3D
## The diorama model: owns the data dictionary, every structure view, the
## terrain, undo/redo and the rules that make pieces react to each other
## (paths open arches in walls, gates in fences and doors in houses).

signal changed
signal structure_built(kind: String, pos: Vector3)

const MAX_UNDO := 40
const IVY_SECONDS := 900.0 # time for ivy to fully cover a wall

var data: Dictionary = {}
var terrain: Terrain
var grass: GrassField
var water: Water
var props: PropBatch
var views: Dictionary = {}
var undo_stack: Array = []
var redo_stack: Array = []
var selection_ring: MeshInstance3D

var _roots: Dictionary = {}
var _interactions_dirty := false
var _ivy_clock := 0.0
var _openings: Dictionary = {}


func _ready() -> void:
	terrain = Terrain.new()
	terrain.name = "Terrain"
	add_child(terrain)
	water = Water.new()
	water.name = "Water"
	add_child(water)
	water.setup(terrain)
	grass = GrassField.new()
	grass.name = "Grass"
	add_child(grass)
	grass.setup(terrain)
	for r in ["walls", "fences", "paths", "buildings"]:
		var n := Node3D.new()
		n.name = r.capitalize()
		add_child(n)
		_roots[r] = n
	props = PropBatch.new()
	props.name = "Props"
	add_child(props)
	selection_ring = MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = 0.92
	torus.outer_radius = 1.0
	torus.rings = 48
	torus.ring_segments = 6
	selection_ring.mesh = torus
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = Color(1.0, 0.95, 0.7, 0.85)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.no_depth_test = true
	selection_ring.material_override = mat
	selection_ring.visible = false
	add_child(selection_ring)


# ---------------------------------------------------------------------------
# Data lifecycle
# ---------------------------------------------------------------------------
static func empty_data(name_text := "My Glade") -> Dictionary:
	return {
		"version": 1, "name": name_text, "season": 1, "time": 0.38, "next_id": 1,
		"walls": [], "fences": [], "paths": [], "buildings": [], "props": [],
		"template": "meadow", "seed": randi() % 100000,
	}


func new_glade(template: String, name_text := "My Glade") -> void:
	data = empty_data(name_text)
	data.template = template
	terrain.generate(template, data.seed)
	terrain.flush()
	data.terrain = terrain.get_heights()
	undo_stack.clear()
	redo_stack.clear()
	rebuild_all()


func load_data(d: Dictionary) -> void:
	data = d
	for key in ["walls", "fences", "paths", "buildings", "props"]:
		if not data.has(key):
			data[key] = []
	if data.has("terrain"):
		terrain.set_heights(data.terrain)
	else:
		terrain.generate(data.get("template", "meadow"), data.get("seed", 1))
	terrain.flush()
	undo_stack.clear()
	redo_stack.clear()
	rebuild_all()


func to_data() -> Dictionary:
	var d := data.duplicate(true)
	d.terrain = terrain.get_heights()
	return d


func next_id() -> int:
	var id: int = data.get("next_id", 1)
	data.next_id = id + 1
	return id


# ---------------------------------------------------------------------------
# Undo / redo
# ---------------------------------------------------------------------------
func begin_change() -> void:
	undo_stack.append(to_data())
	if undo_stack.size() > MAX_UNDO:
		undo_stack.pop_front()
	redo_stack.clear()


func can_undo() -> bool:
	return not undo_stack.is_empty()


func can_redo() -> bool:
	return not redo_stack.is_empty()


func undo() -> void:
	if undo_stack.is_empty():
		return
	redo_stack.append(to_data())
	_restore(undo_stack.pop_back())


func redo() -> void:
	if redo_stack.is_empty():
		return
	undo_stack.append(to_data())
	_restore(redo_stack.pop_back())


func _restore(d: Dictionary) -> void:
	var keep_time: float = data.get("time", 0.38)
	var keep_season: int = data.get("season", 1)
	data = d
	data.time = keep_time
	data.season = keep_season
	terrain.set_heights(d.terrain)
	terrain.flush()
	rebuild_all()
	changed.emit()


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------
func find(id: int) -> Dictionary:
	for key in ["walls", "fences", "paths", "buildings", "props"]:
		for item in data[key]:
			if item.id == id:
				return {"type": key, "item": item}
	return {}


func list_of(type: String) -> Array:
	return data.get(type, [])


# ---------------------------------------------------------------------------
# Adding pieces
# ---------------------------------------------------------------------------
func add_wall(pts: PackedVector2Array, h: float, col: Color) -> Dictionary:
	var w := {"id": next_id(), "pts": pts, "h": h, "col": col, "ivy": 0.0}
	data.walls.append(w)
	_make_view("walls", w, true)
	_after_edit(Geo.v3(pts[pts.size() / 2], terrain.height_at_v(pts[pts.size() / 2])), "wall")
	return w


func add_fence(pts: PackedVector2Array) -> Dictionary:
	var f := {"id": next_id(), "pts": pts}
	data.fences.append(f)
	_make_view("fences", f, true)
	_after_edit(Geo.v3(pts[0], terrain.height_at_v(pts[0])), "fence")
	return f


func add_path(pts: PackedVector2Array, width: float, style: String) -> Dictionary:
	var p := {"id": next_id(), "pts": pts, "w": width, "style": style}
	data.paths.append(p)
	_make_view("paths", p, false)
	_after_edit(Geo.v3(pts[0], terrain.height_at_v(pts[0])), "path")
	return p


func add_building(b: Dictionary) -> Dictionary:
	b.id = next_id()
	if not b.has("seed"):
		b.seed = randi() % 100000
	if not b.has("windows"):
		b.windows = BuildingView.default_windows(b)
	settle_building(b)
	data.buildings.append(b)
	_make_view("buildings", b, true)
	_after_edit(Vector3(b.c.x, b.base, b.c.y), "building")
	return b


## Levels the terrain under a building and stores its base height.
func settle_building(b: Dictionary) -> void:
	var poly := BuildingView.footprint(b)
	var target := terrain.average_height(poly)
	target = maxf(target, Terrain.WATER_LEVEL + 0.15)
	b.base = target
	terrain.flatten_polygon(poly, target, 1.4)
	terrain.flush()


func add_prop(kind: String, pos: Vector3, rot: float, scale_value: float, align := false, pop := true) -> Dictionary:
	var p := {"id": next_id(), "kind": kind, "p": pos, "r": rot, "s": scale_value}
	if align:
		p.n = terrain.normal_at(pos.x, pos.z).lerp(Vector3.UP, 0.4).normalized()
	data.props.append(p)
	if pop:
		props.pop_in(p)
	else:
		props.rebuild(data.props)
	changed.emit()
	return p


func remove(id: int) -> void:
	var f := find(id)
	if f.is_empty():
		return
	data[f.type].erase(f.item)
	if views.has(id):
		views[id].queue_free()
		views.erase(id)
	if f.type == "props":
		props.rebuild(data.props)
	else:
		mark_interactions()
	changed.emit()


func remove_props_near(center: Vector2, radius: float) -> int:
	var removed := 0
	for p in data.props.duplicate():
		var pp: Vector3 = p.p
		if Vector2(pp.x, pp.z).distance_to(center) < radius + ModelLib.radius(p.kind) * 0.5:
			data.props.erase(p)
			removed += 1
	if removed > 0:
		props.rebuild(data.props)
		changed.emit()
	return removed


## Erases parts of walls/fences/paths inside the circle (splitting them).
func erase_lines_near(center: Vector2, radius: float) -> int:
	var count := 0
	for type in ["walls", "fences", "paths"]:
		for item in data[type].duplicate():
			var pts: PackedVector2Array = item.pts
			if Geo.closest(pts, center).x > radius:
				continue
			var pieces := Geo.erase_circle(pts, center, radius)
			data[type].erase(item)
			if views.has(item.id):
				views[item.id].queue_free()
				views.erase(item.id)
			for piece in pieces:
				var copy: Dictionary = item.duplicate(true)
				copy.id = next_id()
				copy.pts = piece
				data[type].append(copy)
				_make_view(type, copy, false)
			count += 1
	if count > 0:
		mark_interactions()
		changed.emit()
	return count


func buildings_near(center: Vector2, radius: float) -> Array:
	var out: Array = []
	for b in data.buildings:
		var poly := BuildingView.footprint(b)
		if Geometry2D.is_point_in_polygon(center, poly):
			out.append(b)
			continue
		for i in poly.size():
			if Geo.dist_to_segment(center, poly[i], poly[(i + 1) % poly.size()]) < radius:
				out.append(b)
				break
	return out


## Rebuilds one structure after its data changed (e.g. from the inspector).
func refresh(id: int, animate := false) -> void:
	var f := find(id)
	if f.is_empty():
		return
	if f.type == "props":
		props.rebuild(data.props)
	else:
		if f.type == "buildings":
			settle_building(f.item)
		_make_view(f.type, f.item, animate)
		mark_interactions()
	changed.emit()


func _after_edit(pos: Vector3, kind: String) -> void:
	mark_interactions()
	structure_built.emit(kind, pos)
	changed.emit()


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------
func _make_view(type: String, item: Dictionary, animate: bool) -> Node3D:
	if views.has(item.id):
		views[item.id].free()
		views.erase(item.id)
	var v: Node3D
	match type:
		"walls":
			v = WallView.new()
			_roots.walls.add_child(v)
			v.build(item, terrain, _openings.get(item.id, []))
		"fences":
			v = FenceView.new()
			_roots.fences.add_child(v)
			v.build(item, terrain, _openings.get(item.id, []))
		"paths":
			v = PathView.new()
			_roots.paths.add_child(v)
			v.build(item, terrain)
		"buildings":
			v = BuildingView.new()
			_roots.buildings.add_child(v)
			v.build(item, _openings.get(item.id, []))
	views[item.id] = v
	if animate and v.has_method("play_build_anim"):
		v.play_build_anim()
	return v


func rebuild_all() -> void:
	for id in views:
		views[id].free()
	views.clear()
	_openings.clear()
	_compute_interactions()
	for type in ["walls", "fences", "paths", "buildings"]:
		for item in data[type]:
			_make_view(type, item, false)
	props.rebuild(data.props)
	_paint_mask()


func mark_interactions() -> void:
	_interactions_dirty = true


## Re-snaps everything that sits on the ground after a sculpt stroke.
func terrain_edited() -> void:
	for p in data.props:
		var pos: Vector3 = p.p
		pos.y = terrain.height_at(pos.x, pos.z)
		p.p = pos
	props.rebuild(data.props)
	for type in ["walls", "fences", "paths"]:
		for item in data[type]:
			_make_view(type, item, false)
	mark_interactions()
	changed.emit()


func _process(delta: float) -> void:
	if _interactions_dirty:
		_interactions_dirty = false
		var old := _openings.duplicate(true)
		_compute_interactions()
		for type in ["walls", "fences", "buildings"]:
			for item in data[type]:
				var before = old.get(item.id, [])
				var after = _openings.get(item.id, [])
				if str(before) != str(after) or not views.has(item.id):
					_make_view(type, item, false)
		for item in data.paths:
			if not views.has(item.id):
				_make_view("paths", item, false)
		_paint_mask()
	_ivy_clock += delta
	if _ivy_clock > 2.0:
		var step := _ivy_clock / IVY_SECONDS
		_ivy_clock = 0.0
		for type in ["walls", "buildings"]:
			for item in data[type]:
				var g: float = minf(1.0, item.get("ivy", 0.0) + step)
				item.ivy = g
				if views.has(item.id):
					views[item.id].set_ivy(g)


func _compute_interactions() -> void:
	_openings.clear()
	for path in data.paths:
		var ppts: PackedVector2Array = path.pts
		var pw: float = path.get("w", 1.4)
		for wall in data.walls:
			for hit in Geo.intersections(ppts, wall.pts):
				var w := pw / maxf(0.5, hit.sin) + 0.5
				_add_opening(wall.id, {"s": snappedf(hit.sb, 0.01), "w": snappedf(clampf(w, 1.2, 4.5), 0.01)})
		for fence in data.fences:
			for hit in Geo.intersections(ppts, fence.pts):
				_add_opening(fence.id, {"s": snappedf(hit.sb, 0.01), "w": snappedf(clampf(pw, 1.0, 2.4), 0.01)})
		for b in data.buildings:
			var door := _door_for(b, ppts)
			if not door.is_empty():
				_add_opening(b.id, door)
	# merge overlapping openings on walls
	for id in _openings:
		var list: Array = _openings[id]
		list.sort_custom(func(a, c): return a.s < c.s)
		var merged: Array = []
		for o in list:
			if not merged.is_empty() and o.has("w") and merged[-1].has("w") and o.s - merged[-1].s < (o.w + merged[-1].w) * 0.5:
				var last: Dictionary = merged[-1]
				var a: float = last.s - last.w * 0.5
				var c: float = maxf(last.s + last.w * 0.5, o.s + o.w * 0.5)
				last.s = (a + c) * 0.5
				last.w = c - a
			else:
				merged.append(o)
		_openings[id] = merged


func _add_opening(id: int, o: Dictionary) -> void:
	if not _openings.has(id):
		_openings[id] = []
	_openings[id].append(o)


func _door_for(b: Dictionary, pts: PackedVector2Array) -> Dictionary:
	var poly := BuildingView.footprint(b)
	var closed := poly.duplicate()
	closed.append(poly[0])
	var hits := Geo.intersections(pts, closed)
	var point := Vector2.INF
	if not hits.is_empty():
		point = hits[0].point
	else:
		# path ends right against the wall?
		for end in [pts[0], pts[pts.size() - 1]]:
			var d := INF
			for i in poly.size():
				d = minf(d, Geo.dist_to_segment(end, poly[i], poly[(i + 1) % poly.size()]))
			if d < 0.9:
				point = end
				break
	if point == Vector2.INF:
		return {}
	var tmp := BuildingView.new()
	tmp.data = b
	tmp.transform = Transform3D(BuildingView.local_basis(b.get("rot", 0.0)), Vector3(b.c.x, b.base, b.c.y))
	tmp.eave = Catalog.PLINTH + b.floors * Catalog.FLOOR_H
	var loc := tmp.locate(Vector3(point.x, b.base + 0.5, point.y))
	tmp.free()
	return {"side": loc.side, "u": snappedf(loc.u, 0.001), "s": 0.0}


func _paint_mask() -> void:
	terrain.clear_mask()
	for b in data.buildings:
		terrain.paint_polygon(BuildingView.footprint(b), 1.1, 2, 0.9)
	for w in data.walls:
		terrain.paint_polyline(w.pts, 1.4, 2, 0.75)
	for f in data.fences:
		terrain.paint_polyline(f.pts, 0.5, 2, 0.4)
	for p in data.paths:
		match p.get("style", "dirt"):
			"cobble":
				terrain.paint_polyline(p.pts, p.w, 1, 1.0)
				terrain.paint_polyline(p.pts, p.w + 0.5, 0, 0.55)
			"stones":
				terrain.paint_polyline(p.pts, p.w * 0.7, 0, 0.45)
			_:
				terrain.paint_polyline(p.pts, p.w, 0, 1.0)
	terrain.commit_mask()
	grass.refresh_all()


# ---------------------------------------------------------------------------
# Picking & selection
# ---------------------------------------------------------------------------
## Raycasts the scene. Returns {kind, id, point, normal} (kind may be "terrain").
func pick(camera: Camera3D, screen: Vector2, mask := 0xF) -> Dictionary:
	var from := camera.project_ray_origin(screen)
	var dir := camera.project_ray_normal(screen)
	var q := PhysicsRayQueryParameters3D.create(from, from + dir * 400.0, mask)
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	var out := {}
	if hit.is_empty():
		# fall back to the ground plane
		if absf(dir.y) > 0.001:
			var t := -from.y / dir.y
			if t > 0.0:
				var gp := from + dir * t
				return {"kind": "terrain", "id": -1, "point": gp, "normal": Vector3.UP}
		return {}
	var col: Object = hit.collider
	out = {"kind": col.get_meta("kind", "terrain"), "id": col.get_meta("id", -1), "point": hit.position, "normal": hit.normal}
	if out.kind == "terrain":
		var best := -1
		var bd := INF
		var hp: Vector3 = hit.position
		for p in data.props:
			var pp: Vector3 = p.p
			var d := Vector2(pp.x - hp.x, pp.z - hp.z).length()
			var r: float = ModelLib.radius(p.kind) * p.get("s", 1.0) + 0.25
			if d < r and d < bd:
				bd = d
				best = p.id
		if best >= 0:
			out.kind = "prop"
			out.id = best
	return out


func ground_hit(camera: Camera3D, screen: Vector2) -> Variant:
	var h := pick(camera, screen, 1)
	if h.is_empty():
		return null
	return h.point


func show_selection(id: int) -> void:
	var f := find(id)
	if f.is_empty():
		selection_ring.visible = false
		return
	var item: Dictionary = f.item
	var center := Vector3.ZERO
	var radius := 1.0
	match f.type:
		"buildings":
			center = Vector3(item.c.x, item.base + 0.1, item.c.y)
			radius = item.r + 0.6 if item.shape == "round" else item.size.length() * 0.5 + 0.4
		"props":
			center = item.p + Vector3.UP * 0.05
			radius = ModelLib.radius(item.kind) * item.get("s", 1.0) + 0.4
		_:
			var pts: PackedVector2Array = item.pts
			var bb := Rect2(pts[0], Vector2.ZERO)
			for p in pts:
				bb = bb.expand(p)
			var c2 := bb.get_center()
			center = Vector3(c2.x, terrain.height_at_v(c2) + 0.1, c2.y)
			radius = bb.size.length() * 0.5 + 0.6
	selection_ring.visible = true
	selection_ring.global_position = center
	selection_ring.scale = Vector3(radius, 1.0, radius)


func hide_selection() -> void:
	selection_ring.visible = false


## Tops of walls, fences and roofs where birds like to sit.
func perches() -> Array[Vector3]:
	var out: Array[Vector3] = []
	for id in views:
		var v = views[id]
		if "perches" in v:
			for p in v.perches:
				out.append(p)
	return out


## Lowest height a camera may sit at above (x, z) without entering a building.
func ceiling_at(p: Vector2) -> float:
	var h := -INF
	for b in data.get("buildings", []):
		var poly := BuildingView.footprint(b)
		var inside := Geometry2D.is_point_in_polygon(p, poly)
		if not inside:
			var d := INF
			for i in poly.size():
				d = minf(d, Geo.dist_to_segment(p, poly[i], poly[(i + 1) % poly.size()]))
			if d > 1.2:
				continue
		var top: float = b.base + Catalog.PLINTH + b.floors * Catalog.FLOOR_H
		var v = views.get(b.id)
		if v:
			top += v.roof_h
		h = maxf(h, top + 1.0)
	return h


func water_cells() -> int:
	var n := 0
	for z in range(0, Terrain.VERTS, 2):
		for x in range(0, Terrain.VERTS, 2):
			if terrain.heights[z * Terrain.VERTS + x] < Terrain.WATER_LEVEL - 0.1:
				n += 1
	return n


func random_water_point(rng: RandomNumberGenerator) -> Variant:
	for i in 60:
		var p := Vector2(rng.randf_range(-Terrain.PLAY_HALF, Terrain.PLAY_HALF), rng.randf_range(-Terrain.PLAY_HALF, Terrain.PLAY_HALF))
		if terrain.height_at_v(p) < Terrain.WATER_LEVEL - 0.25:
			return p
	return null


func is_blocked(p: Vector2) -> bool:
	if terrain.height_at_v(p) < Terrain.WATER_LEVEL + 0.05:
		return true
	if not terrain.in_play_area(p, 0.5):
		return true
	for b in data.buildings:
		if Geometry2D.is_point_in_polygon(p, BuildingView.footprint(b)):
			return true
	return false


## True when walking from a to b would cross a wall, fence or building.
func crosses_obstacle(a: Vector2, b: Vector2) -> bool:
	var seg := PackedVector2Array([a, b])
	for type in ["walls", "fences"]:
		for item in data[type]:
			for hit in Geo.intersections(seg, item.pts):
				# gaps/arches/gates let animals through
				var ok := false
				for o in _openings.get(item.id, []):
					if absf(o.s - hit.sb) < o.w * 0.5:
						ok = true
				if not ok:
					return true
	for bld in data.buildings:
		var poly := BuildingView.footprint(bld)
		var closed := poly.duplicate()
		closed.append(poly[0])
		if not Geo.intersections(seg, closed).is_empty():
			return true
	return false
