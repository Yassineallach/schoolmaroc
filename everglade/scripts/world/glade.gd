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
var backdrop: Backdrop
var landscape: Landscape
var boundary: MeshInstance3D
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
var _links_dirty := false
var _links: Node3D


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
	backdrop = Backdrop.new()
	backdrop.name = "Backdrop"
	add_child(backdrop)
	landscape = Landscape.new()
	landscape.name = "Landscape"
	add_child(landscape)
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
		"walls": [], "fences": [], "paths": [], "buildings": [], "props": [], "patches": [], "stairs": [],
		"template": "meadow", "seed": randi() % 100000,
	}


func new_glade(template: String, name_text := "My Glade") -> void:
	data = empty_data(name_text)
	data.template = template
	terrain.generate(template, data.seed)
	terrain.patches = data.patches
	terrain.flush()
	backdrop.build(template, terrain)
	landscape.build(template, terrain)
	water.set_palette(template)
	data.terrain = terrain.get_heights()
	undo_stack.clear()
	redo_stack.clear()
	rebuild_all()


func load_data(d: Dictionary) -> void:
	data = d
	for key in ["walls", "fences", "paths", "buildings", "props", "patches", "stairs"]:
		if not data.has(key):
			data[key] = []
	if data.has("terrain"):
		terrain.patches = data.patches
		terrain.set_heights(data.terrain)
	else:
		terrain.generate(data.get("template", "meadow"), data.get("seed", 1))
		terrain.patches = data.patches
	terrain.flush()
	backdrop.build(data.get("template", "meadow"), terrain)
	landscape.build(data.get("template", "meadow"), terrain)
	water.set_palette(data.get("template", "meadow"))
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
	if not data.has("patches"):
		data.patches = []
	if not data.has("stairs"):
		data.stairs = []
	terrain.patches = data.patches
	terrain.set_heights(d.terrain)
	terrain.flush()
	rebuild_all()
	changed.emit()


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------
func find(id: int) -> Dictionary:
	for key in ["walls", "fences", "paths", "buildings", "props", "stairs"]:
		for item in data.get(key, []):
			if item.id == id:
				return {"type": key, "item": item}
	return {}


func list_of(type: String) -> Array:
	return data.get(type, [])


# ---------------------------------------------------------------------------
# Adding pieces
# ---------------------------------------------------------------------------
func add_wall(pts: PackedVector2Array, h: float, col: Color, style := "rendered", pattern := "classic") -> Dictionary:
	var w := {"id": next_id(), "pts": pts, "h": h, "col": col, "ivy": 0.0, "style": style, "pattern": pattern}
	data.walls.append(w)
	if batch:
		return w
	_make_view("walls", w, true)
	_after_edit(Geo.v3(pts[pts.size() / 2], terrain.height_at_v(pts[pts.size() / 2])), "wall")
	return w


func add_fence(pts: PackedVector2Array, style := "wood") -> Dictionary:
	var f := {"id": next_id(), "pts": pts, "style": style}
	data.fences.append(f)
	if batch:
		return f
	_make_view("fences", f, true)
	_after_edit(Geo.v3(pts[0], terrain.height_at_v(pts[0])), "fence")
	return f


func add_path(pts: PackedVector2Array, width: float, style: String) -> Dictionary:
	var p := {"id": next_id(), "pts": pts, "w": width, "style": style}
	data.paths.append(p)
	if batch:
		return p
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
	if batch:
		return b
	_make_view("buildings", b, true)
	for o in joined_with(b):
		if views.has(o.id):
			_make_view("buildings", o, false)
	_after_edit(Vector3(b.c.x, b.base, b.c.y), "building")
	return b


## Levels the terrain under a building and stores its base height.
func settle_building(b: Dictionary) -> void:
	if b.get("roof_only", false):
		return   # sits on the player's walls; its base was set when it was made
	_glue(b)
	var poly := BuildingView.footprint(b)
	var target := terrain.average_height(poly)
	target = maxf(target, Terrain.WATER_LEVEL + 0.15)
	# a house joined onto another shares its ground floor level
	var host := _join_host(b)
	if not host.is_empty() and host.has("base"):
		target = host.base
	b.base = target
	if batch:
		terrain.flatten_polygon(poly, target, 1.4)
		return
	sync_pads()
	terrain.flush()


# ---------------------------------------------------------------------------
# Wall rings (for roofs over the player's own walls)
# ---------------------------------------------------------------------------
const RING_SNAP := 1.3


## The ring of walls enclosing p: one wall drawn back to its start, or a
## chain of walls whose ends meet. Returns {poly, walls, h} or {}.
func wall_ring_at(p: Vector2) -> Dictionary:
	for w0 in data.walls:
		var pts: PackedVector2Array = (w0.pts as PackedVector2Array).duplicate()
		if pts.size() < 2:
			continue
		var used: Array = [w0]
		var guard := 0
		while pts[0].distance_to(pts[pts.size() - 1]) > RING_SNAP and guard < 8:
			guard += 1
			var tail: Vector2 = pts[pts.size() - 1]
			var best: Dictionary = {}
			var best_d := RING_SNAP
			var flip := false
			for w in data.walls:
				if used.has(w):
					continue
				var wp: PackedVector2Array = w.pts
				var d0 := wp[0].distance_to(tail)
				var d1 := wp[wp.size() - 1].distance_to(tail)
				if d0 < best_d:
					best_d = d0
					best = w
					flip = false
				if d1 < best_d:
					best_d = d1
					best = w
					flip = true
			if best.is_empty():
				break
			used.append(best)
			var add: PackedVector2Array = (best.pts as PackedVector2Array).duplicate()
			if flip:
				add.reverse()
			pts.append_array(add)
		if pts.size() < 3 or pts[0].distance_to(pts[pts.size() - 1]) > RING_SNAP:
			continue
		if Geometry2D.is_point_in_polygon(p, pts):
			var h := INF
			for w in used:
				h = minf(h, float(w.get("h", 2.4)))
			return {"poly": pts, "walls": used, "h": h}
	return {}


## A roof (gable, hip, flat or spire) fitted over the wall ring enclosing p.
func add_roof_over_walls(p: Vector2, roof: String, pitch: float, roof_col: Color) -> Dictionary:
	var ring := wall_ring_at(p)
	if ring.is_empty():
		return {}
	var poly: PackedVector2Array = ring.poly
	var hull := Geometry2D.convex_hull(poly)
	# smallest rectangle around the ring (rotating calipers over hull edges)
	var best := {"area": INF}
	for i in hull.size() - 1:
		var e := hull[i + 1] - hull[i]
		if e.length() < 0.05:
			continue
		var ang := e.angle()
		var ax := Vector2(cos(ang), sin(ang))
		var az := Vector2(-sin(ang), cos(ang))
		var lo := Vector2(INF, INF)
		var hi := -lo
		for q in hull:
			var l := Vector2(q.dot(ax), q.dot(az))
			lo = lo.min(l)
			hi = hi.max(l)
		var sz := hi - lo
		if sz.x * sz.y < best.area:
			var mid := (lo + hi) * 0.5
			best = {"area": sz.x * sz.y, "size": sz, "rot": ang, "c": ax * mid.x + az * mid.y}
	var area := absf(_poly_area(poly))
	var centroid := Vector2.ZERO
	for q in poly:
		centroid += q
	centroid /= poly.size()
	var size: Vector2 = best.size
	var rot: float = best.rot
	if size.y > size.x:
		size = Vector2(size.y, size.x)
		rot += PI * 0.5
	var fill: float = area / maxf(best.area, 0.01)
	var b := {"roof_only": true, "eave": float(ring.h) - 0.05, "floors": 1, "style": "stone", "windows": [],
			"pitch": pitch, "roof_col": roof_col, "ivy": 0.0, "id": 0, "chimney": BuildingView.NO_CHIMNEY,
			"wall_col": Catalog.WALL_COLORS[0]}
	b.base = terrain.average_height(poly)
	if roof == "cone" or (fill < 0.84 and size.y / size.x > 0.75):
		var r := 0.0
		for q in poly:
			r += q.distance_to(centroid)
		b.shape = "round"
		b.c = centroid
		b.r = r / poly.size() + 0.1
		b.rot = 0.0
		b.roof = "flat" if roof == "flat" else "cone"
	else:
		b.shape = "rect"
		b.c = best.c
		b.size = size + Vector2(0.3, 0.3)
		b.rot = rot
		b.roof = roof
	var made := add_building(b)
	# the walls under the roof drop their battlements so the eaves sit snugly
	for w in ring.walls:
		w.roofed = made.id
		if not batch:
			_make_view("walls", w, false)
	return made


static func _poly_area(poly: PackedVector2Array) -> float:
	var a := 0.0
	for i in poly.size():
		var j := (i + 1) % poly.size()
		a += poly[i].x * poly[j].y - poly[j].x * poly[i].y
	return a * 0.5


