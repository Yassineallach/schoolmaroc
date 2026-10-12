class_name Terrain
extends Node3D
## Chunked heightfield with sculpting, a painted ground mask (paths, trodden
## earth) and textures shared with the water shader.

signal chunk_rebuilt(cx: int, cz: int)

const HALF := 32.0
const RES := 128
const CELL := HALF * 2.0 / RES
const VERTS := RES + 1
const CHUNKS := 8
const CHUNK_CELLS := RES / CHUNKS
const PLAY_HALF := 22.0
const WATER_LEVEL := -0.35
const MASK_RES := 256
const MIN_H := -1.6
const MAX_H := 9.0

var heights := PackedFloat32Array()
var material: ShaderMaterial
var mask_img: Image
var mask_tex: ImageTexture
var height_img: Image
var height_tex: ImageTexture

var _chunks: Array[MeshInstance3D] = []
var _dirty: Dictionary = {}
var _body: StaticBody3D
var _shape: HeightMapShape3D
var _collision_dirty := false
var _height_tex_dirty := false


func _ready() -> void:
	heights.resize(VERTS * VERTS)
	material = ShaderMaterial.new()
	material.shader = load("res://shaders/terrain.gdshader")
	mask_img = Image.create(MASK_RES, MASK_RES, false, Image.FORMAT_RGBA8)
	mask_img.fill(Color(0, 0, 0, 0))
	mask_tex = ImageTexture.create_from_image(mask_img)
	height_img = Image.create(VERTS, VERTS, false, Image.FORMAT_RF)
	height_tex = ImageTexture.create_from_image(height_img)
	material.set_shader_parameter("mask_tex", mask_tex)
	material.set_shader_parameter("terrain_origin", -HALF)
	material.set_shader_parameter("terrain_size", HALF * 2.0)
	material.set_shader_parameter("water_level", WATER_LEVEL)
	material.set_shader_parameter("play_half", PLAY_HALF)
	for cz in CHUNKS:
		for cx in CHUNKS:
			var mi := MeshInstance3D.new()
			mi.name = "Chunk_%d_%d" % [cx, cz]
			mi.material_override = material
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			add_child(mi)
			_chunks.append(mi)
	_body = StaticBody3D.new()
	_body.collision_layer = 1
	_body.set_meta("kind", "terrain")
	add_child(_body)
	var cs := CollisionShape3D.new()
	_shape = HeightMapShape3D.new()
	_shape.map_width = VERTS
	_shape.map_depth = VERTS
	cs.shape = _shape
	cs.scale = Vector3.ONE * CELL
	_body.add_child(cs)


# ---------------------------------------------------------------------------
# Generation & data
# ---------------------------------------------------------------------------
func generate(template: String, seed_value: int) -> void:
	var noise := FastNoiseLite.new()
	noise.seed = seed_value
	noise.frequency = 0.045
	noise.fractal_octaves = 3
	var hills := FastNoiseLite.new()
	hills.seed = seed_value + 11
	hills.frequency = 0.08
	var relief := 0.6
	match template:
		"hills":
			relief = 2.2
		"lake":
			relief = 0.5
		"empty", "town":
			relief = 0.25
		"ruins":
			relief = 0.9
		"village":
			relief = 0.45
	for z in VERTS:
		for x in VERTS:
			var wx := -HALF + x * CELL
			var wz := -HALF + z * CELL
			var h := noise.get_noise_2d(wx, wz) * relief
			if template == "hills":
				h += maxf(0.0, hills.get_noise_2d(wx, wz)) * 2.5
			if template == "lake":
				var d := Vector2(wx + 4.0, wz - 2.0).length() + noise.get_noise_2d(wx * 2.0, wz * 2.0) * 2.5
				h -= (1.0 - smoothstep(4.0, 8.5, d)) * 1.6
			if template == "village":
				# a broad jade lake across the south of the glade
				var dv := Vector2((wx - 1.0) * 0.62, wz - 8.5).length() + noise.get_noise_2d(wx * 1.5, wz * 1.5) * 2.0
				h -= (1.0 - smoothstep(6.0, 10.5, dv)) * 1.8
			h = maxf(h, MIN_H)
			if template != "lake" and template != "village":
				h = maxf(h, WATER_LEVEL + 0.3)
			# wild rolling hills around the glade
			var edge := maxf(absf(wx), absf(wz))
			var ring := smoothstep(PLAY_HALF - 1.0, HALF - 2.0, edge)
			h = lerpf(h, maxf(h, 0.0) + 2.5 + hills.get_noise_2d(wx * 0.6, wz * 0.6) * 2.0 + ring * 3.0, ring)
			heights[z * VERTS + x] = h
	mask_img.fill(Color(0, 0, 0, 0))
	mask_tex.update(mask_img)
	mark_all_dirty()


