class_name Sfx
extends Node

## Tiny synthesized sound effects, so the game ships without audio assets.

const RATE := 22050

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0


func _ready() -> void:
	_streams.click = _tone([660.0], 0.05, 0.25)
	_streams.select = _tone([880.0], 0.06, 0.22)
	_streams.chips = _tone([520.0, 780.0], 0.09, 0.25)
	_streams.mult = _tone([330.0, 495.0], 0.11, 0.28)
	_streams.xmult = _tone([392.0, 587.0, 784.0], 0.16, 0.3)
	_streams.coin = _tone([1046.0, 1568.0], 0.12, 0.22)
	_streams.win = _tone([523.0, 659.0, 784.0, 1046.0], 0.5, 0.3)
	_streams.lose = _tone([392.0, 311.0, 262.0], 0.7, 0.3)
	_streams.deal = _tone([300.0], 0.04, 0.15)
	Music._ensure_bus("SFX")
	for i in 8:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)


func play(name: String, pitch: float = 1.0) -> void:
	if not _streams.has(name):
		return
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	# A little random detune keeps repeated sounds from feeling mechanical.
	p.pitch_scale = pitch * randf_range(0.97, 1.03)
	p.play()


## Plays the frequencies as a quick arpeggio with a decaying envelope.
func _tone(freqs: Array, dur: float, vol: float) -> AudioStreamWAV:
	var n := int(RATE * dur)
	var data := PackedByteArray()
	data.resize(n * 2)
	var seg := n / freqs.size()
	var phase := 0.0
	for i in n:
		var f: float = freqs[mini(i / maxi(seg, 1), freqs.size() - 1)]
		phase += TAU * f / RATE
		var env := 1.0 - float(i) / n
		var v := (sin(phase) * 0.7 + signf(sin(phase)) * 0.3) * env * env * vol
		data.encode_s16(i * 2, int(clampf(v, -1.0, 1.0) * 32767))
	var s := AudioStreamWAV.new()
	s.format = AudioStreamWAV.FORMAT_16_BITS
	s.mix_rate = RATE
	s.stereo = false
	s.data = data
	return s
