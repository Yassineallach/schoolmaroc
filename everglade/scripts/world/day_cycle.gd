class_name DayCycle
extends Node3D
## Sun, moon, sky, fog and seasons. Drives the global shader uniforms that
## light lanterns at night and tint/blanket the glade per season.

signal changed

const SEASONS := ["spring", "summer", "autumn", "winter"]
const SEASON_NAMES := ["Spring", "Summer", "Autumn", "Winter"]

var time_of_day := 0.38: set = set_time
var season := 1: set = set_season
var auto_advance := false
var night := 0.0

var sun: DirectionalLight3D
var moon: DirectionalLight3D
var env: Environment
var sky_mat: ProceduralSkyMaterial
var world_env: WorldEnvironment
var _season_leaf := Color(1, 1, 1, 0)
var _season_ground := Color(1, 1, 1, 1)
var _snow := 0.0
var _target_leaf := Color(1, 1, 1, 0)
var _target_ground := Color(1, 1, 1, 1)
var _target_snow := 0.0
var _particles: Dictionary = {}
var follow: Node3D


func _ready() -> void:
	sun = DirectionalLight3D.new()
	sun.name = "Sun"
	sun.shadow_enabled = Settings.shadows_enabled()
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	sun.directional_shadow_max_distance = 70.0
	sun.shadow_blur = 1.5
	sun.light_angular_distance = 1.0
	add_child(sun)
	moon = DirectionalLight3D.new()
	moon.name = "Moon"
	moon.light_color = Color(0.55, 0.65, 0.95)
	moon.shadow_enabled = false
	add_child(moon)
	sky_mat = ProceduralSkyMaterial.new()
	sky_mat.sun_angle_max = 20.0
	sky_mat.sun_curve = 0.1
	var sky := Sky.new()
	sky.sky_material = sky_mat
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	env = Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_sky_contribution = 0.75
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 1.0
	env.tonemap_white = 6.0
	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_DEPTH
	env.fog_depth_begin = 38.0
	env.fog_depth_end = 110.0
	env.fog_depth_curve = 1.4
	env.fog_sky_affect = 0.4
	env.glow_enabled = true
	env.glow_intensity = 0.6
	env.glow_bloom = 0.08
	env.glow_hdr_threshold = 1.1
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.08
	env.adjustment_contrast = 1.03
	world_env = WorldEnvironment.new()
	world_env.environment = env
	add_child(world_env)
	_build_particles()
	Settings.changed.connect(func(): sun.shadow_enabled = Settings.shadows_enabled())
	set_season(season)
	_snow = _target_snow
	_season_leaf = _target_leaf
	_season_ground = _target_ground
	_apply()


func set_time(t: float) -> void:
	time_of_day = fposmod(t, 1.0)
	if is_inside_tree():
		_apply()


func set_season(s: int) -> void:
	season = clampi(s, 0, 3)
	match SEASONS[season]:
		"spring":
			_target_leaf = Color(0.62, 1.0, 0.38, 0.35)
			_target_ground = Color(1.05, 1.08, 0.95)
			_target_snow = 0.0
		"summer":
			_target_leaf = Color(1, 1, 1, 0.0)
			_target_ground = Color(1, 1, 1)
			_target_snow = 0.0
		"autumn":
			_target_leaf = Color(1.0, 0.42, 0.1, 1.0)
			_target_ground = Color(1.08, 0.94, 0.72)
			_target_snow = 0.0
		"winter":
			_target_leaf = Color(0.62, 0.6, 0.5, 0.6)
			_target_ground = Color(0.92, 0.96, 1.02)
			_target_snow = 0.85
	if is_inside_tree():
		for key in _particles:
			(_particles[key] as CPUParticles3D).emitting = false
		var key: String = SEASONS[season]
		if _particles.has(key):
			(_particles[key] as CPUParticles3D).emitting = true
	changed.emit()


func _process(delta: float) -> void:
	if auto_advance:
		set_time(time_of_day + delta / 240.0)
	_season_leaf = _season_leaf.lerp(_target_leaf, minf(1.0, delta * 1.5))
	_season_ground = _season_ground.lerp(_target_ground, minf(1.0, delta * 1.5))
	_snow = lerpf(_snow, _target_snow, minf(1.0, delta * 1.2))
	RenderingServer.global_shader_parameter_set("season_leaf", _season_leaf)
	RenderingServer.global_shader_parameter_set("season_ground", _season_ground)
	RenderingServer.global_shader_parameter_set("snow_amount", _snow)
	var t := Time.get_ticks_msec() / 1000.0
	RenderingServer.global_shader_parameter_set("wind_strength", 0.8 + 0.4 * sin(t * 0.21) * sin(t * 0.13))
	if follow:
		var p := follow.global_position
		for key in _particles:
			(_particles[key] as Node3D).global_position = Vector3(p.x, maxf(p.y, 0.0) + 7.0, p.z)
		(_particles["fireflies"] as Node3D).global_position = Vector3(p.x, 0.0, p.z)