func set_heights(data: PackedFloat32Array) -> void:
	if data.size() == heights.size():
		heights = data.duplicate()
		mark_all_dirty()


func get_heights() -> PackedFloat32Array:
	return heights.duplicate()


func mark_all_dirty() -> void:
	for cz in CHUNKS:
		for cx in CHUNKS:
			_dirty[Vector2i(cx, cz)] = true
	_collision_dirty = true
	_height_tex_dirty = true


func _mark_region_dirty(min_x: int, min_z: int, max_x: int, max_z: int) -> void:
	var c0x := clampi((min_x - 1) / CHUNK_CELLS, 0, CHUNKS - 1)
	var c0z := clampi((min_z - 1) / CHUNK_CELLS, 0, CHUNKS - 1)
	var c1x := clampi((max_x + 1) / CHUNK_CELLS, 0, CHUNKS - 1)
	var c1z := clampi((max_z + 1) / CHUNK_CELLS, 0, CHUNKS - 1)
	for cz in range(c0z, c1z + 1):
		for cx in range(c0x, c1x + 1):
			_dirty[Vector2i(cx, cz)] = true
	_collision_dirty = true
	_height_tex_dirty = true


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------
func _h(x: int, z: int) -> float:
	return heights[clampi(z, 0, RES) * VERTS + clampi(x, 0, RES)]


func height_at(wx: float, wz: float) -> float:
	var fx := clampf((wx + HALF) / CELL, 0.0, RES - 0.001)
	var fz := clampf((wz + HALF) / CELL, 0.0, RES - 0.001)
	var x0 := int(fx)
	var z0 := int(fz)
	var tx := fx - x0
	var tz := fz - z0
	var a := lerpf(_h(x0, z0), _h(x0 + 1, z0), tx)
	var b := lerpf(_h(x0, z0 + 1), _h(x0 + 1, z0 + 1), tx)
	return lerpf(a, b, tz)


func height_at_v(p: Vector2) -> float:
	return height_at(p.x, p.y)


func normal_at(wx: float, wz: float) -> Vector3:
	var e := CELL
	var dx := height_at(wx + e, wz) - height_at(wx - e, wz)
	var dz := height_at(wx, wz + e) - height_at(wx, wz - e)
	return Vector3(-dx, 2.0 * e, -dz).normalized()


func is_water(wx: float, wz: float) -> bool:
	return height_at(wx, wz) < WATER_LEVEL - 0.08


func in_play_area(p: Vector2, margin := 0.0) -> bool:
	return absf(p.x) <= PLAY_HALF - margin and absf(p.y) <= PLAY_HALF - margin


func clamp_to_play(p: Vector2) -> Vector2:
	return Vector2(clampf(p.x, -PLAY_HALF, PLAY_HALF), clampf(p.y, -PLAY_HALF, PLAY_HALF))


func mask_at(wx: float, wz: float) -> Color:
	var px := clampi(int((wx + HALF) / (HALF * 2.0) * MASK_RES), 0, MASK_RES - 1)
	var pz := clampi(int((wz + HALF) / (HALF * 2.0) * MASK_RES), 0, MASK_RES - 1)
	return mask_img.get_pixel(px, pz)


