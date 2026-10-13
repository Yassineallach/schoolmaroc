class_name PropBatch
extends Node3D
## Draws every placed prop (trees, flowers, lanterns, wells...) through one
## MultiMesh per kind. Freshly placed props pop in as single instances first.

const NO_SHADOW := ["flowers_pink", "flowers_white", "flowers_blue", "flowers_yellow", "flowers_red", "mushrooms", "grass_tuft", "fern", "plant_leafy", "wheat"]

var _mmis: Dictionary = {} # kind -> [solid MMI, glow MMI or null]
var _hidden: Dictionary = {}
var _props: Array = []
var _animated: Dictionary = {} # prop id -> Node3D (windmills...)


static func prop_transform(p: Dictionary) -> Transform3D:
	var basis := Basis(Vector3.UP, p.get("r", 0.0))
	if p.has("n"):
		var n: Vector3 = p.n
		if n.y < 0.999:
			var axis := Vector3.UP.cross(n).normalized()
			basis = Basis(axis, Vector3.UP.angle_to(n)) * basis
	basis = basis.scaled(Vector3.ONE * p.get("s", 1.0))
	return Transform3D(basis, p.p)


func rebuild(props: Array) -> void:
	_props = props
	var groups: Dictionary = {}
	var live: Dictionary = {}
	for p in props:
		if _hidden.has(p.id):
			continue
		if Catalog.ANIMATED.has(p.kind):
			live[p.id] = true
			_sync_animated(p)
			continue
		if not groups.has(p.kind):
			groups[p.kind] = []
		groups[p.kind].append(prop_transform(p))
	for id in _animated.keys():
		if not live.has(id):
			_animated[id].queue_free()
			_animated.erase(id)
	for kind in _mmis.keys():
		if not groups.has(kind):
			for mmi in _mmis[kind]:
				if mmi:
					mmi.queue_free()
			_mmis.erase(kind)
	for kind in groups:
		var m: Dictionary = ModelLib.merged(kind)
		if not _mmis.has(kind):
			var solid: MultiMeshInstance3D = null
			if m.solid:
				solid = _make_mmi(m.solid, ModelLib.props_material, not NO_SHADOW.has(kind))
			var glow: MultiMeshInstance3D = null
			if m.glow:
				glow = _make_mmi(m.glow, ModelLib.glow_material, false)
			var leaves: MultiMeshInstance3D = null
			if m.leaves:
				leaves = _make_mmi(m.leaves, m.get("leaf_mat", ModelLib.leaf_material), true)
			var parts: Array = [solid, glow, leaves]
			for pair in m.tex:
				parts.append(_make_mmi(pair[0], pair[1], not NO_SHADOW.has(kind)))
			_mmis[kind] = parts
		var xforms: Array = groups[kind]
		for mmi in _mmis[kind]:
			if mmi == null:
				continue
			var mm: MultiMesh = mmi.multimesh
			mm.instance_count = xforms.size()
			for i in xforms.size():
				mm.set_instance_transform(i, xforms[i])


func _sync_animated(p: Dictionary) -> void:
	var node: Node3D = _animated.get(p.id)
	if node == null or node.get_meta("kind", "") != p.kind:
		if node:
			node.queue_free()
		node = ModelLib.instance(p.kind)
		node.set_meta("kind", p.kind)
		add_child(node)
		_animated[p.id] = node
	node.transform = prop_transform(p)


func _process(delta: float) -> void:
	var t := Time.get_ticks_msec() / 1000.0
	var wind := 0.8 + 0.4 * sin(t * 0.21) * sin(t * 0.13)
	for node in _animated.values():
		var sails := node.find_child("Sails", true, false) as Node3D
		if sails:
			sails.rotation.z += delta * (0.5 + 0.4 * wind)


func _make_mmi(mesh: Mesh, mat: Material, shadows: bool) -> MultiMeshInstance3D:
	var mmi := MultiMeshInstance3D.new()
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mmi.multimesh = mm
	mmi.material_override = mat
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadows else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mmi)
	return mmi


## Spawns a bouncy single instance for a new prop, then hands it back to the batch.
func pop_in(p: Dictionary, delay := 0.0) -> void:
	_hidden[p.id] = true
	rebuild(_props)
	var node := Node3D.new()
	var m: Dictionary = ModelLib.merged(p.kind)
	for pair in [[m.solid, ModelLib.props_material], [m.glow, ModelLib.glow_material], [m.leaves, m.get("leaf_mat", ModelLib.leaf_material)]] + m.tex:
		if pair[0]:
			var mi := MeshInstance3D.new()
			mi.mesh = pair[0]
			mi.material_override = pair[1]
			node.add_child(mi)
	add_child(node)
	var xf := prop_transform(p)
	node.transform = xf
	var final_scale := xf.basis.get_scale()
	node.scale = Vector3.ONE * 0.01
	var tw := node.create_tween()
	if delay > 0.0:
		tw.tween_interval(delay)
	tw.tween_property(node, "scale", final_scale * 1.12, 0.18).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.tween_property(node, "scale", final_scale, 0.15).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_callback(func():
		_hidden.erase(p.id)
		rebuild(_props)
		node.queue_free())