# ---------------------------------------------------------------------------
# Joined houses (Tiny Glade "glue")
# ---------------------------------------------------------------------------
## Other houses whose footprint overlaps b's (roofs on walls don't join).
func joined_with(b: Dictionary) -> Array:
	var out: Array = []
	if b.get("roof_only", false) or not b.has("c"):
		return out
	var poly := Geometry2D.offset_polygon(BuildingView.footprint(b), 0.2)
	if poly.is_empty():
		return out
	for o in data.buildings:
		if o == b or o.get("roof_only", false) or not o.has("c"):
			continue
		if not Geometry2D.intersect_polygons(poly[0], BuildingView.footprint(o)).is_empty():
			out.append(o)
	return out


## The biggest house b is joined onto, if any.
func _join_host(b: Dictionary) -> Dictionary:
	var best: Dictionary = {}
	var best_a := _footprint_area(b)
	for o in joined_with(b):
		var a := _footprint_area(o)
		if a > best_a:
			best_a = a
			best = o
	return best


static func _footprint_area(b: Dictionary) -> float:
	return PI * b.r * b.r if b.shape == "round" else b.size.x * b.size.y


## A house pushed against a bigger one squares up to it (within 12°).
func _glue(b: Dictionary) -> void:
	if b.shape != "rect":
		return
	var host := _join_host(b)
	if host.is_empty() or host.shape != "rect":
		return
	var hr: float = host.get("rot", 0.0)
	var r: float = b.get("rot", 0.0)
	var quarter := PI * 0.5
	var k := roundf((r - hr) / quarter)
	if absf((r - hr) - k * quarter) < deg_to_rad(12.0):
		b.rot = hr + k * quarter


## Footprints of the houses joined onto b, in b's local XZ (for its view).
func join_polys(b: Dictionary) -> Array:
	var out: Array = []
	if b.get("roof_only", false):
		return out
	var inv := Basis(Vector3.UP, float(b.get("rot", 0.0)))
	for o in joined_with(b):
		var local := PackedVector2Array()
		for q in BuildingView.footprint(o):
			var d: Vector2 = q - (b.c as Vector2)
			var l := inv * Vector3(d.x, 0, d.y)
			local.append(Vector2(l.x, l.z))
		var grown := Geometry2D.offset_polygon(local, 0.05)
		out.append(grown[0] if not grown.is_empty() else local)
	return out


## Rebuilds the flat pads under every building (they sit on top of the
## terrain patches) and recomposes the ground.
func sync_pads() -> void:
	terrain.clear_pads()
	for b in data.buildings:
		if b.has("base") and not b.get("roof_only", false):
			terrain.pads.append([BuildingView.footprint(b), float(b.base), 1.4])
	terrain.compose()


# ---------------------------------------------------------------------------
# Terrain patches (painted hills, cliffs and terraces)
# ---------------------------------------------------------------------------
## Paints a new terrain patch. `stack` starts it on top of the ground under
## the first point (terraces); otherwise it rises from the base meadow.
func add_terrain_patch(pts: PackedVector2Array, radius: float, height: float, fall: float, stack := false) -> Dictionary:
	var floor_h := terrain.height_without(pts[0], -1) if stack else terrain.base_height_at(pts[0])
	floor_h = maxf(floor_h, Terrain.WATER_LEVEL + 0.3)
	var p := {"id": next_id(), "pts": pts, "r": radius, "h": height, "fall": fall, "floor": floor_h}
	data.patches.append(p)
	terrain.compose_rect(Terrain.patch_bounds(p))
	return p


## Re-shapes a patch after its stroke, height or falloff changed (old bounds
## are passed so the ground it left is restored).
func update_terrain_patch(p: Dictionary, old_bounds := Rect2()) -> void:
	var r := Terrain.patch_bounds(p)
	if old_bounds.has_area():
		r = r.merge(old_bounds)
	terrain.compose_rect(r)


func remove_terrain_patch(p: Dictionary) -> void:
	var r := Terrain.patch_bounds(p)
	data.patches.erase(p)
	terrain.compose_rect(r)


