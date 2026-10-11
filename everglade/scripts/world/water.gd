class_name Water
extends MeshInstance3D
## A single water sheet at the pond level; the shader reveals it only where
## the ground was dug below the waterline.

func setup(terrain: Terrain) -> void:
	var plane := PlaneMesh.new()
	plane.size = Vector2(Terrain.PLAY_HALF * 2.0 + 4.0, Terrain.PLAY_HALF * 2.0 + 4.0)
	plane.subdivide_width = 64
	plane.subdivide_depth = 64
	mesh = plane
	position = Vector3(0, Terrain.WATER_LEVEL, 0)
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/water.gdshader")
	mat.set_shader_parameter("height_tex", terrain.height_tex)
	mat.set_shader_parameter("terrain_origin", -Terrain.HALF)
	mat.set_shader_parameter("terrain_size", Terrain.HALF * 2.0)
	mat.set_shader_parameter("water_level", Terrain.WATER_LEVEL)
	material_override = mat
