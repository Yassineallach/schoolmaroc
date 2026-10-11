class_name DecoMerge
extends RefCounted
## Merges many prop placements (windows, posts, cobbles...) into one solid
## mesh and one glowing mesh so each structure costs only a couple of draws.

var _solid := SurfaceTool.new()
var _glow := SurfaceTool.new()
var _has_solid := false
var _has_glow := false


func add(kind: String, xf: Transform3D) -> void:
	var m: Dictionary = ModelLib.merged(kind)
	if m.solid:
		_solid.append_from(m.solid, 0, xf)
		_has_solid = true
	if m.glow:
		_glow.append_from(m.glow, 0, xf)
		_has_glow = true


func add_mesh(mesh: Mesh, xf: Transform3D) -> void:
	for s in mesh.get_surface_count():
		_solid.append_from(mesh, s, xf)
		_has_solid = true


func solid_mesh() -> ArrayMesh:
	return _solid.commit() if _has_solid else null


func glow_mesh() -> ArrayMesh:
	return _glow.commit() if _has_glow else null


## Attaches MeshInstance3D children to `parent` (replacing old ones).
func apply_to(parent: Node3D, solid_name := "Deco", glow_name := "DecoGlow") -> void:
	for n in [solid_name, glow_name]:
		var old := parent.get_node_or_null(n)
		if old:
			old.free()
	var s := solid_mesh()
	if s:
		var mi := MeshInstance3D.new()
		mi.name = solid_name
		mi.mesh = s
		mi.material_override = ModelLib.props_material
		parent.add_child(mi)
	var g := glow_mesh()
	if g:
		var gi := MeshInstance3D.new()
		gi.name = glow_name
		gi.mesh = g
		gi.material_override = ModelLib.glow_material
		gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		parent.add_child(gi)


## Basis whose +Z faces `outward` (horizontal), i.e. Blender's -Y front.
static func facing(outward: Vector3) -> Basis:
	var o := Vector3(outward.x, 0.0, outward.z).normalized()
	if o.length_squared() < 0.5:
		o = Vector3.BACK
	return Basis.looking_at(-o, Vector3.UP)


## Basis whose +X follows `dir` on the ground plane.
static func along(dir: Vector3) -> Basis:
	var d := Vector3(dir.x, 0.0, dir.z).normalized()
	if d.length_squared() < 0.5:
		d = Vector3.RIGHT
	var z := d.cross(Vector3.UP).normalized()
	return Basis(d, Vector3.UP, z)