## Scree and boulders at the foot of cliffs, rebuilt with the patches.
func _rebuild_scree() -> void:
	var old := get_node_or_null("Scree")
	if old:
		old.free()
	var deco := DecoMerge.new()
	var any := false
	for p in data.patches:
		var fall := float(p.get("fall", 0.6))
		if fall > 0.45:
			continue
		var rng := RandomNumberGenerator.new()
		rng.seed = int(p.id) * 131
		var pts: PackedVector2Array = p.pts
		var w := Terrain.patch_slope(p)
		var reach := float(p.r) + w * 0.5 + 0.25
		var samples: Array[Vector2] = []
		if pts.size() == 1:
			var n := int(TAU * reach / 1.1)
			for k in n:
				var a := TAU * k / n + rng.randf() * 0.3
				samples.append(pts[0] + Vector2(cos(a), sin(a)) * reach)
		else:
			var total := Geo.length(pts)
			var s := 0.0
			while s <= total:
				var c := Geo.point_at(pts, s)
				var t := Geo.tangent_at(pts, s)
				var nrm := Vector2(-t.y, t.x)
				samples.append(c + nrm * reach)
				samples.append(c - nrm * reach)
				s += 1.1
			for e in [0, 1]:
				var end: Vector2 = pts[0] if e == 0 else pts[pts.size() - 1]
				var dir := (pts[0] - pts[1]).normalized() if e == 0 else (pts[pts.size() - 1] - pts[pts.size() - 2]).normalized()
				for k in 5:
					var a := atan2(dir.y, dir.x) + (k - 2) * 0.55
					samples.append(end + Vector2(cos(a), sin(a)) * reach)
		for q in samples:
			if rng.randf() > 0.6 or not terrain.in_play_area(q, 0.3):
				continue
			if is_blocked(q):
				continue
			var kind := "rock_a" if rng.randf() < 0.4 else ("rock_b" if rng.randf() < 0.5 else "rock_c")
			var sc := rng.randf_range(0.45, 1.0) * lerpf(1.0, 0.6, fall * 2.0)
			var y := terrain.height_at_v(q) - 0.06
			deco.add(kind, Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * sc), Vector3(q.x, y, q.y)))
			any = true
	if any:
		var node := Node3D.new()
		node.name = "Scree"
		add_child(node)
		deco.apply_to(node)


func add_prop(kind: String, pos: Vector3, rot: float, scale_value: float, align := false, pop := true) -> Dictionary:
	var p := {"id": next_id(), "kind": kind, "p": pos, "r": rot, "s": scale_value}
	if align:
		p.n = terrain.normal_at(pos.x, pos.z).lerp(Vector3.UP, 0.4).normalized()
	data.props.append(p)
	if batch:
		return p
	if pop:
		props.pop_in(p)
	else:
		props.rebuild(data.props)
	changed.emit()
	return p


## Copies a piece a little to the side (Tiny Glade's clone) and returns the
## copy's id, or -1.
func clone(id: int, offset := Vector2(1.6, 1.6)) -> int:
	var f := find(id)
	if f.is_empty():
		return -1
	var src: Dictionary = f.item
	match f.type:
		"props":
			var pp: Vector3 = src.p + Vector3(offset.x, 0, offset.y)
			pp.y = terrain.height_at(pp.x, pp.z) - 0.03
			var p := add_prop(src.kind, pp, src.get("r", 0.0), src.get("s", 1.0), src.has("n"))
			return p.id
		"buildings":
			var b: Dictionary = src.duplicate(true)
			var size: Vector2 = b.get("size", Vector2(b.get("r", 2.0) * 2.0, b.get("r", 2.0) * 2.0))
			b.c = (src.c as Vector2) + offset.normalized() * (maxf(size.x, size.y) + 1.0)
			b.erase("seed")
			return add_building(b).id
		_:
			var item: Dictionary = src.duplicate(true)
			var pts: PackedVector2Array = item.pts
			for i in pts.size():
				pts[i] += offset
			item.pts = pts
			item.id = next_id()
			data[f.type].append(item)
			_make_view(f.type, item, true)
			mark_interactions()
			changed.emit()
			return item.id


## Cuts a wall, fence or path in two at the point nearest p (Tiny Glade's
## scissors). Returns the new piece's id, or -1 when too close to an end.
func split_line(id: int, p: Vector2) -> int:
	var f := find(id)
	if f.is_empty() or not f.type in ["walls", "fences", "paths"]:
		return -1
	var pts := Geo.resample(f.item.pts, 0.25)
	var bi := 0
	for k in pts.size():
		if pts[k].distance_to(p) < pts[bi].distance_to(p):
			bi = k
	var a := pts.slice(0, bi + 1)
	var b := pts.slice(bi)
	if Geo.length(a) < 0.8 or Geo.length(b) < 0.8:
		return -1
	# leave a small gap where the scissors went through
	var gap := 0.25
	a = Geo.resample(a, 0.5)
	b = Geo.resample(b, 0.5)
	if a.size() >= 2:
		a[a.size() - 1] = a[a.size() - 1] - (a[a.size() - 1] - a[a.size() - 2]).normalized() * gap
	if b.size() >= 2:
		b[0] = b[0] + (b[1] - b[0]).normalized() * gap
	f.item.pts = a
	var other: Dictionary = f.item.duplicate(true)
	other.id = next_id()
	other.pts = b
	data[f.type].append(other)
	_make_view(f.type, f.item, false)
	_make_view(f.type, other, false)
	mark_interactions()
	changed.emit()
	return other.id


