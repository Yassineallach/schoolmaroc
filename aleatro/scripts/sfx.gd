class_name Sfx
extends Node

## Sound effect manager. Every .ogg in res://audio/sfx is loaded at startup
## and played by its file name ("sound code"). Files named name_1, name_2...
## are variations of "name"; one is picked at random each time. Each code
## gets a small pool of players so overlapping plays don't cut each other
## off. Files named ambient_* are looping beds faded in and out with
## set_ambient().

const DIR := "res://audio/sfx"
const POOL_MAX := 4
const AMBIENT_FADE := 1.2  # fraction of the gap closed per second

# Older short names still used around the code.
const ALIASES := {"click": "button", "select": "card_select", "deal": "card_slide", "win": "round_win", "lose": "game_over"}

var _streams := {}  # code -> Array[AudioStream] (variations)
var _pools := {}  # code -> Array[AudioStreamPlayer]
var _ambient := {}  # name -> {player, level, target}


func _ready() -> void:
	Music._ensure_bus("SFX")
	var variant := RegEx.create_from_string("^(.*)_(\\d+)$")
	for file in ResourceLoader.list_directory(DIR):
		if not file.ends_with(".ogg"):
			continue
		var code := file.get_basename()
		var stream: AudioStream = load(DIR.path_join(file))
		if code.begins_with("ambient_"):
			_add_ambient(code, stream)
			continue
		var m := variant.search(code)
		var group := m.get_string(1) if m else code
		if not _streams.has(group):
			_streams[group] = []
		_streams[group].append(stream)


func has(code: String) -> bool:
	return _streams.has(ALIASES.get(code, code))


## Play a sound by code at a pitch multiplier and linear volume.
func play(code: String, pitch: float = 1.0, volume: float = 1.0) -> void:
	code = ALIASES.get(code, code)
	var options: Array = _streams.get(code, [])
	if options.is_empty():
		return
	var p := _player_for(code)
	p.stream = options.pick_random()
	# A little random detune keeps repeated sounds from feeling mechanical.
	p.pitch_scale = maxf(0.05, pitch * randf_range(0.97, 1.03))
	p.volume_db = linear_to_db(maxf(volume, 0.001))
	p.play()


## Reuse an idle player for this code, add one if all are busy, or steal
## the one that started first.
func _player_for(code: String) -> AudioStreamPlayer:
	if not _pools.has(code):
		_pools[code] = []
	var pool: Array = _pools[code]
	for p in pool:
		if not p.playing:
			return p
	if pool.size() < POOL_MAX:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		pool.append(p)
		return p
	var oldest: AudioStreamPlayer = pool.pop_front()
	pool.append(oldest)
	return oldest


func stop_all() -> void:
	for pool in _pools.values():
		for p in pool:
			p.stop()


# ---------------------------------------------------------------- ambience

func _add_ambient(name: String, stream: AudioStream) -> void:
	if stream is AudioStreamOggVorbis:
		stream.loop = true
	var p := AudioStreamPlayer.new()
	p.bus = "SFX"
	p.stream = stream
	p.volume_db = -80.0
	add_child(p)
	_ambient[name] = {"player": p, "level": 0.0, "target": 0.0}


## Fade an ambient bed (by name, e.g. "ambient_table") toward `level` 0..1.
func set_ambient(name: String, level: float) -> void:
	if _ambient.has(name):
		_ambient[name].target = clampf(level, 0.0, 1.0)


func _process(delta: float) -> void:
	var dt := delta / maxf(Engine.time_scale, 0.01)
	for a in _ambient.values():
		a.level = move_toward(a.level, a.target, dt * AMBIENT_FADE)
		var p: AudioStreamPlayer = a.player
		if a.level > 0.001:
			if not p.playing:
				p.play()
			p.volume_db = linear_to_db(a.level)
		elif p.playing:
			p.stop()
