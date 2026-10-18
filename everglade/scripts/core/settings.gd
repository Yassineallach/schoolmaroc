extends Node
## Persistent player preferences (audio, graphics, controls).

signal changed

const PATH := "user://settings.cfg"

var music_volume := 0.7
var sfx_volume := 0.9
var ambience_volume := 0.7
var haptics := true
var quality := 1 # 0 low, 1 medium, 2 high
var fog := 0.22 # 0 clear .. 1 thick
var fog_height := 0.35 # 0 hugs the ground .. 1 fills the valley
var snow := 0.85 # how thickly winter glades are snowed over
var zoom_to_cursor := false
var key_hints := true
var perf_overlay := false
var invert_rotate := false
var show_tips := true
var tips_seen: Dictionary = {}


func _ready() -> void:
	load_settings()
	if OS.has_feature("mobile") and not FileAccess.file_exists(PATH):
		quality = _guess_quality()
	apply()


func _guess_quality() -> int:
	var cores := OS.get_processor_count()
	if cores >= 8:
		return 2
	if cores >= 6:
		return 1
	return 0


func load_settings() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(PATH) != OK:
		return
	music_volume = cfg.get_value("audio", "music", music_volume)
	sfx_volume = cfg.get_value("audio", "sfx", sfx_volume)
	ambience_volume = cfg.get_value("audio", "ambience", ambience_volume)
	haptics = cfg.get_value("controls", "haptics", haptics)
	invert_rotate = cfg.get_value("controls", "invert_rotate", invert_rotate)
	show_tips = cfg.get_value("controls", "show_tips", show_tips)
	tips_seen = cfg.get_value("controls", "tips_seen", tips_seen)
	quality = cfg.get_value("graphics", "quality", quality)
	fog = cfg.get_value("graphics", "fog", fog)
	fog_height = cfg.get_value("graphics", "fog_height", fog_height)
	snow = cfg.get_value("graphics", "snow", snow)
	zoom_to_cursor = cfg.get_value("controls", "zoom_to_cursor", zoom_to_cursor)
	key_hints = cfg.get_value("controls", "key_hints", key_hints)
	perf_overlay = cfg.get_value("graphics", "perf_overlay", perf_overlay)


func save_settings() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("audio", "music", music_volume)
	cfg.set_value("audio", "sfx", sfx_volume)
	cfg.set_value("audio", "ambience", ambience_volume)
	cfg.set_value("controls", "haptics", haptics)
	cfg.set_value("controls", "invert_rotate", invert_rotate)
	cfg.set_value("controls", "show_tips", show_tips)
	cfg.set_value("controls", "tips_seen", tips_seen)
	cfg.set_value("graphics", "quality", quality)
	cfg.set_value("graphics", "fog", fog)
	cfg.set_value("graphics", "fog_height", fog_height)
	cfg.set_value("graphics", "snow", snow)
	cfg.set_value("controls", "zoom_to_cursor", zoom_to_cursor)
	cfg.set_value("controls", "key_hints", key_hints)
	cfg.set_value("graphics", "perf_overlay", perf_overlay)
	cfg.save(PATH)


func apply() -> void:
	_set_bus("Music", music_volume)
	_set_bus("SFX", sfx_volume)
	_set_bus("Ambience", ambience_volume)
	var vp := get_viewport()
	if vp:
		if OS.has_feature("mobile"):
			# Phone screens are so dense (an S21+ is 2400 x 1080 on 6.7") that
			# drawing the 3D at full size costs a lot for nothing: render it
			# smaller and bring it back up with AMD FSR, which rebuilds the
			# edges and sharpens, so it looks the same. The UI stays full size.
			vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR
			vp.scaling_3d_scale = [0.6, 0.7, 0.78][quality]
			vp.fsr_sharpness = 0.2
			# A steady 60 instead of chasing 120 Hz: half the work per second,
			# even frame pacing, and the phone doesn't heat up and throttle
			Engine.max_fps = 60
		else:
			vp.scaling_3d_scale = [0.7, 0.85, 1.0][quality]
		vp.msaa_3d = [Viewport.MSAA_DISABLED, Viewport.MSAA_2X, Viewport.MSAA_4X][quality]
	changed.emit()


func _set_bus(bus_name: String, value: float) -> void:
	var idx := AudioServer.get_bus_index(bus_name)
	if idx < 0:
		idx = AudioServer.bus_count
		AudioServer.add_bus(idx)
		AudioServer.set_bus_name(idx, bus_name)
		AudioServer.set_bus_send(idx, "Master")
	AudioServer.set_bus_volume_db(idx, linear_to_db(maxf(value, 0.0001)))
	AudioServer.set_bus_mute(idx, value <= 0.001)


func vibrate(ms: int = 12) -> void:
	if haptics and OS.has_feature("mobile"):
		Input.vibrate_handheld(ms, 0.4)


func tip_seen(key: String) -> bool:
	return not show_tips or tips_seen.has(key)


func mark_tip(key: String) -> void:
	tips_seen[key] = true
	save_settings()


## Grass instances per square metre for the current quality level.
func grass_density() -> float:
	return [1.2, 2.2, 3.4][quality]


func shadows_enabled() -> bool:
	return quality > 0
