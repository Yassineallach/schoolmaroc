class_name Ivy
extends RefCounted
## Climbing ivy that slowly creeps up walls and cottages over time.

static var _leaf: ArrayMesh


static func leaf_mesh() -> ArrayMesh:
	if _leaf:
		return _leaf
	var mb := MeshBuilder.new()
	var c := Color(0.30, 0.50, 0.22, 0.0) # alpha 0 = foliage channel
	var s := 0.07
	var a := Vector3(0, -s, 0)
	var b := Vector3(s * 0.9, 0, 0.02)
	var t := Vector3(0, s * 1.1, 0)
	var d := Vector3(-s * 0.9, 0, 0.02)
	# front (+z) and back faces
	mb.quad(a, b, t, d, c)
	mb.quad(a, d, t, b, c.darkened(0.15))
	_leaf = mb.commit()
	return _leaf


## faces: Array of {a, b (bottom corners), n (outward), h (height)}.
## Returns a MultiMeshInstance3D whose visible count follows `growth`.
static func build(faces: Array, seed_value: int, density := 1.0) -> MultiMeshInstance3D:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var leaves: Array = [] # [order, Transform3D]
	for f in faces:
		var a: Vector3 = f.a
		var b: Vector3 = f.b
		var n: Vector3 = f.n
		var width := a.distance_to(b)
		var vines := int(width / 2.2 * density + rng.randf())
		for v in vines:
			var t := rng.randf_range(0.05, 0.95)
			var base := a.lerp(b, t) + n * 0.03
			var along := (b - a).normalized()
			var max_h: float = f.h * rng.randf_range(0.35, 0.95)
			var y := 0.0
			var x := 0.0
			var step := 0
			while y < max_h:
				var spread := 1 + int(y / 0.6)
				for k in mini(spread + 1, 4):
					var off := x + rng.randf_range(-0.18, 0.18) * (1.0 + k * 0.6)
					var p := base + along * off + Vector3.UP * (y + rng.randf_range(-0.05, 0.05)) + n * rng.randf_range(0.0, 0.05)
					var basis := DecoMerge.facing(n)
					basis = basis * Basis(Vector3.BACK, rng.randf_range(-0.8, 0.8))
					basis = basis.scaled(Vector3.ONE * rng.randf_range(0.7, 1.3))
					leaves.append([step + rng.randf() * 2.0, Transform3D(basis, p)])
				y += 0.09
				x += rng.randf_range(-0.08, 0.08)
				step += 1
	leaves.sort_custom(func(l, r): return l[0] < r[0])
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.mesh = leaf_mesh()
	mm.instance_count = leaves.size()
	for i in leaves.size():
		mm.set_instance_transform(i, leaves[i][1])
		var shade := rng.randf_range(0.8, 1.2)
		mm.set_instance_color(i, Color(shade, shade * rng.randf_range(0.95, 1.08), shade * 0.9, 1.0))
	var mmi := MultiMeshInstance3D.new()
	mmi.name = "Ivy"
	mmi.multimesh = mm
	mmi.material_override = ModelLib.props_material
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mm.visible_instance_count = 0
	return mmi


static func set_growth(mmi: MultiMeshInstance3D, growth: float) -> void:
	if mmi and mmi.multimesh:
		mmi.multimesh.visible_instance_count = int(mmi.multimesh.instance_count * clampf(growth, 0.0, 1.0))
