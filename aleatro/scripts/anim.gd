class_name Anim
extends RefCounted

## Shared animation clock and the idle "float" used by cards, charms and chips.

const FPS := 10.0  # frame rate for frame-stepped animations


static func now() -> float:
	return Time.get_ticks_msec() / 1000.0


## Gentle sway and hover for an object of `size`. `amount` scales the motion
## (0 = still). Returns the transform to draw the object's face with.
static func float_xform(size: Vector2, phase: float, amount: float) -> Transform2D:
	if amount <= 0.0:
		return Transform2D.IDENTITY
	var t := now()
	var angle := 0.035 * amount * sin(2.0 * t + phase)
	var c := size / 2.0
	return Transform2D(angle, c + Vector2(0, -3.0 * lift(phase, amount))) * Transform2D(0.0, -c)


## How high the object hovers; shadows grow with it.
static func lift(phase: float, amount: float) -> float:
	return amount * (1.0 + 0.3 * sin(0.666 * now() + phase * 1.7))