func remove(id: int) -> void:
	var f := find(id)
	if f.is_empty():
		return
	var neighbours: Array = joined_with(f.item) if f.type == "buildings" else []
	data[f.type].erase(f.item)
	if f.type == "buildings" and f.item.get("roof_only", false):
		# the walls it sat on grow their battlements back
		for w in data.walls:
			if int(w.get("roofed", -1)) == id:
				w.erase("roofed")
				if views.has(w.id):
					_make_view("walls", w, false)
	for o in neighbours:
		if views.has(o.id):
			_make_view("buildings", o, false)
	if views.has(id):
		views[id].queue_free()
		views.erase(id)
		_links_dirty = true
	if f.type == "props":
		props.rebuild(data.props)
	else:
		mark_interactions()
	changed.emit()


func remove_props_near(center: Vector2, radius: float, kinds: Array = []) -> int:
	var removed := 0
	for p in data.props.duplicate():
		if not kinds.is_empty() and not kinds.has(p.kind):
			continue
		var pp: Vector3 = p.p
		if Vector2(pp.x, pp.z).distance_to(center) < radius + ModelLib.radius(p.kind) * 0.5:
			data.props.erase(p)
			removed += 1
	if removed > 0:
		props.rebuild(data.props)
		changed.emit()
	return removed


## Erases parts of walls/fences/paths inside the circle (splitting them).
func erase_lines_near(center: Vector2, radius: float, types: Array = ["walls", "fences", "paths", "stairs"]) -> int:
	var count := 0
	for type in ["walls", "fences", "paths"]:
		if not types.has(type):
			continue
		for item in data[type].duplicate():
			var pts: PackedVector2Array = item.pts
			if Geo.closest(pts, center).x > radius:
				continue
			var pieces := Geo.erase_circle(pts, center, radius)
			data[type].erase(item)
			if views.has(item.id):
				views[item.id].queue_free()
				views.erase(item.id)
				_links_dirty = true
			for piece in pieces:
				var copy: Dictionary = item.duplicate(true)
				copy.id = next_id()
				copy.pts = piece
				data[type].append(copy)
				_make_view(type, copy, false)
			count += 1
	# stairs go as a whole
	for st in (data.get("stairs", []) if types.has("stairs") else []).duplicate():
		if Geo.closest(st.pts, center).x <= radius:
			data.stairs.erase(st)
			if views.has(st.id):
				views[st.id].queue_free()
				views.erase(st.id)
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
		var neighbours: Array = []
		if f.type == "buildings":
			neighbours = joined_with(f.item)
			settle_building(f.item)
			for o in joined_with(f.item):
				if not neighbours.has(o):
					neighbours.append(o)
		_make_view(f.type, f.item, animate)
		# houses joined before or after the edit hide or show their buried windows
		for o in neighbours:
			if views.has(o.id):
				_make_view("buildings", o, false)
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
			v.joins = join_polys(item)
			v.build(item, _openings.get(item.id, []))
		"stairs":
			v = StairView.new()
			_roots.walls.add_child(v)
			v.build(item, terrain)
	views[item.id] = v
	_links_dirty = true
	if animate and v.has_method("play_build_anim"):
		v.play_build_anim()
	return v


## While true (templates), add_* only records data; one rebuild_all() at the
## end builds every view once instead of after each addition.
var batch := false


func rebuild_all() -> void:
	if batch:
		return
	sync_pads()
	terrain.flush()
	_rebuild_scree()
	for id in views:
		views[id].free()
	views.clear()
	_openings.clear()
	_compute_interactions()
	for type in ["walls", "fences", "paths", "buildings", "stairs"]:
		for item in data.get(type, []):
			_make_view(type, item, false)
	props.rebuild(data.props)
	_paint_mask()
	_rebuild_shore()


