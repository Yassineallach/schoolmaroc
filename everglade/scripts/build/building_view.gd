class_name BuildingView
extends Node3D
## Procedural cottage / tower. Rectangular footprints get gable, hip or flat
## (crenellated) roofs; round footprints become towers with cone or flat
## battlement tops. Windows, doors, dormers and chimneys are placed from the
## building's data; doors also appear automatically where paths arrive.

const FH := Catalog.FLOOR_H
const PL := Catalog.PLINTH
const NO_CHIMNEY := -99.0

var data: Dictionary
var body: StaticBody3D
var arch_mi: MeshInstance3D
var material: ShaderMaterial
var ivy: MultiMeshInstance3D
var perches: Array[Vector3] = []
var eave := 3.0
var roof_h := 2.0
var _deco_root: Node3D


static func local_basis(rot: float) -> Basis:
	return Basis(Vector3.UP, -rot)


static func footprint(d: Dictionary) -> PackedVector2Array:
	if d.shape == "round":
		var out := PackedVector2Array()
		var r: float = d.r
		for i in 16:
			var a := TAU * i / 16.0
			out.append(d.c + Vector2(cos(a), sin(a)) * r)
		return out
	return Geo.polygon_rect(d.c, d.size, d.rot)


static func default_windows(d: Dictionary) -> Array:
	var out: Array = []
	var floors: int = d.floors
	if d.shape == "round":
		var r: float = d.r
		var count := maxi(2, int(TAU * r / 2.6))
		for f in floors:
			for i in count:
				var u := (float(i) + (0.5 if f % 2 == 1 else 0.0)) / count + 0.125
				if f == 0 and i == 0:
					continue
				out.append({"side": 0, "u": fposmod(u, 1.0), "f": f, "kind": "window"})
		return out
	var L: float = d.size.x
	var W: float = d.size.y
	for side in 4:
		var side_len := L if side % 2 == 0 else W
		var count := int((side_len - 0.4) / 2.1)
		if count <= 0:
			continue
		for f in floors:
			for i in count:
				var u := (i + 0.5) / count
				if side == 0 and f == 0 and absf(u - 0.5) < 0.2:
					continue # keep the middle of the front free for a door
				out.append({"side": side, "u": u, "f": f, "kind": "window"})
	return out


func build(d: Dictionary, auto_doors: Array = [], preview := false) -> void:
	data = d
	for c in get_children():
		c.free()
	perches.clear()
	var c: Vector2 = d.c
	var base: float = d.get("base", 0.0)
	transform = Transform3D(local_basis(d.get("rot", 0.0)), Vector3(c.x, base, c.y))
	var floors: int = clampi(d.get("floors", 1), 1, 8)
	eave = PL + floors * FH
	var mb := MeshBuilder.new()
	var deco := DecoMerge.new()
	var seed_value: int = d.get("seed", 1)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var faces: Array = []
	if d.shape == "round":
		_build_round(d, mb, deco, rng, floors, auto_doors, faces)
	else:
		_build_rect(d, mb, deco, rng, floors, auto_doors, faces)

	material = ModelLib.new_arch_material()
	material.set_shader_parameter("base_height", base)
	material.set_shader_parameter("top_height", base + eave + roof_h + 1.0)
	material.set_shader_parameter("moss_amount", 0.35)
	arch_mi = MeshInstance3D.new()
	arch_mi.name = "Arch"
	arch_mi.mesh = mb.commit()
	arch_mi.material_override = material
	add_child(arch_mi)
	_deco_root = Node3D.new()
	_deco_root.name = "DecoRoot"
	add_child(_deco_root)
	deco.apply_to(_deco_root)
	if preview:
		return
	_add_smoke(d)
	ivy = Ivy.build(faces, seed_value * 13 + 5, 0.9)
	add_child(ivy)
	Ivy.set_growth(ivy, d.get("ivy", 0.0))
	body = StaticBody3D.new()
	body.collision_layer = 8
	body.set_meta("kind", "building")
	body.set_meta("id", d.id)
	var cs := CollisionShape3D.new()
	cs.shape = arch_mi.mesh.create_trimesh_shape()
	body.add_child(cs)
	add_child(body)
	for i in perches.size():
		perches[i] = transform * perches[i]


# ---------------------------------------------------------------------------
# Rectangular cottages
# ---------------------------------------------------------------------------
func _build_rect(d: Dictionary, mb: MeshBuilder, deco: DecoMerge, rng: RandomNumberGenerator, floors: int, auto_doors: Array, faces: Array) -> void:
	var L: float = d.size.x
	var W: float = d.size.y
	var style: String = d.get("style", "plaster")
	var wall_col: Color = d.get("wall_col", Catalog.WALL_COLORS[0])
	var roof_col: Color = d.get("roof_col", Catalog.ROOF_COLORS[0])
	var roof: String = d.get("roof", "gable")
	var pitch: float = d.get("pitch", 1.0)
	var stone_col := Color(0.76, 0.73, 0.68, 0.25)
	var wall_zone := 0.25 if style == "stone" else 0.0
	var wcol := Color(wall_col.r, wall_col.g, wall_col.b, wall_zone)
	if style == "stone":
		wcol = Color(stone_col.r * 1.05, stone_col.g * 1.05, stone_col.b * 1.05, 0.25)
	var corners := [Vector3(-L / 2, 0, -W / 2), Vector3(L / 2, 0, -W / 2), Vector3(L / 2, 0, W / 2), Vector3(-L / 2, 0, W / 2)]
	# foundation plinth (slightly proud of the walls)
	var fl := L + 0.16
	var fw := W + 0.16
	_ring_walls(mb, [Vector3(-fl / 2, 0, -fw / 2), Vector3(fl / 2, 0, -fw / 2), Vector3(fl / 2, 0, fw / 2), Vector3(-fl / 2, 0, fw / 2)], -1.6, PL, stone_col)
	mb.quad(Vector3(-fl / 2, PL, fw / 2), Vector3(fl / 2, PL, fw / 2), Vector3(fl / 2, PL, -fw / 2), Vector3(-fl / 2, PL, -fw / 2), stone_col)
	# main walls
	_ring_walls(mb, corners, PL, eave, wcol)
	for i in 4:
		faces.append({"a": corners[(i + 1) % 4] + Vector3.UP * 0.0, "b": corners[i], "n": _side_normal(corners, i), "h": eave * 0.9})
	# roof
	roof_h = 0.0
	match roof:
		"flat":
			_flat_rect_roof(mb, L, W, stone_col if style == "stone" else Color(0.74, 0.71, 0.66, 0.25))
			perches.append(Vector3(0, eave + 0.9, -W / 2))
		"hip":
			roof_h = W * 0.5 * 0.95 * pitch
			_hip_roof(mb, L, W, roof_h, roof_col)
			perches.append(Vector3(0, eave + roof_h + 0.1, 0))
		_:
			roof_h = W * 0.5 * 1.05 * pitch
			_gable_roof(mb, L, W, roof_h, roof_col, wcol)
			perches.append(Vector3(-L * 0.3, eave + roof_h + 0.15, 0))
			perches.append(Vector3(L * 0.3, eave + roof_h + 0.15, 0))
	# style trims
	if style == "timber":
		_timber(mb, corners, floors, d, auto_doors)
	elif style == "plaster":
		_quoins(mb, corners, Color(0.80, 0.77, 0.72, 1.0))
	# floor band between storeys
	if floors > 1 and style != "timber":
		for f in range(1, floors):
			var y := PL + f * FH
			_band(mb, corners, y, 0.14, 0.05, Color(wall_col.r * 0.9, wall_col.g * 0.88, wall_col.b * 0.85, 1.0))
	# openings
	var doors_done: Array = []
	for door in auto_doors:
		_place_rect_door(deco, corners, door.side, door.u)
		doors_done.append(door)
	var shutters := rng.randf() < 0.55 and style != "stone"
	var boxes := rng.randf() < 0.6
	for w in d.get("windows", []):
		var side: int = w.side
		var u: float = w.u
		var f: int = w.f
		var kind: String = w.get("kind", "window")
		if f >= floors and kind != "dormer":
			continue
		var blocked := false
		for dd in doors_done:
			if dd.side == side and f == 0 and absf(dd.u - u) * _side_len(corners, side) < 1.0:
				blocked = true
		if blocked:
			continue
		match kind:
			"door":
				_place_rect_door(deco, corners, side, u)
			"dormer":
				if roof == "gable" or roof == "hip":
					_place_dormer(deco, L, W, side, u)
			_:
				var a: Vector3 = corners[side]
				var b: Vector3 = corners[(side + 1) % 4]
				var n := _side_normal(corners, side)
				var p := a.lerp(b, u) + Vector3.UP * (PL + f * FH + 1.35)
				var xf := Transform3D(DecoMerge.facing(n), p)
				deco.add("window_frame", xf)
				if shutters:
					deco.add("shutters", xf)
				if boxes and f == 0:
					deco.add("flower_box", xf)
	# chimney
	var ch: float = d.get("chimney", NO_CHIMNEY)
	if ch > NO_CHIMNEY + 1.0:
		var cx := clampf(ch, -0.45, 0.45) * L
		var cz := W * 0.22
		var y_roof := eave + (roof_h * (1.0 - cz / (W * 0.5)) if roof != "flat" else 0.0)
		var sy := 1.0 + roof_h * 0.45
		deco.add("chimney", Transform3D(Basis.from_scale(Vector3(1, sy, 1)), Vector3(cx, y_roof - 0.5, cz)))
		set_meta("smoke_at", Vector3(cx, y_roof - 0.5 + 1.25 * sy + 0.1, cz))
	elif has_meta("smoke_at"):
		remove_meta("smoke_at")


func _side_len(corners: Array, side: int) -> float:
	return (corners[side] as Vector3).distance_to(corners[(side + 1) % 4])


func _side_normal(corners: Array, side: int) -> Vector3:
	var dvec: Vector3 = corners[(side + 1) % 4] - corners[side]
	return Vector3.UP.cross(dvec).normalized()


func _ring_walls(mb: MeshBuilder, corners: Array, y0: float, y1: float, col: Color) -> void:
	var u := 0.0
	for i in corners.size():
		var a: Vector3 = corners[(i + 1) % corners.size()]
		var b: Vector3 = corners[i]
		var l := a.distance_to(b)
		mb.quad(a + Vector3.UP * y0, b + Vector3.UP * y0, b + Vector3.UP * y1, a + Vector3.UP * y1, col,
				Vector2(u, y0), Vector2(u + l, y0), Vector2(u + l, y1), Vector2(u, y1))
		u += l


func _band(mb: MeshBuilder, corners: Array, y: float, h: float, out: float, col: Color) -> void:
	var grown: Array = []
	for c in corners:
		var v: Vector3 = c
		grown.append(v + Vector3(signf(v.x), 0, signf(v.z)) * out)
	_ring_walls(mb, grown, y - h * 0.5, y + h * 0.5, col)
	for i in grown.size():
		var a: Vector3 = grown[(i + 1) % grown.size()]
		var b: Vector3 = grown[i]
		var ia: Vector3 = corners[(i + 1) % corners.size()]
		var ib: Vector3 = corners[i]
		var top := Vector3.UP * (y + h * 0.5)
		mb.quad(ib + top, ia + top, a + top, b + top, col)


func _quoins(mb: MeshBuilder, corners: Array, col: Color) -> void:
	for c in corners:
		var v: Vector3 = c
		var y := PL + 0.05
		var k := 0
		while y < eave - 0.2:
			var big := k % 2 == 0
			var sx := 0.42 if big else 0.26
			var sz := 0.26 if big else 0.42
			var center := v + Vector3(-signf(v.x) * (sx * 0.5 - 0.04), y + 0.16, -signf(v.z) * (sz * 0.5 - 0.04))
			mb.box(Transform3D(Basis.IDENTITY, center), Vector3(sx, 0.3, sz), col)
			y += 0.34
			k += 1


func _timber(mb: MeshBuilder, corners: Array, floors: int, d: Dictionary, doors: Array = []) -> void:
	var beam := Color(0.36, 0.24, 0.16, 0.5)
	var t := 0.16
	for f in floors + 1:
		var y := PL + f * FH
		_band(mb, corners, y + (0.08 if f == 0 else 0.0), 0.16, 0.04, beam)
	for i in 4:
		var a: Vector3 = corners[i]
		var b: Vector3 = corners[(i + 1) % 4]
		var n := _side_normal(corners, i)
		var l := a.distance_to(b)
		var count := maxi(1, int(l / 1.3))
		for k in count + 1:
			var u := float(k) / count
			var skip := false
			for w in d.get("windows", []) + doors:
				if w.side == i and absf(w.u - u) * l < 0.65:
					skip = true
			if skip and k != 0 and k != count:
				continue
			var p := a.lerp(b, u) + n * 0.04
			var h := eave - PL
			mb.box(Transform3D(DecoMerge.facing(n), p + Vector3.UP * (PL + h * 0.5)), Vector3(t, h, 0.08), beam)
		# diagonal braces on the upper storeys at both ends of each side
		for f in range(1, floors):
			var y0 := PL + f * FH
			for end in [0.0, 1.0]:
				var dir := (b - a).normalized() * (1.0 if end == 0.0 else -1.0)
				var start := a.lerp(b, end) + n * 0.045
				var mid := start + dir * 0.55 + Vector3.UP * (y0 + FH * 0.5)
				var basis := DecoMerge.facing(n) * Basis(Vector3.BACK, (0.75 if end == 0.0 else -0.75) * (1.0 if i % 2 == 0 else 1.0))
				mb.box(Transform3D(basis, mid), Vector3(0.12, 1.5, 0.07), beam)


func _gable_roof(mb: MeshBuilder, L: float, W: float, rh: float, roof_col: Color, wall_col: Color) -> void:
	var ov := 0.38
	var ovx := 0.32
	var slope := rh / (W * 0.5)
	var ye := eave - ov * slope
	var yr := eave + rh
	var x0 := -L / 2 - ovx
	var x1 := L / 2 + ovx
	var zw := W / 2 + ov
	var tile := Color(roof_col.r, roof_col.g, roof_col.b, 0.75)
	var under := Color(0.42, 0.30, 0.22, 0.5)
	var fascia := Color(roof_col.r * 0.7, roof_col.g * 0.7, roof_col.b * 0.7, 1.0)
	var slant := sqrt(zw * zw + (yr - ye) * (yr - ye))
	var th := 0.14
	# gable triangles (walls)
	mb.tri(Vector3(L / 2, eave, W / 2), Vector3(L / 2, eave, -W / 2), Vector3(L / 2, yr, 0), wall_col,
			Vector2(0, eave), Vector2(W, eave), Vector2(W / 2, yr))
	mb.tri(Vector3(-L / 2, eave, -W / 2), Vector3(-L / 2, eave, W / 2), Vector3(-L / 2, yr, 0), wall_col,
			Vector2(0, eave), Vector2(W, eave), Vector2(W / 2, yr))
	# slopes (front z<0, back z>0)
	mb.quad(Vector3(x1, ye, -zw), Vector3(x0, ye, -zw), Vector3(x0, yr, 0), Vector3(x1, yr, 0), tile,
			Vector2(0, 0), Vector2(x1 - x0, 0), Vector2(x1 - x0, slant), Vector2(0, slant))
	mb.quad(Vector3(x0, ye, zw), Vector3(x1, ye, zw), Vector3(x1, yr, 0), Vector3(x0, yr, 0), tile,
			Vector2(0, 0), Vector2(x1 - x0, 0), Vector2(x1 - x0, slant), Vector2(0, slant))
	# undersides
	var dn := Vector3.DOWN * th
	mb.quad(Vector3(x0, ye, -zw) + dn, Vector3(x1, ye, -zw) + dn, Vector3(x1, yr, 0) + dn, Vector3(x0, yr, 0) + dn, under)
	mb.quad(Vector3(x1, ye, zw) + dn, Vector3(x0, ye, zw) + dn, Vector3(x0, yr, 0) + dn, Vector3(x1, yr, 0) + dn, under)
	# eave fascia
	mb.quad(Vector3(x1, ye, -zw) + dn, Vector3(x0, ye, -zw) + dn, Vector3(x0, ye, -zw), Vector3(x1, ye, -zw), fascia)
	mb.quad(Vector3(x0, ye, zw) + dn, Vector3(x1, ye, zw) + dn, Vector3(x1, ye, zw), Vector3(x0, ye, zw), fascia)
	# barge boards along the gable rakes
	for xs in [x0, x1]:
		var sgn := 1.0 if xs > 0 else -1.0
		for zs in [-zw, zw]:
			var e := Vector3(xs, ye, zs)
			var r := Vector3(xs, yr, 0)
			if (sgn > 0) == (zs > 0):
				mb.quad(e + dn, r + dn, r, e, fascia)
			else:
				mb.quad(r + dn, e + dn, e, r, fascia)
	# ridge
	mb.box(Transform3D(Basis(Vector3.RIGHT, PI / 4), Vector3(0, yr + 0.02, 0)), Vector3(x1 - x0 + 0.08, 0.2, 0.2), fascia)


func _hip_roof(mb: MeshBuilder, L: float, W: float, rh: float, roof_col: Color) -> void:
	var ov := 0.38
	var slope := rh / (W * 0.5)
	var ye := eave - ov * slope
	var yr := eave + rh
	var rx := maxf(0.0, (L - W) * 0.5)
	var xw := L / 2 + ov
	var zw := W / 2 + ov
	var tile := Color(roof_col.r, roof_col.g, roof_col.b, 0.75)
	var under := Color(0.42, 0.30, 0.22, 0.5)
	var fascia := Color(roof_col.r * 0.7, roof_col.g * 0.7, roof_col.b * 0.7, 1.0)
	var e0 := Vector3(-xw, ye, -zw)
	var e1 := Vector3(xw, ye, -zw)
	var e2 := Vector3(xw, ye, zw)
	var e3 := Vector3(-xw, ye, zw)
	var r0 := Vector3(-rx, yr, 0)
	var r1 := Vector3(rx, yr, 0)
	var slant := sqrt(zw * zw + (yr - ye) * (yr - ye))
	var sx := 2.0 * xw
	mb.quad(e1, e0, r0, r1, tile, Vector2(0, 0), Vector2(sx, 0), Vector2(xw + rx, slant), Vector2(xw - rx, slant))
	mb.quad(e3, e2, r1, r0, tile, Vector2(0, 0), Vector2(sx, 0), Vector2(xw + rx, slant), Vector2(xw - rx, slant))
	var sz := 2.0 * zw
	mb.tri(e2, e1, r1, tile, Vector2(0, 0), Vector2(sz, 0), Vector2(zw, slant))
	mb.tri(e0, e3, r0, tile, Vector2(0, 0), Vector2(sz, 0), Vector2(zw, slant))
	var dn := Vector3.DOWN * 0.14
	mb.quad(e0 + dn, e1 + dn, e2 + dn, e3 + dn, under)
	var ring := [e0, e1, e2, e3]
	for i in 4:
		var a: Vector3 = ring[i]
		var b: Vector3 = ring[(i + 1) % 4]
		mb.quad(b + dn, a + dn, a, b, fascia)
	if rx > 0.01:
		mb.box(Transform3D(Basis(Vector3.RIGHT, PI / 4), Vector3(0, yr + 0.02, 0)), Vector3(rx * 2.0 + 0.1, 0.2, 0.2), fascia)


func _flat_rect_roof(mb: MeshBuilder, L: float, W: float, col: Color) -> void:
	var top := Color(0.62, 0.58, 0.52, 0.5)
	var o := 0.12
	mb.quad(Vector3(-L / 2, eave, W / 2), Vector3(L / 2, eave, W / 2), Vector3(L / 2, eave, -W / 2), Vector3(-L / 2, eave, -W / 2), top,
			Vector2(0, 0), Vector2(L, 0), Vector2(L, W), Vector2(0, W))
	# corbel band then parapet with merlons
	var outer := [Vector3(-L / 2 - o, 0, -W / 2 - o), Vector3(L / 2 + o, 0, -W / 2 - o), Vector3(L / 2 + o, 0, W / 2 + o), Vector3(-L / 2 - o, 0, W / 2 + o)]
	var inner := [Vector3(-L / 2 + 0.2, 0, -W / 2 + 0.2), Vector3(L / 2 - 0.2, 0, -W / 2 + 0.2), Vector3(L / 2 - 0.2, 0, W / 2 - 0.2), Vector3(-L / 2 + 0.2, 0, W / 2 - 0.2)]
	_ring_walls(mb, outer, eave - 0.35, eave + 0.55, col)
	# inner face of the parapet (reverse winding)
	for i in 4:
		var a: Vector3 = inner[i]
		var b: Vector3 = inner[(i + 1) % 4]
		mb.quad(a + Vector3.UP * eave, b + Vector3.UP * eave, b + Vector3.UP * (eave + 0.55), a + Vector3.UP * (eave + 0.55), col)
		var oa: Vector3 = outer[i]
		var ob: Vector3 = outer[(i + 1) % 4]
		var y := eave + 0.55
		mb.quad(a + Vector3.UP * y, b + Vector3.UP * y, ob + Vector3.UP * y, oa + Vector3.UP * y, Color(col.r, col.g, col.b, 1.0))
		# underside of the corbel
		mb.quad(oa + Vector3.UP * (eave - 0.35), ob + Vector3.UP * (eave - 0.35), b + Vector3(0, eave - 0.35, 0) + (b - ob) * 0.0, a + Vector3.UP * (eave - 0.35), col)
		var l := oa.distance_to(ob)
		var count := maxi(1, int(l / 0.95))
		var n := Vector3.UP.cross(ob - oa).normalized()
		for k in count:
			var u := (k + 0.5) / count
			var p := oa.lerp(ob, u) - n * 0.16 + Vector3.UP * (y + 0.22)
			mb.box(Transform3D(DecoMerge.facing(n), p), Vector3(0.48, 0.44, 0.32), col)


# ---------------------------------------------------------------------------
# Round towers
# ---------------------------------------------------------------------------
func _build_round(d: Dictionary, mb: MeshBuilder, deco: DecoMerge, rng: RandomNumberGenerator, floors: int, auto_doors: Array, faces: Array) -> void:
	var R: float = d.r
	var style: String = d.get("style", "stone")
	var wall_col: Color = d.get("wall_col", Catalog.WALL_COLORS[0])
	var roof_col: Color = d.get("roof_col", Catalog.ROOF_COLORS[2])
	var roof: String = d.get("roof", "cone")
	var pitch: float = d.get("pitch", 1.0)
	var stone_col := Color(0.76, 0.73, 0.68, 0.25)
	var wcol := stone_col if style == "stone" else Color(wall_col.r, wall_col.g, wall_col.b, 0.0)
	var segs := clampi(int(R * 9.0), 14, 30)
	_cylinder(mb, R + 0.1, -1.6, PL, segs, stone_col)
	_cylinder(mb, R, PL, eave, segs, wcol)
	# ivy faces
	var chunk := maxi(1, segs / 6)
	var i := 0
	while i < segs:
		var a0 := TAU * i / segs
		var a1 := TAU * mini(i + chunk, segs) / segs
		var pa := Vector3(cos(a0), 0, sin(a0)) * R
		var pb := Vector3(cos(a1), 0, sin(a1)) * R
		faces.append({"a": pb, "b": pa, "n": ((pa + pb) * 0.5).normalized(), "h": eave * 0.9})
		i += chunk
	roof_h = 0.0
	if roof == "flat":
		_cylinder(mb, R + 0.18, eave - 0.3, eave + 0.55, segs, stone_col)
		_disc(mb, R + 0.18, eave - 0.3, segs, stone_col, true)
		_disc(mb, R - 0.05, eave, segs, Color(0.62, 0.58, 0.52, 0.5), false)
		var count := maxi(6, int(TAU * R / 0.95))
		for k in count:
			var a := TAU * (k + 0.5) / count
			var n := Vector3(cos(a), 0, sin(a))
			mb.box(Transform3D(DecoMerge.facing(n), n * (R + 0.02) + Vector3.UP * (eave + 0.77)), Vector3(0.46, 0.44, 0.34), stone_col)
		# inner parapet face & top rim
		_cylinder_inner(mb, R - 0.12, eave, eave + 0.55, segs, stone_col)
		_annulus(mb, R - 0.12, R + 0.18, eave + 0.55, segs, Color(stone_col.r, stone_col.g, stone_col.b, 1.0))
		deco.add("banner", Transform3D(Basis.IDENTITY, Vector3(0, eave, 0)))
		perches.append(Vector3(R * 0.7, eave + 1.0, 0))
	else:
		roof_h = R * 1.7 * pitch
		var ov := 0.4
		var slope := roof_h / R
		var ye := eave - ov * slope
		var apex := Vector3(0, eave + roof_h, 0)
		var tile := Color(roof_col.r, roof_col.g, roof_col.b, 0.75)
		var fascia := Color(roof_col.r * 0.7, roof_col.g * 0.7, roof_col.b * 0.7, 1.0)
		var rr := R + ov
		var slant := sqrt(rr * rr + (apex.y - ye) * (apex.y - ye))
		var rsegs := segs + 4
		for k in rsegs:
			var a0 := TAU * k / rsegs
			var a1 := TAU * (k + 1) / rsegs
			var p0 := Vector3(cos(a0) * rr, ye, sin(a0) * rr)
			var p1 := Vector3(cos(a1) * rr, ye, sin(a1) * rr)
			var u0 := a0 * rr
			var u1 := a1 * rr
			mb.tri(p1, p0, apex, tile, Vector2(-u1, 0), Vector2(-u0, 0), Vector2(-(u0 + u1) * 0.5, slant))
			mb.tri(p0 + Vector3.DOWN * 0.14, p1 + Vector3.DOWN * 0.14, apex + Vector3.DOWN * 0.14, Color(0.42, 0.30, 0.22, 0.5))
			mb.quad(p1 + Vector3.DOWN * 0.14, p0 + Vector3.DOWN * 0.14, p0, p1, fascia)
		deco.add("weathervane", Transform3D(Basis.IDENTITY, apex + Vector3.DOWN * 0.1))
		perches.append(apex + Vector3.UP * 0.9)
	# doors from paths
	for door in auto_doors:
		_place_round_opening(deco, R, door.u, 0, "door", rng)
	var boxes := rng.randf() < 0.4
	for w in d.get("windows", []):
		var f: int = w.f
		if f >= floors:
			continue
		var kind: String = w.get("kind", "window")
		var skip := false
		for door in auto_doors:
			if f == 0 and absf(angle_difference(door.u * TAU, w.u * TAU)) * R < 1.0:
				skip = true
		if not skip:
			_place_round_opening(deco, R, w.u, f, kind, rng, boxes)


func _place_round_opening(deco: DecoMerge, R: float, u: float, f: int, kind: String, rng: RandomNumberGenerator, boxes := false) -> void:
	var a := u * TAU
	var n := Vector3(cos(a), 0, sin(a))
	var p := n * (R - 0.02)
	if kind == "door":
		deco.add("door", Transform3D(DecoMerge.facing(n), p + Vector3.UP * PL))
		deco.add("stair_step", Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(1.2, 1.0, 1.4)), n * (R + 0.25) + Vector3.UP * 0.0))
		var side := n.cross(Vector3.UP).normalized()
		deco.add("wall_lantern", Transform3D(Basis.looking_at(n, Vector3.UP), p + side * 0.8 + Vector3.UP * (PL + 2.0)))
		return
	var xf := Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(0.75, 1, 1)), p + Vector3.UP * (PL + f * FH + 1.35))
	deco.add("window_frame", xf)
	if boxes and f == 0:
		deco.add("flower_box", xf)


func _cylinder(mb: MeshBuilder, r: float, y0: float, y1: float, segs: int, col: Color) -> void:
	for k in segs:
		var a0 := TAU * k / segs
		var a1 := TAU * (k + 1) / segs
		var n0 := Vector3(cos(a0), 0, sin(a0))
		var n1 := Vector3(cos(a1), 0, sin(a1))
		mb.quad_n(n1 * r + Vector3.UP * y0, n0 * r + Vector3.UP * y0, n0 * r + Vector3.UP * y1, n1 * r + Vector3.UP * y1,
				n1, n0, n0, n1, col,
				Vector2(-a1 * r, y0), Vector2(-a0 * r, y0), Vector2(-a0 * r, y1), Vector2(-a1 * r, y1))


func _cylinder_inner(mb: MeshBuilder, r: float, y0: float, y1: float, segs: int, col: Color) -> void:
	for k in segs:
		var a0 := TAU * k / segs
		var a1 := TAU * (k + 1) / segs
		var n0 := Vector3(cos(a0), 0, sin(a0))
		var n1 := Vector3(cos(a1), 0, sin(a1))
		mb.quad_n(n0 * r + Vector3.UP * y0, n1 * r + Vector3.UP * y0, n1 * r + Vector3.UP * y1, n0 * r + Vector3.UP * y1,
				-n0, -n1, -n1, -n0, col,
				Vector2(a0 * r, y0), Vector2(a1 * r, y0), Vector2(a1 * r, y1), Vector2(a0 * r, y1))


func _disc(mb: MeshBuilder, r: float, y: float, segs: int, col: Color, facing_down: bool) -> void:
	var c := Vector3(0, y, 0)
	for k in segs:
		var a0 := TAU * k / segs
		var a1 := TAU * (k + 1) / segs
		var p0 := Vector3(cos(a0) * r, y, sin(a0) * r)
		var p1 := Vector3(cos(a1) * r, y, sin(a1) * r)
		if facing_down:
			mb.tri(c, p0, p1, col, Vector2.ZERO, Vector2(p0.x, p0.z), Vector2(p1.x, p1.z))
		else:
			mb.tri(c, p1, p0, col, Vector2.ZERO, Vector2(p1.x, p1.z), Vector2(p0.x, p0.z))


func _annulus(mb: MeshBuilder, r0: float, r1: float, y: float, segs: int, col: Color) -> void:
	for k in segs:
		var a0 := TAU * k / segs
		var a1 := TAU * (k + 1) / segs
		var i0 := Vector3(cos(a0) * r0, y, sin(a0) * r0)
		var i1 := Vector3(cos(a1) * r0, y, sin(a1) * r0)
		var o0 := Vector3(cos(a0) * r1, y, sin(a0) * r1)
		var o1 := Vector3(cos(a1) * r1, y, sin(a1) * r1)
		mb.quad(i0, i1, o1, o0, col)


# ---------------------------------------------------------------------------
# Openings on rectangular walls
# ---------------------------------------------------------------------------
func _place_rect_door(deco: DecoMerge, corners: Array, side: int, u: float) -> void:
	var a: Vector3 = corners[side]
	var b: Vector3 = corners[(side + 1) % 4]
	var n := _side_normal(corners, side)
	var l := a.distance_to(b)
	var uu := clampf(u, 0.6 / l, 1.0 - 0.6 / l) if l > 1.2 else 0.5
	var p := a.lerp(b, uu)
	deco.add("door", Transform3D(DecoMerge.facing(n), p + Vector3.UP * PL + n * 0.02))
	deco.add("stair_step", Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(1.2, 1.0, 1.4)), p + n * 0.3))
	var along := (b - a).normalized()
	var side_off := 0.85 if uu * l + 0.85 < l - 0.2 else -0.85
	deco.add("wall_lantern", Transform3D(Basis.looking_at(n, Vector3.UP), p + along * side_off + Vector3.UP * (PL + 2.0) + n * 0.02))


func _place_dormer(deco: DecoMerge, L: float, W: float, side: int, u: float) -> void:
	var front := side == 0
	var n := Vector3(0, 0, -1) if front else Vector3(0, 0, 1)
	var x := lerpf(-L / 2 + 0.7, L / 2 - 0.7, clampf(u, 0.0, 1.0))
	if side % 2 == 1:
		x = 0.0
	var zf := W * 0.5 * 0.55
	var y := eave + roof_h * (1.0 - 0.55) - 0.25
	var p := Vector3(x, y, zf * (-1.0 if front else 1.0))
	deco.add("dormer", Transform3D(DecoMerge.facing(n), p))
	deco.add("window_frame", Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(0.75, 0.55, 1)), p + Vector3.UP * 0.4 + n * 0.02))


# ---------------------------------------------------------------------------
# Life
# ---------------------------------------------------------------------------
func _add_smoke(_d: Dictionary) -> void:
	if not has_meta("smoke_at"):
		return
	var p := CPUParticles3D.new()
	p.name = "Smoke"
	p.position = get_meta("smoke_at")
	p.amount = 14
	p.lifetime = 4.0
	p.preprocess = 4.0
	p.direction = Vector3(0.3, 1, 0)
	p.spread = 12.0
	p.gravity = Vector3(0.25, 0.25, 0.1)
	p.initial_velocity_min = 0.3
	p.initial_velocity_max = 0.6
	p.scale_amount_min = 0.6
	p.scale_amount_max = 1.2
	var curve := Curve.new()
	curve.add_point(Vector2(0, 0.3))
	curve.add_point(Vector2(0.3, 1.0))
	curve.add_point(Vector2(1, 1.6))
	p.scale_amount_curve = curve
	var grad := Gradient.new()
	grad.set_color(0, Color(0.9, 0.9, 0.9, 0.55))
	grad.set_color(1, Color(0.95, 0.95, 0.95, 0.0))
	p.color_ramp = grad
	var m := SphereMesh.new()
	m.radius = 0.22
	m.height = 0.44
	m.radial_segments = 8
	m.rings = 4
	var mat := StandardMaterial3D.new()
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.vertex_color_use_as_albedo = true
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_PER_VERTEX
	mat.albedo_color = Color(1, 1, 1, 1)
	m.material = mat
	p.mesh = m
	add_child(p)


func set_ivy(growth: float) -> void:
	Ivy.set_growth(ivy, growth)


func play_build_anim() -> void:
	if material == null:
		return
	material.set_shader_parameter("build_progress", 0.0)
	if _deco_root:
		_deco_root.visible = false
	var tw := create_tween()
	tw.tween_method(func(v): material.set_shader_parameter("build_progress", v), 0.0, 1.0, 0.7).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tw.tween_callback(func():
		if is_instance_valid(_deco_root):
			_deco_root.visible = true
			_deco_root.scale = Vector3.ONE * 0.9
			create_tween().tween_property(_deco_root, "scale", Vector3.ONE, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT))


## Converts a world hit point into {side, u, f, zone("wall"/"roof"), height}.
func locate(world: Vector3) -> Dictionary:
	var lp := transform.affine_inverse() * world
	var out := {"side": 0, "u": 0.5, "f": 0, "zone": "wall", "y": lp.y}
	if lp.y > eave - 0.05:
		out.zone = "roof"
	out.f = clampi(int((lp.y - PL) / FH), 0, maxi(0, int(data.get("floors", 1)) - 1))
	if data.shape == "round":
		out.u = fposmod(atan2(lp.z, lp.x) / TAU, 1.0)
		return out
	var L: float = data.size.x
	var W: float = data.size.y
	var dists := [absf(lp.z + W / 2), absf(lp.x - L / 2), absf(lp.z - W / 2), absf(lp.x + L / 2)]
	var best := 0
	for i in 4:
		if dists[i] < dists[best]:
			best = i
	out.side = best
	match best:
		0: out.u = (lp.x + L / 2) / L
		1: out.u = (lp.z + W / 2) / W
		2: out.u = (L / 2 - lp.x) / L
		3: out.u = (W / 2 - lp.z) / W
	out.u = clampf(out.u, 0.0, 1.0)
	if out.zone == "roof":
		out.side = 0 if lp.z < 0.0 else 2
		out.u = clampf((lp.x + L / 2) / L, 0.0, 1.0)
		out.x = lp.x
	return out
