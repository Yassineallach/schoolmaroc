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
## World-space anchors the Glade strings lines between: clothesline brackets
## ([point, outward normal]) and flag / banner tips (bunting).
var line_anchors: Array = []
var flag_anchors: Array[Vector3] = []
var eave := 3.0
var roof_h := 2.0
var _deco_root: Node3D
## Footprints (in this house's local XZ) of houses joined onto it; set by the
## Glade before build(). Windows and doors buried inside them are left out.
var joins: Array = []
var _preview := false
var _rng := RandomNumberGenerator.new()
var _peel := 1.0      # how much stone shows through worn plaster (0 none)
## Height of the stilts/pillars the house stands on (0 = on the ground).
var lift := 0.0
## Openings planned for the walls being built: WallCut holes to cut, and
## rectangles stonework and boards keep clear of (per side on rectangular
## houses, one list round towers).
var _cut: Array = []
var _clear: Array = []
## Jettied timber houses: how far the upper storeys stand out over the
## ground floor (0 = flush), and where the jetty starts.
var _jet := 0.0
var _jet_y := 0.0
# Tiny Glade's pale sandy stone (#D8C8A6)
const LIMESTONE := Color(0.84, 0.78, 0.65)


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
	line_anchors.clear()
	flag_anchors.clear()
	_preview = preview
	_rng.seed = int(d.get("seed", 1)) * 31 + 7
	var c: Vector2 = d.c
	lift = clampf(float(d.get("lift", 0.0)), 0.0, 8.0)
	_peel = clampf(float(d.get("peel", 1.0)), 0.0, 3.0)
	var base: float = float(d.get("base", 0.0)) + lift
	transform = Transform3D(local_basis(d.get("rot", 0.0)), Vector3(c.x, base, c.y))
	var floors: int = clampi(d.get("floors", 1), 0, 8)
	# no storeys at all: a low tent-like house that is nearly all roof
	eave = PL + floors * FH if floors > 0 else PL + 0.4
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

	if not preview and not d.get("roof_only", false):
		_greenery(deco, d, auto_doors)
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
	if d.has("glass"):
		# window light painted another colour
		var gi := _deco_root.get_node_or_null("DecoGlow") as MeshInstance3D
		if gi:
			var gm := ModelLib.glow_material.duplicate() as ShaderMaterial
			var gc: Color = d.glass
			gm.set_shader_parameter("tint", Vector3(gc.r, gc.g, gc.b) / Vector3(1.0, 0.86, 0.6))
			gi.material_override = gm
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
		box.size = Vector3(d.size.x + 0.3 + 2.0 * _jet, eave + roof_h + 0.3, d.size.y + 0.3 + 2.0 * _jet)
		cs.shape = box
	cs.position = Vector3(0, (eave + roof_h + 0.3) * 0.5 - 0.15, 0)
	body.add_child(cs)
	add_child(body)
	for i in perches.size():
		perches[i] = transform * perches[i]
	for i in flag_anchors.size():
		flag_anchors[i] = transform * flag_anchors[i]
	for a in line_anchors:
		a[0] = transform * a[0]
		a[1] = transform.basis * a[1]


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
	# roof
	# timber houses carry their upper storeys out over the ground floor on a
	# row of beam ends (a jetty), as in Tiny Glade
	_jet = 0.22 if style == "timber" and floors > 1 and not _preview else 0.0
	_jet_y = PL + FH
	_rect_roof(mb, d, L + 2.0 * _jet, W + 2.0 * _jet, roof, pitch, roof_col, wcol, stone_col, style)
	# openings (none where another house is joined on), planned before the
	# walls so the walls can be laid round them
	_cut = [[], [], [], []]
	_clear = [[], [], [], []]
	var doors_done: Array = []
	for door in auto_doors:
		if _in_join(_side_point(corners, door.side, door.u)):
			continue
		if door.get("arch", false):
			var aw: float = clampf(float(door.get("aw", 2.0)), 1.4, 5.0)
			var sa: float = door.u * _side_len(corners, door.side)
			_clear[door.side].append(Rect2(sa - aw * 0.5 - 0.35, -2.0, aw + 0.7, arch_height(aw) + 2.3))
			_place_arch(deco, _side_point(corners, door.side, clampf(door.u, 0.1, 0.9)) + _side_normal(corners, door.side) * 0.02,
					_side_normal(corners, door.side), door)
		else:
			_place_rect_door(deco, corners, door.side, door.u, style)
		doors_done.append(door)
	var lake := style == "lakeside"
	var shutters := rng.randf() < 0.55 and style != "stone" and not lake
	var boxes := rng.randf() < 0.6 and not lake
	# windows and doors placed side by side merge into wide windows,
	# galleries and double doors
	var groups: Dictionary = {}   # "side:f:kind:type" -> [window...]
	for w in d.get("windows", []):
		var side: int = w.side
		var u: float = w.u
		var f: int = w.f
		var kind: String = w.get("kind", "window")
		if kind == "trapdoor":
			# a hatch in a flat roof
			if roof == "flat":
				var tx := clampf(float(w.get("x", 0.0)), -L / 2 + 0.6, L / 2 - 0.6)
				var tz := clampf(float(w.get("z", 0.0)), -W / 2 + 0.6, W / 2 - 0.6)
				deco.add("trapdoor", Transform3D(Basis.IDENTITY, Vector3(tx, eave + 0.02, tz)))
			continue
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
			if (roof == "gable" or roof == "hip") and not lake and not d.get("ridge", false):
				_place_dormer(deco, L, W, side, u)
			continue
		var key := "%d:%d:%s:%s" % [side, f, kind, w.get("wt", "plain")]
		if not groups.has(key):
			groups[key] = []
		groups[key].append(w)
	for key in groups:
		var parts: PackedStringArray = (key as String).split(":")
		var side := int(parts[0])
		var f := int(parts[1])
		var kind := parts[2]
		var wt := parts[3]
		var ws: Array = groups[key]
		ws.sort_custom(func(a, b): return float(a.u) < float(b.u))
		var len_side := _side_len(corners, side)
		var model := _window_model(wt, style) if kind == "window" else ""
		# only plain square windows (and doors) merge into wide ones
		var square := kind == "door" or (model != "" and int(WallCut.MODELS[model].arch) == WallCut.FLAT)
		var reach := (1.85 if kind == "window" else 1.75) if wt == "plain" and square else 0.0
		var i := 0
		while i < ws.size():
			var j := i
			while j + 1 < ws.size() and (float(ws[j + 1].u) - float(ws[j].u)) * len_side < reach:
				j += 1
			var u0: float = ws[i].u
			var u1: float = ws[j].u
			var uc := (u0 + u1) * 0.5
			var extra := (u1 - u0) * len_side
			var trim := -1
			for k in range(i, j + 1):
				trim = maxi(trim, int(ws[k].get("deco", -1)))
			if kind == "door":
				_place_rect_door(deco, corners, side, uc, style, (extra + 1.5) / 1.5)
			else:
				var a: Vector3 = corners[side]
				var b: Vector3 = corners[(side + 1) % 4]
				var n := _side_normal(corners, side)
				if model == "":
					# round windows and arrow slits stay carved ornaments on the face
					var pc := a.lerp(b, uc) + Vector3.UP * (PL + f * FH + 1.35)
					_clear[side].append(_window_hole(wt, uc * len_side, pc.y))
					_fancy_window(deco, wt, Transform3D(DecoMerge.facing(n), pc))
					i = j + 1
					continue
				var mw: float = WallCut.MODELS[model].w
				var sx := (extra + mw) / mw
				var hgt := WallCut.model_height(model)
				var y := PL + f * FH + 0.75
				# under the eaves, keep the window head clear of the roof overhang
				var turned: bool = d.get("ridge", false)
				if (side % 2 == 0) != turned and roof != "flat" and roof_h > 0.0:
					var slope_k := roof_h / ((L if turned else W) * 0.5)
					y = minf(y, eave - 0.34 * slope_k - 0.08 - hgt)
				y = minf(y, eave - 0.12 - hgt)
				# laid-stone storeys keep their deep stone surrounds bare; windrise
				# stone is set 4 cm proud, so its windows sit in that face
				var in_stone := style == "stone" or (style == "windrise" and f == 0 and floors > 1)
				var p := a.lerp(b, uc) + Vector3.UP * y
				if _jet > 0.0 and y >= _jet_y:
					p += n * _jet
				if style == "windrise" and in_stone:
					p += n * 0.04
				var hl := WallCut.hole_for(model, uc * len_side, y, sx)
				_cut[side].append(hl)
				_clear[side].append(WallCut.rect(hl, 0.05 + _surround_w(style)))
				_tg(deco, model, Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(sx, 1, 1)), p))
				# shutters and boxes fit the opening's width
				var xf := Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(hl.w / 0.96, 1, 1)), p)
				if trim < 0:
					# windows placed before decorations were chosen keep the house's look
					if shutters and j == i and not (in_stone and not _preview):
						_tg(deco, "tg_shutters", xf)
					if boxes and f == 0:
						_tg(deco, "tg_flower_box", xf)
				else:
					_window_trim(deco, trim, xf, p + Vector3.UP * hgt * 0.55, n, j == i)
			i = j + 1
	# foundation plinth (slightly proud of the walls)
	var fl := L + 0.16
	var fw := W + 0.16
	var plinth := [Vector3(-fl / 2, 0, -fw / 2), Vector3(fl / 2, 0, -fw / 2), Vector3(fl / 2, 0, fw / 2), Vector3(-fl / 2, 0, fw / 2)]
	var foot := -1.6 if lift < 0.05 else 0.0
	if _preview:
		_ring_walls(mb, plinth, foot, PL, stone_col)
	else:
		_ring_walls(mb, plinth, foot, PL, Masonry.mortar_color(LIMESTONE))
		_masonry_rect(mb, plinth, maxf(foot, -0.35), PL, LIMESTONE.darkened(0.06), [])
	mb.quad(Vector3(-fl / 2, PL, fw / 2), Vector3(fl / 2, PL, fw / 2), Vector3(fl / 2, PL, -fw / 2), Vector3(-fl / 2, PL, -fw / 2), stone_col)
	if lift >= 0.05:
		_stilts_rect(mb, deco, L, W)
	# main walls (whole stone houses are laid stone by stone)
	if style == "stone" and not _preview:
		_ring_walls(mb, corners, PL, eave, Masonry.mortar_color(LIMESTONE), true, 0.0, Color(LIMESTONE.r, LIMESTONE.g, LIMESTONE.b, 0.25))
		_masonry_rect(mb, corners, PL, eave, LIMESTONE, _openings(d, auto_doors, corners))
	elif style == "wood" or style == "boards":
		_plank_walls(mb, corners, d, auto_doors, style == "boards")
	else:
		# windrise stone and lakeside skirting are their own (proud) faces
		var wall_y0 := PL
		if style == "windrise":
			wall_y0 = PL + (FH if floors > 1 else 1.0) - 0.04
		elif style == "lakeside":
			wall_y0 = PL + 0.7
		if _jet > 0.0:
			var up := _at_storey(corners, _jet_y)
			_ring_walls(mb, corners, wall_y0, _jet_y, wcol, true)
			_ring_walls(mb, up, _jet_y, eave, wcol, true, _jet)
			# the jetty's underside between the two wall lines
			var soffit := _wood(Color(0.56, 0.42, 0.27, 0.5))
			for i in 4:
				var a0: Vector3 = corners[i]
				var b0: Vector3 = corners[(i + 1) % 4]
				var a1: Vector3 = up[i]
				var b1: Vector3 = up[(i + 1) % 4]
				var yv := Vector3.UP * _jet_y
				mb.quad_facing(a0 + yv, b0 + yv, b1 + yv, a1 + yv, Vector3.DOWN, soffit)
		else:
			_ring_walls(mb, corners, wall_y0, eave, wcol, true)
		if style == "plaster" and not _preview:
			# worn lime render: stone patches and stone string courses
			var bands: Array = []
			if d.get("bands", true):
				for f in range(1, floors):
					bands.append(PL + f * FH)
			_masonry_rect(mb, corners, PL, eave - 0.1, LIMESTONE, _openings(d, auto_doors, corners), true, bands)
	for i in 4:
		faces.append({"a": corners[(i + 1) % 4] + Vector3.UP * 0.0, "b": corners[i], "n": _side_normal(corners, i), "h": eave * 0.9})
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
	if floors > 1 and d.get("bands", true) and style != "timber" and style != "windrise" and style != "lakeside" and style != "wood" and style != "boards" and not (style == "plaster" and not _preview):
		for f in range(1, floors):
			var y := PL + f * FH
			_band(mb, corners, y, 0.14, 0.05, Color(wall_col.r * 0.9, wall_col.g * 0.88, wall_col.b * 0.85, 1.0))
	if not d.get("roof_only", false):
		_details_rect(mb, d, corners, style, floors, roof, L, W)
	# chimney
	var ch: float = d.get("chimney", NO_CHIMNEY)
	if ch > NO_CHIMNEY + 1.0:
		var cx := clampf(ch, -0.45, 0.45) * L
		var cz := W * 0.22
		var y_roof := eave + (roof_h * (1.0 - cz / (W * 0.5)) if roof != "flat" else 0.0)
		if d.get("ridge", false) and roof != "flat":
			cz = clampf(ch, -0.45, 0.45) * W
			cx = L * 0.22
			y_roof = eave + roof_h * (1.0 - cx / (L * 0.5))
		var sy := 1.0 + roof_h * 0.45
		_stone_chimney(mb, Vector3(cx, y_roof - 0.5, cz), 1.25 * sy)
		set_meta("smoke_at", Vector3(cx, y_roof - 0.5 + 1.25 * sy + 0.35, cz))
	elif has_meta("smoke_at"):
		remove_meta("smoke_at")
	_place_extras(deco, d, false)