## Washing lines between facing clothesline windows (even across a lane to
## the next house) and bunting between nearby flags and banners.
func _rebuild_links() -> void:
	if _links == null:
		_links = Node3D.new()
		_links.name = "Links"
		add_child(_links)
	for c in _links.get_children():
		c.free()
	var lines: Array = []
	var flags: Array = []
	for id in views:
		var v = views[id]
		if not is_instance_valid(v):
			continue
		if "line_anchors" in v:
			for a in v.line_anchors:
				lines.append([a[0], a[1], id])
		if "flag_anchors" in v:
			for p in v.flag_anchors:
				flags.append(p)
	var mb := SurfaceTool.new()
	var any := false
	# washing lines: closest facing pairs first, each window used once
	var cands: Array = []
	for i in lines.size():
		for j in range(i + 1, lines.size()):
			var a: Vector3 = lines[i][0]
			var b: Vector3 = lines[j][0]
			var dv := b - a
			var dist := dv.length()
			if dist < 1.2 or dist > 10.0 or absf(dv.y) > dist * 0.5:
				continue
			var dn := dv / dist
			if (lines[i][1] as Vector3).dot(dn) < 0.25 or (lines[j][1] as Vector3).dot(-dn) < 0.25:
				continue
			cands.append([dist, i, j])
	cands.sort_custom(func(x, y): return x[0] < y[0])
	var used: Dictionary = {}
	for c in cands:
		if used.has(c[1]) or used.has(c[2]):
			continue
		used[c[1]] = true
		used[c[2]] = true
		var a: Vector3 = lines[c[1]][0]
		var b: Vector3 = lines[c[2]][0]
		mb.append_from(Ornaments.laundry(a, b, hash(Vector2i(int(a.x * 10), int(b.z * 10)))), 0, Transform3D.IDENTITY)
		any = true
	# bunting: every flag strings to its nearest neighbours
	var links: Dictionary = {}
	var count: Dictionary = {}
	for i in flags.size():
		var near: Array = []
		for j in flags.size():
			if i == j:
				continue
			var dist := (flags[i] as Vector3).distance_to(flags[j])
			if dist > 1.4 and dist < 9.0:
				near.append([dist, j])
		near.sort_custom(func(x, y): return x[0] < y[0])
		for k in mini(2, near.size()):
			var j: int = near[k][1]
			var key := Vector2i(mini(i, j), maxi(i, j))
			if links.has(key) or count.get(i, 0) >= 2 or count.get(j, 0) >= 2:
				continue
			links[key] = true
			count[i] = count.get(i, 0) + 1
			count[j] = count.get(j, 0) + 1
			mb.append_from(Ornaments.bunting(flags[i], flags[j], key.x * 131 + key.y), 0, Transform3D.IDENTITY)
			any = true
	if not any:
		return
	var mi := MeshInstance3D.new()
	mi.mesh = mb.commit()
	mi.material_override = ModelLib.props_material
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_links.add_child(mi)


## Adds stairs along `pts` rising from y0 (first point) to y1 (last point).
func add_stairs(pts: PackedVector2Array, y0: float, y1: float, w: float, mat: String) -> Dictionary:
	var st := {"id": next_id(), "pts": pts, "y0": snappedf(y0, 0.01), "y1": snappedf(y1, 0.01), "w": w, "mat": mat, "rail": true}
	data.stairs.append(st)
	_make_view("stairs", st, true)
	_after_edit(Geo.v3(pts[0], y0), "stairs")
	return st


## The height something standing at p would rest on: the ground, a flat
## roof, the top of a wall or the walking line of other stairs.
func surface_at(p: Vector2, near := 0.7) -> float:
	var h := terrain.height_at_v(p)
	for b in data.buildings:
		if b.get("roof", "") != "flat" and not b.get("roof_only", false):
			continue
		if Geometry2D.is_point_in_polygon(p, BuildingView.footprint(b)):
			var v = views.get(b.id)
			var top: float = float(b.get("base", 0.0)) + float(b.get("lift", 0.0)) + (v.eave if v else Catalog.PLINTH + b.floors * Catalog.FLOOR_H)
			h = maxf(h, top)
	for w in data.walls:
		var c := Geo.closest(w.pts, p)
		if c.x < near:
			h = maxf(h, terrain.height_at_v(Geo.point_at(w.pts, c.y)) + float(w.get("h", 2.4)))
	for st in data.get("stairs", []):
		var c2 := Geo.closest(st.pts, p)
		if c2.x < float(st.get("w", 1.2)) * 0.5:
			h = maxf(h, StairView.height_at(st, c2.y))
	return h