# ---------------------------------------------------------------------------
# Sculpting
# ---------------------------------------------------------------------------
## mode: "raise", "lower", "smooth", "flatten", "dig" (pond)
func sculpt(center: Vector2, radius: float, strength: float, mode: String, target := 0.0) -> void:
	var min_x := int(floor((center.x - radius + HALF) / CELL))
	var max_x := int(ceil((center.x + radius + HALF) / CELL))
	var min_z := int(floor((center.y - radius + HALF) / CELL))
	var max_z := int(ceil((center.y + radius + HALF) / CELL))
	min_x = clampi(min_x, 0, RES)
	max_x = clampi(max_x, 0, RES)
	min_z = clampi(min_z, 0, RES)
	max_z = clampi(max_z, 0, RES)
	var src := heights.duplicate() if mode == "smooth" else heights
	for z in range(min_z, max_z + 1):
		for x in range(min_x, max_x + 1):
			var wx := -HALF + x * CELL
			var wz := -HALF + z * CELL
			if not in_play_area(Vector2(wx, wz), -1.0):
				continue
			var d := Vector2(wx, wz).distance_to(center) / radius
			if d >= 1.0:
				continue
			var w := (1.0 - d * d) * (1.0 - d * d) * strength
			var i := z * VERTS + x
			var h := heights[i]
			match mode:
				"raise":
					h += w
				"lower":
					h -= w
				"dig":
					h = lerpf(h, minf(h, WATER_LEVEL - 1.1), clampf(w, 0.0, 1.0))
				"flatten":
					h = lerpf(h, target, clampf(w * 1.5, 0.0, 1.0))
				"smooth":
					var avg := 0.0
					for oz in range(-1, 2):
						for ox in range(-1, 2):
							avg += src[clampi(z + oz, 0, RES) * VERTS + clampi(x + ox, 0, RES)]
					h = lerpf(h, avg / 9.0, clampf(w * 2.0, 0.0, 1.0))
			heights[i] = clampf(h, MIN_H, MAX_H)
	_mark_region_dirty(min_x, min_z, max_x, max_z)


## Levels the ground under a footprint (buildings sit on a little plinth).
func flatten_polygon(poly: PackedVector2Array, target: float, margin := 1.2) -> void:
	var bb := Rect2(poly[0], Vector2.ZERO)
	for p in poly:
		bb = bb.expand(p)
	bb = bb.grow(margin)
	var min_x := clampi(int(floor((bb.position.x + HALF) / CELL)), 0, RES)
	var max_x := clampi(int(ceil((bb.end.x + HALF) / CELL)), 0, RES)
	var min_z := clampi(int(floor((bb.position.y + HALF) / CELL)), 0, RES)
	var max_z := clampi(int(ceil((bb.end.y + HALF) / CELL)), 0, RES)
	for z in range(min_z, max_z + 1):
		for x in range(min_x, max_x + 1):
			var p := Vector2(-HALF + x * CELL, -HALF + z * CELL)
			var d := 0.0
			if not Geometry2D.is_point_in_polygon(p, poly):
				d = INF
				for i in poly.size():
					d = minf(d, Geo.dist_to_segment(p, poly[i], poly[(i + 1) % poly.size()]))
			if d > margin:
				continue
			var w := 1.0 - smoothstep(0.0, margin, d)
			var i := z * VERTS + x
			heights[i] = lerpf(heights[i], target, w)
	_mark_region_dirty(min_x, min_z, max_x, max_z)


func average_height(poly: PackedVector2Array) -> float:
	var sum := 0.0
	var n := 0
	for p in poly:
		sum += height_at_v(p)
		n += 1
	var c := Vector2.ZERO
	for p in poly:
		c += p
	c /= maxf(1.0, poly.size())
	sum += height_at_v(c) * 2.0
	n += 2
	return sum / n


# ---------------------------------------------------------------------------
# Ground mask (R dirt path, G cobble path, B trodden earth)
# ---------------------------------------------------------------------------
func clear_mask() -> void:
	mask_img.fill(Color(0, 0, 0, 0))


func commit_mask() -> void:
	mask_tex.update(mask_img)


func _to_px(p: Vector2) -> Vector2:
	return (p + Vector2(HALF, HALF)) / (HALF * 2.0) * MASK_RES


