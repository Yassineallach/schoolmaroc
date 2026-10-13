class_name MeshBuilder
extends RefCounted
## Small immediate-mode mesh accumulator. Faces are given counter-clockwise
## as seen from the front; they are emitted with Godot's clockwise winding.

var verts := PackedVector3Array()
var normals := PackedVector3Array()
var colors := PackedColorArray()
var uvs := PackedVector2Array()
var indices := PackedInt32Array()


func is_empty() -> bool:
	return indices.is_empty()


func _v(p: Vector3, n: Vector3, c: Color, uv: Vector2) -> int:
	verts.append(p)
	normals.append(n)
	colors.append(c)
	uvs.append(uv)
	return verts.size() - 1


func tri(a: Vector3, b: Vector3, c: Vector3, col: Color, ua := Vector2.ZERO, ub := Vector2.ZERO, uc := Vector2.ZERO) -> void:
	var n := (b - a).cross(c - a)
	if n.length_squared() < 1e-12:
		return
	n = n.normalized()
	var i0 := _v(a, n, col, ua)
	var i1 := _v(b, n, col, ub)
	var i2 := _v(c, n, col, uc)
	indices.append_array([i0, i2, i1])


## Flat quad a-b-c-d (counter-clockwise from the front).
func quad(a: Vector3, b: Vector3, c: Vector3, d: Vector3, col: Color,
		ua := Vector2(0, 0), ub := Vector2(1, 0), uc := Vector2(1, 1), ud := Vector2(0, 1)) -> void:
	var n := (b - a).cross(d - a)
	if n.length_squared() < 1e-12:
		n = (c - b).cross(a - b)
	if n.length_squared() < 1e-12:
		return
	n = n.normalized()
	quad_n(a, b, c, d, n, n, n, n, col, ua, ub, uc, ud)


## Quad with explicit per-corner normals (smooth curved surfaces).
func quad_n(a: Vector3, b: Vector3, c: Vector3, d: Vector3,
		na: Vector3, nb: Vector3, nc: Vector3, nd: Vector3, col: Color,
		ua := Vector2(0, 0), ub := Vector2(1, 0), uc := Vector2(1, 1), ud := Vector2(0, 1)) -> void:
	var i0 := _v(a, na, col, ua)
	var i1 := _v(b, nb, col, ub)
	var i2 := _v(c, nc, col, uc)
	var i3 := _v(d, nd, col, ud)
	indices.append_array([i0, i2, i1, i0, i3, i2])


## Axis-aligned-in-local-space box transformed by `xf`; UVs in metres.
func box(xf: Transform3D, size: Vector3, col: Color) -> void:
	var h := size * 0.5
	var c := [
		Vector3(-h.x, -h.y, -h.z), Vector3(h.x, -h.y, -h.z), Vector3(h.x, h.y, -h.z), Vector3(-h.x, h.y, -h.z),
		Vector3(-h.x, -h.y, h.z), Vector3(h.x, -h.y, h.z), Vector3(h.x, h.y, h.z), Vector3(-h.x, h.y, h.z),
	]
	var p: Array[Vector3] = []
	for v in c:
		p.append(xf * v)
	var sx := size.x
	var sy := size.y
	var sz := size.z
	# front (+z), back (-z), right (+x), left (-x), top (+y), bottom (-y)
	quad(p[4], p[5], p[6], p[7], col, Vector2(0, 0), Vector2(sx, 0), Vector2(sx, sy), Vector2(0, sy))
	quad(p[1], p[0], p[3], p[2], col, Vector2(0, 0), Vector2(sx, 0), Vector2(sx, sy), Vector2(0, sy))
	quad(p[5], p[1], p[2], p[6], col, Vector2(0, 0), Vector2(sz, 0), Vector2(sz, sy), Vector2(0, sy))
	quad(p[0], p[4], p[7], p[3], col, Vector2(0, 0), Vector2(sz, 0), Vector2(sz, sy), Vector2(0, sy))
	quad(p[7], p[6], p[2], p[3], col, Vector2(0, 0), Vector2(sx, 0), Vector2(sx, sz), Vector2(0, sz))
	quad(p[0], p[1], p[5], p[4], col, Vector2(0, 0), Vector2(sx, 0), Vector2(sx, sz), Vector2(0, sz))


