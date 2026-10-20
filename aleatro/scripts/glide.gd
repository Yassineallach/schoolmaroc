class_name Glide
extends Node

## Springy movement for a Control. Give it a destination with `to()` and its
## parent chases it each frame instead of following a fixed-length tween: a
## new destination mid-flight just bends the path, the arrival overshoots a
## touch, the object leans into fast sideways moves, and `kick()` sets it
## wobbling. Glide owns only position and rotation, so flips, scale pops and
## fades can keep using tweens on the same node.

## Reduced motion: no overshoot, lean or wobble.
static var calm := false

const STIFF := 320.0  # normal travel
const SNAPPY := 1100.0  # following a finger
const WOBBLE_STIFF := 600.0
const LEAN := 0.00022  # radians of lean per px/s of sideways speed
const MAX_LEAN := 0.22
const STEP := 1.0 / 120.0

signal arrived

var target := Vector2.ZERO
var target_rot := 0.0
var stiffness := STIFF
var _vel := Vector2.ZERO
var _rot := 0.0
var _rot_vel := 0.0
var _lean := 0.0
var _wobble := 0.0
var _wobble_vel := 0.0
var _delay := 0.0
var _active := false


## The Glide on `c`, made on first use.
static func of(c: Control) -> Glide:
	var g: Glide = c.get_node_or_null("Glide")
	if g == null:
		g = Glide.new()
		g.name = "Glide"
		c.add_child(g)
	return g


## Glide on `c` if it has one.
static func on(c: Node) -> Glide:
	return c.get_node_or_null("Glide") as Glide


func _ready() -> void:
	set_process(_active)


func _host() -> Control:
	return get_parent() as Control


## Head for `pos` (parent space) and, if given, `rot` degrees, after `delay` s.
func to(pos: Vector2, rot := NAN, delay := 0.0, stiff := STIFF) -> void:
	var c := _host()
	if not _active:
		_rot = c.rotation
		target_rot = c.rotation
	target = pos
	if not is_nan(rot):
		target_rot = deg_to_rad(rot)
	_delay = delay
	stiffness = stiff
	_wake()


## Jump straight to `pos` / `rot` degrees with no motion.
func snap(pos: Vector2, rot := NAN) -> void:
	var c := _host()
	target = pos
	target_rot = deg_to_rad(rot) if not is_nan(rot) else c.rotation - _lean - _wobble
	_vel = Vector2.ZERO
	_rot_vel = 0.0
	_rot = target_rot
	_lean = 0.0
	_wobble = 0.0
	_wobble_vel = 0.0
	_delay = 0.0
	c.position = pos
	c.rotation = _rot
	_sleep()


## A springy shake, e.g. when the object scores or is grabbed.
func kick(amount := 0.12) -> void:
	if calm:
		return
	if not _active:
		_rot = _host().rotation
		target = _host().position
		target_rot = _rot
	_wobble_vel += (1.0 if randf() < 0.5 else -1.0) * amount * 14.0
	_wake()


func is_moving() -> bool:
	return _active


func _wake() -> void:
	_active = true
	set_process(true)


func _sleep() -> void:
	_active = false
	set_process(false)


func _process(delta: float) -> void:
	var c := _host()
	if c == null:
		return
	var dt := minf(delta, 0.05)
	var k := stiffness
	var d := 2.0 * sqrt(k) * (1.0 if calm else 0.72)
	var wk := WOBBLE_STIFF
	var wd := 2.0 * sqrt(wk) * 0.22
	var pos := c.position
	var steps := maxi(1, ceili(dt / STEP))
	var h := dt / steps
	for i in steps:
		if _delay > 0.0:
			_delay -= h
		else:
			_vel += (k * (target - pos) - d * _vel) * h
			pos += _vel * h
			_rot_vel += (k * (target_rot - _rot) - d * _rot_vel) * h
			_rot += _rot_vel * h
		_wobble_vel += (-wk * _wobble - wd * _wobble_vel) * h
		_wobble += _wobble_vel * h
	var lean_goal := 0.0 if calm else clampf(_vel.x * LEAN, -MAX_LEAN, MAX_LEAN)
	_lean = lerpf(_lean, lean_goal, 1.0 - exp(-14.0 * dt))
	c.position = pos
	c.rotation = _rot + _lean + _wobble
	if _delay <= 0.0 and pos.distance_squared_to(target) < 0.25 and _vel.length_squared() < 25.0 \
			and absf(_rot - target_rot) < 0.002 and absf(_rot_vel) < 0.05 \
			and absf(_wobble) < 0.002 and absf(_wobble_vel) < 0.05 and absf(_lean) < 0.002:
		snap(target, rad_to_deg(target_rot))
		arrived.emit()
