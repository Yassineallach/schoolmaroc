extends Node
## Persistent player preferences (audio, graphics, controls).

signal changed

const PATH := "user://settings.cfg"

var music_volume := 0.7
var sfx_volume := 0.9
var ambience_volume := 0.7
var haptics := true
var quality := 1 # 0 low, 1 medium, 2 high
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
	cfg.save(PATH)


func apply() -> void:
	_set_bus("Music", music_volume)
	_set_bus("SFX", sfx_volume)
	_set_bus("Ambience", ambience_volume)
	var vp := get_viewport()
	if vp:
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
	return [0.6, 1.3, 2.2][quality]


func shadows_enabled() -> bool:
	return quality > 0
