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
