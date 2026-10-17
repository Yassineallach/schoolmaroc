class_name MeshLod
extends RefCounted
## Automatic detail levels for generated meshes (houses, walls). Godot then
## draws a simplified version of a mesh once it is far enough away that the
## difference is under a pixel on screen, in the shadow pass too, so the
## picture stays the same while distant buildings cost a fraction.


## The mesh with LOD index sets added (vertex colours, UVs and normals are
## kept). Small meshes come back unchanged.
static func with_lods(m: Mesh, min_tris := 3000) -> Mesh:
	if not (m is ArrayMesh) or m.get_surface_count() == 0:
		return m
	var am := m as ArrayMesh
	var tris := 0
	for s in am.get_surface_count():
		var idx = am.surface_get_arrays(s)[Mesh.ARRAY_INDEX]
		if idx == null:
			return m
		tris += (idx as PackedInt32Array).size() / 3
	if tris < min_tris:
		return m
	var im := ImporterMesh.new()
	for s in am.get_surface_count():
		im.add_surface(am.surface_get_primitive_type(s), am.surface_get_arrays(s), [], {}, am.surface_get_material(s),
				am.surface_get_name(s), am.surface_get_format(s))
	im.generate_lods(25.0, 60.0, [])
	return im.get_mesh()


## Swaps LOD versions into every MeshInstance3D under `root`.
static func apply_under(root: Node) -> void:
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		if mi.mesh:
			mi.mesh = with_lods(mi.mesh)
	if root is MeshInstance3D and (root as MeshInstance3D).mesh:
		(root as MeshInstance3D).mesh = with_lods((root as MeshInstance3D).mesh)