func _rect_roof(mb: MeshBuilder, d: Dictionary, L: float, W: float, roof: String, pitch: float, roof_col: Color,
		wcol: Color, stone_col: Color, style: String) -> void:
	if d.get("ridge", false) and roof != "flat":
		# the roof turned a quarter: its ridge runs across the house
		var tmp := MeshBuilder.new()
		var first := perches.size()
		_rect_roof_inner(tmp, d, W, L, roof, pitch, roof_col, wcol, stone_col, style)
		var turn := Transform3D(Basis(Vector3.UP, PI * 0.5), Vector3.ZERO)
		mb.append(tmp, turn)
		for i in range(first, perches.size()):
			perches[i] = turn * perches[i]
		return
	_rect_roof_inner(mb, d, L, W, roof, pitch, roof_col, wcol, stone_col, style)


func _rect_roof_inner(mb: MeshBuilder, d: Dictionary, L: float, W: float, roof: String, pitch: float, roof_col: Color,
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


## A ring of wall faces; with `cut`, the planned openings (_cut, measured
## from each side's start corner, `s_off` further along for faces set proud
## of the corners) are left open and lined with reveals.
func _ring_walls(mb: MeshBuilder, corners: Array, y0: float, y1: float, col: Color, cut := false, s_off := 0.0,
		reveal := Color(0, 0, 0, -1)) -> void:
	var u := 0.0
	if cut and _cut.size() == corners.size():
		var rc := col if reveal.a < 0.0 else reveal
		for i in corners.size():
			var a: Vector3 = corners[i]
			var b: Vector3 = corners[(i + 1) % corners.size()]
			var l := a.distance_to(b)
			var holes: Array = []
			for hl in _cut[i]:
				var h2: Dictionary = hl.duplicate()
				h2.s += s_off
				holes.append(h2)
			WallCut.face(mb, WallCut.flat_at(a, b), WallCut.flat_nrm(_side_normal(corners, i)), 0.0, l, y0, y1, holes, col, rc, u)
			u += l
		return
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
	var beam := _wood(Color(0.56, 0.42, 0.27, 0.5))   # Tiny Glade timber, #8E6A44
	var t := 0.16
	for f in floors + 1:
		var y := PL + f * FH
		_band(mb, _at_storey(corners, y), y + (0.08 if f == 0 else 0.0), 0.16, 0.04, beam)
	# posts storey by storey (a jettied upper storey has its own wall line)
	var runs: Array = [[PL, eave, corners, 0.0]]
	if _jet > 0.0:
		runs = [[PL, _jet_y, corners, 0.0], [_jet_y, eave, _at_storey(corners, _jet_y), _jet]]
	for run in runs:
		var y0: float = run[0]
		var y1: float = run[1]
		var cs: Array = run[2]
		var off: float = run[3]
		for i in 4:
			var a: Vector3 = cs[i]
			var b: Vector3 = cs[(i + 1) % 4]
			var n := _side_normal(cs, i)
			var l := a.distance_to(b)
			var count := maxi(1, int(l / 1.3))
			for k in count + 1:
				var u := float(k) / count
				# openings bring their own posts (see _timber_surround)
				var skip := false
				for hl in (_cut[i] if _cut.size() == 4 else []):
					if absf(hl.s + off - u * l) < hl.w * 0.5 + 0.35 and hl.y < y1 and WallCut.top(hl) > y0:
						skip = true
				if skip and k != 0 and k != count:
					continue
				var p := a.lerp(b, u) + n * 0.04
				var h := y1 - y0
				mb.box(Transform3D(DecoMerge.facing(n), p + Vector3.UP * (y0 + h * 0.5)), Vector3(t, h, 0.08), beam)
	var up := _at_storey(corners, eave)
	for i in 4:
		var a: Vector3 = up[i]
		var b: Vector3 = up[(i + 1) % 4]
		var n := _side_normal(up, i)
		var l := a.distance_to(b)
		# diagonal braces on the upper storeys at both ends of each side
		for f in range(1, floors):
			var y0 := PL + f * FH
			for end in [0.0, 1.0]:
				var near := false
				for hl in (_cut[i] if _cut.size() == 4 else []):
					if absf(hl.s + _jet - end * l) < hl.w * 0.5 + 1.3 and hl.y > y0 - 0.5 and hl.y < y0 + FH:
						near = true
				if near:
					continue
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
	# round ridge tiles along the ridge
	if _preview:
		mb.box(Transform3D(Basis(Vector3.RIGHT, PI / 4), Vector3(0, yr + 0.02, 0)), Vector3(x1 - x0 + 0.08, 0.2, 0.2), fascia)
	else:
		Roofing.ridge(mb, Vector3(x0 - 0.02, yr + 0.03, 0), Vector3(x1 + 0.02, yr + 0.03, 0), tc, _rng, 0.13)


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
	if _preview:
		if rx > 0.01:
			mb.box(Transform3D(Basis(Vector3.RIGHT, PI / 4), Vector3(0, yr + 0.02, 0)), Vector3(rx * 2.0 + 0.1, 0.2, 0.2), fascia)
		return
	# round ridge tiles along the ridge and down the four hips
	if rx > 0.01:
		Roofing.ridge(mb, Vector3(-rx, yr + 0.03, 0), Vector3(rx, yr + 0.03, 0), tc, _rng, 0.13)
	for pair in [[e0, r0], [e3, r0], [e1, r1], [e2, r1]]:
		var e: Vector3 = pair[0]
		var r: Vector3 = pair[1]
		var steps := 1 if absf(curve) < 0.02 else 4
		for k in steps:
			var ta := float(k) / steps
			var tb := float(k + 1) / steps
			var pa := e.lerp(r, ta) + Vector3.UP * (_bow(ta, rh, curve, tw) + 0.03)
			var pb := e.lerp(r, tb) + Vector3.UP * (_bow(tb, rh, curve, tw) + 0.03)
			Roofing.ridge(mb, pa, pb, tc, _rng, 0.11)


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
		var count := maxi(1, int(l / 0.95)) if data.get("merlons", true) else 0
		var n := Vector3.UP.cross(ob - oa).normalized()
		for k in count:
			var u := (k + 0.5) / count
			var p := oa.lerp(ob, u) - n * 0.16 + Vector3.UP * (y + 0.22)
			mb.box(Transform3D(DecoMerge.facing(n), p), Vector3(0.48, 0.44, 0.32), col)


# ---------------------------------------------------------------------------
# Round towers
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Tiny Glade's small building details: dressed stone or timber surrounds
# round every opening, rafter ends and knee brackets under the eaves, beam
# ends under jettied storeys, and braces under half-timbered windows
# ---------------------------------------------------------------------------
const TIMBER := Color(0.56, 0.42, 0.27, 0.5)   # #8E6A44
const SURROUND_STONE := 0.2


## The wall line of the storey at height y: upper storeys of a jettied
## timber house stand out by _jet all round.
func _at_storey(corners: Array, y: float) -> Array:
	if _jet <= 0.0 or y < _jet_y - 0.01:
		return corners
	var out: Array = []
	for c in corners:
		var v: Vector3 = c
		out.append(v + Vector3(signf(v.x), 0, signf(v.z)) * _jet)
	return out


## A stone chimney stack from `at` up `h`: courses of rounded blocks, a
## capping slab and a dark pot.
func _stone_chimney(mb: MeshBuilder, at: Vector3, h: float) -> void:
	if _preview:
		mb.box(Transform3D(Basis.IDENTITY, at + Vector3.UP * h * 0.5), Vector3(0.62, h, 0.5), Color(LIMESTONE.r, LIMESTONE.g, LIMESTONE.b, 0.25))
		return
	var stone := Color(LIMESTONE.r, LIMESTONE.g, LIMESTONE.b, 0.25)
	mb.box(Transform3D(Basis.IDENTITY, at + Vector3.UP * h * 0.5), Vector3(0.54, h, 0.42), Masonry.mortar_color(LIMESTONE))
	var y := 0.0
	var k := 0
	while y < h - 0.05:
		var ch := minf(0.2 * _rng.randf_range(0.9, 1.1), h - y)
		var off := (0.035 if k % 2 == 0 else -0.035)
		# two blocks per course, joints alternating
		var split := 0.31 + off * 2.0
		for part in [[-0.31, split - 0.31], [split - 0.31, 0.31]]:
			var x0: float = part[0]
			var x1: float = part[1]
			var c := Masonry.stone_color(stone, _rng)
			mb.bevel_box(Transform3D(Basis(Vector3.UP, _rng.randf_range(-0.04, 0.04)), at + Vector3((x0 + x1) * 0.5, y + ch * 0.5, 0)),
					Vector3(x1 - x0 - 0.02, ch - 0.02, 0.5 + _rng.randf_range(-0.02, 0.02)), 0.04, c)
		y += ch
		k += 1
	mb.bevel_box(Transform3D(Basis.IDENTITY, at + Vector3.UP * (h + 0.05)), Vector3(0.78, 0.1, 0.66), 0.03, Masonry.stone_color(stone, _rng))
	mb.bevel_box(Transform3D(Basis.IDENTITY, at + Vector3.UP * (h + 0.2)), Vector3(0.3, 0.22, 0.28), 0.04, Color(0.43, 0.38, 0.35, 0.25))


## How wide a style's opening surrounds are (stonework keeps clear of them).
static func _surround_w(style: String) -> float:
	match style:
		"stone", "plaster", "windrise":
			return SURROUND_STONE
		"wood", "boards":
			return 0.13
	return 0.0


func _details_rect(mb: MeshBuilder, d: Dictionary, corners: Array, style: String, floors: int, roof: String, L: float, W: float) -> void:
	if _preview or floors <= 0:
		return
	var stone_top := PL + (FH if floors > 1 else 1.0)
	var beam := _wood(TIMBER)
	for i in 4:
		var a: Vector3 = corners[i]
		var b: Vector3 = corners[(i + 1) % 4]
		var n := _side_normal(corners, i)
		var at := WallCut.flat_at(a, b)
		var nrm := WallCut.flat_nrm(n)
		var l := a.distance_to(b)
		for hl0 in _cut[i]:
			var hl: Dictionary = hl0
			var at2 := at
			if _jet > 0.0 and hl.y >= _jet_y:
				# on the jettied storey's wall line
				var up := _at_storey(corners, _jet_y)
				at2 = WallCut.flat_at(up[i], up[(i + 1) % 4])
				hl = hl.duplicate()
				hl.s += _jet
			var kind := style
			if style == "windrise":
				kind = "stone" if hl.y < stone_top else "timber"
			match kind:
				"stone", "plaster":
					if hl.get("model", "") != "tg_door_gothic":
						_stone_surround(mb, at2, nrm, hl, LIMESTONE)
				"wood", "boards":
					_board_surround(mb, at2, nrm, hl, beam)
				"timber":
					_timber_surround(mb, at2, nrm, hl, beam, floors)
		# beam ends under the upper storeys of timber houses (a jettied look)
		if style in ["timber", "windrise", "wood", "boards"]:
			for f in range(1, floors):
				var y := PL + f * FH
				if style == "windrise" and y < stone_top + 0.1:
					continue
				_beam_ends(mb, at, n, l, y - 0.1, beam, _cut[i])
	# under the eaves: rafter ends and knee brackets on the eave sides
	if roof == "flat" or style == "lakeside":
		return
	var turned: bool = d.get("ridge", false)
	for i in 4:
		var eave_side := roof == "hip" or ((i % 2 == 0) != turned)
		if not eave_side:
			continue
		var top_cs := _at_storey(corners, eave)
		var a: Vector3 = top_cs[i]
		var b: Vector3 = top_cs[(i + 1) % 4]
		var n := _side_normal(corners, i)
		var l := a.distance_to(b)
		var dir := (b - a) / l
		var depth := (L if turned else W) * 0.5 + _jet
		var slope := roof_h / maxf(depth, 0.1)
		# rafter ends poking out under the overhang (windrise has its carved
		# brackets there instead)
		var count := maxi(2, int(l / 0.55)) if style != "windrise" else -1
		for k in count + 1:
			var s := l * k / count
			if roof == "hip" and (k == 0 or k == count):
				continue
			var p := a + dir * s
			var ang := atan(slope)
			var out := 0.34
			var c := p + n * (out * 0.5) + Vector3.UP * (eave - 0.09 - out * 0.5 * slope)
			mb.bevel_box(Transform3D(DecoMerge.facing(n) * Basis(Vector3.RIGHT, ang), c), Vector3(0.1, 0.1, out), 0.025, beam)
		# big knee brackets under the overhang, kept clear of windows and
		# doors, and left off the lowest buildings
		if eave - PL < 1.6 or style == "stone":
			continue
		var nb := maxi(1, int(round(l / 2.6)))
		for k in nb + 1:
			var s := lerpf(0.3, l - 0.3, float(k) / nb)
			var busy := false
			for hl in _cut[i]:
				if absf(hl.s + _jet - s) < hl.w * 0.5 + 0.35 and WallCut.top(hl) > eave - 1.0:
					busy = true
			if busy:
				continue
			_knee(mb, a + dir * s, n, eave - 0.24, slope, beam)


## Dressed stone round an opening: alternating long and short jamb blocks,
## a lintel over square heads, voussoirs round arches.
func _stone_surround(mb: MeshBuilder, at: Callable, nrm: Callable, hl: Dictionary, base: Color) -> void:
	var half: float = hl.w * 0.5
	var spring: float = hl.y + hl.h
	var y := float(hl.y)
	var k := 0
	var stone := Color(base.r, base.g, base.b, 0.25)
	while y < spring - 0.05:
		var h := minf(0.3 if k % 2 == 0 else 0.24, spring - y)
		if spring - (y + h) < 0.12:
			h = spring - y
		var wj := SURROUND_STONE if k % 2 == 0 else SURROUND_STONE * 0.65
		for sgn in [-1.0, 1.0]:
			var s0: float = hl.s + sgn * half
			var s1: float = s0 + sgn * wj
			_block(mb, at, nrm, minf(s0, s1), maxf(s0, s1), y + 0.012, y + h - 0.012, 0.07, Masonry.stone_color(stone, _rng))
		y += h
		k += 1
	# heads stay under the eaves
	var room := eave - 0.08 - WallCut.top(hl)
	if room < 0.08:
		return
	if int(hl.arch) == WallCut.FLAT:
		_block(mb, at, nrm, hl.s - half - SURROUND_STONE * 0.8, hl.s + half + SURROUND_STONE * 0.8, spring + 0.012, spring + minf(0.22, room), 0.08,
				Masonry.stone_color(stone, _rng))
		return
	# voussoirs following the arch, a little keystone at the top
	var n_v := 7 if hl.w < 1.2 else 9
	for i in n_v:
		var x0: float = -half + hl.w * i / n_v + 0.012
		var x1: float = -half + hl.w * (i + 1) / n_v - 0.012
		var key := i == n_v / 2
		var r := minf(SURROUND_STONE * (1.15 if key else 0.9), room)
		_arch_block(mb, at, nrm, hl, x0, x1, r, 0.08 if key else 0.07, Masonry.stone_color(stone, _rng))


## Plank frame boards cut round an opening in a board wall.
func _board_surround(mb: MeshBuilder, at: Callable, nrm: Callable, hl: Dictionary, col: Color) -> void:
	var half: float = hl.w * 0.5
	var spring: float = hl.y + hl.h
	var t := 0.12
	for sgn in [-1.0, 1.0]:
		var s0: float = hl.s + sgn * half
		_block(mb, at, nrm, minf(s0, s0 + sgn * t), maxf(s0, s0 + sgn * t), hl.y - (0.0 if hl.get("nosill", false) else 0.1), spring, 0.06, col)
	var room := eave - 0.08 - WallCut.top(hl)
	if room < 0.06:
		return
	if int(hl.arch) == WallCut.FLAT:
		_block(mb, at, nrm, hl.s - half - t - 0.06, hl.s + half + t + 0.06, spring, spring + minf(0.14, room), 0.07, col)
	else:
		var n_v := 6
		for i in n_v:
			_arch_block(mb, at, nrm, hl, -half + hl.w * i / n_v, -half + hl.w * (i + 1) / n_v, minf(t, room), 0.06, col)


## Half-timbering round an opening: posts each side, a lintel over it and,
## under a window, a sill rail with a St Andrew's cross below.
func _timber_surround(mb: MeshBuilder, at: Callable, nrm: Callable, hl: Dictionary, col: Color, _floors: int) -> void:
	var half: float = hl.w * 0.5
	var top := WallCut.top(hl)
	var f := floori((float(hl.y) - PL) / FH)
	var floor_y := PL + f * FH + 0.16
	var t := 0.14
	for sgn in [-1.0, 1.0]:
		var s0: float = hl.s + sgn * half
		_block(mb, at, nrm, minf(s0, s0 + sgn * t), maxf(s0, s0 + sgn * t), floor_y, minf(top + 0.16, eave - 0.08), 0.06, col)
	if eave - 0.08 - top > 0.06:
		_block(mb, at, nrm, hl.s - half - t, hl.s + half + t, top, minf(top + 0.15, eave - 0.08), 0.065, col)
	if hl.get("nosill", false):
		return
	var sill: float = hl.y - 0.02
	_block(mb, at, nrm, hl.s - half - t, hl.s + half + t, sill - 0.14, sill, 0.065, col)
	var lo := floor_y
	var hi := sill - 0.14
	if hi - lo < 0.35:
		return
	# the cross under the window
	var p0: Vector3 = at.call(hl.s - half, lo)
	var p1: Vector3 = at.call(hl.s + half, hi)
	var p2: Vector3 = at.call(hl.s + half, lo)
	var p3: Vector3 = at.call(hl.s - half, hi)
	var n: Vector3 = nrm.call(hl.s)
	for pair in [[p0, p1], [p2, p3]]:
		var u: Vector3 = pair[0]
		var v: Vector3 = pair[1]
		var d3 := v - u
		var mid := (u + v) * 0.5 + n * 0.03
		var x := d3.normalized()
		var basis := Basis(x, n.cross(x).normalized(), n)
		mb.bevel_box(Transform3D(basis, mid), Vector3(d3.length() + 0.04, 0.11, 0.06), 0.02, col)


## A rectangle of the face from s0..s1, y0..y1 raised `d` proud of it.
func _block(mb: MeshBuilder, at: Callable, nrm: Callable, s0: float, s1: float, y0: float, y1: float, d: float, col: Color) -> void:
	var a: Vector3 = at.call(s0, y0)
	var b: Vector3 = at.call(s1, y1)
	var n: Vector3 = nrm.call((s0 + s1) * 0.5)
	var mid := (a + b) * 0.5 + n * d * 0.5
	var along := (Vector3(b.x, 0, b.z) - Vector3(a.x, 0, a.z)).length()
	mb.bevel_box(Transform3D(DecoMerge.facing(n), mid), Vector3(along, y1 - y0, d), minf(0.03, d * 0.4), col)


## One voussoir: the band between the arch and `r` beyond it, over x0..x1
## (offsets from the opening's centre), raised `d` proud of the face.
func _arch_block(mb: MeshBuilder, at: Callable, nrm: Callable, hl: Dictionary, x0: float, x1: float, r: float, d: float, col: Color) -> void:
	var half: float = hl.w * 0.5
	var pts_in: Array[Vector2] = []
	var pts_out: Array[Vector2] = []
	var centre := Vector2(hl.s, float(hl.y) + float(hl.h))
	for x in [x0, x1]:
		var p := Vector2(hl.s + x, WallCut.head(hl, clampf(x, -half, half)))
		var o := (p - centre)
		if int(hl.arch) == WallCut.POINTED:
			var c := half * WallCut.K_C * (-1.0 if x >= 0.0 else 1.0)
			o = p - Vector2(hl.s + c, centre.y)
		o = o.normalized() if o.length() > 0.001 else Vector2.UP
		pts_in.append(p)
		pts_out.append(p + o * r)
	var n: Vector3 = nrm.call(hl.s)
	var q := [at.call(pts_in[0].x, pts_in[0].y), at.call(pts_in[1].x, pts_in[1].y), at.call(pts_out[1].x, pts_out[1].y), at.call(pts_out[0].x, pts_out[0].y)]
	var fr := n * d
	mb.quad_facing(q[0] + fr, q[1] + fr, q[2] + fr, q[3] + fr, n, col)
	for e in 4:
		var u: Vector3 = q[e]
		var v: Vector3 = q[(e + 1) % 4]
		var mid := (u + v) * 0.5
		var ctr: Vector3 = (q[0] + q[1] + q[2] + q[3]) * 0.25
		var side := (mid - ctr)
		side = (side - n * side.dot(n)).normalized()
		mb.quad_facing(u, v, v + fr, u + fr, side, col)


## A row of beam ends sticking out of the wall at height y.
func _beam_ends(mb: MeshBuilder, at: Callable, n: Vector3, l: float, y: float, col: Color, holes: Array) -> void:
	var count := maxi(2, int(l / 0.5))
	for k in range(1, count):
		var s := l * k / count
		var clear := true
		for hl in holes:
			if absf(hl.s - s) < hl.w * 0.5 + 0.12 and y > hl.y - 0.2 and y < WallCut.top(hl) + 0.2:
				clear = false
		if not clear:
			continue
		var p: Vector3 = at.call(s, y)
		mb.bevel_box(Transform3D(DecoMerge.facing(n), p + n * 0.13), Vector3(0.13, 0.13, 0.26), 0.03, col)


## A knee bracket under the eaves: a short post on the wall and a brace up
## to the rafters.
func _knee(mb: MeshBuilder, p: Vector3, n: Vector3, top: float, slope: float, col: Color) -> void:
	var post_h := 0.62
	mb.bevel_box(Transform3D(DecoMerge.facing(n), p + n * 0.06 + Vector3.UP * (top - post_h * 0.5)), Vector3(0.13, post_h, 0.12), 0.03, col)
	var lo := p + n * 0.08 + Vector3.UP * (top - post_h + 0.08)
	var hi := p + n * 0.36 + Vector3.UP * (top - 0.36 * slope - 0.04)
	var d3 := hi - lo
	var z := d3.normalized()
	var x := n.cross(Vector3.UP).normalized()
	var basis := Basis(x, z.cross(x).normalized(), z)
	mb.bevel_box(Transform3D(basis, (lo + hi) * 0.5), Vector3(0.11, 0.11, d3.length() + 0.06), 0.03, col)
	mb.bevel_box(Transform3D(DecoMerge.facing(n), p + n * 0.22 + Vector3.UP * (top - 0.04 - 0.22 * slope)), Vector3(0.14, 0.12, 0.44), 0.03, col)


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
	# openings first, so the walls can be laid round them
	_cut = []
	_clear = []
	for door in auto_doors:
		if door.get("arch", false):
			var an := Vector3(cos(door.u * TAU), 0, sin(door.u * TAU))
			_place_arch(deco, an * (R + 0.02), an, door)
			var aw: float = clampf(float(door.get("aw", 2.0)), 1.4, 5.0)
			var sa := fposmod(door.u, 1.0) * TAU * R
			for k in [-1.0, 0.0, 1.0]:
				_clear.append(Rect2(sa + k * TAU * R - aw * 0.5 - 0.35, -2.0, aw + 0.7, arch_height(aw) + 2.3))
		else:
			_place_round_opening(deco, R, door.u, 0, "door", rng)
	var boxes := rng.randf() < 0.4
	for w in d.get("windows", []):
		if w.get("kind", "") == "trapdoor":
			if roof == "flat":
				var tp := Vector2(float(w.get("x", 0.0)), float(w.get("z", 0.0))).limit_length(maxf(0.0, R - 0.7))
				deco.add("trapdoor", Transform3D(Basis.IDENTITY, Vector3(tp.x, eave + 0.02, tp.y)))
			continue
		var f: int = w.f
		if f >= floors:
			continue
		var kind: String = w.get("kind", "window")
		var skip := false
		for door in auto_doors:
			if f == 0 and absf(angle_difference(door.u * TAU, w.u * TAU)) * R < 1.0:
				skip = true
		if not skip:
			_place_round_opening(deco, R, w.u, f, kind, rng, boxes, w)
	if style == "windrise":
		_round_windrise(mb, R, floors, segs, d, auto_doors)
	var foot := -1.6 if lift < 0.05 else 0.0
	if _preview:
		_cylinder(mb, R + 0.1, foot, PL, segs, stone_col)
	else:
		_cylinder(mb, R + 0.1, foot, PL, segs, Masonry.mortar_color(LIMESTONE))
		_masonry_round(mb, R + 0.1, maxf(foot, -0.35), PL, LIMESTONE.darkened(0.06), [])
	if lift >= 0.05:
		_stilts_round(mb, R, segs)
	if style == "stone" and not _preview:
		_tower_wall(mb, R, R, PL, eave, segs, Masonry.mortar_color(LIMESTONE), Color(LIMESTONE.r, LIMESTONE.g, LIMESTONE.b, 0.25))
		_masonry_round(mb, R, PL, eave, LIMESTONE, _round_openings(d, auto_doors, R))
	elif style == "wood" or style == "boards":
		# timber tower on a stone footing, boards with battens
		var tone := _wood(Color(0.66, 0.48, 0.29))
		var footing := PL + 0.75
		_tower_wall(mb, R, R, PL, footing, segs, Masonry.mortar_color(LIMESTONE) if not _preview else stone_col, stone_col)
		if not _preview:
			_masonry_round(mb, R, PL, footing, LIMESTONE.darkened(0.03), _round_openings(d, auto_doors, R))
		_tower_wall(mb, R, R, footing, eave, segs, Color(tone.r, tone.g, tone.b, 0.5))
		if not _preview:
			var holes := _round_openings(d, auto_doors, R)
			var nb := int(TAU * R / 0.34)
			for k in nb:
				var sa := TAU * R * k / nb
				var clear := true
				for hole in holes:
					var r: Rect2 = hole
					if sa > r.position.x and sa < r.end.x:
						clear = false
				if not clear:
					continue
				var a := sa / R
				var nn := Vector3(cos(a), 0, sin(a))
				var c := tone.darkened(0.12 + 0.06 * sin(sa * 7.0))
				mb.box(Transform3D(DecoMerge.facing(nn), nn * (R + 0.025) + Vector3.UP * (footing + eave) * 0.5), Vector3(0.07, eave - footing, 0.05), Color(c.r, c.g, c.b, 0.5))
	else:
		# windrise stone is its own (proud) face
		var wall_y0 := PL + (FH if floors > 1 else 1.0) - 0.04 if style == "windrise" else PL
		_tower_wall(mb, R, R, wall_y0, eave, segs, wcol)
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
	_place_extras(deco, d, true)


func _round_roof(mb: MeshBuilder, deco: DecoMerge, R: float, roof: String, pitch: float, roof_col: Color,
		stone_col: Color, segs: int) -> void:
	roof_h = 0.0
	if roof == "flat":
		_cylinder(mb, R + 0.18, eave - 0.3, eave + 0.55, segs, stone_col)
		_disc(mb, R + 0.18, eave - 0.3, segs, stone_col, true)
		_disc(mb, R - 0.05, eave, segs, Color(0.62, 0.58, 0.52, 0.5), false)
		var count := maxi(6, int(TAU * R / 0.95)) if data.get("merlons", true) else 0
		for k in count:
			var a := TAU * (k + 0.5) / count
			var n := Vector3(cos(a), 0, sin(a))
			mb.box(Transform3D(DecoMerge.facing(n), n * (R + 0.02) + Vector3.UP * (eave + 0.77)), Vector3(0.46, 0.44, 0.34), stone_col)
		# inner parapet face & top rim
		_cylinder_inner(mb, R - 0.12, eave, eave + 0.55, segs, stone_col)
		_annulus(mb, R - 0.12, R + 0.18, eave + 0.55, segs, Color(stone_col.r, stone_col.g, stone_col.b, 1.0))
		if not _has_top_flag():
			deco.add("banner", Transform3D(Basis.IDENTITY, Vector3(0, eave, 0)))
		perches.append(Vector3(R * 0.7, eave + 1.0, 0))
	elif absf(float(data.get("curve", 0.0))) > 0.05:
		_curved_round_roof(mb, deco, R, pitch, roof_col, segs, float(data.get("curve", 0.0)))
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
		if not _has_top_flag():
			deco.add("weathervane", Transform3D(Basis.IDENTITY, apex + Vector3.DOWN * 0.1))
		perches.append(apex + Vector3.UP * 0.9)


func _place_round_opening(deco: DecoMerge, R: float, u: float, f: int, kind: String, _rng_unused: RandomNumberGenerator, boxes := false, w: Dictionary = {}) -> void:
	var a := u * TAU
	var n := Vector3(cos(a), 0, sin(a))
	var p := n * R
	var s := fposmod(u, 1.0) * TAU * R
	var style: String = data.get("style", "stone")
	var cut: Array = []
	var clear: Array = []
	if kind == "door":
		var half := _door_into(deco, p, n, s, style, 1.0, cut, clear)
		deco.add("stair_step", Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(1.2, 1.0, 1.4)), n * (R + 0.25) + Vector3.UP * 0.0))
		_door_steps(deco, n * (R + 0.1), n, 1.2)
		var side := n.cross(Vector3.UP).normalized()
		deco.add("wall_lantern", Transform3D(Basis.looking_at(n, Vector3.UP), p + side * (half + 0.3) + Vector3.UP * (PL + 2.0)))
		lamps.append(p + side * (half + 0.3) + Vector3.UP * (PL + 1.9) + n * 0.3)
	else:
		var wt: String = w.get("wt", "plain")
		var model := _window_model(wt, style)
		if model == "":
			var pc := n * (R - 0.02) + Vector3.UP * (PL + f * FH + 1.35)
			clear.append(_window_hole(wt, s, pc.y))
			_fancy_window(deco, wt, Transform3D(DecoMerge.facing(n), pc))
		else:
			var hgt := WallCut.model_height(model)
			var y := minf(PL + f * FH + 0.75, eave - 0.12 - hgt)
			# windrise stone is set 4 cm proud
			if style == "windrise" and f == 0 and data.get("floors", 1) > 1:
				p += n * 0.04
			var xf := Transform3D(DecoMerge.facing(n), p + Vector3.UP * y)
			_tg(deco, model, xf)
			var hl := WallCut.hole_for(model, s, y)
			cut.append(hl)
			clear.append(WallCut.rect(hl, 0.05))
			var trim := int(w.get("deco", -1))
			var txf := Transform3D(xf.basis * Basis.from_scale(Vector3(hl.w / 0.96, 1, 1)), xf.origin)
			if trim < 0:
				if boxes and f == 0:
					_tg(deco, "tg_flower_box", txf)
			else:
				_window_trim(deco, trim, txf, xf.origin + Vector3.UP * hgt * 0.55, n, true)
	# round the back of the tower too, where the openings wrap past s = 0
	var circ := TAU * R
	for hl in cut:
		for k in [-1.0, 0.0, 1.0]:
			var h2: Dictionary = hl.duplicate()
			h2.s += k * circ
			_cut.append(h2)
	for r in clear:
		for k in [-1.0, 0.0, 1.0]:
			_clear.append(Rect2((r as Rect2).position + Vector2(k * circ, 0), (r as Rect2).size))


