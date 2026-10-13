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
var sky_mat: ShaderMaterial
var clouds: Node3D
var cloud_mat: ShaderMaterial
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
	sky_mat = ShaderMaterial.new()
	sky_mat.shader = load("res://shaders/sky.gdshader")
	var sky := Sky.new()
	sky.sky_material = sky_mat
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	env = Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	# soft natural fill: a gentle sky-tinted ambient keeps shade readable
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.70, 0.75, 0.84)
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 1.12
	env.tonemap_white = 6.0
	# exponential height fog: thin over the glade, thicker in the distance
	# and close to the ground (density/height follow the player's settings)
	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_EXPONENTIAL
	env.fog_sky_affect = 0.35
	_apply_fog_settings()
	env.glow_enabled = true
	env.glow_intensity = 0.6
	env.glow_bloom = 0.08
	env.glow_hdr_threshold = 1.1
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.06
	env.adjustment_contrast = 1.08
	world_env = WorldEnvironment.new()
	world_env.environment = env
	add_child(world_env)
	_build_particles()
	_build_clouds()
	Settings.changed.connect(func():
		sun.shadow_enabled = Settings.shadows_enabled()
		_apply_fog_settings())
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
	if clouds:
		clouds.rotate_y(delta * 0.004)
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
	sun.light_energy = 1.55 * day
	sun.light_color = Color(1.0, 0.93, 0.8).lerp(Color(1.0, 0.68, 0.44), golden)
	sun.visible = day > 0.01
	moon.light_energy = 0.32 * night
	moon.visible = night > 0.01
	var top_day := Color(0.36, 0.58, 0.86)
	var hor_day := Color(0.80, 0.87, 0.92)
	var top_gold := Color(0.36, 0.38, 0.78)
	var hor_gold := Color(1.0, 0.62, 0.46)
	var top_night := Color(0.03, 0.05, 0.18)
	var hor_night := Color(0.14, 0.18, 0.40)
	var top := top_night.lerp(top_day, day).lerp(top_gold, golden * 0.7)
	var hor := hor_night.lerp(hor_day, day).lerp(hor_gold, golden * 0.8)
	if season == 3:
		hor = hor.lerp(Color(0.85, 0.88, 0.92), 0.4 * day)
	sky_mat.set_shader_parameter("top_color", top)
	sky_mat.set_shader_parameter("horizon_color", hor)
	sky_mat.set_shader_parameter("ground_color", hor.darkened(0.15))
	sky_mat.set_shader_parameter("glow_color", Color(1.0, 0.95, 0.85).lerp(Color(1.0, 0.55, 0.45), golden))
	sky_mat.set_shader_parameter("night", night)
	sky_mat.set_shader_parameter("sunset", golden)
	env.fog_light_color = hor.lerp(Color(0.7, 0.8, 0.95), 0.25)
	# fill light: cool sky by day, warm at golden hour, deep blue at night
	var amb := Color(0.78, 0.79, 0.82).lerp(Color(0.86, 0.74, 0.66), golden).lerp(Color(0.24, 0.30, 0.52), night)
	env.ambient_light_color = amb
	env.ambient_light_energy = lerpf(0.55, 0.62, day)
	if cloud_mat:
		var lit := Color(1, 1, 1).lerp(Color(1.0, 0.78, 0.66), golden).lerp(Color(0.32, 0.38, 0.62), night)
		var shade := Color(0.72, 0.80, 0.98).lerp(Color(0.70, 0.56, 0.78), golden).lerp(Color(0.16, 0.2, 0.38), night)
		cloud_mat.set_shader_parameter("lit_color", lit)
		cloud_mat.set_shader_parameter("shade_color", shade)
		cloud_mat.set_shader_parameter("sun_dir", dir if night < 0.5 else Vector3(-dir.x, absf(dir.y) + 0.3, dir.z))
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


## A ring of big painted cumulus clouds drifting around the glade.
func _build_clouds() -> void:
	clouds = Node3D.new()
	clouds.name = "Clouds"
	add_child(clouds)
	cloud_mat = ShaderMaterial.new()
	cloud_mat.shader = load("res://shaders/cloud_card.gdshader")
	cloud_mat.set_shader_parameter("cloud_tex", load("res://assets/textures/clouds.png"))
	var rng := RandomNumberGenerator.new()
	rng.seed = 99
	var quad := QuadMesh.new()
	quad.size = Vector2(1.0, 0.62)
	quad.center_offset = Vector3(0.0, 0.31, 0.0)
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = quad
	mm.instance_count = 26
	for i in mm.instance_count:
		var a := rng.randf() * TAU
		var low := i < 12
		# a low bank of big cumulus near the horizon plus higher scattered puffs
		var r := rng.randf_range(120.0, 165.0) if low else rng.randf_range(95.0, 150.0)
		var y := rng.randf_range(4.0, 16.0) if low else rng.randf_range(26.0, 60.0)
		var s := rng.randf_range(55.0, 85.0) if low else rng.randf_range(28.0, 48.0)
		mm.set_instance_transform(i, Transform3D(Basis.from_scale(Vector3(s, s, s)), Vector3(cos(a) * r, y, sin(a) * r)))
		mm.set_instance_custom_data(i, Color(float(i % 2), float((i / 2) % 2), 0.0, 0.0))
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.material_override = cloud_mat
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mmi.extra_cull_margin = 200.0
	clouds.add_child(mmi)


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


## Fog density and how tightly it hugs the ground (Settings.fog / fog_height).
func _apply_fog_settings() -> void:
	var amount: float = Settings.fog
	# a soft aerial haze always swallows the far landscape
	env.fog_density = lerpf(0.0045, 0.03, amount * amount)
	env.fog_height = lerpf(-2.0, 6.0, Settings.fog_height)
	env.fog_height_density = lerpf(0.0, 0.2, amount * amount)
	env.fog_aerial_perspective = 0.25
