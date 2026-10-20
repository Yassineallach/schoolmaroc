class_name Anim
extends RefCounted

## Shared animation clock and the idle "float" used by cards, charms and chips.

const FPS := 10.0  # frame rate for frame-stepped animations

## Reduced motion: objects sit still instead of swaying.
static var calm := false


static func now() -> float:
	return Time.get_ticks_msec() / 1000.0


## Gentle sway and hover for an object of `size`. `amount` scales the motion
## (0 = still). Returns the transform to draw the object's face with.
static func float_xform(size: Vector2, phase: float, amount: float) -> Transform2D:
	if amount <= 0.0 or calm:
		return Transform2D.IDENTITY
	var t := now()
	var angle := 0.035 * amount * sin(2.0 * t + phase)
	var c := size / 2.0
	return Transform2D(angle, c + Vector2(0, -3.0 * lift(phase, amount))) * Transform2D(0.0, -c)


## How high the object hovers; shadows grow with it.
static func lift(phase: float, amount: float) -> float:
	if calm:
		return amount
	return amount * (1.0 + 0.3 * sin(0.666 * now() + phase * 1.7))


## Sideways shadow shift for an object at its place on screen, as if lit from
## above the middle: things on the right throw their shadow further right.
static func parallax(ci: Control) -> Vector2:
	var half := ci.get_viewport_rect().size.x / 2.0
	if half <= 0.0:
		return Vector2.ZERO
	var x := ci.get_global_rect().get_center().x
	return Vector2(clampf((x - half) / half, -1.0, 1.0) * 5.0, 0.0)