## A few bushes hugging the foot of the walls (not in front of doors), and
## a bird nest tucked in where this house's roof meets a joined one.
func _greenery(deco: DecoMerge, d: Dictionary, auto_doors: Array) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = int(d.get("seed", 1)) * 13 + 3
	if lift < 0.05:
		var round_b: bool = d.shape == "round"
		var count := rng.randi_range(1, 3)
		for i in count:
			var side := rng.randi() % 4
			var u := rng.randf_range(0.12, 0.88)
			var blocked := false
			for door in auto_doors + d.get("windows", []).filter(func(w): return w.get("kind", "") == "door"):
				if int(door.side) == side and absf(float(door.u) - u) < 0.25:
					blocked = true
			if blocked or (not round_b and _in_join(_side_point([Vector3(-d.size.x / 2, 0, -d.size.y / 2), Vector3(d.size.x / 2, 0, -d.size.y / 2),
					Vector3(d.size.x / 2, 0, d.size.y / 2), Vector3(-d.size.x / 2, 0, d.size.y / 2)], side, u))):
				continue
			var spot := _wall_spot(0 if round_b else side, u, 0.0)
			var sc := rng.randf_range(0.45, 0.7)
			deco.add("bush_a" if rng.randf() < 0.6 else "bush_berries",
					Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * sc), spot[0] + spot[1] * 0.35 + Vector3.DOWN * 0.05))
	if d.shape != "round" and d.get("roof", "gable") != "flat" and not joins.is_empty() and rng.randf() < 0.7:
		var poly: PackedVector2Array = joins[0]
		var cen := Vector2.ZERO
		for q in poly:
			cen += q
		cen /= poly.size()
		var L: float = d.size.x
		var W: float = d.size.y
		var q2 := Vector2(clampf(cen.x, -L / 2, L / 2), clampf(cen.y, -W / 2, W / 2))
		if absf(q2.x) < L / 2 - 0.01 and absf(q2.y) < W / 2 - 0.01:
			q2 = Vector2(q2.x, signf(q2.y) * W / 2) if absf(q2.y) / W > absf(q2.x) / L else Vector2(signf(q2.x) * L / 2, q2.y)
		deco.add_mesh(Ornaments.nest(), Transform3D(Basis(Vector3.UP, rng.randf() * TAU), Vector3(q2.x * 0.92, eave - 0.06, q2.y * 0.92)))