## Reeds along pond banks and lily pads on open water, placed deterministically.
func _rebuild_shore() -> void:
	var reeds: Array[Transform3D] = []
	var lilies: Array[Transform3D] = []
	var lim := Terrain.PLAY_HALF
	var step := 0.7
	var x := -lim
	while x <= lim:
		var z := -lim
		while z <= lim:
			var hsh := absi(hash(Vector2i(int(x * 10), int(z * 10))))
			var jx := x + (hsh % 100) / 100.0 * step
			var jz := z + ((hsh / 100) % 100) / 100.0 * step
			var h := terrain.height_at(jx, jz)
			var depth := Terrain.WATER_LEVEL - h
			var rot := Basis(Vector3.UP, (hsh % 628) / 100.0)
			if depth > -0.12 and depth < 0.18 and hsh % 3 == 0:
				reeds.append(Transform3D(rot.scaled(Vector3.ONE * (0.8 + (hsh % 50) / 100.0)), Vector3(jx, h - 0.05, jz)))
			elif depth > 0.45 and hsh % 11 == 0:
				lilies.append(Transform3D(rot.scaled(Vector3.ONE * (0.8 + (hsh % 40) / 100.0)), Vector3(jx, Terrain.WATER_LEVEL + 0.01, jz)))
			z += step
		x += step
	for pair in [["ShoreReeds", "reeds", reeds], ["ShoreLilies", "lily_pad_a", lilies]]:
		var mmi := get_node_or_null(pair[0]) as MultiMeshInstance3D
		if mmi == null:
			mmi = MultiMeshInstance3D.new()
			mmi.name = pair[0]
			mmi.material_override = ModelLib.grass_material
			mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			add_child(mmi)
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = ModelLib.merged(pair[1]).solid
		var xfs: Array = pair[2]
		mm.instance_count = xfs.size()
		for i in xfs.size():
			mm.set_instance_transform(i, xfs[i])
		mmi.multimesh = mm


func mark_interactions() -> void:
	_interactions_dirty = true


## Re-snaps everything that sits on the ground after a sculpt stroke.
func terrain_edited() -> void:
	# buildings ride up and down with the ground they stand on
	terrain.clear_pads()
	terrain.compose()
	var moved: Array = []
	for b in data.buildings:
		var target := maxf(terrain.average_height(BuildingView.footprint(b)), Terrain.WATER_LEVEL + 0.15)
		if absf(target - float(b.get("base", target))) > 0.05:
			b.base = target
			moved.append(b)
	sync_pads()
	terrain.flush()
	for b in moved:
		_make_view("buildings", b, false)
	for p in data.props:
		var pos: Vector3 = p.p
		pos.y = terrain.height_at(pos.x, pos.z)
		p.p = pos
	props.rebuild(data.props)
	for type in ["walls", "fences", "paths", "stairs"]:
		for item in data.get(type, []):
			_make_view(type, item, false)
	_rebuild_shore()
	_rebuild_scree()
	if boundary:
		var was := boundary.visible
		boundary.free()
		boundary = null
		show_boundary(was)
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
	if _links_dirty:
		_links_dirty = false
		_rebuild_links()
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
			var hits := Geo.intersections(ppts, wall.pts)
			for hit in hits:
				var w := pw / maxf(0.5, hit.sin) + 0.5
				_add_opening(wall.id, {"s": snappedf(hit.sb, 0.01), "w": snappedf(clampf(w, 1.2, 4.5), 0.01)})
			# a path that runs up to a wall (without passing through) gets a
			# door on that face of the wall
			if float(wall.get("h", 2.4)) >= 2.3:
				var wlen := Geo.length(wall.pts)
				for end in [ppts[0], ppts[ppts.size() - 1]]:
					var c := Geo.closest(wall.pts, end)
					if c.x > 1.1 or c.y < 0.9 or c.y > wlen - 0.9:
						continue
					var near_hit := false
					for hit in hits:
						if absf(hit.sb - c.y) < 2.0:
							near_hit = true
					if near_hit:
						continue
					var t := Geo.tangent_at(wall.pts, c.y)
					var wp := Geo.point_at(wall.pts, c.y)
					var side := 1.0 if (end - wp).dot(Vector2(-t.y, t.x)) >= 0.0 else -1.0
					_add_opening(wall.id, {"s": snappedf(c.y, 0.01), "door": side})
		for fence in data.fences:
			for hit in Geo.intersections(ppts, fence.pts):
				_add_opening(fence.id, {"s": snappedf(hit.sb, 0.01), "w": snappedf(clampf(pw, 1.0, 2.4), 0.01)})
		for b in data.buildings:
			for door in _doors_for(b, ppts, pw):
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


