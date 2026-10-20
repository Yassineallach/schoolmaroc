class_name Motes
extends Node2D

## Little spinning pixel squares. Each mote pops up to full size quickly,
## coasts outward while drag slows it, and shrinks away by the end of its
## life. An emitter can trickle motes steadily (`rate`), throw a `burst()`,
## spawn from a point or anywhere inside `area`, and fade out as a whole.
##
##   Motes.pop(fx_layer, pos, [Color.GOLD, Color.WHITE], 24)   # one-shot burst
##   var m := Motes.new(); m.rate = 0.08; m.area = box.size    # steady trickle

## Reduced motion: trickles stop and bursts are thinner.
static var calm := false

var area := Vector2.ZERO  ## spawn inside a rect of this size centred on the node
var rate := 0.0  ## seconds between motes in a steady trickle; 0 = off
var life := 0.9  ## seconds
var life_jitter := 0.3  ## fraction of `life` randomised per mote
var speed := 120.0  ## px/s at spawn
var speed_jitter := 0.7  ## fraction of `speed` randomised per mote
var spread := TAU  ## cone of directions (radians) around `heading`
var heading := -PI / 2  ## centre of the cone; default is straight up
var size := 9.0  ## largest edge in px
var drag := 2.2  ## how fast motes lose speed, per second
var gravity := Vector2.ZERO  ## px/s² pull
var spin := 4.0  ## max rad/s each way
var colors: Array = [Color.WHITE]
var cap := 160  ## most motes alive at once
var free_when_empty := false  ## free the emitter once it has nothing left to show

var _motes: Array = []  # [pos, vel, angle, spin, age, life, color]
var _clock := 0.0
var _fade := 1.0


## A one-shot burst of `n` motes at `pos` in `parent` that frees itself.
## `cfg` sets any of the emitter's fields.
static func pop(parent: Node, pos: Vector2, palette: Array, n: int, cfg := {}) -> Motes:
	var m := Motes.new()
	m.position = pos
	m.colors = palette
	for k in cfg:
		m.set(k, cfg[k])
	m.free_when_empty = true
	parent.add_child(m)
	m.burst(n)
	return m


func _ready() -> void:
	set_process(true)


## Throw `n` motes at once.
func burst(n: int) -> void:
	if calm:
		n = ceili(n / 3.0)
	for i in n:
		_spawn()


## Run the trickle for `seconds` so the emitter starts already full.
func prewarm(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		_step(1.0 / 30.0)
		t += 1.0 / 30.0


## Stop spawning and fade everything out over `time`, then free.
func fade_out(time := 0.4) -> void:
	rate = 0.0
	free_when_empty = true
	var tw := create_tween()
	tw.tween_property(self, "_fade", 0.0, time)
	tw.tween_callback(queue_free)


func count() -> int:
	return _motes.size()


func _spawn() -> void:
	if _motes.size() >= cap:
		return
	var at := Vector2(randf_range(-0.5, 0.5) * area.x, randf_range(-0.5, 0.5) * area.y)
	var dir := heading + randf_range(-0.5, 0.5) * spread
	var v := speed * (1.0 - speed_jitter * randf())
	var col: Color = colors[randi() % colors.size()]
	_motes.append([at, Vector2.from_angle(dir) * v, randf() * TAU, randf_range(-spin, spin),
		0.0, life * (1.0 - life_jitter * randf()), col])


func _process(delta: float) -> void:
	_step(delta)
	queue_redraw()
	if free_when_empty and _motes.is_empty() and (rate <= 0.0 or calm):
		queue_free()


func _step(dt: float) -> void:
	if rate > 0.0 and not calm:
		_clock += dt
		var spawned := 0
		while _clock >= rate and spawned < 20:
			_clock -= rate
			_spawn()
			spawned += 1
		_clock = minf(_clock, rate)
	var slow := exp(-drag * dt)
	for i in range(_motes.size() - 1, -1, -1):
		var m: Array = _motes[i]
		m[4] += dt
		if m[4] >= m[5]:
			_motes.remove_at(i)
			continue
		m[1] = m[1] * slow + gravity * dt
		m[0] += m[1] * dt
		m[2] += m[3] * dt


## Edge length at age `t` of `span`: up fast, then a long ease down to nothing.
static func _size_at(t: float, span: float, full: float) -> float:
	var k := t / span
	var grow := minf(k / 0.15, 1.0)
	var shrink := 1.0 - pow(maxf(k - 0.15, 0.0) / 0.85, 2.0)
	return full * grow * shrink


func _draw() -> void:
	for m in _motes:
		var s := roundf(_size_at(m[4], m[5], size))
		if s < 1.0:
			continue
		var col: Color = m[6]
		col.a *= _fade
		draw_set_transform(m[0].round(), m[2], Vector2.ONE)
		draw_rect(Rect2(-s / 2.0, -s / 2.0, s, s), col)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