## Height of an archway `w` wide that fits under the eaves.
func arch_height(w: float) -> float:
	var span := w if w <= 2.8 else (w - 0.5) * 0.5
	return clampf(maxf(2.3, span * 0.5 + 1.6), 1.6, eave - 0.35)


## An archway where a wide path enters (or a tunnel where it runs right
## through); a water gate when the passage floor is under water.
func _place_arch(deco: DecoMerge, p: Vector3, n: Vector3, door: Dictionary) -> void:
	var w: float = clampf(float(door.get("aw", 2.0)), 1.4, 5.0)
	deco.add_mesh(Ornaments.portal(snappedf(w, 0.1), snappedf(arch_height(w), 0.1), door.get("grate", false)),
			Transform3D(DecoMerge.facing(n), Vector3(p.x, -lift, p.z)))
	var side := n.cross(Vector3.UP).normalized()
	deco.add("wall_lantern", Transform3D(Basis.looking_at(n, Vector3.UP), p + side * (w * 0.5 + 0.55) + Vector3.UP * 2.0))
	lamps.append(p + side * (w * 0.5 + 0.55) + Vector3.UP * 1.9 + n * 0.3)


## A flight of steps from a raised house's door down to the ground.
func _door_steps(deco: DecoMerge, p: Vector3, n: Vector3, width: float) -> void:
	if lift < 0.3:
		return
	var count := int(ceil(lift / 0.21))
	var rise := lift / count
	for i in count:
		var at := p + n * (0.62 + 0.36 * i) + Vector3.DOWN * (rise * (i + 1))
		deco.add("stair_step", Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(width, rise / 0.22, 1.0)), at))


## Stone pillars under a raised house (a passage or a sheep shelter below),
## with timber brackets under the floor.
func _stilts_rect(mb: MeshBuilder, deco: DecoMerge, L: float, W: float) -> void:
	var under := Color(0.46, 0.38, 0.30, 0.5)
	# underside of the floor
	mb.quad_facing(Vector3(-L / 2 - 0.08, 0.0, -W / 2 - 0.08), Vector3(L / 2 + 0.08, 0.0, -W / 2 - 0.08),
			Vector3(L / 2 + 0.08, 0.0, W / 2 + 0.08), Vector3(-L / 2 - 0.08, 0.0, W / 2 + 0.08), Vector3.DOWN, under)
	var nx := maxi(2, int(ceil(L / 3.2)) + 1)
	var nz := maxi(2, int(ceil(W / 3.2)) + 1)
	var spots: Array = []
	for i in nx:
		var x := lerpf(-L / 2 + 0.3, L / 2 - 0.3, float(i) / (nx - 1))
		spots.append(Vector2(x, -W / 2 + 0.3))
		spots.append(Vector2(x, W / 2 - 0.3))
	for j in range(1, nz - 1):
		var z := lerpf(-W / 2 + 0.3, W / 2 - 0.3, float(j) / (nz - 1))
		spots.append(Vector2(-L / 2 + 0.3, z))
		spots.append(Vector2(L / 2 - 0.3, z))
	for sp in spots:
		_pillar(mb, Vector3(sp.x, 0, sp.y))
	# joists along the length
	for j in nz:
		var z2 := lerpf(-W / 2 + 0.3, W / 2 - 0.3, float(j) / maxf(1, nz - 1))
		mb.box(Transform3D(Basis.IDENTITY, Vector3(0, -0.12, z2)), Vector3(L, 0.22, 0.2), under)


func _stilts_round(mb: MeshBuilder, R: float, segs: int) -> void:
	var under := Color(0.46, 0.38, 0.30, 0.5)
	_disc(mb, R + 0.1, 0.0, segs, under, true)
	var count := maxi(4, int(TAU * R / 2.4))
	for k in count:
		var a := TAU * (k + 0.5) / count
		_pillar(mb, Vector3(cos(a), 0, sin(a)) * (R - 0.25))


## One square stone pillar from the ground up to the floor (y = 0).
func _pillar(mb: MeshBuilder, at: Vector3) -> void:
	var h := lift + 1.6   # reaches into the ground on slopes
	var col := Color(LIMESTONE.r * 0.95, LIMESTONE.g * 0.95, LIMESTONE.b * 0.95, 0.25)
	mb.bevel_box(Transform3D(Basis.IDENTITY, at + Vector3.DOWN * (h * 0.5)), Vector3(0.5, h, 0.5), 0.04, col)
	mb.bevel_box(Transform3D(Basis.IDENTITY, at + Vector3.DOWN * 0.12), Vector3(0.66, 0.24, 0.66), 0.04, col)


## Timber plank walls on a stone footing: horizontal weatherboards, or
## vertical boards and battens.
func _plank_walls(mb: MeshBuilder, corners: Array, d: Dictionary, auto_doors: Array, vertical: bool) -> void:
	var wood_c: Color = d.get("wall_col", Catalog.WALL_COLORS[0])
	# wall colours are pale limewash; timber takes a warm tone of it
	var tone := _wood(Color(0.66, 0.48, 0.29)).lerp(Color(wood_c.r * 0.62, wood_c.g * 0.5, wood_c.b * 0.4), 0.35)
	var footing := PL + 0.75
	if _preview:
		_ring_walls(mb, corners, PL, footing, Color(0.78, 0.74, 0.68, 0.25), true)
	else:
		_ring_walls(mb, corners, PL, footing, Masonry.mortar_color(LIMESTONE), true, 0.0, Color(LIMESTONE.r, LIMESTONE.g, LIMESTONE.b, 0.25))
		_masonry_rect(mb, corners, PL, footing, LIMESTONE.darkened(0.03), _openings(d, auto_doors, corners))
	_ring_walls(mb, corners, footing, eave, Color(tone.r, tone.g, tone.b, 0.5), true)
	if _preview:
		return
	var holes := _openings(d, auto_doors, corners)
	for i in 4:
		var a: Vector3 = corners[i]
		var b: Vector3 = corners[(i + 1) % 4]
		var n := _side_normal(corners, i)
		var dir := (b - a).normalized()
		var l := a.distance_to(b)
		var side_holes: Array = holes[i]
		if vertical:
			# battens over the board joints
			var k := 0.0
			while k < l - 0.05:
				var s0 := k + 0.32
				k = s0
				if s0 > l - 0.1:
					break
				var y_a := footing
				for hole in side_holes:
					var r: Rect2 = hole
					if s0 > r.position.x and s0 < r.end.x:
						y_a = -1.0
				if y_a < 0.0:
					continue
				var c := tone.darkened(0.12 + 0.06 * sin(s0 * 7.0))
				mb.box(Transform3D(DecoMerge.facing(n), a + dir * s0 + Vector3.UP * (footing + eave) * 0.5 + n * 0.025),
						Vector3(0.07, eave - footing, 0.05), Color(c.r, c.g, c.b, 0.5))
		else:
			# overlapping weatherboards: each course a slightly proud strip
			var y := footing
			var row := 0
			while y < eave - 0.05:
				var y1 := minf(y + 0.24, eave)
				var shade := 0.94 + 0.08 * float((row * 7) % 3) / 2.0
				var c2 := Color(tone.r * shade, tone.g * shade, tone.b * shade, 0.5)
				var segs := _free_runs(side_holes, l, y, y1)
				for run in segs:
					var s_a: float = run.x
					var s_b: float = run.y
					var p0 := a + dir * s_a
					var p1 := a + dir * s_b
					var lip := n * 0.035
					mb.quad_facing(p0 + Vector3.UP * y + lip, p1 + Vector3.UP * y + lip, p1 + Vector3.UP * y1 + n * 0.012, p0 + Vector3.UP * y1 + n * 0.012, n, c2)
					mb.quad_facing(p0 + Vector3.UP * y, p1 + Vector3.UP * y, p1 + Vector3.UP * y + lip, p0 + Vector3.UP * y + lip, Vector3.DOWN, c2.darkened(0.25))
				y = y1
				row += 1
	# corner posts
	for i in 4:
		var cp: Vector3 = corners[i]
		var out := (cp * Vector3(1, 0, 1)).normalized() * 0.04
		mb.box(Transform3D(Basis.IDENTITY, cp + out + Vector3.UP * (footing + eave) * 0.5), Vector3(0.16, eave - footing, 0.16), Color(tone.r * 0.7, tone.g * 0.7, tone.b * 0.7, 0.5))


## Pieces of [0, l] at height y0..y1 not covered by any opening rectangle.
static func _free_runs(holes: Array, l: float, y0: float, y1: float) -> Array:
	var cuts: Array = []
	for h in holes:
		var r: Rect2 = h
		if r.position.y < y1 and r.end.y > y0:
			cuts.append(Vector2(r.position.x, r.end.x))
	cuts.sort_custom(func(p, q): return p.x < q.x)
	var out: Array = []
	var s := 0.0
	for c in cuts:
		if c.x > s + 0.02:
			out.append(Vector2(s, minf(c.x, l)))
		s = maxf(s, c.y)
	if s < l - 0.02:
		out.append(Vector2(s, l))
	return out


## A cone roof bent into a dome (curve > 0) or swept up into a flared
## spire (curve < 0), in tiled rings.
func _curved_round_roof(mb: MeshBuilder, deco: DecoMerge, R: float, pitch: float, roof_col: Color, segs: int, curve: float) -> void:
	roof_h = R * (2.1 * pitch if curve < 0.0 else lerpf(2.1 * pitch, 1.0 + pitch * 0.4, curve))
	var ov := 0.35
	var rr := R + ov
	var ye := eave - 0.15
	var rings := 12
	var rsegs := segs + 4
	var tile := Color(roof_col.r, roof_col.g, roof_col.b, 0.75)
	var prof: Array = []
	for i in rings + 1:
		var t := float(i) / rings
		var lin := 1.0 - t
		var r: float
		if curve > 0.0:
			r = lerpf(lin, sqrt(maxf(0.0, 1.0 - t * t)), curve)
		else:
			r = lerpf(lin, pow(1.0 - t, 2.4), -curve)
		prof.append(Vector2(rr * r, ye + roof_h * t))
	for i in rings:
		var p0: Vector2 = prof[i]
		var p1: Vector2 = prof[i + 1]
		var slope := Vector2(p1.x - p0.x, p1.y - p0.y)
		var nrm2 := Vector2(slope.y, -slope.x).normalized()
		if nrm2.x < 0.0:
			nrm2 = -nrm2
		var shade := 0.94 + 0.06 * float(i % 2)
		var c := Color(tile.r * shade, tile.g * shade, tile.b * shade, 0.75)
		for k in rsegs:
			var a0 := TAU * k / rsegs
			var a1 := TAU * (k + 1) / rsegs
			var d0 := Vector3(cos(a0), 0, sin(a0))
			var d1 := Vector3(cos(a1), 0, sin(a1))
			var n0 := (d0 * nrm2.x + Vector3.UP * nrm2.y).normalized()
			var n1 := (d1 * nrm2.x + Vector3.UP * nrm2.y).normalized()
			mb.quad_facing(d0 * p0.x + Vector3.UP * p0.y, d1 * p0.x + Vector3.UP * p0.y, d1 * p1.x + Vector3.UP * p1.y, d0 * p1.x + Vector3.UP * p1.y,
					((n0 + n1) * 0.5).normalized(), c, n0, n1, n1, n0,
					Vector2(-a0 * p0.x, p0.y), Vector2(-a1 * p0.x, p0.y), Vector2(-a1 * p1.x, p1.y), Vector2(-a0 * p1.x, p1.y))
	# eave underside
	_annulus(mb, R - 0.05, rr, ye - 0.01, rsegs, Color(0.42, 0.30, 0.22, 0.5))
	var apex := Vector3(0, ye + roof_h, 0)
	if not _has_top_flag():
		deco.add("weathervane", Transform3D(Basis.IDENTITY, apex + Vector3.DOWN * 0.1))
	perches.append(apex + Vector3.UP * 0.9)


## Arched, round and arrow-slit windows (Ornaments) with glowing glass.
func _fancy_window(deco: DecoMerge, wt: String, xf: Transform3D) -> void:
	var m := Ornaments.window(wt)
	deco.add_mesh(m.solid, xf)
	deco.add_glow_mesh(m.glow, xf)


## The decoration a plain window was given (tap it again to change):
## 0 none, 1 flower box, 2 clothesline bracket, 3 shutters.
func _window_trim(deco: DecoMerge, trim: int, xf: Transform3D, p: Vector3, n: Vector3, single: bool) -> void:
	match trim:
		1:
			_tg(deco, "tg_flower_box", xf)
		2:
			# an iron arm over the window that a washing line is tied to
			var arm := p + Vector3.UP * 0.98 + n * 0.22
			var mb := MeshBuilder.new()
			mb.box(Transform3D(DecoMerge.facing(n), Vector3.ZERO), Vector3(0.04, 0.04, 0.46), Ornaments.IRON)
			Ornaments._layer(mb, 0, Ornaments.M_METAL)
			deco.add_mesh(mb.commit(), Transform3D(Basis.IDENTITY, arm))
			line_anchors.append([arm + n * 0.22, n])
		3:
			if single:
				_tg(deco, "tg_shutters", xf)


## Point and outward normal on the wall at (side, u) and height y (local).
func _wall_spot(side: int, u: float, y: float) -> Array:
	if data.shape == "round":
		var R: float = data.r
		var n := Vector3(cos(u * TAU), 0, sin(u * TAU))
		return [n * R + Vector3.UP * y, n]
	var L: float = data.size.x
	var W: float = data.size.y
	var corners := [Vector3(-L / 2, 0, -W / 2), Vector3(L / 2, 0, -W / 2), Vector3(L / 2, 0, W / 2), Vector3(-L / 2, 0, W / 2)]
	var a: Vector3 = corners[side % 4]
	var b: Vector3 = corners[(side + 1) % 4]
	return [a.lerp(b, clampf(u, 0.05, 0.95)) + Vector3.UP * y, _side_normal(corners, side % 4)]


func _has_top_flag() -> bool:
	for fl in data.get("flags", []):
		if fl.get("at", "") == "top":
			return true
	return false


## Flags flying from the roof, banners hanging from the walls and lanterns
## the player put up with the Details tool.
func _place_extras(deco: DecoMerge, d: Dictionary, round_b: bool) -> void:
	for fl in d.get("flags", []):
		var pat := int(fl.get("pat", 0))
		if fl.get("at", "") == "top":
			var top := Vector3(0, eave, 0)
			var roof: String = d.get("roof", "gable" if not round_b else "cone")
			if round_b:
				top.y = eave + (roof_h - 0.15 if roof != "flat" else 0.0)
			else:
				var L: float = d.size.x
				var W: float = d.size.y
				var x := (float(fl.get("u", 0.5)) - 0.5) * L
				if roof == "flat":
					top = Vector3(clampf(x, -L / 2 + 0.5, L / 2 - 0.5), eave, clampf(float(fl.get("z", 0.0)), -W / 2 + 0.5, W / 2 - 0.5))
				else:
					var ridge := maxf(0.0, L / 2 - W / 2 * 0.95) if roof == "hip" else L / 2 - 0.2
					top = Vector3(clampf(x, -ridge, ridge), eave + roof_h - 0.12, 0)
			deco.add_mesh(Ornaments.flag(pat), Transform3D(Basis(Vector3.UP, float(fl.get("r", 0.6))), top))
			if d.get("links", true):
				flag_anchors.append(top + Vector3.UP * 2.0)
			perches.append(top + Vector3.UP * 2.25)
		else:
			var spot := _wall_spot(int(fl.get("side", 0)), float(fl.get("u", 0.5)), float(fl.get("y", 3.0)))
			var p: Vector3 = spot[0] + spot[1] * 0.02
			deco.add_mesh(Ornaments.banner(pat), Transform3D(DecoMerge.facing(spot[1]), p))
			if d.get("links", true):
				flag_anchors.append(p + spot[1] * 0.62)
	for lt in d.get("lanterns", []):
		var spot := _wall_spot(int(lt.get("side", 0)), float(lt.get("u", 0.5)), float(lt.get("y", 2.2)))
		var n: Vector3 = spot[1]
		deco.add("wall_lantern", Transform3D(Basis.looking_at(n, Vector3.UP), spot[0] + n * 0.02))
		lamps.append(spot[0] + n * 0.3 + Vector3.DOWN * 0.1)