## Quad whose winding is fixed up to face `n` (handy for generated solids).
func quad_facing(a: Vector3, b: Vector3, c: Vector3, d: Vector3, n: Vector3, col: Color,
		na := Vector3.ZERO, nb := Vector3.ZERO, nc := Vector3.ZERO, nd := Vector3.ZERO,
		ua := Vector2(0, 0), ub := Vector2(1, 0), uc := Vector2(1, 1), ud := Vector2(0, 1)) -> void:
	if na == Vector3.ZERO:
		na = n
		nb = n
		nc = n
		nd = n
	if (b - a).cross(d - a).dot(n) < 0.0:
		quad_n(a, d, c, b, na, nd, nc, nb, col, ua, ud, uc, ub)
	else:
		quad_n(a, b, c, d, na, nb, nc, nd, col, ua, ub, uc, ud)


func tri_facing(a: Vector3, b: Vector3, c: Vector3, n: Vector3, col: Color) -> void:
	var i0 := _v(a, n, col, Vector2(a.x + a.z, a.y))
	var i1 := _v(b, n, col, Vector2(b.x + b.z, b.y))
	var i2 := _v(c, n, col, Vector2(c.x + c.z, c.y))
	if (b - a).cross(c - a).dot(n) < 0.0:
		indices.append_array([i0, i1, i2])
	else:
		indices.append_array([i0, i2, i1])


## Box with every edge chamfered by `bevel` (soft, hand-cut blocks: coping
## stones, merlons, quoins, voussoirs, roof tiles). Edge normals are blended
## so the chamfers catch light like rounded edges.
func bevel_box(xf: Transform3D, size: Vector3, bevel: float, col: Color) -> void:
	var h := size * 0.5
	var b := minf(bevel, minf(h.x, minf(h.y, h.z)) * 0.45)
	var basis := xf.basis
	var nb := basis.inverse().transposed()
	# point on face `axis` (0..2) with sign `s`, at signs (t1, t2) of the other axes
	var pt := func(axis: int, s: float, t1: float, t2: float) -> Vector3:
		var o := Vector3.ZERO
		var a1 := (axis + 1) % 3
		var a2 := (axis + 2) % 3
		o[axis] = s * h[axis]
		o[a1] = t1 * (h[a1] - b)
		o[a2] = t2 * (h[a2] - b)
		return xf * o
	var wn := func(v: Vector3) -> Vector3:
		return (nb * v).normalized()
	for axis in 3:
		for s in [-1.0, 1.0]:
			var n := Vector3.ZERO
			n[axis] = s
			var w: Vector3 = wn.call(n)
			quad_facing(pt.call(axis, s, -1.0, -1.0), pt.call(axis, s, 1.0, -1.0), pt.call(axis, s, 1.0, 1.0), pt.call(axis, s, -1.0, 1.0), w, col)
	# 12 edge chamfers: faces (a, sa) and (c, sc) meet along the third axis
	for a in 3:
		var c := (a + 1) % 3
		var e := (a + 2) % 3
		for sa in [-1.0, 1.0]:
			for sc in [-1.0, 1.0]:
				var na := Vector3.ZERO
				na[a] = sa
				na[c] = sc
				var w2: Vector3 = wn.call(na)
				var na_only := Vector3.ZERO
				na_only[a] = sa
				var nc_only := Vector3.ZERO
				nc_only[c] = sc
				var p := []
				for se in [-1.0, 1.0]:
					# on face a: other axes are (a+1)=c and (a+2)=e
					var on_a: Vector3 = pt.call(a, sa, sc, se)
					# on face c: other axes are (c+1)=e and (c+2)=a
					var on_c: Vector3 = pt.call(c, sc, se, sa)
					p.append([on_a, on_c])
				quad_facing(p[0][0], p[1][0], p[1][1], p[0][1], w2, col,
						wn.call(na_only.lerp(na, 0.6)), wn.call(na_only.lerp(na, 0.6)), wn.call(nc_only.lerp(na, 0.6)), wn.call(nc_only.lerp(na, 0.6)))
	# 8 corner triangles
	for sx in [-1.0, 1.0]:
		for sy in [-1.0, 1.0]:
			for sz in [-1.0, 1.0]:
				var sgn := Vector3(sx, sy, sz)
				tri_facing(pt.call(0, sx, sy, sz), pt.call(1, sy, sz, sx), pt.call(2, sz, sx, sy), wn.call(sgn), col)


func commit(mesh: ArrayMesh = null) -> ArrayMesh:
	if mesh == null:
		mesh = ArrayMesh.new()
	else:
		mesh.clear_surfaces()
	if indices.is_empty():
		return mesh
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_COLOR] = colors
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_INDEX] = indices
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh
