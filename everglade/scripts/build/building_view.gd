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
var ivy: Node3D
var perches: Array[Vector3] = []
var lamps: Array[Vector3] = []   # local positions of wall lanterns (lit at night)
var eave := 3.0
var roof_h := 2.0
var _deco_root: Node3D
## Footprints (in this house's local XZ) of houses joined onto it; set by the
## Glade before build(). Windows and doors buried inside them are left out.
var joins: Array = []
var _preview := false
var _rng := RandomNumberGenerator.new()
const LIMESTONE := Color(0.80, 0.76, 0.67)


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
	lamps.clear()
	_preview = preview
	_rng.seed = int(d.get("seed", 1)) * 31 + 7
	var c: Vector2 = d.c
	var base: float = d.get("base", 0.0)
	transform = Transform3D(local_basis(d.get("rot", 0.0)), Vector3(c.x, base, c.y))
	var floors: int = clampi(d.get("floors", 1), 1, 8)
	eave = PL + floors * FH
	if d.get("roof_only", false):
		eave = float(d.get("eave", 2.4))
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
	ivy = Ivy.build(faces, seed_value * 13 + 5, 1.4)
	add_child(ivy)
	Ivy.set_growth(ivy, d.get("ivy", 0.0))
	body = StaticBody3D.new()
	body.collision_layer = 8
	body.set_meta("kind", "building")
	body.set_meta("id", d.id)
	var cs := CollisionShape3D.new()
	# a simple volume is plenty for picking and for keeping the camera out
	# (a trimesh of every stone and tile would be slow to build)
	if d.shape == "round":
		var cyl := CylinderShape3D.new()
		cyl.radius = float(d.r) + 0.15
		cyl.height = eave + roof_h + 0.3
		cs.shape = cyl
	else:
		var box := BoxShape3D.new()
		box.size = Vector3(d.size.x + 0.3, eave + roof_h + 0.3, d.size.y + 0.3)
		cs.shape = box
	cs.position = Vector3(0, (eave + roof_h + 0.3) * 0.5 - 0.15, 0)
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
	var stone_col := Color(0.78, 0.74, 0.68, 0.25)
	var wall_zone := 0.25 if style == "stone" else 0.0
	var wcol := Color(wall_col.r, wall_col.g, wall_col.b, wall_zone)
	if style == "stone":
		wcol = Color(stone_col.r * 1.05, stone_col.g * 1.05, stone_col.b * 1.05, 0.25)
	var corners := [Vector3(-L / 2, 0, -W / 2), Vector3(L / 2, 0, -W / 2), Vector3(L / 2, 0, W / 2), Vector3(-L / 2, 0, W / 2)]
	if d.get("roof_only", false):
		# a roof laid over a ring of the player's own walls
		_rect_roof(mb, d, L, W, roof, pitch, roof_col, Color(stone_col.r, stone_col.g, stone_col.b, 0.25), stone_col, "stone")
		return
	# foundation plinth (slightly proud of the walls)
	var fl := L + 0.16
	var fw := W + 0.16
	var plinth := [Vector3(-fl / 2, 0, -fw / 2), Vector3(fl / 2, 0, -fw / 2), Vector3(fl / 2, 0, fw / 2), Vector3(-fl / 2, 0, fw / 2)]
	if _preview:
		_ring_walls(mb, plinth, -1.6, PL, stone_col)
	else:
		_ring_walls(mb, plinth, -1.6, PL, Masonry.mortar_color(LIMESTONE))
		_masonry_rect(mb, plinth, -0.35, PL, LIMESTONE.darkened(0.06), [])
	mb.quad(Vector3(-fl / 2, PL, fw / 2), Vector3(fl / 2, PL, fw / 2), Vector3(fl / 2, PL, -fw / 2), Vector3(-fl / 2, PL, -fw / 2), stone_col)
	# main walls (whole stone houses are laid stone by stone)
	if style == "stone" and not _preview:
		_ring_walls(mb, corners, PL, eave, Masonry.mortar_color(LIMESTONE))
		_masonry_rect(mb, corners, PL, eave, LIMESTONE, _openings(d, auto_doors, corners))
	else:
		_ring_walls(mb, corners, PL, eave, wcol)
		if style == "plaster" and not _preview:
			# worn lime render: stone patches and stone string courses
			var bands: Array = []
			for f in range(1, floors):
				bands.append(PL + f * FH)
			_masonry_rect(mb, corners, PL, eave - 0.1, LIMESTONE, _openings(d, auto_doors, corners), true, bands)
	for i in 4:
		faces.append({"a": corners[(i + 1) % 4] + Vector3.UP * 0.0, "b": corners[i], "n": _side_normal(corners, i), "h": eave * 0.9})
	# roof
	_rect_roof(mb, d, L, W, roof, pitch, roof_col, wcol, stone_col, style)
	# style trims
	if style == "windrise":
		_windrise(mb, corners, floors, d, auto_doors)
	elif style == "timber":
		_timber(mb, corners, floors, d, auto_doors)
	elif style == "plaster":
		_quoins(mb, corners, Color(0.80, 0.77, 0.72, 1.0))
	elif style == "lakeside":
		_lakeside(mb, corners, floors)
	# floor band between storeys
	if floors > 1 and style != "timber" and style != "windrise" and style != "lakeside" and not (style == "plaster" and not _preview):
		for f in range(1, floors):
			var y := PL + f * FH
			_band(mb, corners, y, 0.14, 0.05, Color(wall_col.r * 0.9, wall_col.g * 0.88, wall_col.b * 0.85, 1.0))
	# openings (none where another house is joined on)
	var doors_done: Array = []
	for door in auto_doors:
		if _in_join(_side_point(corners, door.side, door.u)):
			continue
		_place_rect_door(deco, corners, door.side, door.u, style)
		doors_done.append(door)
	var lake := style == "lakeside"
	var shutters := rng.randf() < 0.55 and style != "stone" and not lake
	var boxes := rng.randf() < 0.6 and not lake
	# windows and doors placed side by side merge into wide windows,
	# galleries and double doors
	var groups: Dictionary = {}   # "side:f:kind" -> [u...]
	for w in d.get("windows", []):
		var side: int = w.side
		var u: float = w.u
		var f: int = w.f
		var kind: String = w.get("kind", "window")
		if f >= floors and kind != "dormer":
			continue
		if kind != "dormer" and _in_join(_side_point(corners, side, u)):
			continue
		var blocked := false
		for dd in doors_done:
			if dd.side == side and f == 0 and absf(dd.u - u) * _side_len(corners, side) < 1.0:
				blocked = true
		if blocked:
			continue
		if kind == "dormer":
			if (roof == "gable" or roof == "hip") and not lake:
				_place_dormer(deco, L, W, side, u)
			continue
		var key := "%d:%d:%s" % [side, f, kind]
		if not groups.has(key):
			groups[key] = []
		groups[key].append(u)
	for key in groups:
		var parts: PackedStringArray = (key as String).split(":")
		var side := int(parts[0])
		var f := int(parts[1])
		var kind := parts[2]
		var us: Array = groups[key]
		us.sort()
		var len_side := _side_len(corners, side)
		var reach := 1.85 if kind == "window" else 1.75
		var i := 0
		while i < us.size():
			var j := i
			while j + 1 < us.size() and (float(us[j + 1]) - float(us[j])) * len_side < reach:
				j += 1
			var u0: float = us[i]
			var u1: float = us[j]
			var uc := (u0 + u1) * 0.5
			var extra := (u1 - u0) * len_side
			if kind == "door":
				_place_rect_door(deco, corners, side, uc, style, (extra + 1.5) / 1.5)
			else:
				var a: Vector3 = corners[side]
				var b: Vector3 = corners[(side + 1) % 4]
				var n := _side_normal(corners, side)
				var p := a.lerp(b, uc) + Vector3.UP * (PL + f * FH + 1.35)
				# under the eaves, keep the window head clear of the roof overhang
				if side % 2 == 0 and roof != "flat" and roof_h > 0.0:
					var slope_k := roof_h / (W * 0.5)
					p.y = minf(p.y, eave - 0.34 * slope_k - 1.0)
				# laid-stone storeys keep their deep stone surrounds bare, and sit
				# the window on the stone face (windrise stone is set 4 cm proud)
				var in_stone := style == "stone" or (style == "windrise" and f == 0 and floors > 1)
				if in_stone and style == "windrise" and not _preview:
					p += n * 0.05
				var sx := (extra + 1.4) / 1.4
				var xf := Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(sx, 1, 1)), p)
				deco.add("window_lattice" if lake else "window_frame", xf)
				if shutters and j == i and not (in_stone and not _preview):
					deco.add("shutters", xf)
				if boxes and f == 0:
					deco.add("flower_box", xf)
			i = j + 1
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




func _rect_roof(mb: MeshBuilder, d: Dictionary, L: float, W: float, roof: String, pitch: float, roof_col: Color,
		wcol: Color, stone_col: Color, style: String) -> void:
	var curve: float = d.get("curve", 0.0)
	roof_h = 0.0
	match roof:
		"flat":
			_flat_rect_roof(mb, L, W, stone_col if style == "stone" else Color(0.74, 0.71, 0.66, 0.25))
			perches.append(Vector3(0, eave + 0.9, -W / 2))
		"hip":
			roof_h = W * 0.5 * 0.95 * pitch
			_hip_roof(mb, L, W, roof_h, roof_col, curve)
			perches.append(Vector3(0, eave + roof_h + 0.1, 0))
		_ when style == "lakeside":
			roof_h = W * 0.5 * 0.8 * pitch
			_lakeside_roof(mb, L, W, roof_h, roof_col, wcol)
			perches.append(Vector3(0, eave + roof_h + 0.2, 0))
		_:
			roof_h = W * 0.5 * 1.05 * pitch
			_gable_roof(mb, L, W, roof_h, roof_col, wcol, curve)
			perches.append(Vector3(-L * 0.3, eave + roof_h + 0.15, 0))
			perches.append(Vector3(L * 0.3, eave + roof_h + 0.15, 0))


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


func _quoins(mb: MeshBuilder, corners: Array, col: Color, top := -1.0) -> void:
	var limit := eave - 0.2 if top < 0.0 else top - 0.1
	for c in corners:
		var v: Vector3 = c
		var y := PL + 0.05
		var k := 0
		while y < limit:
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


## Height offset of a roof profile at t (0 eave .. 1 ridge): positive curve
## bulges the slopes into a rounded roof, negative sags them into a flared,
## swept roof. Zero is the straight slope.
## `t0` is where the wall line meets the slope: the curve only starts inside
## it, so the roof keeps its height above the walls and window heads.
static func _bow(t: float, rh: float, curve: float, t0 := 0.0) -> float:
	var u := clampf((t - t0) / maxf(1.0 - t0, 0.01), 0.0, 1.0)
	return rh * curve * 0.32 * sin(PI * u)


## One roof face from the eave edge (el, er) up to the ridge edge (rl, rr),
## cut into bands that follow the curve; tiles, underside and all.
func _roof_face(mb: MeshBuilder, el: Vector3, er: Vector3, rl: Vector3, rr: Vector3, rh: float, curve: float,
		tile: Color, under: Color, tc: Color, t0 := 0.0) -> void:
	var bands := 1 if absf(curve) < 0.02 else 4
	var dn := Vector3.DOWN * 0.14
	for k in bands:
		var ta := float(k) / bands
		var tb := float(k + 1) / bands
		var a0 := el.lerp(rl, ta) + Vector3.UP * _bow(ta, rh, curve, t0)
		var b0 := er.lerp(rr, ta) + Vector3.UP * _bow(ta, rh, curve, t0)
		var a1 := el.lerp(rl, tb) + Vector3.UP * _bow(tb, rh, curve, t0)
		var b1 := er.lerp(rr, tb) + Vector3.UP * _bow(tb, rh, curve, t0)
		var w0 := a0.distance_to(b0)
		var sl := ((a0 + b0) * 0.5).distance_to((a1 + b1) * 0.5)
		var up := (b0 - a0).cross(a1 - a0)
		if up.length_squared() < 1e-8:
			up = (b1 - a1).cross(a1 - a0)
		up = up.normalized()
		if up.y < 0.0:
			up = -up
		mb.quad_facing(a0, b0, b1, a1, up, tile, up, up, up, up,
				Vector2(0, 0), Vector2(w0, 0), Vector2(w0, sl), Vector2(0, sl))
		mb.quad_facing(a0 + dn, b0 + dn, b1 + dn, a1 + dn, -up, under)
		if not _preview:
			Roofing.slope(mb, a1, b1, a0, b0, tc, _rng)


func _gable_roof(mb: MeshBuilder, L: float, W: float, rh: float, roof_col: Color, wall_col: Color, curve := 0.0) -> void:
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
	var tc := Color(roof_col.r, roof_col.g, roof_col.b, 1.0)
	var span := yr - ye
	var tw := ov / zw   # where the wall line meets the slope
	# gable end walls: follow the (possibly curved) roof profile
	var steps := 1 if absf(curve) < 0.02 else 6
	for xs in [L / 2, -L / 2]:
		var prof: Array = []
		for side in [-1.0, 1.0]:
			for k in steps + 1:
				var t := float(k) / steps
				var z: float = side * (W / 2) * (1.0 - t)
				# the roof surface above the wall plane (eave at the wall, not the overhang)
				var tq := 1.0 - (W / 2) * (1.0 - t) / zw
				var y := ye + span * tq + _bow(tq, rh, curve, tw)
				prof.append(Vector3(xs, maxf(y, eave), z))
		var foot := Vector3(xs, eave, 0)
		var pts: Array = [Vector3(xs, eave, -W / 2)]
		for k in steps + 1:
			pts.append(prof[k])
		for k in range(steps, -1, -1):
			pts.append(prof[steps + 1 + k])
		pts.append(Vector3(xs, eave, W / 2))
		for i in pts.size() - 1:
			var pa: Vector3 = pts[i]
			var pb: Vector3 = pts[i + 1]
			var facing := Vector3(signf(xs), 0, 0)
			mb.tri_facing(foot, pa, pb, facing, wall_col)
	# slopes (front z<0, back z>0)
	_roof_face(mb, Vector3(x0, ye, -zw), Vector3(x1, ye, -zw), Vector3(x0, yr, 0), Vector3(x1, yr, 0), rh, curve, tile, under, tc, tw)
	_roof_face(mb, Vector3(x1, ye, zw), Vector3(x0, ye, zw), Vector3(x1, yr, 0), Vector3(x0, yr, 0), rh, curve, tile, under, tc, tw)
	var dn := Vector3.DOWN * 0.14
	# eave fascia
	mb.quad(Vector3(x1, ye, -zw) + dn, Vector3(x0, ye, -zw) + dn, Vector3(x0, ye, -zw), Vector3(x1, ye, -zw), fascia)
	mb.quad(Vector3(x0, ye, zw) + dn, Vector3(x1, ye, zw) + dn, Vector3(x1, ye, zw), Vector3(x0, ye, zw), fascia)
	# barge boards along the gable rakes, following the curve
	var bands := 1 if absf(curve) < 0.02 else 4
	for xs in [x0, x1]:
		for zs in [-zw, zw]:
			for k in bands:
				var t0 := float(k) / bands
				var t1 := float(k + 1) / bands
				var e := Vector3(xs, ye, zs).lerp(Vector3(xs, yr, 0), t0) + Vector3.UP * _bow(t0, rh, curve, tw)
				var r := Vector3(xs, ye, zs).lerp(Vector3(xs, yr, 0), t1) + Vector3.UP * _bow(t1, rh, curve, tw)
				mb.quad_facing(e + dn, r + dn, r, e, Vector3(signf(xs), 0, 0), fascia)
	# ridge with gold finials at both gable ends
	mb.box(Transform3D(Basis(Vector3.RIGHT, PI / 4), Vector3(0, yr + 0.02, 0)), Vector3(x1 - x0 + 0.08, 0.2, 0.2), fascia)
	var gold := Color(0.95, 0.74, 0.30, 1.0)
	for xs in [x0 + 0.05, x1 - 0.05]:
		mb.box(Transform3D(Basis.IDENTITY, Vector3(xs, yr + 0.22, 0)), Vector3(0.12, 0.42, 0.12), gold)
		mb.box(Transform3D(Basis(Vector3.RIGHT, PI / 4), Vector3(xs, yr + 0.48, 0)), Vector3(0.1, 0.16, 0.16), gold)


func _hip_roof(mb: MeshBuilder, L: float, W: float, rh: float, roof_col: Color, curve := 0.0) -> void:
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
	var tc := Color(roof_col.r, roof_col.g, roof_col.b, 1.0)
	var e0 := Vector3(-xw, ye, -zw)
	var e1 := Vector3(xw, ye, -zw)
	var e2 := Vector3(xw, ye, zw)
	var e3 := Vector3(-xw, ye, zw)
	var r0 := Vector3(-rx, yr, 0)
	var r1 := Vector3(rx, yr, 0)
	var tw := ov / zw
	_roof_face(mb, e0, e1, r0, r1, rh, curve, tile, under, tc, tw)
	_roof_face(mb, e2, e3, r1, r0, rh, curve, tile, under, tc, tw)
	_roof_face(mb, e1, e2, r1, r1, rh, curve, tile, under, tc, tw)
	_roof_face(mb, e3, e0, r0, r0, rh, curve, tile, under, tc, tw)
	var dn := Vector3.DOWN * 0.14
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
	var ro: bool = d.get("roof_only", false)
	if ro:
		# a spire laid over a round ring of the player's own walls
		_round_roof(mb, deco, R, roof, pitch, roof_col, stone_col, segs)
		return
	if style == "windrise":
		_round_windrise(mb, R, floors, segs, d, auto_doors)
	if _preview:
		_cylinder(mb, R + 0.1, -1.6, PL, segs, stone_col)
	else:
		_cylinder(mb, R + 0.1, -1.6, PL, segs, Masonry.mortar_color(LIMESTONE))
		_masonry_round(mb, R + 0.1, -0.35, PL, LIMESTONE.darkened(0.06), [])
	if style == "stone" and not _preview:
		_cylinder(mb, R, PL, eave, segs, Masonry.mortar_color(LIMESTONE))
		_masonry_round(mb, R, PL, eave, LIMESTONE, _round_openings(d, auto_doors, R))
	else:
		_cylinder(mb, R, PL, eave, segs, wcol)
		if style == "plaster" and not _preview:
			var rbands: Array = []
			for f in range(1, floors):
				rbands.append(PL + f * FH)
			_masonry_round(mb, R, PL, eave - 0.1, LIMESTONE, _round_openings(d, auto_doors, R), true, rbands)
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
	_round_roof(mb, deco, R, roof, pitch, roof_col, stone_col, segs)
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


func _round_roof(mb: MeshBuilder, deco: DecoMerge, R: float, roof: String, pitch: float, roof_col: Color,
		stone_col: Color, segs: int) -> void:
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
		roof_h = R * 2.1 * pitch
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
		if not _preview:
			Roofing.cone(mb, apex, ye, rr, Color(roof_col.r, roof_col.g, roof_col.b, 1.0), _rng)
		deco.add("weathervane", Transform3D(Basis.IDENTITY, apex + Vector3.DOWN * 0.1))
		perches.append(apex + Vector3.UP * 0.9)


func _place_round_opening(deco: DecoMerge, R: float, u: float, f: int, kind: String, rng: RandomNumberGenerator, boxes := false) -> void:
	var a := u * TAU
	var n := Vector3(cos(a), 0, sin(a))
	var p := n * (R - 0.02)
	if kind == "door":
		deco.add("door", Transform3D(DecoMerge.facing(n), p + Vector3.UP * PL))
		deco.add("stair_step", Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(1.2, 1.0, 1.4)), n * (R + 0.25) + Vector3.UP * 0.0))
		var side := n.cross(Vector3.UP).normalized()
		deco.add("wall_lantern", Transform3D(Basis.looking_at(n, Vector3.UP), p + side * 0.8 + Vector3.UP * (PL + 2.0)))
		lamps.append(p + side * 0.8 + Vector3.UP * (PL + 1.9) + n * 0.3)
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
# Windrise style (fantasy-European town: stone base, plaster + timber above)
# ---------------------------------------------------------------------------
## Stone ground floor with quoins, white plaster upper storeys framed in dark
## timber with braces, gold trim between storeys and carved eave brackets.
func _windrise(mb: MeshBuilder, corners: Array, floors: int, d: Dictionary, doors: Array) -> void:
	var stone := Color(0.88, 0.84, 0.76, 0.25)
	var beam := Color(0.32, 0.22, 0.17, 0.5)
	var gold := Color(0.95, 0.74, 0.30, 1.0)
	var stone_top := PL + (FH if floors > 1 else 1.0)
	var grown: Array = []
	for c in corners:
		var v: Vector3 = c
		grown.append(v + Vector3(signf(v.x), 0, signf(v.z)) * 0.04)
	if _preview:
		_ring_walls(mb, grown, PL, stone_top, stone)
		_quoins(mb, corners, Color(0.95, 0.92, 0.85, 1.0), stone_top)
	else:
		_ring_walls(mb, grown, PL, stone_top, Masonry.mortar_color(LIMESTONE))
		_masonry_rect(mb, grown, PL, stone_top - 0.04, LIMESTONE, _openings(d, doors, corners))
	_band(mb, corners, stone_top, 0.12, 0.08, gold)
	# timber framing on the plaster above the stone
	for i in 4:
		var a: Vector3 = corners[i]
		var b: Vector3 = corners[(i + 1) % 4]
		var n := _side_normal(corners, i)
		var l := a.distance_to(b)
		var count := maxi(1, int(round(l / 1.25)))
		var h := eave - stone_top
		for k in count + 1:
			var u := float(k) / count
			var skip := false
			for w in d.get("windows", []) + doors:
				if w.side == i and w.get("f", 0) >= (1 if floors > 1 else 0) and absf(w.u - u) * l < 0.6 and k != 0 and k != count:
					skip = true
			if skip:
				continue
			var p := a.lerp(b, u) + n * 0.05
			mb.box(Transform3D(DecoMerge.facing(n), p + Vector3.UP * (stone_top + h * 0.5)), Vector3(0.16, h, 0.09), beam)
		# St Andrew's braces inside window-free bays, one per storey
		var seg_w := l / count
		var first_f := 1 if floors > 1 else 0
		for f in range(first_f, floors):
			var y0 := maxf(PL + f * FH, stone_top) + 0.1
			var y1 := PL + (f + 1) * FH - 0.12
			var fh := y1 - y0
			if fh < 0.8:
				continue
			for k in count:
				var busy := false
				for w in d.get("windows", []) + doors:
					if w.side == i and w.get("f", 0) == f and w.u > float(k) / count and w.u < float(k + 1) / count:
						busy = true
				if busy:
					continue
				var mid := a.lerp(b, (k + 0.5) / count) + n * 0.055 + Vector3.UP * ((y0 + y1) * 0.5)
				var ang := atan2(fh, seg_w - 0.16) * (1.0 if (k + f) % 2 == 0 else -1.0)
				var diag := sqrt((seg_w - 0.16) * (seg_w - 0.16) + fh * fh)
				mb.box(Transform3D(DecoMerge.facing(n) * Basis(Vector3.BACK, ang), mid), Vector3(diag, 0.11, 0.07), beam)
	for f in range(1, floors + 1):
		var y := PL + f * FH
		if y > stone_top + 0.3:
			_band(mb, corners, y - (0.08 if f == floors else 0.0), 0.15, 0.06, beam)
	# carved brackets under the eaves
	for i in 4:
		var a2: Vector3 = corners[i]
		var b2: Vector3 = corners[(i + 1) % 4]
		var n2 := _side_normal(corners, i)
		var l2 := a2.distance_to(b2)
		var nb := maxi(2, int(l2 / 1.2))
		for k in nb + 1:
			var p2 := a2.lerp(b2, float(k) / nb) + n2 * 0.18 + Vector3.UP * (eave - 0.12)
			mb.box(Transform3D(DecoMerge.facing(n2) * Basis(Vector3.RIGHT, -0.5), p2), Vector3(0.1, 0.1, 0.42), beam)


## Lake-village style: whitewashed walls over a dark stone skirting, a timber
## band under the eaves and slim dark posts at the corners.
func _lakeside(mb: MeshBuilder, corners: Array, _floors: int) -> void:
	var skirt := Color(0.46, 0.47, 0.50, 0.25)
	var wood := Color(0.24, 0.17, 0.13, 0.5)
	var grown: Array = []
	for c in corners:
		var v: Vector3 = c
		grown.append(v + Vector3(signf(v.x), 0, signf(v.z)) * 0.05)
	_ring_walls(mb, grown, PL, PL + 0.75, skirt)
	_band(mb, corners, PL + 0.78, 0.08, 0.07, Color(0.36, 0.37, 0.40, 1.0))
	_band(mb, corners, eave - 0.22, 0.32, 0.06, wood)
	for c in corners:
		var v2: Vector3 = c
		mb.box(Transform3D(Basis.IDENTITY, v2 + Vector3(0, (PL + 0.75 + eave) * 0.5, 0)), Vector3(0.2, eave - PL - 0.75, 0.2), wood)


## Dark-tiled roof with gently curved (concave) slopes and upturned corners,
## flanked by stepped "horse-head" parapet gables.
func _lakeside_roof(mb: MeshBuilder, L: float, W: float, rh: float, roof_col: Color, wall_col: Color) -> void:
	var ov := 0.55
	var zw := W / 2 + ov
	var x0 := -L / 2 + 0.12
	var x1 := L / 2 - 0.12
	var ye := eave - 0.12
	var yr := eave + rh
	var tile := Color(roof_col.r, roof_col.g, roof_col.b, 0.75)
	var under := Color(0.30, 0.22, 0.17, 0.5)
	var fascia := Color(roof_col.r * 0.65, roof_col.g * 0.65, roof_col.b * 0.65, 1.0)
	var nx := 8
	var nt := 6
	var th := 0.12
	for side in [-1.0, 1.0]:
		var grid: Array = []
		for ix in nx + 1:
			var row: Array = []
			var x := lerpf(x0, x1, float(ix) / nx)
			var ex := absf(float(ix) / nx * 2.0 - 1.0)
			for it in nt + 1:
				var t := float(it) / nt
				var y := ye + (yr - ye) * pow(t, 1.9)
				y += 0.6 * pow(ex, 3.0) * (1.0 - t) * (1.0 - t)
				row.append(Vector3(x, y, side * zw * (1.0 - t)))
			grid.append(row)
		for ix in nx:
			for it in nt:
				var a: Vector3 = grid[ix][it]
				var b: Vector3 = grid[ix + 1][it]
				var c: Vector3 = grid[ix + 1][it + 1]
				var e: Vector3 = grid[ix][it + 1]
				var ua := Vector2(a.x - x0, zw * float(it) / nt * 1.15)
				var ub := Vector2(b.x - x0, ua.y)
				var uc := Vector2(b.x - x0, zw * float(it + 1) / nt * 1.15)
				var ue := Vector2(a.x - x0, uc.y)
				var dn := Vector3.DOWN * th
				if side < 0:
					mb.quad(b, a, e, c, tile, ub, ua, ue, uc)
					mb.quad(a + dn, b + dn, c + dn, e + dn, under)
				else:
					mb.quad(a, b, c, e, tile, ua, ub, uc, ue)
					mb.quad(b + dn, a + dn, e + dn, c + dn, under)
			# eave fascia strip
			var f0: Vector3 = grid[ix][0]
			var f1: Vector3 = grid[ix + 1][0]
			var d2 := Vector3.DOWN * th
			if side < 0:
				mb.quad(f1 + d2, f0 + d2, f0, f1, fascia)
			else:
				mb.quad(f0 + d2, f1 + d2, f1, f0, fascia)
	# ridge beam with curled tips
	mb.box(Transform3D(Basis.IDENTITY, Vector3(0, yr + 0.08, 0)), Vector3(x1 - x0, 0.2, 0.24), fascia)
	for xs in [x0 + 0.1, x1 - 0.1]:
		mb.box(Transform3D(Basis(Vector3.BACK, 0.6 * signf(xs)), Vector3(xs, yr + 0.26, 0)), Vector3(0.12, 0.36, 0.2), fascia)
	# stepped horse-head gables (white walls with dark tiled caps)
	var cap := Color(roof_col.r * 0.8, roof_col.g * 0.8, roof_col.b * 0.8, 1.0)
	var steps := 3
	for xs2 in [-L / 2, L / 2]:
		for k in steps:
			var z_out := (W / 2 + 0.06) * (1.0 - float(k) / steps)
			var z_in := 0.0 if k == steps - 1 else (W / 2) * (1.0 - float(k + 1) / steps)
			var t_in := 1.0 - z_in / zw
			var top := ye + (yr - ye) * pow(t_in, 1.9) + 0.55
			for zsgn in ([1.0] if k == steps - 1 else [-1.0, 1.0]):
				var za: float = z_out * zsgn
				var zb: float = -z_out if k == steps - 1 else z_in * zsgn
				var zc: float = (za + zb) * 0.5
				var zl := absf(za - zb)
				mb.box(Transform3D(Basis.IDENTITY, Vector3(xs2, (eave - 0.3 + top) * 0.5, zc)), Vector3(0.3, top - eave + 0.3, zl), Color(wall_col.r, wall_col.g, wall_col.b, 0.0))
				mb.box(Transform3D(Basis.IDENTITY, Vector3(xs2, top + 0.06, zc)), Vector3(0.46, 0.12, zl + 0.12), cap)
				mb.box(Transform3D(Basis(Vector3.RIGHT, PI / 4), Vector3(xs2, top + 0.14, zc)), Vector3(0.12, 0.14, zl + 0.1), cap)
				# horse-head tip curling up at the outer end
				var tip_z: float = za + signf(za) * 0.06 if absf(za) > 0.01 else 0.0
				mb.box(Transform3D(Basis(Vector3.RIGHT, -0.5 * signf(za)), Vector3(xs2, top + 0.2, tip_z)), Vector3(0.32, 0.12, 0.28), cap)


func _round_windrise(mb: MeshBuilder, R: float, floors: int, segs: int, d: Dictionary = {}, auto_doors: Array = []) -> void:
	var stone := Color(0.88, 0.84, 0.76, 0.25)
	var beam := Color(0.32, 0.22, 0.17, 0.5)
	var gold := Color(0.95, 0.74, 0.30, 1.0)
	var stone_top := PL + (FH if floors > 1 else 1.0)
	if _preview:
		_cylinder(mb, R + 0.04, PL, stone_top, segs, stone)
	else:
		_cylinder(mb, R + 0.04, PL, stone_top, segs, Masonry.mortar_color(LIMESTONE))
		_masonry_round(mb, R + 0.04, PL, stone_top - 0.04, LIMESTONE, _round_openings(d, auto_doors, R))
	_cylinder(mb, R + 0.09, stone_top - 0.06, stone_top + 0.06, segs, gold)
	for f in range(2, floors + 1):
		var y := PL + f * FH
		_cylinder(mb, R + 0.05, y - 0.07, y + 0.07, segs, beam)
	var posts := maxi(6, int(TAU * R / 1.3))
	for k in posts:
		var a := TAU * (k + 0.5) / posts
		var nn := Vector3(cos(a), 0, sin(a))
		var h := eave - stone_top
		if h > 0.5:
			mb.box(Transform3D(DecoMerge.facing(nn), nn * (R + 0.04) + Vector3.UP * (stone_top + h * 0.5)), Vector3(0.14, h, 0.08), beam)


# ---------------------------------------------------------------------------
# Openings on rectangular walls
# ---------------------------------------------------------------------------
func _side_point(corners: Array, side: int, u: float) -> Vector3:
	var a: Vector3 = corners[side]
	var b: Vector3 = corners[(side + 1) % 4]
	return a.lerp(b, u) + _side_normal(corners, side) * 0.3


## True when a point (local space) lies inside a house joined onto this one.
func _in_join(p: Vector3) -> bool:
	for poly in joins:
		if Geometry2D.is_point_in_polygon(Vector2(p.x, p.z), poly):
			return true
	return false


func _place_rect_door(deco: DecoMerge, corners: Array, side: int, u: float, style := "", sx := 1.0) -> void:
	var a: Vector3 = corners[side]
	var b: Vector3 = corners[(side + 1) % 4]
	var n := _side_normal(corners, side)
	var l := a.distance_to(b)
	var uu := clampf(u, 0.6 / l, 1.0 - 0.6 / l) if l > 1.2 else 0.5
	var p := a.lerp(b, uu)
	if style == "lakeside":
		# timber double door with red paper lanterns (they glow by night)
		deco.add("door_wood", Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(sx, 1, 1)), p + Vector3.UP * PL + n * 0.02))
		deco.add("stair_step", Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(1.4, 1.0, 1.4)), p + n * 0.3))
		return
	deco.add("door", Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(sx, 1, 1)), p + Vector3.UP * PL + n * 0.02))
	deco.add("stair_step", Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(1.2 * sx, 1.0, 1.4)), p + n * 0.3))
	var along := (b - a).normalized()
	var side_off := 0.85 * sx if uu * l + 0.85 * sx < l - 0.2 else -0.85 * sx
	deco.add("wall_lantern", Transform3D(Basis.looking_at(n, Vector3.UP), p + along * side_off + Vector3.UP * (PL + 2.0) + n * 0.02))
	lamps.append(p + along * side_off + Vector3.UP * (PL + 1.9) + n * 0.3)


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


