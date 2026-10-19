class_name Music
extends Node

## Plays every music track at once, in sync, and fades each one toward its
## target volume so switching tracks is a smooth crossfade on the beat.
## Also owns the Music/SFX buses, the volume settings and the pause muffle.

const TRACKS := {
	"table": "res://audio/music_table.ogg",
	"shop": "res://audio/music_shop.ogg",
	"boss": "res://audio/music_boss.ogg",
}
const FADE_RATE := 1.6  # fraction of the gap closed per second
const SILENT_DB := -60.0

var track := "table"
var pitch_target := 1.0

var _players := {}
var _levels := {}
var _music_bus := -1
var _muffle: AudioEffectLowPassFilter


func _ready() -> void:
	_music_bus = _ensure_bus("Music")
	_ensure_bus("SFX")
	_muffle = AudioEffectLowPassFilter.new()
	_muffle.cutoff_hz = 900.0
	AudioServer.add_bus_effect(_music_bus, _muffle)
	AudioServer.set_bus_effect_enabled(_music_bus, 0, false)
	for name in TRACKS:
		var stream: AudioStreamOggVorbis = load(TRACKS[name])
		stream.loop = true
		var p := AudioStreamPlayer.new()
		p.stream = stream
		p.bus = "Music"
		p.volume_db = SILENT_DB
		add_child(p)
		_players[name] = p
		_levels[name] = 1.0 if name == track else 0.0
	for p in _players.values():
		p.play()


static func _ensure_bus(name: String) -> int:
	var idx := AudioServer.get_bus_index(name)
	if idx == -1:
		AudioServer.add_bus()
		idx = AudioServer.bus_count - 1
		AudioServer.set_bus_name(idx, name)
		AudioServer.set_bus_send(idx, "Master")
	return idx


func _process(delta: float) -> void:
	# Fades run on real time so game speed does not change them.
	var dt := delta / maxf(Engine.time_scale, 0.01)
	var k := clampf(dt * FADE_RATE, 0.0, 1.0)
	for name in _players:
		var target := 1.0 if name == track else 0.0
		_levels[name] = lerpf(_levels[name], target, k)
		var p: AudioStreamPlayer = _players[name]
		p.volume_db = linear_to_db(maxf(_levels[name], 0.001))
		p.pitch_scale = lerpf(p.pitch_scale, pitch_target, k)


func set_track(name: String) -> void:
	if _players.has(name):
		track = name


## Muffle the music while a menu is open.
func set_muffled(on: bool) -> void:
	AudioServer.set_bus_effect_enabled(_music_bus, 0, on)


## Apply the 0-100 volume settings to the buses.
static func apply_volumes(master: float, music: float, sfx: float) -> void:
	_set_bus("Master", master)
	_set_bus("Music", music)
	_set_bus("SFX", sfx)


static func _set_bus(name: String, percent: float) -> void:
	var idx := _ensure_bus(name)
	AudioServer.set_bus_mute(idx, percent <= 0.0)
	AudioServer.set_bus_volume_db(idx, linear_to_db(maxf(percent / 100.0, 0.001)))