func _apply() -> void:
	# 0.25 sunrise, 0.5 noon, 0.75 sunset
	var sun_angle := (time_of_day - 0.25) * TAU
	var elevation := sin(sun_angle)
	var dir := Vector3(cos(sun_angle), sin(sun_angle) * 0.85, 0.35).normalized()
	sun.look_at_from_position(Vector3.ZERO, -dir, Vector3.UP)
	moon.look_at_from_position(Vector3.ZERO, Vector3(dir.x, -absf(dir.y) - 0.3, -dir.z), Vector3.UP)
	var day := smoothstep(-0.12, 0.22, elevation)
	var golden := smoothstep(0.45, 0.05, absf(elevation)) * smoothstep(-0.15, 0.05, elevation)
	night = 1.0 - smoothstep(-0.18, 0.06, elevation)
	sun.light_energy = 1.25 * day
	sun.light_color = Color(1.0, 0.97, 0.9).lerp(Color(1.0, 0.62, 0.38), golden)
	sun.visible = day > 0.01
	moon.light_energy = 0.32 * night
	moon.visible = night > 0.01
	var top_day := Color(0.36, 0.6, 0.88)
	var hor_day := Color(0.78, 0.88, 0.95)
	var top_gold := Color(0.42, 0.48, 0.75)
	var hor_gold := Color(1.0, 0.68, 0.48)
	var top_night := Color(0.04, 0.06, 0.16)
	var hor_night := Color(0.12, 0.16, 0.3)
	var top := top_night.lerp(top_day, day).lerp(top_gold, golden * 0.7)
	var hor := hor_night.lerp(hor_day, day).lerp(hor_gold, golden * 0.8)
	if season == 3:
		hor = hor.lerp(Color(0.85, 0.88, 0.92), 0.4 * day)
	sky_mat.sky_top_color = top
	sky_mat.sky_horizon_color = hor
	sky_mat.ground_horizon_color = hor
	sky_mat.ground_bottom_color = hor.darkened(0.3)
	sky_mat.sun_angle_max = 30.0
	env.fog_light_color = hor.lerp(Color(0.6, 0.7, 0.8), 0.2)
	env.ambient_light_energy = lerpf(0.55, 1.0, day)
	env.glow_intensity = lerpf(0.5, 1.1, night)
	RenderingServer.global_shader_parameter_set("night", night)
	Sfx.night = night
	if _particles.has("fireflies"):
		(_particles["fireflies"] as CPUParticles3D).emitting = night > 0.5 and season != 3
	changed.emit()


func _build_particles() -> void:
	_particles["autumn"] = _make_particles(Color(0.92, 0.55, 0.2), 60, Vector3(0.6, -1.0, 0.3), 0.09, false)
	_particles["winter"] = _make_particles(Color(1, 1, 1), 220, Vector3(0.1, -1.0, 0.05), 0.05, true)
	_particles["spring"] = _make_particles(Color(1.0, 0.8, 0.88), 40, Vector3(0.5, -0.6, 0.2), 0.06, false)
	var ff := CPUParticles3D.new()
	ff.amount = 50
	ff.lifetime = 6.0
	ff.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	ff.emission_box_extents = Vector3(18, 1.2, 18)
	ff.direction = Vector3.UP
	ff.spread = 180.0
	ff.gravity = Vector3.ZERO
	ff.initial_velocity_min = 0.1
	ff.initial_velocity_max = 0.4
	ff.position = Vector3(0, 1.0, 0)
	var curve := Curve.new()
	curve.add_point(Vector2(0, 0))
	curve.add_point(Vector2(0.5, 1))
	curve.add_point(Vector2(1, 0))
	ff.scale_amount_curve = curve
	var m := SphereMesh.new()
	m.radius = 0.04
	m.height = 0.08
	m.radial_segments = 6
	m.rings = 3
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = Color(1.0, 0.95, 0.5)
	mat.emission_enabled = true
	mat.emission = Color(1.0, 0.9, 0.4)
	mat.emission_energy_multiplier = 4.0
	m.material = mat
	ff.mesh = m
	ff.emitting = false
	add_child(ff)
	_particles["fireflies"] = ff


func _make_particles(col: Color, amount: int, dir: Vector3, size: float, round_flake: bool) -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.amount = amount
	p.lifetime = 8.0
	p.preprocess = 8.0
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	p.emission_box_extents = Vector3(22, 1, 22)
	p.direction = dir
	p.spread = 25.0
	p.gravity = Vector3(0, -0.4, 0)
	p.initial_velocity_min = 0.4
	p.initial_velocity_max = 1.0
	p.angular_velocity_min = -90.0
	p.angular_velocity_max = 90.0
	p.particle_flag_rotate_y = true
	var mesh: Mesh
	if round_flake:
		var s := SphereMesh.new()
		s.radius = size
		s.height = size * 2.0
		s.radial_segments = 4
		s.rings = 2
		mesh = s
	else:
		var q := QuadMesh.new()
		q.size = Vector2(size * 2.0, size * 1.3)
		mesh = q
	var mat := StandardMaterial3D.new()
	mat.albedo_color = col
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED if round_flake else BaseMaterial3D.SHADING_MODE_PER_VERTEX
	(mesh as PrimitiveMesh).material = mat
	p.mesh = mesh
	p.emitting = false
	add_child(p)
	return p


## Normalised daylight factor for UI (sun icon etc).
func is_night() -> bool:
	return night > 0.5