## Openings a path makes in a house: a door where it arrives, a wide
## archway when the path is broad, a tunnel (arches on both faces) where it
## runs right through, with an iron water gate if the passage is flooded.
func _doors_for(b: Dictionary, pts: PackedVector2Array, pw: float) -> Array:
	var poly := BuildingView.footprint(b)
	var closed := poly.duplicate()
	closed.append(poly[0])
	var hits := Geo.intersections(pts, closed)
	var points: Array = []
	for hit in hits:
		points.append(hit.point)
	if points.is_empty():
		# path ends right against the wall?
		for end in [pts[0], pts[pts.size() - 1]]:
			var d := INF
			for i in poly.size():
				d = minf(d, Geo.dist_to_segment(end, poly[i], poly[(i + 1) % poly.size()]))
			if d < 0.9:
				points.append(end)
				break
	if points.is_empty():
		return []
	var through := points.size() >= 2
	var tmp := BuildingView.new()
	tmp.data = b
	tmp.transform = Transform3D(BuildingView.local_basis(b.get("rot", 0.0)), Vector3(b.c.x, b.base, b.c.y))
	tmp.eave = Catalog.PLINTH + b.floors * Catalog.FLOOR_H
	var out: Array = []
	for point in points:
		var loc := tmp.locate(Vector3(point.x, b.base + 0.5, point.y))
		var o := {"side": loc.side, "u": snappedf(loc.u, 0.001), "s": 0.0}
		if (through or pw >= 2.0) and float(b.get("lift", 0.0)) < 0.3 and b.floors * Catalog.FLOOR_H > 2.4:
			o.arch = true
			o.aw = snappedf(pw + 0.4, 0.1)
			if terrain.height_at_v(point) < Terrain.WATER_LEVEL - 0.05:
				o.grate = true
		out.append(o)
		if not through:
			break
	tmp.free()
	return out


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
			"worn":
				# run-down cobbles: earth showing between the stones
				terrain.paint_polyline(p.pts, p.w + 0.3, 0, 1.0)
				terrain.paint_polyline(p.pts, p.w * 0.7, 1, 0.55)
			"setts":
				terrain.paint_polyline(p.pts, p.w, 3, 0.8)
				terrain.paint_polyline(p.pts, p.w * 0.6, 1, 0.4)
			"stones":
				terrain.paint_polyline(p.pts, p.w * 0.7, 0, 0.45)
			"paved":
				terrain.paint_polyline(p.pts, p.w, 3, 1.0)
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
		var top: float = b.base + float(b.get("lift", 0.0)) + Catalog.PLINTH + b.floors * Catalog.FLOOR_H
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
		# animals can shelter under a house raised on pillars
		if float(b.get("lift", 0.0)) >= 1.4:
			continue
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
		if float(bld.get("lift", 0.0)) >= 1.4:
			continue
		var poly := BuildingView.footprint(bld)
		var closed := poly.duplicate()
		closed.append(poly[0])
		if not Geo.intersections(seg, closed).is_empty():
			return true
	return false


## The plot's edge, drawn as a soft white line on the ground while building
## (like Tiny Glade's boundary); hidden in Explore and photo mode.
func show_boundary(on: bool) -> void:
	if on and boundary == null:
		var mb := MeshBuilder.new()
		var h := Terrain.PLAY_HALF
		var corners := [Vector2(-h, -h), Vector2(h, -h), Vector2(h, h), Vector2(-h, h)]
		var col := Color(1, 1, 1, 1)
		for i in 4:
			var a: Vector2 = corners[i]
			var b: Vector2 = corners[(i + 1) % 4]
			var steps := int(a.distance_to(b) / 0.5)
			var dir := (b - a).normalized()
			var nrm := Vector2(-dir.y, dir.x) * 0.06
			for k in steps:
				var p0 := a.lerp(b, float(k) / steps)
				var p1 := a.lerp(b, float(k + 1) / steps)
				var y0 := terrain.height_at_v(p0) + 0.06
				var y1 := terrain.height_at_v(p1) + 0.06
				mb.quad(Vector3(p0.x - nrm.x, y0, p0.y - nrm.y), Vector3(p1.x - nrm.x, y1, p1.y - nrm.y),
						Vector3(p1.x + nrm.x, y1, p1.y + nrm.y), Vector3(p0.x + nrm.x, y0, p0.y + nrm.y), col)
		boundary = MeshInstance3D.new()
		boundary.name = "Boundary"
		boundary.mesh = mb.commit()
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.albedo_color = Color(1.0, 1.0, 0.97, 0.75)
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		boundary.material_override = mat
		boundary.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(boundary)
	if boundary:
		boundary.visible = on
