class_name CameraRig
extends Node3D
## Diorama camera: orbits a focus point; zooming in lowers the camera
## towards eye level (like peeking into the glade), zooming out gives an
## overview. Supports pinch/twist/pan gestures and mouse/keyboard.

const MIN_DIST := 5.0
const MAX_DIST := 62.0

var camera: Camera3D
var terrain: Terrain
## Optional Callable(Vector2) -> float giving the lowest safe camera height (roofs).
var height_probe: Callable
var target := Vector3.ZERO
var yaw := deg_to_rad(35.0)
var distance := 30.0
var pitch_offset := 0.0
var auto_orbit := false
var photo_mode := false
## Top-down map view (Tiny Glade's map camera).
var map_mode := false

var _s_target := Vector3.ZERO
var _s_yaw := 0.0
var _s_distance := 30.0
var _s_pitch_offset := 0.0
var _shake := 0.0


func _ready() -> void:
	camera = Camera3D.new()
	camera.fov = 42.0
	camera.near = 0.1
	camera.far = 400.0
	add_child(camera)
	var attrs := CameraAttributesPractical.new()
	camera.attributes = attrs
	_add_outline()
	_add_far_blur()
	_s_target = target
	_s_yaw = yaw
	_s_distance = distance
	_apply()


## Camera blur over the distance beyond the glade (shaders/far_blur).
var far_blur: MeshInstance3D
var _far_blur_mat: ShaderMaterial


func _add_far_blur() -> void:
	far_blur = MeshInstance3D.new()
	far_blur.name = "FarBlur"
	var quad := QuadMesh.new()
	quad.size = Vector2.ONE
	far_blur.mesh = quad
	_far_blur_mat = ShaderMaterial.new()
	_far_blur_mat.shader = load("res://shaders/far_blur.gdshader")
	_far_blur_mat.set_shader_parameter("glade_half", Terrain.PLAY_HALF + 3.0)
	_far_blur_mat.render_priority = -1
	far_blur.material_override = _far_blur_mat
	far_blur.extra_cull_margin = 16384.0
	far_blur.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	far_blur.position = Vector3(0, 0, -1.0)
	camera.add_child(far_blur)


## Full-screen contact shading (soft occlusion in creases) from the depth buffer.
var outline: MeshInstance3D


func _add_outline() -> void:
	outline = MeshInstance3D.new()
	outline.name = "Outline"
	var quad := QuadMesh.new()
	quad.size = Vector2.ONE
	outline.mesh = quad
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/contact_ao.gdshader")
	outline.material_override = mat
	outline.extra_cull_margin = 16384.0
	outline.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	outline.position = Vector3(0, 0, -1.0)
	camera.add_child(outline)
	Settings.changed.connect(func(): outline.visible = Settings.quality > 0)
	outline.visible = Settings.quality > 0


func base_pitch(dist: float) -> float:
	var t := inverse_lerp(MIN_DIST, MAX_DIST, dist)
	return deg_to_rad(lerpf(14.0, 58.0, pow(clampf(t, 0.0, 1.0), 0.8)))


func _process(delta: float) -> void:
	if auto_orbit:
		yaw += delta * 0.06
	var k := 1.0 - exp(-delta * 10.0)
	_s_target = _s_target.lerp(target, k)
	_s_yaw = lerp_angle(_s_yaw, yaw, k)
	_s_distance = lerpf(_s_distance, distance, k)
	_s_pitch_offset = lerpf(_s_pitch_offset, pitch_offset, k)
	_shake = maxf(0.0, _shake - delta * 3.0)
	_apply()


func _apply() -> void:
	var pitch := clampf(base_pitch(_s_distance) + _s_pitch_offset, deg_to_rad(3.0), deg_to_rad(85.0))
	if map_mode:
		pitch = deg_to_rad(89.5)
	var dir := Vector3(sin(_s_yaw) * cos(pitch), sin(pitch), cos(_s_yaw) * cos(pitch))
	var pos := _s_target + dir * _s_distance
	if terrain:
		var ground := terrain.height_at(pos.x, pos.z)
		pos.y = maxf(pos.y, ground + 0.8)
		pos.y = maxf(pos.y, Terrain.WATER_LEVEL + 0.5)
	if height_probe.is_valid():
		pos.y = maxf(pos.y, height_probe.call(Vector2(pos.x, pos.z)))
	if _shake > 0.0:
		pos += Vector3(randf_range(-1, 1), randf_range(-1, 1), randf_range(-1, 1)) * _shake * 0.05
	camera.global_position = pos
	var look := _s_target + Vector3.UP * lerpf(0.6, 0.0, inverse_lerp(MIN_DIST, MAX_DIST, _s_distance))
	if pos.distance_to(look) > 0.01:
		camera.look_at(look, Vector3.UP)
	# tilt-shift style camera blur for the miniature look; it also softens
	# the woods running off to the horizon
	if _far_blur_mat:
		_far_blur_mat.set_shader_parameter("far_start", _s_distance * 1.1 + 8.0)
		_far_blur_mat.set_shader_parameter("far_end", _s_distance * 2.6 + 50.0)
	if far_blur:
		# photo mode focuses with its own lens settings (PhotoUI)
		far_blur.visible = not photo_mode
	var attrs := camera.attributes as CameraAttributesPractical
	if attrs and not photo_mode:
		# Godot's own far blur smears the whole screen with MSAA on Mobile
		attrs.dof_blur_far_enabled = false
		attrs.dof_blur_far_distance = _s_distance * 1.6 + 6.0
		attrs.dof_blur_far_transition = _s_distance * 1.2 + 8.0
		attrs.dof_blur_near_enabled = photo_mode
		attrs.dof_blur_near_distance = maxf(0.5, _s_distance * 0.35)
		attrs.dof_blur_near_transition = _s_distance * 0.3
		attrs.dof_blur_amount = 0.08 if photo_mode else 0.05


func pan_screen(delta_px: Vector2) -> void:
	var vp := get_viewport().get_visible_rect().size
	var scale_m := _s_distance * 1.25 / maxf(vp.y, 1.0)
	var right := Vector3(cos(yaw), 0, -sin(yaw))
	var fwd := Vector3(-sin(yaw), 0, -cos(yaw))
	target += (-right * delta_px.x + fwd * delta_px.y) * scale_m
	_clamp_target()


func pan_world(offset: Vector3) -> void:
	target += Vector3(offset.x, 0, offset.z)
	_clamp_target()


func rotate_by(radians: float) -> void:
	yaw += radians


func tilt_by(radians: float) -> void:
	pitch_offset = clampf(pitch_offset + radians, deg_to_rad(-30.0), deg_to_rad(30.0))


func zoom_by(factor: float) -> void:
	var min_d := 2.5 if photo_mode else MIN_DIST
	distance = clampf(distance * factor, min_d, MAX_DIST)


func focus_on(p: Vector3, dist := -1.0) -> void:
	target = Vector3(p.x, 0, p.z)
	if dist > 0.0:
		distance = dist
	_clamp_target()


func shake(amount := 1.0) -> void:
	_shake = maxf(_shake, amount)


func snap() -> void:
	_s_target = target
	_s_yaw = yaw
	_s_distance = distance
	_s_pitch_offset = pitch_offset
	_apply()


func _clamp_target() -> void:
	var lim := Terrain.PLAY_HALF + 2.0
	target.x = clampf(target.x, -lim, lim)
	target.z = clampf(target.z, -lim, lim)
	if terrain:
		target.y = maxf(terrain.height_at(target.x, target.z), Terrain.WATER_LEVEL)