## A tower's wall face of radius r with the planned openings (_cut, in arc
## length at radius `ref`) left open and lined.
func _tower_wall(mb: MeshBuilder, r: float, ref: float, y0: float, y1: float, segs: int, col: Color, reveal := Color(0, 0, 0, -1)) -> void:
	WallCut.face(mb, WallCut.round_at(r, ref), WallCut.round_nrm(ref), 0.0, TAU * ref, y0, y1, _cut, col,
			col if reveal.a < 0.0 else reveal, 0.0, TAU * ref / segs)


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
	var beam := _wood(Color(0.50, 0.37, 0.24, 0.5))
	var gold := Color(0.95, 0.74, 0.30, 1.0)
	var stone_top := PL + (FH if floors > 1 else 1.0)
	var grown: Array = []
	for c in corners:
		var v: Vector3 = c
		grown.append(v + Vector3(signf(v.x), 0, signf(v.z)) * 0.04)
	if _preview:
		_ring_walls(mb, grown, PL, stone_top, stone, true, 0.04)
		_quoins(mb, corners, Color(0.95, 0.92, 0.85, 1.0), stone_top)
	else:
		_ring_walls(mb, grown, PL, stone_top, Masonry.mortar_color(LIMESTONE), true, 0.04, Color(LIMESTONE.r, LIMESTONE.g, LIMESTONE.b, 0.25))
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
	_ring_walls(mb, grown, PL, PL + 0.75, skirt, true, 0.05)
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
	var beam := _wood(Color(0.50, 0.37, 0.24, 0.5))
	var gold := Color(0.95, 0.74, 0.30, 1.0)
	var stone_top := PL + (FH if floors > 1 else 1.0)
	if _preview:
		_tower_wall(mb, R + 0.04, R, PL, stone_top, segs, stone)
	else:
		_tower_wall(mb, R + 0.04, R, PL, stone_top, segs, Masonry.mortar_color(LIMESTONE), Color(LIMESTONE.r, LIMESTONE.g, LIMESTONE.b, 0.25))
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
		_clear[side].append(Rect2(uu * l - 0.64 * sx, PL - 0.2, 1.28 * sx, 2.55))
		deco.add("door_wood", Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(sx, 1, 1)), p + Vector3.UP * PL + n * 0.02))
		deco.add("stair_step", Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(1.4, 1.0, 1.4)), p + n * 0.3))
		return
	var half := _door_into(deco, p, n, uu * l, style, sx, _cut[side], _clear[side])
	deco.add("stair_step", Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(half * 1.75, 1.0, 1.4)), p + n * 0.3))
	_door_steps(deco, p, n, half * 1.75)
	var along := (b - a).normalized()
	var reach := half + 0.3
	var side_off := reach if uu * l + reach < l - 0.2 else -reach
	deco.add("wall_lantern", Transform3D(Basis.looking_at(n, Vector3.UP), p + along * side_off + Vector3.UP * (PL + 2.0) + n * 0.02))
	lamps.append(p + along * side_off + Vector3.UP * (PL + 1.9) + n * 0.3)


## A Tiny Glade plank door set into the wall at p (ground level, on the face)
## `sx` times as wide; adds its opening to `cut` / `clear` (at s along the
## face) and returns the opening's half-width.
func _door_into(deco: DecoMerge, p: Vector3, n: Vector3, s: float, style: String, sx: float, cut: Array, clear: Array) -> float:
	var model := "tg_door"
	if sx > 1.3:
		model = "tg_door_double"
		sx = maxf(1.0, sx * 1.4 / 2.2)
	elif style == "stone":
		model = "tg_door_gothic"
	elif style == "plaster":
		model = "tg_door_arch"
	var room := eave - PL - 0.12
	if room < 1.6:
		# no storey to cut it into: a door standing on the face
		_tg(deco, model, Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(sx, 1, 1)), p + Vector3.UP * PL + n * 0.18))
		return float(WallCut.MODELS[model].w) * sx * 0.5
	if WallCut.model_height(model) > room and model == "tg_door_gothic":
		model = "tg_door_arch"
	if WallCut.model_height(model) > room and model == "tg_door_arch":
		model = "tg_door"
	var sy := minf(1.0, room / WallCut.model_height(model))
	_tg(deco, model, Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(sx, sy, 1)), p + Vector3.UP * PL))
	var hl := WallCut.hole_for(model, s, PL, sx)
	hl.h *= sy
	hl.nosill = true
	cut.append(hl)
	clear.append(WallCut.rect(hl, 0.08 + _surround_w(style)))
	return hl.w * 0.5


## A tg_* wood model in this house's wood tone and trim colour (Paint tool).
func _tg(deco: DecoMerge, kind: String, xf: Transform3D) -> void:
	deco.add_tinted(kind, xf, data.get("wood_tone", Color(0, 0, 0, 0)), data.get("trim_col", Color(0, 0, 0, 0)))


## This house's wood tone applied to a timber colour (beams, boards).
func _wood(c: Color) -> Color:
	var tone: Color = data.get("wood_tone", Color(0, 0, 0, 0))
	if tone.a <= 0.0:
		return c
	var h := ModelLib.HONEY
	return Color(minf(1.0, c.r * tone.r / h.r), minf(1.0, c.g * tone.g / h.g), minf(1.0, c.b * tone.b / h.b), c.a)


## The tg_* model a window of type `wt` uses on a house of `style` ("" for
## the carved round windows and arrow slits).
static func _window_model(wt: String, style: String) -> String:
	match wt:
		"arched":
			return "tg_window_arch"
		"gothic":
			return "tg_window_gothic"
		"lattice":
			return "tg_window_lattice"
		"round", "slit":
			return ""
	return "tg_window_lattice" if style in ["stone", "timber", "windrise", "lakeside"] else "tg_window"


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
	_tg(deco, "tg_window", Transform3D(DecoMerge.facing(n) * Basis.from_scale(Vector3(0.72, 0.7, 0.6)), p + Vector3.UP * 0.12 + n * 0.14))


# ---------------------------------------------------------------------------
# Life
# ---------------------------------------------------------------------------
func _add_smoke(_d: Dictionary) -> void:
	if not has_meta("smoke_at") or not _d.get("smoke", true):
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
## Rectangles stonework and boards keep clear of (planned with the openings).
func _openings(_d: Dictionary, _doors: Array, _corners: Array) -> Array:
	return _clear


func _round_openings(_d: Dictionary, _doors: Array, _R: float) -> Array:
	return _clear


## The stone-free rectangle a window of type `wt` needs, centred at s, y.
static func _window_hole(wt: String, s: float, y: float) -> Rect2:
	match wt:
		"arched":
			return Rect2(s - 0.58, y - 0.66, 1.16, 1.75)
		"round":
			return Rect2(s - 0.55, y - 0.3, 1.1, 1.1)
		"slit":
			return Rect2(s - 0.22, y - 0.6, 0.44, 1.5)
	return Rect2(s - 0.5, y - 0.62, 1.0, 1.42)


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
	var count := int((length * (y1 - y0) / 9.0 + _rng.randf() * 1.5) * _peel)
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
		Masonry.pattern = "glade"   # pillowy hand-laid stones, big at the foot
		Masonry.lay(mb, surf, -Masonry.DEPTH, l + Masonry.DEPTH, 0.0, y1 - y0, col, _rng,
				func(s0, s1, ya, yb): return _hits(side_holes, s0, s1, ya, yb),
				_patch_veto(l, y0, y1, bands) if patchy else Callable())


func _masonry_round(mb: MeshBuilder, R: float, y0: float, y1: float, col: Color, holes: Array, patchy := false, bands: Array = []) -> void:
	var surf := func(s: float) -> Dictionary:
		var ang := s / R
		var n := Vector3(cos(ang), 0.0, sin(ang))
		return {"p": n * R, "n": n, "g": y0, "low": y0 - 0.01, "top": y1}
	Masonry.pattern = "glade"
	Masonry.lay(mb, surf, 0.0, TAU * R, 0.0, y1 - y0, col, _rng,
			func(s0, s1, ya, yb): return _hits(holes, s0, s1, ya, yb),
			_patch_veto(TAU * R, y0, y1, bands) if patchy else Callable())
