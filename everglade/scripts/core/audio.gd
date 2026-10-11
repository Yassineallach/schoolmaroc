extends Node
## Sound effects, ambience beds and the gentle music playlist.

const DIR := "res://assets/audio/"
const MUSIC := ["music_morning", "music_meadow", "music_evening"]

var _streams: Dictionary = {}
var _pool: Array[AudioStreamPlayer] = []
var _pool3d: Array[AudioStreamPlayer3D] = []
var _music: AudioStreamPlayer
var _amb_day: AudioStreamPlayer
var _amb_night: AudioStreamPlayer
var _music_index := 0
var _music_gap := 0.0
var _last_play: Dictionary = {}
var night := 0.0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for i in 10:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_pool.append(p)
	for i in 6:
		var p3 := AudioStreamPlayer3D.new()
		p3.bus = "SFX"
		p3.unit_size = 8.0
		p3.max_distance = 70.0
		add_child(p3)
		_pool3d.append(p3)
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.finished.connect(_on_music_finished)
	add_child(_music)
	_amb_day = _loop_player("amb_day")
	_amb_night = _loop_player("amb_night")
	_music_index = randi() % MUSIC.size()
	_music_gap = 4.0


func _loop_player(stream_name: String) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.bus = "Ambience"
	var s := _stream(stream_name)
	if s is AudioStreamOggVorbis:
		(s as AudioStreamOggVorbis).loop = true
	elif s is AudioStreamWAV:
		(s as AudioStreamWAV).loop_mode = AudioStreamWAV.LOOP_FORWARD
	p.stream = s
	p.volume_db = -80.0
	add_child(p)
	if s:
		p.play()
	return p


func _stream(stream_name: String) -> AudioStream:
	if _streams.has(stream_name):
		return _streams[stream_name]
	var s: AudioStream = null
	for ext in [".ogg", ".wav"]:
		if ResourceLoader.exists(DIR + stream_name + ext):
			s = load(DIR + stream_name + ext)
			break
	_streams[stream_name] = s
	return s


func _process(delta: float) -> void:
	# crossfade day birdsong and night crickets
	_amb_day.volume_db = linear_to_db(clampf(1.0 - night, 0.0001, 1.0)) - 4.0
	_amb_night.volume_db = linear_to_db(clampf(night, 0.0001, 1.0)) - 4.0
	if not _music.playing:
		_music_gap -= delta
		if _music_gap <= 0.0:
			_play_next_music()


func _play_next_music() -> void:
	var s := _stream(MUSIC[_music_index % MUSIC.size()])
	_music_index += 1
	if s == null:
		_music_gap = 30.0
		return
	if s is AudioStreamOggVorbis:
		(s as AudioStreamOggVorbis).loop = false
	_music.stream = s
	_music.play()


func _on_music_finished() -> void:
	# a quiet pause between pieces, like the original's sparse soundtrack
	_music_gap = randf_range(25.0, 60.0)


## Plays a non-positional sound. `variants` picks name_1..name_N at random.
func play(stream_name: String, volume_db := 0.0, pitch_jitter := 0.08, variants := 0) -> void:
	var key := stream_name
	if variants > 0:
		key = "%s_%d" % [stream_name, randi() % variants + 1]
	var now := Time.get_ticks_msec()
	if _last_play.get(key, -1000) > now - 45:
		return # avoid machine-gunning during drags
	_last_play[key] = now
	var s := _stream(key)
	if s == null:
		return
	for p in _pool:
		if not p.playing:
			p.stream = s
			p.volume_db = volume_db
			p.pitch_scale = 1.0 + randf_range(-pitch_jitter, pitch_jitter)
			p.play()
			return


func play_at(stream_name: String, pos: Vector3, volume_db := 0.0, variants := 0) -> void:
	var key := stream_name
	if variants > 0:
		key = "%s_%d" % [stream_name, randi() % variants + 1]
	var s := _stream(key)
	if s == null:
		return
	for p in _pool3d:
		if not p.playing:
			p.stream = s
			p.global_position = pos
			p.volume_db = volume_db
			p.pitch_scale = randf_range(0.92, 1.08)
			p.play()
			return