func paint_polyline(pts: PackedVector2Array, width: float, channel: int, strength := 1.0) -> void:
	if pts.size() < 2:
		return
	var px_per_m := MASK_RES / (HALF * 2.0)
	var bb := Rect2(pts[0], Vector2.ZERO)
	for p in pts:
		bb = bb.expand(p)
	bb = bb.grow(width)
	var p0 := _to_px(bb.position).floor()
	var p1 := _to_px(bb.end).ceil()
	var half_w := width * 0.5
	for y in range(maxi(0, int(p0.y)), mini(MASK_RES, int(p1.y) + 1)):
		for x in range(maxi(0, int(p0.x)), mini(MASK_RES, int(p1.x) + 1)):
			var wp := Vector2(x + 0.5, y + 0.5) / px_per_m - Vector2(HALF, HALF)
			var d := Geo.closest(pts, wp).x
			if d > half_w + 0.3:
				continue
			var v := (1.0 - smoothstep(half_w - 0.35, half_w + 0.3, d)) * strength
			var c := mask_img.get_pixel(x, y)
			c[channel] = maxf(c[channel], v)
			mask_img.set_pixel(x, y, c)


func paint_polygon(poly: PackedVector2Array, margin: float, channel: int, strength := 1.0) -> void:
	var px_per_m := MASK_RES / (HALF * 2.0)
	var bb := Rect2(poly[0], Vector2.ZERO)
	for p in poly:
		bb = bb.expand(p)
	bb = bb.grow(margin)
	var p0 := _to_px(bb.position).floor()
	var p1 := _to_px(bb.end).ceil()
	for y in range(maxi(0, int(p0.y)), mini(MASK_RES, int(p1.y) + 1)):
		for x in range(maxi(0, int(p0.x)), mini(MASK_RES, int(p1.x) + 1)):
			var wp := Vector2(x + 0.5, y + 0.5) / px_per_m - Vector2(HALF, HALF)
			var d := 0.0
			if not Geometry2D.is_point_in_polygon(wp, poly):
				d = INF
				for i in poly.size():
					d = minf(d, Geo.dist_to_segment(wp, poly[i], poly[(i + 1) % poly.size()]))
			if d > margin:
				continue
			var v := (1.0 - smoothstep(0.0, margin, d)) * strength
			var c := mask_img.get_pixel(x, y)
			c[channel] = maxf(c[channel], v)
			mask_img.set_pixel(x, y, c)


# ---------------------------------------------------------------------------
# Mesh building
# ---------------------------------------------------------------------------
func _process(_delta: float) -> void:
	flush(4)


## Rebuilds up to `budget` dirty chunks (pass -1 to rebuild everything).
func flush(budget := -1) -> void:
	var built := 0
	for key in _dirty.keys():
		if budget >= 0 and built >= budget:
			break
		_dirty.erase(key)
		_build_chunk(key.x, key.y)
		built += 1
	if _collision_dirty and (budget < 0 or _dirty.is_empty()):
		_collision_dirty = false
		var data := PackedFloat32Array()
		data.resize(heights.size())
		for i in heights.size():
			data[i] = heights[i] / CELL
		_shape.map_data = data
	if _height_tex_dirty:
		_height_tex_dirty = false
		for z in VERTS:
			for x in VERTS:
				height_img.set_pixel(x, z, Color(heights[z * VERTS + x], 0, 0))
		height_tex.update(height_img)


func is_settled() -> bool:
	return _dirty.is_empty()


func _build_chunk(cx: int, cz: int) -> void:
	var n := CHUNK_CELLS + 1
	var verts := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var idx := PackedInt32Array()
	verts.resize(n * n)
	normals.resize(n * n)
	uvs.resize(n * n)
	for lz in n:
		for lx in n:
			var x := cx * CHUNK_CELLS + lx
			var z := cz * CHUNK_CELLS + lz
			var wx := -HALF + x * CELL
			var wz := -HALF + z * CELL
			var i := lz * n + lx
			verts[i] = Vector3(wx, _h(x, z), wz)
			var dx := _h(x + 1, z) - _h(x - 1, z)
			var dz := _h(x, z + 1) - _h(x, z - 1)
			normals[i] = Vector3(-dx, 2.0 * CELL, -dz).normalized()
			uvs[i] = Vector2(wx, wz)
	for lz in CHUNK_CELLS:
		for lx in CHUNK_CELLS:
			var a := lz * n + lx
			var b := a + 1
			var c := a + n
			var d := c + 1
			# clockwise when seen from above (+Y)
			idx.append_array([a, b, d, a, d, c])
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	_chunks[cz * CHUNKS + cx].mesh = mesh
	chunk_rebuilt.emit(cx, cz)