# ---------------------------------------------------------------------------
# Individually laid stonework
# ---------------------------------------------------------------------------
## Opening rectangles per side (s along the side, absolute y) for windows
## and doors, so no stone is laid across them.
func _openings(d: Dictionary, doors: Array, corners: Array) -> Array:
	var holes: Array = [[], [], [], []]
	for w in d.get("windows", []) + doors:
		var side: int = w.side
		if side < 0 or side > 3:
			continue
		var l := _side_len(corners, side)
		var s: float = w.u * l
		var kind: String = w.get("kind", "door" if not w.has("f") else "window")
		if kind == "dormer":
			continue
		if kind == "door":
			holes[side].append(Rect2(s - 0.64, PL - 0.2, 1.28, 2.55))
		else:
			var y: float = PL + int(w.get("f", 0)) * FH + 1.35
			holes[side].append(Rect2(s - 0.5, y - 0.62, 1.0, 1.42))
	return holes


func _round_openings(d: Dictionary, doors: Array, R: float) -> Array:
	var holes: Array = []
	var circ := TAU * R
	for w in d.get("windows", []) + doors:
		var kind: String = w.get("kind", "door" if not w.has("f") else "window")
		var s: float = fposmod(w.u, 1.0) * circ
		var rect: Rect2
		if kind == "door":
			rect = Rect2(s - 0.66, PL - 0.2, 1.32, 2.6)
		else:
			var y: float = PL + int(w.get("f", 0)) * FH + 1.35
			rect = Rect2(s - 0.4, y - 0.62, 0.8, 1.42)
		holes.append(rect)
		holes.append(Rect2(rect.position + Vector2(circ, 0), rect.size))
		holes.append(Rect2(rect.position - Vector2(circ, 0), rect.size))
	return holes


static func _hits(holes: Array, s0: float, s1: float, y0: float, y1: float) -> bool:
	var r := Rect2(s0, y0, s1 - s0, y1 - y0)
	for h in holes:
		if (h as Rect2).intersects(r):
			return true
	return false


## Veto for plastered walls: stones only show in worn patches and along the
## band courses between storeys.
func _patch_veto(length: float, y0: float, y1: float, bands: Array) -> Callable:
	var patches: Array = []
	var count := int(length * (y1 - y0) / 9.0 + _rng.randf() * 1.5)
	for i in count:
		patches.append(Vector4(_rng.randf_range(0.4, length - 0.4), _rng.randf_range(y0 + 0.3, y1 - 0.4), _rng.randf_range(0.3, 0.7), _rng.randf_range(0.22, 0.45)))
	return func(s0: float, s1: float, ya: float, yb: float) -> bool:
		var ym := (ya + yb) * 0.5
		for b in bands:
			if absf(ym - b) < 0.13:
				return false
		var sm := (s0 + s1) * 0.5
		for p in patches:
			var dx: float = (sm - p.x) / p.z
			var dy: float = (ym - p.y) / p.w
			if dx * dx + dy * dy < 1.0:
				return false
		return true


func _masonry_rect(mb: MeshBuilder, corners: Array, y0: float, y1: float, col: Color, holes: Array, patchy := false, bands: Array = []) -> void:
	for i in 4:
		var a: Vector3 = corners[i]
		var b: Vector3 = corners[(i + 1) % 4]
		var n := _side_normal(corners, i)
		var dir := (b - a).normalized()
		var l := a.distance_to(b)
		var side_holes: Array = holes[i] if i < holes.size() else []
		var surf := func(s: float) -> Dictionary:
			return {"p": Vector3(a.x, 0.0, a.z) + dir * s, "n": n, "g": y0, "low": y0 - 0.01, "top": y1}
		# run a little past both corners so the faces interlock
		Masonry.lay(mb, surf, -Masonry.DEPTH, l + Masonry.DEPTH, 0.0, y1 - y0, col, _rng,
				func(s0, s1, ya, yb): return _hits(side_holes, s0, s1, ya, yb),
				_patch_veto(l, y0, y1, bands) if patchy else Callable())


func _masonry_round(mb: MeshBuilder, R: float, y0: float, y1: float, col: Color, holes: Array, patchy := false, bands: Array = []) -> void:
	var surf := func(s: float) -> Dictionary:
		var ang := s / R
		var n := Vector3(cos(ang), 0.0, sin(ang))
		return {"p": n * R, "n": n, "g": y0, "low": y0 - 0.01, "top": y1}
	Masonry.lay(mb, surf, 0.0, TAU * R, 0.0, y1 - y0, col, _rng,
			func(s0, s1, ya, yb): return _hits(holes, s0, s1, ya, yb),
			_patch_veto(TAU * R, y0, y1, bands) if patchy else Callable())
